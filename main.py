import STAController
from solver import *

# This will
#   1. Start sta
#   2. Start thread
#   3. Run setup_sta.tcl
sta = STAController("setup_sta.tcl")


#-----------------------
# run SMT Solver # times
#-----------------------
iters = 100
for _ in range(iters):
    
    # Runs SMT
    # Outputs chosen buffer sizes to buffer.sol
    run_SMT_solver(data)
    
    # Grabs values from buffer.sol
    # runs apply_buffer_solution
    # then runs worst slack with new buffers
    sta.apply_and_get_slack()

sta.close()
