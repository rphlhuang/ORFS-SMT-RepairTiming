# OpenROAD Buffer Resizing with SMT

This repository contains the core logic for a formal methods final project (CSE 216 at UC Santa Cruz). The goal is to find an **optimal** set of buffer sizes for a critical timing path in a VLSI design, ensuring that both setup and hold timing constraints are met.

Instead of relying on traditional heuristics, this project models the entire timing path as a system of constraints, which is then solved by the Z3 SMT solver to find a valid, timing-aware solution.

## Architecture

The project is built as a closed-loop system that uses **OpenROAD** for real timing data and **Z3** as the formal-methods engine to find a solution.

The core architecture is as follows:
1.  **Data Extraction (OpenROAD):** Timing reports from OpenSTA are used to extract all necessary data for the critical paths: linear delay models, static timing constraints (period, skew, etc.), and capacitance values.
2.  **Constraint Generation (Python):** A Python script parses this data and generates a conjunction of constraints in the SMT-LIB format for Z3.
3.  **SMT Solving (Z3):** The Z3 solver uses its internal SAT engine to propose solutions (Boolean assignments for buffer choices) and its Theory Solver (e.g., Theory of Linear Real Arithmetic) to check if those choices are physically valid.
4.  **Implementation (TCL Conversion):** If a `sat` solution is found, it's converted into a set of Tcl commands (`resize_cell`).
5.  **Validation (OpenROAD):** The Tcl commands are run in OpenROAD to modify the design, and OpenSTA is run again to validate if timing is truly met. If it fails, the loop can be run again.


## Running the Project
1.  **Install dependencies:**
    ```bash
    pip3 install z3-solver
    ```
2.  **Run the solver:**
    ```bash
    python3 solver.py
    ```