#!/usr/bin/env python3
"""Wrap a CD-Agent run's summary.json into a leaderboard submission file.

Usage:
    python scripts/build_submission.py <run_dir> \
        --run-name <name> --submitter <handle> [--notes "..."]

Writes data/runs/<run-name>.json and appends an entry to data/index.json.
Rejects partial-coverage runs (leaderboard policy).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = ROOT / "data" / "runs"
INDEX = ROOT / "data" / "index.json"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("run_dir", type=Path, help="Directory containing summary.json")
    p.add_argument("--run-name", required=True)
    p.add_argument("--submitter", required=True)
    p.add_argument("--notes", default="")
    args = p.parse_args()

    summary_path = args.run_dir / "summary.json"
    if not summary_path.exists():
        print(f"error: {summary_path} not found", file=sys.stderr)
        return 1

    summary = json.loads(summary_path.read_text())
    if summary.get("coverage") != "full" or summary.get("missing"):
        print(
            f"error: partial coverage ({summary.get('coverage')!r}, "
            f"{len(summary.get('missing', []))} missing) — leaderboard requires full coverage",
            file=sys.stderr,
        )
        return 2

    for key in ("model", "agent_style", "judge_model", "weighted_accuracy", "labs"):
        if key not in summary:
            print(f"error: summary.json missing required field {key!r}", file=sys.stderr)
            return 3

    # Strip the absolute local path — not useful once published.
    summary.pop("run_dir", None)

    submission = {
        "submission": {
            "run_name": args.run_name,
            "submitter": args.submitter,
            "submitted_at": dt.date.today().isoformat(),
            "notes": args.notes,
        },
        "summary": summary,
    }

    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    out = RUNS_DIR / f"{args.run_name}.json"
    out.write_text(json.dumps(submission, indent=2) + "\n")
    print(f"wrote {out.relative_to(ROOT)}")

    index = json.loads(INDEX.read_text()) if INDEX.exists() else {"runs": []}
    runs = [r for r in index["runs"] if r != args.run_name]
    runs.append(args.run_name)
    runs.sort()
    index["runs"] = runs
    INDEX.write_text(json.dumps(index, indent=2) + "\n")
    print(f"updated {INDEX.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
