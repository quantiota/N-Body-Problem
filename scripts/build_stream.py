#!/usr/bin/env python3
"""Build a learner-facing planetary reception stream from the saved tick data.

The output contains one JSON object per reception tick. Planet names and
Cartesian positions are deliberately absent from the learner stream. The
Compton frequency remains as the source signature.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np


J2000_JD_TDB = 2451545.0
SECONDS_PER_DAY = 86400.0


def open_input(path: Path):
    return gzip.open(path, "rt", encoding="utf-8") if path.suffix == ".gz" else path.open("rt", encoding="utf-8")


def make_event(i: int, data: dict[str, np.ndarray], source: dict[str, np.ndarray],
               log_f_min: float, log_f_max: float) -> dict:
    planet_id = int(data["planet_id"][i])
    names = data["planet_names"].tolist()
    planet_name = names[planet_id]
    local_index = int(data["planet_round_trip_index"][i]) - 1
    raw = source[planet_name][local_index]
    launch_s = float(raw[0])
    reception_s = float(data["reception_seconds_since_J2000"][i])
    duration_s = float(raw[1] - raw[0])
    q = float(data["A_return_over_A0"][i])
    delta = float(data["delta_A_over_A0"][i])
    frequency = float(data["compton_frequency_hz"][i])
    log_f = float(np.log10(frequency))
    az = float(data["azimuth_radians"][i])
    el = float(data["elevation_radians"][i])
    previous_reception = None if i == 0 else float(data["reception_seconds_since_J2000"][i - 1])
    gap = None if previous_reception is None else reception_s - previous_reception
    # Circular coordinates avoid a discontinuity at azimuth 0/2π. The
    # logarithm preserves the tiny positive return envelope near delta=-1.
    normalized_log_f = 0.0 if log_f_max == log_f_min else (log_f - log_f_min) / (log_f_max - log_f_min)
    x_candidate = [
        float(np.log10(q)),
        float(np.cos(az)),
        float(np.sin(az)),
        float(np.sin(el)),
        float(np.cos(el)),
        float(normalized_log_f),
    ]
    return {
        "schema": "ska.planetary_reception.v1",
        "event_id": f"planetary-reception-{i + 1:06d}",
        "tick": i + 1,
        "reception_seconds_since_j2000_tdb": reception_s,
        "reception_jd_tdb": J2000_JD_TDB + reception_s / SECONDS_PER_DAY,
        "reception_gap_seconds": gap,
        "source_compton_frequency_hz": frequency,
        "source_log10_compton_frequency": log_f,
        "return_amplitude_over_A0": q,
        "delta_A_over_A0": delta,
        "azimuth_radians": az,
        "elevation_radians": el,
        "round_trip_duration_seconds": duration_s,
        "source_sequence_index": local_index + 1,
        "x_candidate": x_candidate,
        "x_candidate_names": [
            "log10_return_amplitude_over_A0",
            "cos_azimuth",
            "sin_azimuth",
            "sin_elevation",
            "cos_elevation",
            "normalized_log10_compton_frequency",
        ],
    }


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--directional-ticks",
        type=Path,
        default=repo_root / "data/directional_tick_stream.npz",
        help="directional chronological tick dataset",
    )
    parser.add_argument(
        "--wave-samples",
        type=Path,
        default=repo_root / "data/planetary_wave_samples.npz",
        help="per-planet launch/return samples used to recover each arc interval",
    )
    parser.add_argument(
        "--output-dir", type=Path, default=repo_root / "data",
    )
    args = parser.parse_args()
    if not args.directional_ticks.exists():
        raise SystemExit(f"missing directional dataset: {args.directional_ticks}")
    if not args.wave_samples.exists():
        raise SystemExit(f"missing wave dataset: {args.wave_samples}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    data_file = np.load(args.directional_ticks, allow_pickle=False)
    source_file = np.load(args.wave_samples, allow_pickle=False)
    # NpzFile lazily decompresses members. Materialize once so the event loop
    # never repeatedly decompresses the same per-planet array.
    data = {name: data_file[name] for name in data_file.files}
    source = {name: source_file[name] for name in source_file.files}
    n = len(data["tick"])
    names = data["planet_names"].tolist()
    assert np.array_equal(data["tick"], np.arange(1, n + 1))
    assert np.all(np.diff(data["reception_seconds_since_J2000"]) >= 0)
    assert np.all(data["A_return_over_A0"] > 0)
    frequencies_by_planet = {
        name: float(data["compton_frequency_hz"][np.flatnonzero(data["planet_id"] == i)[0]])
        for i, name in enumerate(names)
    }
    log_f_values = np.log10(np.array(list(frequencies_by_planet.values())))
    log_f_min, log_f_max = float(log_f_values.min()), float(log_f_values.max())

    jsonl_path = args.output_dir / "planetary_reception_stream.jsonl.gz"
    sha = hashlib.sha256()
    preview = []
    with gzip.open(jsonl_path, "wt", encoding="utf-8", compresslevel=6) as stream:
        for i in range(n):
            event = make_event(i, data, source, log_f_min, log_f_max)
            line = (json.dumps(event, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")
            sha.update(line)
            stream.write(line.decode("utf-8"))
            if i < 12:
                preview.append(event)
    (args.output_dir / "stream_preview.json").write_text(json.dumps(preview, indent=2) + "\n", encoding="utf-8")

    # This map is evaluation metadata. It is separate from the learner-facing
    # stream, whose event records contain frequency but no planet names.
    frequency_map = {
        f"{frequency:.17e}": name for name, frequency in frequencies_by_planet.items()
    }
    (args.output_dir / "frequency_truth_map.json").write_text(
        json.dumps(frequency_map, indent=2) + "\n", encoding="utf-8"
    )
    def manifest_path(path: Path) -> str:
        try:
            return str(path.relative_to(repo_root))
        except ValueError:
            return str(path)

    manifest = {
        "schema": "ska.planetary_reception.v1",
        "event_count": n,
        "first_tick": 1,
        "last_tick": n,
        "first_reception_seconds_since_j2000_tdb": float(data["reception_seconds_since_J2000"][0]),
        "last_reception_seconds_since_j2000_tdb": float(data["reception_seconds_since_J2000"][-1]),
        # Keep the manifest usable without revealing the evaluation labels.
        # The optional frequency_truth_map.json sidecar contains the labels.
        "source_signature_frequencies_hz": sorted(frequencies_by_planet.values()),
        "learner_visible_fields": [
            "schema", "event_id", "tick", "reception_seconds_since_j2000_tdb",
            "reception_jd_tdb", "reception_gap_seconds", "source_compton_frequency_hz",
            "source_log10_compton_frequency", "return_amplitude_over_A0", "delta_A_over_A0",
            "azimuth_radians", "elevation_radians", "round_trip_duration_seconds",
            "source_sequence_index", "x_candidate", "x_candidate_names",
        ],
        "hidden_from_stream": ["planet_name", "planet_id", "heliocentric_distance", "x", "y", "z"],
        "x_candidate_definition": "[log10(q), cos(az), sin(az), sin(el), cos(el), normalized_log10(f_C)] with q=1+delta_A/A0",
        "time_basis": "J2000.0, JD 2451545.0 TDB; relative reception times preserve chronological order",
        "source_dataset": manifest_path(args.directional_ticks),
        "orbit_dataset": manifest_path(args.wave_samples),
        "evaluation_truth_map": manifest_path(args.output_dir / "frequency_truth_map.json"),
        "model_source": "https://ssd.jpl.nasa.gov/planets/approx_pos.html",
        "sha256_uncompressed_jsonl": sha.hexdigest(),
        "compression": "gzip; decompress to newline-delimited JSON",
    }
    (args.output_dir / "stream_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"events": n, "output": str(jsonl_path), "sha256": sha.hexdigest()}))


if __name__ == "__main__":
    main()
