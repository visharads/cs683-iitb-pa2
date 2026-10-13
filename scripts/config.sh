# Matches the PA2 repo README and build_champsim.sh
BUILD_TEMPLATE="./build_champsim.sh @L1D@ lru t1"
BIN_TEMPLATE="bin/hashed_perceptron-no-@L1D@-no-no-no-no-no-lru-lru-lru-lru-lru-lru-lru-lru-1core-t1"
RUN_TEMPLATE="@BIN@ -warmup_instructions 25000000 -simulation_instructions 25000000 -traces @TRACE@"

TRACE_DIR="${TRACE_DIR:-traces}"
RESULT_DIR="${RESULT_DIR:-results/task1}"
JOBS="${JOBS:-$(nproc)}"
