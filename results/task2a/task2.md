# Task 2A: I-RRIP Design

I-RRIP has to prioritise instruction lines over data lines at L2 so that L2 instruction load MPKI goes down. The spec asks for a decision on each of insertion, promotion and eviction, and leaving one unchanged counts as a decision as long as it is justified.

## Data design choices

The L2 baseline is the SRRIP template in `replacement/rrip.l2c_repl`. It inserts new lines at a middle RRPV, fully protects a line on its first hit, and evicts a line once it has aged to the maximum RRPV. It treats every line the same way, whether it holds instructions or data.

| Cache | Policy | Insertion | Promotion | Eviction |
|---|---|---|---|---|
| L2C (template `rrip.l2c_repl`) | SRRIP-HP | RRPV = `maxRRPV-1` = 2 | Hit sets RRPV to 0 (Hit Priority) | First way at 3; if none, age the whole set and search again |

## Possible choices for instruction handling

I-RRIP starts as a copy of `rrip.l2c_repl`, and the changes go in three places:

| Lines | Function | What it decides |
|---|---|---|
| 22–30 | `l2c_find_victim` | **Eviction**: which way gets replaced, and how the set ages when no line is at `maxRRPV` |
| 70–71 | `l2c_update_replacement_state`, `if (hit)` | **Promotion**: the RRPV a line gets on a hit |
| 72–73 | `l2c_update_replacement_state`, `else` | **Insertion**: the RRPV a line gets when it's filled |

Insertion and promotion learn the line's type from the `isInstruction` parameter. Eviction reads it from `current_set[i].instruction`.

### Insertion (fill, `hit == 0`)

| Choice | Options |
|---|---|
| Which lines get a different insertion RRPV | Instructions only, data only, or both |
| Instruction insertion RRPV | Below the RRIP default of `maxRRPV-1`, so the line survives longer before it becomes a victim |
| Data insertion RRPV | Unchanged, or at `maxRRPV`, so the line is the next victim unless it's hit first |
| Distinguish fill sources with `type` | Demand `LOAD`, `PREFETCH` (from the L1D prefetcher, if one is enabled), `WRITEBACK` (dirty lines from L1D) and translation types can each get their own RRPV |

If instructions are inserted very low, the policy effectively assumes every instruction line will be reused, so one-shot code lines sit in the cache and push data out. Inserting data at `maxRRPV` resists scans, but data that is actually reused can be evicted before its second access.

### Promotion (hit, `hit == 1`)

| Choice | Options |
|---|---|
| Hit Priority vs Frequency Priority | Jump to 0 on a hit, or subtract 1 per hit |
| Per-type promotion | For example, one rule for instructions and a different one for data |
| Data promotion | Promote as in RRIP, promote only partly, or don't promote |
| Writeback hits | Promote them or not, since they aren't demand reuse |

Under Hit Priority a single hit fully protects a line. Under Frequency Priority a line needs several hits to get there, which separates lines with steady reuse from lines that are hit once. Weakening data promotion pushes the cache towards instructions even when the data does have reuse.

### Eviction (`find_victim`)

| Choice | Options |
|---|---|
| Unchanged | Take the first way at `maxRRPV`, and let insertion and promotion do all the prioritizing |
| Tie-break | Among ways at `maxRRPV`, prefer a data line over an instruction line |
| Two-pass search | Look for data at `maxRRPV` first, then instructions at `maxRRPV` |
| Asymmetric aging | Age data lines faster than instruction lines, or age only data lines |
| Strict protection | Evict a data line whenever the set has one, and evict an instruction line only if the set has no data |

Leaving eviction unchanged is the simplest option, and it keeps the effect of each RRPV choice easy to explain. The tie-break and the two-pass search only favour instructions among lines that are already victims. Asymmetric aging and strict protection bias the cache much more strongly and can starve data, which raises data MPKI. If only data lines are aged, a set holding nothing but instruction lines never produces a victim, so the `while (1)` loop needs a fallback for that case.

### Global choices

The width of the RRPV matters: 2 bits give 4 levels, and more bits leave more room to separate instruction lines from data lines. The biases from insertion, promotion and eviction also add up, so changing all three gives the strongest instruction priority and the largest risk to data MPKI. Task 2B will need to switch each set between I-RRIP and plain RRIP, which is easier if the I-RRIP rules are kept separate from the RRIP rules in the code.

## Chosen design

| Part | Choice | Rationale |
|---|---|---|
| Insertion | _TBD_ | _TBD_ |
| Promotion | _TBD_ | _TBD_ |
| Eviction | _TBD_ | _TBD_ |
