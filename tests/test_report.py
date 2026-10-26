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


def test_page_has_video_only_when_clip_present():
    data = _sample_data()
    page = render_html(data)
    for finding in data["findings"]:
        if finding["clip"] is not None:
            assert f'src="{html.escape(finding["clip"]["path"], quote=True)}"' in page
    # f3 and f5 have no clip, so the page holds exactly the four clip paths.
    assert page.count("<video") == 4
