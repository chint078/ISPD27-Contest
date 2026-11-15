#!/usr/bin/env bash
set -e

# Load conda environment with OpenROAD binaries
source /opt/miniconda3/etc/profile.d/conda.sh
conda activate base

export PATH="/opt/oss-cad-suite/bin:/install/OpenROAD/bin:/OpenROAD/build/bin:$PATH"
export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:-}:/usr/lib/x86_64-linux-gnu:/usr/local/lib:/opt/miniconda3/lib"
export OPENROAD_EXE=$(which openroad)
export KEPLER_FORMAL_EXE=$(which kepler-formal)
export YOSYS_EXE=$(which yosys)

BENCHMARK="${1:-aes}"
RUN_DIR="/workspace/results/${BENCHMARK}-submission-run"
rm -rf "$RUN_DIR"

echo "=========================================================="
echo "Running submission pipeline for: $BENCHMARK"
echo "OPENROAD_EXE: $OPENROAD_EXE"
echo "=========================================================="

python3 evaluator/run_submission.py "$BENCHMARK" "$RUN_DIR" -- bash run.sh

echo "=========================================================="
echo "Submission Completed Successfully! Summary CSV:"
echo "=========================================================="
cat "$RUN_DIR/evaluation/summary.csv"

echo "=========================================================="
echo "Legality Validation:"
echo "=========================================================="
cat "$RUN_DIR/evaluation/legality.json"

echo "=========================================================="
echo "Computing Official Score:"
echo "=========================================================="
python3 evaluator/score.py \
  --baseline "evaluator/reference_results/${BENCHMARK}/baseline.csv" \
  --candidate "$RUN_DIR/evaluation/summary.csv" \
  --reference "evaluator/reference_results/${BENCHMARK}/resizer.csv" \
  --runtimes "$RUN_DIR/evaluation/runtimes.json" \
  --output "$RUN_DIR/evaluation/score.json"

cat "$RUN_DIR/evaluation/score.json"
