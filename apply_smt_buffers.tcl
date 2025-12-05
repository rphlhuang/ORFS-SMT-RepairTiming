# after_smt.tcl
#
# One-shot physical step:
#   - Load LEFs + DEF
#   - Apply final buffer mapping
#   - Write after_smt.odb
#

set design_name   "gcd"
set def_file      "../results/sky130hd/gcd/base/6_final.def"
set lib_files     "../platforms/sky130hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib"
set solution_file "buffers.sol"
set odb_out       "../results/sky130hd/gcd/base/after_smt.odb"

# 1 LEFs
set tech_lef "../platforms/sky130hd/lef/sky130_fd_sc_hd.tlef"
if {![file exists $tech_lef]} {
    puts "ERROR: Tech LEF $tech_lef not found"
    exit 1
}
puts "INFO: read_lef $tech_lef"
read_lef $tech_lef

# Standard-cell LEFs
set cell_lefs {
    ../platforms/sky130hd/lef/sky130_fd_sc_hd_merged.lef
    ../platforms/sky130hd/lef/sky130io_fill.lef
}

foreach lef $cell_lefs {
    if {![file exists $lef]} {
        puts "WARNING: LEF $lef not found, skipping"
        continue
    }
    puts "INFO: read_lef $lef"
    read_lef $lef
}

# 2 DEF
if {[file exists $def_file]} {
    puts "INFO: read_def $def_file"
    read_def $def_file
} else {
    puts "ERROR: DEF file '$def_file' not found"
    exit 1
}

# 3 Liberty
foreach lib $lib_files {
    set lib_trim [string trim $lib]
    if {$lib_trim eq ""} { continue }
    if {![file exists $lib_trim]} {
        puts "WARNING: Liberty '$lib_trim' not found, skipping"
        continue
    }
    puts "INFO: read_liberty $lib_trim"
    read_liberty $lib_trim
}


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
        if {$line eq ""} { continue }
        if {[string index $line 0] eq "#"} { continue }

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

apply_buffer_solution $solution_file

# Write final ODB
puts "INFO: Writing DB to '$odb_out'"
write_db $odb_out
