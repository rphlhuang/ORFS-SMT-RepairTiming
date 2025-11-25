import STAController
from solver import *

# This will
#   1. Start sta
#   2. Start thread
#   3. Run setup_sta.tcl
sta = STAController("setup_sta.tcl")

# Runs SMT
while True:
    # Outputs chosen buffer sizes to buffer.sol
    SAT = SMTsolver(data)

    # If SAT 
    #   run apply_buffers
    # else
    #   No valid solution
    if SAT:
        # Grabs values from buffer.sol
        # runs apply_buffer_solution
        # then runs timing slack with new buffers
        setup_slack, hold_slack = sta.apply_and_get_slack()
        
        # Slack is still negative
        if (setup_slack <= 0) or (hold_slack <= 0):
            # add conflict clause
            print("STA output has negative slack, adding conflict clause...")
        
        # Slack is now positive
        else:
            print("STA output has positive slack")
        
    else:
        print("Unsatisfiable. No buffer combination meets timing.")
        break
    
    
    

sta.close()
