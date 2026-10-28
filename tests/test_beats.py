from analyzer.beats import assign_beats, zone_intervals


def _finding(fid, time_s, game_state="Fan platform by the blue barrier."):
    return {
        "id": fid,
        "time_s": time_s,
        "game_state": game_state,
        "summary": "Moment.",
        "check": {"verdict": "keep"},
    }


def test_assign_beats_groups_one_puzzle_into_attempts():
    findings = [
        _finding("f1", 444.0),
        _finding("f2", 475.0),
        _finding("f3", 502.0),
        # Away solving something else, then back: a second attempt.
        _finding("f4", 610.0, game_state="Hexahedron jump by the gate."),
        _finding("f5", 890.0),
        _finding("f6", 920.0),
    ]
    findings[0]["check"] = {"verdict": "keep"}
    assign_beats(findings)
    puzzle = [f for f in findings if f["game_state"].startswith("Fan")]
    assert [f["beat"]["attempt"] for f in puzzle] == [1, 1, 1, 2, 2]
    assert puzzle[0]["beat"]["zone"] is None


def test_assign_beats_uses_log_zones_when_present():
    events = [
        {"t": 1.0, "event": "sync_flash"},
        {"t": 11.0, "event": "zone_enter", "zone": "Laboratory", "puzzle": "Keypad door"},
        {"t": 41.0, "event": "zone_exit", "zone": "Laboratory", "puzzle": "Keypad door"},
    ]
    zones = zone_intervals(events, 101.0)
    assert zones[0]["start_s"] == 111.0 and zones[0]["end_s"] == 141.0
    findings = [_finding("f1", 120.0, game_state="Whatever the model said.")]
    assign_beats(findings, zones=zones)
    assert findings[0]["beat"]["zone"] == "Laboratory"
    assert findings[0]["beat"]["puzzle"] == "Keypad door"


def test_assign_beats_leaves_dropped_alone():
    finding = _finding("f1", 10.0)
    finding["check"] = {"verdict": "drop"}
    assign_beats([finding])
    assert "beat" not in finding


def test_assign_beats_groups_label_variants_of_one_puzzle():
    findings = [
        {**_finding("f1", 444.0), "check": {"verdict": "keep", "puzzle": "fan and blue barrier"}},
        {**_finding("f2", 475.0), "check": {"verdict": "keep", "puzzle": "blue barrier and hexahedron"}},
        {**_finding("f3", 502.0), "check": {"verdict": "keep", "puzzle": "fan blue barrier plate"}},
    ]
    assign_beats(findings)
    assert len({f["beat"]["puzzle"] for f in findings}) == 1


def test_assign_beats_zone_reentry_is_a_new_attempt():
    events = [
        {"t": 1.0, "event": "sync_flash"},
        {"t": 11.0, "event": "zone_enter", "zone": "Lab", "puzzle": "Door"},
        {"t": 21.0, "event": "zone_exit", "zone": "Lab", "puzzle": "Door"},
        {"t": 31.0, "event": "zone_enter", "zone": "Lab", "puzzle": "Door"},
        {"t": 41.0, "event": "zone_exit", "zone": "Lab", "puzzle": "Door"},
    ]
    zones = zone_intervals(events, 101.0)
    findings = [_finding("f1", 115.0), _finding("f2", 135.0)]
    assign_beats(findings, zones=zones)
    assert [f["beat"]["attempt"] for f in findings] == [1, 2]
