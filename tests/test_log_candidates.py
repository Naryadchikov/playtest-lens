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


def test_fixture_idle_covers_the_long_stand():
    candidates = find_candidates(load_log(FIXTURE), VIDEO_FLASH_S)
    idle = next(c for c in candidates if c["kind"] == "idle")
    assert 39.0 <= idle["end_s"] - idle["time_s"] <= 42.0


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
