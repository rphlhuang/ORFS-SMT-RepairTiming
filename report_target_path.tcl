# report_target_path.tcl
#
# Usage:
#   DB_FILE=../results/sky130hd/gcd/base/6_final.odb \
#   ENDPOINTS_FILE=critical_path_variants_reg.endpoints.txt \
#   ../../tools/install/OpenROAD/bin/openroad -exit report_target_path.tcl \
#     > path_before_smt.rpt
#
#   DB_FILE=../results/sky130hd/gcd/base/after_smt.odb \
#   ENDPOINTS_FILE=critical_path_variants_reg.endpoints.txt \
#   ../../tools/install/OpenROAD/bin/openroad -exit report_target_path.tcl \
#     > path_after_smt.rpt
#

# --- env configuration ---
if {![info exists ::env(DB_FILE)]} {
    puts "ERROR: DB_FILE env var not set"
    exit 1
}
set db_file $::env(DB_FILE)

if {![info exists ::env(ENDPOINTS_FILE)]} {
    puts "ERROR: ENDPOINTS_FILE env var not set"
    exit 1
}
set endpoints_file $::env(ENDPOINTS_FILE)

set lib_file  "../platforms/sky130hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib"
set sdc_file  "../results/sky130hd/gcd/base/6_final.sdc"
set spef_file "../results/sky130hd/gcd/base/6_final.spef"

set tech_lef  "../platforms/sky130hd/lef/sky130_fd_sc_hd.tlef"
set cell_lefs {
    ../platforms/sky130hd/lef/sky130_fd_sc_hd_merged.lef
    ../platforms/sky130hd/lef/sky130io_fill.lef
}

puts "INFO: DB_FILE        = $db_file"
puts "INFO: ENDPOINTS_FILE = $endpoints_file"

# --- read endpoints file: line 1 = launch pin, line 2 = endpoint ---
if {![file exists $endpoints_file]} {
    puts "ERROR: endpoints file $endpoints_file not found"
    exit 1
}
set fh [open $endpoints_file r]
set launch_pin_name [string trim [gets $fh]]
set end_obj_name    [string trim [gets $fh]]
close $fh

puts "INFO: Launch pin  = $launch_pin_name"
puts "INFO: Endpoint    = $end_obj_name"

# --- LEFs ---
if {![file exists $tech_lef]} {
    puts "ERROR: Tech LEF $tech_lef not found"
    exit 1
}
puts "INFO: read_lef $tech_lef"
read_lef $tech_lef

foreach lef $cell_lefs {
    if {![file exists $lef]} {
        puts "WARNING: LEF $lef not found, skipping"
        continue
    }
    puts "INFO: read_lef $lef"
    read_lef $lef
}

# --- DB/DEF ---
if {![file exists $db_file]} {
    puts "ERROR: DB/DEF file $db_file not found"
    exit 1
}
set ext [string tolower [file extension $db_file]]
if {$ext eq ".odb"} {
    puts "INFO: read_db $db_file"
    read_db $db_file
} elseif {$ext eq ".def"} {
    puts "INFO: read_def $db_file"
    read_def $db_file
} else {
    puts "ERROR: DB_FILE must be .odb or .def, got $ext"
    exit 1
}

# --- Liberty / SDC / SPEF ---
if {![file exists $lib_file]} {
    puts "ERROR: Liberty $lib_file not found"
    exit 1
}
puts "INFO: read_liberty $lib_file"
read_liberty $lib_file

if {![file exists $sdc_file]} {
    puts "ERROR: SDC $sdc_file not found"
    exit 1
}
puts "INFO: read_sdc $sdc_file"
read_sdc $sdc_file

if {[file exists $spef_file]} {
    puts "INFO: read_spef $spef_file"
    read_spef $spef_file
} else {
    puts "WARNING: SPEF $spef_file not found; continuing without parasitics"
}

# --- Setup timing ---
set_propagated_clock [all_clocks]

# --- Resolve start and end objects ---
set start_pin [get_pins $launch_pin_name]
if {[llength $start_pin] == 0} {
    puts "ERROR: Could not find launch pin '$launch_pin_name'"
    exit 1
}

# Endpoint may be a port or a pin
set end_obj [get_ports $end_obj_name]
if {[llength $end_obj] == 0} {
    set end_obj [get_pins $end_obj_name]
}
if {[llength $end_obj] == 0} {
    puts "ERROR: Could not find endpoint '$end_obj_name' as port or pin"
    exit 1
}

puts "INFO: Resolved start_pin = $start_pin"
puts "INFO: Resolved end_obj   = $end_obj"

puts "======================================="
puts "Timing for path:"
puts "  from: $launch_pin_name"
puts "    to: $end_obj_name"
puts "  using DB: $db_file"
puts "======================================="

# --- Report timing using plain OpenROAD commands ---
# Use report_checks for setup/hold on that path.
report_checks -from $start_pin -to $end_obj -path_delay max
report_checks -from $start_pin -to $end_obj -path_delay min

exit
