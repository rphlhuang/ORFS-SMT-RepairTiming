# ==========================================
#               STA Setup
# ==========================================

# Load timing, netlist, and constraints
read_liberty ./lib/typical.lib
read_verilog ./netlist/design_post_synth.v
link_design top_module_name
read_sdc ./constraints/design.sdc

# Get initial timing values
update_timing



# ==========================================
#             TCL Functions
# ==========================================

# Apply buffer solution file
# ==========================================
# File format expected:
#   <slot_name> <cell_name>
# Example:
#   buf_slot_1 BUF_X1
#   buf_slot_2 BUF_X2

proc apply_buffer_solution {filename} {
    global slot_to_insts

    puts "INFO: Applying buffer solution from $filename"

    set fh [open $filename r]
    while {[gets $fh line] >= 0} {
        set line [string trim $line]
        if {$line eq ""} {
            continue
        }
        # allow comments starting with '#'
        if {[string index $line 0] eq "#"} {
            continue
        }

        set fields [split $line]
        if {[llength $fields] < 2} {
            puts "WARNING: malformed line in $filename: '$line'"
            continue
        }

        set slot_name [lindex $fields 0]
        set cell_name [lindex $fields 1]

        if {![info exists slot_to_insts($slot_name)]} {
            puts "WARNING: unknown slot $slot_name, skipping"
            continue
        }

        set inst_list $slot_to_insts($slot_name)

        foreach inst $inst_list {
            # check the instance exists in the design
            set inst_cells [get_cells $inst -quiet]
            if {[sizeof_collection $inst_cells] == 0} {
                puts "WARNING: instance $inst (slot $slot_name) not found, skipping"
                continue
            }

            puts "INFO: replace_cell $inst $cell_name"
            replace_cell $inst $cell_name
        }
    }
    close $fh
}


# Run timing & print worst slacks

proc compute_worst_slacks {} {
    # recompute timing after buffer changes
    update_timing

    # get worst setup and hold slacks
    set ws_setup [report_worst_slack]
    set ws_hold  [report_worst_slack -hold]

    # print in a machine-parseable way
    puts "WORST_SETUP_SLACK $ws_setup"
    puts "WORST_HOLD_SLACK  $ws_hold"

    # optional: dump the worst path for debugging/conflict clauses
    # report_timing -max_paths 1 > worst_path.rpt
}

puts "INFO: OpenSTA setup complete."