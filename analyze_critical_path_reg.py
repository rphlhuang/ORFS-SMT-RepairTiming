#!/usr/bin/env python3
"""Variant analyzer for the register-to-register critical path."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from analyze_critical_path import (
    LibertyDatabase,
    SpefParser,
    build_rows,
    load_json,
    write_csv,
)


def resolve_spef(path: Path, json_path: Path) -> Path:
    if path.exists():
        return path
    candidates = [
        json_path.parent / "6_final.spef",
        json_path.parent / "5_route.spef",
        json_path.parent / "5_1_grt.spef",
    ]
    for cand in candidates:
        if cand.exists():
            return cand
    raise SystemExit(f"SPEF file not found (checked {', '.join(str(c) for c in candidates)})")


def parse_args() -> argparse.Namespace:
    script_dir = Path(__file__).resolve().parent
    default_results = script_dir / "results" / "sky130hd" / "gcd" / "base"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--path-json",
        type=Path,
        default=default_results / "critical_path_data_reg.json",
        help="Path to the register-to-register critical path JSON.",
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
        help="SPEF file for the routed design.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default="critical_path_variants_reg.csv",
        help="Destination CSV path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.path_json.exists():
        raise SystemExit(f"GRT critical path JSON not found: {args.path_json}")
    lib_paths = sorted(args.lib_dir.glob("*.lib"))
    if not lib_paths:
        raise SystemExit(f"No liberty files found in {args.lib_dir}")
    spef_path = resolve_spef(args.spef, args.path_json)
    data = load_json(args.path_json)
    summary = data.get("summary")
    stages = data.get("stages")
    if not isinstance(summary, dict) or not isinstance(stages, list):
        raise SystemExit("Malformed JSON payload.")
    libdb = LibertyDatabase(lib_paths)
    spef = SpefParser(spef_path)
    rows = build_rows(summary, stages, libdb, spef)
    if not rows:
        print("[WARN] No variant rows generated.", file=sys.stderr)
    write_csv(rows, args.output)
    print(f"Wrote {len(rows)} rows to {args.output}")


if __name__ == "__main__":
    main()
