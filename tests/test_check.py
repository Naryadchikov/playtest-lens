import json
from pathlib import Path

import pytest

from analyzer import findings as findings_module
from analyzer import log_candidates
from analyzer.check import build_prompt, clamp_time, engine_name, log_slice_text, merge_candidates, merge_same_moment, parse_check, run_checks, store_clip_path, verified_quote

FIXTURE = Path(__file__).parent / "fixtures" / "check_reply.json"
CAUSE_FIXTURE = Path(__file__).parent / "fixtures" / "check_reply_cause.json"
TEMPLATE = (Path(__file__).parent.parent / "analyzer" / "prompts" / "check.md").read_text(
    encoding="utf-8"
)

CANDIDATES = [
    {"time_s": 502.0, "kind": "stuck", "reason": "Cube behind barrier.", "quote": "I can't take it from here"},
    {"time_s": 853.0, "kind": "surprised", "reason": "Voice speaks.", "quote": None},
]


def test_parse_check_accepts_fixture_and_rejects_bad_verdict():
    reply = json.loads(FIXTURE.read_text(encoding="utf-8"))
    parsed = parse_check(reply["output_text"])
    assert parsed["verdict"] == "keep"
    assert parsed["area"] == "temple entrance"
    with pytest.raises(ValueError, match="invalid area"):
        parse_check('{"verdict": "keep", "kind": "confused", "friction": "learning", "resolved": "unknown", "note": "x", "summary": "y", "quote": null, "game_state": null, "puzzle": null, "area": []}')
    with pytest.raises(ValueError, match="invalid verdict"):
        parse_check('{"verdict": "maybe", "note": "x", "summary": "y", "quote": null, "game_state": null}')


def test_run_checks_keeps_and_drops_into_valid_findings(tmp_path):
    replies = {
        "c502.0.mp4": json.loads(FIXTURE.read_text(encoding="utf-8")),
        "c853.0.mp4": {
            "output_text": '{"verdict": "drop", "kind": "surprised", "friction": "learning", "resolved": "unknown", "note": "A game voice line, the player says nothing.", "summary": "Elohim speaks.", "quote": null, "game_state": "Voice line playing.", "puzzle": null, "area": null}'
        },
    }

    def clip_for(candidate):
        path = tmp_path / f"c{candidate['time_s']:05.1f}.mp4"
        return path, candidate["time_s"] - 10, candidate["time_s"] + 10

    def transcript_for(clip_path):
        return "I can't take it from here" if "502" in clip_path.name else ""

    def call_for(clip_path, prompt):
        assert "Cube behind barrier" in prompt or "Voice speaks" in prompt
        return replies[clip_path.name]

    findings = run_checks(
        CANDIDATES,
        model="muse-wonder-1.0",
        clip_for=clip_for,
        transcript_for=transcript_for,
        call_for=call_for,
        template=TEMPLATE,
    )
    assert findings[0]["check"]["verdict"] == "keep" and findings[0]["rank"] == 1
    assert findings[1]["check"]["verdict"] == "drop" and findings[1]["rank"] is None

    path = tmp_path / "findings.json"
    path.write_text(
        json.dumps(
            {
                "format": 1,
                "session": {"id": "s01", "recording": "s01.mp4", "duration_s": 930.0, "start_flash_s": None},
                "findings": findings,
            }
        ),
        encoding="utf-8",
    )
    assert findings_module.load(path)["findings"][0]["quote"] == "I can't take it from here"


def test_cause_is_kept_from_the_reply_and_null_when_missing_or_blank(tmp_path):
    reply = json.loads(CAUSE_FIXTURE.read_text(encoding="utf-8"))
    assert parse_check(reply["output_text"])["cause"] == "the gate the lever opens is out of sight from the lever"
    old = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert parse_check(old["output_text"])["cause"] is None
    blank = old["output_text"][:-1] + ', "cause": "  "}'
    assert parse_check(blank)["cause"] is None
    with pytest.raises(ValueError, match="invalid cause"):
        parse_check(old["output_text"][:-1] + ', "cause": ["gate"]}')

    findings = run_checks(
        CANDIDATES[:1],
        model="muse-spark-1.2-contributor",
        clip_for=lambda c: (tmp_path / "c.mp4", c["time_s"] - 10, c["time_s"] + 10),
        transcript_for=lambda clip: "did that do anything",
        call_for=lambda clip, prompt: reply,
        template=TEMPLATE,
    )
    assert findings[0]["check"]["cause"] == "the gate the lever opens is out of sight from the lever"


def test_store_clip_path_is_relative_to_findings_dir():
    stored = store_clip_path(
        Path("runs/check/talos-clips/c00052.00.mp4"), Path("runs/check/talos-findings.json")
    )
    assert stored == "talos-clips/c00052.00.mp4"


def test_merge_candidates_maps_log_kinds_and_dedupes_near_spark():
    spark = [{"time_s": 100.0, "kind": "stuck", "reason": "Barrier.", "quote": None}]
    log_cands = [
        {"time_s": 103.0, "end_s": 103.0, "kind": "death", "detail": "Died in Lab"},
        {"time_s": 200.0, "end_s": 230.0, "kind": "looking_around", "detail": "Still 30 s, view turning"},
        {"time_s": 300.0, "end_s": 300.0, "kind": "death", "detail": "Died in Lab"},
    ]
    merged = merge_candidates(spark, log_cands)
    assert [m["time_s"] for m in merged] == [100.0, 200.0, 300.0]
    assert merged[1]["kind"] == "confused" and merged[1]["_source"] == "event_log"
    assert merged[2]["kind"] == "stuck" and merged[2]["reason"] == "Died in Lab"


def test_clamp_time_never_passes_duration():
    assert clamp_time(15.006, 15.006) == 15.006
    assert clamp_time(930.126, 930.126) == 930.126
    assert clamp_time(5.0, 930.0) == 5.0


def test_verified_quote_must_come_from_transcript():
    transcript = "Okay so for now I think I'll take it with me. Can I do this? No, wait."
    assert verified_quote("Can I do this?", transcript) == "Can I do this?"
    assert verified_quote("I am completely lost here", transcript) is None
    assert verified_quote(None, transcript) is None


def test_prompt_and_log_slice():
    prompt = build_prompt(TEMPLATE, CANDIDATES[0], "some words", "")
    assert "502.0" in prompt and "some words" in prompt and "no event log" in prompt
    events = [
        {"t": 1.0, "event": "sync_flash"},
        {"t": 6.0, "event": "death"},
        {"t": 60.0, "event": "death"},
    ]
    # Flash at log 1.0 maps to video 101.0, so death at log 6.0 is video 106.0.
    text = log_slice_text(events, 101.0, 100.0, 120.0)
    assert text.count("death") == 1


def test_log_slice_carries_the_zone_open_at_clip_start():
    events = [
        {"t": 1.0, "event": "sync_flash"},
        {"t": 11.0, "event": "zone_enter", "zone": "Laboratory", "puzzle": "Keypad door"},
        {"t": 15.0, "event": "zone_enter", "zone": "Hall", "puzzle": ""},
        {"t": 20.0, "event": "zone_exit", "zone": "Hall", "puzzle": ""},
        {"t": 45.0, "event": "death"},
    ]
    # Video = log + 100. The clip 140 to 160 holds only the death at 145;
    # the Laboratory entry at 111 is still open, the Hall closed at 120.
    lines = log_slice_text(events, 101.0, 140.0, 160.0).splitlines()
    assert lines[0] == (
        '[video 111.0s, before this clip, still open] '
        '{"event": "zone_enter", "puzzle": "Keypad door", "zone": "Laboratory"}'
    )
    assert len(lines) == 2 and "Hall" not in "\n".join(lines)
    assert lines[1] == '[video 145.0s] {"event": "death", "t": 45.0}'


def test_log_slice_leaves_an_in_clip_zone_enter_as_it_was():
    events = [
        {"t": 1.0, "event": "sync_flash"},
        {"t": 45.0, "event": "zone_enter", "zone": "Laboratory", "puzzle": "Keypad door"},
    ]
    text = log_slice_text(events, 101.0, 140.0, 160.0)
    assert text == (
        '[video 145.0s] {"event": "zone_enter", "puzzle": "Keypad door", "t": 45.0, "zone": "Laboratory"}'
    )


def test_engine_name_reads_session_start_or_says_unknown():
    events = log_candidates.load_log(Path(__file__).parent / "fixtures" / "session_log.jsonl")
    assert engine_name(events) == "Godot 4.7.2-stable (official)"
    assert engine_name([]) == "unknown"


def test_build_prompt_names_the_engine():
    prompt = build_prompt(TEMPLATE, CANDIDATES[0], "some words", "", engine="Godot 4.7.2")
    assert "The game runs in Godot 4.7.2." in prompt
    default = build_prompt(TEMPLATE, CANDIDATES[0], "some words", "")
    assert "The game runs in unknown." in default


def _finding(index, time_s, kind, verdict, quote=None):
    return {
        "id": f"f{index}",
        "rank": None,
        "time_s": time_s,
        "end_s": None,
        "kind": kind,
        "summary": f"Summary {index}.",
        "quote": quote,
        "clip": None,
        "game_state": None,
        "sources": ["spark"],
        "check": {"verdict": verdict, "note": "Evidence.", "model": "m", "friction": "stuck", "resolved": "unknown", "puzzle": None, "area": None},
    }


def test_merge_same_moment_keeps_the_quoted_one_and_ranks_the_rest(tmp_path):
    findings = [
        _finding(1, 100.0, "suspected_bug", "keep"),
        _finding(2, 102.0, "suspected_bug", "drop"),
        _finding(3, 104.0, "suspected_bug", "keep", quote="it is broken"),
        _finding(4, 108.0, "suspected_bug", "keep"),
        _finding(5, 200.0, "stuck", "keep"),
        _finding(6, 206.0, "surprised", "keep"),
    ]
    merged = merge_same_moment(findings)
    assert [f["id"] for f in merged] == ["f2", "f3", "f5", "f6"]
    kept = [f for f in merged if f["check"]["verdict"] == "keep"]
    assert [f["id"] for f in kept] == ["f3", "f5", "f6"]
    assert [f["rank"] for f in kept] == [1, 2, 3]
    assert merged[0]["rank"] is None

    path = tmp_path / "findings.json"
    path.write_text(
        json.dumps(
            {
                "format": 1,
                "session": {"id": "s01", "recording": "s01.mp4", "duration_s": 930.0, "start_flash_s": None},
                "findings": merged,
            }
        ),
        encoding="utf-8",
    )
    assert len(findings_module.load(path)["findings"]) == 4


def test_merge_same_moment_folds_a_long_visit_and_keeps_the_other_kind():
    zones = [{"zone": "Archive", "puzzle": "", "start_s": 0.0, "end_s": 80.0}]
    findings = [
        _finding(1, 10.0, "stuck", "keep"),
        _finding(2, 20.0, "surprised", "keep"),
        _finding(3, 40.0, "stuck", "keep", quote="still here"),
    ]
    merged = merge_same_moment(findings, zones)
    assert [f["id"] for f in merged] == ["f2", "f3"]
    stuck = next(f for f in merged if f["id"] == "f3")
    assert stuck["quote"] == "still here"
    assert stuck["end_s"] == 40.0
    assert next(f for f in merged if f["id"] == "f2")["end_s"] is None


def test_merge_same_moment_starts_again_after_the_player_reenters():
    zones = [
        {"zone": "Archive", "puzzle": "", "start_s": 0.0, "end_s": 50.0},
        {"zone": "Archive", "puzzle": "", "start_s": 60.0, "end_s": 120.0},
    ]
    findings = [
        _finding(1, 10.0, "stuck", "keep"),
        _finding(2, 80.0, "stuck", "keep"),
    ]
    assert [f["id"] for f in merge_same_moment(findings, zones)] == ["f1", "f2"]


def test_merge_same_moment_prefers_the_puzzle_box_inside_the_room():
    zones = [
        {"zone": "Archive", "puzzle": "", "start_s": 0.0, "end_s": 100.0},
        {"zone": "Archive", "puzzle": "Code Lock", "start_s": 10.0, "end_s": 40.0},
    ]
    findings = [
        _finding(1, 20.0, "stuck", "keep"),
        _finding(2, 30.0, "stuck", "keep"),
        _finding(3, 50.0, "stuck", "keep"),
    ]
    merged = merge_same_moment(findings, zones)
    assert [f["id"] for f in merged] == ["f1", "f3"]
    assert next(f for f in merged if f["id"] == "f1")["end_s"] == 30.0
    assert next(f for f in merged if f["id"] == "f3")["end_s"] is None


def test_merge_same_moment_leaves_a_long_gap_alone_when_there_is_no_zone():
    findings = [
        _finding(1, 10.0, "stuck", "keep"),
        _finding(2, 40.0, "stuck", "keep"),
    ]
    assert [f["id"] for f in merge_same_moment(findings)] == ["f1", "f2"]
