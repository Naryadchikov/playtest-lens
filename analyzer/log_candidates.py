"""Candidate moments from a session event log, with no model call.

One path: load_log parses the JSONL written by the game's add-on, and
find_candidates flags deaths, retries, idle stretches and backtracks.
Log times map to video time through the first sync_flash, whose video
time the caller supplies (tools/video.py's find_start_flash).
Headless sync_flash stamps are approximate (about one frame late, and
no frame was drawn); windowed stamps mark the drawn frame.
"""

import json
import math
from pathlib import Path

# Idle and backtrack thresholds. These numbers are a proposal
# (Muse Code on Muse Wonder, 2026-10-27), not yet Sasha's decision.
IDLE_MIN_S = 10.0
IDLE_MAX_MOVE_M = 0.5
IDLE_MAX_GAP_S = 2.0
# View turning: more than this many degrees between two position
# samples (about 0.5 s apart). Also a proposal, as above.
VIEW_TURN_MIN_DEG = 5.0
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


def _has_view(event):
    return _is_number(event.get("yaw")) or _is_number(event.get("pitch"))


# Degrees the view turned between two samples, or None when the two
# samples share no yaw or pitch. Yaw wraps at 180, so 179 to -179
# is 2 degrees.
def _view_turn_deg(a, b):
    dyaw = 0.0
    dpitch = 0.0
    shared = False
    if _is_number(a.get("yaw")) and _is_number(b.get("yaw")):
        dyaw = abs((b["yaw"] - a["yaw"] + 180.0) % 360.0 - 180.0)
        shared = True
    if _is_number(a.get("pitch")) and _is_number(b.get("pitch")):
        dpitch = abs(b["pitch"] - a["pitch"])
        shared = True
    if not shared:
        return None
    return math.hypot(dyaw, dpitch)


# Idle stretches: no input, and every position within IDLE_MAX_MOVE_M
# of the stretch's first position, for at least IDLE_MIN_S. With view
# data, a run where the view stays still for at least IDLE_MIN_S is an
# idle part; what is left between and around those runs, if at least
# IDLE_MIN_S long, is one looking_around part, short pauses included.
def _idle_candidates(events, offset):
    candidates = []
    run = []

    def emit(start, end, kind, steps=None):
        # start and end are sample indexes into run, both included.
        if end <= start:
            return
        duration = run[end]["t"] - run[start]["t"]
        if duration < IDLE_MIN_S:
            return
        if steps is None:
            detail = f"No input for {duration:.1f} s"
        else:
            turned_deg = sum(
                step for step in steps[start:end] if step is not None
            )
            detail = (
                f"No input for {duration:.1f} s, "
                f"view turned {turned_deg:.0f} degrees"
            )
        candidates.append(
            _candidate(kind, run[start]["t"], run[end]["t"], offset, detail)
        )

    def close_run():
        if len(run) < 2:
            return
        if not any(_has_view(event) for event in run):
            emit(0, len(run) - 1, "idle")
            return
        steps = [
            _view_turn_deg(run[index], run[index + 1])
            for index in range(len(run) - 1)
        ]
        # Maximal runs of still steps, kept as idle only when long
        # enough. Their sample spans share a boundary sample with
        # the looking_around parts around them.
        def is_turning(step):
            return step is not None and step > VIEW_TURN_MIN_DEG

        idle_parts = []
        index = 0
        while index < len(steps):
            if is_turning(steps[index]):
                index += 1
                continue
            last = index
            while last + 1 < len(steps) and not is_turning(steps[last + 1]):
                last += 1
            if run[last + 1]["t"] - run[index]["t"] >= IDLE_MIN_S:
                idle_parts.append((index, last + 1))
            index = last + 1
        cursor = 0
        for start, end in idle_parts:
            emit(cursor, start, "looking_around", steps)
            emit(start, end, "idle", steps)
            cursor = end
        emit(cursor, len(run) - 1, "looking_around", steps)

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
