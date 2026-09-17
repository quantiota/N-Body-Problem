#!/usr/bin/env python3
"""Plot the relative return amplitude q_i for each planet and check separation.

For every reception tick, q_i = A_return/A0 = return_amplitude_over_A0 (the
relative return amplitude, equal to 1 + delta_A/A0). This script groups the
ticks by their source signature, labels each signature with the evaluation
truth map (data/frequency_truth_map.json), and draws a violin+box plot of
log10(q_i) per planet so the per-body distributions can be compared.

The learner never uses these labels; the truth map is evaluation metadata,
used here only to interpret the result after the fact.

Requires matplotlib (an analysis extra, not part of the core build
dependency in requirements.txt):

    pip install matplotlib
"""
from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path

import numpy as np

ORDER = ["Mercury", "Venus", "Earth", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune"]


def load(stream_path: Path, truth_path: Path):
    truth = {float(k): v for k, v in json.loads(truth_path.read_text()).items()}

    def label(freq: float) -> str:
        return truth[min(truth, key=lambda k: abs(k - freq))]

    q, lab = [], []
    with gzip.open(stream_path, "rt", encoding="utf-8") as fh:
        for line in fh:
            e = json.loads(line)
            q.append(e["return_amplitude_over_A0"])
            lab.append(label(e["source_compton_frequency_hz"]))
    return np.array(q), np.array(lab)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--stream", type=Path, default=repo_root / "data/planetary_reception_stream.jsonl.gz")
    p.add_argument("--truth", type=Path, default=repo_root / "data/frequency_truth_map.json")
    p.add_argument("--output", type=Path, default=repo_root / "figures/qi_per_planet.png")
    args = p.parse_args()

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    q, lab = load(args.stream, args.truth)
    data = [np.log10(q[lab == n]) for n in ORDER]

    print("planet     n      median_log10q   p5..p95            range(dex)")
    for n, d in zip(ORDER, data):
        p5, p50, p95 = np.percentile(d, [5, 50, 95])
        print("%-8s %6d   %8.3f      [%.3f..%.3f]   %.3f" % (n, len(d), p50, p5, p95, d.max() - d.min()))

    fig, ax = plt.subplots(figsize=(11, 6))
    ax.violinplot(data, showmedians=True, widths=0.85)
    ax.boxplot(data, widths=0.25, showfliers=False,
               medianprops=dict(color="k"), boxprops=dict(alpha=0.6))
    ax.set_xticks(range(1, 9))
    ax.set_xticklabels(ORDER, rotation=20)
    ax.set_ylabel(r"$\log_{10}\,q_i$   (relative return amplitude)")
    ax.set_title(r"Relative return amplitude $q_i$ per planet")
    ax.grid(axis="y", alpha=0.3)
    for i, d in enumerate(data, 1):
        ax.text(i, np.median(d) + 0.12, "%.2f" % np.median(d), ha="center", fontsize=8)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(args.output, dpi=130)
    print("saved:", args.output)


if __name__ == "__main__":
    main()
