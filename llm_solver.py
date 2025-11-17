from z3 import *

# --- 1. The "Fake" Non-Linear Dataset (with R_wire) ---
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

# --- 2. Create the Z3 Solver ---
s = Solver()

# --- 3. Create Boolean Decision Variables ---
S_1_X1 = Bool('S_1_X1')
S_1_X2 = Bool('S_1_X2')
S_2_X1 = Bool('S_2_X1')
S_2_X2 = Bool('S_2_X2')

# --- 4. Add One-Hot Constraints ---
s.add(If(S_1_X1, 1, 0) + If(S_1_X2, 1, 0) == 1)
s.add(If(S_2_X1, 1, 0) + If(S_2_X2, 1, 0) == 1)

# --- 5. Model the Load (C_in, C_out) ---
slot2_choices = data['path_data']['buffer_slots'][1]['choices']
net1_data = data['path_data']['nets'][0]
net2_data = data['path_data']['nets'][1]

# C_in_2 is a variable that depends on the boolean choice for slot 2
C_in_2 = Real('C_in_2')
s.add(C_in_2 == If(S_2_X1, slot2_choices[0]['C_in'], slot2_choices[1]['C_in']))

# C_out_1 is the load driven by slot 1
C_out_1 = Real('C_out_1')
s.add(C_out_1 == net1_data['C_wire'] + C_in_2)

# C_out_2 is the load driven by slot 2
C_in_flop = net2_data['C_downstream_in'] # Fixed load
C_out_2 = Real('C_out_2')
s.add(C_out_2 == net2_data['C_wire'] + C_in_flop)


# --- 6. Link Booleans to Non-Linear Delays ---
# This section now calculates D_stage = D_cell + D_net

slot1_choices = data['path_data']['buffer_slots'][0]['choices']
s1_X1 = slot1_choices[0]
s1_X2 = slot1_choices[1]
s2_X1 = slot2_choices[0]
s2_X2 = slot2_choices[1]

# Create Real variables for the total delay of each stage
D_stage_1_max = Real('D_stage_1_max')
D_stage_1_min = Real('D_stage_1_min')
D_stage_2_max = Real('D_stage_2_max')
D_stage_2_min = Real('D_stage_2_min')

# --- Calculate Stage 1 Delay (D_cell_1 + D_net_1) ---
# D_cell_1 depends on choice S_1_... and load C_out_1
D_cell_1_max = If(S_1_X1, s1_X1['a_max'] * C_out_1 + s1_X1['b_max'],
                          s1_X2['a_max'] * C_out_1 + s1_X2['b_max'])
D_cell_1_min = If(S_1_X1, s1_X1['a_min'] * C_out_1 + s1_X1['b_min'],
                          s1_X2['a_min'] * C_out_1 + s1_X2['b_min'])

# D_net_1 (Elmore) depends on R_wire_1 and C_in_2
R_wire_1 = net1_data['R_wire']
C_wire_1 = net1_data['C_wire']
D_net_1 = R_wire_1 * (C_wire_1 / 2 + C_in_2) 

# D_stage_1 is the sum
s.add(D_stage_1_max == D_cell_1_max + D_net_1)
s.add(D_stage_1_min == D_cell_1_min + D_net_1)

# --- Calculate Stage 2 Delay (D_cell_2 + D_net_2) ---
# D_cell_2 depends on choice S_2_... and load C_out_2
D_cell_2_max = If(S_2_X1, s2_X1['a_max'] * C_out_2 + s2_X1['b_max'],
                          s2_X2['a_max'] * C_out_2 + s2_X2['b_max'])
D_cell_2_min = If(S_2_X1, s2_X1['a_min'] * C_out_2 + s2_X1['b_min'],
                          s2_X2['a_min'] * C_out_2 + s2_X2['b_min'])

# D_net_2 (Elmore) depends on R_wire_2 and C_in_flop (which is fixed)
R_wire_2 = net2_data['R_wire']
C_wire_2 = net2_data['C_wire']
D_net_2 = R_wire_2 * (C_wire_2 / 2 + C_in_flop)

# D_stage_2 is the sum
s.add(D_stage_2_max == D_cell_2_max + D_net_2)
s.add(D_stage_2_min == D_cell_2_min + D_net_2)


# --- 7. Define Total Path Delays ---
D_path_max = Real('D_path_max')
D_path_min = Real('D_path_min')

T_clk_q_max = data['path_data']['fixed_delays']['T_clk_q_max']
T_clk_q_min = data['path_data']['fixed_delays']['T_clk_q_min']

s.add(D_path_max == T_clk_q_max + D_stage_1_max + D_stage_2_max)
s.add(D_path_min == T_clk_q_min + D_stage_1_min + D_stage_2_min)

# --- 8. Add Setup and Hold Slack Constraints ---
g = data['global_timing']
s.add(D_path_max <= g['T_period'] + g['T_skew'] - g['T_setup'])
s.add(D_path_min >= g['T_skew'] + g['T_hold'])

# --- 9. Solve and Print Model ---
print("Solving with non-linear (NRA) constraints...")
print("This may be slow...")

try:
    result = s.check()
    
    if result == sat:
        print("Found a valid solution!")
        m = s.model()
        print(m)
    else:
        print("Unsatisfiable. No buffer combination meets timing.")

except Exception as e:
    print(f"An error occurred (common with complex NRA problems): {e}")