from STAController import *
from solver import *
import json

THRESHOLD = 0.0

# This will
#   1. Start sta
#   2. Start thread
#   3. Run setup_sta.tcl
print("Setting up STAcontroller")
sta = STAController("setup_sta.tcl")

with open("solver_input.json", "r") as f:
    data = json.load(f)

# Creating SMT instance
print("Setting up SMT solver")
SMT_inst = SMTsolver(data)

# Runs SMT
iter = 1
while True:
    # Outputs chosen buffer sizes to buffer.sol
    print("-------------------------")
    print(f"[ITER] {iter}")
    print("-------------------------")
    print("Running solve() on SMT_inst")
    SAT = SMT_inst.solve()

    iter += 1
    # If SAT 
    #   run apply_buffers
    # else
    #   No valid solution
    if SAT:
        # Grabs values from buffer.sol
        # runs apply_buffer_solution
        # then runs timing slack with new buffers
        print("running sta.apply_and_get_slack")
        setup_slack, hold_slack = sta.apply_and_get_slacks()
        
        # add conflict clause
        # print("STA output has negative slack, adding conflict clause...")
        # SMT_inst.add_conflict(SMT_inst.model)
        
        # Slack is now positive
        # else:
        print("STA output has optimal slack")
        
        # create new odb file
        sta.send_cmd("write_current_db ../results/sky130hd/gcd/base/after_smt.odb\n")
        break
        
    else:
        print("Unsatisfiable. No buffer combination meets timing.")
        break

sta.close()
