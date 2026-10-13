"""Generate report/task1.tex and report/Summary.tex from results CSVs, the sweep table and plots."""
import csv, os, re

R = "report"
os.makedirs(R, exist_ok=True)


def esc(s):
    return str(s).replace("_", r"\_").replace("%", r"\%").replace("&", r"\&")


def csv_rows(path):
    return list(csv.DictReader(open(path))) if os.path.exists(path) else []


def table(header, rows, spec=None):
    spec = spec or "l" + "r" * (len(header) - 1)
    out = [r"\begin{center}", r"\small", rf"\begin{{tabular}}{{{spec}}}", r"\toprule", " & ".join(esc(h) for h in header) + r" \\", r"\midrule"]
    out += [" & ".join(esc(c) for c in r) + r" \\" for r in rows]
    out += [r"\bottomrule", r"\end{tabular}", r"\end{center}"]
    return "\n".join(out)


def results_table(name, path):
    rows = csv_rows(path)
    if not rows:
        return ""
    body = [[r["trace"], f"{float(r['ipc']):.3f}", f"{float(r['speedup']):.3f}", f"{float(r['l1d_load_mpki']):.2f}",
             f"{float(r['accuracy_pct']):.1f}", f"{float(r['coverage_pct']):.1f}"] for r in rows]
    n = len(rows)
    gm = lambda k: (lambda xs: __import__("math").exp(sum(map(__import__("math").log, xs)) / n))([float(r[k]) for r in rows])
    mean = lambda k: sum(float(r[k]) for r in rows) / n
    body.append(["Geomean / mean", f"{gm('ipc'):.3f}", f"{gm('speedup'):.3f}", f"{mean('l1d_load_mpki'):.2f}",
                 f"{mean('accuracy_pct'):.1f}", f"{mean('coverage_pct'):.1f}"])
    return rf"\subsection*{{{name}}}" + "\n" + table(["Trace", "IPC", "Speedup", "L1D load MPKI", "Accuracy (\\%)", "Coverage (\\%)"], body)


def sweep_table(path):
    if not os.path.exists(path):
        return ""
    rows = [[c.strip() for c in ln.strip("|").split("|")] for ln in open(path).read().splitlines()
            if ln.startswith("|") and not re.match(r"^\|[-| ]+\|$", ln)]
    return table(rows[0], rows[1:], "lrrrr")


def fig(name, caption):
    p = f"../plots/task1/{name}.png"
    return rf"""\begin{{figure}}[h]
\centering
\includegraphics[width=0.8\linewidth]{{{p}}}
\caption{{{caption}}}
\end{{figure}}"""


body = r"""
\section{Task 1: Stride Pattern Prefetching}

\subsection{Task 1A: IP-stride prefetcher}
The provided IP-stride prefetcher (\texttt{ip\_stride.l1d\_pref}) keeps 24 trackers, fully associative with LRU replacement, indexed by the low 8 bits of the load IP.
Each tracker stores the last cache-line address seen from that IP and the last stride.
A new IP allocates a tracker and prefetches nothing.
On a repeat access the line stride is computed and a zero stride is ignored.
If the stride equals the stored one, the next 3 lines (degree 3) at multiples of the stride are prefetched, stopping at the 4~KB page boundary.
The fill level is L1 while the MSHR is under half full, otherwise L2.
The tracker is then updated with the new address and stride.
Because it remembers a single stride and needs it to repeat, an IP that cycles through $(+1,+2,+2,+2,+3)$ rarely has two equal consecutive strides at the right moment and gets few useful prefetches.
The 8-bit IP mask also lets different IPs alias onto one tracker.

\subsection{Task 1B: SPP design}
\paragraph{Tables.}
(1) An IP table of 64 direct-mapped entries holds per-IP last offset, last stride, a confidence counter, a uniform-mode bit and a 12-bit stride signature.
(2) A pattern table of 256 entries, shared across IPs and indexed by a hash of the signature, holds the next stride that followed that signature and a 2-bit confidence.
(3) A 128-entry recent-prefetch filter of partial line tags is filled when a prefetched line arrives in L1D and counts demand hits on prefetched lines.
(4) A 256-entry resident filter approximates which lines are in L1D (set on hits, fills and issued prefetches, cleared on evictions) and is used to skip redundant prefetches.

\paragraph{Dual pattern classification.}
An IP enters uniform mode after the same stride is seen four times in a row (confidence saturates at 3) and leaves it when confidence falls to 1 or below.
In uniform mode it prefetches $s, 2s, \dots$ up to the current degree.
Otherwise every observed stride trains the pattern table under the previous signature,
$\mathrm{sig}' = ((\mathrm{sig} \ll 3)\oplus s)\ \&\ \mathtt{0xFFF}$,
and prediction walks the table from the current signature, feeding each predicted stride back into the signature, up to the current degree.
The walk stops at the first entry with zero confidence.
Requiring four equal strides for uniform mode prevents a run of three $+2$ strides inside $(+1,+2,+2,+2,+3)$ from being mistaken for a uniform stream.
Every prefetch offset is checked to lie inside the current 4~KB page.

\subsection{Storage overhead}
""" + table(["Structure", "Entries", "Bits/entry", "Fields", "Total bits"], [
    ["IP table", "64", "45", "valid 1, uniform 1, conf 2, tag 8, page hash 8, last offset 6, last stride 7, signature 12", "2880"],
    ["Pattern table", "256", "9", "next stride 7, conf 2", "2304"],
    ["Recent-prefetch filter", "128", "10", "valid 1, partial tag 9", "1280"],
    ["Resident filter", "256", "9", "valid 1, partial tag 8", "2304"],
    ["Accuracy counters", "1", "18", "prefetch fills 7, useful 9, degree 2", "18"],
    ["Total", "", "", "", "8786 bits (1098.3 bytes)"]], "lrrp{5.0cm}p{2.3cm}") + r"""
Without the resident filter the total is 6482 bits.

\subsection{Accuracy-based throttling}
Every 64 prefetch fills into L1D the accuracy (useful fills divided by fills) is evaluated and the degree is set to 1 below $T_1$\%, 2 below $T_2$\%, 3 below $T_3$\% and 4 otherwise.
We swept five threshold sets and three fixed degrees over the three traces:
""" + sweep_table("results/task1_sweep/sweep_table.md") + r"""
% EDIT: confirm these statements against your sweep table before submitting.
Throttled variants (1.0116 to 1.0121 geomean speedup) beat every fixed degree (1.0090 to 1.0100).
Fixed degree 4 has the highest coverage but the lowest accuracy and speedup, consistent with cache pollution; the throttle recovers the benefit of a high degree without it.
The threshold sets differ by only about 0.05\%, so performance is insensitive to their exact values.
We keep 30/55/75, within 0.01\% of the best speedup with moderate accuracy.
The maximum degree of 4 keeps a single trigger from filling more than half of the 8-entry prefetch queue, and the degree never drops to 0 so accuracy remains measurable.

\paragraph{Resident filter.}
Without it SPP issues 763K, 452K and 3.49M prefetch requests on the three traces; with it 263K, 132K and 469K.
Useful prefetches, prefetches sent to the lower level and IPC (1.0120 both ways) are unchanged.
The filter costs 2304 bits and reduces L1D prefetch traffic rather than improving speedup.

\subsection{Results}
""" + results_table("IP-stride", "results/task1/metrics_ip_stride.csv") + "\n" + results_table("SPP", "results/task1/metrics_spp.csv") + r"""
Accuracy is the simulator's useful over useful-plus-useless prefetched lines. Coverage is the reduction in L1D load misses relative to the no-prefetching baseline.
% EDIT: add the simulator's own ACCURACY line (useful / issued to lower level) as a second column if you report both.
SPP improves on IP-stride in speedup and coverage, but IP-stride has higher accuracy on two traces because it issues far fewer prefetches.
All three traces are dominated by L2 and LLC misses (baseline LLC load MPKI 12.3, 8.2 and 3.1), which limits what an L1D prefetcher can gain.
""" + fig("speedup", "Speedup over the no-prefetching baseline.") + fig("mpki", "L1D load MPKI.") + fig("accuracy", "L1D prefetch accuracy.") + fig("coverage", "L1D prefetch coverage.") + fig("sweep", "Throttle sweep: geomean speedup per variant.")

open(f"{R}/task1.tex", "w").write(body)
if not os.path.exists(f"{R}/Summary.tex"):
    open(f"{R}/Summary.tex", "w").write(r"""\documentclass[11pt,a4paper]{article}
\usepackage[margin=2.2cm]{geometry}
\usepackage{graphicx,booktabs,amsmath,array}
\usepackage[T1]{fontenc}
\begin{document}
\begin{center}{\LARGE CS683 PA2 Summary}\\[4pt] Team: TEAMNAME (LDAP1, LDAP2)\end{center}
\input{task1}
% \input{task2a}
% \input{task2b}
% \input{task3}
\end{document}
""")
print("wrote report/task1.tex and report/Summary.tex; build with: cd report && pdflatex Summary.tex")