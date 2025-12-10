# OpenROAD Buffer Resizing with SMT

**NOTE: Clone this repo into the flow/ folder inside OpenROAD-flow-scripts**

This repository contains the core logic for a formal methods final project (CSE 216 at UC Santa Cruz). The goal is to find an **optimal** set of cell sizes for a critical timing path in a VLSI design, ensuring that both setup and hold timing constraints are met.

Instead of relying on traditional heuristics, this project models the entire timing path as a system of constraints, which is then solved by the Z3 SMT solver to find a valid, timing-aware solution.

## Architecture

The project is built as a closed-loop system that uses **OpenROAD** for real timing data and **Z3** as the formal-methods engine to find a solution.

The core architecture is as follows:
1.  **Data Extraction (OpenROAD):** Timing reports from OpenSTA are used to extract all necessary data for the critical paths: linear delay models, static timing constraints (period, skew, etc.), and capacitance values.
2.  **Constraint Generation (Python):** `csvtojson.py` parses this data and generates `solver_input.json` containing the design constraints and linear delay models.
3.  **SMT Solving (Z3):** The Z3 solver (`main.py` using `solver.py`) uses its internal OMT engine to propose solutions (Boolean assignments for buffer choices) and optimizes setup/hold slack using the derived linear delay models.
4.  **Implementation (TCL Conversion):** If a `sat` solution is found, it's converted into a set of Tcl commands (`resize_cell`).
5.  **Validation (OpenROAD):** The Tcl commands are run in OpenROAD to modify the design, and OpenSTA is run again to validate if timing is truly met. If it fails, the loop can be run again.

<!-- 
## Running the Project
1.  **Install dependencies:**
    ```bash
    pip3 install -r requirements.txt
    ```
2.  **Run the solver:**
    ```bash
    python3 solver.py
    ``` -->

## Running the Flow
- `make all` to run the whole closed loop system (OpenROAD -> Extraction -> Z3 -> Optimization). Alter which design this chooses by changing the `DESIGN_TARGET` parameter.
- `make setup` sets up the Python libraries in a virtual environment (required for later steps)
- `make run_initial_design` runs ORFS.
- `make extract_csv` generates a timing info CSV from an 6_final.odb in the results folder.
- `make convert_json` converts the CSV to JSON (`solver_input.json`) including linear regression parameters.
- `make solve` runs the Z3 solver (`main.py`) and applies resizing in OpenROAD if a valid assignment is found.
