#!/usr/bin/env python3
"""
Generate per-variant timing data for the extracted critical path.

The script reads:
  * critical_path_data.json from extract_critical_path.tcl
  * All Sky130HD liberty files (for timing tables and pin caps)
  * The design SPEF to obtain wire RC values

For each gate on the path and every drive-strength variant in the same family,
we evaluate cell delay at the fixed input slew while sweeping every NLDM load
column. The resulting CSV also carries global timing info (period/skew/setup/
hold, clock-to-q delays) plus per-net wire resistance/capacitance and
downstream input capacitance.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

PS_TO_NS = 1e-3
PF_TO_FF = 1e3


def clamp(value: float, lower: float, upper: float) -> float:
    if value < lower:
        return lower
    if value > upper:
        return upper
    return value


def find_interval(axis: List[float], value: float) -> Tuple[int, int, float]:
    if not axis:
        raise ValueError("Timing axis is empty")
    if len(axis) == 1:
        return 0, 0, 0.0
    value = clamp(value, axis[0], axis[-1])
    for idx in range(len(axis) - 1):
        low = axis[idx]
        high = axis[idx + 1]
        if low <= value <= high:
            span = high - low
            t = 0.0 if span == 0 else (value - low) / span
            return idx, idx + 1, t
    return len(axis) - 2, len(axis) - 1, 0.0


def bilinear(table: Dict[str, List], x: float, y: float) -> float:
    idx_x = table.get("index_1", [])
    idx_y = table.get("index_2", [])
    values = table.get("values", [])
    if not idx_x or not idx_y or not values:
        raise ValueError("Incomplete timing table")
    if len(idx_x) == 1 and len(idx_y) == 1:
        return values[0][0]
    if len(idx_x) == 1:
        j1, j2, ty = find_interval(idx_y, y)
        v1, v2 = values[0][j1], values[0][j2]
        return v1 + (v2 - v1) * ty
    if len(idx_y) == 1:
        i1, i2, tx = find_interval(idx_x, x)
        v1, v2 = values[i1][0], values[i2][0]
        return v1 + (v2 - v1) * tx
    i1, i2, tx = find_interval(idx_x, x)
    j1, j2, ty = find_interval(idx_y, y)
    q11 = values[i1][j1]
    q12 = values[i1][j2]
    q21 = values[i2][j1]
    q22 = values[i2][j2]
    r1 = q11 + (q12 - q11) * ty
    r2 = q21 + (q22 - q21) * ty
    return r1 + (r2 - r1) * tx


def extract_block(text: str, start_idx: int) -> Tuple[str, int]:
    brace_idx = text.find("{", start_idx)
    if brace_idx == -1:
        raise ValueError("Missing '{' in liberty block")
    depth = 0
    for idx in range(brace_idx, len(text)):
        char = text[idx]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[brace_idx + 1 : idx], idx + 1
    raise ValueError("Unterminated liberty block")


def parse_values(block: str) -> List[List[float]]:
    match = re.search(r"values\s*\(\s*(.*?)\)\s*;", block, re.IGNORECASE | re.DOTALL)
    if not match:
        return []
    rows: List[List[float]] = []
    for row_text in re.findall(r'"([^"]+)"', match.group(1)):
        rows.append([float(tok) for tok in row_text.replace(",", " ").split() if tok.strip()])
    return rows


def parse_index(block: str, keyword: str) -> List[float]:
    match = re.search(rf'{keyword}\s*\(\s*"([^"]+)"\s*\)\s*;', block, re.IGNORECASE)
    if not match:
        return []
    return [float(tok) for tok in match.group(1).replace(",", " ").split() if tok.strip()]


def parse_table(block: str, keyword: str) -> Optional[Dict[str, List]]:
    pattern = re.compile(rf"{keyword}\s*\([^{{]*\)\s*{{", re.IGNORECASE)
    match = pattern.search(block)
    if not match:
        return None
    table_block, _ = extract_block(block, match.start())
    idx1 = parse_index(table_block, "index_1")
    idx2 = parse_index(table_block, "index_2")
    values = parse_values(table_block)
    if not idx1 or not idx2 or not values:
        return None
    return {"index_1": idx1, "index_2": idx2, "values": values}


def parse_pin_block(block: str) -> Dict[str, object]:
    info: Dict[str, object] = {}
    cap_match = re.search(
        r"capacitance\s*:\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)", block, re.IGNORECASE
    )
    if cap_match:
        info["capacitance"] = float(cap_match.group(1))
    dir_match = re.search(r"direction\s*:\s*(input|output|inout)", block, re.IGNORECASE)
    if dir_match:
        info["direction"] = dir_match.group(1).lower()
    timings: List[Dict[str, object]] = []
    pattern = re.compile(r'timing\s*\([^)]*\)\s*{', re.IGNORECASE)
    pos = 0
    while True:
        match = pattern.search(block, pos)
        if not match:
            break
        timing_block, end = extract_block(block, match.start())
        timings.append(parse_timing_block(timing_block))
        pos = end
    info["timing"] = timings
    return info


def parse_pins(block: str) -> Dict[str, Dict[str, object]]:
    pins: Dict[str, Dict[str, object]] = {}
    pattern = re.compile(r'pin\s*\(\s*"([^"]+)"\s*\)\s*{', re.IGNORECASE)
    pos = 0
    while True:
        match = pattern.search(block, pos)
        if not match:
            break
        pin_name = match.group(1)
        pin_block, end = extract_block(block, match.start())
        pins[pin_name] = parse_pin_block(pin_block)
        pos = end
    return pins


def parse_timing_block(block: str) -> Dict[str, object]:
    entry: Dict[str, object] = {}
    rel = re.search(r'related_pin\s*:\s*"([^"]+)"', block, re.IGNORECASE)
    if rel:
        entry["related_pin"] = rel.group(1)
    type_match = re.search(r'timing_type\s*:\s*"([^"]+)"', block, re.IGNORECASE)
    if type_match:
        entry["timing_type"] = type_match.group(1)
    for key in ("cell_rise", "cell_fall", "rise_transition", "fall_transition"):
        table = parse_table(block, key)
        if table:
            entry[key] = table
    return entry


@dataclass
class TimingArc:
    related_pin: str
    cell_rise: Optional[Dict[str, List]]
    cell_fall: Optional[Dict[str, List]]

    def delay_ps(self, slew_ps: float, load_pf: float) -> float:
        slew_ns = slew_ps * PS_TO_NS
        delays: List[float] = []
        if self.cell_rise:
            delays.append(bilinear(self.cell_rise, slew_ns, load_pf))
        if self.cell_fall:
            delays.append(bilinear(self.cell_fall, slew_ns, load_pf))
        if not delays:
            raise ValueError("Timing arc has no rise/fall tables.")
        return max(delays) * 1e3  # convert ns to ps


class LibertyCell:
    def __init__(self, name: str, pins: Dict[str, Dict[str, object]]) -> None:
        self.name = name
        self.pins = pins

    def get_pin_cap(self, pin_name: str) -> Optional[float]:
        pin = self.pins.get(pin_name)
        if not pin:
            return None
        cap = pin.get("capacitance")
        return float(cap) if cap is not None else None

    def find_timing_arc(self, from_pin: str, to_pin: str) -> TimingArc:
        pin = self.pins.get(to_pin)
        if not pin:
            raise KeyError(f"{self.name} has no pin '{to_pin}'")
        for timing in pin.get("timing", []):
            if timing.get("related_pin") == from_pin and timing.get("cell_rise"):
                return TimingArc(
                    related_pin=from_pin,
                    cell_rise=timing.get("cell_rise"),
                    cell_fall=timing.get("cell_fall"),
                )
        raise KeyError(f"No timing arc {from_pin}->{to_pin} found in {self.name}")


class LibertyDatabase:
    def __init__(self, lib_paths: Sequence[Path]) -> None:
        if not lib_paths:
            raise ValueError("No liberty files provided.")
        self.cells: Dict[str, LibertyCell] = {}
        self.family_map: Dict[str, List[Tuple[Optional[int], str]]] = {}
        for lib_path in lib_paths:
            text = lib_path.read_text()
            for match in re.finditer(r'cell\s*\(\s*"([^"]+)"\s*\)\s*{', text):
                cell_name = match.group(1)
                if cell_name in self.cells:
                    continue
                try:
                    block, _ = extract_block(text, match.start())
                except ValueError:
                    continue
                pins = parse_pins(block)
                self.cells[cell_name] = LibertyCell(cell_name, pins)
        for cell_name in self.cells:
            base, strength = split_cell_family(cell_name)
            self.family_map.setdefault(base, []).append((strength, cell_name))
        for variants in self.family_map.values():
            variants.sort(key=lambda item: ((item[0] is None), item[0] or -1, item[1]))

    def get_cell(self, name: str) -> Optional[LibertyCell]:
        return self.cells.get(name)

    def family_variants(self, cell_name: str) -> List[str]:
        base, _ = split_cell_family(cell_name)
        entries = self.family_map.get(base, [])
        if not entries and cell_name in self.cells:
            return [cell_name]
        return [name for _, name in entries]


class SpefParser:
    """Minimal SPEF parser for wire RC + pin caps."""

    def __init__(self, spef_path: Path) -> None:
        self.lines = spef_path.read_text().splitlines()
        self.name_map: Dict[str, str] = {}
        self.net_data: Dict[str, Dict[str, object]] = {}
        self._parse()

    def _resolve(self, token: str) -> str:
        token = token.strip()
        if token.startswith("*"):
            body = token[1:]
            if ":" in body:
                idx, rest = body.split(":", 1)
                return self.name_map.get(idx, "") + ":" + rest
            return self.name_map.get(body, "")
        return token.replace("\\", "")

    def _parse(self) -> None:
        i = 0
        n = len(self.lines)
        while i < n:
            line = self.lines[i].strip()
            if not line:
                i += 1
                continue
            if line.startswith("*NAME_MAP"):
                i += 1
                while i < n:
                    entry = self.lines[i].strip()
                    if entry.startswith("*D_NET") or not entry:
                        break
                    if entry.startswith("*"):
                        parts = entry.split(None, 1)
                        if len(parts) == 2:
                            idx = parts[0][1:]
                            self.name_map[idx] = parts[1].strip().replace("\\", "")
                    i += 1
                continue
            if line.startswith("*D_NET"):
                parts = line.split()
                net_name = self._resolve(parts[1])
                total_cap = float(parts[2])
                i += 1
                conn_nodes: set[str] = set()
                pin_caps: Dict[str, float] = {}
                wire_cap = 0.0
                total_res = 0.0
                section = None
                while i < n:
                    entry = self.lines[i].strip()
                    if entry.startswith("*CONN"):
                        section = "CONN"
                        i += 1
                        continue
                    if entry.startswith("*CAP"):
                        section = "CAP"
                        i += 1
                        continue
                    if entry.startswith("*RES"):
                        section = "RES"
                        i += 1
                        continue
                    if entry.startswith("*END"):
                        i += 1
                        break
                    if section == "CONN":
                        parts = entry.split()
                        if len(parts) >= 2:
                            conn_nodes.add(self._resolve(parts[1]))
                    elif section == "CAP":
                        parts = entry.split()
                        if len(parts) == 3:
                            node = self._resolve(parts[1])
                            val = float(parts[2])
                            if node in conn_nodes:
                                pin_caps[node] = pin_caps.get(node, 0.0) + val
                            else:
                                wire_cap += val
                        elif len(parts) == 4:
                            wire_cap += float(parts[3])
                    elif section == "RES":
                        parts = entry.split()
                        if len(parts) >= 4:
                            total_res += float(parts[3])
                    i += 1
                self.net_data[net_name] = {
                    "total_cap": total_cap,
                    "wire_cap_pf": wire_cap,
                    "pin_caps": pin_caps,
                    "wire_res_ohm": total_res,
                }
                continue
            i += 1

    def net_info(self, net_name: str) -> Dict[str, object]:
        return self.net_data.get(
            net_name,
            {"total_cap": 0.0, "wire_cap_pf": 0.0, "pin_caps": {}, "wire_res_ohm": 0.0},
        )


def split_cell_family(cell_name: str) -> Tuple[str, Optional[int]]:
    match = re.match(r"^(.*)_([0-9]+)$", cell_name)
    if match:
        return match.group(1), int(match.group(2))
    return cell_name, None


def as_float(value) -> Optional[float]:
    if value in ("", None):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def stage_variants(stage: Dict[str, object], libdb: LibertyDatabase) -> List[Tuple[str, float, float]]:
    input_pin_full = stage.get("input_pin") or ""
    driver_pin = stage.get("driver_pin_name") or ""
    input_pin_name = input_pin_full.split("/")[-1] if input_pin_full else ""
    driver_pin_name = str(driver_pin)
    if not input_pin_name or not driver_pin_name:
        return []
    cell_name = str(stage.get("cell") or "")
    stage_slew_ps = as_float(stage.get("input_slew_ps")) or 0.0
    variants = libdb.family_variants(cell_name)
    data: List[Tuple[str, float, float]] = []
    for variant in variants:
        cell = libdb.get_cell(variant)
        if not cell:
            continue
        try:
            arc = cell.find_timing_arc(input_pin_name, driver_pin_name)
            load_table = arc.cell_rise or arc.cell_fall
            if not load_table:
                continue
            loads_pf = load_table.get("index_2", [])
            for load_pf in loads_pf:
                delay_ps = arc.delay_ps(stage_slew_ps, load_pf)
                data.append((variant, load_pf, delay_ps))
        except (KeyError, ValueError):
            continue
    return data


def load_json(path: Path) -> Dict[str, object]:
    with path.open() as fh:
        return json.load(fh)


def compute_downstream_cap(stage: Dict[str, object], libdb: LibertyDatabase) -> float:
    total = 0.0
    for load in stage.get("load_pins", []):
        if load.get("is_port"):
            continue
        cell = libdb.get_cell(str(load.get("cell") or ""))
        pin_name = str(load.get("pin_name") or "")
        if not cell or not pin_name:
            continue
        cap = cell.get_pin_cap(pin_name)
        if cap is None:
            continue
        total += cap * PF_TO_FF  # Liberty caps use PF units
    return total


def write_csv(rows: List[Dict[str, object]], out_path: Path) -> None:
    fieldnames = [
        "gate_index",
        "instance_name",
        "original_cell",
        "variant_cell",
        "fixed_input_slew_ps",
        "output_capacitance_fF",
        "cell_delay_ps",
        "global_T_period_ps",
        "global_T_skew_ps",
        "global_T_setup_ps",
        "global_T_hold_ps",
        "t_clk_q_max_ps",
        "t_clk_q_min_ps",
        "wire_resistance_ohm",
        "wire_capacitance_fF",
        "downstream_input_cap_fF",
        "clock_period_ps_and_freq",
        "global_slack_ps",
    ]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def build_rows(
    summary: Dict[str, object],
    stages: Sequence[Dict[str, object]],
    libdb: LibertyDatabase,
    spef: SpefParser,
) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    total_slack = as_float(summary.get("total_slack_ps"))
    t_period = as_float(summary.get("clock_period_ps"))
    t_skew = as_float(summary.get("clock_skew_ps"))
    t_setup = as_float(summary.get("t_setup_ps"))
    t_hold = as_float(summary.get("t_hold_ps"))
    clk_q_max = as_float(summary.get("clk_q_max_ps"))
    clk_q_min = as_float(summary.get("clk_q_min_ps"))
    clock_freq_hz = as_float(summary.get("clock_frequency_hz"))
    t_skew = as_float(summary.get("clock_skew_ps"))
    if (t_skew is None or t_skew == 0.0) and "launch_clock_arrival_ps" in summary and "capture_clock_arrival_ps" in summary:
        launch = as_float(summary.get("launch_clock_arrival_ps"))
        capture = as_float(summary.get("capture_clock_arrival_ps"))
        if launch is not None and capture is not None:
            t_skew = capture - launch
    clock_period_display = ""
    if t_period:
        freq_ghz = clock_freq_hz / 1e9 if clock_freq_hz else 0.0
        if freq_ghz:
            clock_period_display = f"{t_period:.3f} ps ({freq_ghz:.3f} GHz)"
        else:
            clock_period_display = f"{t_period:.3f} ps"
    for stage in stages:
        variants = stage_variants(stage, libdb)
        if not variants:
            continue
        stage_index = stage.get("stage_index")
        inst_name = stage.get("instance")
        original_cell = stage.get("cell")
        input_slew_ps = as_float(stage.get("input_slew_ps")) or 0.0
        net_name = stage.get("net", "")
        spef_info = spef.net_info(str(net_name))
        wire_cap_fF = spef_info["wire_cap_pf"] * PF_TO_FF
        wire_res = spef_info["wire_res_ohm"]
        downstream_cap_fF = compute_downstream_cap(stage, libdb)
        for variant_cell, load_pf, delay_ps in variants:
            rows.append(
                {
                    "gate_index": stage_index,
                    "instance_name": inst_name,
                    "original_cell": original_cell,
                    "variant_cell": variant_cell,
                    "fixed_input_slew_ps": input_slew_ps,
                    "output_capacitance_fF": load_pf * PF_TO_FF,
                    "cell_delay_ps": delay_ps,
                    "global_T_period_ps": t_period,
                    "global_T_skew_ps": t_skew,
                    "global_T_setup_ps": t_setup,
                    "global_T_hold_ps": t_hold,
                    "t_clk_q_max_ps": clk_q_max,
                    "t_clk_q_min_ps": clk_q_min,
                    "wire_resistance_ohm": wire_res,
                    "wire_capacitance_fF": wire_cap_fF,
                    "downstream_input_cap_fF": downstream_cap_fF,
                    "clock_period_ps_and_freq": clock_period_display,
                    "global_slack_ps": total_slack,
                }
            )
    return rows


def parse_args() -> argparse.Namespace:
    script_dir = Path(__file__).resolve().parent
    default_results = script_dir / "results" / "sky130hd" / "gcd" / "base"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--path-json",
        type=Path,
        default=default_results / "critical_path_data.json",
        help="Path to extract_critical_path.tcl JSON output.",
    )
    parser.add_argument(
        "--lib-dir",
        type=Path,
        default=script_dir / "platforms" / "sky130hd" / "lib",
        help="Directory containing Sky130HD liberty files.",
    )
    parser.add_argument(
        "--spef",
        type=Path,
        default=default_results / "6_final.spef",
        help="SPEF file for the design.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=default_results / "critical_path_variants.csv",
        help="Destination CSV path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.path_json.exists():
        raise SystemExit(f"Critical path JSON not found: {args.path_json}")
    if not args.spef.exists():
        raise SystemExit(f"SPEF file not found: {args.spef}")
    lib_paths = sorted(args.lib_dir.glob("*.lib"))
    if not lib_paths:
        raise SystemExit(f"No liberty files found in {args.lib_dir}")
    data = load_json(args.path_json)
    summary = data.get("summary")
    stages = data.get("stages")
    if not isinstance(summary, dict) or not isinstance(stages, list):
        raise SystemExit("Malformed JSON payload.")
    libdb = LibertyDatabase(lib_paths)
    spef = SpefParser(args.spef)
    rows = build_rows(summary, stages, libdb, spef)
    if not rows:
        print("[WARN] No variant rows generated.", file=sys.stderr)
    write_csv(rows, args.output)
    print(f"Wrote {len(rows)} rows to {args.output}")


if __name__ == "__main__":
    main()
