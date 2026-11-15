#!/usr/bin/env bash
set -e

# Setup environment as defined in container's entrypoint
source /opt/miniconda3/etc/profile.d/conda.sh || true
export PATH="/opt/oss-cad-suite/bin:/install/OpenROAD/bin:/OpenROAD/build/bin:$PATH"
export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:-}:/usr/lib/x86_64-linux-gnu:/usr/local/lib:/opt/miniconda3/lib"
export OPENROAD_EXE=/OpenROAD/build/bin/openroad
export KEPLER_FORMAL_EXE=/usr/local/bin/kepler-formal
export YOSYS_EXE=/opt/oss-cad-suite/bin/yosys

echo "OpenROAD executable: $(which openroad)"
echo "Kepler-formal: $(which kepler-formal)"
echo "Yosys: $(which yosys)"
echo "Python: $(which python3)"

# Execute requested benchmark or default to aes
BENCHMARK="${1:-aes}"
RUN_DIR="/tmp/${BENCHMARK}-baseline"

rm -rf "$RUN_DIR"
echo "Starting evaluation on $BENCHMARK at $RUN_DIR..."
bash evaluator/eval.sh "$BENCHMARK" "$RUN_DIR"
echo "Evaluation completed successfully! Results summary:"
cat "$RUN_DIR/evaluation/summary.csv"
