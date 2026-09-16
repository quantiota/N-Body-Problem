#!/usr/bin/env python3
"""Replay the planetary reception stream in chronological real time.

Example:
  python planetary_stream_replay.py --speed 1000000 --limit 160 \\
      | your_ska_consumer

At speed 1, successive events retain their modeled reception-time intervals.
Use a larger speed for accelerated experiments; use speed 0 for a fast replay.
"""
from __future__ import annotations

import argparse
import gzip
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


def open_stream(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8")
    return path.open("rt", encoding="utf-8")


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=repo_root / "data/planetary_reception_stream.jsonl.gz")
    parser.add_argument("--speed", type=float, default=1.0, help="replay speed relative to modeled reception time; 0 means no waiting")
    parser.add_argument("--limit", type=int, default=0, help="stop after this many ticks; 0 means all")
    parser.add_argument("--emit-replay-time", action="store_true", help="add the wall-clock emission time to each output event")
    args = parser.parse_args()
    if not args.input.exists():
        raise SystemExit(f"missing stream: {args.input}")
    if args.speed < 0:
        raise SystemExit("--speed must be non-negative")
    if args.limit < 0:
        raise SystemExit("--limit must be non-negative")

    previous_reception = None
    emitted = 0
    with open_stream(args.input) as stream:
        for line in stream:
            if not line.strip():
                continue
            event = json.loads(line)
            reception = float(event["reception_seconds_since_j2000_tdb"])
            if previous_reception is not None and args.speed > 0:
                time.sleep(max(0.0, reception - previous_reception) / args.speed)
            if args.emit_replay_time:
                event["replay_wall_time_utc"] = datetime.now(timezone.utc).isoformat()
            sys.stdout.write(json.dumps(event, separators=(",", ":"), allow_nan=False) + "\n")
            sys.stdout.flush()
            previous_reception = reception
            emitted += 1
            if args.limit and emitted >= args.limit:
                break
    print(f"replayed {emitted} ticks", file=sys.stderr)


if __name__ == "__main__":
    main()
