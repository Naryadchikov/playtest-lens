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


def _row(page, rank):
    match = re.search(rf'<article class="m [^"]+" id="m{rank}"[^>]*>(.*?)</article>', page, re.DOTALL)
    assert match, f"moment m{rank} not found"
    return match.group(1)


def _read(page):
    return page[page.index('<div class="read" id="read">'):page.index('<div class="watch"')]


def _watch(page):
    return page[page.index('<div class="watch"'):page.index("<script>")]


def _overview(page):
    block = page[page.index('<figure class="ovmap'):]
    return block[:block.index("</figure>")]


# One floor's markup inside a block (the overview map or Watch's maps).
def _floor(block, index):
    match = re.search(rf'<div class="floor" data-floor="{index}"[^>]*>(.*?)</div>', block, re.DOTALL)
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


def test_read_then_watch_in_the_layout_order(redesign):
    page = render_html(redesign)
    read = _read(page)
    assert re.findall(r'<h2 id="([^"]+)"', read) == ["problems", "across", "moments", "dropped"]
    header = read[read.index('<header class="head">'):read.index("</header>")]
    assert 'class="verdict"' in header
    # The first screen: the problems with the level's map beside them.
    first = read[read.index('<div class="first">'):read.index('<section class="across"')]
    assert first.index('<section class="problems"') < first.index('<figure class="ovmap')
    # Watch comes after Read, hidden until a moment opens it, and the script last.
    assert page.index("</footer>") < page.index('<div class="watch"') < page.index("<script>")
    assert re.search(r'<div class="watch" id="watch" role="dialog" aria-modal="true"[^>]* hidden>', page)
    assert re.findall(r'<h2 id="([^"]+)"', _watch(page)) == ["before-h"]


def test_header_line_counts_the_file_and_the_time_stuck(redesign):
    page = render_html(redesign)
    assert '<p class="meta">14:20 recording, 9 moments kept, 3 dropped. 4:45 stuck or blocked.</p>' in page
    redesign["summary"]["lost_s"] = 0
    page = render_html(redesign)
    assert "stuck or blocked" not in _read(page).split('<div class="first">')[0]


def test_page_shows_every_kept_finding_once(redesign):
    page = render_html(redesign)
    for finding in redesign["findings"]:
        if finding["check"]["verdict"] != "keep":
            continue
        row = _row(page, finding["rank"])
        assert html.escape(finding["summary"]) in row
        if finding["quote"] is not None:
            assert html.escape(finding["quote"]) in row
        assert _mss(finding["time_s"]) in row
        assert html.escape(finding["check"]["note"]) in row
    # Written once: Watch clones the row's nodes at run time.
    for finding in redesign["findings"]:
        assert page.count(html.escape(finding["summary"])) == 1
        assert page.count(html.escape(finding["check"]["note"])) == 1


def test_every_moment_has_its_anchor_and_its_pins_open_it(redesign):
    page = render_html(redesign)
    for finding in redesign["findings"]:
        if finding["check"]["verdict"] == "keep":
            anchor, link = f'id="m{finding["rank"]}"', f'href="#m{finding["rank"]}"'
        else:
            anchor, link = f'id="d-{finding["id"]}"', f'href="#d-{finding["id"]}"'
        assert page.count(anchor) == 1
        # A pin on the overview map and one in Watch, both opening the moment.
        pins = re.findall(rf'<a class="pin (?:hollow )?k-[a-z]+(?: soft)?" {link} data-open="{finding["id"]}"', page)
        assert len(pins) == 2, finding["id"]


def test_moments_run_in_time_order_under_their_place_headings(redesign):
    page = render_html(redesign)
    assert re.findall(r'<article class="m [^"]+" id="m(\d+)"', page) == [
        "5", "8", "9", "2", "1", "3", "7", "6", "4"
    ]
    assert re.findall(r'<h3 id="g\d+">([^<]*)<span class="note">', page) == [
        "Hall, Puzzle 1: badge reader",
        "North room, Puzzle 2: weighted plates",
        "South room, Puzzle 3: crate shelf",
    ]
    assert "<h4>Attempt 2 (5:30-7:10)</h4>" in page
    # Every moment reads without script: the only disclosures are the notes.
    assert page.count("<details") == page.count('<details class="more">')


def _as_area_visit(finding, start_s, end_s):
    finding["beat"].update(puzzle=None, puzzle_number=None, attempt=None, attempt_start_s=start_s, attempt_end_s=end_s)


def test_a_beat_without_a_puzzle_renders_the_area_alone(redesign):
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
    tag = re.search(r'<article class="m confused" id="m6"[^>]*>', page).group(0)
    assert 'data-place="South room, Ground floor"' in tag


def test_problems_block_lists_the_file_places_worst_first(redesign):
    page = render_html(redesign)
    block = page[page.index('<section class="problems"'):]
    block = block[:block.index("</section>")]
    assert ">Top problems</h2>" in block
    assert re.findall(r'<a class="place" href="#m(\d+)" data-open="(f\d+)">([^<]*)</a>', block) == [
        ("9", "f9", "North room, weighted plates"),
        ("6", "f6", "South room, crate shelf"),
    ]
    first = block.split("<li>")[1]
    assert "High" in first and "3 attempts" in first and "5 moments" in first
    assert "2:57 stuck" in first and "Partly resolved" in first
    assert re.findall(r'class="mk [^"]+" href="#m(\d+)" data-open', first) == ["1", "2", "3", "7", "9"]
    redesign["summary"]["problems"] = []
    assert 'class="problems"' not in render_html(redesign)


def test_overview_map_shows_one_floor_with_the_counts_as_its_legend(redesign):
    page = render_html(redesign)
    block = _overview(page)
    # The floor of the first route point is checked; the switch is radios, so it works without script.
    assert '<input type="radio" class="ov-floor" name="ov-floor" value="0" checked>' in block
    assert '<input type="radio" class="ov-floor" name="ov-floor" value="1">' in block
    # CSS picks the floor from the radios, so neither floor carries the hidden attribute.
    assert '<div class="floor" data-floor="0" data-name="Ground floor">' in block
    assert '<div class="floor" data-floor="1" data-name="Upper floor">' in block
    assert ".ovmap.multi .floor { display: none; }" in page
    for index in (0, 1):
        assert f'.ovmap:has(.ov-floor[value="{index}"]:checked) .floor[data-floor="{index}"] {{ display: grid; }}' in page
    legend = re.search(r'<ul class="legend">(.*?)</ul>', block).group(1)
    assert re.findall(r"<b>(\d+)</b> ([A-Za-z ]+)</li>", legend) == [("4", "Stuck"), ("3", "Confused"), ("1", "Surprised"), ("1", "Suspected bug")]
    assert "3 dropped" in legend and "4:45 stuck or blocked" in legend
    # Each floor's picture is in the page once and drawn twice: the overview and Watch.
    assert page.count("data:image/png;base64,") == 2
    for index in (0, 1):
        assert page.count(f'<use class="bg" href="#map-img-{index}"/>') == 2


def test_time_spent_switch_is_on_the_overview_map_only(redesign):
    page = render_html(redesign)
    block = _overview(page)
    assert page.count('<input type="checkbox" id="heat">') == 1 and 'id="heat"' in block
    assert ".ovmap:has(#heat:checked) .map .heat { display: inline; }" in page
    assert '<g class="heat"' not in _watch(page)
    for index in (0, 1):
        floor = _floor(block, index)
        spots = [s for s in redesign["route"]["heat"] if s["floor"] == index]
        heat = floor[floor.index('<g class="heat"'):floor.index('<g class="route"')]
        assert heat.count('fill="url(#heat-blob)"') == len(spots)
        for spot in spots:
            assert f'>{_mss(spot["seconds"])}</text>' in heat
    redesign["route"]["heat"] = []
    page = render_html(redesign)
    assert 'id="heat"' not in page and '<g class="heat"' not in page


def test_route_and_pins_land_on_their_floor_in_its_pixels(redesign):
    page = render_html(redesign)
    watch = _watch(page)
    metas = [_meta("lobby"), _meta("lobby_upper")]
    stamps = {0: [], 1: []}
    for index in (0, 1):
        for times in re.findall(r'<polyline class="line" data-t="([^"]*)"', _floor(watch, index)):
            stamps[index].extend(float(t) for t in times.split(" "))
    for t, x, z, floor in redesign["route"]["points"]:
        assert t in stamps[floor] and t not in stamps[1 - floor]
        px, py = _map_px(metas[floor], x, z)
        assert f"{px:.1f},{py:.1f}" in _floor(watch, floor)
    for finding in redesign["findings"]:
        at = finding.get("at")
        if at is None:
            continue
        px, py = _map_px(metas[at["floor"]], at["x"], at["z"])
        for block in (watch, _overview(page)):
            assert re.search(rf'data-open="{finding["id"]}"[^>]*transform="translate\({px:.1f} {py:.1f}\)"', _floor(block, at["floor"]))
    # Watch shows one floor at a time and offers the other.
    assert '<div class="floor" data-floor="0" data-name="Ground floor">' in watch
    assert '<div class="floor" data-floor="1" data-name="Upper floor" hidden>' in watch
    assert re.findall(r'data-show-floor="(\d)"', watch) == ["0", "1"]


def test_rows_carry_the_times_the_script_reads(redesign):
    page = render_html(redesign)
    tag = re.search(r'<article class="m stuck" id="m1"[^>]*>', page).group(0)
    assert 'data-id="f1"' in tag and 'data-t="345.0"' in tag and 'data-rank="1"' in tag
    assert 'data-clip="335.0 360.0"' in tag and 'data-floor="0"' in tag
    assert 'data-label="Moment 1, Stuck, 5:45"' in tag
    assert 'data-place="weighted plates, attempt 2, Ground floor"' in tag


def test_play_stops_only_at_unplanned_moments(redesign):
    page = render_html(redesign)
    for finding in redesign["findings"]:
        kept = finding["check"]["verdict"] == "keep"
        tag = re.search(rf'<article class="[^"]+" id="{"m" + str(finding["rank"]) if kept else "d-" + finding["id"]}"[^>]*>', page).group(0)
        unplanned = finding["check"].get("friction") in ("stuck", "blocked")
        assert ("data-stop" in tag) == (kept and unplanned), finding["id"]
    script = _script(page)
    assert 'stop: a.hasAttribute("data-stop")' in script
    assert "var stops = kept.filter(function (r) { return r.stop; });" in script
    assert "for (var i = 0; i < stops.length; i++)" in script
    # Previous and Next step through every kept moment.
    assert "showMoment(kept[i], S.playing)" in script


def test_dropped_candidates_are_a_visible_section_with_their_reasons(redesign):
    page = render_html(redesign)
    section = page[page.index('<section class="dropped"'):]
    section = section[:section.index("</section>")]
    assert "3 candidates the check did not keep" in section
    dropped = [f for f in redesign["findings"] if f["check"]["verdict"] == "drop"]
    assert section.count('<span class="intent dropped">Dropped by the check</span>') == len(dropped)
    assert "Dropped by the check" not in page[:page.index('<section class="dropped"')]
    for finding in dropped:
        assert f'<article class="d" id="d-{finding["id"]}"' in section
        assert html.escape(f'Reason: {finding["check"]["note"]}') in section
        assert re.search(rf'<a class="pin hollow k-[a-z]+" href="#d-{finding["id"]}"', page)
    assert 'data-w-count-dropped="Dropped {n} of {of}"' in page


def test_timeline_rows_come_from_the_file(redesign):
    page = render_html(redesign)
    strip = page[page.index('<div class="tl" id="tl"'):page.index('<p class="vh" id="keys">')]
    duration = redesign["session"]["duration_s"]
    rooms = re.search(r'<div class="r-rooms">(.*?)</div>', strip, re.DOTALL).group(1)
    assert rooms.count('<span class="room') == len(redesign["zones"])
    assert 'title="South room, crate shelf 10:40-14:20"' in rooms
    assert f'data-s="640.0" data-e="{duration}" data-room="South room"' in rooms
    for finding in redesign["findings"]:
        left = f'left:{finding["time_s"] / duration * 100:.2f}%'
        if finding["check"]["verdict"] == "keep":
            assert re.search(rf'<button type="button" class="tm k-[a-z]+( soft)?" data-open="{finding["id"]}" style="{left};--row:\d".*?<b>{finding["rank"]}</b>', strip)
        else:
            assert re.search(rf'<button type="button" class="tm k-[a-z]+ hollow" data-open="{finding["id"]}" style="{left};--row:\d"', strip)
    assert re.findall(r'<div class="r-axis" aria-hidden="true">(.*?)</div>', strip)[0].count("<span") == 8
    assert 'id="past"' in strip and 'id="cursor"' in strip


def test_short_room_visits_keep_their_name_for_the_tooltip_only(redesign):
    redesign["zones"] = [
        {"zone": "Closet", "puzzle": "", "start_s": 100.0, "end_s": 101.0},
        {"zone": "Hall", "puzzle": "", "start_s": 200.0, "end_s": 400.0},
    ]
    page = render_html(redesign)
    rooms = re.search(r'<div class="r-rooms">(.*?)</div>', page, re.DOTALL).group(1)
    assert 'data-room="Closet" style="left:11.63%;width:0.12%" title="Closet 1:40-1:41"></span>' in rooms
    assert 'data-room="Hall" style="left:23.26%;width:23.26%" title="Hall 3:20-6:40">Hall</span>' in rooms


def test_timeline_marks_stack_into_rows_by_time():
    assert render._stack([0.0, 1.0, 2.0, 3.0, 100.0], 100.0) == [0, 1, 0, 1, 0]


def test_game_events_wait_hidden_in_watch(redesign):
    page = render_html(redesign)
    start = page.index('<ol id="before" class="events">')
    events = page[start:page.index("</ol>", start)]
    for event in redesign["events"]:
        assert f'<li data-t="{event["t"]}" hidden><time>{_mss(event["t"])}</time>{html.escape(event["label"])}</li>' in events
    assert '<h2 id="before-h">Before this moment</h2>' in page
    assert 'data-w-so-far="Game events so far"' in page


@pytest.mark.parametrize("path", [SAMPLE, SAMPLE_B])
def test_missing_optional_fields_hide_their_elements(path):
    page = render_html(_data(path))
    assert 'class="ovmap' not in page
    assert 'class="maps"' not in page
    assert 'data-show-floor' not in _watch(page)
    assert "data:image/png" not in page
    assert 'class="pin' not in page
    assert 'class="problems"' not in page
    assert 'class="verdict"' not in page
    assert "Across players" not in page
    assert "The moments" in page
    # Watch and its script still serve the clips.
    assert page.count("<script") == 1
    assert '<video id="clip" controls playsinline preload="auto"></video>' in page


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
    redesign["findings"][0]["check"]["cause"] = payload
    page = render_html(redesign)
    assert "<script>alert(1)" not in page
    assert page.count("<script") == 1
    assert page.count(html.escape(payload)) >= 11


def test_a_stored_time_of_zero_is_shown_as_zero(redesign):
    first = redesign["findings"][0]
    redesign["findings"] = [first]
    redesign["summary"]["problems"] = []
    first["beat"].update(attempt_start_s=0, attempt_end_s=90)
    first["time_s"], first["end_s"] = 12, 20
    page = render_html(redesign)
    assert "<h4>Attempt 2 (0:00-1:30)</h4>" in page
    assert "1 attempt, 1 moment, 0:00-1:30" in page
    assert '<span class="time">0:12-0:20</span>' in page


@pytest.mark.parametrize(
    "friction, level, tag, unplanned",
    [("learning", 1, "by design", False), ("stuck", 2, "unplanned", True), ("blocked", 3, "unplanned", True)],
)
def test_friction_drives_the_meter_and_tag(redesign, friction, level, tag, unplanned):
    finding = next(f for f in redesign["findings"] if f["id"] == "f1")
    finding["check"]["friction"] = friction
    finding["check"]["resolved"] = "unknown"
    row = _row(render_html(redesign), 1)
    assert row.count('class="on"') == level
    css = "intent unplanned" if unplanned else "intent"
    assert f'<span class="{css}">{html.escape(tag)}</span>' in row


@pytest.mark.parametrize(
    "resolved, after, text, css",
    [("solved", 28, "Resolved after 0:28", "status done"), ("solved", None, "Resolved", "status done"), ("abandoned", None, "Abandoned", "status open")],
)
def test_resolved_drives_the_status(redesign, resolved, after, text, css):
    finding = next(f for f in redesign["findings"] if f["id"] == "f1")
    finding["check"]["resolved"] = resolved
    finding["check"]["resolved_after_s"] = after
    assert f'<span class="{css}">{text}</span>' in _row(render_html(redesign), 1)


def test_unknown_resolved_shows_no_status(redesign):
    finding = next(f for f in redesign["findings"] if f["id"] == "f1")
    finding["check"]["resolved"] = "unknown"
    assert 'class="status' not in _row(render_html(redesign), 1)


def test_unexpected_friction_shows_its_text_and_no_meter(redesign):
    finding = next(f for f in redesign["findings"] if f["id"] == "f1")
    finding["check"]["friction"] = "odd"
    finding["check"]["resolved"] = "unknown"
    row = _row(render_html(redesign), 1)
    assert '<span class="intent">odd</span>' in row
    assert 'class="meter"' not in row


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


def test_controls_wait_for_the_script_and_the_keys_are_wired(redesign):
    page = render_html(redesign)
    assert re.search(r'<p class="start" data-needs-script hidden><button type="button" class="primary" id="play-session">.*?Play the session</button>', page)
    assert ">Previous</button>" in page and ">Next</button>" in page and ">Back</button>" in page
    assert '<span class="when-paused">Play</span><span class="when-playing">Pause</span>' in page
    assert 'data-w-count="Moment {n} of {of}"' in page
    assert 'data-w-up-next="Up next: moment {rank} at {time}, {place}"' in page
    script = _script(page)
    assert "SPEED = 10" in script and "TRAIL = 30" in script
    assert "S.cur.clip[0] + video.currentTime" in script
    assert "ArrowRight" in script and "ArrowLeft" in script and "Escape" in script
    assert 'read.inert = true' in script


def test_f9_markers_sit_on_their_floor_and_link_to_their_moment(redesign):
    page = render_html(redesign)
    watch = _watch(page)
    assert 'class="pin f9" href="#m5" data-open="f5"' in _floor(watch, 0)
    assert 'class="f9line"' in _row(page, 5)
    for marker in redesign["markers"]:
        marker["moment"] = None
    page = render_html(redesign)
    assert '<g class="pin f9"' in page and 'class="f9line"' not in page
    redesign["markers"] = []
    assert 'pin f9' not in render_html(redesign)


def test_missing_map_drops_the_maps_and_warns_once(redesign, capsys):
    redesign["route"]["maps"] = ["lobby", "no-such-map"]
    page = render_html(redesign)
    assert 'class="ovmap' not in page and 'class="maps"' not in page
    assert 'class="pin' not in page
    assert '<span class="mk k-stuck">' in page
    assert page.count("<script") == 1
    err = capsys.readouterr().err
    assert err.count("\n") == 1 and "no-such-map" in err


def test_each_clip_is_a_still_frame_once_and_watch_starts_empty(redesign):
    page = render_html(redesign)
    with_clip = [f for f in redesign["findings"] if f["clip"] is not None]
    assert page.count("<video") == len(with_clip) + 1
    assert '<video id="clip" controls playsinline preload="auto"></video>' in page
    for finding in with_clip:
        assert page.count(html.escape(finding["clip"]["path"], quote=True)) == 1
    row = _row(page, 1)
    assert 'src="clips/demo-02/f1.mp4#t=10.0"' in row
    assert "Clip 5:35-6:00" in row
    assert '<button type="button" class="watchbtn" data-open="f1" aria-label="Watch moment 1">' in row
    # A moment without a clip still opens Watch from its row.
    redesign["findings"][0]["clip"] = None
    assert '<button type="button" class="watchbtn none" data-open="f1" aria-label="Watch moment 1">' in render_html(redesign)


def test_missing_quote_shows_the_label(redesign):
    assert '<p class="quote none">No spoken comment.</p>' in _row(render_html(redesign), 7)


def test_a_cause_shows_on_its_row_and_nowhere_else(redesign):
    redesign["findings"][0]["check"]["cause"] = "the lever <hint> is out of sight"
    page = render_html(redesign)
    assert '<p class="cause"><span class="lab">Likely cause</span>the lever &lt;hint&gt; is out of sight</p>' in _row(page, 1)
    assert page.count("Likely cause") == 1


def test_span_with_one_time_at_both_ends_reads_as_one_time():
    assert render._span(39.2, 39.8) == "0:39"
    assert render._span(39, 54) == "0:39-0:54"


def test_moments_by_design_recede_and_the_unplanned_ones_stand_out(redesign):
    page = render_html(redesign)
    by_id = {f["id"]: f for f in redesign["findings"]}
    strong, soft = by_id["f1"], by_id["f5"]
    assert strong["check"]["friction"] == "blocked" and soft["check"]["friction"] == "learning"
    assert re.search(rf'<article class="m stuck" id="m{strong["rank"]}"', page)
    assert re.search(rf'<article class="m [a-z]+ soft" id="m{soft["rank"]}"', page)
    assert len(re.findall(rf'<a class="pin k-[a-z]+" href="#m{strong["rank"]}"[^>]*>.*?width="{2 * render.PIN_R}"', page, re.DOTALL)) == 2
    assert len(re.findall(rf'<a class="pin k-[a-z]+ soft" href="#m{soft["rank"]}"[^>]*>.*?width="{2 * render.SOFT_R}"', page, re.DOTALL)) == 2
    assert re.search(rf'<button type="button" class="tm k-[a-z]+ soft" data-open="{soft["id"]}"', page)
    assert re.search(rf'<button type="button" class="tm k-[a-z]+" data-open="{strong["id"]}"', page)


def test_watch_shows_the_place_and_the_floor_in_words(redesign):
    page = render_html(redesign)
    assert 'data-w-where="{room}, {floor}"' in page and 'data-w-between="Between rooms"' in page
    assert '<p class="where" id="where"></p><p class="lastev" id="lastev"></p>' in page
    assert 'aria-label="Floor"><button type="button" data-show-floor="0" aria-pressed="true">Ground floor</button>' in page


def test_across_players_renders_from_the_file(redesign):
    page = render_html(redesign)
    block = page[page.index('<section class="across"'):]
    block = block[:block.index("</section>")]
    assert "2 of 3 players got stuck here." in block
    assert '<a class="chip you" href="#m1">Player 2: 3 moments</a>' in block
    assert '<span class="chip">Player 1: 4:10</span>' in block


def test_long_node_paths_may_wrap_after_their_separators(redesign):
    f = redesign["findings"][0]
    f["game_state"] = "Looking at BREAK_ROOM/kitchenSink/CabinetDoor, then action_primary/action_secondary"
    f["check"]["note"] = "Short words keep their shape; so does a/short_path."
    page = render_html(redesign)
    row = _row(page, f["rank"])
    assert "BREAK_<wbr>ROOM/<wbr>kitchenSink/<wbr>CabinetDoor," in row
    assert "action_<wbr>primary/<wbr>action_<wbr>secondary" in row
    assert "a/short_path." in row and "a/<wbr>short" not in row
    f["game_state"] = "<b>" + "x" * 30 + "</b>"
    page = render_html(redesign)
    assert "<b>" + "x" * 30 not in page
    assert "&lt;b&gt;" + "x" * 30 + "&lt;/<wbr>b&gt;" in page


def test_no_dashes_in_the_pages_words(redesign):
    page = render_html(redesign)
    assert chr(0x2014) not in page and " " + chr(0x2013) + " " not in page


def test_main_writes_the_page(tmp_path):
    out = tmp_path / "page.html"
    assert render.main([str(REDESIGN), "-o", str(out)]) == 0
    assert out.read_text(encoding="utf-8").startswith("<!DOCTYPE html>")
