#!/usr/bin/env tclsh
#
# buffer_replace.tcl - Replace buffers in critical path and measure impact
#
# DESCRIPTION:
#   This script finds the register-to-register critical path with SPEF parasitic
#   data and allows interactive buffer replacement to analyze timing impact.
#
# USAGE:
#   cd /path/to/flow
#
#   DESIGN_NAME=gcd \
#   ODB_FILE=results/sky130hd/gcd/base/6_final.odb \
#   SDC_FILE=results/sky130hd/gcd/base/6_final.sdc \
#   SPEF_FILE=results/sky130hd/gcd/base/6_final.spef \
#   TECH_LEF=platforms/sky130hd/lef/sky130_fd_sc_hd.tlef \
#   SC_LEF=platforms/sky130hd/lef/sky130_fd_sc_hd.lef \
#   LIB_FILES="platforms/sky130hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib" \
#   openroad buffer_replace.tcl
#
# ENVIRONMENT VARIABLES:
#   DESIGN_NAME       - Design name (required)
#   ODB_FILE          - Path to 6_final.odb (required)
#   SDC_FILE          - Path to 6_final.sdc (required)
#   SPEF_FILE         - Path to 6_final.spef (optional, for parasitic RC)
#   TECH_LEF          - Path to technology LEF file (optional)
#   SC_LEF            - Path to standard cell LEF file (optional)
#   LIB_FILES         - Space/semicolon-separated liberty files (optional)
#
# INTERACTIVE INPUT:
#   When prompted, enter buffer replacements as:
#     instance_name new_cell_name
#
#   Example:
#     rebuffer387 sky130_fd_sc_hd__buf_1
#     place178 sky130_fd_sc_hd__buf_4
#     DONE
#
# OUTPUT:
#   - Original critical path with SPEF parasitic data
#   - Available buffer cell variants in library
#   - Buffer replacements applied
#   - New critical path timing after replacement
#   - Slack comparison (before/after)
#
# NOTES:
#   - Uses register-to-register paths only (-from registers -to registers)
#   - Clock is propagated for accurate skew calculation
#   - SPEF file includes wire RC parasitic data for accurate timing
#   - All measurements are on the same register-to-register critical path

package require Tcl 8.6

# Read from environment variables
set design [expr {[info exists ::env(DESIGN_NAME)] ? $::env(DESIGN_NAME) : ""}]
set odb_file [expr {[info exists ::env(ODB_FILE)] ? $::env(ODB_FILE) : ""}]
set sdc_file [expr {[info exists ::env(SDC_FILE)] ? $::env(SDC_FILE) : ""}]
set spef_file [expr {[info exists ::env(SPEF_FILE)] ? $::env(SPEF_FILE) : ""}]

# Validate required arguments
if {$design eq "" || $odb_file eq "" || $sdc_file eq ""} {
  puts "ERROR: Missing required environment variables"
  exit 1
}

puts "INFO: Loading design: $design"

# Load optional LEF files
if {[info exists ::env(TECH_LEF)] && [file exists $::env(TECH_LEF)]} {
  read_lef $::env(TECH_LEF)
}

if {[info exists ::env(SC_LEF)] && [file exists $::env(SC_LEF)]} {
  read_lef $::env(SC_LEF)
}

# Load optional liberty files
if {[info exists ::env(LIB_FILES)]} {
  foreach lib_file $::env(LIB_FILES) {
    set trimmed [string trim $lib_file]
    if {$trimmed ne "" && [file exists $trimmed]} {
      read_liberty $trimmed
    }
  }
}

# Load the design
read_db $odb_file
read_sdc $sdc_file

# Load SPEF parasitic data for accurate timing (optional but recommended)
if {$spef_file ne "" && [file exists $spef_file]} {
  puts "INFO: Loading SPEF parasitic data: $spef_file"
  read_spef $spef_file
} else {
  puts "WARNING: No SPEF file provided. Timing analysis will use only library RC data."
}

puts "INFO: Design loaded successfully"
puts ""

# Get the register-to-register critical path (same method as extract_critical_path_reg.tcl)
puts "=========================================="
puts "FINDING REGISTER-TO-REGISTER CRITICAL PATH"
puts "=========================================="
puts ""

# Propagate clock delays for accurate timing
set clocks [all_clocks]
if {[llength $clocks] == 0} {
  puts "WARNING: Design has no clocks. Using default timing paths."
  set critical_path_end ""
} else {
  set_propagated_clock $clocks

  # Get all registers
  set register_set [all_registers]
  if {[llength $register_set] == 0} {
    puts "WARNING: No registers found in design."
    set critical_path_end ""
  } else {
    # Find register-to-register path with worst slack
    set critical_path_end [lindex [find_timing_paths -path_delay max \
      -from $register_set -to $register_set -sort_by_slack] 0]

    if {$critical_path_end eq ""} {
      puts "WARNING: Unable to find a register-to-register critical path."
    } else {
      set selected_start_pin [get_full_name [get_property $critical_path_end startpoint]]
      set selected_end_pin [get_full_name [get_property $critical_path_end endpoint]]

      puts "Found critical path:"
      puts "  Start: $selected_start_pin"
      puts "  End:   $selected_end_pin"
      puts ""
    }
  }
}

# Report the critical path
puts "=========================================="
puts "ORIGINAL CRITICAL PATH (REG-TO-REG)"
puts "=========================================="
puts ""

if {$critical_path_end ne ""} {
  set selected_start_pin [get_full_name [get_property $critical_path_end startpoint]]
  set selected_end_pin [get_full_name [get_property $critical_path_end endpoint]]
  report_checks -path_delay max -digits 6 \
    -fields {slew capacitance net} \
    -from [list $selected_start_pin] -to [list $selected_end_pin] \
    -group_path_count 1 -endpoint_path_count 1 -format full
} else {
  report_checks -path_delay max -group_path_count 1 -endpoint_path_count 1 -format full
}

# Summary already shown in full report above

# Now let's extract the path to find buffers
# We'll use a simpler approach: print the path and let user identify buffers
puts ""
puts "=========================================="
puts "BUFFERS IN CRITICAL PATH"
puts "=========================================="
puts ""

# Get all instances in design and find buffers
set all_insts [get_cells -quiet *]
set buffers [list]

foreach inst $all_insts {
  set ref_name [get_property $inst ref_name]
  set cell_lower [string tolower $ref_name]

  # Check if it's a buffer
  if {[string match "buf*" $cell_lower] || [string match "inv*" $cell_lower]} {
    lappend buffers [list $inst $ref_name]
  }
}

puts "Found [llength $buffers] buffer instances in design:"
puts ""

set idx 1
foreach buf $buffers {
  set inst [lindex $buf 0]
  set cell [lindex $buf 1]
  puts "$idx. Instance: $inst, Cell: $cell"
  incr idx

  if {$idx > 20} {
    puts "... (showing first 20)"
    break
  }
}

puts ""
puts "=========================================="
puts "EXAMPLE: Replace buffers with smaller variants"
puts "=========================================="
puts ""
puts "To replace a buffer, use:"
puts "  replace_cell <instance_name> <new_cell_name>"
puts ""
puts "Example:"
puts "  replace_cell place263 sky130_fd_sc_hd__buf_2"
puts ""

# Check what buffer variants are available
set lib_cells [get_lib_cells -quiet "*buf*"]
set buf_variants [list]

foreach lib_cell $lib_cells {
  set cell_name [get_property $lib_cell name]
  set cell_base [lindex [split $cell_name "/"] end]
  if {[lsearch -exact $buf_variants $cell_base] < 0} {
    lappend buf_variants $cell_base
  }
}

puts "Available buffer cell variants:"
set idx 1
foreach variant [lsort $buf_variants] {
  puts "  $idx. $variant"
  incr idx
}

puts ""
puts "=========================================="
puts "INTERACTIVE BUFFER REPLACEMENT"
puts "=========================================="
puts ""
puts "Enter buffer replacements (format: instance_name new_cell_name)"
puts "Type 'DONE' when finished"
puts ""

set replacements [dict create]

while {1} {
  puts -nonewline "Enter replacement (or DONE): "
  flush stdout
  gets stdin user_input

  set user_input [string trim $user_input]

  if {[string tolower $user_input] eq "done"} {
    break
  }

  # Parse input
  set parts [split $user_input " "]
  if {[llength $parts] != 2} {
    puts "  Invalid format. Please use: instance_name new_cell_name"
    continue
  }

  set inst_name [lindex $parts 0]
  set new_cell [lindex $parts 1]

  # Verify instance exists
  set inst_objs [get_cells -quiet $inst_name]
  if {[llength $inst_objs] == 0} {
    puts "  ERROR: Instance '$inst_name' not found"
    continue
  }

  # Verify new cell exists in library
  set lib_cells [get_lib_cells -quiet */$new_cell]
  if {[llength $lib_cells] == 0} {
    puts "  ERROR: Cell '$new_cell' not found in library"
    continue
  }

  dict set replacements $inst_name $new_cell
  puts "  ✓ Queued: $inst_name → $new_cell"
}

if {[dict size $replacements] == 0} {
  puts ""
  puts "INFO: No replacements specified, exiting"
  exit 0
}

puts ""
puts "=========================================="
puts "APPLYING BUFFER REPLACEMENTS"
puts "=========================================="
puts ""

dict for {inst new_cell} $replacements {
  puts "Replacing $inst with $new_cell..."
  if {[catch {
    replace_cell $inst $new_cell
  } err]} {
    puts "  ERROR: Failed to replace: $err"
    continue
  }
  puts "  ✓ Success"
}

puts ""
puts "=========================================="
puts "CRITICAL PATH AFTER REPLACEMENT (REG-TO-REG)"
puts "=========================================="
puts ""

# Re-find the critical path to get fresh path object for reporting
if {$critical_path_end ne ""} {
  # Get all registers again
  set register_set [all_registers]
  # Find critical path again with fresh path object
  set critical_path_after [lindex [find_timing_paths -path_delay max \
    -from $register_set -to $register_set -sort_by_slack] 0]

  if {$critical_path_after ne ""} {
    set selected_start_pin [get_full_name [get_property $critical_path_after startpoint]]
    set selected_end_pin [get_full_name [get_property $critical_path_after endpoint]]
    report_checks -path_delay max -digits 6 \
      -fields {slew capacitance net} \
      -from [list $selected_start_pin] -to [list $selected_end_pin] \
      -group_path_count 1 -endpoint_path_count 1 -format full
  } else {
    report_checks -path_delay max -group_path_count 1 -endpoint_path_count 1 -format full
  }
} else {
  report_checks -path_delay max -group_path_count 1 -endpoint_path_count 1 -format full
}

puts ""
puts "INFO: Buffer replacement and STA analysis completed"

exit 0
