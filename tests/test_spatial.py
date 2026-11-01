import re
import copy
import json
import math
import shutil
from pathlib import Path

import pytest

from analyzer import findings as findings_module
from analyzer import log_candidates
from analyzer import spatial
from report.render import render_html

FIXTURES = Path(__file__).parent / "fixtures"
LOG = FIXTURES / "spatial_log.jsonl"
REAL_LOG = FIXTURES / "session_log.jsonl"
FINDINGS = FIXTURES / "spatial_findings.json"
LOBBY = "res://addons/cogito/DemoScenes/COGITO_3_Lobby.tscn"
LAB = "res://addons/cogito/DemoScenes/COGITO_4_Laboratory.tscn"


def _flash(t=0.0, reason="new_game"):
    return {"event": "sync_flash", "t": t, "reason": reason}


def _scene(name, t=0.0):
    return {"event": "scene", "t": t, "scene": name}


def _position(t, x=0.0, z=0.0, y=0.8):
    return {"event": "position", "t": t, "x": x, "y": y, "z": z}


def _finding(fid="f1", rank=1, time_s=10.0, end_s=None, kind="stuck", verdict="keep"):
    return {
        "id": fid,
        "rank": rank if verdict == "keep" else None,
        "time_s": time_s,
        "end_s": end_s,
        "kind": kind,
        "summary": "A moment.",
        "quote": None,
        "game_state": None,
        "clip": None,
        "sources": ["spark"],
        "check": {"verdict": verdict, "note": "A note.", "model": "muse-spark"},
    }


def _placed(finding, area, puzzle=None, attempt=None, start_s=0.0, friction="learning", resolved="unknown"):
    finding["check"].update(friction=friction, resolved=resolved)
    finding["beat"] = {
        "area": area,
        "puzzle": puzzle,
        "zone": area,
        "puzzle_number": 1 if puzzle else None,
        "attempt": attempt,
        "attempt_start_s": start_s,
        "attempt_end_s": start_s + 30.0,
        "index": 1,
    }
    return finding


def _data(findings, duration_s=120.0):
    return {
        "format": 1,
        "session": {
            "id": "s01",
            "recording": "s01.mp4",
            "duration_s": duration_s,
            "start_flash_s": 0.0,
        },
        "findings": findings,
    }


def _lobby_meta():
    return json.loads((Path(spatial.MAPS_DIR) / "lobby.json").read_text(encoding="utf-8"))


def _px_distance(meta, first, second):
    scale_x = meta["px_width"] / (meta["world_max_x"] - meta["world_min_x"])
    scale_z = meta["px_height"] / (meta["world_max_z"] - meta["world_min_z"])
    return math.hypot(
        (first["x"] - second["x"]) * scale_x,
        (first["z"] - second["z"]) * scale_z,
    )


def test_video_time_maps_through_the_first_flash():
    events = [
        _flash(t=1.0),
        _scene(LOBBY, t=1.05),
        _position(0.5, x=99.0, z=99.0),
        _position(11.0, x=1.0, z=2.0),
        _position(12.5, x=3.0, z=4.0),
    ]
    data = spatial.enrich(_data([]), events, video_flash_s=4.0)
    # A position at log 11.0 is at video 11.0 + (4.0 - 1.0) = 14.0.
    assert data["route"]["points"][0] == [14.0, 1.0, 2.0, 0]
    assert data["route"]["points"][-1] == [15.5, 3.0, 4.0, 0]
    # The sample before the first flash is not on the route.
    assert all(point[0] >= 4.0 for point in data["route"]["points"])


def test_paused_time_is_skipped():
    events = [
        _flash(t=0.0),
        _scene(LOBBY, t=0.5),
        _position(1.5, x=1.0),
        _position(2.0, x=2.0),
        {"event": "pause", "t": 2.2},
        _position(2.5, x=100.0, z=100.0),
        _position(3.0, x=100.0, z=100.0),
        {"event": "resume", "t": 3.2},
        _position(3.5, x=3.0),
    ]
    data = spatial.enrich(_data([]), events, video_flash_s=0.0)
    assert [point[0] for point in data["route"]["points"]] == [1.5, 3.5]
    assert [point[1] for point in data["route"]["points"]] == [1.0, 3.0]


def test_map_choice_follows_time_with_samples():
    events = [
        _flash(t=0.0),
        _scene(LOBBY, t=0.5),
        _position(1.0),
        _position(1.5),
        _position(2.0),
        _scene(LAB, t=2.5),
    ]
    for step in range(35):
        events.append(_position(3.0 + 0.5 * step))
    # A repeated scene line is not time with samples.
    events.append(_scene(LOBBY, t=20.5))
    data = spatial.enrich(_data([]), events, video_flash_s=0.0)
    assert data["route"]["scene"] == LAB
    assert data["route"]["maps"] == ["laboratory"]


def test_unmapped_dominant_scene_hides_the_map(capsys):
    scene = "res://elsewhere/Unmapped.tscn"
    events = [_flash(), _scene(LOBBY, t=0.5), _position(1.0), _scene(scene, t=1.5)]
    for step in range(20):
        events.append(_position(2.0 + 0.5 * step))
    data = spatial.enrich(_data([]), events, video_flash_s=0.0)
    assert "route" not in data
    err = capsys.readouterr().err
    assert err.count("\n") == 1
    assert scene in err


def test_no_map_file_writes_no_route_and_names_the_scene(capsys):
    scene = "res://elsewhere/Unmapped.tscn"
    events = [_flash(), _scene(scene, t=0.5), _position(1.0)]
    data = _data([_finding(time_s=1.0)])
    data["findings"][0]["at"] = {"x": 1.0, "z": 1.0}
    spatial.enrich(data, events, video_flash_s=0.0)
    assert "route" not in data
    assert "markers" not in data
    assert "at" not in data["findings"][0]
    assert data["summary"]["kept"] == 1
    err = capsys.readouterr().err
    assert err.count("\n") == 1
    assert scene in err


def test_downsample_keeps_first_last_and_one_second_apart():
    events = [_flash(), _scene(LOBBY, t=0.1)]
    for step in range(41):
        events.append(_position(0.25 * step, x=1.0, z=2.0))
    data = spatial.enrich(_data([]), events, video_flash_s=0.0)
    times = [point[0] for point in data["route"]["points"]]
    assert times == [float(step) for step in range(11)]
    assert all(second - first >= 1.0 for first, second in zip(times, times[1:]))


def test_downsample_keeps_the_sample_where_the_floor_changes():
    # Review 20, nit 2: a floor change inside the one-second step kept its
    # floor span but had no route point. t=0 floor 0, t=0.5 floor 1, t=1.0 floor 0.
    events = [_flash(), _scene(LOBBY, t=0.05)]
    events.append(_position(0.0, x=1.0, z=1.0, y=0.0))
    events.append(_position(0.5, x=1.0, z=1.5, y=3.0))
    events.append(_position(1.0, x=1.0, z=2.0, y=0.0))
    data = spatial.enrich(_data([]), events, video_flash_s=0.0)
    route = data["route"]
    assert [(point[0], point[3]) for point in route["points"]] == [(0.0, 0), (0.5, 1), (1.0, 0)]
    for span in route["floor_spans"]:
        assert any(point[3] == span["floor"] and span["start_s"] <= point[0] <= span["end_s"] for point in route["points"])


@pytest.mark.parametrize(
    "name, words",
    [
        ("kitchenCabinet4", "Kitchen cabinet 4"),
        ("UPPER_OFFICE_CEO", "Upper office CEO"),
        ("BATHROOM_STALL2", "Bathroom stall 2"),
        ("AnimatableBody3D", "Animatable body 3D"),
        ("Platform", "Platform"),
        ("", ""),
    ],
)
def test_node_names_become_words(name, words):
    assert spatial._words(name) == words


def test_door_and_lock_labels_name_the_thing_and_its_room():
    label = spatial._event_label
    assert label({"event": "door", "open": True, "path": "BREAK_ROOM/kitchenSink/CabinetDoor"}) == "Kitchen sink opened (Break room)"
    assert label({"event": "door", "open": False, "path": "MEETING_ROOM/desk/AnimatableBody3D"}) == "Desk closed (Meeting room)"
    assert label({"event": "lock", "locked": False, "path": "BATHROOM_STALL2/DuctDoor"}) == "Duct door unlocked (Bathroom stall 2)"
    # One segment: no room to name.
    assert label({"event": "door", "open": True, "path": "Platform"}) == "Platform opened"
    assert label({"event": "quest", "quest": "demo_steal_laptop", "step": "activated"}) == "Demo steal laptop activated"


def test_heat_finds_a_linger_and_ignores_a_walk_through():
    events = [_flash(), _scene(LOBBY, t=0.5)]
    for step in range(9):
        events.append(_position(1.0 + 0.5 * step, x=2.0 * step, z=0.0))
    for step in range(61):
        events.append(_position(10.0 + 0.5 * step, x=20.0, z=20.0))
    data = spatial.enrich(_data([]), events, video_flash_s=0.0)
    spots = data["route"]["heat"]
    assert len(spots) == 1
    assert spots[0]["x"] == 20.0 and spots[0]["z"] == 20.0
    assert spots[0]["seconds"] == 30.0
    assert spots[0]["r_m"] == 1.5


def test_at_within_three_seconds_and_absent_beyond():
    events = [
        _flash(),
        _scene(LOBBY, t=0.5),
        _position(10.0, x=7.0, z=7.0),
        _position(20.0, x=9.0, z=9.0),
    ]
    near = _finding("f1", 1, time_s=12.9)
    far = _finding("f2", 2, time_s=13.5)
    dropped = _finding("f3", None, time_s=10.0, verdict="drop")
    data = spatial.enrich(_data([near, far, dropped]), events, video_flash_s=0.0)
    assert near["at"] == {"x": 7.0, "z": 7.0, "floor": 0}
    assert "at" not in far
    # A dropped candidate is pinned too, and moves aside for a kept pin.
    assert dropped["at"]["floor"] == 0
    assert _px_distance(_lobby_meta(), near["at"], dropped["at"]) >= spatial.PIN_SEPARATION_PX


def test_the_pin_nudge_keeps_two_close_pins_apart_deterministically():
    events = [_flash(), _scene(LOBBY, t=0.5), _position(10.0, x=5.0, z=5.0)]
    first = _finding("f1", 1, time_s=10.0)
    second = _finding("f2", 2, time_s=10.5)
    data = _data([first, second])
    spatial.enrich(data, events, video_flash_s=0.0)
    meta = _lobby_meta()
    assert first["at"] == {"x": 5.0, "z": 5.0, "floor": 0}
    assert _px_distance(meta, first["at"], second["at"]) >= spatial.PIN_SEPARATION_PX

    nudged = copy.deepcopy(data)
    spatial.enrich(data, events, video_flash_s=0.0)
    assert data == nudged


def test_marker_links_to_a_moment_and_is_null_when_none():
    events = log_candidates.load_log(LOG)
    finding = _finding("f1", 1, time_s=33.0, end_s=34.0)
    data = spatial.enrich(_data([finding]), events, video_flash_s=4.0)
    assert [marker["t"] for marker in data["markers"]] == [34.0, 40.0]
    assert data["markers"][0]["moment"] == "f1"
    assert data["markers"][1]["moment"] is None
    assert data["markers"][0]["x"] == 6.0 and data["markers"][0]["z"] == 0.0


def test_markers_render_as_f9_pins_linked_to_the_card():
    events = log_candidates.load_log(LOG)
    data = spatial.enrich(
        _data([_finding("f1", 1, time_s=33.0, end_s=34.0)]), events, video_flash_s=4.0
    )
    assert [marker["floor"] for marker in data["markers"]] == [0, 0]
    page = render_html(data)
    # Each marker is a pin on the overview map and one in Watch.
    assert page.count('class="pin f9"') == 4
    assert page.count('class="pin f9" href="#m1" data-open="f1"') == 2
    assert page.count('<g class="pin f9"') == 2
    assert 'class="f9line"' in page


def test_lost_s_is_the_time_in_visits_with_a_stuck_or_blocked_moment():
    events = [_flash(), _scene(LOBBY, t=0.5), _position(1.0)]
    findings = [
        # Two visits that overlap count once: 10-40 and 25-55 make 45 s.
        _placed(_finding("f1", 1, time_s=12.0, kind="confused"), "Hall", start_s=10.0, friction="stuck"),
        _placed(_finding("f2", 2, time_s=30.0, kind="surprised"), "Hall", start_s=25.0, friction="blocked"),
        # A moment by design never counts, whatever its kind.
        _placed(_finding("f3", 3, time_s=70.0, end_s=80.0, kind="stuck"), "Hall", start_s=60.0),
        # A dropped candidate never counts.
        _placed(_finding("f4", None, time_s=0.0, end_s=50.0, verdict="drop"), "Hall", start_s=0.0, friction="blocked"),
        # No usable visit span: the moment's own span, 100-110.
        _placed(_finding("f5", 4, time_s=100.0, end_s=110.0, kind="confused"), "Yard", start_s=100.0, friction="stuck"),
        # Neither span: nothing to count.
        _placed(_finding("f6", 5, time_s=115.0, kind="confused"), "Yard", start_s=115.0, friction="stuck"),
    ]
    findings[4]["beat"]["attempt_end_s"] = 100.0
    findings[5]["beat"]["attempt_end_s"] = 115.0
    data = spatial.enrich(_data(findings), events, video_flash_s=0.0)
    assert data["summary"]["lost_s"] == 55.0
    assert data["summary"]["counts"] == {
        "stuck": 1,
        "confused": 3,
        "surprised": 1,
        "suspected_bug": 0,
    }
    assert data["summary"]["kept"] == 5
    assert data["summary"]["dropped"] == 1


@pytest.mark.parametrize(
    "findings, verdict",
    [
        ([_finding(verdict="drop")], "No problem moments found."),
        (
            [_finding("f1", 1, kind="stuck")],
            "1 moment worth a look: 1 stuck.",
        ),
        (
            [
                _finding("f1", 1, kind="stuck"),
                _finding("f2", 2, time_s=20.0, kind="confused"),
                _finding("f3", 3, time_s=30.0, kind="surprised"),
                _finding("f4", None, time_s=40.0, verdict="drop"),
            ],
            "3 moments worth a look: 1 stuck, 1 confused, 1 surprised.",
        ),
    ],
)
def test_summary_counts_and_verdict_sentence(findings, verdict):
    events = [_flash(), _scene(LOBBY, t=0.5), _position(1.0)]
    data = spatial.enrich(_data(findings), events, video_flash_s=0.0)
    assert data["summary"]["verdict"] == verdict


def test_enrich_twice_gives_the_same_file():
    first = findings_module.load(FINDINGS)
    first = json.loads(json.dumps(first))
    events = log_candidates.load_log(REAL_LOG)
    spatial.enrich(first, events, video_flash_s=2.0)
    once = json.dumps(first, sort_keys=True)
    spatial.enrich(first, events, video_flash_s=2.0)
    assert json.dumps(first, sort_keys=True) == once
    assert first["route"]["maps"] == ["lobby", "lobby_upper"]
    assert first["summary"]["verdict"] == (
        "3 moments worth a look: 1 stuck, 1 confused, 1 surprised."
    )


def test_enriched_file_loads_and_renders(tmp_path):
    shutil.copyfile(FINDINGS, tmp_path / "findings.json")
    events = log_candidates.load_log(REAL_LOG)
    assert spatial.main(
        [
            str(tmp_path / "findings.json"),
            "--log",
            str(REAL_LOG),
            "--video-flash-s",
            "2.0",
        ]
    ) == 0
    data = findings_module.load(tmp_path / "findings.json")
    assert data["route"]["points"]
    assert data["markers"] == []
    # f1 is stuck over its attempt 6-9; f2 is by design and does not count.
    assert data["summary"]["lost_s"] == 3.0

    page = render_html(data)
    assert 'id="where"' in page
    assert 'class="ovmap multi"' in page
    assert 'class="tl" id="tl"' in page
    assert page.count('<div class="floor" data-floor="0"') == 2
    assert page.count('<div class="floor" data-floor="1"') == 2
    assert 'fill="url(#heat-blob)"' in page
    assert "<polyline" in page
    # f1 happened past the map's right edge: its pin is clamped to the edge and marked.
    assert len(re.findall(r'class="pin k-[a-z]+ edge" href="#m1" data-open="f1"', page)) == 2
    assert "3 moments worth a look: 1 stuck, 1 confused, 1 surprised." in page


def test_no_sync_flash_raises():
    with pytest.raises(ValueError, match="sync_flash"):
        spatial.enrich(_data([]), [_scene(LOBBY)], video_flash_s=0.0)


def test_floors_come_from_height_and_tile_the_route():
    # Lobby's upper floor starts at y 2.4 (report/maps/lobby_upper.json).
    events = [
        _flash(),
        _scene(LOBBY, t=0.5),
        _position(1.0, x=1.0, y=0.8),
        _position(2.0, x=2.0, y=2.4),
        _position(3.0, x=3.0, y=3.5),
        {"event": "position", "t": 4.0, "x": 4.0, "z": 0.0},
        _position(5.0, x=5.0, y=0.9),
    ]
    upstairs = _finding("f1", 1, time_s=3.0)
    data = spatial.enrich(_data([upstairs]), events, video_flash_s=0.0)
    route = data["route"]
    assert route["maps"] == ["lobby", "lobby_upper"]
    # At y_floor_min is upstairs; a line with no height is the ground floor.
    assert [point[3] for point in route["points"]] == [0, 1, 1, 0, 0]
    assert route["floor_spans"] == [
        {"floor": 0, "start_s": 1.0, "end_s": 2.0},
        {"floor": 1, "start_s": 2.0, "end_s": 4.0},
        {"floor": 0, "start_s": 4.0, "end_s": 5.0},
    ]
    assert upstairs["at"] == {"x": 3.0, "z": 0.0, "floor": 1}


def test_heat_is_per_floor_and_never_mixes_a_room_with_the_one_above():
    events = [_flash(), _scene(LOBBY, t=0.5)]
    # 30 s below, then 20 s right above it on the upper floor.
    for step in range(61):
        events.append(_position(1.0 + 0.5 * step, x=-3.0, z=-13.0, y=0.8))
    for step in range(41):
        events.append(_position(40.0 + 0.5 * step, x=-3.0, z=-13.0, y=3.5))
    data = spatial.enrich(_data([]), events, video_flash_s=0.0)
    spots = data["route"]["heat"]
    assert [(spot["floor"], spot["seconds"]) for spot in spots] == [(0, 32.0), (1, 20.0)]
    assert all(spot["x"] == -3.0 and spot["z"] == -13.0 for spot in spots)


def test_the_pin_nudge_works_per_floor():
    events = [
        _flash(),
        _scene(LOBBY, t=0.5),
        _position(10.0, x=-3.0, z=-13.0, y=0.8),
        _position(11.0, x=-3.0, z=-13.0, y=3.5),
    ]
    below = _finding("f1", 1, time_s=10.0)
    above = _finding("f2", 2, time_s=11.0)
    spatial.enrich(_data([below, above]), events, video_flash_s=0.0)
    # Same spot, different floors: neither pin moves.
    assert below["at"] == {"x": -3.0, "z": -13.0, "floor": 0}
    assert above["at"] == {"x": -3.0, "z": -13.0, "floor": 1}


def test_problems_rank_places_by_friction_then_time_stuck_then_time():
    findings = [
        # A learning-only area is never a problem.
        _placed(_finding("f1", 1, time_s=5.0, kind="confused"), "Hall"),
        # A puzzle over two attempts: blocked once, solved once.
        _placed(_finding("f2", 2, time_s=20.0, end_s=30.0), "Vault", "Dial", 1, 15.0, "blocked", "abandoned"),
        _placed(_finding("f3", 3, time_s=60.0), "Vault", "Dial", 2, 55.0, "learning", "solved"),
        # The same area with no puzzle is its own place.
        _placed(_finding("f4", 4, time_s=70.0, end_s=130.0, kind="confused"), "Vault", None, None, 65.0, "stuck"),
        # Blocked, a longer visit than the Dial's attempt: first.
        _placed(_finding("f5", 5, time_s=80.0, end_s=100.0), "Kitchen", None, None, 75.0, "blocked"),
        # Stuck, a short visit: last.
        _placed(_finding("f6", 6, time_s=10.0, kind="surprised"), "Atrium", None, None, 8.0, "stuck"),
        # A dropped candidate never counts.
        _placed(_finding("f7", None, time_s=90.0, verdict="drop"), "Basement", None, None, 88.0, "blocked"),
    ]
    findings[4]["beat"]["attempt_end_s"] = 135.0
    findings[5]["beat"]["attempt_end_s"] = 13.0
    events = [_flash(), _scene(LOBBY, t=0.5), _position(1.0)]
    data = spatial.enrich(_data(findings, duration_s=200.0), events, video_flash_s=0.0)
    problems = data["summary"]["problems"]
    assert [problem["place"] for problem in problems] == [
        "Kitchen", "Vault, Dial", "Vault", "Atrium",
    ]
    code_lock = problems[1]
    assert code_lock == {
        "place": "Vault, Dial",
        "moments": ["f2", "f3"],
        "attempts": 2,
        "lost_s": 30.0,
        "friction": "blocked",
        "resolved": "mixed",
    }
    assert problems[2]["lost_s"] == 30.0 and problems[2]["resolved"] == "unknown"
    assert problems[3]["lost_s"] == 5.0
    assert problems[3]["friction"] == "stuck"


def test_problems_keep_at_most_five_places():
    findings = [
        _placed(_finding(f"f{n}", n, time_s=10.0 * n), f"Room {n}", None, None, 10.0 * n, "stuck")
        for n in range(1, 8)
    ]
    events = [_flash(), _scene(LOBBY, t=0.5), _position(1.0)]
    data = spatial.enrich(_data(findings), events, video_flash_s=0.0)
    assert [p["place"] for p in data["summary"]["problems"]] == [f"Room {n}" for n in range(1, 6)]


def test_events_and_zones_are_written_in_video_time():
    # Video time = log time - 2.
    events = [
        {"event": "pickup", "t": 1.0, "item": "Before the recording"},
        _flash(t=5.0),
        _scene(LOBBY, t=5.05),
        {"event": "zone_enter", "t": 6.0, "zone": "Lobby", "puzzle": ""},
        {"event": "door", "t": 7.0, "open": True, "path": "HALL/BadgeDoor/Frame"},
        {"event": "door", "t": 8.0, "open": False, "path": "Lift"},
        {"event": "lock", "t": 9.0, "locked": False, "path": "NORTH_ROOM/PlateDoor/Frame"},
        {"event": "pickup", "t": 10.0, "item": "Crate"},
        {"event": "quest", "t": 11.0, "quest": "find_exit", "step": "completed"},
        {"event": "pause", "t": 12.0},
        {"event": "resume", "t": 13.0},
        {"event": "input", "t": 13.5, "action": "jump", "pressed": True},
        {"event": "zone_exit", "t": 14.0, "zone": "Lobby", "puzzle": ""},
        {"event": "pickup", "t": 200.0, "item": "After the recording"},
    ]
    data = spatial.enrich(_data([], duration_s=100.0), events, video_flash_s=3.0)
    assert data["events"] == [
        {"t": 5.0, "kind": "door", "label": "Badge door opened (Hall)"},
        {"t": 6.0, "kind": "door", "label": "Lift closed"},
        {"t": 7.0, "kind": "lock", "label": "Plate door unlocked (North room)"},
        {"t": 8.0, "kind": "pickup", "label": "Picked up Crate"},
        {"t": 9.0, "kind": "quest", "label": "Find exit completed"},
        {"t": 10.0, "kind": "pause", "label": "Paused"},
        {"t": 11.0, "kind": "resume", "label": "Resumed"},
    ]
    assert data["zones"] == [{"zone": "Lobby", "puzzle": "", "start_s": 4.0, "end_s": 12.0}]


def test_command_line_upgrades_a_file_in_the_old_route_format(tmp_path):
    old = json.loads(FINDINGS.read_text(encoding="utf-8"))
    old["route"] = {"scene": LOBBY, "map": "lobby", "points": [[0.0, 1.0, 2.0]], "heat": []}
    counts = {"stuck": 0, "confused": 0, "surprised": 0, "suspected_bug": 0}
    old["summary"] = {"verdict": "old", "lost_s": 0, "counts": counts, "kept": 0, "dropped": 0}
    old["findings"][0]["at"] = {"x": 1.0, "z": 2.0}
    path = tmp_path / "findings.json"
    path.write_text(json.dumps(old), encoding="utf-8")
    with pytest.raises(ValueError, match="summary.problems"):
        findings_module.load(path)
    del old["summary"]
    path.write_text(json.dumps(old), encoding="utf-8")
    with pytest.raises(ValueError, match="route.maps"):
        findings_module.load(path)
    assert spatial.main([str(path), "--log", str(REAL_LOG), "--video-flash-s", "2.0"]) == 0
    data = findings_module.load(path)
    assert data["route"]["maps"] == ["lobby", "lobby_upper"]
    assert "problems" in data["summary"]
