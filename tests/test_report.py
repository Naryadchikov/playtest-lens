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


def _meta(name):
    return json.loads((Path(render.MAPS_DIR) / f"{name}.json").read_text(encoding="utf-8"))


def _map_px(meta, x, z):
    px = (x - meta["world_min_x"]) / (meta["world_max_x"] - meta["world_min_x"]) * meta["px_width"]
    py = (z - meta["world_min_z"]) / (meta["world_max_z"] - meta["world_min_z"]) * meta["px_height"]
    return px, py


def _card(page, rank):
    match = re.search(
        rf'<article class="card [^"]+" id="m{rank}"[^>]*>(.*?)</article>', page, re.DOTALL
    )
    assert match, f"card m{rank} not found"
    return match.group(1)


def _floor(page, index):
    match = re.search(
        rf'<figure class="floor" data-floor="{index}"[^>]*>(.*?)</figure>', page, re.DOTALL
    )
    assert match, f"floor {index} not found"
    return match.group(1)


def _script(page):
    return page[page.index("<script>"):page.index("</script>")]


@pytest.fixture()
def redesign():
    return _data(REDESIGN)


def test_redesign_fixture_loads():
    data = findings_module.load(REDESIGN)
    assert data["session"]["player"] == "Player 2"
    assert len(data["route"]["points"]) == 40


def test_sections_follow_the_layout_order(redesign):
    page = render_html(redesign)
    # The write-up column first, then the map pane.
    assert re.findall(r'<h2 id="([^"]+)"', page) == [
        "problems", "glance", "across", "moments", "dropped", "where",
    ]
    column = page[page.index('<main class="col">'):page.index("</main>")]
    order = [column.index(mark) for mark in (
        'class="verdict"', 'id="problems"', 'class="tiles"', 'class="strip"', 'id="moments"', 'id="dropped"',
    )]
    assert order == sorted(order)
    assert page.index("</main>") < page.index('<aside class="pane"')


def test_time_lost_tile_shows_only_when_there_is_time_lost(redesign):
    assert "Time lost to being stuck or confused" in render_html(redesign)
    redesign["summary"]["lost_s"] = 0
    assert "Time lost to being stuck or confused" not in render_html(redesign)


def test_header_names_the_model(redesign):
    page = render_html(redesign)
    assert '<li><b>Model</b><span class="mono">muse-spark-1.2-contributor</span></li>' in page


def test_page_shows_every_kept_finding_summary_quote_and_time(redesign):
    page = render_html(redesign)
    for finding in redesign["findings"]:
        if finding["check"]["verdict"] != "keep":
            continue
        card = _card(page, finding["rank"])
        assert html.escape(finding["summary"]) in card
        if finding["quote"] is not None:
            assert html.escape(finding["quote"]) in card
        assert _mss(finding["time_s"]) in card
        assert html.escape(finding["check"]["note"]) in card


def test_every_kept_finding_has_its_anchor_and_its_pin_links_back(redesign):
    page = render_html(redesign)
    for finding in redesign["findings"]:
        if finding["check"]["verdict"] != "keep":
            continue
        rank = finding["rank"]
        assert page.count(f'id="m{rank}"') == 1
        assert re.search(rf'<a class="pin [^"]+" id="pin-m{rank}" href="#m{rank}"', page)
        assert f'href="#pin-m{rank}"' in _card(page, rank)


def test_sections_and_cards_run_in_time_order(redesign):
    page = render_html(redesign)
    assert re.findall(r'<article class="card [^"]+" id="m(\d+)"', page) == [
        "5", "8", "9", "2", "1", "3", "7", "6", "4"
    ]
    assert re.findall(r'<h3 id="g\d+">([^<]*)<span class="note">', page) == [
        "Hall, Puzzle 1: badge reader",
        "North room, Puzzle 2: weighted plates",
        "South room, Puzzle 3: crate shelf",
    ]
    # Every section is open, so every moment and its clip shows without script.
    assert "<details" not in page


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
    titles = re.findall(r'<h3 id="g\d+">([^<]*)<span class="note">', page)
    assert titles == [
        "Hall, Puzzle 1: badge reader",
        "North room, Puzzle 2: weighted plates",
        "South room",
        "South room",
    ]
    notes = re.findall(r'<h3 id="g\d+">South room<span class="note">([^<]*)</span>', page)
    assert notes == ["1 moment, 11:00-11:50", "1 moment, 12:20-13:00"]
    south = page[page.index(">South room<span"):]
    assert "Attempt" not in south.split("</section>")[0]
    tag = re.search(r'<article class="card confused" id="m6"[^>]*>', page).group(0)
    assert 'data-place="South room, Ground floor"' in tag


def test_problems_block_lists_the_file_places_worst_first(redesign):
    page = render_html(redesign)
    block = page[page.index('<section class="problems"'):]
    block = block[:block.index("</section>")]
    assert ">Top problems</h2>" in block
    assert re.findall(r'<a class="place" href="#m(\d+)">([^<]*)</a>', block) == [
        ("9", "North room, weighted plates"),
        ("6", "South room, crate shelf"),
    ]
    first = block.split('<li class="problem">')[1]
    assert "High" in first and "3 attempts" in first and "5 moments" in first
    assert "2:57 lost" in first and "Partly resolved" in first
    # Its moments, by rank, each linking to its card.
    assert re.findall(r'class="mk [^"]+" href="#m(\d+)"', first) == ["1", "2", "3", "7", "9"]
    # No problems, no block.
    redesign["summary"]["problems"] = []
    assert 'class="problems"' not in render_html(redesign)


def test_the_page_draws_every_floor_from_its_own_map(redesign):
    page = render_html(redesign)
    floors = re.findall(r'<figure class="floor" data-floor="(\d)" style="--ar:([0-9.]+)">', page)
    lobby, upper = _meta("lobby"), _meta("lobby_upper")
    assert floors == [
        ("0", f'{lobby["px_width"] / lobby["px_height"]:.4f}'),
        ("1", f'{upper["px_width"] / upper["px_height"]:.4f}'),
    ]
    for index, meta in ((0, lobby), (1, upper)):
        floor = _floor(page, index)
        assert f'viewBox="0 0 {meta["px_width"]} {meta["px_height"]}"' in floor
        assert '<image class="bg" href="data:image/png;base64,' in floor
    assert '<figcaption class="floor-label">Ground floor</figcaption>' in page
    assert '<figcaption class="floor-label">Upper floor</figcaption>' in page


def test_route_and_pins_land_on_their_floor_in_its_pixels(redesign):
    page = render_html(redesign)
    metas = [_meta("lobby"), _meta("lobby_upper")]
    stamps = {0: [], 1: []}
    for index in (0, 1):
        for times in re.findall(r'<polyline class="line" data-t="([^"]*)"', _floor(page, index)):
            stamps[index].extend(float(t) for t in times.split(" "))
    for t, x, z, floor in redesign["route"]["points"]:
        assert t in stamps[floor] and t not in stamps[1 - floor]
        px, py = _map_px(metas[floor], x, z)
        assert f"{px:.1f},{py:.1f}" in _floor(page, floor)
    for finding in redesign["findings"]:
        at = finding.get("at")
        if at is None:
            continue
        px, py = _map_px(metas[at["floor"]], at["x"], at["z"])
        pin = f'pin-m{finding["rank"]}' if finding["rank"] else f'pin-d-{finding["id"]}'
        assert re.search(
            rf'id="{pin}"[^>]*transform="translate\({px:.1f} {py:.1f}\)"', _floor(page, at["floor"])
        )
    # A card upstairs says so; one downstairs does not.
    assert '<span class="floortag">Upper floor</span>' in _card(page, 7)
    assert "floortag" not in _card(page, 1)


def test_cards_carry_the_times_the_map_lights(redesign):
    page = render_html(redesign)
    tag = re.search(r'<article class="card stuck" id="m1"[^>]*>', page).group(0)
    assert 'data-t="345.0"' in tag
    assert 'data-visit="330.0 430.0"' in tag
    assert 'data-clip="335.0 360.0"' in tag
    assert 'data-floor="0"' in tag
    assert 'data-label="Moment 1, Stuck, 5:45"' in tag
    assert 'data-place="weighted plates, attempt 2, Ground floor"' in tag


def test_dropped_candidates_are_a_visible_section_with_hollow_pins(redesign):
    page = render_html(redesign)
    section = page[page.index('<section class="dropped"'):]
    section = section[:section.index("</section>")]
    assert "<details" not in section
    assert "3 candidates the check did not keep" in section
    for finding in redesign["findings"]:
        if finding["check"]["verdict"] != "drop":
            continue
        assert f'id="d-{finding["id"]}"' in section
        assert html.escape(f'Reason: {finding["check"]["note"]}') in section
        assert re.search(rf'<a class="pin hollow [^"]+" id="pin-d-{finding["id"]}" href="#d-{finding["id"]}"', page)


def test_session_strip_rows_come_from_the_file(redesign):
    page = render_html(redesign)
    strip = page[page.index('<section class="strip"'):]
    strip = strip[:strip.index("</section>")]
    duration = redesign["session"]["duration_s"]
    labels = re.findall(r'<div class="labs">(.*?)</div>', strip)[0]
    assert re.findall(r">([^<]+)</span>", labels) == [
        "Hall", "North room", "South room", "Upper floor", "Moments", "Dropped",
    ]
    # An open zone runs to the end of the recording.
    assert 'title="South room, crate shelf 10:40-14:20"' in strip
    for span in redesign["route"]["floor_spans"]:
        if span["floor"] == 1:
            left = span["start_s"] / duration * 100
            assert f'class="bar up" style="left:{left:.2f}%' in strip
    for finding in redesign["findings"]:
        left = finding["time_s"] / duration * 100
        if finding["check"]["verdict"] == "keep":
            assert re.search(
                rf'href="#m{finding["rank"]}" style="left:{left:.2f}%;top:\d+px".*?<b>{finding["rank"]}</b>', strip
            )
        else:
            assert f'href="#d-{finding["id"]}" style="left:{left:.2f}%"' in strip


def test_strip_markers_stack_into_rows_by_time():
    rows, count = render._stack([0.0, 1.0, 2.0, 3.0, 100.0], 100.0)
    assert rows == [0, 1, 2, 0, 0]
    assert count == 3


def test_game_events_wait_in_the_moment_box(redesign):
    page = render_html(redesign)
    box = page[page.index('<div class="box-now"'):]
    for event in redesign["events"]:
        assert f'<li data-t="{event["t"]}" hidden><time>{_mss(event["t"])}</time><span>{html.escape(event["label"])}</span></li>' in box
    assert 'data-up-to="Game events up to {time}"' in box


@pytest.mark.parametrize("path", [SAMPLE, SAMPLE_B])
def test_missing_optional_fields_hide_their_elements(path):
    page = render_html(_data(path))
    assert 'class="pane"' not in page
    assert 'class="strip"' not in page
    assert 'class="tiles"' not in page
    assert 'class="problems"' not in page
    assert "Across players" not in page
    assert "data:image/png" not in page
    assert 'id="pin-' not in page
    assert 'class="verdict"' not in page
    assert "<script" not in page.lower()
    assert "The moments" in page


def test_every_string_from_the_file_is_escaped(redesign):
    payload = "<script>alert(1)</script>"
    redesign["session"]["id"] = payload
    redesign["session"]["player"] = payload
    redesign["summary"]["verdict"] = payload
    redesign["summary"]["problems"][0]["place"] = payload
    redesign["cross_player"][0]["place"] = payload
    redesign["events"][0]["label"] = payload
    redesign["zones"][0]["zone"] = payload
    redesign["findings"][0]["summary"] = payload
    redesign["findings"][0]["quote"] = payload
    page = render_html(redesign)
    # The page's own script is the only one.
    assert "<script>alert(1)" not in page
    assert page.count("<script") == 1
    assert page.count(html.escape(payload)) >= 10


def test_a_stored_time_of_zero_is_shown_as_zero(redesign):
    first = redesign["findings"][0]
    redesign["findings"] = [first]
    redesign["summary"]["problems"] = []
    first["beat"].update(attempt_start_s=0, attempt_end_s=90)
    first["time_s"], first["end_s"] = 12, 20
    page = render_html(redesign)
    assert "(0:00-1:30)" in page
    assert "1 attempt, 1 moment, 0:00-1:30" in page
    assert 'data-visit="0 90"' in page


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
    card = _card(render_html(redesign), 1)
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
    card = _card(render_html(redesign), 1)
    assert f'<span class="{css}">{text}</span>' in card


def test_unknown_resolved_shows_no_status(redesign):
    finding = next(f for f in redesign["findings"] if f["id"] == "f1")
    finding["check"]["resolved"] = "unknown"
    assert 'class="status' not in _card(render_html(redesign), 1)


def test_unexpected_friction_shows_its_text_and_no_meter(redesign):
    finding = next(f for f in redesign["findings"] if f["id"] == "f1")
    finding["check"]["friction"] = "odd"
    finding["check"]["resolved"] = "unknown"
    card = _card(render_html(redesign), 1)
    assert '<span class="intent">odd</span>' in card
    assert 'class="meter"' not in card


def test_page_has_one_inline_script_no_network_and_no_capture_hooks(redesign):
    page = render_html(redesign)
    lowered = page.lower()
    assert lowered.count("<script") == 1
    assert "src=" not in re.sub(r"<video[^>]*>", "", page)
    assert not re.findall(r'href="(?!#|data:image/png;base64,)', page)
    assert "javascript:" not in lowered
    assert "eval(" not in page
    assert "innerHTML" not in page
    assert "http" not in _script(page).replace("http://www.w3.org/2000/svg", "")
    for hook in ("selftest", "&shot", "#sim", "shot=", "window.DATA"):
        assert hook not in page


def test_controls_are_hidden_until_the_script_runs(redesign):
    page = render_html(redesign)
    for css in ("btn play", "trail", "readout", "scrub", "box-now"):
        tag = re.search(rf'<[a-z]+ [^>]*class="{css}"[^>]*>', page).group(0)
        assert "data-needs-script hidden" in tag, css
    duration = int(redesign["session"]["duration_s"])
    assert f'min="0" max="{duration}" step="1" value="{duration}"' in page
    assert 'aria-label="Time in the recording"' in page
    assert 'data-play="Play" data-pause="Pause"' in page
    script = _script(page)
    assert "SPEED = 10" in script
    assert "r.clipStart + v.currentTime" in script
    assert "ArrowRight" in script and "ArrowLeft" in script


def test_trail_offers_from_start_and_the_window_lengths(redesign):
    page = render_html(redesign)
    select = re.search(r'<label class="trail"[^>]*>.*?</label>', page).group(0)
    assert re.findall(r'<option value="(\d+)">', select) == ["0", "10", "15", "30", "60"]
    assert ">From start</option>" in select and ">10 s</option>" in select
    assert 'data-readout-window="{start}-{time} of {duration}"' in page


def test_heat_is_its_own_view_per_floor(redesign):
    page = render_html(redesign)
    assert '<input type="radio" name="view" value="trail" checked>' in page
    assert '<input type="radio" name="view" value="heat" class="view-heat">' in page
    assert ".pane:has(.view-heat:checked) :is(.trail-layer, .box-whole, .box-now) { display: none; }" in page
    for index in (0, 1):
        floor = _floor(page, index)
        spots = [s for s in redesign["route"]["heat"] if s["floor"] == index]
        heat = floor[floor.index('<g class="heat"'):floor.index('<g class="trail-layer">')]
        assert heat.count('fill="url(#heat-blob)"') == len(spots)
        for spot in spots:
            assert f'>{_mss(spot["seconds"])}</text>' in heat
        # Route, pins and dot sit in the trail layer, never in the heat.
        assert "<polyline" not in heat and 'class="pin' not in heat
    assert "Time spent, whole session" in page
    redesign["route"]["heat"] = []
    page = render_html(redesign)
    assert 'name="view"' not in page
    assert 'class="box-heat"' not in page
    assert '<g class="heat"' not in page


def test_f9_markers_sit_on_their_floor_and_link_to_their_moment(redesign):
    page = render_html(redesign)
    assert "F9: the player flagged confusion" in page
    assert 'class="pin f9" id="pin-f1" href="#m5"' in _floor(page, 0)
    assert 'class="f9line"' in _card(page, 5)
    for marker in redesign["markers"]:
        marker["moment"] = None
    page = render_html(redesign)
    assert '<g class="pin f9" id="pin-f1"' in page
    assert 'class="f9line"' not in page
    redesign["markers"] = []
    assert "F9: the player flagged confusion" not in render_html(redesign)


def test_missing_map_hides_the_pane_and_warns_once(redesign, capsys):
    redesign["route"]["maps"] = ["lobby", "no-such-map"]
    page = render_html(redesign)
    assert 'class="pane"' not in page
    assert 'href="#pin-m1"' not in page
    assert '<span class="mk num-pin k-stuck">' in page
    assert "<script" not in page
    err = capsys.readouterr().err
    assert err.count("\n") == 1
    assert "no-such-map" in err


def test_clips_render_only_for_kept_findings(redesign):
    page = render_html(redesign)
    kept_with_clip = [
        f for f in redesign["findings"] if f["check"]["verdict"] == "keep" and f["clip"] is not None
    ]
    assert page.count("<video") == len(kept_with_clip)
    for finding in kept_with_clip:
        assert f'src="{html.escape(finding["clip"]["path"], quote=True)}"' in page
    assert "Clip 5:35-6:00" in _card(page, 1)


def test_missing_quote_shows_the_label(redesign):
    page = render_html(redesign)
    assert '<p class="quote none">No spoken comment.</p>' in _card(page, 7)


def test_span_with_one_time_at_both_ends_reads_as_one_time():
    assert render._span(39.2, 39.8) == "0:39"
    assert render._span(39, 54) == "0:39-0:54"
