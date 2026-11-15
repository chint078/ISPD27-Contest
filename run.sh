#!/usr/bin/env bash
# ==============================================================================
# ISPD 2027 Contest: MCMM Post-CTS Buffering and Sizing
# Contestant Tool Entry Point
#
# Usage:
#   run.sh <input_dir> <platform_dir> <output_dir> <top_module>
#
# Arguments:
#   $1 - input_dir:    Benchmark input directory (contains input.def, input.v, sdc/, etc.)
#   $2 - platform_dir: Technology platform directory (platform/asap7)
#   $3 - output_dir:   Directory to write output files (<name>.def and <name>.v)
#   $4 - top_module:   Top-level Verilog module name
#
# Environment variables provided by launcher:
#   INPUT_DEF, INPUT_VERILOG, OUTPUT_DEF, OUTPUT_VERILOG,
#   BENCHMARK_DIR, MCMM_CONFIG, PLATFORM_DIR, TECH_LEF,
#   ADDITIONAL_LEFS, ADDITIONAL_LIBS
# ==============================================================================

set -euo pipefail

INPUT_DIR="$1"
PLATFORM_DIR="$2"
OUTPUT_DIR="$3"
TOP_MODULE="$4"

# Derive benchmark name: replace '/' with '_' in the benchmark path relative to benchmarks/
BENCHMARK_NAME=$(basename "$INPUT_DIR")
# If it's a scan benchmark (inside a scan/ dir), name is <parent>_scan
PARENT_DIR=$(basename "$(dirname "$INPUT_DIR")")
if [ "$BENCHMARK_NAME" = "scan" ]; then
    BENCHMARK_NAME="${PARENT_DIR}_scan"
fi

# Ensure output directory exists
mkdir -p "$OUTPUT_DIR"

OUTPUT_DEF="${OUTPUT_DEF:-$OUTPUT_DIR/${BENCHMARK_NAME}.def}"
OUTPUT_VERILOG="${OUTPUT_VERILOG:-$OUTPUT_DIR/${BENCHMARK_NAME}.v}"

echo "============================================================"
echo "ISPD 2027 Optimizer"
echo "============================================================"
echo "Input Dir:      $INPUT_DIR"
echo "Platform Dir:   $PLATFORM_DIR"
echo "Output Dir:     $OUTPUT_DIR"
echo "Top Module:     $TOP_MODULE"
echo "Benchmark Name: $BENCHMARK_NAME"
echo "Output DEF:     $OUTPUT_DEF"
echo "Output Verilog: $OUTPUT_VERILOG"
echo "============================================================"

# Find Python 3
PYTHON=${PYTHON:-python3}

# Get script directory (where src/ lives)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if our Python optimizer is available
if [ -f "$SCRIPT_DIR/src/optimizer.py" ]; then
    echo "Running Python optimizer..."
    $PYTHON "$SCRIPT_DIR/src/optimizer.py" \
        --input-dir "$INPUT_DIR" \
        --platform-dir "$PLATFORM_DIR" \
        --output-def "$OUTPUT_DEF" \
        --output-verilog "$OUTPUT_VERILOG" \
        --top-module "$TOP_MODULE" \
        --benchmark "$BENCHMARK_NAME"
else
    # Fallback: copy input as-is (passthrough mode for pipeline testing)
    echo "WARNING: src/optimizer.py not found. Running in passthrough mode."
    INPUT_DEF_FILE="${INPUT_DEF:-$INPUT_DIR/input.def}"
    INPUT_V_FILE="${INPUT_VERILOG:-$INPUT_DIR/input.v}"

    if [ ! -f "$INPUT_DEF_FILE" ] && [ -f "${INPUT_DEF_FILE}.gz" ]; then
        echo "Decompressing $INPUT_DEF_FILE.gz..."
        gunzip -k "${INPUT_DEF_FILE}.gz"
    fi
    if [ ! -f "$INPUT_V_FILE" ] && [ -f "${INPUT_V_FILE}.gz" ]; then
        echo "Decompressing $INPUT_V_FILE.gz..."
        gunzip -k "${INPUT_V_FILE}.gz"
    fi

    cp "$INPUT_DEF_FILE" "$OUTPUT_DEF"
    cp "$INPUT_V_FILE" "$OUTPUT_VERILOG"
fi

# Verify outputs were created
if [ ! -f "$OUTPUT_DEF" ]; then
    echo "ERROR: Output DEF not created: $OUTPUT_DEF" >&2
    exit 1
fi
if [ ! -f "$OUTPUT_VERILOG" ]; then
    echo "ERROR: Output Verilog not created: $OUTPUT_VERILOG" >&2
    exit 1
fi

echo "Successfully generated:"
echo "  $OUTPUT_DEF ($(wc -c < "$OUTPUT_DEF") bytes)"
echo "  $OUTPUT_VERILOG ($(wc -c < "$OUTPUT_VERILOG") bytes)"
echo "Optimization complete."
