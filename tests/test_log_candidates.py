import json
from pathlib import Path

import pytest

from analyzer.log_candidates import find_candidates, load_log

FIXTURE = Path(__file__).parent / "fixtures" / "session_log.jsonl"
VIDEO_FLASH_S = 12.34


def _kinds(candidates):
    return [candidate["kind"] for candidate in candidates]


def test_fixture_has_one_of_each_candidate():
    candidates = find_candidates(load_log(FIXTURE), VIDEO_FLASH_S)
    assert _kinds(candidates).count("death") == 1
    assert _kinds(candidates).count("retry") == 1
    assert _kinds(candidates).count("idle") == 1
    assert _kinds(candidates).count("looking_around") == 1
    assert _kinds(candidates).count("backtrack") == 1
    assert [c["time_s"] for c in candidates] == sorted(
        c["time_s"] for c in candidates
    )


def test_fixture_times_map_through_the_flash():
    candidates = find_candidates(load_log(FIXTURE), VIDEO_FLASH_S)
    death = next(c for c in candidates if c["kind"] == "death")
    # By hand: the first sync_flash is at log t 0.182098 and death at
    # log t 48.041704, so 48.041704 - 0.182098 + 12.34 = 60.20.
    assert death["time_s"] == 60.2
    assert death["end_s"] == 60.2
    assert "COGITO_3_Lobby" in death["detail"]

    retry = next(c for c in candidates if c["kind"] == "retry")
    assert retry["time_s"] == 61.06
    assert "COGITO_3_Lobby" in retry["detail"]


def test_fixture_stand_splits_into_looking_then_idle():
    candidates = find_candidates(load_log(FIXTURE), VIDEO_FLASH_S)
    looking = next(c for c in candidates if c["kind"] == "looking_around")
    idle = next(c for c in candidates if c["kind"] == "idle")
    assert 19.0 <= looking["end_s"] - looking["time_s"] <= 21.0
    assert 19.0 <= idle["end_s"] - idle["time_s"] <= 21.0
    assert looking["end_s"] == idle["time_s"]
    assert "view turned" in looking["detail"]
    assert "view turned 0 degrees" in idle["detail"]


def test_fixture_backtrack_is_on_the_way_back():
    candidates = find_candidates(load_log(FIXTURE), VIDEO_FLASH_S)
    backtrack = next(c for c in candidates if c["kind"] == "backtrack")
    death = next(c for c in candidates if c["kind"] == "death")
    assert backtrack["time_s"] < backtrack["end_s"] < death["time_s"]
    assert "Walked back" in backtrack["detail"]


def _events(tmp_path, lines):
    path = tmp_path / "log.jsonl"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return load_log(path)


def _line(**fields):
    return json.dumps(fields)


def test_no_sync_flash_raises(tmp_path):
    events = _events(tmp_path, [
        _line(t=0.0, event="session_start"),
        _line(t=1.0, event="death"),
    ])
    with pytest.raises(ValueError, match="sync_flash"):
        find_candidates(events, 0.0)


def test_malformed_line_names_its_line_number(tmp_path):
    path = tmp_path / "log.jsonl"
    path.write_text(
        _line(t=0.0, event="session_start") + "\nnot json\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="line 2"):
        load_log(path)


def test_missing_session_end_still_works(tmp_path):
    events = _events(tmp_path, [
        _line(t=0.0, event="session_start"),
        _line(t=0.5, event="sync_flash", reason="new_game"),
        _line(t=1.0, event="scene", scene="level.tscn"),
        _line(t=2.0, event="death"),
        _line(t=3.0, event="scene", scene="level.tscn"),
    ])
    candidates = find_candidates(events, 10.0)
    assert _kinds(candidates) == ["death", "retry"]
    assert candidates[0]["time_s"] == 11.5


def test_no_position_lines_gives_no_idle_or_backtrack(tmp_path):
    events = _events(tmp_path, [
        _line(t=0.0, event="session_start"),
        _line(t=0.5, event="sync_flash", reason="new_game"),
        _line(t=1.0, event="scene", scene="level.tscn"),
        _line(t=30.0, event="death"),
        _line(t=31.0, event="session_end"),
    ])
    candidates = find_candidates(events, 10.0)
    assert _kinds(candidates) == ["death"]


def test_pause_is_not_idle_time():
    events = [{"t": 0.0, "event": "sync_flash"}]
    for step in range(6):
        events.append({
            "t": 1.0 + step, "event": "position",
            "x": 0.0, "y": 0.0, "z": 0.0, "yaw": 0.0, "pitch": 0.0,
        })
    events.append({"t": 7.0, "event": "pause"})
    for step in range(30):
        events.append({
            "t": 8.0 + step, "event": "position",
            "x": 0.0, "y": 0.0, "z": 0.0, "yaw": 0.0, "pitch": 0.0,
        })
    events.append({"t": 38.0, "event": "resume"})
    for step in range(6):
        events.append({
            "t": 39.0 + step, "event": "position",
            "x": 0.0, "y": 0.0, "z": 0.0, "yaw": 0.0, "pitch": 0.0,
        })
    candidates = find_candidates(events, 0.0)
    assert [c for c in candidates if c["kind"] in ("idle", "looking_around")] == []


def test_paused_motion_is_not_a_backtrack():
    events = [
        {"t": 0.0, "event": "sync_flash"},
        {"t": 1.0, "event": "position", "x": 0.0, "y": 0.0, "z": 0.0},
        {"t": 2.0, "event": "pause"},
        {"t": 2.5, "event": "position", "x": 0.0, "y": 0.0, "z": 0.0},
        {"t": 3.0, "event": "position", "x": 6.0, "y": 0.0, "z": 0.0},
        {"t": 9.0, "event": "position", "x": 0.0, "y": 0.0, "z": 0.0},
        {"t": 10.0, "event": "resume"},
        {"t": 11.0, "event": "position", "x": 0.0, "y": 0.0, "z": 0.0},
    ]
    candidates = find_candidates(events, 0.0)
    assert [c for c in candidates if c["kind"] == "backtrack"] == []


def test_unsupported_schema_is_rejected(tmp_path):
    path = tmp_path / "log.jsonl"
    path.write_text(
        _line(t=0.0, event="session_start", schema=99) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="unsupported log schema"):
        load_log(path)


def test_input_breaks_an_idle_stretch():
    events = [
        {"t": 0.0, "event": "sync_flash"},
        {"t": 1.0, "event": "position", "x": 0.0, "y": 0.0, "z": 0.0},
        {"t": 6.0, "event": "input", "action": "jump", "pressed": True},
        {"t": 7.0, "event": "position", "x": 0.0, "y": 0.0, "z": 0.0},
        {"t": 12.0, "event": "position", "x": 0.0, "y": 0.0, "z": 0.0},
    ]
    assert find_candidates(events, 0.0) == []


def test_still_and_quiet_is_idle():
    events = [{"t": 0.0, "event": "sync_flash"}]
    for step in range(12):
        events.append({
            "t": 1.0 + step,
            "event": "position",
            "x": 0.0, "y": 0.0, "z": 0.0,
        })
    candidates = find_candidates(events, 100.0)
    assert _kinds(candidates) == ["idle"]
    assert candidates[0]["time_s"] == 101.0
    assert candidates[0]["end_s"] == 112.0
    assert candidates[0]["detail"] == "No input for 11.0 s"


def _still_events(view_for_step, steps=12):
    events = [{"t": 0.0, "event": "sync_flash"}]
    for step in range(steps):
        event = {
            "t": 1.0 + step,
            "event": "position",
            "x": 0.0, "y": 0.0, "z": 0.0,
        }
        event.update(view_for_step(step))
        events.append(event)
    return events


def test_yaw_wrap_counts_as_two_degrees_not_358():
    # Yaw only, no pitch: 179 to -179 is a 2 degree step, below the
    # turning threshold, so the stretch stays idle.
    events = _still_events(
        lambda step: {"yaw": 179.0 if step % 2 == 0 else -179.0}
    )
    candidates = find_candidates(events, 0.0)
    assert _kinds(candidates) == ["idle"]
    assert candidates[0]["detail"] == (
        "No input for 11.0 s, view turned 22 degrees"
    )


def test_yaw_only_turning_is_looking_around():
    events = _still_events(lambda step: {"yaw": -150.0 + 15.0 * step})
    candidates = find_candidates(events, 0.0)
    assert _kinds(candidates) == ["looking_around"]
    assert candidates[0]["detail"] == (
        "No input for 11.0 s, view turned 165 degrees"
    )


def test_on_and_off_looking_is_one_looking_around():
    # 2 s turning, 1 s still, repeated: the still runs are too short
    # to be idle, so the whole 30 s is one looking_around part.
    def view(step):
        turned_steps = (step // 3) * 2 + min(step % 3, 2)
        yaw = (15.0 * turned_steps + 180.0) % 360.0 - 180.0
        return {"yaw": yaw, "pitch": 0.0}

    candidates = find_candidates(_still_events(view, steps=31), 0.0)
    assert _kinds(candidates) == ["looking_around"]
    assert candidates[0]["time_s"] == 1.0
    assert candidates[0]["end_s"] == 31.0
    assert candidates[0]["detail"] == (
        "No input for 30.0 s, view turned 300 degrees"
    )


def test_one_turn_in_middle_of_still_gives_two_idle():
    events = _still_events(
        lambda step: {"yaw": 15.0 if step >= 16 else 0.0, "pitch": 0.0},
        steps=31,
    )
    candidates = find_candidates(events, 0.0)
    assert _kinds(candidates) == ["idle", "idle"]
    assert candidates[0]["time_s"] == 1.0
    assert candidates[0]["end_s"] == 16.0
    assert candidates[1]["time_s"] == 17.0
    assert candidates[1]["end_s"] == 31.0
    assert "view turned 0 degrees" in candidates[0]["detail"]
    assert "view turned 0 degrees" in candidates[1]["detail"]


def test_one_turn_near_start_gives_one_idle():
    # The 5 s still side before the turn is under IDLE_MIN_S, and the
    # leftover before the long still run is 6 s, also under it, so
    # only the long still run remains, as one idle from the turn.
    events = _still_events(
        lambda step: {"yaw": 15.0 if step >= 6 else 0.0, "pitch": 0.0},
        steps=31,
    )
    candidates = find_candidates(events, 0.0)
    assert _kinds(candidates) == ["idle"]
    assert candidates[0]["time_s"] == 7.0
    assert candidates[0]["end_s"] == 31.0


def test_short_looking_part_is_dropped():
    def view(step):
        return {"yaw": 15.0 * min(step, 5), "pitch": 0.0}

    candidates = find_candidates(_still_events(view, steps=21), 0.0)
    assert _kinds(candidates) == ["idle"]
    assert candidates[0]["time_s"] == 6.0
    assert candidates[0]["end_s"] == 21.0


def test_out_and_back_is_one_backtrack():
    events = [{"t": 0.0, "event": "sync_flash"}]
    for step in range(11):
        x = float(step if step <= 5 else 10 - step)
        events.append({
            "t": 1.0 + step,
            "event": "position",
            "x": x, "y": 0.0, "z": 0.0,
        })
    candidates = find_candidates(events, 0.0)
    assert _kinds(candidates) == ["backtrack"]
