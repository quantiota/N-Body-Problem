#!/usr/bin/env python3
"""Phase-space (Lissajous) matrix of q_relative_diff for every planet pair.

Reads the ingested reception stream from QuestDB (table
planetary_reception_stream), pivots q_relative_diff into one column per planet
keyed on the event index (source_sequence_index), and draws the pairwise
phase-space plane for all 8 planets: each cell (i, j) is (Delta q/q)_i vs
(Delta q/q)_j, a Lissajous curve colored by event index.

The Lissajous shape encodes the two bodies' oscillation-frequency ratio (which,
in event index, scales as sqrt(a_i / a_j)); a closed, stationary figure would
mark a commensurate (resonant) pair, an open/precessing one a non-resonant pair.

Reproduces queries/phase_space_pairs.png.

Requires matplotlib (analysis extra, not part of requirements.txt):
    pip install matplotlib
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import psycopg2

# planet -> Compton-frequency signature stored in the table (ordered by distance)
PLANETS = [
    ("Mercury", "4.4774923001163785e73"),
    ("Venus",   "6.601982728808719e74"),
    ("Earth",   "8.100606534925774e74"),
    ("Mars",    "8.703848530773663e73"),
    ("Jupiter", "2.5746024944209535e77"),
    ("Saturn",  "7.708609105416307e76"),
    ("Uranus",  "1.1774829638745261e76"),
    ("Neptune", "1.3890706975128312e76"),
]


def fetch(host, port, table, hi, stride):
    names = [p[0] for p in PLANETS]
    cols = ",\n  ".join(
        'max(CASE WHEN source_compton_frequency_hz = %s THEN q_relative_diff END) AS "%s"' % (f, n)
        for n, f in PLANETS)
    sql = ("SELECT source_sequence_index,\n  %s\n"
           "FROM %s\n"
           "WHERE source_sequence_index BETWEEN 1 AND %d AND source_sequence_index %% %d = 0\n"
           "ORDER BY source_sequence_index" % (cols, table, hi, stride))
    conn = psycopg2.connect(host=host, port=port, user="admin", password="quest",
                            dbname="qdb", connect_timeout=10)
    cur = conn.cursor(); cur.execute(sql); rows = cur.fetchall(); cur.close(); conn.close()
    d = np.array([[(v if v is not None else np.nan) for v in r] for r in rows], float)
    idx = d[:, 0]
    y = {names[k]: d[:, k + 1] for k in range(len(names))}
    return names, idx, y


def main() -> None:
    repo = Path(__file__).resolve().parents[1]
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--host", default="questdb")
    p.add_argument("--port", type=int, default=8812)
    p.add_argument("--table", default="planetary_reception_stream")
    p.add_argument("--hi", type=int, default=50000, help="upper bound of the event-index window")
    p.add_argument("--stride", type=int, default=12, help="decimation: keep every Nth index")
    p.add_argument("--output", type=Path, default=Path(__file__).resolve().parent / "phase_space_pairs.png")
    args = p.parse_args()

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    names, idx, y = fetch(args.host, args.port, args.table, args.hi, args.stride)
    n = len(names)
    fig, ax = plt.subplots(n, n, figsize=(17, 17))
    for i in range(n):
        for j in range(n):
            a = ax[i, j]
            if i == j:
                a.text(.5, .5, names[i], ha="center", va="center", fontsize=11, weight="bold")
                a.set_xticks([]); a.set_yticks([])
            elif i > j:
                x = y[names[j]]; yy = y[names[i]]
                m = ~(np.isnan(x) | np.isnan(yy))
                a.scatter(x[m], yy[m], c=idx[m], s=1, cmap="viridis")
                a.set_xticks([]); a.set_yticks([])
            else:
                a.axis("off")
    for j in range(n):
        ax[n - 1, j].set_xlabel(names[j], fontsize=8)
    for i in range(n):
        ax[i, 0].set_ylabel(names[i], fontsize=8)
    fig.suptitle(r"Phase-space of $\Delta q/q$ for every planet pair (i,j) — "
                 r"Lissajous, colored by event index", fontsize=14)
    fig.tight_layout(rect=[0, 0, 1, 0.98])
    fig.savefig(args.output, dpi=110)
    print("saved:", args.output)


if __name__ == "__main__":
    main()
