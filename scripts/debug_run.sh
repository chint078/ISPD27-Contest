#!/usr/bin/env bash
source /opt/miniconda3/etc/profile.d/conda.sh
conda activate base

export PATH="/opt/oss-cad-suite/bin:/install/OpenROAD/bin:/OpenROAD/build/bin:$PATH"
export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:-}:/usr/lib/x86_64-linux-gnu:/usr/local/lib:/opt/miniconda3/lib"
export OPENROAD_EXE=$(which openroad)
export KEPLER_FORMAL_EXE=$(which kepler-formal)
export YOSYS_EXE=$(which yosys)

RUN_DIR="/workspace/results/aes-debug-run"
rm -rf "$RUN_DIR"
mkdir -p "$RUN_DIR"

python3 evaluator/run_submission.py aes "$RUN_DIR" -- bash run.sh || true

if [ -f "$RUN_DIR/evaluation.log" ]; then
    echo "=== EVALUATION LOG ==="
    tail -n 100 "$RUN_DIR/evaluation.log"
elif [ -f "$RUN_DIR/tool.log" ]; then
    echo "=== TOOL LOG ==="
    cat "$RUN_DIR/tool.log"
fi
