"""Summarise the throttle sweep: geomean speedup, mean accuracy and coverage per variant."""
import sys, glob, os, re
from parse_results import load, metrics, geomean
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

d = sys.argv[1] if len(sys.argv) > 1 else "results/task1_sweep"
base = load("results/task1", "no")
rows = []
for cfg in sorted(os.listdir(d)):
    if not os.path.isdir(f"{d}/{cfg}"):
        continue
    m = metrics(base, load(d, cfg))
    if m:
        hist = np.zeros(4, dtype=int)
        for f in glob.glob(f"{d}/{cfg}/*.txt"):
            h = re.search(r"SPP epochs at degree 1/2/3/4: (\d+)/(\d+)/(\d+)/(\d+)", open(f).read())
            if h:
                hist += [int(x) for x in h.groups()]
        rows.append((cfg, geomean([r["speedup"] for r in m]), np.mean([r["accuracy_pct"] for r in m]), np.mean([r["coverage_pct"] for r in m]), "/".join(map(str, hist))))
with open(f"{d}/sweep_table.md", "w") as f:
    f.write("| Variant | Geomean speedup | Mean accuracy % | Mean coverage % | Epochs at degree 1/2/3/4 |\n|---|---|---|---|---|\n")
    for c, s, a, v, h in rows:
        f.write(f"| {c} | {s:.4f} | {a:.1f} | {v:.1f} | {h} |\n")
print(open(f"{d}/sweep_table.md").read())
fig, ax = plt.subplots(figsize=(8, 4))
ax.bar([r[0].replace("spp_", "") for r in rows], [r[1] for r in rows], edgecolor="gray")
ax.axhline(1.0, color="red", ls="--", lw=1)
lo, hi = min(r[1] for r in rows), max(r[1] for r in rows)
ax.set_ylim(min(0.995, lo - 0.002), hi + 0.004)
ax.set_ylabel("Geomean speedup")
ax.set_title("SPP throttle sweep (thresholds T1_T2_T3, fixed degrees d1/d2/d4)")
plt.xticks(rotation=30, ha="right")
fig.tight_layout()
os.makedirs("plots/task1", exist_ok=True)
fig.savefig("plots/task1/sweep.png", dpi=160)
