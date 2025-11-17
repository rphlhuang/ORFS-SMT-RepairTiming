from z3 import *

data = {
  "global_timing": { "T_period": 1.8, "T_skew": 0.05, "T_setup": 0.08, "T_hold": 0.04 },
  "path_data": {
    "fixed_delays": { "T_clk_q_max": 0.12, "T_clk_q_min": 0.09 },
    "buffer_slots": [
      { "slot_id": "buf_slot_1", "choices": [
          { "cell_type": "BUF_X1", "a_max": 2.1, "b_max": 0.08, "a_min": 1.8, "b_min": 0.06, "C_in": 0.015 },
          { "cell_type": "BUF_X2", "a_max": 1.5, "b_max": 0.06, "a_min": 1.3, "b_min": 0.05, "C_in": 0.022 } ]
      },
      { "slot_id": "buf_slot_2", "choices": [
          { "cell_type": "BUF_X1", "a_max": 2.1, "b_max": 0.08, "a_min": 1.8, "b_min": 0.06, "C_in": 0.015 },
          { "cell_type": "BUF_X2", "a_max": 1.5, "b_max": 0.06, "a_min": 1.3, "b_min": 0.05, "C_in": 0.022 } ]
      }
    ],
    "nets": [
      { "net_id": "net_1_to_2", "C_wire": 0.035, "R_wire": 0.15 },
      { "net_id": "net_2_to_flop", "C_wire": 0.040, "R_wire": 0.18, "C_downstream_in": 0.012 }
    ]
  }
}

s = Solver()

# Construct boolean decision vars
