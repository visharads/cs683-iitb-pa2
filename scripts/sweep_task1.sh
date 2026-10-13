#!/bin/bash
# Threshold and fixed-degree sweep for the accuracy throttle. Builds spp variants and runs them.
set -e
cd "$(dirname "$0")/.."
source scripts/config.sh
SRC=prefetcher/spp.l1d_pref
variant() {
    name=$1; t1=$2; t2=$3; t3=$4; fixed=$5; rf=${6:-1}
    sed "s/^#define SPP_T1 .*/#define SPP_T1 $t1/; s/^#define SPP_T2 .*/#define SPP_T2 $t2/; s/^#define SPP_T3 .*/#define SPP_T3 $t3/; s/^#define SPP_FIXED_DEGREE .*/#define SPP_FIXED_DEGREE $fixed/; s/^#define SPP_USE_RF .*/#define SPP_USE_RF $rf/" $SRC > prefetcher/$name.l1d_pref
}
variant spp_t20_40_60 20 40 60 0
variant spp_t25_50_75 25 50 75 0
variant spp_t30_55_75 30 55 75 0
variant spp_t40_60_80 40 60 80 0
variant spp_t50_70_90 50 70 90 0
variant spp_d1 30 55 75 1
variant spp_d2 30 55 75 2
variant spp_d4 30 55 75 4
variant spp_norf 30 55 75 0 0
RESULT_DIR=results/task1_sweep scripts/run_task1.sh spp_t20_40_60 spp_t25_50_75 spp_t30_55_75 spp_t40_60_80 spp_t50_70_90 spp_d1 spp_d2 spp_d4 spp_norf