"""Combine kept findings across sessions (PLAN.md step 4).

Reads findings.json files through analyzer/findings.py (the one
format), keeps only verdict keep, and groups moments that share a
place: same kind, and the same place text (the finding's beat Area
and Puzzle when it has a beat, else its game_state), normalised. A
group seen in two or more sessions is a shared moment ("3 of 4
players stuck at the lab door"). No model call.

cross_player() turns the same shared groups into each file's own
"Across players" block, and --write-cross-player writes it back into
the findings files, because the report page only renders the file.

Run as: .venv/bin/python -m analyzer.summary <findings.json> [<findings.json> ...]
    [-o <summary.json>] [--write-cross-player]
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


# Readable place text for a shared group, from its first finding in
# rank order. The wording is Sasha's to change.
def _place_text(finding) -> str:
    beat = finding.get("beat") or {}
    area = beat.get("area")
    puzzle = beat.get("puzzle")
    if area and puzzle:
        text = f"{area}, {puzzle}"
    elif area or puzzle:
        text = area or puzzle
    else:
        text = finding.get("game_state") or ""
    return text[:1].upper() + text[1:]


# The time_s of the finding with the longest span; a missing end_s
# counts as a span of 0, and ties go to the earliest time_s.
def _worst_t(finding_list):
    worst = None
    worst_span = 0
    for finding in finding_list:
        end_s = finding.get("end_s")
        span = end_s - finding["time_s"] if end_s is not None else 0
        if worst is None or span > worst_span or (
            span == worst_span and finding["time_s"] < worst["time_s"]
        ):
            worst = finding
            worst_span = span
    return worst["time_s"]


# One "Across players" block per session in the batch, in batch order.
# Each block holds one entry per shared group (two or more sessions),
# with here set only for the session the block belongs to. Single-
# session groups are left out, and a session with none gets [].
def cross_player(sessions_data):
    by_moment = {}
    labels = {}
    for data in sessions_data:
        session = data["session"]
        labels[session["id"]] = session.get("player") or session["id"]
        for finding in data["findings"]:
            if finding["check"]["verdict"] == "keep":
                by_moment[(session["id"], finding["id"])] = finding

    entries = []
    for group in summarize(sessions_data)["groups"]:
        if not group["shared"]:
            continue
        findings = [
            (moment["session"], by_moment[(moment["session"], moment["id"])])
            for moment in group["moments"]
        ]
        first = min(findings, key=lambda item: item[1]["rank"])[1]
        player_sessions = list(group["sessions"])
        players = []
        for session_id in player_sessions:
            own = sorted(
                (
                    finding
                    for moment_session, finding in findings
                    if moment_session == session_id
                ),
                key=lambda finding: finding["rank"],
            )
            players.append(
                {
                    "label": labels[session_id],
                    "moments": [finding["id"] for finding in own],
                    "worst_t": _worst_t(own),
                }
            )
        entries.append(
            {
                "place": _place_text(first),
                "kind": group["kind"],
                "of": len(sessions_data),
                "players": players,
                "player_sessions": player_sessions,
            }
        )

    blocks = []
    for data in sessions_data:
        own_id = data["session"]["id"]
        block = []
        for entry in entries:
            block.append(
                {
                    "place": entry["place"],
                    "kind": entry["kind"],
                    "of": entry["of"],
                    "players": [
                        {**player, "here": session_id == own_id}
                        for session_id, player in zip(
                            entry["player_sessions"], entry["players"]
                        )
                    ],
                }
            )
        blocks.append(block)
    return blocks


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Combine kept findings across sessions into a cross-player summary."
    )
    parser.add_argument("findings", nargs="+", help="findings.json files, one per session")
    parser.add_argument("-o", "--out", default=None, help="Summary path (default: print to stdout)")
    parser.add_argument(
        "--write-cross-player",
        action="store_true",
        help="Rewrite each findings file in place with its cross_player block "
        "(no summary output; -o is not used)",
    )
    args = parser.parse_args(argv)

    sessions_data = [findings_module.load(path) for path in args.findings]

    if args.write_cross_player:
        for path, data, block in zip(
            args.findings, sessions_data, cross_player(sessions_data)
        ):
            if block:
                data["cross_player"] = block
            else:
                data.pop("cross_player", None)
            Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")
            # Prove the file the report will read is in the one format.
            findings_module.load(path)
            print(f"Wrote {len(block)} cross-player groups to {path}")
        return 0

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
