#!/usr/bin/env python3
"""Generate a long planetary reception stream and load it into QuestDB.

The QuestDB table schema mirrors the learner-facing parameters of the existing
46,786-tick stream (data/planetary_reception_stream.jsonl.gz). The table is
created explicitly (CREATE TABLE with typed columns, a designated timestamp,
yearly partitions) *before* ingestion, then populated by the model below.

Model (matching the README abstraction):
  * Planet positions from JPL approximate Keplerian elements (Table 1,
    https://ssd.jpl.nasa.gov/planets/approx_pos.html), propagated from J2000.
  * Each planet returns one wave per round trip tau_i = 2 r_i / c; reception
    times are the merged, chronological arrivals.
  * q_i = R_sun R_i / ((R_sun+d_i)(R_i+d_i)), d_i = r_i - R_sun - R_i ;
    delta_A/A0 = q_i - 1 ; source signature f_C = m_i c^2 / h.

Time basis identical to the repo: seconds since J2000, JD = 2451545.0 + s/86400.

Usage:
  python scripts/generate_long_stream.py --validate                    # 88-day check
  python scripts/generate_long_stream.py --years 25 --ingest --recreate # build DB + load
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import time
from pathlib import Path

import numpy as np
import psycopg2
from psycopg2.extras import execute_values

C = 299792458.0
H = 6.62607015e-34
AU = 1.495978707e11
R_SUN = 6.957e8
J2000_JD = 2451545.0
SEC_PER_DAY = 86400.0
CENTURY_S = SEC_PER_DAY * 36525.0
J2000_UNIX_NS = 946728000_000_000_000

ELEMENTS = {
    "Mercury": (0.38709927, 0.20563593, 7.00497902, 252.25032350, 77.45779628, 48.33076593,
                0.00000037, 0.00001906, -0.00594749, 149472.67411175, 0.16047689, -0.12534081),
    "Venus":   (0.72333566, 0.00677672, 3.39467605, 181.97909950, 131.60246718, 76.67984255,
                0.00000390, -0.00004107, -0.00078890, 58517.81538729, 0.00268329, -0.27769418),
    "Earth":   (1.00000261, 0.01671123, -0.00001531, 100.46457166, 102.93768193, 0.0,
                0.00000562, -0.00004392, -0.01294668, 35999.37244981, 0.32327364, 0.0),
    "Mars":    (1.52371034, 0.09339410, 1.84969142, -4.55343205, -23.94362959, 49.55953891,
                0.00001847, 0.00007882, -0.00813131, 19140.30268499, 0.44441088, -0.29257343),
    "Jupiter": (5.20288700, 0.04838624, 1.30439695, 34.39644051, 14.72847983, 100.47390909,
                -0.00011607, -0.00013253, -0.00183714, 3034.74612775, 0.21252668, 0.20469106),
    "Saturn":  (9.53667594, 0.05386179, 2.48599187, 49.95424423, 92.59887831, 113.66242448,
                -0.00125060, -0.00050991, 0.00193609, 1222.49362201, -0.41897216, -0.28867794),
    "Uranus":  (19.18916464, 0.04725744, 0.77263783, 313.23810451, 170.95427630, 74.01692503,
                -0.00196176, -0.00004397, -0.00242939, 428.48202785, 0.40805281, 0.04240589),
    "Neptune": (30.06992276, 0.00859048, 1.77004347, -55.12002969, 44.96476227, 131.78422574,
                0.00026291, 0.00005105, 0.00035372, 218.45945325, -0.32241464, -0.00508664),
}
RADII_KM = {"Mercury": 2439.7, "Venus": 6051.8, "Earth": 6371.0, "Mars": 3389.5,
            "Jupiter": 69911.0, "Saturn": 58232.0, "Uranus": 25362.0, "Neptune": 24622.0}
ORDER = list(ELEMENTS)

# QuestDB DDL: raw reception-stream columns; names mirror the JSON event keys.
# The SKA learning columns (knowledge, decision, decision_norm, entropy,
# delta_t, cosine_similarity, delta_h_over_delta_d, frobenius_norm) are added
# in a second stage via ALTER TABLE and populated by the learning engine.
DDL = """CREATE TABLE {table} (
  "tick" LONG,
  "reception_seconds_since_j2000_tdb" DOUBLE,
  "reception_jd_tdb" DOUBLE,
  "reception_gap_seconds" DOUBLE,
  "source_compton_frequency_hz" DOUBLE,
  "source_log10_compton_frequency" DOUBLE,
  "return_amplitude_over_A0" DOUBLE,
  "delta_A_over_A0" DOUBLE,
  "q_relative_diff" DOUBLE,
  "azimuth_radians" DOUBLE,
  "elevation_radians" DOUBLE,
  "round_trip_duration_seconds" DOUBLE,
  "source_sequence_index" LONG,
  "x_candidate" DOUBLE[],
  "reception_ts" TIMESTAMP
) TIMESTAMP(reception_ts) PARTITION BY MONTH WAL;"""

INSERT_SQL = (
    'INSERT INTO {table} ("tick","reception_seconds_since_j2000_tdb","reception_jd_tdb",'
    '"reception_gap_seconds","source_compton_frequency_hz","source_log10_compton_frequency",'
    '"return_amplitude_over_A0","delta_A_over_A0","q_relative_diff","azimuth_radians",'
    '"elevation_radians","round_trip_duration_seconds","source_sequence_index",'
    '"x_candidate","reception_ts") '
    "VALUES %s"
)


def connect(host):
    c = psycopg2.connect(host=host, port=8812, user="admin", password="quest",
                         dbname="qdb", connect_timeout=10)
    c.autocommit = True
    return c


def ddl(table):
    return DDL.format(table=table)


def create_table(cur, table, recreate):
    if recreate:
        print("DROP TABLE IF EXISTS %s" % table)
        cur.execute("DROP TABLE IF EXISTS %s" % table)
    print("creating table %s (JSON-standard schema) ..." % table)
    cur.execute(DDL.format(table=table))


def kepler_xyz(name, t_s):
    a0, e0, I0, L0, w0, O0, da, de, dI, dL, dw, dO = ELEMENTS[name]
    T = t_s / CENTURY_S
    a = a0 + da * T; e = e0 + de * T
    I = np.radians(I0 + dI * T)
    L = L0 + dL * T; varpi = w0 + dw * T
    Omega = np.radians(O0 + dO * T)
    omega = np.radians(varpi) - Omega
    M = np.radians(((L - varpi + 180.0) % 360.0) - 180.0)
    E = M + e * np.sin(M)
    for _ in range(12):
        E = E - (E - e * np.sin(E) - M) / (1.0 - e * np.cos(E))
    xp = a * (np.cos(E) - e); yp = a * np.sqrt(1.0 - e * e) * np.sin(E)
    cO, sO = np.cos(Omega), np.sin(Omega)
    cw, sw = np.cos(omega), np.sin(omega)
    cI, sI = np.cos(I), np.sin(I)
    x = (cw * cO - sw * sO * cI) * xp + (-sw * cO - cw * sO * cI) * yp
    y = (cw * sO + sw * cO * cI) * xp + (-sw * sO + cw * cO * cI) * yp
    z = (sw * sI) * xp + (cw * sI) * yp
    return np.stack([x, y, z], axis=-1)


def planet_tick_times(name, T_end, grid_dt=3600.0):
    tg = np.arange(0.0, T_end + grid_dt, grid_dt)
    r = np.linalg.norm(kepler_xyz(name, tg), axis=1) * AU
    rate = C / (2.0 * r)
    cum = np.concatenate([[0.0], np.cumsum(0.5 * (rate[1:] + rate[:-1]) * np.diff(tg))])
    n = int(np.floor(cum[-1]))
    return np.interp(np.arange(1, n + 1), cum, tg)


def build(years):
    truth = json.loads((Path(__file__).resolve().parents[1] / "data/frequency_truth_map.json").read_text())
    masses = {v: float(k) * H / (C * C) for k, v in truth.items()}
    freqs = {n: masses[n] * C * C / H for n in ORDER}
    logf = np.log10(np.array([freqs[n] for n in ORDER]))
    lfmin, lfmax = logf.min(), logf.max()
    T_end = years * 365.25 * SEC_PER_DAY
    parts = {k: [] for k in ("t", "freq", "q", "dqr", "az", "el", "rtt", "seq")}
    for name in ORDER:
        tt = planet_tick_times(name, T_end)
        xyz = kepler_xyz(name, tt)
        r = np.linalg.norm(xyz, axis=1) * AU
        Ri = RADII_KM[name] * 1e3
        d = r - R_SUN - Ri
        qp = (R_SUN * Ri) / ((R_SUN + d) * (Ri + d))
        # per-source successive relative diff: (q_k - q_{k-1}) / q_{k-1}
        # (this source vs its own previous return; NaN on the first return)
        dqr = np.full(qp.shape, np.nan)
        dqr[1:] = (qp[1:] - qp[:-1]) / qp[:-1]
        parts["t"].append(tt)
        parts["freq"].append(np.full(tt.shape, freqs[name]))
        parts["q"].append(qp)
        parts["dqr"].append(dqr)
        parts["az"].append(np.arctan2(xyz[:, 1], xyz[:, 0]))
        parts["el"].append(np.arcsin(np.clip(xyz[:, 2] / (r / AU), -1, 1)))
        parts["rtt"].append(2.0 * r / C)
        parts["seq"].append(np.arange(1, tt.size + 1))
    for k in parts:
        parts[k] = np.concatenate(parts[k])
    o = np.argsort(parts["t"], kind="stable")
    for k in parts:
        parts[k] = parts[k][o]
    n = parts["t"].size
    t, q, az, el, f = parts["t"], parts["q"], parts["az"], parts["el"], parts["freq"]
    return dict(
        tick=np.arange(1, n + 1),
        reception_seconds=t, reception_jd=J2000_JD + t / SEC_PER_DAY,
        gap_seconds=np.concatenate([[0.0], np.diff(t)]),
        source_freq=f, source_log10_freq=np.log10(f),
        q=q, delta_a=q - 1.0, dqr=parts["dqr"], azimuth=az, elevation=el,
        round_trip=parts["rtt"], seq=parts["seq"].astype(np.int64),
        x0=np.log10(q), x1=np.cos(az), x2=np.sin(az),
        x3=np.sin(el), x4=np.cos(el), x5=(np.log10(f) - lfmin) / (lfmax - lfmin),
    ), freqs


def validate():
    out, freqs = build(88.4 / 365.25)
    Ri = {n: RADII_KM[n] * 1e3 for n in ORDER}
    known = {"Mercury": .387, "Venus": .723, "Earth": 1.0, "Mars": 1.524,
             "Jupiter": 5.203, "Saturn": 9.537, "Uranus": 19.19, "Neptune": 30.07}
    print("events = %d over %.2f days" % (out["tick"].size, out["reception_seconds"][-1] / SEC_PER_DAY))
    print("planet    n      recovered_r(AU)  known   median_q")
    for n in ORDER:
        m = np.isclose(out["source_freq"], freqs[n])
        rr = np.sqrt(R_SUN * Ri[n] / out["q"][m]) / AU
        print("  %-8s %7d   %7.3f       %6.3f  %.3e" %
              (n, m.sum(), np.median(rr), known[n], np.median(out["q"][m])))


def _row(out, ts_us, i):
    return (
        int(out["tick"][i]),
        float(out["reception_seconds"][i]), float(out["reception_jd"][i]),
        float(out["gap_seconds"][i]),
        float(out["source_freq"][i]), float(out["source_log10_freq"][i]),
        float(out["q"][i]), float(out["delta_a"][i]),
        (None if np.isnan(out["dqr"][i]) else float(out["dqr"][i])),
        float(out["azimuth"][i]), float(out["elevation"][i]),
