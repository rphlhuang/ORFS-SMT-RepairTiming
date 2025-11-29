package require Tcl 8.6
package require json

proc require_file {path label} {
  if {![file exists $path]} {
    error "Missing $label file: $path"
  }
  return $path
}

proc seconds_to_ps {value} {
  if {$value eq ""} {
    return ""
  }
  return [expr {$value * 1.0e12}]
}

proc farads_to_ff {value} {
  if {$value eq ""} {
    return ""
  }
  return [expr {$value * 1.0e15}]
}

proc normalize_pin_name {pin_name} {
  set parts [split $pin_name "/"]
  if {[llength $parts] < 2} {
    return [list "" $pin_name]
  }
  set inst [join [lrange $parts 0 end-1] "/"]
  set pin [lindex $parts end]
  return [list $inst $pin]
}

proc collect_load_pins {net_name driver_pin} {
  set loads {}
  if {$net_name eq ""} {
    return $loads
  }
  set net_obj [get_nets -quiet $net_name]
  if {[llength $net_obj] == 0} {
    return $loads
  }
  foreach pin_obj [get_pins -of_objects $net_obj] {
    set full_pin [get_full_name $pin_obj]
    if {$full_pin eq $driver_pin} {
      continue
    }
    set parts [split $full_pin "/"]
    set pin_name [lindex $parts end]
    set inst_name ""
    if {[llength $parts] > 1} {
      set inst_name [join [lrange $parts 0 end-1] "/"]
    }
    set is_port 0
    if {$inst_name eq ""} {
      set is_port 1
    }
    set cell_type ""
    if {!$is_port} {
      set cell_obj [get_cells -quiet $inst_name]
      if {[llength $cell_obj] > 0} {
        set cell_type [get_property [lindex $cell_obj 0] ref_name]
      }
    }
    set entry [dict create \
      pin [expr {$is_port ? "PORT/$pin_name" : "$inst_name/$pin_name"}] \
      cell $cell_type \
      pin_name $pin_name \
      is_port $is_port]
    lappend loads $entry
  }
  return $loads
}

proc json_escape {text} {
  set map_list [list "\\" "\\\\" "\"" "\\\"" "\b" "\\b" "\f" "\\f" "\n" "\\n" "\r" "\\r" "\t" "\\t"]
  return [string map $map_list $text]
}

proc json_scalar {value} {
  if {$value eq ""} {
    return "\"\""
  }
  if {[string is double -strict $value]} {
    return $value
  }
  return "\"[json_escape $value]\""
}

proc dict_to_json {dict_value} {
  set items {}
  dict for {k v} $dict_value {
    lappend items "\"[json_escape $k]\": [json_scalar $v]"
  }
  return "\{[join $items , ]\}"
}

proc list_of_dicts_to_json {list_value} {
  set items {}
  foreach entry $list_value {
    lappend items [dict_to_json $entry]
  }
  return "\[[join $items , ]\]"
}

proc stage_to_json {stage_dict} {
  set load_list {}
  if {[dict exists $stage_dict load_pins]} {
    set load_list [dict get $stage_dict load_pins]
    dict unset stage_dict load_pins
  }
  set items {}
  dict for {k v} $stage_dict {
    lappend items "\"[json_escape $k]\": [json_scalar $v]"
  }
  set load_json [list_of_dicts_to_json $load_list]
  lappend items "\"load_pins\": $load_json"
  return "\{[join $items , ]\}"
}

set script_dir [file dirname [file normalize [info script]]]
set flow_root [file normalize $script_dir]

set results_dir [file normalize [file join $flow_root results/sky130hd/gcd/base]]
set odb_path  [require_file [file join $results_dir 6_final.odb] "ODB"]
set sdc_path  [require_file [file join $results_dir 6_final.sdc] "SDC"]
set spef_path [require_file [file join $results_dir 6_final.spef] "SPEF"]

set lib_dir [file normalize [file join $flow_root platforms/sky130hd/lib]]
set all_libs [lsort [glob -nocomplain -types f [file join $lib_dir *.lib]]]
set lib_files {}
foreach lib $all_libs {
  if {[string match *sky130_fd_sc_hd__* [file tail $lib]]} {
    lappend lib_files $lib
  }
}
if {[llength $lib_files] == 0} {
  error "No Liberty files found under $lib_dir"
}

foreach lib $lib_files {
  read_liberty $lib
}

read_db $odb_path
read_sdc $sdc_path
read_spef $spef_path

set clocks [all_clocks]
if {[llength $clocks] == 0} {
  error "Design has no clocks after reading SDC."
}
set_propagated_clock $clocks

set register_set [all_registers]
if {[llength $register_set] == 0} {
  error "No registers found in design."
}
set critical_path_end [lindex [find_timing_paths -path_delay max -from $register_set -to $register_set -sort_by_slack] 0]
if {$critical_path_end eq ""} {
  error "Unable to find a register-to-register critical path."
}
set selected_start_pin [get_full_name [get_property $critical_path_end startpoint]]
set selected_end_pin [get_full_name [get_property $critical_path_end endpoint]]

set setup_tmp [file join $results_dir __setup_path_reg.json]
report_checks -path_delay max -digits 6 \
  -fields {slew capacitance net} \
  -group_path_count 1 -endpoint_path_count 1 \
  -from [list $selected_start_pin] -to [list $selected_end_pin] \
  -format json > $setup_tmp
set setup_data_fd [open $setup_tmp r]
set setup_json [read $setup_data_fd]
close $setup_data_fd
file delete -force $setup_tmp

set setup_dict [json::json2dict $setup_json]
set setup_checks [dict get $setup_dict checks]
if {[llength $setup_checks] == 0} {
  error "report_checks returned no setup paths."
}
set worst_setup [lindex $setup_checks 0]
set source_points [dict get $worst_setup source_path]

set startpoint_name [dict get $worst_setup startpoint]
set endpoint_name   [dict get $worst_setup endpoint]
set target_clock ""
if {[dict exists $worst_setup target_clock]} {
  set target_clock [dict get $worst_setup target_clock]
}

set setup_slack_s [dict get $worst_setup slack]
set setup_required_s [dict get $worst_setup required_time]
set setup_arrival_s [dict get $worst_setup data_arrival_time]

set hold_tmp [file join $results_dir __hold_path_reg.json]
report_checks -path_delay min -digits 6 \
  -from [list $selected_start_pin] -to [list $selected_end_pin] \
  -group_path_count 1 -endpoint_path_count 1 \
  -format json > $hold_tmp
set hold_data_fd [open $hold_tmp r]
set hold_json [read $hold_data_fd]
close $hold_data_fd
file delete -force $hold_tmp
set hold_dict [json::json2dict $hold_json]
set hold_checks [dict get $hold_dict checks]
if {[llength $hold_checks] == 0} {
  error "report_checks returned no hold paths for $startpoint_name -> $endpoint_name"
}
set worst_hold [lindex $hold_checks 0]
set hold_slack_s [dict get $worst_hold slack]
set hold_required_s [dict get $worst_hold required_time]
set hold_arrival_s [dict get $worst_hold data_arrival_time]

set clock_period_ps ""
set clock_freq_hz ""
if {$target_clock ne ""} {
  set clk_objs [get_clocks -quiet $target_clock]
  if {[llength $clk_objs] > 0} {
    set clk_obj [lindex $clk_objs 0]
    set clk_period_val [get_property $clk_obj period]
    if {$clk_period_val ne ""} {
      set clock_period_ps [expr {$clk_period_val * 1000.0}]
      if {$clk_period_val > 0} {
        set clock_freq_hz [expr {1.0e9 / $clk_period_val}]
      }
    }
  }
}

set max_source_clock_path {}
if {[dict exists $worst_setup source_clock_path]} {
  set max_source_clock_path [dict get $worst_setup source_clock_path]
}
set max_target_clock_path {}
if {[dict exists $worst_setup target_clock_path]} {
  set max_target_clock_path [dict get $worst_setup target_clock_path]
}
set hold_source_points {}
if {[dict exists $worst_hold source_path]} {
  set hold_source_points [dict get $worst_hold source_path]
}
set hold_first_arrival_ps ""
if {[llength $hold_source_points] > 0} {
  set hold_first_arrival_ps [seconds_to_ps [dict get [lindex $hold_source_points 0] arrival]]
}

set stages {}
set prev_point {}
set stage_index 0
set first_stage_arrival_ps ""

foreach point $source_points {
  if {![dict exists $point instance]} {
    set prev_point $point
    continue
  }
  set inst_name [dict get $point instance]
  set cell_name [dict get $point cell]
  set pin_name [dict get $point pin]
  set net_name ""
  if {[dict exists $point net]} {
    set net_name [dict get $point net]
  }
  set arrival_s [dict get $point arrival]
  set slew_s ""
  if {[dict exists $point slew]} {
    set slew_s [dict get $point slew]
  }

  set has_cap [dict exists $point capacitance]
  if {!$has_cap} {
    set prev_point $point
    continue
  }

  set cap_f [dict get $point capacitance]
  set input_pin ""
  set input_slew_s ""
  if {[dict size $prev_point] > 0 && [dict exists $prev_point instance]} {
    if {[dict get $prev_point instance] eq $inst_name} {
      set input_pin [dict get $prev_point pin]
      if {[dict exists $prev_point slew]} {
        set input_slew_s [dict get $prev_point slew]
      }
    }
  }

  if {$input_slew_s eq ""} {
    set input_slew_s $slew_s
  }

  set driver_parts [normalize_pin_name $pin_name]
  set driver_pin_name [lindex $driver_parts 1]
  set loads [collect_load_pins $net_name $pin_name]

  set arrival_ps [seconds_to_ps $arrival_s]
  set required_ps ""
  if {$arrival_ps ne ""} {
    set required_ps [seconds_to_ps [expr {$arrival_s + $setup_slack_s}]]
  }

  set stage_dict [dict create \
    stage_index $stage_index \
    instance $inst_name \
    cell $cell_name \
    input_pin $input_pin \
    driver_pin $pin_name \
    driver_pin_name $driver_pin_name \
    net $net_name \
    input_slew_ps [seconds_to_ps $input_slew_s] \
    output_cap_fF [farads_to_ff $cap_f] \
    arrival_ps $arrival_ps \
    required_ps $required_ps \
    load_pins $loads]
  lappend stages $stage_dict
  if {$stage_index == 0} {
    set first_stage_arrival_ps $arrival_ps
  }
  incr stage_index
  set prev_point $point
}

set setup_required_ps [seconds_to_ps $setup_required_s]
set hold_required_ps [seconds_to_ps $hold_required_s]

set launch_clk_arrival_ps ""
if {[llength $max_source_clock_path] > 0} {
  set last_src [lindex $max_source_clock_path end]
  if {[dict exists $last_src arrival]} {
    set launch_clk_arrival_ps [seconds_to_ps [dict get $last_src arrival]]
  }
}

set capture_clk_arrival_ps ""
if {[llength $max_target_clock_path] > 0} {
  set last_tgt [lindex $max_target_clock_path end]
  if {[dict exists $last_tgt arrival]} {
    set capture_clk_arrival_ps [seconds_to_ps [dict get $last_tgt arrival]]
  } elseif {[dict exists $worst_setup target_clock_time]} {
    set capture_clk_arrival_ps [seconds_to_ps [dict get $worst_setup target_clock_time]]
  }
}

set clock_skew_ps ""
if {$launch_clk_arrival_ps ne "" && $capture_clk_arrival_ps ne ""} {
  set clock_skew_ps [expr {$capture_clk_arrival_ps - $launch_clk_arrival_ps}]
}

set t_setup_ps ""
if {$capture_clk_arrival_ps ne "" && $setup_required_ps ne ""} {
  set t_setup_ps [expr {$capture_clk_arrival_ps - $setup_required_ps}]
}

set t_hold_ps ""
if {$capture_clk_arrival_ps ne "" && $hold_required_ps ne ""} {
  set t_hold_ps [expr {$capture_clk_arrival_ps - $hold_required_ps}]
}

set clk_q_max_ps ""
if {$first_stage_arrival_ps ne "" && $launch_clk_arrival_ps ne ""} {
  set clk_q_max_ps [expr {$first_stage_arrival_ps - $launch_clk_arrival_ps}]
}

set clk_q_min_ps ""
if {$hold_first_arrival_ps ne "" && $launch_clk_arrival_ps ne ""} {
  set clk_q_min_ps [expr {$hold_first_arrival_ps - $launch_clk_arrival_ps}]
}

set summary [dict create \
  startpoint $startpoint_name \
  endpoint $endpoint_name \
  total_slack_ps [seconds_to_ps $setup_slack_s] \
  setup_slack_ps [seconds_to_ps $setup_slack_s] \
  hold_slack_ps [seconds_to_ps $hold_slack_s] \
  setup_required_ps $setup_required_ps \
  hold_required_ps $hold_required_ps \
  setup_arrival_ps [seconds_to_ps $setup_arrival_s] \
  hold_arrival_ps [seconds_to_ps $hold_arrival_s] \
  clock_period_ps $clock_period_ps \
  clock_frequency_hz $clock_freq_hz \
  launch_clock_arrival_ps $launch_clk_arrival_ps \
  capture_clock_arrival_ps $capture_clk_arrival_ps \
  clock_skew_ps $clock_skew_ps \
  t_setup_ps $t_setup_ps \
  t_hold_ps $t_hold_ps \
  clk_q_max_ps $clk_q_max_ps \
  clk_q_min_ps $clk_q_min_ps \
  num_stages [llength $stages]]

set out_path [file join $results_dir critical_path_data_reg.json]
set out_fh [open $out_path w]
set summary_json [dict_to_json $summary]
set stage_json_list {}
foreach stage $stages {
  lappend stage_json_list [stage_to_json $stage]
}
set stages_json "\[[join $stage_json_list , ]\]"
puts $out_fh "\{\"summary\": $summary_json, \"stages\": $stages_json\}"
close $out_fh

puts "Critical path data written to $out_path"
