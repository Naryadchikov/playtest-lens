import json
from pathlib import Path

from analyzer import findings as findings_module
from analyzer.summary import cross_player, main, summarize
from report.render import render_html

FIXTURES = Path(__file__).parent / "fixtures"
SAMPLE = FIXTURES / "findings_sample.json"
SAMPLE_B = FIXTURES / "findings_sample_b.json"


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


def _session(session_id, findings, player=None):
    session = {"id": session_id, "recording": f"{session_id}.mov"}
    if player is not None:
        session["player"] = player
    return {"session": session, "findings": findings}


def _finding(fid, game_state, summary="x", kind="confused", time_s=10.0,
             end_s=None, rank=1):
    return {"id": fid, "kind": kind, "time_s": time_s, "end_s": end_s,
            "rank": rank, "game_state": game_state, "summary": summary,
            "check": {"verdict": "keep"}}


def test_summary_groups_by_beat_when_game_state_wording_differs():
    first = _finding("f1", "Cube behind a blue energy barrier.")
    first["beat"] = {"area": "Lab", "puzzle": "Door", "attempt": 1}
    second = _finding("f1", "A locked door in the laboratory.")
    second["beat"] = {"area": "Lab", "puzzle": "Door", "attempt": 2}
    summary = summarize([_session("s1", [first]), _session("s2", [second])])
    shared = [group for group in summary["groups"] if group["shared"]]
    assert len(shared) == 1
    assert shared[0]["session_count"] == 2


def test_summary_never_groups_a_finding_without_a_place():
    first = _session("s1", [_finding("f1", "Fictional lab door is locked")])
    second = _session("s2", [_finding("f1", None, summary="Fictional lab door is locked")])
    summary = summarize([first, second])
    assert not any(group["shared"] for group in summary["groups"])


def test_cross_player_gives_each_file_its_own_here():
    first = findings_module.load(SAMPLE)
    second = findings_module.load(SAMPLE_B)
    blocks = cross_player([first, second])

    assert len(blocks) == 2
    expect = [
        ("sample-01", ["f1"], 312.5, True),
        ("sample-02", ["f1"], 280.0, False),
    ]
    assert blocks[0] == [
        {
            "place": "Fictional lab door is locked; the blue token is in the player inventory.",
            "kind": "confused",
            "of": 2,
            "players": [
                {"label": label, "moments": moments, "worst_t": worst_t, "here": here}
                for label, moments, worst_t, here in expect
            ],
        }
    ]
    assert [player["here"] for player in blocks[1][0]["players"]] == [False, True]
    # A place only one session saw is not written.
    assert "Fictional corridor loop; stairwell door is unmarked." not in json.dumps(blocks)


def test_cross_player_of_one_session_writes_nothing():
    assert cross_player([findings_module.load(SAMPLE)]) == [[]]


def test_cross_player_place_text_comes_from_beat_then_game_state():
    def place(beat_first, beat_second, state_first="x", state_second="x"):
        first = _finding("f1", state_first)
        second = _finding("f1", state_second)
        if beat_first:
            first["beat"] = beat_first
        if beat_second:
            second["beat"] = beat_second
        blocks = cross_player([_session("s1", [first]), _session("s2", [second])])
        return blocks[0][0]["place"]

    assert place({"area": "lab", "puzzle": "door"}, {"area": "Lab", "puzzle": "Door"}) == "Lab, door"
    assert place({"area": "attic"}, {"area": "Attic"}) == "Attic"
    assert place({"puzzle": "crank"}, {"puzzle": "Crank"}) == "Crank"
    assert place(None, None, "fictional hall", "Fictional hall") == "Fictional hall"


def test_cross_player_worst_t_is_longest_span_then_earliest():
    first = _session(
        "s1",
        [
            _finding("f1", "same place", time_s=10.0, end_s=20.0, rank=1),
            _finding("f2", "same place", time_s=1.0, end_s=None, rank=2),
            _finding("f3", "same place", time_s=90.0, end_s=95.0, rank=3),
        ],
        player="Player one",
    )
    second = _session(
        "s2",
        [
            _finding("f1", "same place", time_s=50.0, end_s=60.0, rank=1),
            _finding("f2", "same place", time_s=20.0, end_s=30.0, rank=2),
        ],
    )
    entry = cross_player([first, second])[0][0]
    assert [(p["label"], p["moments"], p["worst_t"]) for p in entry["players"]] == [
        ("Player one", ["f1", "f2", "f3"], 10.0),
        ("s2", ["f1", "f2"], 20.0),
    ]


def test_cli_writes_both_files_and_is_idempotent(tmp_path):
    first = tmp_path / "a.json"
    second = tmp_path / "b.json"
    first.write_text(SAMPLE.read_text(encoding="utf-8"), encoding="utf-8")
    second.write_text(SAMPLE_B.read_text(encoding="utf-8"), encoding="utf-8")
    args = ["--write-cross-player", str(first), str(second)]

    assert main(args) == 0
    data = findings_module.load(first)
    assert data["cross_player"][0]["players"][0]["here"] is True
    assert data["cross_player"][0]["players"][1]["here"] is False
    page = render_html(data)
    assert "Across players" in page
    assert "sample-01: 5:12" in page and "sample-02: 4:40" in page

    before = (first.read_bytes(), second.read_bytes())
    assert main(args) == 0
    assert (first.read_bytes(), second.read_bytes()) == before


def test_cli_removes_a_stale_cross_player(tmp_path):
    path = tmp_path / "a.json"
    data = json.loads(SAMPLE.read_text(encoding="utf-8"))
    data["cross_player"] = [
        {
            "place": "Old place",
            "kind": "stuck",
            "of": 2,
            "players": [
                {"label": "sample-01", "moments": ["f1"], "worst_t": 1.0, "here": True}
            ],
        }
    ]
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    assert main(["--write-cross-player", str(path)]) == 0
    assert "cross_player" not in findings_module.load(path)
