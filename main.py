from solver import *
import subprocess
import json

OpenROAD = "../../tools/install/OpenROAD/bin/openroad"

# grab data values
with open("solver_input.json", "r") as f:
    data = json.load(f)

# Creating SMT instance
print("Setting up SMT solver")
SMT_inst = SMTsolver(data)

# Outputs chosen buffer sizes to buffer.sol
print("Running solve() on SMT_inst")
SAT = SMT_inst.solve()

# If SAT 
#   run apply_buffers
# else
#   No valid solution
if SAT:
    # Grabs values from buffer.sol
    # runs apply_buffer_solution
    # then runs timing slack with new buffers
    # creates new odb file
    print("STA output has optimal slack")
    subprocess.run(
        [OpenROAD, "-exit", "apply_smt_buffers.tcl"],
        check=True
    )
else:
    print("Unsatisfiable. No buffer combination meets timing.")