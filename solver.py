from z3 import *
import pprint

# --- SETUP --- 
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
          { "cell_type": "BUF_X1", "a_max": 2.1, "b_max": 0.08, "a_min": 1.8, "b_min": 0.06, "C_in": 0.016 },
          { "cell_type": "BUF_X2", "a_max": 1.5, "b_max": 0.06, "a_min": 1.3, "b_min": 0.05, "C_in": 0.024 } ]
      }
    ],
    "nets": [
      { "net_id": "net_1_to_2", "C_wire": 0.035, "R_wire": 0.15 },
      { "net_id": "net_2_to_flop", "C_wire": 0.040, "R_wire": 0.18, "C_downstream_in": 0.012 }
    ]
  }
}

buffer_sizes = set()
for i in data['path_data']['buffer_slots']:
    for cell in i['choices']:
        buffer_sizes.add(cell['cell_type'])
buffer_sizes = list(buffer_sizes)
print("Buffer sizes: " + str(buffer_sizes))

slot_ids = set()
for i in data['path_data']['buffer_slots']:
        slot_ids.add(i['slot_id'])
slot_ids = list(slot_ids)
print("Slot ids: " + str(slot_ids))

# Instantiate PyZ3 solver
s = Solver()


# --- BASIC CONSTRAINTS ---
# Construct boolean decision vars: dictionary of (slot_id, cell): z3_var pairs
# E.g. ("buf_slot_1", "BUF_X1") : S_buf_slot_1_BUF_X1 == True implies we chose BUF_X1 for buf_slot_1
decision_vars = {
    (slot['slot_id'], cell): Bool(f"S_{slot['slot_id']}_{cell}")
        for slot in data['path_data']['buffer_slots']
        for cell in buffer_sizes}
print("Decision vars: ", str(decision_vars))

# One-hot constraints: at least one cell per slot, but no more
for slot in slot_ids:
     s.add(Sum([If(Bool(f"S_{slot}_{cell}"), 1, 0) for cell in buffer_sizes]) == 1)

# Capacitance coherency constaints
C_in = {slot: Real(f"C_in_{slot}") for slot in slot_ids}
C_out ={slot: Real(f"C_out_{slot}") for slot in slot_ids}

# C_in = C_in of cell chosen
for slot in data['path_data']['buffer_slots']:
    # Build a sum of If(decision_var, C_in_val, 0)
    cin_sum_terms = []
    for choice in slot['choices']:
        cell_type = choice['cell_type']
        z3_var = decision_vars[(slot['slot_id'], cell_type)]
        c_in_val = choice['C_in']
        cin_sum_terms.append(If(z3_var, c_in_val, 0))
    # Add the constraint: C_in_buf_slot_1 == If(S_1_X1, 0.015, 0) + If(S_1_X2, 0.022, 0) + ...
    s.add(C_in[slot['slot_id']] == Sum(cin_sum_terms))

# C_out = C_in + C_net
for i, slot in enumerate(slot_ids):
    slot_id = slot
    net = data['path_data']['nets'][i] # Assumes nets list matches slots list
    C_wire = net['C_wire']
    if i < len(slot_ids) - 1:
        # Not the last slot. Load is C_wire + C_in of next slot.
        next_slot_id = slot_ids[i+1]
        C_in_next = C_in[next_slot_id]
        s.add(C_out[slot_id] == C_wire + C_in_next)
    else:
        # This is the last slot. Load is C_wire + fixed downstream cap.
        C_downstream = net['C_downstream_in']
        s.add(C_out[slot_id] == C_wire + C_downstream)


# --- STAGE DELAY CONSTRAINTS ---
D_stage_max = {slot: Real(f"D_stage_max_{slot}") for slot in slot_ids}
D_stage_min = {slot: Real(f"D_stage_min_{slot}") for slot in slot_ids}

# Loop through each slot and build its delay equation
for i, slot_id in enumerate(slot_ids):
    slot_data = data['path_data']['buffer_slots'][i]
    net_data = data['path_data']['nets'][i]
    
    # Get the C_out variable for this slot (already defined)
    C_out_var = C_out[slot_id]

    # --- 1. Build D_cell (using "sum of products") ---
    cell_delay_max_sum = []
    cell_delay_min_sum = []
    
    for choice in slot_data['choices']:
        cell_type = choice['cell_type']
        z3_var = decision_vars[(slot_id, cell_type)]
        
        # D_cell_max = a_max * C_out + b_max
        a_max, b_max = choice['a_max'], choice['b_max']
        cell_delay_max_sum.append( If(z3_var, a_max * C_out_var + b_max, 0) )
        
        # D_cell_min = a_min * C_out + b_min
        a_min, b_min = choice['a_min'], choice['b_min']
        cell_delay_min_sum.append( If(z3_var, a_min * C_out_var + b_min, 0) )

    D_cell_max = Sum(cell_delay_max_sum)
    D_cell_min = Sum(cell_delay_min_sum)

    # --- 2. Build D_net (Elmore Delay) ---
    R_wire = net_data['R_wire']
    C_wire = net_data['C_wire']
    
    # Get the downstream load (C_in of next stage, or fixed flop cap)
    if i < len(slot_ids) - 1:
        next_slot_id = slot_ids[i+1]
        C_downstream_load = C_in[next_slot_id]
    else:
        C_downstream_load = net_data['C_downstream_in']

    # D_net = R_wire * (C_wire / 2.0 + C_downstream_load)
    # Note: Use 2.0 to ensure floating-point math, not integer
    D_net = R_wire * (C_wire / 2.0 + C_downstream_load)

    # --- 3. Add the Final D_stage constraint ---
    s.add(D_stage_max[slot_id] == D_cell_max + D_net)
    s.add(D_stage_min[slot_id] == D_cell_min + D_net)

print("\nPrinting all constraints:")
set_option(rational_to_decimal=True)
set_option(precision=10)
for constaint in s.assertions():
    print(constaint, "\n")

try:
    print(" ---- SOLVING ---- ")
    result = s.check()
    if result == sat:
        print("Found a valid solution!")
        m = s.model()
        nicer = sorted([(d, m[d]) for d in m], key = lambda x: str(x[0]))
        pprint.pprint(nicer)
    else:
        print("Unsatisfiable. No buffer combination meets timing.")

except Exception as e:
    print(f"An error occurred: {e}")