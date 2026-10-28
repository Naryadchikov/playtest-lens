"""Group kept findings into Puzzles, Attempts and Sub-beats.

Sasha, 2026-10-28, on the Talos report: moments are the wrong unit.
A Puzzle is one place across the session. An Attempt is one visit to
it (the player may leave, solve something else, and come back). A
Sub-beat is one kept finding, as before.

Grouping is deterministic, no model call. With an event log, zone
intervals from telemetry volumes (zone_enter and zone_exit) bound the
Attempts. Without a log, an Attempt ends when the place changes or
the gap since the previous moment passes ATTEMPT_GAP_S.
"""

from __future__ import annotations

import re

# Proposal (Muse Wonder, orchestrator, 2026-10-28), not Sasha's number:
# a longer silence than this, in the same place, reads as a new visit.
ATTEMPT_GAP_S = 180.0


def place_key(finding) -> str:
    # The checker's stable puzzle label wins; game_state is its
    # per-clip description and almost never repeats word for word.
    text = finding["check"].get("puzzle") or finding.get("game_state") or ""
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _zone_at(zones, time_s):
    for zone in zones or []:
        if zone["start_s"] <= time_s and (zone["end_s"] is None or time_s <= zone["end_s"]):
            return zone
    return None


# Zone intervals from a session log's telemetry events, in video time.
def zone_intervals(events, video_flash_s):
    if not events or video_flash_s is None:
        return []
    first_flash = next((e for e in events if e.get("event") == "sync_flash"), None)
    if first_flash is None:
        return []
    offset = video_flash_s - float(first_flash["t"])
    open_zones = {}
    intervals = []
    for event in events:
        video_t = round(float(event["t"]) + offset, 2)
        if event.get("event") == "zone_enter":
            open_zones[event.get("zone", "")] = {
                "zone": event.get("zone", ""),
                "puzzle": event.get("puzzle", ""),
                "start_s": video_t,
                "end_s": None,
            }
        elif event.get("event") == "zone_exit":
            zone = open_zones.pop(event.get("zone", ""), None)
            if zone is not None:
                zone["end_s"] = video_t
                intervals.append(zone)
    intervals.extend(open_zones.values())
    return sorted(intervals, key=lambda zone: zone["start_s"])


_STOPWORDS = {"and", "the", "a", "an", "of", "with", "on", "in", "by", "at", "near"}


def _tokens(label: str):
    words = re.sub(r"[^a-z0-9]+", " ", (label or "").lower()).split()
    return {word for word in words if word not in _STOPWORDS}


# Add a "beat" field to every kept finding, in place:
# {"puzzle": label, "zone": label or None, "attempt": n, "index": n}
# Dropped findings are untouched. Returns the findings list.
def assign_beats(findings, zones=None):
    kept = [f for f in findings if f["check"]["verdict"] == "keep"]
    kept.sort(key=lambda f: f["time_s"])
    puzzles = []
    for finding in kept:
        zone = _zone_at(zones, finding["time_s"])
        if zone is not None:
            label = zone["puzzle"] or zone["zone"]
            zone_label = zone["zone"] or None
            state = next((s for s in puzzles if s["label"] == label), None)
            if state is None:
                state = {"label": label, "tokens": _tokens(label), "attempt": 0, "last_time": None, "count": 0}
                puzzles.append(state)
        else:
            label = finding["check"].get("puzzle") or finding.get("game_state") or finding["summary"]
            zone_label = None
            tokens = _tokens(label)
            # An identical label is the same puzzle at any distance.
            state = next((s for s in puzzles if s["label"] == label), None)
            if state is None:
                best = 0.34
                for candidate in puzzles:
                    if not tokens or not candidate["tokens"]:
                        continue
                    # Only a puzzle visited recently can be the same one:
                    # barrier words repeat across a whole game. One shared
                    # word never joins two puzzles.
                    if candidate["last_time"] is None or finding["time_s"] - candidate["last_time"] > 300.0:
                        continue
                    shared = len(tokens & candidate["tokens"])
                    overlap = shared / min(len(tokens), len(candidate["tokens"]))
                    if shared >= 2 and overlap >= best:
                        best = overlap
                        state = candidate
            if state is None:
                state = {"label": label, "tokens": tokens, "attempt": 0, "last_time": None, "count": 0}
                puzzles.append(state)
            label = state["label"]
        # With a log, a new zone interval is a new Attempt by definition.
        zone_start = zone["start_s"] if zone is not None else None
        if state["last_time"] is None:
            state["attempt"] += 1
        elif zone_start is not None and state.get("last_zone_start") != zone_start:
            state["attempt"] += 1
        elif finding["time_s"] - state["last_time"] > ATTEMPT_GAP_S:
            state["attempt"] += 1
        state["last_zone_start"] = zone_start
        state["last_time"] = finding["time_s"]
        state["count"] += 1
        finding["beat"] = {
            "puzzle": label,
            "zone": zone_label,
            "attempt": state["attempt"],
            "index": state["count"],
        }
    return findings
