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
    # The header, then the write-up column, then the stage, then the timeline bar.
    assert re.findall(r'<h2 id="([^"]+)"', page) == [
        "problems", "glance", "across", "moments", "dropped", "where",
    ]
    header = page[page.index('<header class="head">'):page.index("</header>")]
    assert 'class="verdict"' in header
    # The problems are their own grid row between the header and the column
    # (task 35: the stacked layout puts them above the stage).
    assert page.index("</header>") < page.index('<section class="problems"') < page.index('<main class="col">')
    assert ".problems { grid-area: probs;" in page
    assert '"head" "probs" "pane" "tl" "col"' in page
    column = page[page.index('<main class="col">'):page.index("</main>")]
    order = [column.index(mark) for mark in ('class="tiles"', 'id="moments"', 'id="dropped"')]
    assert order == sorted(order)
    assert 'id="problems"' not in column
    assert "verdict" not in column and "timeline" not in column
    assert page.index("</main>") < page.index('<aside class="pane"') < page.index('<section class="timeline"')


def test_time_lost_tile_shows_only_when_there_is_time_lost(redesign):
    page = render_html(redesign)
    assert "Time stuck or blocked" in page
    assert "in the visits and attempts with an unplanned moment" in page
    redesign["summary"]["lost_s"] = 0
    assert "Time stuck or blocked" not in render_html(redesign)


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
    assert "2:57 stuck" in first and "Partly resolved" in first
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


def test_timeline_rows_come_from_the_file(redesign):
    page = render_html(redesign)
    strip = page[page.index('<section class="timeline"'):]
    strip = strip[:strip.index("</section>")]
    duration = redesign["session"]["duration_s"]
    labels = re.findall(r'<div class="labs">(.*?)</div>', strip)[0]
    assert re.findall(r">([^<]+)</span>", labels) == [
        "Rooms", "Upper floor", "Moments", "Dropped", "Events",
    ]
    # Every visit is a bar on the one rooms row, with its times for the script;
    # an open zone runs to the end of the recording.
    rooms = re.search(r'<div class="track r-rooms">(.*?)</div>', strip).group(1)
    assert rooms.count('class="bar') == len(redesign["zones"])
    assert 'title="South room, crate shelf 10:40-14:20"' in rooms
    assert f'data-s="640.0" data-e="{duration}" data-room="South room"' in rooms
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
    for event in redesign["events"]:
        left = event["t"] / duration * 100
        assert f'<i class="tick" style="left:{left:.2f}%" title="{_mss(event["t"])} {html.escape(event["label"])}"></i>' in strip
    # The timeline's height is on the page, so the stage can size the floors.
    rows, count = render._stack(
        sorted(f["time_s"] for f in redesign["findings"] if f["check"]["verdict"] == "keep"), duration
    )
    height = render._timeline_height(count, 2, True, True)
    assert f"--tl-h:{height}px" in page


def test_short_room_visits_keep_their_name_for_the_tooltip_only(redesign):
    redesign["zones"] = [
        {"zone": "Closet", "puzzle": "", "start_s": 100.0, "end_s": 101.0},
        {"zone": "Hall", "puzzle": "", "start_s": 200.0, "end_s": 400.0},
    ]
    page = render_html(redesign)
    rooms = re.search(r'<div class="track r-rooms">(.*?)</div>', page).group(1)
    assert 'data-room="Closet" title="Closet 1:40-1:41"></span>' in rooms
    assert 'data-room="Hall" title="Hall 3:20-6:40">Hall</span>' in rooms


def test_strip_markers_stack_into_rows_by_time():
    rows, count = render._stack([0.0, 1.0, 2.0, 3.0, 100.0], 100.0)
    assert rows == [0, 1, 2, 0, 0]
    assert count == 3


def test_game_events_wait_in_the_foot_with_an_icon_per_kind(redesign):
    redesign["events"].append({"t": 400.0, "kind": "odd", "label": "Something else"})
    page = render_html(redesign)
    row = page[page.index('<div class="evrow"'):]
    row = row[:row.index("</ol>")]
    for event in redesign["events"]:
        icon = event["kind"] if event["kind"] in render.EVENT_KINDS else "other"
        assert (
            f'<li data-t="{event["t"]}" hidden><svg aria-hidden="true" focusable="false"><use href="#ev-{icon}"/></svg>'
            f'<time>{_mss(event["t"])}</time><span>{html.escape(event["label"])}</span></li>'
        ) in row
    assert 'data-so-far="Game events so far"' in row
    assert f'data-near="{html.escape("Game events in this moment" + chr(39) + "s visit and clip")}"' in row


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
    for css in ("btn big play-session", "readout", "seg focus", "mode side-now", "mode side-session", "mode foot-now", "nav"):
        tag = re.search(rf'<[a-z]+ [^>]*class="{css}"[^>]*>', page).group(0)
        assert "data-needs-script hidden" in tag, css
    assert 'data-play="Play" data-pause="Pause"' in page
    assert ">Play the session</span>" in page
    assert ">Previous</button>" in page and ">Next</button>" in page and ">Overview</button>" in page
    assert 'data-count="Moment {n} of {of}"' in page
    script = _script(page)
    assert "SPEED = 10" in script
    assert "r.clip[0] + v.currentTime" in script
    assert "ArrowRight" in script and "ArrowLeft" in script and "Escape" in script


def test_trail_offers_from_start_and_the_window_lengths_with_30_s_picked(redesign):
    page = render_html(redesign)
    select = re.search(r'<label class="trail"[^>]*>.*?</label>', page).group(0)
    assert re.findall(r'<option value="(\d+)"', select) == ["0", "10", "15", "30", "60"]
    assert ">From start</option>" in select and ">10 s</option>" in select
    assert '<option value="30" selected>30 s</option>' in select
    assert 'data-readout-window="{start}-{time} of {duration}"' in page


def test_heat_is_its_own_view_per_floor(redesign):
    page = render_html(redesign)
    assert '<input type="radio" name="view" value="trail" checked>' in page
    assert '<input type="radio" name="view" value="heat" class="view-heat">' in page
    assert ".pane:has(.view-heat:checked) .trail-layer { display: none; }" in page
    assert '<div class="mode side-heat">' in page
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
    assert 'class="mode side-heat"' not in page
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
    # One video per clip in the list, plus the stage's, which starts empty:
    # the script loads the first problem's clip into it.
    assert page.count("<video") == len(kept_with_clip) + 1
    assert re.search(r'<figure class="stage-clip" data-first="m\d+" data-needs-script hidden><video preload="metadata"></video>', page)
    for finding in kept_with_clip:
        assert page.count(f'src="{html.escape(finding["clip"]["path"], quote=True)}"') == 1
    assert "Clip 5:35-6:00" in _card(page, 1)


def test_missing_quote_shows_the_label(redesign):
    page = render_html(redesign)
    assert '<p class="quote none">No spoken comment.</p>' in _card(page, 7)


def test_span_with_one_time_at_both_ends_reads_as_one_time():
    assert render._span(39.2, 39.8) == "0:39"
    assert render._span(39, 54) == "0:39-0:54"


def test_moments_by_design_recede_and_the_unplanned_ones_stand_out(redesign):
    page = render_html(redesign)
    by_id = {f["id"]: f for f in redesign["findings"]}
    # f1 is blocked (unplanned), f5 is learning (by design).
    assert by_id["f1"]["check"]["friction"] == "blocked"
    assert by_id["f5"]["check"]["friction"] == "learning"
    strong, soft = by_id["f1"], by_id["f5"]
    assert re.search(rf'<article class="card stuck" id="m{strong["rank"]}"', page)
    assert re.search(rf'<article class="card [a-z]+ soft" id="m{soft["rank"]}"', page)
    assert re.search(rf'<a class="pin k-[a-z]+" id="pin-m{strong["rank"]}"[^>]*>.*?width="{2 * render.PIN_R}"', page, re.DOTALL)
    assert re.search(rf'<a class="pin k-[a-z]+ soft" id="pin-m{soft["rank"]}"[^>]*>.*?width="{2 * render.SOFT_R}"', page, re.DOTALL)
    strip = page[page.index('<section class="timeline"'):]
    assert re.search(rf'<a class="mk soft k-[a-z]+" href="#m{soft["rank"]}"', strip)
    assert re.search(rf'<a class="mk k-[a-z]+" href="#m{strong["rank"]}"', strip)
    assert '<input type="radio" name="focus" value="unplanned">' in page
    # With no moment by design there is nothing to filter.
    for finding in redesign["findings"]:
        finding["check"]["friction"] = "stuck"
    page = render_html(redesign)
    assert 'name="focus"' not in page
    assert ' soft"' not in page


def test_each_moment_is_written_once_and_the_stage_starts_empty(redesign):
    page = render_html(redesign)
    for finding in redesign["findings"]:
        assert page.count(html.escape(finding["summary"])) == 1
        assert page.count(html.escape(finding["check"]["note"])) == 1
    assert '<div class="mode side-now" data-needs-script hidden></div>' in page


def test_without_script_the_stage_still_shows_the_legend(redesign):
    page = render_html(redesign)
    assert "html:not(.js) .side { display: none; }" in page
    foot = page[page.index('<div class="mode foot-whole">'):page.index('<div class="mode foot-now"')]
    assert "Route, arrows point the way walked" in foot
    assert "Hollow shapes are candidates the check dropped." in foot
    assert "F9: the player flagged confusion" in foot


def test_the_heat_view_reaches_the_timeline_outside_the_pane(redesign):
    # Review 20 (blocking): the timeline bar is a sibling of the pane, so a
    # rule scoped to .pane cannot hide it. Every rule that hides it on the
    # heat switch must start at an ancestor of both.
    page = render_html(redesign)
    style = re.sub(r"/\*.*?\*/", "", page[page.index("<style>"):page.index("</style>")], flags=re.DOTALL)
    assert page.index("</aside>") < page.index('<section class="timeline"')
    rules = re.findall(r"([^{}]*:has\(\.view-heat:checked\)[^{}]*)\{", style)
    timeline_rules = [r.strip() for r in rules if ".timeline" in r]
    assert timeline_rules, "no rule hides the timeline in the heat view"
    for rule in timeline_rules:
        assert rule.startswith(".page:has(.view-heat:checked) .timeline"), rule
    assert ".page:has(.view-heat:checked) .timeline { visibility: hidden; }" in style
    assert ".page:has(.view-heat:checked) .timeline { display: none; }" in style
    assert "(.timeline, " not in style


def test_a_dropped_candidate_says_so_and_counts_among_the_dropped(redesign):
    page = render_html(redesign)
    dropped = [f for f in redesign["findings"] if f["check"]["verdict"] == "drop"]
    assert dropped
    section = page[page.index('<section class="dropped"'):]
    assert section.count('<span class="intent dropped">Dropped by the check</span>') == len(dropped)
    assert 'data-count-dropped="Dropped {n} of {of}"' in page
    assert "Dropped by the check" not in page[:page.index('<section class="dropped"')]


def test_long_node_paths_may_wrap_after_their_separators(redesign):
    f = redesign["findings"][0]
    f["game_state"] = "Looking at BREAK_ROOM/kitchenSink/CabinetDoor, then action_primary/action_secondary"
    f["check"]["note"] = "Short words keep their shape; so does a/short_path."
    page = render_html(redesign)
    card = _card(page, f["rank"])
    assert "BREAK_<wbr>ROOM/<wbr>kitchenSink/<wbr>CabinetDoor," in card
    assert "action_<wbr>primary/<wbr>action_<wbr>secondary" in card
    assert "a/short_path." in card and "a/<wbr>short" not in card
    # The escaping still happens first.
    f["game_state"] = "<b>" + "x" * 30 + "</b>"
    page = render_html(redesign)
    assert "<b>" + "x" * 30 not in page
    assert "&lt;b&gt;" + "x" * 30 + "&lt;/<wbr>b&gt;" in page


def test_the_overview_clip_is_the_first_problems_moment(redesign):
    page = render_html(redesign)
    first = redesign["summary"]["problems"][0]["moments"][0]
    rank = next(f["rank"] for f in redesign["findings"] if f["id"] == first)
    assert f'<figure class="stage-clip" data-first="m{rank}"' in page
    # Without problems the rank 1 moment's clip; without any clip, none.
    redesign["summary"]["problems"] = []
    assert '<figure class="stage-clip" data-first="m1"' in render_html(redesign)
    for f in redesign["findings"]:
        f["clip"] = None
    assert 'data-first=' not in render_html(redesign)


def test_the_kept_tile_does_not_repeat_its_number(redesign):
    page = render_html(redesign)
    summary = redesign["summary"]
    tile = re.search(r'<div class="tile"><div class="n">(\d+)<span class="note">kept</span></div>.*?</div></div>', page).group(0)
    assert tile.startswith(f'<div class="tile"><div class="n">{summary["kept"]}<span class="note">kept</span>')
    assert f'<span class="note">{summary["dropped"]} dropped</span>' in tile
    assert f'{summary["kept"]} kept' not in page
