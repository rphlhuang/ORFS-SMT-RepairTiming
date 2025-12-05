import pandas as pd
import numpy as np
import json
import re
import sys

def parse_size(cell_name):
    match = re.search(r'_(\d+)$', cell_name)
    if match:
        return int(match.group(1))
    return 1

def perform_regression(df_variant):
    X = df_variant['output_capacitance_fF'].values
    y = df_variant['cell_delay_ps'].values
    
    # Fit linear polynomial (deg=1)
    slope, intercept = np.polyfit(X, y, 1)
    
    # Units:
    # Slope 'a' is ps/fF. 
    # (1 ps / 1 fF) = (1e-12 s) / (1e-15 F) = 1000 Ohm = 1 kOhm.
    # So 'a' in kOhm is exactly the slope value. No conversion needed.
    
    # Intercept 'b' is ps. Convert to ns.
    b_ns = intercept / 1000.0
    
    return slope, b_ns

def main():
    input_csv = 'critical_path_variants_reg.csv'
    output_json = 'solver_input.json'

    print(f"Reading {input_csv}...")
    try:
        df = pd.read_csv(input_csv)
    except FileNotFoundError:
        print(f"Error: File {input_csv} not found.")
        return

    # --- Extract Global Timing ---
    # Get values from the first row (assuming constant for the path)
    row0 = df.iloc[0]
    global_timing = {
        "T_period": row0['global_T_period_ps'] / 1000.0,
        "T_skew": row0['global_T_skew_ps'] / 1000.0,
        "T_setup": row0['global_T_setup_ps'] / 1000.0,
        "T_hold": row0['global_T_hold_ps'] / 1000.0
    }

    # --- Build C_in Reference Map ---
    # We use 'downstream_input_cap_fF' from stage i to determine C_in of original cell at stage i+1.
    cin_ref_map = {} # Cell_Name -> Capacitance (fF)
    
    sorted_gate_indices = sorted(df['gate_index'].unique())
    
    for i in range(len(sorted_gate_indices) - 1):
        curr_idx = sorted_gate_indices[i]
        next_idx = sorted_gate_indices[i+1]
        
        # Get downstream cap of current stage
        curr_stage_rows = df[df['gate_index'] == curr_idx]
        downstream_cap = curr_stage_rows.iloc[0]['downstream_input_cap_fF']
        
        # Get original cell name of next stage
        next_stage_rows = df[df['gate_index'] == next_idx]
        next_orig_cell = next_stage_rows.iloc[0]['original_cell']
        
        cin_ref_map[next_orig_cell] = downstream_cap

    # --- Process Stages ---
    stages = []
    nets = []
    
    for i, gate_idx in enumerate(sorted_gate_indices):
        stage_df = df[df['gate_index'] == gate_idx]
        original_cell_name = stage_df.iloc[0]['original_cell']
        instance_name = stage_df.iloc[0]['instance_name']
        
        # Determine Cell Type (Buffer vs Combinational)
        # Simple heuristic: check if "buf" or "dly" is in the name
        is_buffer = "buf" in original_cell_name or "dly" in original_cell_name
        stage_type = "buffer" if is_buffer else "combinational"

        # --- Determine Baseline C_in for Original Cell ---
        # If we found it in the map, use it.
        # If not (e.g., first stage), try to find ANY instance of this cell type in map, or estimate.
        if original_cell_name in cin_ref_map:
            c_in_orig_fF = cin_ref_map[original_cell_name]
        else:
            # Fallback: Check if we saw this cell type elsewhere
            if original_cell_name in cin_ref_map:
                 c_in_orig_fF = cin_ref_map[original_cell_name]
            else:
                # Fallback: Estimate based on size (e.g. 1.5fF per size unit)
                # This mostly applies to the very first gate if it's unique
                orig_size = parse_size(original_cell_name)
                c_in_orig_fF = orig_size * 1.5 
                print(f"Warning: Estimated C_in for {original_cell_name} as {c_in_orig_fF} fF")

        orig_size = parse_size(original_cell_name)

        # --- Process Variants ---
        choices = []
        # Group by variant_cell to handle the sweep data
        for variant_name, variant_df in stage_df.groupby('variant_cell'):
            # create linear regression from scatterplot
            a_val, b_val = perform_regression(variant_df)
            
            # scale C_in
            var_size = parse_size(variant_name)
            c_in_variant_fF = c_in_orig_fF * (var_size / orig_size)

            # grab area
            try:
                area_val = variant_df.iloc[0]['variant_area_um2']
                choices.append({
                    "cell_type": variant_name,
                    "a": round(a_val, 4), # kOhm
                    "b": round(b_val, 5), # ns
                    "C_in": round(c_in_variant_fF / 1000.0, 5), # pF
                    "area": round(area_val, 5)
                })
            except Exception as e:
                print(f"Failed to retrieve area data: {e}")
                choices.append({
                    "cell_type": variant_name,
                    "a": round(a_val, 4), # kOhm
                    "b": round(b_val, 5), # ns
                    "C_in": round(c_in_variant_fF / 1000.0, 5), # pF
                })
                continue
            
        
        # sort choices by size/name for consistency
        choices.sort(key=lambda x: x['cell_type'])

        stages.append({
            "slot_id": instance_name,
            "type": stage_type,
            "choices": choices
        })

        # --- Build Net ---
        source = instance_name
        
        if i < len(sorted_gate_indices) - 1:
            # intermediate Net
            next_gate_idx = sorted_gate_indices[i+1]
            next_instance = df[df['gate_index'] == next_gate_idx].iloc[0]['instance_name']
            sink = next_instance
            is_terminal = False
        else:
            # final Net
            sink = "sink_pin"
            is_terminal = True

        # net parasitics (Constant for the stage)
        wire_res_ohm = stage_df.iloc[0]['wire_resistance_ohm']
        wire_cap_fF = stage_df.iloc[0]['wire_capacitance_fF']
        
        net_obj = {
            "net_id": f"net_{source}_to_{sink}",
            "source": source,
            "sink": sink,
            "C_wire": round(wire_cap_fF / 1000.0, 5),      # pF
            "R_wire": round(wire_res_ohm / 1000.0, 5)      # kOhm
        }
        
        if is_terminal:
            # Add the fixed downstream cap for the endpoint
            downstream_fF = stage_df.iloc[0]['downstream_input_cap_fF']
            net_obj["C_downstream_in"] = round(downstream_fF / 1000.0, 5) # pF

        nets.append(net_obj)

    # --- Construct Final JSON ---
    final_json = {
        "global_timing": global_timing,
        "path_data": {
            "fixed_delays": {
                # taking T_clk_q from the first row
                "T_clk_q": round(row0['t_clk_q_max_ps'] / 1000.0, 4)
            },
            "stages": stages,
            "nets": nets
        }
    }

    # write to file
    with open(output_json, 'w') as f:
        json.dump(final_json, f, indent=2)
    
    print(f"Successfully wrote {output_json}")

if __name__ == "__main__":
    main()