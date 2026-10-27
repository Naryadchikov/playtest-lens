import json
from pathlib import Path

import pytest

from analyzer import findings as findings_module
from analyzer.check import build_prompt, clamp_time, log_slice_text, parse_check, run_checks, verified_quote

FIXTURE = Path(__file__).parent / "fixtures" / "check_reply.json"
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
    with pytest.raises(ValueError, match="invalid verdict"):
        parse_check('{"verdict": "maybe", "note": "x", "summary": "y", "quote": null, "game_state": null}')


def test_run_checks_keeps_and_drops_into_valid_findings(tmp_path):
    replies = {
        "c502.0.mp4": json.loads(FIXTURE.read_text(encoding="utf-8")),
        "c853.0.mp4": {
            "output_text": '{"verdict": "drop", "note": "A game voice line, the player says nothing.", "summary": "Elohim speaks.", "quote": null, "game_state": "Voice line playing."}'
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
