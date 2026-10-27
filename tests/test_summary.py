import json
from pathlib import Path

from analyzer import findings as findings_module
from analyzer.summary import summarize

FIXTURES = Path(__file__).parent / "fixtures"


def test_summary_groups_shared_lab_door_across_sessions():
    first = findings_module.load(FIXTURES / "findings_sample.json")
    second = findings_module.load(FIXTURES / "findings_sample_b.json")
    summary = summarize([first, second])

    assert summary["sessions"] == [
        {"id": "sample-01", "recording": "sample-01.mov", "kept": 3, "dropped": 3},
        {"id": "sample-02", "recording": "sample-02.mov", "kept": 1, "dropped": 1},
    ]
    shared = [group for group in summary["groups"] if group["shared"]]
    assert len(shared) == 1
    group = shared[0]
    assert group["kind"] == "confused"
    assert group["session_count"] == 2
    assert group["sessions"] == ["sample-01", "sample-02"]
    assert [(m["session"], m["id"]) for m in group["moments"]] == [
        ("sample-01", "f1"),
        ("sample-02", "f1"),
    ]
    assert group["avg_span_s"] == round(((442.0 - 312.5) + (390.0 - 280.0)) / 2, 2)
    # Dropped findings never appear in any group.
    all_ids = {(m["session"], m["id"]) for g in summary["groups"] for m in g["moments"]}
    assert ("sample-01", "f4") not in all_ids and ("sample-02", "f2") not in all_ids
    json.dumps(summary)


def _session(session_id, findings):
    return {"session": {"id": session_id, "recording": f"{session_id}.mov"}, "findings": findings}


def _finding(fid, game_state, summary="x"):
    return {"id": fid, "kind": "confused", "time_s": 10.0, "end_s": None,
            "game_state": game_state, "summary": summary,
            "check": {"verdict": "keep"}}


def test_summary_never_groups_a_finding_without_a_place():
    first = _session("s1", [_finding("f1", "Fictional lab door is locked")])
    second = _session("s2", [_finding("f1", None, summary="Fictional lab door is locked")])
    summary = summarize([first, second])
    assert not any(group["shared"] for group in summary["groups"])
