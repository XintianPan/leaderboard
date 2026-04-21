#!/usr/bin/env python3
"""Validate a leaderboard submission JSON file.

Checks structure, full coverage, and that per-lab question counts match the
CD-Agent benchmark. Exits non-zero on failure so CI can gate PRs.

Usage:
    python scripts/validate_submission.py data/runs/<name>.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Expected (scenario_id -> question_count) for CD-Agent benchmark.
# Source of truth: benchmark/scenarios/*/metadata.json in the CD-Agent repo.
# Keep in sync via scripts/refresh_scenarios.py (not yet shipped).
EXPECTED_LAB_QUESTIONS = {
    "data-leakage-case": 60,
    "fc01": 11,
    "fc02": 10,
    "fc03": 10,
    "fc04": 18,
    "fc05": 10,
    "fc06": 10,
    "fc07": 14,
    "fc08": 14,
    "fc09": 12,
    "fc11": 6,
    "fc12": 20,
    "fc14": 11,
    "hacking-case": 31,
}
EXPECTED_TOTAL = sum(EXPECTED_LAB_QUESTIONS.values())  # 237


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: validate_submission.py <path>")
    path = Path(sys.argv[1])
    doc = json.loads(path.read_text())

    sub = doc.get("submission") or {}
    for k in ("run_name", "submitter", "submitted_at"):
        if not sub.get(k):
            fail(f"submission.{k} missing")

    s = doc.get("summary") or {}
    for k in ("model", "agent_style", "judge_model", "weighted_accuracy",
              "total_points", "total_max_points", "labs"):
        if k not in s:
            fail(f"summary.{k} missing")

    if s.get("coverage") != "full":
        fail(f"coverage must be 'full', got {s.get('coverage')!r}")
    if s.get("missing"):
        fail(f"missing questions not allowed: {s['missing']}")

    if s.get("agent_style") not in ("codeblock", "native-tools", "claude-sdk"):
        fail(f"unknown agent_style {s.get('agent_style')!r}")

    labs = {lab["scenario_id"]: lab for lab in s["labs"]}
    if set(labs) != set(EXPECTED_LAB_QUESTIONS):
        missing = set(EXPECTED_LAB_QUESTIONS) - set(labs)
        extra = set(labs) - set(EXPECTED_LAB_QUESTIONS)
        fail(f"lab set mismatch — missing={sorted(missing)} extra={sorted(extra)}")

    for sid, expected in EXPECTED_LAB_QUESTIONS.items():
        got = labs[sid].get("total_questions")
        if got != expected:
            fail(f"{sid}: expected {expected} questions, got {got}")

    if s.get("total_questions") != EXPECTED_TOTAL:
        fail(f"total_questions {s.get('total_questions')} != {EXPECTED_TOTAL}")

    acc = s["weighted_accuracy"]
    if not (0.0 <= acc <= 1.0):
        fail(f"weighted_accuracy out of range: {acc}")

    print(f"OK: {path.name} — {s['model']} / {s['agent_style']} / "
          f"{acc*100:.2f}% weighted accuracy")


if __name__ == "__main__":
    main()
