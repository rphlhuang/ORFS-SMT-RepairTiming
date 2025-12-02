from z3 import *
import pprint


data = {
  "global_timing": {
    "T_period": 1.1,
    "T_skew": 0.00010000000000002269,
    "T_setup": -0.8435,
    "T_hold": 0.12890000000000001
  },
  "path_data": {
    "fixed_delays": {
      "T_clk_q": 0.3916
    },
    "stages": [
      {
        "slot_id": "_174_",
        "type": "combinational",
        "choices": [
          {
            "cell_type": "sky130_fd_sc_hd__nor2b_1",
            "a": 12.5722,
            "b": 0.11051,
            "C_in": 0.0015
          },
          {
            "cell_type": "sky130_fd_sc_hd__nor2b_2",
            "a": 7.1856,
            "b": 0.13481,
            "C_in": 0.003
          },
          {
            "cell_type": "sky130_fd_sc_hd__nor2b_4",
            "a": 4.1792,
            "b": 0.12488,
            "C_in": 0.006
          }
        ]
      },
      {
        "slot_id": "_178_",
        "type": "combinational",
        "choices": [
          {
            "cell_type": "sky130_fd_sc_hd__maj3_1",
            "a": 5.4853,
            "b": 0.30226,
            "C_in": 0.00269
          },
          {
            "cell_type": "sky130_fd_sc_hd__maj3_2",
            "a": 3.004,
            "b": 0.27212,
            "C_in": 0.00539
          },
          {
            "cell_type": "sky130_fd_sc_hd__maj3_4",
            "a": 1.6685,
            "b": 0.3049,
            "C_in": 0.01078
          }
        ]
      },
      {
        "slot_id": "_185_",
        "type": "combinational",
        "choices": [
          {
            "cell_type": "sky130_fd_sc_hd__maj3_1",
            "a": 5.5,
            "b": 0.30991,
            "C_in": 0.00163
          },
          {
            "cell_type": "sky130_fd_sc_hd__maj3_2",
            "a": 3.0072,
            "b": 0.2818,
            "C_in": 0.00327
          },
          {
            "cell_type": "sky130_fd_sc_hd__maj3_4",
            "a": 1.6702,
            "b": 0.31451,
            "C_in": 0.00654
          }
        ]
      },
      {
        "slot_id": "_187_",
        "type": "combinational",
        "choices": [
          {
            "cell_type": "sky130_fd_sc_hd__a21oi_1",
            "a": 13.9494,
            "b": 0.09056,
            "C_in": 0.00291
          },
          {
            "cell_type": "sky130_fd_sc_hd__a21oi_2",
            "a": 8.266,
            "b": 0.09508,
            "C_in": 0.00582
          },
          {
            "cell_type": "sky130_fd_sc_hd__a21oi_4",
            "a": 4.7374,
            "b": 0.1008,
            "C_in": 0.01164
          }
        ]
      },
      {
        "slot_id": "_207_",
        "type": "combinational",
        "choices": [
          {
            "cell_type": "sky130_fd_sc_hd__a21oi_1",
            "a": 14.0685,
            "b": 0.13455,
            "C_in": 0.00291
          },
          {
            "cell_type": "sky130_fd_sc_hd__a21oi_2",
            "a": 7.6699,
            "b": 0.1404,
            "C_in": 0.00582
          },
          {
            "cell_type": "sky130_fd_sc_hd__a21oi_4",
            "a": 4.5814,
            "b": 0.15251,
            "C_in": 0.01164
          }
        ]
      },
      {
        "slot_id": "_254_",
        "type": "combinational",
        "choices": [
          {
            "cell_type": "sky130_fd_sc_hd__a2111oi_0",
            "a": 45.3085,
            "b": 0.16224,
            "C_in": 0.0
          },
          {
            "cell_type": "sky130_fd_sc_hd__a2111oi_1",
            "a": 31.2722,
            "b": 0.18118,
            "C_in": 0.00271
          },
          {
            "cell_type": "sky130_fd_sc_hd__a2111oi_2",
            "a": 17.0649,
            "b": 0.1648,
            "C_in": 0.00543
          },
          {
            "cell_type": "sky130_fd_sc_hd__a2111oi_4",
            "a": 9.2645,
            "b": 0.16206,
            "C_in": 0.01085
          }
        ]
      },
      {
        "slot_id": "rebuffer233",
        "type": "buffer",
        "choices": [
          {
            "cell_type": "sky130_fd_sc_hd__buf_1",
            "a": 7.3893,
            "b": 0.15894,
            "C_in": 0.0012
          },
          {
            "cell_type": "sky130_fd_sc_hd__buf_12",
            "a": 0.7386,
            "b": 0.22301,
            "C_in": 0.0144
          },
          {
            "cell_type": "sky130_fd_sc_hd__buf_16",
            "a": 0.6529,
            "b": 0.22926,
            "C_in": 0.0192
          },
          {
            "cell_type": "sky130_fd_sc_hd__buf_2",
            "a": 3.0679,
            "b": 0.22536,
            "C_in": 0.0024
          },
          {
            "cell_type": "sky130_fd_sc_hd__buf_4",
            "a": 1.7105,
            "b": 0.24621,
            "C_in": 0.0048
          },
          {
            "cell_type": "sky130_fd_sc_hd__buf_6",
            "a": 1.2154,
            "b": 0.22434,
            "C_in": 0.0072
          },
          {
            "cell_type": "sky130_fd_sc_hd__buf_8",
            "a": 1.0492,
            "b": 0.21025,
            "C_in": 0.0096
          }
        ]
      },
      {
        "slot_id": "_257_",
        "type": "combinational",
        "choices": [
          {
            "cell_type": "sky130_fd_sc_hd__a2111oi_0",
            "a": 45.2437,
            "b": 0.20756,
            "C_in": 0.0
          },
          {
            "cell_type": "sky130_fd_sc_hd__a2111oi_1",
            "a": 31.1524,
            "b": 0.22319,
            "C_in": 0.00271
          },
          {
            "cell_type": "sky130_fd_sc_hd__a2111oi_2",
            "a": 17.0476,
            "b": 0.21944,
            "C_in": 0.00543
          },
          {
            "cell_type": "sky130_fd_sc_hd__a2111oi_4",
            "a": 9.2445,
            "b": 0.22618,
            "C_in": 0.01085
          }
        ]
      },
      {
        "slot_id": "_271_",
        "type": "combinational",
        "choices": [
          {
            "cell_type": "sky130_fd_sc_hd__a2111oi_0",
            "a": 45.181,
            "b": 0.25388,
            "C_in": 0.0
          },
          {
            "cell_type": "sky130_fd_sc_hd__a2111oi_1",
            "a": 31.1803,
            "b": 0.28188,
            "C_in": 0.00271
          },
          {
            "cell_type": "sky130_fd_sc_hd__a2111oi_2",
            "a": 17.0857,
            "b": 0.28935,
            "C_in": 0.00543
          },
          {
            "cell_type": "sky130_fd_sc_hd__a2111oi_4",
            "a": 9.2422,
            "b": 0.29085,
            "C_in": 0.01085
          }
        ]
      },
      {
        "slot_id": "rebuffer232",
        "type": "buffer",
        "choices": [
          {
            "cell_type": "sky130_fd_sc_hd__buf_1",
            "a": 7.4906,
            "b": 0.1428,
            "C_in": 0.0012
          },
          {
            "cell_type": "sky130_fd_sc_hd__buf_12",
            "a": 0.7425,
            "b": 0.1963,
            "C_in": 0.0144
          },
          {
            "cell_type": "sky130_fd_sc_hd__buf_16",
            "a": 0.6573,
            "b": 0.20259,
            "C_in": 0.0192
          },
          {
            "cell_type": "sky130_fd_sc_hd__buf_2",
            "a": 3.1113,
            "b": 0.20074,
            "C_in": 0.0024
          },
          {
            "cell_type": "sky130_fd_sc_hd__buf_4",
            "a": 1.7402,
            "b": 0.21946,
            "C_in": 0.0048
          },
          {
            "cell_type": "sky130_fd_sc_hd__buf_6",
            "a": 1.2388,
            "b": 0.19978,
            "C_in": 0.0072
          },
          {
            "cell_type": "sky130_fd_sc_hd__buf_8",
            "a": 1.0524,
            "b": 0.18799,
            "C_in": 0.0096
          }
        ]
      },
      {
        "slot_id": "_274_",
        "type": "combinational",
        "choices": [
          {
            "cell_type": "sky130_fd_sc_hd__o31ai_1",
            "a": 21.2819,
            "b": 0.1696,
            "C_in": 0.00429
          },
          {
            "cell_type": "sky130_fd_sc_hd__o31ai_2",
            "a": 12.3911,
            "b": 0.17776,
            "C_in": 0.00857
          },
          {
            "cell_type": "sky130_fd_sc_hd__o31ai_4",
            "a": 6.9579,
            "b": 0.18902,
            "C_in": 0.01715
          }
        ]
      },
      {
        "slot_id": "place139",
        "type": "buffer",
        "choices": [
          {
            "cell_type": "sky130_fd_sc_hd__buf_1",
            "a": 7.6916,
            "b": 0.10267,
            "C_in": 0.00285
          },
          {
            "cell_type": "sky130_fd_sc_hd__buf_12",
            "a": 0.7503,
            "b": 0.14698,
            "C_in": 0.03414
          },
          {
            "cell_type": "sky130_fd_sc_hd__buf_16",
            "a": 0.6643,
            "b": 0.1514,
            "C_in": 0.04553
          },
          {
            "cell_type": "sky130_fd_sc_hd__buf_2",
            "a": 3.228,
            "b": 0.14259,
            "C_in": 0.00569
          },
          {
            "cell_type": "sky130_fd_sc_hd__buf_4",
            "a": 1.7957,
            "b": 0.15822,
            "C_in": 0.01138
          },
          {
            "cell_type": "sky130_fd_sc_hd__buf_6",
            "a": 1.2824,
            "b": 0.14148,
            "C_in": 0.01707
          },
          {
            "cell_type": "sky130_fd_sc_hd__buf_8",
            "a": 1.0611,
            "b": 0.13897,
            "C_in": 0.02276
          }
        ]
      },
      {
        "slot_id": "_312_",
        "type": "combinational",
        "choices": [
          {
            "cell_type": "sky130_fd_sc_hd__mux2i_1",
            "a": 14.0689,
            "b": 0.09551,
            "C_in": 0.0252
          },
          {
            "cell_type": "sky130_fd_sc_hd__mux2i_2",
            "a": 9.0896,
            "b": 0.12725,
            "C_in": 0.0504
          },
          {
            "cell_type": "sky130_fd_sc_hd__mux2i_4",
            "a": 5.1776,
            "b": 0.12398,
            "C_in": 0.10081
          }
        ]
      },
      {
        "slot_id": "_314_",
        "type": "combinational",
        "choices": [
          {
            "cell_type": "sky130_fd_sc_hd__a21oi_1",
            "a": 13.928,
            "b": 0.14633,
            "C_in": 0.00235
          },
          {
            "cell_type": "sky130_fd_sc_hd__a21oi_2",
            "a": 8.3262,
            "b": 0.14879,
            "C_in": 0.0047
          },
          {
            "cell_type": "sky130_fd_sc_hd__a21oi_4",
            "a": 4.7603,
            "b": 0.15525,
            "C_in": 0.00941
          }
        ]
      }
    ],
    "nets": [
      {
        "net_id": "net__174__to__178_",
        "source": "_174_",
        "sink": "_178_",
        "C_wire": 0.00253,
        "R_wire": 0.0666
      },
      {
        "net_id": "net__178__to__185_",
        "source": "_178_",
        "sink": "_185_",
        "C_wire": 0.00204,
        "R_wire": 0.05501
      },
      {
        "net_id": "net__185__to__187_",
        "source": "_185_",
        "sink": "_187_",
        "C_wire": 0.00251,
        "R_wire": 0.0648
      },
      {
        "net_id": "net__187__to__207_",
        "source": "_187_",
        "sink": "_207_",
        "C_wire": 0.00088,
        "R_wire": 0.04488
      },
      {
        "net_id": "net__207__to__254_",
        "source": "_207_",
        "sink": "_254_",
        "C_wire": 0.00214,
        "R_wire": 0.06879
      },
      {
        "net_id": "net__254__to_rebuffer233",
        "source": "_254_",
        "sink": "rebuffer233",
        "C_wire": 0.00288,
        "R_wire": 0.07156
      },
      {
        "net_id": "net_rebuffer233_to__257_",
        "source": "rebuffer233",
        "sink": "_257_",
        "C_wire": 0.00021,
        "R_wire": 0.03099
      },
      {
        "net_id": "net__257__to__271_",
        "source": "_257_",
        "sink": "_271_",
        "C_wire": 0.00153,
        "R_wire": 0.05626
      },
      {
        "net_id": "net__271__to_rebuffer232",
        "source": "_271_",
        "sink": "rebuffer232",
        "C_wire": 0.00234,
        "R_wire": 0.0623
      },
      {
        "net_id": "net_rebuffer232_to__274_",
        "source": "rebuffer232",
        "sink": "_274_",
        "C_wire": 0.00386,
        "R_wire": 0.08738
      },
      {
        "net_id": "net__274__to_place139",
        "source": "_274_",
        "sink": "place139",
        "C_wire": 0.01547,
        "R_wire": 0.22052
      },
      {
        "net_id": "net_place139_to__312_",
        "source": "place139",
        "sink": "_312_",
        "C_wire": 0.00541,
        "R_wire": 0.1236
      },
      {
        "net_id": "net__312__to__314_",
        "source": "_312_",
        "sink": "_314_",
        "C_wire": 0.00476,
        "R_wire": 0.07273
      },
      {
        "net_id": "net__314__to_sink_pin",
        "source": "_314_",
        "sink": "sink_pin",
        "C_wire": 0.0026,
        "R_wire": 0.05571,
        "C_downstream_in": 0.0018
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
        self.model = []

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
        slack_hold = Real("slack_hold")

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
                self.model = self.solver.model()
                choices = self.extract_buffers(self.model)
                nicer = sorted([(d, self.model[d]) for d in self.model], key = lambda x: str(x[0]))
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
        self.solver.add(clause)