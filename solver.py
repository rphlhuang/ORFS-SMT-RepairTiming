from z3 import *
import pprint


data = {
  "global_timing": {
    "T_period": 1.8,
    "T_skew": 0.05,
    "T_setup": 0.08,
    "T_hold": 0.04
  },
  "path_data": {
    "fixed_delays": {
      "T_clk_q": 0.11
    },
    "stages": [
      {
        "slot_id": "inst_1_NAND2",
        "type": "combinational",
        "choices": [
          { "cell_type": "NAND2_X1", "a": 2.50, "b": 0.09, "C_in": 0.012 }
        ]
      },
      {
        "slot_id": "inst_2_BUF",
        "type": "buffer",
        "choices": [
          { "cell_type": "BUF_X1",  "a": 1.95, "b": 0.07,  "C_in": 0.015 },
          { "cell_type": "BUF_X2",  "a": 1.40, "b": 0.055, "C_in": 0.022 },
          { "cell_type": "BUF_X4",  "a": 0.72, "b": 0.065, "C_in": 0.044 },
          { "cell_type": "BUF_X6",  "a": 0.50, "b": 0.075, "C_in": 0.066 },
          { "cell_type": "BUF_X8",  "a": 0.36, "b": 0.085, "C_in": 0.088 },
          { "cell_type": "BUF_X12", "a": 0.25, "b": 0.095, "C_in": 0.132 },
          { "cell_type": "BUF_X16", "a": 0.18, "b": 0.11,  "C_in": 0.176 }
        ]
      },
      {
        "slot_id": "inst_3_NOR3",
        "type": "combinational",
        "choices": [
          { "cell_type": "NOR3_X2", "a": 3.10, "b": 0.12, "C_in": 0.018 }
        ]
      },
      {
        "slot_id": "inst_4_BUF",
        "type": "buffer",
        "choices": [
          { "cell_type": "BUF_X1",  "a": 1.95, "b": 0.07,  "C_in": 0.015 },
          { "cell_type": "BUF_X2",  "a": 1.40, "b": 0.055, "C_in": 0.022 },
          { "cell_type": "BUF_X4",  "a": 0.72, "b": 0.065, "C_in": 0.044 },
          { "cell_type": "BUF_X6",  "a": 0.50, "b": 0.075, "C_in": 0.066 },
          { "cell_type": "BUF_X8",  "a": 0.36, "b": 0.085, "C_in": 0.088 },
          { "cell_type": "BUF_X12", "a": 0.25, "b": 0.095, "C_in": 0.132 },
          { "cell_type": "BUF_X16", "a": 0.18, "b": 0.11,  "C_in": 0.176 }
        ]
      }
    ],
    "nets": [
      {
        "net_id": "net_inst_1_to_inst_2",
        "source": "inst_1_NAND2",
        "sink": "inst_2_BUF",
        "C_wire": 0.035,
        "R_wire": 0.15
      },
      {
        "net_id": "net_inst_2_to_inst_3",
        "source": "inst_2_BUF",
        "sink": "inst_3_NOR3",
        "C_wire": 0.030,
        "R_wire": 0.12
      },
      {
        "net_id": "net_inst_3_to_inst_4",
        "source": "inst_3_NOR3",
        "sink": "inst_4_BUF",
        "C_wire": 0.040,
        "R_wire": 0.18
      },
      {
        "net_id": "net_inst_4_to_sink",
        "source": "inst_4_BUF",
        "sink": "D_pin",
        "C_wire": 0.010,
        "R_wire": 0.05,
        "C_downstream_in": 0.005
      }
    ]
  }
}

class SMTsolver:
    def __init__(self, data):
        self.stages = data['path_data']['stages']

        self.slot_ids = []
        for i in data['path_data']['stages']:
            self.slot_ids.append(i['slot_id'])
        self.slot_ids = list(self.slot_ids)
        print("Slot ids: " + str(self.slot_ids))

        # Instantiate PyZ3 solver
        self.solver = Solver()

        # --- BASIC CONSTRAINTS ---
        # Construct boolean decision vars: dictionary of (slot_id, cell): z3_var pairs
        # E.g. ("buf_slot_1", "BUF_X1") : S_buf_slot_1_BUF_X1 == True implies we chose BUF_X1 for buf_slot_1
        self.decision_vars = {}
        for slot in data['path_data']['stages']:
                for cell_option in slot['choices']:
                    cell_name = cell_option['cell_type']
                    self.decision_vars[(slot['slot_id'], cell_name)] = Bool(f"S_{slot['slot_id']}_{cell_name}")
        print("Decision vars: ", str(self.decision_vars))

        # One-hot constraints: at least one cell per slot, but no more
        for slot in self.stages:
            slot_id = slot['slot_id']
            self.solver.add(Sum([If(Bool(f"S_{slot_id}_{cell['cell_type']}"), 1, 0) for cell in slot['choices']]) == 1)

        # Capacitance coherency constaints
        C_in = {slot: Real(f"C_in_{slot}") for slot in self.slot_ids}
        C_out ={slot: Real(f"C_out_{slot}") for slot in self.slot_ids}

        # C_in = C_in of cell chosen
        for slot in data['path_data']['stages']:
            # Build a sum of If(decision_var, C_in_val, 0)
            cin_sum_terms = []
            for choice in slot['choices']:
                cell_type = choice['cell_type']
                z3_var = self.decision_vars[(slot['slot_id'], cell_type)]
                c_in_val = choice['C_in']
                cin_sum_terms.append(If(z3_var, c_in_val, 0))
            # Add the constraint: C_in_buf_slot_1 == If(S_1_X1, 0.015, 0) + If(S_1_X2, 0.022, 0) + ...
            self.solver.add(C_in[slot['slot_id']] == Sum(cin_sum_terms))

        # C_out = C_in + C_net
        nets_by_source = {net['source']: net for net in data['path_data']['nets']}
        for slot_id in self.slot_ids:
            # Ensure this slot actually drives a net
            if slot_id not in nets_by_source:
                raise ValueError(f"Error: Slot '{slot_id}' is not listed as a source for any net.")
            
            net = nets_by_source[slot_id]
            C_wire = net['C_wire']
            sink_id = net['sink']

            # Check if this is a net that goes to DFF or an intermediate net
            if 'C_downstream_in' in net:
                # net to DFF
                C_downstream = net['C_downstream_in']
                self.solver.add(C_out[slot_id] == C_wire + C_downstream)
            elif sink_id in C_in:
                # intermediate net
                C_in_next = C_in[sink_id]
                self.solver.add(C_out[slot_id] == C_wire + C_in_next)
            else:
                raise ValueError(f"Connectivity Error: Net from '{slot_id}' drives '{sink_id}', "
                                 f"but '{sink_id}' is not a known buffer/gate slot and no fixed C_downstream_in was provided.")

        # --- STAGE DELAY CONSTRAINTS ---
        D_stage = {slot: Real(f"D_stage_{slot}") for slot in self.slot_ids}

        # Loop through each stage and build its delay equation
        for i, slot_id in enumerate(self.slot_ids):
            slot_data = data['path_data']['stages'][i]
            net_data = data['path_data']['nets'][i]
            
            # Get the C_out variable for this slot (already defined)
            C_out_var = C_out[slot_id]

            # Build D_cell (using "sum of products")
            cell_delay_sum = []
            for choice in slot_data['choices']:
                cell_type = choice['cell_type']
                z3_var = self.decision_vars[(slot_id, cell_type)]
                a = choice['a']
                b = choice['b']
                cell_delay_sum.append(If(z3_var, a * C_out_var + b, 0))

            D_cell = Sum(cell_delay_sum)

            # Build D_net (Elmore delay)
            R_wire = net_data['R_wire']
            C_wire = net_data['C_wire']
            
            # Get the downstream load (C_in of next stage, or fixed flop cap)
            if i < len(self.slot_ids) - 1:
                next_slot_id = self.slot_ids[i+1]
                C_downstream_load = C_in[next_slot_id]
            else:
                C_downstream_load = net_data['C_downstream_in']

            # Note: Use 2.0 to ensure floating-point math, not integer
            D_net = R_wire * (C_wire / 2.0 + C_downstream_load)

            # Add the Final D_stage constraint
            self.solver.add(D_stage[slot_id] == D_cell + D_net)
            
        # --- GLOBAL TIMING PARAMETERS ---
        T_period = data["global_timing"]["T_period"]
        T_skew = data["global_timing"]["T_skew"]
        T_setup = data["global_timing"]["T_setup"]
        T_hold = data["global_timing"]["T_hold"]
        T_clk_q = data["path_data"]["fixed_delays"]["T_clk_q"]

        # --- ARRIVAL TIMES (DATA) ---
        AT = Real("AT")  # nominal arrival at capture flop

        # Sum the stage delays
        sum_D = Sum([D_stage[slot] for slot in self.slot_ids])

        # AT = clk->Q + sum of stage delays
        self.solver.add(AT == T_clk_q + sum_D)

        # --- REQUIRED TIMES ---
        RAT_setup = T_period - T_setup - T_skew # Python float
        RAT_hold = T_hold + T_skew

        # --- SLACK VARIABLES ---
        slack_setup = Real("slack_setup")
        slack_hold  = Real("slack_hold")

        # slack_setup = RAT_setup - AT_max
        self.solver.add(slack_setup == RAT_setup - AT)

        # slack_hold = AT_min - RAT_hold
        self.solver.add(slack_hold == AT - RAT_hold)

        # Enforce non-negative slack => timing-legal
        self.solver.add(slack_setup >= 0)
        self.solver.add(slack_hold >= 0)
            
    def solve(self):
        print("\nPrinting all constraints:")
        set_option(rational_to_decimal=True)
        set_option(precision=10)
        for constaint in self.solver.assertions():
            print(constaint, "\n")

        try:
            print(" ---- SOLVING ---- ")
            result = self.solver.check()
            if result == sat:
                print("Found a valid solution!")
                m = self.solver.model()
                choices = self.extract_buffers(m)
                nicer = sorted([(d, m[d]) for d in m], key = lambda x: str(x[0]))
                pprint.pprint(nicer)

                print("\nExtracted buffers:")
                pprint.pprint(choices)
                
                with open("buffers.sol", "w") as f:
                    for slot, cell in sorted(choices.items()):
                        f.write(f"{slot} {cell}\n")
                        
                return True
            else:
                return False

        except Exception as e:
            print(f"An error occurred: {e}")

    def extract_buffers(self, model):
        choices = {}
        for (slot_id, cell_name), z3_var in self.decision_vars.items():
            # check if Z3 set this variable to True
            if is_true(model[z3_var]):
                choices[slot_id] = cell_name
        
        return choices
            
    def add_conflict(self, model):
        true_vars = []
        for (_, _), var in self.decision_vars.items():
            if is_true(model[var]):
                true_vars.append(var)

        if not true_vars:
            return  # nothing to block, shouldn't really happen

        # Clause: at least one of these must flip next time
        clause = Or([Not(v) for v in true_vars])
        self.s.add(clause)
