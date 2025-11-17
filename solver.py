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

buffer_sizes = set()
for i in data["path_data"]["buffer_slots"]:
    for cell in i["choices"]:
        buffer_sizes.add(cell["cell_type"])
buffer_sizes = list(buffer_sizes)
print("Buffer sizes: " + str(buffer_sizes))

slot_ids = set()
for i in data["path_data"]["buffer_slots"]:
        slot_ids.add(i["slot_id"])
slot_ids = list(slot_ids)
print("Slot ids: " + str(slot_ids))

s = Solver()

# Construct boolean decision vars
decision_vars = [Bool(f"S_{slot["slot_id"]}_{cell}") for slot in data["path_data"]["buffer_slots"] for cell in buffer_sizes]
print("Decision vars: ", str(decision_vars))

# One-hot constraint: at least one cell per slot, but no more
for slot in slot_ids:
     s.add(Sum([If(Bool(f"S_{slot}_{cell}"), 1, 0) for cell in buffer_sizes]) == 1)

try:
    result = s.check()
    
    if result == sat:
        print("Found a valid solution!")
        m = s.model()
        print(m)
    else:
        print("Unsatisfiable. No buffer combination meets timing.")


except Exception as e:
    print(f"An error occurred: {e}")