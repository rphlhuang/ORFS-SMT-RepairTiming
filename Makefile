.PHONY: all clean run_initial_design extract_csv convert_json solve

# --- Configuration ---
ORFS_FLOW_DIR := ..
DESIGN_TARGET := sky130hd/gcd
DESIGN_TARGET_CONFIG := designs/$(DESIGN_TARGET)/config.mk
OPENROAD_BIN := ../../tools/install/OpenROAD/bin/openroad
VENV_DIR := venv
VENV_BIN := $(VENV_DIR)/bin
PYTHON := $(VENV_BIN)/python3

# --- File Artifacts ---
# The final output of the standard ORFS flow (used to check if design is built)
RESULTS := $(ORFS_FLOW_DIR)/results/$(DESIGN_TARGET)/base
BASE_ODB := $(RESULTS)/6_final.odb
CSV_REPORT := critical_path_variants_reg.csv
JSON_INPUT := solver_input.json
SOLVER_OUTPUT := buffers.sol

all: solve

# Setup Python virtual environment
setup: $(VENV_DIR)
$(VENV_DIR): requirements.txt
	python3 -m venv $(VENV_DIR)
	$(VENV_BIN)/pip3 install -r requirements.txt
	touch $(VENV_DIR)

# Calls the parent ORFS Makefile if final ODB doesn't exist yet
run_initial_design: $(BASE_ODB)
$(BASE_ODB):
	@echo "--- [1/4] Running Initial OpenROAD Flow for $(DESIGN_TARGET_CONFIG) ---"
	env -u VIRTUAL_ENV PATH=$(shell echo $$PATH | sed -e 's|$(PWD)/$(VENV_BIN):||') \
	$(MAKE) -C $(ORFS_FLOW_DIR) DESIGN_CONFIG="$(DESIGN_TARGET_CONFIG)"

# Generate CSV
extract_csv: $(CSV_REPORT)
$(CSV_REPORT): $(BASE_ODB) extract_critical_path_reg.tcl
	@echo "--- [2/4] Extracting Critical Path Data ---"
	$(OPENROAD_BIN) -exit extract_critical_path_reg.tcl
	$(PYTHON) analyze_critical_path_reg.py

# Runs Python script to regress and format data
convert_json: $(JSON_INPUT)
$(JSON_INPUT): $(CSV_REPORT) csvtojson.py | $(VENV_DIR)
	@echo "--- [3/4] Converting CSV to Solver JSON ---"
	$(PYTHON) csvtojson.py

# Runs main.py
solve: $(JSON_INPUT) main.py | $(VENV_DIR)
	@echo "--- [4/4] Running SMT Optimization & Application ---"
	$(PYTHON) main.py

clean:
	rm -f $(CSV_REPORT) $(JSON_INPUT) $(SOLVER_OUTPUT)
	