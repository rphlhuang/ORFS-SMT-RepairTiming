# ==============================
# OpenSTA setup for gcd on nangate45
# ==============================

# 1. Design + platform
set design   "gcd"
set platform "nangate45"

# 2. Base directories (container paths)
set flow_root   "/OpenROAD-flow-scripts/flow"
set results_dir "$flow_root/results/$platform/$design/base"
set lib_dir     "$flow_root/platforms/$platform/lib"

# 3. Liberty timing model
read_liberty "$lib_dir/NangateOpenCellLibrary_typical.lib"

# 4. Netlist + link (use post-route final netlist)
read_verilog "$results_dir/6_final.v"
link_design $design

# 5. Constraints
read_sdc "$results_dir/6_final.sdc"

# 6. Parasitics (post-route SPEF)
if {[file exists "$results_dir/6_final.spef"]} {
    read_spef "$results_dir/6_final.spef"
}

# 7. Procs expected by Python

# For now, this doesn't actually modify the design — it just logs.
# Later you'll implement real ECOs here.
proc apply_buffer_solution {solfile} {
    puts "APPLYING_BUFFER_SOLUTION $solfile"
}

proc compute_worst_slacks {} {
    # Max = setup; Min = hold
    set ws_setup [report_worst_slack -max]
    set ws_hold  [report_worst_slack -min]

    # These markers are what your Python code waits for
    puts "WS_SETUP $ws_setup"
    puts "WS_HOLD $ws_hold"
}
