import copy
import html
import json
import re
from pathlib import Path

import pytest

from analyzer import findings as findings_module
from report import render
from report.render import render_html

FIXTURES = Path(__file__).parent / "fixtures"
REDESIGN = FIXTURES / "findings_redesign.json"
SAMPLE = FIXTURES / "findings_sample.json"
SAMPLE_B = FIXTURES / "findings_sample_b.json"


def _data(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _mss(seconds):
    total = int(seconds)
    return f"{total // 60}:{total % 60:02d}"


def _map_px(meta, x, z):
    px = (x - meta["world_min_x"]) / (
        meta["world_max_x"] - meta["world_min_x"]
    ) * meta["px_width"]
    py = (z - meta["world_min_z"]) / (
        meta["world_max_z"] - meta["world_min_z"]
    ) * meta["px_height"]
    return px, py


def _card(page, rank):
    match = re.search(
        rf'<article class="card [^"]+" id="m{rank}"[^>]*>(.*?)</article>',
        page,
        re.DOTALL,
    )
    assert match, f"card m{rank} not found"
    return match.group(1)


@pytest.fixture()
def redesign():
    return _data(REDESIGN)


def test_redesign_fixture_loads():
    data = findings_module.load(REDESIGN)
    assert data["session"]["player"] == "Player 2"
    assert len(data["route"]["points"]) == 40


def test_time_lost_tile_shows_only_when_there_is_time_lost(redesign):
    assert "Time lost to being stuck or confused" in render_html(redesign)
    redesign["summary"]["lost_s"] = 0
    assert "Time lost to being stuck or confused" not in render_html(redesign)


def test_page_shows_every_kept_finding_summary_quote_and_time(redesign):
    page = render_html(redesign)
    for finding in redesign["findings"]:
        if finding["check"]["verdict"] != "keep":
            continue
        assert html.escape(finding["summary"]) in page
        if finding["quote"] is not None:
            assert html.escape(finding["quote"]) in page
        assert _mss(finding["time_s"]) in page


def test_sections_follow_the_mockup_order(redesign):
    page = render_html(redesign)
    assert re.findall(r'<h2 id="([^"]+)"', page) == [
        "glance",
        "across",
        "where",
        "moments",
        "dropped",
    ]


def test_sections_and_cards_run_in_time_order(redesign):
    page = render_html(redesign)
    assert re.findall(r'<article class="card [^"]+" id="m(\d+)"', page) == [
        "5", "8", "9", "2", "1", "3", "7", "6", "4"
    ]
    assert re.findall(
        r"<summary>([^<]*)<span class=\"note\">", page
    ) == [
        "Hall, Puzzle 1: badge reader",
        "North room, Puzzle 2: weighted plates",
        "South room, Puzzle 3: crate shelf",
    ]
    # Only the section that holds the lowest rank (1) is open.
    assert page.count('class="puzzle" open') == 1
    opened = page.index('class="puzzle" open')
    assert "North room, Puzzle 2: weighted plates" in page[opened:opened + 400]


def _as_area_visit(finding, start_s, end_s):
    finding["beat"].update(
        puzzle=None, puzzle_number=None, attempt=None,
        attempt_start_s=start_s, attempt_end_s=end_s,
    )


def test_a_beat_without_a_puzzle_renders_the_area_alone(redesign):
    # Two visits to one area, in file order the later one first.
    for finding in redesign["findings"]:
        if finding["id"] == "f4":
            _as_area_visit(finding, 740.0, 780.0)
        if finding["id"] == "f6":
            _as_area_visit(finding, 660.0, 710.0)
    page = render_html(redesign)
    titles = re.findall(r"<summary>([^<]*)<span class=\"note\">", page)
    assert titles == [
        "Hall, Puzzle 1: badge reader",
        "North room, Puzzle 2: weighted plates",
        "South room",
        "South room",
    ]
    notes = re.findall(r'<summary>South room<span class="note">([^<]*)</span>', page)
    assert notes == ["1 moment, 11:00-11:50", "1 moment, 12:20-13:00"]
    south = page[page.index("<summary>South room"):]
    assert "Puzzle" not in south.split("</details>")[0]
    assert "Attempt" not in south
    assert 'id="pin-m6"' in page
    pinlist = page.split('<ol class="pinlist">')[1].split("</ol>")[0]
    assert "crate shelf" not in pinlist


@pytest.mark.parametrize("path", [SAMPLE, SAMPLE_B])
def test_missing_optional_fields_hide_their_elements(path):
    page = render_html(_data(path))
    assert 'id="where"' not in page
    assert 'class="tiles"' not in page
    assert "Across players" not in page
    assert "data:image/png" not in page
    assert 'id="pin-' not in page
    assert 'class="verdict"' not in page
    assert "The moments" in page


def test_every_string_from_the_file_is_escaped(redesign):
    payload = "<script>alert(1)</script>"
    redesign["session"]["id"] = payload
    redesign["session"]["player"] = payload
    redesign["summary"]["verdict"] = payload
    redesign["cross_player"][0]["place"] = payload
    redesign["findings"][0]["summary"] = payload
    redesign["findings"][0]["quote"] = payload
    page = render_html(redesign)
    # The page's own script is the only one.
    assert "<script>alert(1)" not in page
    assert page.count("<script") == 1
    assert page.count(html.escape(payload)) >= 7


def test_a_stored_time_of_zero_is_shown_as_zero(redesign):
    first = redesign["findings"][0]
    redesign["findings"] = [first]
    first["beat"].update(attempt_start_s=0, attempt_end_s=90)
    first["time_s"], first["end_s"] = 12, 20
    page = render_html(redesign)
    assert "(0:00-1:30)" in page
    assert "1 attempt, 1 moment, 0:00-1:30" in page


def test_route_and_pin_pixels_match_the_map_json(redesign):
    page = render_html(redesign)
    meta = json.loads(
        (Path(render.MAPS_DIR) / "lobby.json").read_text(encoding="utf-8")
    )
    for point in (redesign["route"]["points"][0], redesign["route"]["points"][10]):
        px, py = _map_px(meta, point[1], point[2])
        assert f"{px:.1f},{py:.1f}" in page

    finding = next(f for f in redesign["findings"] if f["id"] == "f1")
    px, py = _map_px(meta, finding["at"]["x"], finding["at"]["z"])
    assert re.search(
        rf'id="pin-m1"[^>]*transform="translate\({px:.1f} {py:.1f}\)"', page
    )


@pytest.mark.parametrize(
    "friction, level, tag, unplanned",
    [
        ("learning", 1, "by design", False),
        ("stuck", 2, "unplanned", True),
        ("blocked", 3, "unplanned", True),
    ],
)
def test_friction_drives_the_meter_and_tag(redesign, friction, level, tag, unplanned):
    finding = next(f for f in redesign["findings"] if f["id"] == "f1")
    finding["check"]["friction"] = friction
    finding["check"]["resolved"] = "unknown"
    page = render_html(redesign)
    card = _card(page, 1)
    assert card.count('class="on"') == level
    css = "intent unplanned" if unplanned else "intent"
    assert f'<span class="{css}">{html.escape(tag)}</span>' in card


@pytest.mark.parametrize(
    "resolved, after, text, css",
    [
        ("solved", 28, "Resolved after 0:28", "status done"),
        ("solved", None, "Resolved", "status done"),
        ("abandoned", None, "Abandoned", "status open"),
    ],
)
def test_resolved_drives_the_status(redesign, resolved, after, text, css):
    finding = next(f for f in redesign["findings"] if f["id"] == "f1")
    finding["check"]["resolved"] = resolved
    finding["check"]["resolved_after_s"] = after
    page = render_html(redesign)
    card = _card(page, 1)
    assert f'<span class="{css}">{text}</span>' in card


def test_unknown_resolved_shows_no_status(redesign):
    finding = next(f for f in redesign["findings"] if f["id"] == "f1")
    finding["check"]["resolved"] = "unknown"
    page = render_html(redesign)
    assert 'class="status' not in _card(page, 1)


def test_unexpected_friction_shows_its_text_and_no_meter(redesign):
    finding = next(f for f in redesign["findings"] if f["id"] == "f1")
    finding["check"]["friction"] = "odd"
    finding["check"]["resolved"] = "unknown"
    page = render_html(redesign)
    card = _card(page, 1)
    assert '<span class="intent">odd</span>' in card
    assert 'class="meter"' not in card


def test_page_has_one_inline_script_and_no_network(redesign):
    page = render_html(redesign)
    lowered = page.lower()
    assert lowered.count("<script") == 1
    assert "src=" not in re.sub(r'<img src="data:[^"]*"|<video[^>]*>', "", page)
    assert "javascript:" not in lowered
    assert "eval(" not in page
    assert "innerHTML" not in page
    script = page[page.index("<script>"):page.index("</script>")]
    assert "http" not in script


def _route_times(redesign):
    return [point[0] for point in redesign["route"]["points"]]


def test_map_elements_carry_the_times_from_the_file(redesign):
    page = render_html(redesign)
    times = _route_times(redesign)
    stamps = " ".join(str(t) for t in times)
    polylines = re.findall(r'<polyline data-t="([^"]*)"[^>]*points="([^"]*)"', page)
    assert len(polylines) == 2
    for data_t, points in polylines:
        assert data_t == stamps
        # The no-script view keeps the whole route.
        assert len(points.split(" ")) == len(times)
    for finding in redesign["findings"]:
        if finding["check"]["verdict"] == "keep":
            assert re.search(
                rf'id="pin-m{finding["rank"]}"[^>]*data-t="{finding["time_s"]}"', page
            )
    for index, marker in enumerate(redesign["markers"], start=1):
        assert re.search(rf'id="pin-f{index}"[^>]*data-t="{marker["t"]}"', page)
    arrow_times = re.findall(r'<path data-t="([^"]*)" d="M-16', page)
    assert arrow_times
    assert all(float(t) in times for t in arrow_times)
    assert page.count(f'<g data-t="{times[-1]}">') == 1
    pinlist = page.split('<ol class="pinlist">')[1].split("</ol>")[0]
    assert len(re.findall(r'<li data-t="', pinlist)) == len(
        [f for f in redesign["findings"] if f["check"]["verdict"] == "keep" and f.get("at")]
    )


def test_timeline_controls_are_hidden_until_the_script_runs(redesign):
    page = render_html(redesign)
    box = re.search(r'<div class="timeline"[^>]*>', page).group(0)
    assert " hidden" in box
    duration = int(redesign["session"]["duration_s"])
    assert f'min="0" max="{duration}" step="1" value="{duration}"' in page
    assert 'aria-label="Time in the recording"' in page
    assert 'data-play="Play"' in page and 'data-pause="Pause"' in page


def test_heat_is_its_own_view_and_hides_the_trail(redesign):
    page = render_html(redesign)
    # A view switch, timeline checked by default, heat map by CSS alone.
    assert '<input type="radio" name="view" value="trail" checked>' in page
    assert '<input type="radio" name="view" value="heat" class="view-heat">' in page
    assert "> Timeline</label>" in page and "> Heat map</label>" in page
    assert ".where:has(.view-heat:checked) :is(.trail, .legend-trail, .timeline) { display: none; }" in page
    assert ".map .heat, .legend-heat { display: none; }" in page
    # Heat sits outside the trail group; route, pins and markers inside it.
    svg = page[page.index("<svg viewBox"):page.index("</svg>")]
    heat_at = svg.index('<g class="heat"')
    trail_at = svg.index('<g class="trail">')
    assert heat_at < trail_at
    trail = svg[trail_at:]
    assert "<polyline" in trail and 'id="pin-m1"' in trail and 'id="pin-f1"' in trail
    assert 'class="now' in trail
    assert "<polyline" not in svg[heat_at:trail_at]
    assert 'class="pin' not in svg[heat_at:trail_at]
    # One blob per spot, drawn through the color scale, labeled with its time.
    heat = svg[heat_at:trail_at]
    assert heat.count('fill="url(#heat-blob)"') == len(redesign["route"]["heat"])
    assert '<g filter="url(#heat-ramp)">' in heat
    for spot in redesign["route"]["heat"]:
        assert f'>{_mss(spot["seconds"])}</text>' in heat
    assert 'class="legend-heat"' in page and "Time spent, whole session" in page
    # A route with no heat has no switch and no heat legend.
    redesign["route"]["heat"] = []
    page = render_html(redesign)
    assert 'name="view"' not in page
    assert 'class="legend-heat"' not in page
    assert '<g class="heat"' not in page


def test_trail_offers_from_start_and_the_window_lengths(redesign):
    page = render_html(redesign)
    box = page[page.index('<div class="timeline"'):]
    box = box[:box.index('<aside')]
    values = re.findall(r'<input type="radio" name="trail" value="(\d+)"', box)
    assert values == ["0", "10", "15", "30", "60"]
    assert '<input type="radio" name="trail" value="0" checked>' in box
    assert 'data-readout-window="{start}-{time} of {duration}"' in box
    script = page[page.index("<script>"):page.index("</script>")]
    assert "t - span" in script


def test_cards_carry_their_times_for_dimming(redesign):
    page = render_html(redesign)
    for finding in redesign["findings"]:
        if finding["check"]["verdict"] != "keep":
            continue
        tag = re.search(rf'<article class="card [^"]+" id="m{finding["rank"]}"[^>]*>', page).group(0)
        assert f'data-t="{finding["time_s"]}"' in tag
        if finding.get("end_s") is not None:
            assert f'data-end="{finding["end_s"]}"' in tag
        else:
            assert "data-end" not in tag
    # Dimmed, never removed: the span note starts hidden and resets the view.
    assert '<p class="span-note" hidden data-text="Moments in {span} are lit. The rest are dimmed.">' in page
    assert ">Show all moments</button>" in page
    assert ".card.dim { opacity: .4; }" in page


def test_f9_legend_only_when_the_file_has_markers(redesign):
    assert "F9: the player flagged confusion" in render_html(redesign)
    redesign["markers"] = []
    assert "F9: the player flagged confusion" not in render_html(redesign)


@pytest.mark.parametrize("path", [SAMPLE, SAMPLE_B])
def test_pages_with_no_map_have_no_timeline_and_no_script(path):
    page = render_html(_data(path))
    assert 'class="timeline"' not in page
    assert 'class="span-note"' not in page
    assert "<script" not in page.lower()


def test_missing_map_hides_the_map_section_and_warns_once(redesign, capsys):
    redesign["route"]["map"] = "no-such-map"
    page = render_html(redesign)
    assert 'id="where"' not in page
    assert 'href="#pin-m1"' not in page
    assert '<span class="num-pin">1</span>' in page
    err = capsys.readouterr().err
    assert err.count("\n") == 1
    assert "no-such-map" in err


def test_f9_marker_without_a_kept_moment_has_no_link(redesign):
    for marker in redesign["markers"]:
        marker["moment"] = None
    page = render_html(redesign)
    assert '<g class="pin f9" id="pin-f1"' in page
    assert 'class="pin f9" id="pin-f1" href=' not in page
    assert 'class="f9line"' not in page


def test_pin_list_lists_only_pinned_findings_in_rank_order(redesign):
    page = render_html(redesign)
    pinned = [
        f for f in redesign["findings"]
        if f["check"]["verdict"] == "keep" and f.get("at") is not None
    ]
    pinlist = page.split('<ol class="pinlist">')[1].split("</ol>")[0]
    assert re.findall(r'<span class="num">(\d+)</span>', pinlist) == [
        str(f["rank"]) for f in pinned
    ]

    for finding in redesign["findings"]:
        if finding["id"] == "f5":
            del finding["at"]
    page = render_html(redesign)
    assert 'id="pin-m5"' not in page
    assert '<article class="card confused" id="m5" ' in page
    pinlist = page.split('<ol class="pinlist">')[1].split("</ol>")[0]
    assert '<span class="num">5</span>' not in pinlist


def test_clips_render_only_for_kept_findings(redesign):
    page = render_html(redesign)
    kept_with_clip = [
        f for f in redesign["findings"]
        if f["check"]["verdict"] == "keep" and f["clip"] is not None
    ]
    assert page.count("<video") == len(kept_with_clip)
    for finding in kept_with_clip:
        assert f'src="{html.escape(finding["clip"]["path"], quote=True)}"' in page


def test_missing_quote_shows_the_label(redesign):
    page = render_html(redesign)
    assert '<p class="quote none">No spoken comment.</p>' in _card(page, 7)
