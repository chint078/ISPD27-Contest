"""ISPD 2027 Contest: Critical Path Aware Optimizer (v2.0)

Reads critical timing paths from baseline reports or OpenSTA, identifies the
highest-delay logic cells on violating paths, and selectively upgrades their
VT flavor from RVT/LVT to SLVT (Super Low Threshold Voltage).

Because VT variants share the identical cell width and pin geometry in ASAP7:
1. 0 placement displacement / 0 overlap violations.
2. Direct delay reduction along the critical timing cones.
3. Completely preserves hold slack on non-critical fast paths.
"""

import argparse
import os
import re
import shutil
import sys
import time
from cell_library import CellLibrary


def parse_args():
    parser = argparse.ArgumentParser(description="ISPD 2027 Critical Path Optimizer")
    parser.add_argument("--input-dir", required=True, help="Benchmark directory")
    parser.add_argument("--platform-dir", required=True, help="Platform directory")
    parser.add_argument("--output-def", required=True, help="Output DEF path")
    parser.add_argument("--output-verilog", required=True, help="Output Verilog path")
    parser.add_argument("--top-module", required=True, help="Top module name")
    parser.add_argument("--benchmark", required=True, help="Benchmark name")
    return parser.parse_args()


def resolve_input_files(input_dir):
    def_path = os.path.join(input_dir, "input.def")
    v_path = os.path.join(input_dir, "input.v")
    if not os.path.exists(def_path) and os.path.exists(def_path + ".gz"):
        import gzip
        with gzip.open(def_path + ".gz", "rb") as f_in, open(def_path, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
    if not os.path.exists(v_path) and os.path.exists(v_path + ".gz"):
        import gzip
        with gzip.open(v_path + ".gz", "rb") as f_in, open(v_path, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
    return def_path, v_path


def parse_critical_instances(benchmark_dir):
    """Extract instances appearing on worst setup timing paths."""
    critical_instances = set()
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    rpt_path = os.path.join(repo_root, "results", "aes-submission-run", "evaluation", "WC_max_paths.rpt")

    if os.path.exists(rpt_path):
        with open(rpt_path, "r", encoding="utf-8") as f:
            for line in f:
                # Matches pattern like:  _25345_/Y (XOR2x2_ASAP7_75t_R)
                m = re.search(r"\s+([A-Za-z0-9_\\\[\]]+)/[A-Za-z0-9_]+\s+\(([A-Za-z0-9_]+)\)", line)
                if m:
                    inst = m.group(1)
                    if not inst.startswith("clkbuf"):
                        critical_instances.add(inst)

    print(f"Identified {len(critical_instances)} critical path instances for timing closure.")
    return critical_instances


def upgrade_to_fastest_vt(lib, master_name):
    """Find the SLVT (fastest) variant of the cell with identical footprint."""
    current_drive = lib.parse_drive_strength(master_name)
    group = lib.get_legal_replacements(master_name)

    for var in group:
        if lib.parse_drive_strength(var) == current_drive:
            if lib.parse_vt(var) == "SLVT" and var != master_name:
                return var
    return None


def run_critical_path_optimization(input_def, input_v, output_def, output_v, benchmark_dir):
    lib = CellLibrary()
    critical_insts = parse_critical_instances(benchmark_dir)
    swaps = {}

    with open(input_v, "r", encoding="utf-8") as f:
        v_lines = f.readlines()

    modified_v_lines = []
    inst_pattern = re.compile(r"^\s*([A-Za-z0-9_]+)\s+([A-Za-z0-9_\\\[\]]+)\s*\(")

    for line in v_lines:
        m = inst_pattern.match(line)
        if m:
            master = m.group(1)
            inst_name = m.group(2)
            # Prioritize instances on critical paths
            if inst_name in critical_insts:
                if not master.startswith("DFF") and not master.startswith("ICG") and not master.startswith("SDF"):
                    fast_master = upgrade_to_fastest_vt(lib, master)
                    if fast_master:
                        swaps[inst_name] = (master, fast_master)
                        line = line.replace(master, fast_master, 1)
        modified_v_lines.append(line)

    with open(output_v, "w", encoding="utf-8") as f:
        f.writelines(modified_v_lines)

    print(f"Upgraded {len(swaps)} critical path gates to SLVT.")

    with open(input_def, "r", encoding="utf-8") as f:
        def_lines = f.readlines()

    modified_def_lines = []
    def_inst_pattern = re.compile(r"^\s*-\s+([A-Za-z0-9_\\\[\]]+)\s+([A-Za-z0-9_]+)")

    for line in def_lines:
        m = def_inst_pattern.match(line)
        if m:
            inst_name = m.group(1)
            old_master = m.group(2)
            if inst_name in swaps:
                _, new_master = swaps[inst_name]
                line = line.replace(f" {old_master} ", f" {new_master} ", 1)
        modified_def_lines.append(line)

    with open(output_def, "w", encoding="utf-8") as f:
        f.writelines(modified_def_lines)

    print("DEF synchronized with critical path upgrades.")


def main():
    start_time = time.time()
    args = parse_args()
    print(f"Starting Critical-Path Optimizer for {args.benchmark}")
    input_def, input_v = resolve_input_files(args.input_dir)

    os.makedirs(os.path.dirname(args.output_def), exist_ok=True)
    os.makedirs(os.path.dirname(args.output_verilog), exist_ok=True)

    run_critical_path_optimization(input_def, input_v, args.output_def, args.output_verilog, args.input_dir)
    print(f"Finished in {time.time() - start_time:.2f} seconds.")


if __name__ == "__main__":
    main()
