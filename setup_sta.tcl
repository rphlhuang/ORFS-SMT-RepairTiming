# setup_sta.tcl
#
# Loads the design into OpenSTA once and defines helper procs
# used by the Python STAController:
#
#   apply_buffer_solution <file>
#   compute_worst_slacks
#
# EXPECTED ENV VARS:
#   DESIGN_NAME   : top module name
#   NETLIST_FILE  : gate-level Verilog (or a space-separated list)
#   SDC_FILE      : timing constraints
#   SPEF_FILE     : optional SPEF for parasitics
#   LIB_FILES     : space-separated list of liberty files
#
#
# -----------------------------
# 1. Read environment variables
# -----------------------------
proc getenv_or_empty {name} {
    if {[info exists ::env($name)]} {
        return $::env($name)
    } else {
        return ""
    }
}

# TEMP: hardcoded for gcd / sky130hd
set design_name  "gcd"
set netlist_file "../results/sky130hd/gcd/base/6_final.v"
set sdc_file     "../results/sky130hd/gcd/base/6_final.sdc"
set spef_file    "../results/sky130hd/gcd/base/6_final.spef"
set lib_files    "../platforms/sky130hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib"
set tech_lefs    "../platforms/sky130hd/tech/sky130_fd_sc_hd.tlef"


# You can either list specific LEFs or grab all of them:
set cell_lefs [glob -nocomplain ../platforms/sky130hd/lef/*.lef]

foreach lef [concat $tech_lefs $cell_lefs] {
    set lef_trim [string trim $lef]
    if {$lef_trim eq ""} {
        continue
    }
    if {![file exists $lef_trim]} {
        puts "WARNING: LEF file '$lef_trim' not found, skipping"
        continue
    }
    puts "INFO: read_lef $lef_trim"
    read_lef $lef_trim
}

if {$design_name eq ""} {
    puts "ERROR: DESIGN_NAME environment variable is not set"
    return
}
if {$netlist_file eq ""} {
    puts "ERROR: NETLIST_FILE environment variable is not set"
    return
}
if {$sdc_file eq ""} {
    puts "ERROR: SDC_FILE environment variable is not set"
    return
}
if {$lib_files eq ""} {
    puts "WARNING: LIB_FILES not set; you must have already loaded liberty files."
}

puts "INFO: DESIGN_NAME   = $design_name"
puts "INFO: NETLIST_FILE  = $netlist_file"
puts "INFO: SDC_FILE      = $sdc_file"
puts "INFO: SPEF_FILE     = $spef_file"
puts "INFO: LIB_FILES     = $lib_files"
puts "INFO: LEF_FILES     = $tech_lefs"

# -----------------------------
# 2. Read liberty file(s)
# -----------------------------
if {$lib_files ne ""} {
    foreach lib $lib_files {
        set lib_trim [string trim $lib]
        if {$lib_trim eq ""} {
            continue
        }
        if {![file exists $lib_trim]} {
            puts "WARNING: Liberty file '$lib_trim' not found, skipping"
            continue
        }
        puts "INFO: read_liberty $lib_trim"
        read_liberty $lib_trim
    }
}

# -----------------------------
# 3. Read netlist & link design
# -----------------------------
set netlist_list [split $netlist_file " "]
foreach vfile $netlist_list {
    set vtrim [string trim $vfile]
    if {$vtrim eq ""} {
        continue
    }
    if {![file exists $vtrim]} {
        puts "WARNING: Verilog file '$vtrim' not found, skipping"
        continue
    }
    puts "INFO: read_verilog $vtrim"
    read_verilog $vtrim
}

puts "INFO: link_design $design_name"
link_design $design_name

# -----------------------------
# 4. Read SDC and SPEF (optional)
# -----------------------------
if {![file exists $sdc_file]} {
    puts "WARNING: SDC file '$sdc_file' not found"
} else {
    puts "INFO: read_sdc $sdc_file"
    read_sdc $sdc_file
}

if {$spef_file ne ""} {
    if {[file exists $spef_file]} {
        puts "INFO: read_spef $spef_file"
        read_spef $spef_file
    } else {
        puts "WARNING: SPEF file '$spef_file' not found; continuing without parasitics"
    }
} else {
    puts "INFO: SPEF_FILE not set; continuing without parasitics"
}

# -----------------------------
# 5. Initial timing setup
# -----------------------------
set clocks [all_clocks]
if {[llength $clocks] > 0} {
    puts "INFO: set_propagated_clock on [llength $clocks] clock(s)"
    set_propagated_clock $clocks
} else {
    puts "WARNING: no clocks found in design"
}

puts "INFO: Setup complete"

# -----------------------------
# 6. Procedure: apply_buffer_solution
# -----------------------------
# Expect each non-comment, non-empty line of filename to be:
#   <inst_name> <cell_name>
# Example:
#   _174_ sky130_fd_sc_hd__buf_2
#   rebuffer63 sky130_fd_sc_hd__buf_4
# -----------------------------
proc apply_buffer_solution {filename} {
    if {![file exists $filename]} {
        puts "ERROR: apply_buffer_solution: file '$filename' does not exist"
        return
    }

    puts "INFO: Applying buffer solution from '$filename'"

    set fh [open $filename r]
    set line_no 0
    while {[gets $fh line] >= 0} {
        incr line_no
        set line [string trim $line]
        if {$line eq ""} {
            continue
        }
        if {[string index $line 0] eq "#"} {
            continue
        }

        # Expect: <inst_name> <cell_name>
        set fields [split $line]
        if {[llength $fields] < 2} {
            puts "WARNING: line $line_no: expected 'inst cell', got '$line'"
            continue
        }

        set inst_name [lindex $fields 0]
        set cell_name [lindex $fields 1]

        if {[catch { replace_cell $inst_name $cell_name } err]} {
            puts "ERROR: replace_cell $inst_name $cell_name failed: $err"
        } else {
            puts "INFO: replaced $inst_name -> $cell_name"
        }
    }
    close $fh
}

# -----------------------------
# 7. Procedure: compute_worst_slacks
# -----------------------------
proc compute_worst_slacks {} {
    puts "INFO: Updating timing in compute_worst_slacks"

    if {[llength [info commands update_timing]]} {
        update_timing
    } else {
        puts "INFO: update_timing not found; relying on implicit timing update"
    }

    # These two commands print:
    #   worst slack max <value>
    #   worst slack min <value>
    report_worst_slack
    report_worst_slack -min

    flush stdout
}

# -----------------------------
# 8. Procedure: write_current_db
# -----------------------------
proc write_current_db {odb_path} {
    puts "INFO: Writing DB to '$odb_path'"
    write_db $odb_path
    flush stdout
}