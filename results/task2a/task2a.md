# Task 2A: I-RRIP Design

I-RRIP must give priority to instruction lines over data lines at L2. The goal is to decrease the L2 instruction load MPKI. The spec tells you to make a decision for insertion, promotion and eviction. If you keep one of them unchanged, that is also a decision, but you must give a reason for it.

## Data design choices

The L2 baseline is the SRRIP template in `replacement/rrip.l2c_repl`. This policy inserts a new line at a middle RRPV. On the first hit, it gives the line full protection. When the RRPV of a line increases to the maximum value, the policy evicts that line. The policy uses the same rules for all lines, for instruction lines and for data lines.

| Cache | Policy | Insertion | Promotion | Eviction |
|---|---|---|---|---|
| L2C (template `rrip.l2c_repl`) | SRRIP-HP | RRPV = `maxRRPV-1` = 2 | A hit sets the RRPV to 0 (Hit Priority) | Select the first way at 3. If there is no way at 3, increase the RRPV of all lines in the set and search again |

## Possible choices for instruction handling

I-RRIP starts as a copy of `rrip.l2c_repl`. You must make the changes in three locations:

| Lines | Function | What it controls |
|---|---|---|
| 22–30 | `l2c_find_victim` | **Eviction**: the way that the policy replaces, and how the RRPVs in the set increase when no line is at `maxRRPV` |
| 70–71 | `l2c_update_replacement_state`, `if (hit)` | **Promotion**: the RRPV that a line gets on a hit |
| 72–73 | `l2c_update_replacement_state`, `else` | **Insertion**: the RRPV that a line gets when the cache fills it |

For insertion and promotion, the `isInstruction` parameter gives the type of the line. For eviction, `current_set[i].instruction` gives the type of the line.

### Insertion (fill, `hit == 0`)

| Choice | Options |
|---|---|
| The lines that get a different insertion RRPV | Instruction lines only, data lines only, or both |
| Instruction insertion RRPV | A value less than the RRIP default of `maxRRPV-1`. The line then stays in the cache for a longer time before it becomes a victim |
| Data insertion RRPV | No change, or `maxRRPV`. At `maxRRPV`, the line is the next victim if it does not get a hit first |
| Use `type` to identify the fill source | Demand `LOAD`, `PREFETCH` (from the L1D prefetcher, if it is on), `WRITEBACK` (dirty lines from L1D) and translation types can each have a different RRPV |

If you insert instruction lines at a very low RRPV, the policy expects that the cache will use each instruction line again. Thus, instruction lines that the program uses only one time stay in the cache, and they cause the eviction of data lines. If you insert data lines at `maxRRPV`, the cache has better resistance to scans. But the cache can evict a data line that the program uses again before the second access occurs.

### Promotion (hit, `hit == 1`)

| Choice | Options |
|---|---|
| Hit Priority or Frequency Priority | Set the RRPV to 0 on a hit, or decrease the RRPV by 1 on each hit |
| Promotion for each type | For example, one rule for instruction lines and a different rule for data lines |
| Data promotion | Promote as in RRIP, promote by a smaller quantity, or do not promote |
| Writeback hits | Promote them or do not promote them. A writeback hit is not a demand reuse |

With Hit Priority, one hit gives a line full protection. With Frequency Priority, a line must get many hits to get full protection. Thus, Frequency Priority can identify the lines that the program uses frequently and the lines that get only one hit. If you decrease the data promotion, the cache gives more priority to instruction lines. This occurs also when the program uses the data lines again.

### Eviction (`find_victim`)

| Choice | Options |
|---|---|
| No change | Select the first way at `maxRRPV`. Insertion and promotion then do all the work of priority |
| Tie-break | If many ways are at `maxRRPV`, select a data line before an instruction line |
| Two-pass search | First, search for a data line at `maxRRPV`. Then, search for an instruction line at `maxRRPV` |
| Asymmetric aging | Increase the RRPV of data lines faster than the RRPV of instruction lines, or increase the RRPV of data lines only |
| Strict protection | If the set has a data line, evict a data line. Evict an instruction line only if the set has no data lines |

The "no change" option is the simplest option. With it, it is easy to explain the effect of each RRPV choice. The tie-break and the two-pass search give priority to instruction lines only among the lines that are already victims. Asymmetric aging and strict protection give a much larger priority to instruction lines. These two options can cause the cache to remove too many data lines, and the data MPKI then increases. If the policy increases the RRPV of data lines only, a set that has only instruction lines never gives a victim. Thus, the `while (1)` loop must have a fallback for this condition.

### Global choices

The number of RRPV bits is important. With 2 bits, there are 4 levels. With more bits, there are more levels to separate instruction lines from data lines. The effects of insertion, promotion and eviction also add together. If you change all three, instruction lines get the largest priority, but the risk to the data MPKI is also the largest. In Task 2B, the policy must change each set between I-RRIP and plain RRIP. This is easier if the code keeps the I-RRIP rules separate from the RRIP rules.

## Chosen design

| Part | Choice | Rationale |
|---|---|---|
| Insertion | _TBD_ | _TBD_ |
| Promotion | _TBD_ | _TBD_ |
| Eviction | _TBD_ | _TBD_ |

## Test run

Use these commands from the repository root to make a short test of the baseline. The default compiler, GCC 13, makes a binary that stops with a crash at the first page fault, because `PAGE_TABLE_WALKER::handle_page_fault` has no `return` statement. Thus, you must build with GCC 7.

### 1. Build the baseline binary

```bash
CXX=g++-7 ./build_champsim.sh no rrip srrip
```

`CXX=g++-7` tells the Makefile to use GCC 7 for this command only. `no` sets no L1D prefetcher. `rrip` selects `replacement/rrip.l2c_repl` (SRRIP) as the L2 replacement policy. `srrip` is the last part of the binary name. For each I-RRIP variant, use `irrip` and a new name.

### 2. Keep the binary path in a variable

```bash
BIN=bin/hashed_perceptron-no-no-no-no-no-no-no-lru-lru-lru-rrip-lru-lru-lru-lru-1core-srrip
```

This variable is only for the current terminal.

### 3. Run a short test

```bash
$BIN -warmup_instructions 1000000 -simulation_instructions 1000000 \
  -traces ../traces/trace1.champsimtrace.gz > results/task2a/test_trace1.txt
```

The warmup fills the caches and the predictors, but ChampSim does not count statistics for it. ChampSim counts statistics only for the simulation instructions. ChampSim decompresses the `.gz` trace. The full runs use `25000000` for the two values.

### 4. Get the metrics

```bash
grep -E "^CPU 0 cumulative IPC|L2C (INSTRUCTION|DATA) LOAD MPKI" results/task2a/test_trace1.txt
```

| Trace | Instructions (warmup / sim) | IPC | L2C instruction load MPKI | L2C data load MPKI |
|---|---|---|---|---|
| trace1 | 1M / 1M | 0.228816 | 6.244 | 11.245 |

IPC is the number of instructions for each cycle. A higher value is better. The L2C instruction load MPKI is the number of instruction misses at L2 for each 1000 instructions. I-RRIP must decrease this value. The L2C data load MPKI is the same value for data misses. Make sure that it does not increase too much. These values only show that the setup operates correctly. They are not the baseline results.

## Baseline results

The baseline is SRRIP (`replacement/rrip.l2c_repl`) with no L1D prefetcher. Each run has 25M warmup instructions and 25M simulation instructions. The three runs operated in parallel with the commands below.

```bash
BIN=bin/hashed_perceptron-no-no-no-no-no-no-no-lru-lru-lru-rrip-lru-lru-lru-lru-1core-srrip
for t in 1 2 3; do
  $BIN -warmup_instructions 25000000 -simulation_instructions 25000000 \
    -traces ../traces/trace$t.champsimtrace.gz > results/task2a/srrip_trace$t.txt 2>&1 &
done
wait
for t in 1 2 3; do
  grep -E "^CPU 0 cumulative IPC|L2C (INSTRUCTION|DATA) LOAD MPKI" results/task2a/srrip_trace$t.txt
done
```

| Trace | IPC | L2C instruction load MPKI | L2C data load MPKI |
|---|---|---|---|
| trace1 | 0.232213 | 10.5632 | 7.05572 |
| trace2 | 0.251848 | 17.9797 | 8.03228 |
| trace3 | 0.381574 | 1.1904 | 2.84644 |

The full output of each run is in `results/task2a/srrip_traceN.txt`. Compare each I-RRIP variant with these values.

## Insertion variants

Each variant changes one insertion RRPV and keeps `maxRRPV` = 3. The name `iXdY` gives the instruction insertion RRPV (X) and the data insertion RRPV (Y). The baseline is `i2d2`. Promotion and eviction are the same as in SRRIP. For each variant, only line 73 of `irrip.l2c_repl` changes:

| Variant | Line 73 |
|---|---|
| `i1d2` | `l2_rrpv[set][way] = isInstruction ? 1 : maxRRPV-1;` |
| `i0d2` | `l2_rrpv[set][way] = isInstruction ? 0 : maxRRPV-1;` |
| `i2d3` | `l2_rrpv[set][way] = isInstruction ? maxRRPV-1 : maxRRPV;` |

Each variant was built from a temporary copy of `irrip.l2c_repl`, one build at a time. Then all nine runs (25M warmup, 25M simulation) operated in parallel. The full output of each run is in `results/task2a/{i1,i0,d3}_traceN.txt` (`i1` is `i1d2`, `i0` is `i0d2` and `d3` is `i2d3`).

```bash
for v in i1 i0 d3; do CXX=g++-7 ./build_champsim.sh no irrip_$v $v; done
for v in i1 i0 d3; do
  BIN=bin/hashed_perceptron-no-no-no-no-no-no-no-lru-lru-lru-irrip_$v-lru-lru-lru-lru-1core-$v
  for t in 1 2 3; do
    $BIN -warmup_instructions 25000000 -simulation_instructions 25000000 \
      -traces ../traces/trace$t.champsimtrace.gz > results/task2a/${v}_trace$t.txt 2>&1 &
  done
done
wait
```

The percentages show the change from the baseline.

| Variant | Trace | IPC | L2C instruction load MPKI | L2C data load MPKI |
|---|---|---|---|---|
| `i1d2` | trace1 | 0.232311 (+0.04%) | 10.255 (-2.92%) | 7.33124 (+3.90%) |
| `i1d2` | trace2 | 0.254038 (+0.87%) | 16.1849 (-9.98%) | 8.47644 (+5.53%) |
| `i1d2` | trace3 | 0.381725 (+0.04%) | 1.11504 (-6.33%) | 2.8672 (+0.73%) |
| `i0d2` | trace1 | 0.232243 (+0.01%) | 10.141 (-4.00%) | 7.54644 (+6.95%) |
| `i0d2` | trace2 | 0.254583 (+1.09%) | 15.7326 (-12.50%) | 8.84368 (+10.10%) |
| `i0d2` | trace3 | 0.381818 (+0.06%) | 1.07744 (-9.49%) | 2.87928 (+1.15%) |
| `i2d3` | trace1 | 0.232403 (+0.08%) | 9.7054 (-8.12%) | 8.6432 (+22.50%) |
| `i2d3` | trace2 | 0.258309 (+2.57%) | 11.5506 (-35.76%) | 9.7902 (+21.89%) |
| `i2d3` | trace3 | 0.381817 (+0.06%) | 0.94956 (-20.23%) | 3.07424 (+8.00%) |

## Promotion variants on `i2d2`

Each variant changes one promotion rule. The insertion is `i2d2` (SRRIP) and the eviction is the same as in SRRIP. The name `piXdY` gives the RRPV that a hit sets for instruction lines (X) and for data lines (Y). In a name, `f` is Frequency Priority (decrease the RRPV by 1), `n` is no change on a hit, and the `w` suffix tells that writeback hits do not change the RRPV. The baseline is `pi0d0`. For each variant, only line 71 of `irrip.l2c_repl` changes (`rrpv` is `l2_rrpv[set][way]`):

| Variant | Instruction hit | Data hit | Line 71 |
|---|---|---|---|
| `pi0df` | 0 | RRPV − 1 | `rrpv = isInstruction ? 0 : (rrpv > 0 ? rrpv-1 : 0);` |
| `pi0d1` | 0 | 1 | `rrpv = isInstruction ? 0 : 1;` |
| `pi0d2` | 0 | 2 | `rrpv = isInstruction ? 0 : 2;` |
| `pi0dn` | 0 | No change | `rrpv = isInstruction ? 0 : rrpv;` |
| `pifd0` | RRPV − 1 | 0 | `rrpv = isInstruction ? (rrpv > 0 ? rrpv-1 : 0) : 0;` |
| `pi0d0w` | 0 | 0, but no change for a writeback hit | `rrpv = (type == WRITEBACK) ? rrpv : 0;` |

The build and run steps are the same as for the insertion variants, with these six names. The full output of each run is in `results/task2a/<variant>_traceN.txt`. The percentages show the change from the SRRIP baseline.

| Variant | Trace | IPC | L2C instruction load MPKI | L2C data load MPKI |
|---|---|---|---|---|
| `pi0df` | trace1 | 0.232433 (+0.09%) | 10.3128 (-2.37%) | 7.14868 (+1.32%) |
| `pi0df` | trace2 | 0.253444 (+0.63%) | 16.209 (-9.85%) | 8.48032 (+5.58%) |
| `pi0df` | trace3 | 0.381676 (+0.03%) | 1.13876 (-4.34%) | 2.84484 (-0.06%) |
| `pi0d1` | trace1 | 0.232261 (+0.02%) | 10.3159 (-2.34%) | 7.19352 (+1.95%) |
| `pi0d1` | trace2 | 0.253539 (+0.67%) | 16.0911 (-10.50%) | 8.41236 (+4.73%) |
| `pi0d1` | trace3 | 0.38163 (+0.01%) | 1.1406 (-4.18%) | 2.84496 (-0.05%) |
| `pi0d2` | trace1 | 0.232437 (+0.10%) | 10.041 (-4.94%) | 7.50376 (+6.35%) |
| `pi0d2` | trace2 | 0.255078 (+1.28%) | 14.3532 (-20.17%) | 8.8794 (+10.55%) |
| `pi0d2` | trace3 | 0.381803 (+0.06%) | 1.05784 (-11.14%) | 2.85684 (+0.37%) |
| `pi0dn` | trace1 | 0.232443 (+0.10%) | 9.94832 (-5.82%) | 7.74336 (+9.75%) |
| `pi0dn` | trace2 | 0.255539 (+1.47%) | 13.6808 (-23.91%) | 9.4134 (+17.19%) |
| `pi0dn` | trace3 | 0.381796 (+0.06%) | 1.03324 (-13.20%) | 2.88892 (+1.49%) |
| `pifd0` | trace1 | 0.232132 (-0.03%) | 10.7752 (+2.01%) | 7.0056 (-0.71%) |
| `pifd0` | trace2 | 0.249173 (-1.06%) | 20.9943 (+16.77%) | 7.72736 (-3.80%) |
| `pifd0` | trace3 | 0.381559 (-0.00%) | 1.21888 (+2.39%) | 2.84392 (-0.09%) |
| `pi0d0w` | trace1 | 0.232552 (+0.15%) | 10.2244 (-3.21%) | 7.20688 (+2.14%) |
| `pi0d0w` | trace2 | 0.25407 (+0.88%) | 15.7886 (-12.19%) | 8.0318 (-0.01%) |
| `pi0d0w` | trace3 | 0.381805 (+0.06%) | 1.09128 (-8.33%) | 2.82124 (-0.89%) |

## Promotion variants on `i2d3`

These variants use the same six promotion rules as the `i2d2` section, but the insertion is `i2d3`. Thus, line 73 of `irrip.l2c_repl` is `l2_rrpv[set][way] = isInstruction ? maxRRPV-1 : maxRRPV;` and line 71 is the same as in the `i2d2` section. The name `i2d3piXdY` gives the insertion and then the promotion. The reference for this section is `i2d3` with SRRIP promotion (the `d3` runs). The full output of each run is in `results/task2a/<variant>_traceN.txt`.

In each cell, the first percentage shows the change from `i2d3`, and the second percentage shows the change from the SRRIP baseline.

| Variant | Trace | IPC | L2C instruction load MPKI | L2C data load MPKI |
|---|---|---|---|---|
| `i2d3pi0df` | trace1 | 0.233439 (+0.45% / +0.53%) | 9.39508 (-3.20% / -11.06%) | 8.8444 (+2.33% / +25.35%) |
| `i2d3pi0df` | trace2 | 0.260688 (+0.92% / +3.51%) | 9.81336 (-15.04% / -45.42%) | 10.0963 (+3.13% / +25.70%) |
| `i2d3pi0df` | trace3 | 0.382896 (+0.28% / +0.35%) | 0.83196 (-12.38% / -30.11%) | 3.07844 (+0.14% / +8.15%) |
| `i2d3pi0d1` | trace1 | 0.232745 (+0.15% / +0.23%) | 9.48788 (-2.24% / -10.18%) | 8.81492 (+1.99% / +24.93%) |
| `i2d3pi0d1` | trace2 | 0.25994 (+0.63% / +3.21%) | 10.0656 (-12.86% / -44.02%) | 10.3356 (+5.57% / +28.68%) |
| `i2d3pi0d1` | trace3 | 0.382255 (+0.11% / +0.18%) | 0.88488 (-6.81% / -25.67%) | 3.09528 (+0.68% / +8.74%) |
| `i2d3pi0d2` | trace1 | 0.233373 (+0.42% / +0.50%) | 9.25888 (-4.60% / -12.35%) | 9.0984 (+5.27% / +28.95%) |
| `i2d3pi0d2` | trace2 | 0.261758 (+1.34% / +3.93%) | 8.87912 (-23.13% / -50.62%) | 10.72 (+9.50% / +33.46%) |
| `i2d3pi0d2` | trace3 | 0.382975 (+0.30% / +0.37%) | 0.79552 (-16.22% / -33.17%) | 3.11976 (+1.48% / +9.60%) |
| `i2d3pi0dn` | trace1 | 0.233423 (+0.44% / +0.52%) | 8.91616 (-8.13% / -15.59%) | 10.0134 (+15.85% / +41.92%) |
| `i2d3pi0dn` | trace2 | 0.262535 (+1.64% / +4.24%) | 8.36248 (-27.60% / -53.49%) | 12.3542 (+26.19% / +53.81%) |
| `i2d3pi0dn` | trace3 | 0.384727 (+0.76% / +0.83%) | 0.6356 (-33.06% / -46.61%) | 3.2746 (+6.52% / +15.04%) |
| `i2d3pifd0` | trace1 | 0.231898 (-0.22% / -0.14%) | 9.82368 (+1.22% / -7.00%) | 8.63544 (-0.09% / +22.39%) |
| `i2d3pifd0` | trace2 | 0.256254 (-0.80% / +1.75%) | 13.8596 (+19.99% / -22.92%) | 9.44776 (-3.50% / +17.62%) |
| `i2d3pifd0` | trace3 | 0.381639 (-0.05% / +0.02%) | 0.987 (+3.94% / -17.09%) | 3.06556 (-0.28% / +7.70%) |
| `i2d3pi0d0w` | trace1 | 0.233519 (+0.48% / +0.56%) | 9.388 (-3.27% / -11.13%) | 9.15728 (+5.95% / +29.79%) |
| `i2d3pi0d0w` | trace2 | 0.261237 (+1.13% / +3.73%) | 10.1043 (-12.52% / -43.80%) | 9.77392 (-0.17% / +21.68%) |
| `i2d3pi0d0w` | trace3 | 0.384282 (+0.65% / +0.71%) | 0.77096 (-18.81% / -35.24%) | 3.10524 (+1.01% / +9.09%) |
