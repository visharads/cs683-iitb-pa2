"""Parse ChampSim stats into per-trace metrics, CSV/markdown tables and plots."""
import re, sys, glob, os, csv, math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

IPC = re.compile(r"CPU 0 cumulative IPC:\s*([\d.]+)\s+instructions:\s*(\d+)\s+cycles:\s*(\d+)")
ACC = re.compile(r"^(\S+)\s+(TOTAL|LOAD|RFO|PREFETCH)\s+ACCESS:\s*(\d+)\s+HIT:\s*(\d+)\s+MISS:\s*(\d+)", re.M)
PF = re.compile(r"^(\S+)\s+PREFETCH\s+REQUESTED:\s*(\d+)\s+ISSUED:\s*(\d+)\s+USEFUL:\s*(\d+)\s+USELESS:\s*(\d+)", re.M)
ACCL = re.compile(r"^(\S+)\s+USEFUL LOAD PREFETCHES:\s*(\d+)\s+PREFETCH ISSUED TO LOWER LEVEL:\s*(\d+)", re.M)


def norm(name):
    return re.sub(r"^cpu\d+_", "", name)


def parse(path):
    txt = open(path).read()
    roi = txt.split("Region of Interest Statistics")[-1]
    m = IPC.search(roi)
    if not m:
        raise ValueError(f"no ROI IPC in {path}")
    d = {"ipc": float(m.group(1)), "instr": int(m.group(2))}
    for lvl, kind, a, h, ms in ACC.findall(roi):
        lvl = norm(lvl)
        d[f"{lvl}_{kind}_miss"] = int(ms)
        d[f"{lvl}_{kind}_acc"] = int(a)
    for lvl, req, iss, use, usl in PF.findall(roi):
        lvl = norm(lvl)
        d[f"{lvl}_pf_issued"] = int(iss)
        d[f"{lvl}_pf_useful"] = int(use)
        d[f"{lvl}_pf_useless"] = int(usl)
    for lvl, use, low in ACCL.findall(roi):
        d[f"{norm(lvl)}_acc_useful"] = int(use)
        d[f"{norm(lvl)}_acc_lower"] = int(low)
    return d


def load(base_dir, cfg):
    out = {}
    for p in sorted(glob.glob(f"{base_dir}/{cfg}/*.txt")):
        out[os.path.basename(p)[:-4]] = parse(p)
    return out


def mpki(d, lvl, kind="LOAD"):
    return d.get(f"{lvl}_{kind}_miss", 0) / (d["instr"] / 1000)


def geomean(xs):
    xs = [x for x in xs if x > 0]
    return math.exp(sum(math.log(x) for x in xs) / len(xs)) if xs else float("nan")


def metrics(base, run):
    rows = []
    for t in sorted(set(base) & set(run)):
        b, r = base[t], run[t]
        bm, rm = b.get("L1D_LOAD_miss", 0), r.get("L1D_LOAD_miss", 0)
        useful = r.get("L1D_pf_useful", 0)
        useless = r.get("L1D_pf_useless", 0)
        rows.append({
            "trace": t,
            "ipc": r["ipc"],
            "speedup": r["ipc"] / b["ipc"],
            "l1d_load_mpki": mpki(r, "L1D"),
            "base_l1d_load_mpki": mpki(b, "L1D"),
            "accuracy_pct": (100.0 * useful / (useful+useless)) if (useful + useless) > 0 else 0.0,
            "coverage_pct": 100 * (bm - rm) / bm if bm else 0.0,
        })
    return rows


def write_csv(path, rows):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def bar(ax_data, labels, series, ylabel, title, fname, baseline=None, ylim=None):
    x = np.arange(len(labels))
    w = 0.8 / len(series)
    fig, ax = plt.subplots(figsize=(max(7, len(labels) * 0.9), 4.2))
    for i, (name, vals) in enumerate(series):
        ax.bar(x + (i - (len(series) - 1) / 2) * w, vals, w, label=name, edgecolor="gray")
    if baseline is not None:
        ax.axhline(baseline, color="red", ls="--", lw=1, label="Baseline")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    if ylim:
        ax.set_ylim(*ylim)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(fname, dpi=160)
    plt.close(fig)


def main():
    base_dir = sys.argv[1] if len(sys.argv) > 1 else "results/task1"
    os.makedirs("plots/task1", exist_ok=True)
    base = load(base_dir, "no")
    cfgs = {"IP-stride": load(base_dir, "ip_stride"), "SPP": load(base_dir, "spp")}
    tables = {n: metrics(base, d) for n, d in cfgs.items() if d}
    for n, rows in tables.items():
        write_csv(f"{base_dir}/metrics_{n.lower().replace('-', '_')}.csv", rows)
    traces = [r["trace"] for r in next(iter(tables.values()))] + ["GEOMEAN"]

    def col(n, k):
        v = [r[k] for r in tables[n]]
        return v + [geomean(v) if k in ("speedup", "ipc") else float(np.mean(v))]

    bar(None, traces, [(n, col(n, "speedup")) for n in tables], "Speedup",
        "Speedup of L1D prefetchers over baseline (no prefetching)", "plots/task1/speedup.png", baseline=1.0)
    bm = [r["base_l1d_load_mpki"] for r in next(iter(tables.values()))]
    bm.append(float(np.mean(bm)))
    bar(None, traces, [("Baseline", bm)] + [(n, col(n, "l1d_load_mpki")) for n in tables], "L1D load MPKI",
        "L1D load MPKI", "plots/task1/mpki.png")
    bar(None, traces, [(n, col(n, "accuracy_pct")) for n in tables], "L1D prefetch accuracy (%)",
        "L1D prefetch accuracy", "plots/task1/accuracy.png", ylim=(0, 100))
    bar(None, traces, [(n, col(n, "coverage_pct")) for n in tables], "L1D prefetch coverage (%)",
        "L1D prefetch coverage", "plots/task1/coverage.png")

    with open(f"{base_dir}/task1_tables.md", "w") as f:
        for n, rows in tables.items():
            f.write(f"### {n}\n\n| Trace | IPC | Speedup | L1D load MPKI | Accuracy % | Coverage % |\n|---|---|---|---|---|---|\n")
            for r in rows:
                f.write(f"| {r['trace']} | {r['ipc']:.3f} | {r['speedup']:.3f} | {r['l1d_load_mpki']:.2f} | {r['accuracy_pct']:.1f} | {r['coverage_pct']:.1f} |\n")
            f.write(f"| GEOMEAN/MEAN | {geomean([r['ipc'] for r in rows]):.3f} | {geomean([r['speedup'] for r in rows]):.3f} | {np.mean([r['l1d_load_mpki'] for r in rows]):.2f} | {np.mean([r['accuracy_pct'] for r in rows]):.1f} | {np.mean([r['coverage_pct'] for r in rows]):.1f} |\n\n")
    print(open(f"{base_dir}/task1_tables.md").read())


if __name__ == "__main__":
    main()
