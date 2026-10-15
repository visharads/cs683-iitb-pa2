#!/usr/bin/env python3
# Task 3 tables and plots. Run from the repository root:
#   python3 results/task3/final/make_task3_report.py
import math, re, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = "results/task3/final"
TRACES = [1, 2, 3]

def read(path):
    s = open(path).read()
    g = lambda pat: float(re.search(pat, s, re.M).group(1))
    d = {"ipc": g(r"^CPU 0 cumulative IPC: ([\d.]+)"),
         "l1d_miss": g(r"^L1D LOAD\s+ACCESS:.*MISS:\s+(\d+)"),
         "l1d": g(r"^L1D LOAD\s+ACCESS:.*MPKI: ([\d.]+)"),
         "l2c": g(r"^L2C LOAD\s+ACCESS:.*MPKI: ([\d.]+)"),
         "l2i": g(r"^L2C INSTRUCTION LOAD MPKI: ([\d.]+)"),
         "l2d": g(r"^L2C DATA LOAD MPKI: ([\d.]+)")}
    m = re.search(r"^L1D USEFUL LOAD PREFETCHES:.*ACCURACY: ([\d.]+)", s, re.M)
    d["acc"] = float(m.group(1)) if m else None
    return d

def runs(prefix):
    return [read(f"{prefix}_trace{t}.txt") for t in TRACES]

gmean = lambda xs: math.exp(sum(math.log(x) for x in xs) / len(xs))
amean = lambda xs: sum(xs) / len(xs)

# policies: (label, output prefix, uses SPP)
POL = [("RRIP (no prefetcher)", "results/task2a/srrip", False),
       ("Dynamic I-RRIP (no prefetcher)", "results/task2b/dyn_irrip", False),
       ("SPP + RRIP", "results/task3/spp_srrip", True),
       ("SPP + Task 3", "results/task3/task3_final", True)]
base = runs(POL[0][1])
data = {}
for name, pre, spp in POL:
    r = runs(pre)
    for i in range(3):
        r[i]["speedup"] = r[i]["ipc"] / base[i]["ipc"]
        # coverage: L1D load misses removed, relative to RRIP without a prefetcher
        r[i]["cov"] = (base[i]["l1d_miss"] - r[i]["l1d_miss"]) / base[i]["l1d_miss"] * 100 if spp else None
        if not spp:
            r[i]["acc"] = None
    data[name] = r

METRICS = [("ipc", "IPC", "gmean"), ("speedup", "Speedup over RRIP", "gmean"),
           ("acc", "L1D prefetch accuracy (%)", "amean"), ("cov", "L1D prefetch coverage (%)", "amean"),
           ("l1d", "L1D load MPKI", "gmean"), ("l2c", "L2C load MPKI", "gmean"),
           ("l2i", "L2C instruction load MPKI", "gmean"), ("l2d", "L2C data load MPKI", "gmean")]

def mean_of(name, k, how):
    vals = [data[name][i][k] for i in range(3)]
    if vals[0] is None:
        return None
    return gmean(vals) if how == "gmean" else amean(vals)

# ---------- tables ----------
fmt = lambda v, k: "-" if v is None else (f"{v:.6f}" if k == "ipc" else (f"{v:.2f}" if k in ("acc", "cov") else f"{v:.4f}"))
lines = ["Task 3: SPP-aware dynamic I-RRIP (replacement/dyn_irrip_task3.l2c_repl) with the SPP L1D prefetcher",
         "25M warmup + 25M simulation instructions per trace.",
         "Speedup = IPC / IPC of RRIP (SRRIP) without a prefetcher, on the same trace.",
         "Accuracy = ChampSim L1D 'USEFUL LOAD PREFETCHES ... ACCURACY' (useful / issued to lower level).",
         "Coverage = (L1D load misses of RRIP without a prefetcher - L1D load misses with SPP) / L1D load misses of RRIP without a prefetcher.",
         "Mean: geometric mean for IPC, speedup and MPKI; arithmetic mean for accuracy and coverage.",
         ""]
header = ["Policy"] + [m[1] for m in METRICS]
for title, idx in [("trace1", 0), ("trace2", 1), ("trace3", 2), ("Mean over the 3 traces", None)]:
    lines.append(f"== {title} ==")
    rows = [header]
    for name, _, _ in POL:
        if idx is None:
            vals = [mean_of(name, k, how) for k, _, how in METRICS]
        else:
            vals = [data[name][idx][k] for k, _, _ in METRICS]
        rows.append([name] + [fmt(v, k) for v, (k, _, _) in zip(vals, METRICS)])
    widths = [max(len(r[c]) for r in rows) for c in range(len(header))]
    for r in rows:
        lines.append("  ".join(cell.ljust(w) for cell, w in zip(r, widths)))
    lines.append("")
open(os.path.join(OUT, "task3_results.txt"), "w").write("\n".join(lines))
print("\n".join(lines))

# ---------- plots ----------
COL = {"RRIP (no prefetcher)": "#8a8984", "Dynamic I-RRIP (no prefetcher)": "#2a78d6",
       "SPP + RRIP": "#1baf7a", "SPP + Task 3": "#eb6834"}
INK, INK2, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#8a8984", "#e6e5e0", "#fcfcfb"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": MUTED, "axes.labelcolor": INK2,
                     "xtick.color": INK2, "ytick.color": INK2, "axes.titlecolor": INK,
                     "figure.facecolor": SURF, "axes.facecolor": SURF})
groups = ["trace1", "trace2", "trace3", "Mean"]
for k, label, how in METRICS:
    pols = [n for n, _, _ in POL if data[n][0][k] is not None]
    fig, ax = plt.subplots(figsize=(7, 3.4))
    w = 0.8 / len(pols)
    for j, name in enumerate(pols):
        ys = [data[name][i][k] for i in range(3)] + [mean_of(name, k, how)]
        xs = [x + (j - (len(pols) - 1) / 2) * w for x in range(4)]
        ax.bar(xs, ys, width=w - 0.03, color=COL[name], label=name)
    ax.set_xticks(range(4))
    ax.set_xticklabels(groups)
    ax.set_ylabel(label)
    ax.set_title(label + (" (mean: geometric)" if how == "gmean" else " (mean: arithmetic)"), fontsize=10)
    if k in ("ipc", "speedup"):
        lo = min(min(data[n][i][k] for i in range(3)) for n in pols)
        ax.set_ylim(lo * (0.9 if k == "ipc" else 0.99), None)
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.legend(frameon=False, fontsize=8, ncol=2, loc="upper left", bbox_to_anchor=(0, -0.12))
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, f"task3_{k}.png"), dpi=150)
    plt.close(fig)
print("wrote plots to", OUT)
