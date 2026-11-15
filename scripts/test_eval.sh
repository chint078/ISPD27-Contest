#!/usr/bin/env bash
source /opt/miniconda3/etc/profile.d/conda.sh
conda activate base

export PATH="/opt/oss-cad-suite/bin:/install/OpenROAD/bin:/OpenROAD/build/bin:$PATH"
export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:-}:/usr/lib/x86_64-linux-gnu:/usr/local/lib:/opt/miniconda3/lib"
export OPENROAD_EXE=$(which openroad)
export KEPLER_FORMAL_EXE=$(which kepler-formal)
export YOSYS_EXE=$(which yosys)

echo "OPENROAD_EXE is: $OPENROAD_EXE"
echo "KEPLER_FORMAL_EXE is: $KEPLER_FORMAL_EXE"

python3 -c "import shutil, os; print('Python shutil.which openroad:', shutil.which('openroad')); print('OPENROAD_EXE env:', os.environ.get('OPENROAD_EXE'))"

BENCHMARK="${1:-aes}"
RUN_DIR="/tmp/${BENCHMARK}-baseline"
rm -rf "$RUN_DIR"

python3 evaluator/internal/run.py "$BENCHMARK" "$RUN_DIR"
cat "$RUN_DIR/summary.csv"
