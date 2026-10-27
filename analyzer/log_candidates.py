"""Candidate moments from a session event log, with no model call.

One path: load_log parses the JSONL written by the game's add-on, and
find_candidates flags deaths, retries, idle stretches and backtracks.
Log times map to video time through the first sync_flash, whose video
time the caller supplies (tools/video.py's find_start_flash).
"""

import json
import math
from pathlib import Path

# Idle and backtrack thresholds. These numbers are a proposal
# (Muse Code on Muse Wonder, 2026-10-27), not yet Sasha's decision.
IDLE_MIN_S = 10.0
IDLE_MAX_MOVE_M = 0.5
IDLE_MAX_GAP_S = 2.0
BACKTRACK_NEAR_M = 2.0
BACKTRACK_MIN_AWAY_M = 5.0
BACKTRACK_MIN_GAP_S = 5.0


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


# Parse one log file, raising ValueError naming the line on a bad line.
def load_log(path):
    """Return the log's events as a list of dicts, in file order.

    A missing session_end line (a crash) is fine. Any malformed line
    raises ValueError with its 1-based line number.
    """
    events = []
    text = Path(path).read_text(encoding="utf-8")
    for number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"line {number}: invalid JSON ({exc.msg})") from exc
        if not isinstance(event, dict):
            raise ValueError(f"line {number}: must be a JSON object")
        if not _is_number(event.get("t")):
            raise ValueError(f"line {number}: t must be a number")
        if not isinstance(event.get("event"), str):
            raise ValueError(f"line {number}: event must be a string")
        kind = event["event"]
        if kind == "position":
            for field in ("x", "y", "z"):
                if not _is_number(event.get(field)):
                    raise ValueError(f"line {number}: {field} must be a number")
        if kind == "scene" and not isinstance(event.get("scene"), str):
            raise ValueError(f"line {number}: scene must be a string")
        events.append(event)
    return events


def _distance(a, b):
    return math.dist((a["x"], a["y"], a["z"]), (b["x"], b["y"], b["z"]))


# One candidate dict, with log times mapped to video time and rounded.
def _candidate(kind, start_log_t, end_log_t, offset, detail):
    return {
        "time_s": round(start_log_t + offset, 2),
        "end_s": round(end_log_t + offset, 2),
        "kind": kind,
        "detail": detail,
    }


# Idle stretches: no input, and every position within IDLE_MAX_MOVE_M
# of the stretch's first position, for at least IDLE_MIN_S.
def _idle_candidates(events, offset):
    candidates = []
    run = []

    def close_run():
        if len(run) >= 2:
            duration = run[-1]["t"] - run[0]["t"]
            if duration >= IDLE_MIN_S:
                candidates.append(
                    _candidate(
                        "idle",
                        run[0]["t"],
                        run[-1]["t"],
                        offset,
                        f"No input for {duration:.1f} s",
                    )
                )

    for event in events:
        kind = event["event"]
        if kind == "position":
            if run and event["t"] - run[-1]["t"] > IDLE_MAX_GAP_S:
                close_run()
                run = []
            if run and _distance(event, run[0]) > IDLE_MAX_MOVE_M:
                close_run()
                run = []
            run.append(event)
        elif kind in ("input", "scene", "death", "session_end"):
            close_run()
            run = []
    close_run()
    return candidates


# Backtracks: the player comes back within BACKTRACK_NEAR_M of a point
# passed at least BACKTRACK_MIN_GAP_S earlier, after reaching at least
# BACKTRACK_MIN_AWAY_M from that point. One candidate per return; its
# span runs from the farthest point reached to the return.
def _backtrack_candidates(events, offset):
    candidates = []
    history = []
    max_away = []

    def reset(event=None):
        history.clear()
        max_away.clear()
        if event is not None:
            history.append(event)
            max_away.append(0.0)

    for event in events:
        kind = event["event"]
        if kind in ("scene", "death", "session_end"):
            reset()
            continue
        if kind != "position":
            continue
        for index, earlier in enumerate(history):
            max_away[index] = max(max_away[index], _distance(event, earlier))
        found = None
        for index, earlier in enumerate(history):
            if (
                event["t"] - earlier["t"] >= BACKTRACK_MIN_GAP_S
                and max_away[index] >= BACKTRACK_MIN_AWAY_M
                and _distance(event, earlier) <= BACKTRACK_NEAR_M
            ):
                found = index
                break
        if found is None:
            history.append(event)
            max_away.append(0.0)
            continue
        earlier = history[found]
        farthest = max(
            history[found:],
            key=lambda point: _distance(point, earlier),
        )
        walked_back = 0.0
        points = history[history.index(farthest):] + [event]
        for first, second in zip(points, points[1:]):
            walked_back += _distance(first, second)
        candidates.append(
            _candidate(
                "backtrack",
                farthest["t"],
                event["t"],
                offset,
                f"Walked back {walked_back:.1f} m to a point passed "
                f"{event['t'] - earlier['t']:.0f} s earlier",
            )
        )
        reset(event)
    return candidates


# All candidate moments in the log, sorted by video time.
def find_candidates(events, video_flash_s):
    """Return candidate dicts (time_s, end_s, kind, detail) by time_s.

    video_flash_s is the video time of the first white flash. Raises
    ValueError when the log has no sync_flash line.
    """
    flashes = [event for event in events if event.get("event") == "sync_flash"]
    if not flashes:
        raise ValueError("log has no sync_flash line, so log times "
                         "cannot be mapped to video time")
    offset = video_flash_s - flashes[0]["t"]

    candidates = []
    current_scene = None
    death_scene = None
    for event in events:
        kind = event["event"]
        if kind == "scene":
            current_scene = event["scene"]
            if death_scene is not None and current_scene == death_scene:
                candidates.append(
                    _candidate(
                        "retry", event["t"], event["t"], offset,
                        f"Reloaded {current_scene} after death",
                    )
                )
                death_scene = None
        elif kind == "death":
            death_scene = current_scene
            if current_scene is not None:
                detail = f"Died in {current_scene}"
            else:
                detail = "Died"
            candidates.append(
                _candidate("death", event["t"], event["t"], offset, detail)
            )

    candidates.extend(_idle_candidates(events, offset))
    candidates.extend(_backtrack_candidates(events, offset))
    candidates.sort(key=lambda candidate: candidate["time_s"])
    return candidates
