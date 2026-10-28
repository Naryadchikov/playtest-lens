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


def _position(t, x=0.0, z=0.0):
    return {"event": "position", "t": t, "x": x, "y": 0.8, "z": z}


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
    assert data["route"]["points"][0] == [14.0, 1.0, 2.0]
    assert data["route"]["points"][-1] == [15.5, 3.0, 4.0]
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
    assert data["route"]["map"] == "laboratory"


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
    assert near["at"] == {"x": 7.0, "z": 7.0}
    assert "at" not in far
    assert "at" not in dropped


def test_the_pin_nudge_keeps_two_close_pins_apart_deterministically():
    events = [_flash(), _scene(LOBBY, t=0.5), _position(10.0, x=5.0, z=5.0)]
    first = _finding("f1", 1, time_s=10.0)
    second = _finding("f2", 2, time_s=10.5)
    data = _data([first, second])
    spatial.enrich(data, events, video_flash_s=0.0)
    meta = _lobby_meta()
    assert first["at"] == {"x": 5.0, "z": 5.0}
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
    page = render_html(data)
    assert page.count('class="pin f9"') == 2
    assert 'class="pin f9" id="pin-f1" href="#m1"' in page
    assert '<g class="pin f9" id="pin-f2"' in page
    assert 'class="f9line"' in page


def test_lost_s_counts_overlapping_spans_once():
    events = [_flash(), _scene(LOBBY, t=0.5), _position(1.0)]
    findings = [
        _finding("f1", 1, time_s=10.0, end_s=20.0, kind="stuck"),
        _finding("f2", 2, time_s=15.0, end_s=25.0, kind="confused"),
        _finding("f3", 3, time_s=30.0, end_s=40.0, kind="stuck"),
        _finding("f4", 4, time_s=12.0, end_s=18.0, kind="surprised"),
        _finding("f5", None, time_s=0.0, end_s=50.0, kind="stuck", verdict="drop"),
    ]
    data = spatial.enrich(_data(findings), events, video_flash_s=0.0)
    assert data["summary"]["lost_s"] == 25.0
    assert data["summary"]["counts"] == {
        "stuck": 2,
        "confused": 1,
        "surprised": 1,
        "suspected_bug": 0,
    }
    assert data["summary"]["kept"] == 4
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
    assert first["route"]["map"] == "lobby"
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
    assert data["summary"]["lost_s"] == 5.0

    page = render_html(data)
    assert 'id="where"' in page
    assert 'class="tiles"' in page
    assert 'fill="url(#heat)"' in page
    assert "<polyline" in page
    assert 'id="pin-m1"' in page
    assert "3 moments worth a look: 1 stuck, 1 confused, 1 surprised." in page


def test_no_sync_flash_raises():
    with pytest.raises(ValueError, match="sync_flash"):
        spatial.enrich(_data([]), [_scene(LOBBY)], video_flash_s=0.0)
