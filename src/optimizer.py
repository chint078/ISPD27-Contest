"""ISPD 2027 Contest: MCMM Post-CTS Buffering and Sizing.

Heuristic Optimizer Module (v1)
Performs contest-legal standard cell sizing transformations to close timing.
"""

import argparse
import os
import re
import shutil
import sys
import time
from cell_library import CellLibrary


def parse_args():
    parser = argparse.ArgumentParser(description="ISPD 2027 Optimizer")
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


def apply_sample_legal_resizing(input_def, input_v, output_def, output_v):
    """Applies valid cell resizing using our CellLibrary to create a legal transformed design."""
    lib = CellLibrary()
    swaps = {}

    # Read Verilog and identify movable non-clock standard cells to size
    with open(input_v, "r", encoding="utf-8") as f:
        v_lines = f.readlines()

    modified_v_lines = []
    # Match instance lines like: AND2x2_ASAP7_75t_R _1234_ ( ...
    inst_pattern = re.compile(r"^\s*([A-Za-z0-9_]+)\s+([A-Za-z0-9_\\\[\]]+)\s*\(")

    cells_modified = 0
    max_to_modify = 50  # modify a legal subset for v1 test

    for line in v_lines:
        m = inst_pattern.match(line)
        if m and cells_modified < max_to_modify:
            master = m.group(1)
            inst_name = m.group(2)
            # Check if this cell has legal upsize or equivalent replacements
            upsizes = lib.get_upsize_candidates(master)
            if upsizes and not master.startswith("DFF") and not master.startswith("ICG"):
                new_master = upsizes[0]
                swaps[inst_name] = (master, new_master)
                line = line.replace(master, new_master, 1)
                cells_modified += 1
        modified_v_lines.append(line)

    with open(output_v, "w", encoding="utf-8") as f:
        f.writelines(modified_v_lines)

    print(f"Applied legal sizing to {len(swaps)} instances in Verilog.")

    # Apply corresponding master changes in DEF COMPONENTS section
    with open(input_def, "r", encoding="utf-8") as f:
        def_lines = f.readlines()

    modified_def_lines = []
    # DEF component line format: - inst_name master_name + PLACED ( x y ) ...
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

    print(f"DEF updated with matching masters.")


def main():
    start_time = time.time()
    args = parse_args()

    print(f"Running ISPD 2027 Optimizer on {args.benchmark} ({args.top_module})")
    input_def, input_v = resolve_input_files(args.input_dir)

    os.makedirs(os.path.dirname(args.output_def), exist_ok=True)
    os.makedirs(os.path.dirname(args.output_verilog), exist_ok=True)

    apply_sample_legal_resizing(input_def, input_v, args.output_def, args.output_verilog)
    print(f"Optimization finished in {time.time() - start_time:.2f} seconds.")


if __name__ == "__main__":
    main()
