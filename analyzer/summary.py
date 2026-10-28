"""Combine kept findings across sessions (PLAN.md step 4).

Reads findings.json files through analyzer/findings.py (the one
format), keeps only verdict keep, and groups moments that share a
place: same kind, and the same place text (the finding's beat Area
and Puzzle when it has a beat, else its game_state), normalised. A
group seen in two or more sessions is a shared moment ("3 of 4
players stuck at the lab door"). No model call.

Run as: .venv/bin/python -m analyzer.summary <findings.json> [<findings.json> ...]
    [-o <summary.json>]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analyzer import findings as findings_module  # noqa: E402


# Group key from the finding's beat when it has one (the pipeline's
# Area and Puzzle), else from game_state. A finding with no usable
# place text gets a unique key (its session and id), so never groups.
def _place_key(finding, session_id: str) -> str:
    beat = finding.get("beat") or {}
    text = " ".join(
        part for part in (beat.get("area"), beat.get("puzzle")) if part
    ) or finding.get("game_state") or ""
    normalised = re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()
    if not normalised:
        return f"unique:{session_id}:{finding['id']}"
    return normalised


# One summary dict from a list of loaded findings data dicts.
def summarize(sessions_data) -> dict:
    sessions = []
    groups = {}
    for data in sessions_data:
        session_id = data["session"]["id"]
        kept = [f for f in data["findings"] if f["check"]["verdict"] == "keep"]
        sessions.append(
            {
                "id": session_id,
                "recording": data["session"]["recording"],
                "kept": len(kept),
                "dropped": len(data["findings"]) - len(kept),
            }
        )
        for finding in kept:
            key = (finding["kind"], _place_key(finding, session_id))
            group = groups.setdefault(
                key,
                {
                    "kind": finding["kind"],
                    "game_state": finding.get("game_state"),
                    "sessions": [],
                    "moments": [],
                },
            )
            if session_id not in group["sessions"]:
                group["sessions"].append(session_id)
            group["moments"].append(
                {
                    "session": session_id,
                    "id": finding["id"],
                    "time_s": finding["time_s"],
                    "end_s": finding.get("end_s"),
                }
            )
    ordered = sorted(
        groups.values(),
        key=lambda group: (-len(group["sessions"]), group["kind"], group["game_state"] or ""),
    )
    for group in ordered:
        group["session_count"] = len(group["sessions"])
        group["shared"] = group["session_count"] >= 2
        spans = [
            moment["end_s"] - moment["time_s"]
            for moment in group["moments"]
            if moment.get("end_s") is not None
        ]
        group["avg_span_s"] = round(sum(spans) / len(spans), 2) if spans else None
    return {"format": 1, "sessions": sessions, "groups": ordered}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Combine kept findings across sessions into a cross-player summary."
    )
    parser.add_argument("findings", nargs="+", help="findings.json files, one per session")
    parser.add_argument("-o", "--out", default=None, help="Summary path (default: print to stdout)")
    args = parser.parse_args(argv)

    sessions_data = [findings_module.load(path) for path in args.findings]
    summary = summarize(sessions_data)
    text = json.dumps(summary, indent=2)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        shared = sum(1 for group in summary["groups"] if group["shared"])
        print(f"Wrote summary of {len(sessions_data)} sessions ({shared} shared groups) to {args.out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
