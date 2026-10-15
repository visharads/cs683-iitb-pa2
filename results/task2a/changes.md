# Task 2A: Changes

## Traces
Moved to `../traces/`, renamed with `.champsimtrace.gz` (ChampSim needs the extension).
- `Trace1-002` → `trace1.champsimtrace.gz`
- `Trace2-001` → `trace2.champsimtrace.gz`
- `Trace3-003` → `trace3.champsimtrace.gz`

## `isInstruction` parameter
Added `uint8_t isInstruction` after `uint8_t hit` in `update_replacement_state`.

Declarations, `inc/cache.h`:
- function pointer `(CACHE::*update_replacement_state)`
- `base_`, `btb_`, `l1i_`, `l1d_`, `l2c_`, `llc_`, `itlb_`, `dtlb_`, `stlb_update_replacement_state`

Definitions:
- `replacement/base_replacement.cc`
- `replacement/lru.{btb,l1i,l1d,l2c,llc,itlb,dtlb,stlb}_repl`
- `replacement/rrip.l2c_repl`: already had it

Call sites, `src/cache.cc`:

| Line | Path | Argument |
|---|---|---|
| 140 | fill | `MSHR.entry[mshr_index].instruction` |
| 527 | fill | `MSHR.entry[mshr_index].instruction` |
| 819 | writeback hit | `WQ.entry[index].instruction` |
| 1080 | writeback fill | `WQ.entry[index].instruction` |
| 1766 | read hit | `RQ.entry[index].instruction` |
| 2452 | prefetch hit | `PQ.entry[index].instruction` |

Not changed: lines 559 and 1543 (`#ifdef PUSH_DTLB_PB`, disabled).

Call sites, `src/ooo_cpu.cc` (BTB): lines 432, 456 and 983, argument `0`.

## Runs
- Warmup 25M, simulation 25M.
- Traces passed as `../traces/traceN.champsimtrace.gz`.
