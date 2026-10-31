import json
import re
from pathlib import Path

import pytest

from analyzer import findings

SAMPLE = Path(__file__).parent / "fixtures" / "findings_sample.json"
REDESIGN = Path(__file__).parent / "fixtures" / "findings_redesign.json"


def _sample_data():
    return json.loads(SAMPLE.read_text(encoding="utf-8"))


def _redesign_data():
    return json.loads(REDESIGN.read_text(encoding="utf-8"))


def _set(path, value):
    def change(data):
        target = data
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = value

    return change


def _write(tmp_path, data):
    path = tmp_path / "findings.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_load_accepts_sample():
    data = findings.load(SAMPLE)
    assert data["format"] == 1
    assert data["session"]["id"] == "sample-01"
    assert len(data["findings"]) == 6


def test_load_rejects_missing_time_s(tmp_path):
    data = _sample_data()
    del data["findings"][0]["time_s"]
    with pytest.raises(ValueError, match=r"time_s"):
        findings.load(_write(tmp_path, data))


def test_load_rejects_bad_kind(tmp_path):
    data = _sample_data()
    data["findings"][0]["kind"] = "bored"
    with pytest.raises(ValueError, match=r"kind"):
        findings.load(_write(tmp_path, data))


def test_load_rejects_duplicate_id(tmp_path):
    data = _sample_data()
    data["findings"][1]["id"] = data["findings"][0]["id"]
    with pytest.raises(ValueError, match=r"id"):
        findings.load(_write(tmp_path, data))


def test_load_rejects_time_past_end(tmp_path):
    data = _sample_data()
    data["findings"][0]["time_s"] = data["session"]["duration_s"] + 1
    with pytest.raises(ValueError, match=r"time_s"):
        findings.load(_write(tmp_path, data))


def test_load_accepts_the_optional_blocks():
    data = findings.load(REDESIGN)
    assert data["summary"]["kept"] == 9
    assert len(data["route"]["points"]) == 40
    assert len(data["cross_player"]) == 3
    assert data["route"]["maps"] == ["lobby", "lobby_upper"]
    assert len(data["summary"]["problems"]) == 2


def test_a_summary_without_problems_is_the_old_format(tmp_path):
    data = _redesign_data()
    del data["summary"]["problems"]
    with pytest.raises(ValueError, match=r"summary\.problems: missing"):
        findings.load(_write(tmp_path, data))


def test_zones_events_and_a_dropped_pin_are_optional(tmp_path):
    data = _redesign_data()
    del data["zones"], data["events"]
    for finding in data["findings"]:
        if finding["check"]["verdict"] == "drop":
            finding.pop("at", None)
    assert findings.load(_write(tmp_path, data))["findings"]


@pytest.mark.parametrize(
    "path, value, field",
    [
        (["session", "player"], 5, "session.player"),
        (["summary", "lost_s"], "285", "summary.lost_s"),
        (["summary", "counts", "stuck"], True, "summary.counts.stuck"),
        (["summary", "kept"], 9.5, "summary.kept"),
        (["route", "maps"], "lobby", "route.maps"),
        (["route", "maps"], [], "route.maps"),
        (["route", "points", 0], [1.0, 2.0, 3.0], "route.points[0]"),
        (["route", "points", 0, 3], 2, "route.points[0].floor"),
        (["route", "heat", 0, "r_m"], "2", "route.heat[0].r_m"),
        (["route", "heat", 0, "floor"], -1, "route.heat[0].floor"),
        (["route", "floor_spans", 0, "end_s"], None, "route.floor_spans[0].end_s"),
        (["markers", 0, "t"], "1", "markers[0].t"),
        (["markers", 0, "floor"], 0.0, "markers[0].floor"),
        (["markers", 0, "moment"], 7, "markers[0].moment"),
        (["zones", 0, "puzzle"], None, "zones[0].puzzle"),
        (["zones", 0, "end_s"], "open", "zones[0].end_s"),
        (["events", 0, "kind"], "death", "events[0].kind"),
        (["events", 0, "label"], None, "events[0].label"),
        (["summary", "problems", 0, "moments"], [], "summary.problems[0].moments"),
        (["summary", "problems", 0, "friction"], "learning", "summary.problems[0].friction"),
        (["summary", "problems", 0, "resolved"], "yes", "summary.problems[0].resolved"),
        (["summary", "problems", 0, "attempts"], 1.5, "summary.problems[0].attempts"),
        (["cross_player", 0, "of"], "3", "cross_player[0].of"),
        (
            ["cross_player", 0, "players", 0, "here"],
            "yes",
            "cross_player[0].players[0].here",
        ),
        (["findings", 0, "at", "x"], "left", "findings[0].at.x"),
        (["findings", 0, "at", "floor"], 2, "findings[0].at.floor"),
        (["findings", 0, "at"], "here", "findings[0].at"),
        (
            ["findings", 0, "check", "resolved_after_s"],
            "soon",
            "findings[0].check.resolved_after_s",
        ),
    ],
)
def test_load_rejects_bad_new_field(tmp_path, path, value, field):
    data = _redesign_data()
    _set(path, value)(data)
    with pytest.raises(ValueError, match=re.escape(field)):
        findings.load(_write(tmp_path, data))
