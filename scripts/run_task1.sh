#!/bin/bash
# Usage: scripts/run_task1.sh [prefetcher ...]   (default: no ip_stride spp)
set -e
cd "$(dirname "$0")/.."
source scripts/config.sh
CFGS=("$@")
[ ${#CFGS[@]} -eq 0 ] && CFGS=(no ip_stride spp)

fill() { echo "$1" | sed "s|@L1D@|$2|g; s|@BIN@|$3|g; s|@TRACE@|$4|g"; }

for cfg in "${CFGS[@]}"; do
    echo "== build $cfg"
    eval "$(fill "$BUILD_TEMPLATE" "$cfg")" > "build_$cfg.log" 2>&1 || { tail -30 "build_$cfg.log"; exit 1; }
    BIN=$(fill "$BIN_TEMPLATE" "$cfg")
    cp "$BIN" "bin/_task1_$cfg"
    mkdir -p "$RESULT_DIR/$cfg"
done

jobs_file=$(mktemp)
for cfg in "${CFGS[@]}"; do
    for t in "$TRACE_DIR"/*; do
        name=$(basename "$t"); name=${name%%.*}
        out="$RESULT_DIR/$cfg/$name.txt"
        [ -s "$out" ] && grep -q "Region of Interest" "$out" && continue
        echo "$(fill "$RUN_TEMPLATE" "$cfg" "bin/_task1_$cfg" "$t") > $out 2>&1" >> "$jobs_file"
    done
done
echo "== running $(wc -l < "$jobs_file") simulations with $JOBS jobs"
xargs -P "$JOBS" -I{} bash -c "{}" < "$jobs_file"
rm -f "$jobs_file"
echo "done: $RESULT_DIR"
