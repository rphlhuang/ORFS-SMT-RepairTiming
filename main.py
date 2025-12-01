from STAController import *
from solver import *

# This will
#   1. Start sta
#   2. Start thread
#   3. Run setup_sta.tcl
print("Setting up STAcontroller")
sta = STAController("setup_sta.tcl")

# Creating SMT instance
print("Setting up SMT solver")
SMT_inst = SMTsolver(data)

setup_slack = -3
hold_slack = -3
# Runs SMT
while True:
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
        print("running sta.apply_and_get_slack")
        setup_slack += 1
        hold_slack += 1
        # setup_slack, hold_slack = sta.apply_and_get_slacks()
        
        # Slack is still negative
        print("Checking if slack is negative")
        if (setup_slack <= 0) or (hold_slack <= 0):
            # add conflict clause
            print("Adding conflict clause")
            SMT_inst.add_conflict(SMT_inst.model)
            print("STA output has negative slack, adding conflict clause...")
        
        # Slack is now positive
        else:
            print("STA output has positive slack")
            break
        
    else:
        print("Unsatisfiable. No buffer combination meets timing.")
        break

sta.close()
