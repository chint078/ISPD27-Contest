#!/usr/bin/env bash
# ==============================================================================
# Run and evaluate all benchmarks
# ==============================================================================

set -euo pipefail

BENCHMARKS=("aes" "jpeg")
# Add large benchmarks if decompressed:
# BENCHMARKS=("aes" "jpeg" "aes/scan" "jpeg/scan" "coralnpu" "nyuzi")

TOOL_SCRIPT="${1:-run.sh}"
RESULTS_DIR="results/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$RESULTS_DIR"

echo "============================================================"
echo "Running All Benchmarks"
echo "Tool: $TOOL_SCRIPT"
echo "Results Dir: $RESULTS_DIR"
echo "============================================================"

for bench in "${BENCHMARKS[@]}"; do
    bench_clean=$(echo "$bench" | tr '/' '_')
    run_dir="/tmp/${bench_clean}-run"
    rm -rf "$run_dir"

    echo ""
    echo ">>> Running $bench..."
    python3 evaluator/run_submission.py "$bench" "$run_dir" -- bash "$TOOL_SCRIPT"

    # Score if reference results exist
    baseline_csv="evaluator/reference_results/${bench}/baseline.csv"
    resizer_csv="evaluator/reference_results/${bench}/resizer.csv"

    if [ -f "$baseline_csv" ] && [ -f "$resizer_csv" ]; then
        echo ">>> Scoring $bench..."
        python3 evaluator/score.py \
            --baseline "$baseline_csv" \
            --candidate "$run_dir/evaluation/summary.csv" \
            --reference "$resizer_csv" \
            --runtimes "$run_dir/evaluation/runtimes.json" \
            --output "$run_dir/evaluation/score.json" || true
    fi

    # Copy results
    mkdir -p "$RESULTS_DIR/$bench_clean"
    cp -r "$run_dir/evaluation"/* "$RESULTS_DIR/$bench_clean/" 2>/dev/null || true
    echo ">>> Finished $bench. Results saved to $RESULTS_DIR/$bench_clean"
done

echo ""
echo "============================================================"
echo "All benchmarks completed. Summary in $RESULTS_DIR"
echo "============================================================"
