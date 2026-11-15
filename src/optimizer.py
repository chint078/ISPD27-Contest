"""ISPD 2027 Contest: MCMM Post-CTS Buffering and Sizing.

Core Optimizer Module

Architecture:
1. Load design (DEF, Verilog, LEF, Liberty)
2. Build timing graph across MCMM corners (BC, TC, WC)
3. Identify critical paths (worst negative slack)
4. Apply transformations:
   a. Gate sizing (upsize critical, downsize non-critical)
   b. Buffer insertion on high-cap / high-slew nets
   c. VT swapping (SLVT for speed, RVT/LVT for leakage)
   d. Pin swapping (equivalent pins)
5. Incremental legalization
6. Export modified DEF and Verilog
"""

import argparse
import os
import shutil
import sys
import time


def parse_args():
    parser = argparse.ArgumentParser(description="ISPD 2027 Optimizer")
    parser.add_argument("--input-dir", required=True, help="Benchmark directory")
    parser.add_argument("--platform-dir", required=True, help="Platform directory")
    parser.add_argument("--output-def", required=True, help="Output DEF path")
    parser.add_argument("--output-verilog", required=True, help="Output Verilog path")
    parser.add_argument("--top-module", required=True, help="Top module name")
    parser.add_argument("--benchmark", required=True, help="Benchmark name")
    parser.add_argument("--mode", default="heuristic", choices=["passthrough", "heuristic", "advanced"])
    return parser.parse_args()


def resolve_input_files(input_dir):
    """Find input DEF and Verilog, decompressing if necessary."""
    def_path = os.path.join(input_dir, "input.def")
    v_path = os.path.join(input_dir, "input.v")

    if not os.path.exists(def_path) and os.path.exists(def_path + ".gz"):
        import gzip
        print(f"Decompressing {def_path}.gz...")
        with gzip.open(def_path + ".gz", "rb") as f_in, open(def_path, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)

    if not os.path.exists(v_path) and os.path.exists(v_path + ".gz"):
        import gzip
        print(f"Decompressing {v_path}.gz...")
        with gzip.open(v_path + ".gz", "rb") as f_in, open(v_path, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)

    return def_path, v_path


def passthrough_optimization(input_def, input_v, output_def, output_v):
    """Copy inputs to outputs (baseline passthrough)."""
    print(f"Copying {input_def} -> {output_def}")
    shutil.copy2(input_def, output_def)
    print(f"Copying {input_v} -> {output_v}")
    shutil.copy2(input_v, output_v)


def run_heuristic_optimization(args, input_def, input_v):
    """Placeholder for heuristic optimization engine.

    Will be implemented in Phase 1 (Alpha):
    - Parse DEF/Verilog
    - Load timing via OpenSTA
    - Find critical path cells
    - Upsize drivers on critical path
    - Re-legalize
    """
    print("Running heuristic optimization...")
    # For now, falls back to passthrough until transforms are implemented
    passthrough_optimization(input_def, input_v, args.output_def, args.output_verilog)


def main():
    start_time = time.time()
    args = parse_args()

    print(f"Starting ISPD 2027 Optimizer for {args.benchmark} ({args.top_module})")
    print(f"  Mode: {args.mode}")

    input_def, input_v = resolve_input_files(args.input_dir)
    print(f"  Input DEF: {input_def} ({os.path.getsize(input_def)} bytes)")
    print(f"  Input Verilog: {input_v} ({os.path.getsize(input_v)} bytes)")

    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.output_def), exist_ok=True)
    os.makedirs(os.path.dirname(args.output_verilog), exist_ok=True)

    if args.mode == "passthrough":
        passthrough_optimization(input_def, input_v, args.output_def, args.output_verilog)
    else:
        run_heuristic_optimization(args, input_def, input_v)

    elapsed = time.time() - start_time
    print(f"Optimization finished in {elapsed:.2f} seconds.")


if __name__ == "__main__":
    main()
