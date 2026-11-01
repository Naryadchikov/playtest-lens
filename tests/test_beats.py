import json
from pathlib import Path

from analyzer import beats as beats_module
from analyzer import findings as findings_module
from analyzer.beats import assign_beats, zone_intervals


def _finding(fid, time_s, game_state="Fan platform by the blue barrier."):
    return {
        "id": fid,
        "time_s": time_s,
        "game_state": game_state,
        "summary": "Moment.",
        "check": {"verdict": "keep"},
    }


def _labelled(fid, time_s, area, puzzle, verdict="keep"):
    return {
        "id": fid,
        "time_s": time_s,
        "game_state": puzzle,
        "summary": "Moment.",
        "check": {"verdict": verdict, "area": area, "puzzle": puzzle},
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


def test_return_after_solving_elsewhere_is_attempt_two_even_when_soon():
    findings = [
        _labelled("f1", 444.0, "Yellow Puzzle Area", "fan and blue barrier"),
        _labelled("f2", 475.0, "Yellow Puzzle Area", "fan and blue barrier"),
        _labelled("d1", 523.0, "Yellow Puzzle Area", "fan on pressure plate", verdict="drop"),
        _labelled("d2", 574.0, "Yellow Puzzle Area", "fan on pressure plate", verdict="drop"),
        _labelled("f3", 592.0, "Yellow Puzzle Area", "fan and blue barrier"),
        _labelled("f4", 610.0, "Yellow Puzzle Area", "fan and blue barrier"),
    ]
    assign_beats(findings)
    kept = [f for f in findings if f["check"]["verdict"] == "keep"]
    assert [f["beat"]["attempt"] for f in kept] == [1, 1, 2, 2]
    assert kept[0]["beat"]["area"] == "Yellow Puzzle Area"
    assert kept[0]["beat"]["puzzle_number"] == 1
    assert kept[0]["beat"]["attempt_start_s"] == 444.0
    assert kept[0]["beat"]["attempt_end_s"] == 475.0
    assert kept[2]["beat"]["attempt_start_s"] == 592.0
    assert kept[2]["beat"]["attempt_end_s"] == 610.0
    assert "beat" not in findings[2]


def test_one_stray_moment_elsewhere_does_not_start_attempt_two():
    findings = [
        _labelled("f1", 10.0, "Yellow Puzzle Area", "fan and blue barrier"),
        _labelled("d1", 20.0, "Yellow Puzzle Area", "another puzzle", verdict="drop"),
        _labelled("f2", 30.0, "Yellow Puzzle Area", "fan and blue barrier"),
    ]
    assign_beats(findings)
    assert [f["beat"]["attempt"] for f in findings if f["check"]["verdict"] == "keep"] == [1, 1]


def test_puzzle_numbers_are_per_area_in_first_visit_order():
    findings = [
        _labelled("f1", 10.0, "Yellow Puzzle Area", "fan and blue barrier"),
        _labelled("f2", 20.0, "Yellow Puzzle Area", "sigil gate"),
        _labelled("f3", 30.0, "Blue Puzzle Area", "fan and blue barrier"),
    ]
    assign_beats(findings)
    assert [f["beat"]["puzzle_number"] for f in findings] == [1, 2, 1]
    assert [f["beat"]["area"] for f in findings] == [
        "Yellow Puzzle Area",
        "Yellow Puzzle Area",
        "Blue Puzzle Area",
    ]


def test_dropped_only_puzzle_takes_no_number():
    findings = [
        _labelled("d1", 10.0, "Yellow Puzzle Area", "sigil gate", verdict="drop"),
        _labelled("f1", 20.0, "Yellow Puzzle Area", "fan and blue barrier"),
    ]
    assign_beats(findings)
    assert findings[1]["beat"]["puzzle_number"] == 1


def test_sigil_word_alone_never_joins_distinct_puzzles():
    findings = [
        _labelled("f1", 100.0, "Initiation temple courtyard", "Main gate sigil lock"),
        _labelled("f2", 200.0, "Gate sigil collection", "Raised platform green sigil"),
        _labelled("f3", 300.0, "Fencing sigil room", "Fencing L sigil puzzle"),
    ]
    assign_beats(findings)
    assert len({f["beat"]["puzzle"] for f in findings}) == 3


def test_sigil_never_chains_distinct_puzzles_within_a_minute():
    first = _labelled("f1", 200.0, "Gate sigil collection", "Raised platform green sigil")
    first["summary"] = "Player climbs to the raised platform and collects the green sigil."
    first["game_state"] = "Raised platform with a green sigil."
    second = _labelled("f2", 230.0, "Fencing sigil room", "Fencing L sigil puzzle")
    second["summary"] = "Player repeatedly fails to get the hexahedron over the spiked fence."
    second["game_state"] = "Spiked fence in the Fencing room."
    assign_beats([first, second])
    assert first["beat"]["puzzle"] != second["beat"]["puzzle"]


def test_zone_names_win_over_checker_words_inside_a_volume():
    events = [
        {"t": 1.0, "event": "sync_flash"},
        {"t": 11.0, "event": "zone_enter", "zone": "Lab", "puzzle": "Door"},
        {"t": 41.0, "event": "zone_exit", "zone": "Lab", "puzzle": "Door"},
    ]
    zones = zone_intervals(events, 101.0)
    outside = _labelled("f1", 70.0, "Lab courtyard", "Fan lift")
    outside["summary"] = "Player rides the fan lift up."
    inside = _labelled("f2", 120.0, "Lab courtyard", "fan thing")
    inside["summary"] = "Player mentions the fan while standing at the door."
    inside["game_state"] = "A locked door, a fan nearby."
    assign_beats([outside, inside], zones=zones)
    assert inside["beat"]["puzzle"] == "Door"
    assert inside["beat"]["area"] == "Lab"
    assert inside["beat"]["zone"] == "Lab"
    assert inside["beat"]["attempt"] == 1


def test_colour_areas_never_collapse_through_a_generic_parent():
    findings = [
        _labelled("f1", 10.0, "Puzzle Area", "gate lock"),
        _labelled("f2", 20.0, "Yellow Puzzle Area", "yellow fan"),
        _labelled("f3", 30.0, "Blue Puzzle Area", "blue fan"),
    ]
    assign_beats(findings)
    assert [f["beat"]["area"] for f in findings] == [
        "Puzzle Area",
        "Yellow Puzzle Area",
        "Blue Puzzle Area",
    ]
    assert len({f["beat"]["puzzle"] for f in findings}) == 3


def test_generic_parent_with_shared_object_never_absorbs_colour_puzzles():
    findings = [
        _labelled("f1", 10.0, "Puzzle Area", "fan lock"),
        _labelled("f2", 20.0, "Yellow Puzzle Area", "yellow fan"),
        _labelled("f3", 30.0, "Blue Puzzle Area", "blue fan"),
    ]
    assign_beats(findings)
    assert [f["beat"]["area"] for f in findings] == [
        "Puzzle Area",
        "Yellow Puzzle Area",
        "Blue Puzzle Area",
    ]
    assert len({f["beat"]["puzzle"] for f in findings}) == 3


def test_generic_temple_parent_never_absorbs_colour_areas():
    findings = [
        _labelled("f1", 10.0, "Temple Ruins", "gate lock"),
        _labelled("f2", 20.0, "Yellow Temple Ruins", "yellow fan"),
        _labelled("f3", 30.0, "Blue Temple Ruins", "blue fan"),
    ]
    assign_beats(findings)
    assert [f["beat"]["area"] for f in findings] == [
        "Temple Ruins",
        "Yellow Temple Ruins",
        "Blue Temple Ruins",
    ]
    assert len({f["beat"]["puzzle"] for f in findings}) == 3


def test_zone_two_word_name_is_exact_not_fuzzy():
    events = [
        {"t": 1.0, "event": "sync_flash"},
        {"t": 11.0, "event": "zone_enter", "zone": "East Lab", "puzzle": "Door"},
        {"t": 41.0, "event": "zone_exit", "zone": "East Lab", "puzzle": "Door"},
    ]
    zones = zone_intervals(events, 101.0)
    findings = [
        _labelled("f1", 70.0, "East Lab Wing", "Door"),
        _labelled("f2", 120.0, "East Lab Wing", "Door"),
    ]
    assign_beats(findings, zones=zones)
    assert findings[1]["beat"]["area"] == "East Lab"
    assert findings[1]["beat"]["puzzle"] == "Door"
    assert findings[1]["beat"]["attempt"] == 1


def test_joined_labels_do_not_arm_the_next_puzzle():
    findings = [
        _labelled("f1", 0.0, "Courtyard", "fan lift"),
        _labelled("f2", 30.0, "Courtyard", "keypad door"),
        _labelled("f3", 50.0, "Courtyard", "laser grid"),
    ]
    findings[0]["summary"] = "Rides the fan."
    findings[1]["summary"] = "The fan is still running beside the keypad door."
    findings[2]["summary"] = "Steps through the keypad."
    findings[2]["game_state"] = "A keypad lock."
    assign_beats(findings)
    assert findings[2]["beat"]["puzzle"] == "laser grid"


def test_fuzzy_joined_labels_do_not_arm_the_next_puzzle():
    findings = [
        _labelled("f1", 0.0, "Courtyard", "blue barrier fan plate"),
        _labelled("f2", 200.0, "Courtyard", "blue barrier keypad plate"),
        _labelled("f3", 230.0, "Courtyard", "laser hall"),
    ]
    findings[1]["summary"] = "Works at the plate."
    findings[2]["summary"] = "Uses the keypad."
    assign_beats(findings)
    assert findings[2]["beat"]["puzzle"] == "laser hall"


def test_identical_label_joins_the_most_recent_colour_room():
    findings = [
        _labelled("f1", 10.0, "Yellow Temple Ruins", "fan lock"),
        _labelled("f2", 20.0, "Blue Temple Ruins", "fan lock"),
        _labelled("f3", 30.0, "Temple Ruins", "fan lock"),
    ]
    assign_beats(findings)
    assert findings[2]["beat"]["area"] == "Blue Temple Ruins"
    assert findings[2]["beat"]["attempt"] == 1


def test_colour_named_areas_with_shared_words_stay_separate():
    findings = [
        _labelled("f1", 10.0, "Blue barrier temple chamber", "fan and blue barrier"),
        _labelled("f2", 20.0, "Yellow barrier temple chamber", "fan and blue barrier"),
    ]
    assign_beats(findings)
    assert [f["beat"]["area"] for f in findings] == [
        "Blue barrier temple chamber",
        "Yellow barrier temple chamber",
    ]
    assert [f["beat"]["puzzle_number"] for f in findings] == [1, 1]


def test_zone_visits_number_in_time_order_with_unzoned_moments():
    events = [
        {"t": 1.0, "event": "sync_flash"},
        {"t": 11.0, "event": "zone_enter", "zone": "Lab", "puzzle": "Door"},
        {"t": 21.0, "event": "zone_exit", "zone": "Lab", "puzzle": "Door"},
    ]
    zones = zone_intervals(events, 101.0)
    findings = [
        _labelled("f1", 105.0, "Lab", "Door"),
        _labelled("f2", 115.0, "Lab", "Door"),
        _labelled("f3", 130.0, "Lab", "Door"),
    ]
    assign_beats(findings, zones=zones)
    # Only the moment inside the volume (111 to 121) is a Puzzle moment.
    assert [f["beat"]["attempt"] for f in findings] == [None, 1, None]
    assert [f["beat"]["puzzle_number"] for f in findings] == [None, 1, None]


def test_one_kept_moment_elsewhere_opens_the_next_attempt():
    findings = [
        _labelled("f1", 10.0, "Yellow Puzzle Area", "fan and blue barrier"),
        _labelled("f2", 20.0, "Yellow Puzzle Area", "sigil gate"),
        _labelled("f3", 30.0, "Yellow Puzzle Area", "fan and blue barrier"),
    ]
    assign_beats(findings)
    assert [f["beat"]["attempt"] for f in findings] == [1, 1, 2]


def test_unzoned_moment_after_a_volume_visit_is_an_area_visit():
    events = [
        {"t": 1.0, "event": "sync_flash"},
        {"t": 11.0, "event": "zone_enter", "zone": "Lab", "puzzle": "Door"},
        {"t": 21.0, "event": "zone_exit", "zone": "Lab", "puzzle": "Door"},
    ]
    zones = zone_intervals(events, 101.0)
    findings = [
        _labelled("f1", 115.0, "Lab", "Door"),
        _labelled("f2", 130.0, "Lab", "Door"),
    ]
    assign_beats(findings, zones=zones)
    # f1 is inside the volume (111 to 121), f2 is not: it is an area visit.
    assert [(f["beat"]["puzzle_number"], f["beat"]["attempt"]) for f in findings] == [
        (1, 1),
        (None, None),
    ]
    assert findings[1]["beat"]["puzzle"] is None


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


def test_a_step_out_and_back_within_seconds_is_one_visit():
    events = [
        {"t": 1.0, "event": "sync_flash"},
        {"t": 11.0, "event": "zone_enter", "zone": "Archive", "puzzle": "Code Lock"},
        {"t": 21.0, "event": "zone_exit", "zone": "Archive", "puzzle": "Code Lock"},
        {"t": 21.2, "event": "zone_enter", "zone": "Archive", "puzzle": "Code Lock"},
        {"t": 41.0, "event": "zone_exit", "zone": "Archive", "puzzle": "Code Lock"},
    ]
    zones = zone_intervals(events, 101.0)
    assert [(z["start_s"], z["end_s"]) for z in zones] == [(111.0, 141.0)]
    findings = [_finding("f1", 115.0), _finding("f2", 135.0)]
    assign_beats(findings, zones=zones)
    assert [f["beat"]["attempt"] for f in findings] == [1, 1]


def test_a_moment_just_before_a_puzzle_volume_joins_it():
    events = [
        {"t": 1.0, "event": "sync_flash"},
        {"t": 11.0, "event": "zone_enter", "zone": "Archive", "puzzle": "Code Lock"},
        {"t": 21.0, "event": "zone_exit", "zone": "Archive", "puzzle": "Code Lock"},
    ]
    zones = zone_intervals(events, 101.0)
    findings = [_labelled("f1", 110.5, "Archive", "Code Lock"), _labelled("f2", 115.0, "Archive", "Code Lock")]
    assign_beats(findings, zones=zones)
    assert [(f["beat"]["puzzle"], f["beat"]["attempt"]) for f in findings] == [("Code Lock", 1), ("Code Lock", 1)]


def test_colourless_area_wording_joins_the_most_recent_colour_room():
    findings = [
        _labelled("f1", 10.0, "Yellow Temple Ruins", "green sigil plinth"),
        _labelled("f2", 20.0, "Blue Temple Ruins", "green sigil pedestal marker"),
        _labelled("f3", 30.0, "Temple Ruins", "green sigil pedestal"),
    ]
    assign_beats(findings)
    assert findings[2]["beat"]["area"] == "Blue Temple Ruins"


def test_identical_label_beats_chaining_after_a_long_gap():
    findings = [
        _labelled("f1", 0.0, "Courtyard", "fan lock"),
        _labelled("f2", 100.0, "Courtyard", "laser grid"),
        _labelled("f3", 130.0, "Courtyard", "fan lock"),
    ]
    findings[2]["summary"] = "Back at the fan lock after the laser grid."
    assign_beats(findings)
    assert findings[2]["beat"]["puzzle"] == "fan lock"
    assert findings[2]["beat"]["attempt"] == 2


def _two_volumes():
    events = [
        {"t": 1.0, "event": "sync_flash"},
        {"t": 11.0, "event": "zone_enter", "zone": "Vault", "puzzle": "Code Lock"},
        {"t": 21.0, "event": "zone_exit", "zone": "Vault", "puzzle": "Code Lock"},
        {"t": 31.0, "event": "zone_enter", "zone": "Hall", "puzzle": ""},
        {"t": 41.0, "event": "zone_exit", "zone": "Hall", "puzzle": ""},
        {"t": 61.0, "event": "zone_enter", "zone": "Hall", "puzzle": ""},
        {"t": 71.0, "event": "zone_exit", "zone": "Hall", "puzzle": ""},
    ]
    return events, zone_intervals(events, 101.0)


def test_only_a_volume_with_a_puzzle_line_is_a_puzzle():
    _events, zones = _two_volumes()
    findings = [
        _labelled("f1", 115.0, "Vault", "Code Lock"),
        _labelled("f2", 135.0, "Hall", "Hall"),
        _labelled("f3", 200.0, "Roof", "Whatever"),
    ]
    assign_beats(findings, zones=zones)
    puzzle, room, outside = (f["beat"] for f in findings)
    assert (puzzle["puzzle"], puzzle["puzzle_number"], puzzle["attempt"]) == ("Code Lock", 1, 1)
    for beat in (room, outside):
        assert beat["puzzle"] is None
        assert beat["puzzle_number"] is None
        assert beat["attempt"] is None
    assert room["area"] == "Hall" and room["zone"] == "Hall"
    assert (room["attempt_start_s"], room["attempt_end_s"]) == (131.0, 141.0)
    assert outside["area"] == "Roof" and outside["zone"] is None
    assert outside["attempt_start_s"] == 200.0 and outside["attempt_end_s"] == 200.0
    assert room["index"] == 1


def test_puzzle_numbers_skip_area_visits():
    _events, zones = _two_volumes()
    findings = [
        _labelled("f1", 135.0, "Hall", "Hall"),
        _labelled("f2", 115.0, "Vault", "Code Lock"),
    ]
    assign_beats(findings, zones=zones)
    assert findings[1]["beat"]["puzzle_number"] == 1


def test_empty_puzzle_volume_visited_twice_gives_two_visits():
    _events, zones = _two_volumes()
    findings = [
        _labelled("f1", 135.0, "Hall", "Hall"),
        _labelled("f2", 165.0, "Hall", "Hall"),
    ]
    assign_beats(findings, zones=zones)
    starts = [f["beat"]["attempt_start_s"] for f in findings]
    assert starts == [131.0, 161.0]


def test_overlapping_boxes_with_one_name_keep_their_own_intervals():
    events = [
        {"t": 1.0, "event": "sync_flash"},
        {"t": 11.0, "event": "zone_enter", "zone": "Archive", "puzzle": "Code Lock"},
        {"t": 15.0, "event": "zone_enter", "zone": "Archive", "puzzle": ""},
        {"t": 18.0, "event": "zone_exit", "zone": "Archive", "puzzle": "Code Lock"},
        {"t": 21.0, "event": "zone_exit", "zone": "Archive", "puzzle": ""},
    ]
    zones = zone_intervals(events, 101.0)
    assert [(z["puzzle"], z["start_s"], z["end_s"]) for z in zones] == [
        ("Code Lock", 111.0, 118.0),
        ("", 115.0, 121.0),
    ]


def _cli_inputs(tmp_path):
    events, _zones = _two_volumes()
    log = tmp_path / "session.jsonl"
    log.write_text("\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")
    source = json.loads(
        (Path(__file__).parent / "fixtures" / "spatial_findings.json").read_text(encoding="utf-8")
    )
    source["session"]["duration_s"] = 300.0
    source["findings"][0]["time_s"] = 115.0
    source["findings"][1]["time_s"] = 135.0
    source["findings"][2]["time_s"] = 165.0
    findings = tmp_path / "findings.json"
    findings.write_text(json.dumps(source), encoding="utf-8")
    return findings, log


def test_cli_writes_a_loadable_file_and_leaves_the_input(tmp_path, capsys):
    findings, log = _cli_inputs(tmp_path)
    before = findings.read_bytes()
    out = tmp_path / "out.json"
    code = beats_module.main(
        [str(findings), "--log", str(log), "--video-flash-s", "101.0", "-o", str(out)]
    )
    assert code == 0
    assert findings.read_bytes() == before
    data = findings_module.load(out)
    kept = [f for f in data["findings"] if f["check"]["verdict"] == "keep"]
    assert [f["beat"]["puzzle"] for f in kept] == ["Code Lock", None, None]
    assert [f["beat"]["zone"] for f in kept] == ["Vault", "Hall", "Hall"]


def test_cli_without_output_refuses_and_leaves_the_input(tmp_path, capsys):
    findings, log = _cli_inputs(tmp_path)
    before = findings.read_bytes()
    code = beats_module.main([str(findings), "--log", str(log), "--video-flash-s", "101.0"])
    assert code == 1
    assert "-o is required" in capsys.readouterr().err
    assert findings.read_bytes() == before


def test_cli_refuses_to_write_over_its_input(tmp_path, capsys):
    findings, log = _cli_inputs(tmp_path)
    before = findings.read_bytes()
    code = beats_module.main(
        [str(findings), "--log", str(log), "--video-flash-s", "101.0", "-o", str(findings)]
    )
    assert code == 1
    assert findings.read_bytes() == before
