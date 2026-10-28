import copy
import html
import json
from pathlib import Path

from report.render import render_html

SAMPLE = Path(__file__).parent / "fixtures" / "findings_sample.json"


def _sample_data():
    return json.loads(SAMPLE.read_text(encoding="utf-8"))


def _mss(seconds):
    total = int(seconds)
    return f"{total // 60}:{total % 60:02d}"


def test_page_shows_every_finding_as_in_file():
    data = _sample_data()
    page = render_html(data)
    for finding in data["findings"]:
        assert html.escape(finding["summary"]) in page
        if finding["quote"] is not None:
            assert html.escape(finding["quote"]) in page
        assert _mss(finding["time_s"]) in page


def test_page_escapes_script_in_quote():
    data = _sample_data()
    data["findings"][0]["quote"] = "<script>alert(1)</script>"
    page = render_html(data)
    assert "<script>alert(1)</script>" not in page
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in page


def test_dropped_findings_only_under_dropped():
    data = _sample_data()
    page = render_html(data)
    kept_part, dropped_part = page.split("<h2>Dropped</h2>")
    for finding in data["findings"]:
        summary = html.escape(finding["summary"])
        if finding["check"]["verdict"] == "drop":
            assert summary not in kept_part
            assert summary in dropped_part
        else:
            assert summary in kept_part
            assert summary not in dropped_part


def test_kept_findings_in_rank_order():
    data = _sample_data()
    page = render_html(data)
    kept = sorted(
        (f for f in data["findings"] if f["check"]["verdict"] == "keep"),
        key=lambda f: f["rank"],
    )
    positions = [page.index(html.escape(f["summary"])) for f in kept]
    assert positions == sorted(positions)


def test_beat_header_names_area_puzzle_attempt_and_span():
    data = _sample_data()
    kept = [f for f in data["findings"] if f["check"]["verdict"] == "keep"]
    first = copy.deepcopy(kept[0])
    second = copy.deepcopy(kept[0])
    for finding, rank, time_s, summary in [
        (first, 1, 444.0, "First fan moment."),
        (second, 2, 502.0, "Second fan moment."),
    ]:
        finding["rank"] = rank
        finding["time_s"] = time_s
        finding["summary"] = summary
        finding["clip"] = None
        finding["beat"] = {
            "area": "Yellow Puzzle Area",
            "puzzle": "fan and blue barrier",
            "puzzle_number": 1,
            "attempt": 1,
            "attempt_start_s": 444.0,
            "attempt_end_s": 502.0,
            "index": rank,
        }
    data["findings"] = [first, second]
    page = render_html(data)
    assert 'class="beat"' in page
    assert "Yellow Puzzle Area · Puzzle 1: fan and blue barrier · Attempt 1 · 7:24–8:22" in page
    assert page.count('class="beat"') == 1


def test_beat_headers_never_pull_a_later_moment_forward():
    data = _sample_data()
    kept = [f for f in data["findings"] if f["check"]["verdict"] == "keep"]
    rows = []
    for rank, (time_s, puzzle, summary) in enumerate(
        [
            (10.0, "Door", "Door first."),
            (20.0, "Fan", "Fan middle."),
            (30.0, "Door", "Door last."),
        ],
        start=1,
    ):
        finding = copy.deepcopy(kept[0])
        finding["rank"] = rank
        finding["time_s"] = time_s
        finding["summary"] = summary
        finding["clip"] = None
        finding["beat"] = {
            "area": "Lab",
            "puzzle": puzzle,
            "puzzle_number": 1,
            "attempt": 1,
            "attempt_start_s": time_s,
            "attempt_end_s": time_s,
            "index": rank,
        }
        rows.append(finding)
    data["findings"] = rows
    page = render_html(data)
    positions = [page.index(s) for s in ("Door first.", "Fan middle.", "Door last.")]
    assert positions == sorted(positions)


def test_page_has_video_only_when_clip_present():
    data = _sample_data()
    page = render_html(data)
    for finding in data["findings"]:
        if finding["clip"] is not None:
            assert f'src="{html.escape(finding["clip"]["path"], quote=True)}"' in page
    # f3 and f5 have no clip, so the page holds exactly the four clip paths.
    assert page.count("<video") == 4
