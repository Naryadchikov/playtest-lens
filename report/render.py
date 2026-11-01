"""Render a findings.json file as one self-contained HTML page.

The page only renders what the file holds. It computes nothing beyond
formatting seconds as m:ss, converting a world point to image pixels
with each floor's map JSON, placing times along the timeline, and the
structural counts a group needs. Section and card order come from the
file's times and beat fields: sections by their start, cards by time,
ties by rank.

Layout (task 32, Claude Fable 5.1, on task 30's build): the write-up
scrolls on the left and the stage stays on the right: every floor of
the scene side by side, the moment panel under them (the current
moment's clip beside its words, or the player's time and room while
the session plays), and the timeline under that. One inline script
drives the stage from one state: the current moment and the map time.
Picking a problem, a pin, a timeline mark or a card makes that moment
current; Play runs the session at 10x and stops at each shown moment
to play its clip at normal speed, then goes on; a playing clip moves
the dot; the list follows the current moment and the moment in the
middle of the screen becomes current when the reader scrolls. The
script only shows, hides and highlights what the page already drew, by
the times the file holds (written into data-attributes), and moves a
dot to an existing route point. It never makes a finding, a time, a
position or a count. Without script the page shows every moment with
its clip and every floor with the whole route; the heat map view is a
CSS switch (:has), so it needs no script.

All page wording lives in LABELS, so changing a string never means
touching the markup.
"""

from __future__ import annotations

import argparse
import base64
import html
import json
import re
import sys
from pathlib import Path

from analyzer import findings as findings_module

MAPS_DIR = Path(__file__).resolve().parent / "maps"

KIND_ORDER = ("stuck", "confused", "surprised", "suspected_bug")

# Every word the page shows, except values from the findings file.
LABELS = {
    "title": "Playtest Lens: session {id}",
    "session": "Session {id}",
    "meta": {
        "level": "Level",
        "recording": "Recording",
        "length": "Length",
        "date": "Date",
        # Proposal (Claude Opus 5.5, 2026-11-01), not Sasha's wording.
        "model": "Model",
    },
    "sections": {
        "glance": "At a glance",
        "across": "Across players",
        "where": "Where it happened",
        "moments": "The moments",
        "dropped": "Dropped moments",
        # Proposal (Claude Opus 5.5, 2026-11-01), not Sasha's wording:
        # the problems block's heading and words are his to choose.
        "problems": "Top problems",
    },
    "tiles": {
        # Proposals (Claude Fable 5.1, 2026-11-01), not Sasha's wording:
        # the number is the time in the visits and attempts that hold a
        # stuck or blocked moment (analyzer/spatial.py, _lost_s).
        "time_lost": "Time stuck or blocked",
        "time_lost_note": "in the visits and attempts with an unplanned moment",
        "kept": "Moments checked against the video and the event log",
        "of": "of {duration}",
        # Proposals (Claude Fable 5.1, 2026-11-01), not Sasha's wording:
        # the big number is the kept count, so the note no longer repeats it.
        "count_note": "kept",
        "dropped_note": "{dropped} dropped",
    },
    "kinds": {
        "stuck": {"label": "Stuck", "lower": "stuck", "class": "stuck"},
        "confused": {"label": "Confused", "lower": "confused", "class": "confused"},
        "surprised": {"label": "Surprised", "lower": "surprised", "class": "surprised"},
        "suspected_bug": {"label": "Suspected bug", "lower": "suspected bug", "class": "bug"},
    },
    "friction": {
        # Proposal (Claude Opus 5.5, 2026-10-29), not Sasha's wording.
        "learning": {"level": 1, "tag": "by design", "unplanned": False},
        "stuck": {"level": 2, "tag": "unplanned", "unplanned": True},
        "blocked": {"level": 3, "tag": "unplanned", "unplanned": True},
    },
    "meter": {0: "None", 1: "Low", 2: "Medium", 3: "High"},
    "meter_aria": "Friction: {level}",
    "resolved": {"solved": "Resolved", "after": "Resolved after {time}"},
    "abandoned": "Abandoned",
    # Proposals (Claude Opus 5.5, 2026-11-01), not Sasha's wording.
    "problems": {
        "sub": "Places where the player was stuck or blocked, worst first.",
        "attempt": "attempt",
        "visit": "visit",
        "moment": "moment",
        # Proposal (Claude Fable 5.1, 2026-11-01), not Sasha's wording.
        "lost": "{time} stuck",
        "mixed": "Partly resolved",
    },
    "across": {
        "verbs": {
            "stuck": "got stuck",
            "confused": "were confused",
            "surprised": "were surprised",
            "suspected_bug": "suspected a bug",
        },
        "who": "{n} of {of} players {verb} here.",
        "who_other": "{n} of {of} players had {kind} here.",
        "chip_time": "{label}: {time}",
        "chip_moments": "{label}: {n} moments",
        "note": "Chips in the accent outline are this page's player. Others come from their own reports.",
    },
    "moments": {
        # Proposal (Claude Sonnet 5.5, 2026-10-28, from the task 25 plan), not Sasha's wording.
        "sub": "In time order. A room with a puzzle line groups its attempts. Time is from the recording's start flash.",
        "fallback": "Moments",
        "attempt": "Attempt {n} ({span})",
        "attempt_note": "{attempts}, {moments}, {span}",
        "note": "{moments}, {span}",
        "puzzle": "Puzzle {n}: {name}",
        "pin_attempt": "{title}, attempt {n}",
    },
    "card": {
        "game": "Game",
        # Proposal (Claude Opus 5.5, 2026-10-31, task 33), not Sasha's wording.
        "cause": "Likely cause",
        "checker": "Checker",
        "no_quote": "No spoken comment.",
        "f9": "Player pressed F9 at {time}",
        "num_pin": "Show moment {rank} on the map",
        "pin": "Moment {rank}, {kind}, {time}",
        # Proposals (Claude Opus 5.5, 2026-11-01, from mockup B), not Sasha's wording.
        "clip": "Clip {span}",
        "sync": "Map follows the clip",
    },
    # Proposals (Claude Fable 5.1, 2026-11-01, after mockup A's timeline),
    # not Sasha's wording. "bar" and "bar_puzzle" are Claude Opus 5.5's
    # (mockup B).
    "strip": {
        "aria": "Timeline of the recording: the rooms the player was in, time on the upper floor, the kept moments by rank, the dropped candidates and the game events. Click or drag to set the map's time.",
        "rooms": "Rooms",
        "moments": "Moments",
        "dropped": "Dropped",
        "events": "Events",
        "bar": "{room} {span}",
        "bar_puzzle": "{room}, {puzzle} {span}",
        "event": "{time} {label}",
    },
    # Proposals (Claude Fable 5.1, 2026-11-01), not Sasha's wording.
    "focus": {
        "aria": "Which moments to show",
        "all": "All moments",
        "unplanned": "Unplanned only",
    },
    # Proposals (Claude Fable 5.1, 2026-11-01), not Sasha's wording.
    # "Previous", "Next" and "Overview" are mockup A's (Claude Opus 5.5).
    "panel": {
        "play_session": "Play the session",
        "hint": "Runs at 10x and stops at each moment to play its clip at normal speed, then goes on. Or pick a problem, a pin or a moment.",
        "keys": "Space plays and pauses. Left and right arrows step between moments. Escape returns to the overview.",
        "previous": "Previous",
        "next": "Next",
        "overview": "Overview",
        "count": "Moment {n} of {of}",
        # Proposals (Claude Fable 5.1, 2026-11-01), not Sasha's wording:
        # a dropped candidate on the stage says so, and counts among the dropped.
        "count_dropped": "Dropped {n} of {of}",
        "dropped_tag": "Dropped by the check",
        "last": "Last moment: {label}",
        "events_so_far": "Game events so far",
        "events_none_yet": "No game events yet.",
    },
    # Proposals (Claude Opus 5.5, 2026-11-01, from mockup B), not Sasha's wording.
    "floors": ("Ground floor", "Upper floor"),
    "floor_n": "Floor {n}",
    "map": {
        # Adapted from the old one-floor wording by Claude Opus 5.5, 2026-11-01.
        "alt": "Top-down plan of the {level} level, {floor}. The timeline view draws the player's route and numbered pins on top; the heat map view shows where the player spent time.",
        "level": "level",
        "marker": "F9 marker at {time}",
        "start": "start",
        "end": "end",
        "route": "Route, arrows point the way walked (start circle to end circle)",
        "f9": "F9: the player flagged confusion",
        # Proposals (Claude Opus 5.5, 2026-11-01, from mockup B), not Sasha's wording.
        "dropped": "Hollow shapes are candidates the check dropped.",
        "drop_pin": "Dropped, {kind}, {time}",
    },
    # Proposals (Claude Opus 5.5 plan, task 25, 2026-10-28), not Sasha's wording.
    # "view", "trail" and "readout_window" are proposals by
    # Claude Opus 5.5 (Cursor, task 26, 2026-10-28). The window lengths
    # come from Sasha's "10 sec, 15, 30, etc." (Cursor chat,
    # 2026-10-28); 60 is the brief's.
    "timeline": {
        "view": "Map view",
        "view_trail": "Timeline",
        "view_heat": "Heat map",
        "play": "Play",
        "pause": "Pause",
        "readout": "{time} of {duration}",
        "readout_window": "{start}-{time} of {duration}",
        "trail": "Trail",
        "trail_all": "From start",
        "trail_last": "{n} s",
        "windows": (10, 15, 30, 60),
        # Proposal (Claude Fable 5.1, 2026-11-01): the strong trail is the
        # last 30 s by default; the whole route stays faint behind it.
        "trail_default": 30,
        # Proposals (Claude Opus 5.5, 2026-11-01, from mockup B), not Sasha's wording.
        "events_near": "Game events in this moment's visit and clip",
        "events_none": "No game events in this span.",
    },
    # Proposals by Claude Opus 5.5 (Cursor, task 26, 2026-10-28), not Sasha's wording.
    "heat": {
        "title": "Time spent, whole session",
        "low": "Less",
        "high": "More",
        "note": "Each number is the time spent at that spot. The route, the pins and the timeline are in the timeline view.",
    },
    "dropped": {
        "note": "{n} candidates the check did not keep",
        "reason": "Reason: {note}",
    },
    "warning": "warning: map {map} not found; the page has no map section",
}

STYLE = """
:root {
  color-scheme: light dark;
  --bg: #f5f6f8; --surface: #ffffff; --sunk: #eceef2;
  --ink: #151a24; --ink2: #434b5c; --muted: #596175; --line: #d6dae3;
  --accent: #2f45c7; --accent-tint: #e6e9fb; --on-accent: #ffffff;
  --k-stuck: #c2410c; --k-confused: #946200; --k-surprised: #0f766e; --k-bug: #a3195b;
  --t-stuck: #fbe9e0; --t-confused: #f7edd2; --t-surprised: #d9f1ee; --t-bug: #f9dfea;
  /* Pins and markers always use the bright colors: the map is dark in both schemes. */
  --p-stuck: #ff8a5c; --p-confused: #f2c14e; --p-surprised: #4fd1c5; --p-bug: #ff7aa8;
  --bar: #c3c9d5; --bar-puzzle: #9aa6e8; --map-bg: #0a0d14;
  --s1: 4px; --s2: 8px; --s3: 12px; --s4: 16px; --s5: 24px; --s6: 40px;
  --fs-s: .8125rem; --fs-b: .9375rem; --fs-m: 1.125rem; --fs-l: 1.5rem; --fs-xl: 2rem;
  --font: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  --mono: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #0f131b; --surface: #171c27; --sunk: #202636;
    --ink: #e8ecf4; --ink2: #b0b8c8; --muted: #909ab0; --line: #2c3344;
    --accent: #8da2ff; --accent-tint: #232b52; --on-accent: #0b1020;
    --k-stuck: #ff8a5c; --k-confused: #f2c14e; --k-surprised: #4fd1c5; --k-bug: #ff7aa8;
    --t-stuck: #3a2219; --t-confused: #382e12; --t-surprised: #12322f; --t-bug: #3b1a2a;
    --bar: #3a4458; --bar-puzzle: #5867b8;
  }
}
* { box-sizing: border-box; }
[hidden] { display: none !important; }
body { margin: 0; background: var(--bg); color: var(--ink); font: var(--fs-b)/1.5 var(--font); }
a { color: var(--accent); }
a:focus-visible, summary:focus-visible, button:focus-visible, input:focus-visible, select:focus-visible, video:focus-visible { outline: 3px solid var(--accent); outline-offset: 2px; border-radius: 3px; }
.vh { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }
h1 { font-size: var(--fs-xl); line-height: 1.2; margin: 0 0 var(--s2); }
h2 { font-size: var(--fs-l); margin: var(--s6) 0 var(--s2); }
h3 { font-size: var(--fs-m); margin: 0 0 var(--s1); }
h4 { font-size: var(--fs-b); margin: var(--s4) 0 var(--s2); color: var(--ink2); }
.sub { color: var(--muted); font-size: var(--fs-s); margin: 0 0 var(--s3); max-width: 70ch; }
.note { color: var(--muted); font-size: var(--fs-s); font-weight: 400; }
.mono { font-family: var(--mono); font-size: .92em; }

/* Two columns: the header and the write-up on the left scroll, the stage on the right stays.
   The floors take the height the panel and the timeline leave, capped by half the width. */
.page { --side-w: 280px; --foot-h: 200px;
  --floor-h: max(300px, min(calc(100vh - var(--tl-h) - 36px - var(--foot-h) - 44px), calc((56vw - var(--side-w) - 12px - (var(--floors) - 1) * 10px) / var(--ars))));
  --pane-w: calc(var(--floor-h) * var(--ars) + (var(--floors) - 1) * 10px + var(--side-w) + 12px);
  display: grid; grid-template-columns: minmax(0, 1fr) var(--pane-w); grid-template-rows: auto auto 1fr auto;
  grid-template-areas: "head pane" "probs pane" "col pane" "tl tl"; column-gap: var(--s5); padding: 0 var(--s5); max-width: 1880px; margin: 0 auto; }
.page.solo { grid-template-columns: minmax(0, 1fr); grid-template-areas: "head" "probs" "col"; max-width: 1120px; }
.head { grid-area: head; padding-top: var(--s5); min-width: 0; max-width: 1100px; }
.col { grid-area: col; padding: 0 0 40vh; min-width: 0; max-width: 1100px; }
.page.solo .col { padding-bottom: var(--s6); }

/* header */
.meta { display: flex; flex-wrap: wrap; gap: var(--s1) var(--s5); margin: 0 0 var(--s4); padding: 0; list-style: none; color: var(--ink2); font-size: var(--fs-s); }
.meta b { color: var(--muted); font-weight: 600; margin-right: var(--s1); }
.verdict { font-size: var(--fs-m); font-weight: 600; margin: 0; padding: var(--s3) var(--s4); background: var(--surface); border: 1px solid var(--line); border-left: 6px solid var(--accent); border-radius: 6px; }

/* kind shapes in text: badges, legends */
.k { display: inline-block; width: .85em; height: .85em; background: var(--c); flex: none; }
.k-stuck { --c: var(--k-stuck); --p: var(--p-stuck); }
.k-confused { --c: var(--k-confused); --p: var(--p-confused); }
.k-surprised { --c: var(--k-surprised); --p: var(--p-surprised); }
.k-bug { --c: var(--k-bug); --p: var(--p-bug); }
.k.k-confused { border-radius: 50%; }
.k.k-surprised { clip-path: polygon(50% 0, 100% 50%, 50% 100%, 0 50%); }
.k.k-bug { clip-path: polygon(50% 0, 100% 100%, 0 100%); }
svg.sh { display: block; width: 100%; height: 100%; overflow: visible; }
svg.sh use { fill: var(--p); stroke: #0b1020; stroke-width: 1.2; }
.hollow svg.sh use { fill: none; stroke: var(--c); stroke-width: 2.4; }

/* problems: their own grid row, so the stacked layout puts them above the stage */
.problems { grid-area: probs; min-width: 0; max-width: 1100px; margin: 0 0 var(--s5); }
.problems ol { list-style: none; margin: 0; padding: 0; display: grid; gap: var(--s2); counter-reset: problem; }
.problem { background: var(--surface); border: 1px solid var(--line); border-left: 6px solid var(--k-stuck); border-radius: 6px; padding: var(--s2) var(--s4); display: grid; gap: 2px; }
.problem a.place { font-weight: 700; color: var(--ink); text-decoration: none; font-size: var(--fs-m); }
.problem a.place::before { counter-increment: problem; content: counter(problem) ". "; color: var(--muted); font-weight: 600; }
.problem a.place:hover { text-decoration: underline; }
.problem .facts-line { display: flex; flex-wrap: wrap; align-items: center; gap: var(--s1) var(--s4); font-size: var(--fs-s); color: var(--ink2); }
.problem .facts-line > span { display: inline-flex; align-items: center; gap: var(--s2); }
.problem .mks { display: inline-flex; flex-wrap: wrap; gap: 2px; }

/* rank markers: timeline, problems, card numbers */
.mk { position: relative; display: inline-grid; place-items: center; width: 22px; height: 22px; flex: none; color: #0b1020; text-decoration: none; }
.mk svg.sh { position: absolute; inset: 0; }
.mk b { position: relative; font: 700 11px var(--font); }
.k-surprised.mk b, .k-bug.mk b { font-size: 10px; }
.k-bug.mk b { top: 2px; }
a.mk:hover svg.sh use, a.mk:focus-visible svg.sh use { stroke: var(--ink); stroke-width: 2.4; }
.mk.is-active svg.sh use { stroke: var(--accent); stroke-width: 3; }

/* at a glance */
.tiles { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--s3); margin: 0 0 var(--s3); }
.tile { background: var(--surface); border: 1px solid var(--line); border-radius: 6px; padding: var(--s2) var(--s4); }
.tile .n { font-size: var(--fs-l); font-weight: 700; line-height: 1.25; font-variant-numeric: tabular-nums; }
.tile .n .note { margin-left: var(--s1); font-weight: 600; }
.tile .l { color: var(--ink2); font-size: var(--fs-s); }
.tile .l .note { display: block; }
.kinds { list-style: none; margin: 0 0 var(--s4); padding: 0; display: flex; flex-wrap: wrap; gap: var(--s2) var(--s5); font-size: var(--fs-s); color: var(--ink2); }
.kinds li { display: inline-flex; align-items: center; gap: 6px; }
.kinds b { color: var(--ink); font-size: var(--fs-b); }
.kinds .zero, .kinds .zero b { color: var(--muted); }
.kinds .zero .k { opacity: .45; }

/* across players */
.groups { list-style: none; margin: 0; padding: 0; display: grid; gap: var(--s3); }
.groups .group { background: var(--surface); border: 1px solid var(--line); border-radius: 6px; padding: var(--s3) var(--s4); display: grid; gap: var(--s2); }
.groups .group p { margin: 0; color: var(--ink2); }
.group .who { font-weight: 600; color: var(--ink); }
.chips { display: flex; flex-wrap: wrap; gap: var(--s2); align-items: center; }
.chip { display: inline-flex; align-items: center; gap: var(--s1); padding: 2px var(--s3); border: 1px solid var(--line); border-radius: 999px; font-size: var(--fs-s); background: var(--sunk); color: var(--ink2); text-decoration: none; }
.chip.you { background: var(--accent-tint); border-color: var(--accent); color: var(--ink); }
a.chip:hover { border-color: var(--accent); }

/* moments */
section.moments-group { margin-top: var(--s5); }
section.moments-group > h3 { font-size: var(--fs-l); line-height: 1.25; margin: 0 0 var(--s3); padding-bottom: var(--s2); border-bottom: 1px solid var(--line); display: flex; flex-wrap: wrap; align-items: baseline; gap: var(--s1) var(--s3); }
.card, .drop { position: relative; display: grid; min-width: 0; grid-template-columns: minmax(0, 1fr); grid-template-areas: "head" "main" "clip" "facts"; column-gap: var(--s4); margin: 0 0 var(--s3); padding: var(--s3) var(--s4); background: var(--surface); border: 1px solid var(--line); border-left: 6px solid var(--c); border-radius: 8px; transition: border-color .2s, box-shadow .2s; }
/* Without script the fragment jump leaves a card below the top; with script the page centers it exactly. */
html:not(.js) :is(.card, .drop) { scroll-margin-top: 30vh; }
.card.stuck { --c: var(--k-stuck); } .card.confused { --c: var(--k-confused); }
.card.surprised { --c: var(--k-surprised); } .card.bug { --c: var(--k-bug); }
/* A moment by design recedes: a thinner edge, a smaller number. */
.card.soft { border-left-width: 3px; padding-left: calc(var(--s4) + 3px); }
.card.soft .num-pin { width: 22px; height: 22px; }
.card.soft .num-pin b { font-size: 11px; }
.card.soft .summary { font-weight: 500; }
.card.is-active, .drop.is-active, html:not(.js) :is(.card, .drop):target { box-shadow: 0 0 0 2px var(--accent); }
.card-head { grid-area: head; display: flex; flex-wrap: wrap; align-items: center; gap: 6px 10px; margin-bottom: var(--s2); }
.card-main { grid-area: main; }
.card-facts { grid-area: facts; margin-top: var(--s2); padding-top: var(--s2); border-top: 1px solid var(--line); display: grid; gap: var(--s2); }
.num-pin { width: 28px; height: 28px; }
.num-pin b { font-size: 12px; }
.time { font-family: var(--mono); font-size: var(--fs-s); font-weight: 600; color: var(--ink2); font-variant-numeric: tabular-nums; }
.time small { color: var(--muted); font-weight: 400; }
.badge { display: inline-flex; align-items: center; gap: var(--s1); padding: 1px var(--s2); border-radius: 4px; font-size: var(--fs-s); font-weight: 600; background: var(--tint); color: var(--ink); border: 1px solid var(--c); }
.stuck .badge, .badge.k-stuck { --tint: var(--t-stuck); } .confused .badge, .badge.k-confused { --tint: var(--t-confused); }
.surprised .badge, .badge.k-surprised { --tint: var(--t-surprised); } .bug .badge, .badge.k-bug { --tint: var(--t-bug); }
.intent, .floortag { font-size: var(--fs-s); padding: 1px var(--s2); border-radius: 4px; border: 1px dashed var(--muted); color: var(--ink2); }
.intent.unplanned { border-style: solid; border-color: var(--ink2); font-weight: 600; }
.floortag { border-radius: 999px; color: var(--muted); }
.summary { font-size: var(--fs-m); font-weight: 600; margin: 0 0 var(--s2); line-height: 1.35; }
.quote { margin: 0 0 var(--s2); padding-left: var(--s3); border-left: 3px solid var(--line); color: var(--ink2); font-style: italic; }
.quote.none { font-style: normal; color: var(--muted); }
.facts { display: grid; grid-template-columns: max-content minmax(0, 1fr); gap: var(--s1) var(--s3); margin: 0; font-size: var(--fs-s); color: var(--ink2); }
.facts dt { color: var(--muted); font-weight: 600; }
/* A long node path breaks after its slashes and underscores (the renderer's <wbr>), a word only as a last resort. */
.facts dd { margin: 0; min-width: 0; overflow-wrap: anywhere; }
.intent.dropped { border-style: solid; border-color: var(--ink2); font-weight: 600; }
.fric { display: flex; flex-wrap: wrap; align-items: center; gap: var(--s2); margin: 0; font-size: var(--fs-s); color: var(--ink2); }
.meter { display: inline-flex; gap: 2px; }
.meter i { width: 14px; height: 8px; border: 1px solid var(--ink2); border-radius: 2px; }
.meter i.on { background: var(--ink2); }
.status { font-weight: 600; }
.status.open::before { content: "\\25CB  "; } .status.done::before { content: "\\2713  "; }
.f9line { font-size: var(--fs-s); color: var(--ink2); margin: 0; }
.f9line b { border: 1px dashed var(--ink2); border-radius: 4px; padding: 0 var(--s1); margin-right: var(--s1); }
.clip { grid-area: clip; margin: 0 0 var(--s2); align-self: start; }
.clip video { display: block; width: 100%; aspect-ratio: 16 / 9; background: #000; border-radius: 6px; }
.clip figcaption { margin-top: var(--s1); font-size: var(--fs-s); color: var(--muted); display: flex; justify-content: space-between; gap: var(--s2); }
.clip .sync { color: var(--accent); font-weight: 600; visibility: hidden; }
.card.is-playing .clip .sync { visibility: visible; }
@media (min-width: 900px) {
  .card:has(> .clip) { grid-template-columns: minmax(0, 1fr) min(44%, 440px); grid-template-areas: "head clip" "main clip" "facts facts"; grid-template-rows: auto 1fr auto; }
}
/* Unplanned only: the moments by design leave the map, the timeline and the list. */
.page[data-focus="unplanned"] :is(.card.soft, .pin.soft, .mk.soft) { display: none; }
.page[data-focus="unplanned"] section.moments-group:not(:has(.card:not(.soft))) { display: none; }

/* dropped */
.drop { --c: var(--line); border-style: dashed; border-left-style: solid; background: transparent; }
.drop .summary { font-size: var(--fs-b); color: var(--ink2); }
.reason { margin: 0; font-size: var(--fs-s); color: var(--ink); padding: var(--s1) var(--s2); background: var(--sunk); border-radius: 6px; }
.drop .num-pin { width: 18px; height: 18px; }

/* the stage */
.pane { grid-area: pane; position: sticky; top: 0; height: calc(100vh - var(--tl-h)); display: flex; flex-direction: column; gap: var(--s2); padding: var(--s3) 0 var(--s2); }
.toolbar { display: flex; align-items: center; gap: var(--s2) var(--s3); flex-wrap: wrap; min-height: 28px; }
.toolbar .readout { margin-left: auto; }
.seg { display: inline-flex; border: 1px solid var(--line); border-radius: 8px; background: var(--surface); padding: 2px; }
.seg label { position: relative; }
.seg input { position: absolute; inset: 0; margin: 0; opacity: 0; cursor: pointer; }
.seg span { display: block; padding: 2px 12px; border-radius: 6px; font-size: var(--fs-s); font-weight: 600; color: var(--ink2); }
.seg input:checked + span { background: var(--accent); color: var(--on-accent); }
.seg input:focus-visible + span { outline: 3px solid var(--accent); outline-offset: 2px; }
.btn { font: 600 var(--fs-s) var(--font); color: var(--ink); background: var(--surface); border: 1px solid var(--line); border-radius: 8px; padding: 4px 12px; cursor: pointer; display: inline-flex; align-items: center; gap: 6px; }
.btn:hover { border-color: var(--accent); }
.btn:disabled { opacity: .45; cursor: default; }
.btn svg { width: 10px; height: 10px; fill: currentColor; }
.btn.big { font-size: var(--fs-m); padding: var(--s2) var(--s5); background: var(--accent); color: var(--on-accent); border-color: var(--accent); }
.btn.big svg { width: 14px; height: 14px; }
.readout { font-family: var(--mono); font-size: var(--fs-s); color: var(--ink2); white-space: nowrap; font-variant-numeric: tabular-nums; }
.trail { font-size: var(--fs-s); color: var(--ink2); display: inline-flex; gap: 6px; align-items: center; white-space: nowrap; }
.trail select { font: inherit; color: var(--ink); background: var(--surface); border: 1px solid var(--line); border-radius: 6px; padding: 2px 4px; }
.floors { display: flex; gap: 10px; }
.floor { position: relative; width: calc(var(--floor-h) * var(--ar)); height: var(--floor-h); margin: 0; background: var(--map-bg); border-radius: 8px; overflow: hidden; outline: 2px solid transparent; outline-offset: -2px; transition: outline-color .25s; }
.floor.lit { outline-color: var(--accent); }
.floor svg.map { display: block; width: 100%; height: 100%; }
.floor-label { position: absolute; top: 8px; left: 8px; padding: 2px 10px; border-radius: 999px; font-size: var(--fs-s); font-weight: 700; background: rgba(11, 16, 32, .8); color: #e8ecf4; border: 1px solid #3a4458; }
.floor.lit .floor-label { background: #8da2ff; color: #0b1020; border-color: #8da2ff; }
.floor.quiet .bg { opacity: .45; }
.map .route polyline, .map .strong polyline { fill: none; stroke-linejoin: round; stroke-linecap: round; }
.map .route .case { stroke: #0b1020; stroke-opacity: .7; stroke-width: 11; }
.map .route .line { stroke: #dbe7ff; stroke-opacity: .85; stroke-width: 5; }
.map .strong .case { stroke: #0b1020; stroke-width: 17; }
.map .strong .line { stroke: #ffffff; stroke-width: 8; }
.map .strong .faint { stroke: #dbe7ff; stroke-opacity: .25; stroke-width: 5; }
.map .arrow { fill: #ffffff; stroke: #0b1020; stroke-width: 3; }
.map .start { fill: #ffffff; stroke: #0b1020; stroke-width: 6; }
.map .end { fill: #0b1020; stroke: #ffffff; stroke-width: 6; }
.pane[data-mode="moment"] .route { opacity: .3; }
.pane[data-mode="session"] .route, .pane:not([data-mode="whole"]) .ends { display: none; }
.pin { cursor: pointer; }
.pin .scale { transition: transform .25s, opacity .25s; }
.pin use { fill: var(--p); stroke: #0b1020; stroke-width: 1.3; }
.pin.hollow use { fill: rgba(11, 16, 32, .55); stroke: var(--p); stroke-width: 2.6; }
.pin text { font: 700 46px var(--font); fill: #0b1020; text-anchor: middle; dominant-baseline: central; pointer-events: none; }
.pin.soft text { font-size: 37px; }
.pin.soft .scale { opacity: .8; }
.pin.f9 use { fill: #0b1020; stroke: #ffffff; stroke-width: 1.2; stroke-dasharray: 2.4 1.6; }
.pin.f9 text { fill: #ffffff; font-size: 28px; }
.pin:focus { outline: none; }
.pin:focus-visible use, .pin:hover use, html:not(.js) .pin:target use { stroke: #8da2ff; stroke-width: 3; }
.pin .ring { fill: none; stroke: #ffffff; stroke-width: 6; opacity: 0; }
.pin.is-quiet .scale { opacity: .45; }
.pin.is-later { visibility: hidden; }
.pin.is-focus .scale { transform: scale(1.5); opacity: 1; }
.pin.is-focus .ring { opacity: 1; }
.dot .halo { fill: #8da2ff; opacity: .35; }
.dot .core { fill: #8da2ff; stroke: #ffffff; stroke-width: 7; }
.dot .tag { font: 600 34px var(--font); fill: #ffffff; stroke: #0a0d14; stroke-width: 8; paint-order: stroke; text-anchor: start; }
/* Near the floor's right edge the tag sits left of the dot, so it never runs off the map. */
.dot.flip .tag { text-anchor: end; }
.halo-text { font: 700 40px var(--font); fill: #ffffff; stroke: #0a0d14; stroke-width: 9; paint-order: stroke; text-anchor: middle; }

/* heat map view: the plan muted, the whole-session heat on top, nothing else */
.map .heat { display: none; }
.pane:has(.view-heat:checked) .map .heat { display: inline; }
.pane:has(.view-heat:checked) .trail-layer { display: none; }
.pane:has(.view-heat:checked) .floor.quiet .bg { opacity: 1; }
.pane:has(.view-heat:checked) :is(.focus, .readout), .pane[data-mode="whole"] .readout { visibility: hidden; }
/* The timeline bar sits outside the pane, so the heat switch reaches it from the page. */
.page:has(.view-heat:checked) .timeline { visibility: hidden; }
.pane:has(.view-heat:checked) .bg { filter: grayscale(1) brightness(.5); }
.ramp { height: 10px; border-radius: 3px; max-width: 220px; }
.ramp-ends { display: flex; justify-content: space-between; max-width: 220px; color: var(--ink2); margin: 2px 0 var(--s1); }

/* the stage body: the floors with the side column beside them; the foot row under both */
.stagebody { display: flex; gap: var(--s3); flex: 1 1 auto; min-height: 0; }
.side { flex: 1 1 var(--side-w); min-width: 200px; background: var(--surface); border: 1px solid var(--line); border-radius: 8px; padding: var(--s3); overflow: auto; font-size: var(--fs-s); display: flex; flex-direction: column; }
.side p { margin: 0; }
.side > .mode, .foot .rest > .mode { display: none; }
.side > .mode { flex-direction: column; gap: var(--s2); }
.pane[data-mode="whole"] :is(.side-whole, .foot-whole), .pane[data-mode="heat"] .side-heat,
.pane[data-mode="moment"] :is(.side-now, .foot-now), .pane[data-mode="session"] :is(.side-session, .foot-now) { display: flex; }
.pane[data-mode="heat"] .foot { visibility: hidden; }
.side .facts dd, .side .quote, .side .summary, .side .reason { overflow-wrap: anywhere; }
.side-whole { justify-content: center; gap: var(--s3); }
.side-whole .btn.big { align-self: flex-start; }
.side-whole .hint, .side-whole .keys { color: var(--ink2); }
.btn.big { font-size: var(--fs-m); padding: var(--s2) var(--s5); background: var(--accent); color: var(--on-accent); border-color: var(--accent); }
.btn.big svg { width: 14px; height: 14px; }
.side-now .head { display: flex; flex-wrap: wrap; align-items: center; gap: 4px var(--s2); }
.side-now .where { color: var(--ink2); }
.side-now .summary { font-size: var(--fs-b); }
.side-now .card-facts { margin-top: var(--s1); }
.side-session { gap: var(--s3); }
.side-session .now-t { font: 700 var(--fs-xl)/1.1 var(--mono); font-variant-numeric: tabular-nums; }
.side-session .now-where { font-size: var(--fs-m); font-weight: 600; }
.side-session .now-last { color: var(--ink2); }
.side-session .now-last a { color: var(--ink); }
/* The foot row: the clip the whole height on the left; the legend or the game events, then the transport row, on the right. */
.foot { height: var(--foot-h); flex: none; display: grid; grid-template-columns: auto minmax(0, 1fr); grid-template-rows: minmax(0, 1fr) auto; grid-template-areas: "clip rest" "clip nav"; gap: 6px var(--s3); background: var(--surface); border: 1px solid var(--line); border-radius: 8px; padding: var(--s2) var(--s3); font-size: var(--fs-s); overflow: hidden; }
.foot p { margin: 0; }
.foot .rest { grid-area: rest; min-height: 0; min-width: 0; display: flex; flex-direction: column; }
.foot .rest > .mode { flex: 1 1 auto; min-height: 0; }
.foot-whole { flex-direction: column; justify-content: center; gap: var(--s2); }
html:not(.js) .side { display: none; }
.legend { display: flex; flex-wrap: wrap; gap: 4px var(--s4); list-style: none; margin: 0; padding: 0; color: var(--ink2); }
.legend li { display: inline-flex; align-items: center; gap: 6px; }
.stage-clip { grid-area: clip; display: flex; flex-direction: column; gap: 2px; margin: 0; min-height: 0; }
.stage-clip video { display: block; height: calc(var(--foot-h) - 2 * var(--s2) - 2px - 18px); aspect-ratio: 16 / 9; background: #000; border-radius: 6px; }
.stage-clip figcaption { height: 16px; font-size: 11px; line-height: 16px; color: var(--muted); display: flex; justify-content: space-between; gap: var(--s2); white-space: nowrap; overflow: hidden; }
.stage-clip figcaption a { color: var(--ink2); text-decoration: none; font-weight: 600; overflow: hidden; text-overflow: ellipsis; }
.stage-clip figcaption a:hover { text-decoration: underline; }
.stage-clip .sync { color: var(--accent); font-weight: 600; visibility: hidden; }
.pane.is-stage-playing .stage-clip .sync { visibility: visible; }
.evrow { display: flex; flex-direction: column; gap: 4px; min-height: 0; min-width: 0; flex: 1 1 auto; }
.evrow .evh { color: var(--muted); font-weight: 600; white-space: nowrap; }
.events { list-style: none; margin: 0; padding: 0; display: flex; flex-wrap: wrap; gap: 4px var(--s2); overflow: auto; scrollbar-width: thin; align-content: flex-start; }
.events li { display: inline-flex; align-items: center; gap: 4px; color: var(--ink2); padding: 1px 6px; border-radius: 4px; background: var(--sunk); white-space: nowrap; max-width: 34ch; overflow: hidden; text-overflow: ellipsis; transition: background-color 1.2s; }
.events li.later { opacity: .65; }
.events li.fresh { background: var(--accent-tint); color: var(--ink); transition: none; }
.events time { color: var(--muted); font-family: var(--mono); }
.events svg { width: 11px; height: 11px; fill: none; stroke: currentColor; stroke-width: 1.6; flex: none; }
.events span { overflow: hidden; text-overflow: ellipsis; }
.nav { grid-area: nav; display: flex; align-items: center; gap: var(--s2); flex: none; flex-wrap: wrap; }
.nav .count { margin-left: auto; color: var(--ink2); font-variant-numeric: tabular-nums; }
.nav:not(.in-session) .trail { display: none; }

/* the timeline: a bar across the page's foot, staying in view */
.timeline { grid-area: tl; position: sticky; bottom: 0; z-index: 2; height: var(--tl-h); display: grid; grid-template-columns: max-content minmax(0, 1fr); gap: 0 var(--s3); background: var(--surface); border-top: 1px solid var(--line); margin: 0 calc(-1 * var(--s5)); padding: var(--s2) var(--s5); }
.labs, .tracks { display: flex; flex-direction: column; gap: 4px; }
.labs span { height: 14px; line-height: 14px; font-size: 12px; font-weight: 600; color: var(--ink2); white-space: nowrap; display: flex; align-items: center; }
.tracks { position: relative; cursor: crosshair; touch-action: none; }
.track { position: relative; height: 14px; border-radius: 3px; background: var(--sunk); }
.track.r-marks, .track.r-drops, .track.r-events { background: none; }
.track.r-drops { height: 16px; }
.track.r-events { height: 8px; }
.bar { position: absolute; top: 0; bottom: 0; min-width: 2px; border-radius: 3px; background: var(--bar); overflow: hidden; padding: 0 4px; font: 600 11px/14px var(--font); color: var(--ink); white-space: nowrap; text-overflow: ellipsis; }
.bar.puzzle { background: var(--bar-puzzle); }
.bar.up { background: var(--muted); opacity: .55; }
.tick { position: absolute; top: 0; bottom: 0; width: 2px; margin-left: -1px; border-radius: 1px; background: var(--muted); opacity: .6; }
.track .mk { position: absolute; margin-left: -11px; width: 22px; height: 22px; }
.track .mk.soft { opacity: .75; }
.track.r-drops .mk { width: 14px; height: 14px; margin-left: -7px; top: 1px; }
.axis { position: relative; height: 14px; font: 12px var(--mono); color: var(--muted); }
.axis span { position: absolute; top: 2px; transform: translateX(-50%); white-space: nowrap; }
.axis span:first-child { transform: none; }
.tracks .past { position: absolute; left: 0; top: 0; bottom: 18px; background: var(--accent); opacity: .1; pointer-events: none; }
.tracks .band { position: absolute; top: 0; bottom: 18px; background: var(--accent); opacity: .18; pointer-events: none; min-width: 2px; }
.tracks .cursor { position: absolute; top: 0; bottom: 18px; width: 2px; margin-left: -1px; background: var(--accent); pointer-events: none; }

@media (prefers-reduced-motion: no-preference) { html { scroll-behavior: smooth; } }
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { transition: none !important; animation: none !important; } }
@media (max-width: 1100px) {
  /* Stacked: the problems above the stage, so half a screen still opens on the worst places. */
  .page { grid-template-columns: minmax(0, 1fr); grid-template-rows: auto auto auto auto 1fr; grid-template-areas: "head" "probs" "pane" "tl" "col"; --foot-h: 210px;
    --floor-h: max(160px, min(50vh, calc((100vw - 2 * var(--s5) - (var(--floors) - 1) * 10px) / var(--ars)))); }
  .pane { position: static; height: auto; }
  .timeline { position: static; border: 1px solid var(--line); border-radius: 8px; margin: 0; padding: var(--s2) var(--s3); }
  .page:has(.view-heat:checked) .timeline { display: none; }
  .col { padding-bottom: var(--s6); }
}
@media (max-width: 640px) {
  .stagebody { flex-wrap: wrap; }
  .side { flex-basis: 100%; max-height: none; }
  .foot { height: auto; grid-template-columns: minmax(0, 1fr); grid-template-areas: "clip" "rest" "nav"; }
  .stage-clip video { height: auto; width: 100%; }
}
@media print {
  body { background: #fff; color: #000; }
  .page { grid-template-columns: 1fr; grid-template-areas: "head" "col"; }
  .pane, .timeline { display: none; }
  .card, .drop, .tile, .problem { break-inside: avoid; }
  .clip { display: none; }
}
"""

# The heat map's color scale, cool and sparse to hot, as on public
# shooter heatmaps. One list feeds the SVG filter and the legend's bar.
HEAT_RAMP = ("#2b59ff", "#18c1e6", "#3ddc84", "#f5d327", "#fb7a1c", "#e8231f")
HEAT_ALPHA = (0, .5, .65, .78, .86, .92)


def _ramp_table(channel):
    return " ".join(
        f"{int(color[1 + 2 * channel:3 + 2 * channel], 16) / 255:.3f}"
        for color in HEAT_RAMP
    )


# Shapes in a -10..10 box, drawn by <use> at any size; heat spots are
# white blobs whose opacity is their weight, and the filter turns that
# opacity into the color scale. One hidden SVG holds them for the page.
SVG_DEFS = (
    '<svg class="vh" width="0" height="0" aria-hidden="true" focusable="false"><defs>'
    '<symbol id="sh-stuck" viewBox="-10 -10 20 20" overflow="visible"><rect x="-8" y="-8" width="16" height="16" rx="1.5"/></symbol>'
    '<symbol id="sh-confused" viewBox="-10 -10 20 20" overflow="visible"><circle r="8.8"/></symbol>'
    '<symbol id="sh-surprised" viewBox="-10 -10 20 20" overflow="visible"><polygon points="0,-10 10,0 0,10 -10,0"/></symbol>'
    '<symbol id="sh-bug" viewBox="-10 -10 20 20" overflow="visible"><polygon points="0,-9.5 10,8.5 -10,8.5"/></symbol>'
    '<symbol id="sh-f9" viewBox="-10 -10 20 20" overflow="visible"><polygon points="0,-9.5 8.2,-4.75 8.2,4.75 0,9.5 -8.2,4.75 -8.2,-4.75"/></symbol>'
    # Game event icons, one per kind the analyzer writes; a kind without one gets a plain dot.
    '<symbol id="ev-door" viewBox="0 0 12 12"><rect x="2.5" y="1" width="7" height="10" rx="1"/><circle cx="7.5" cy="6.5" r=".8"/></symbol>'
    '<symbol id="ev-lock" viewBox="0 0 12 12"><rect x="2" y="5.5" width="8" height="5.5" rx="1"/><path d="M4 5.5V4a2 2 0 0 1 4 0v1.5"/></symbol>'
    '<symbol id="ev-pickup" viewBox="0 0 12 12"><path d="M2 5.5h8M6 1.5v8M2.5 10.5h7"/></symbol>'
    '<symbol id="ev-quest" viewBox="0 0 12 12"><path d="M3 11V1.5h6.5L8 4l1.5 2.5H3"/></symbol>'
    '<symbol id="ev-pause" viewBox="0 0 12 12"><path d="M4 2v8M8 2v8"/></symbol>'
    '<symbol id="ev-resume" viewBox="0 0 12 12"><path d="M3.5 2l6 4-6 4z"/></symbol>'
    '<symbol id="ev-other" viewBox="0 0 12 12"><circle cx="6" cy="6" r="2.5"/></symbol>'
    '<radialGradient id="heat-blob"><stop offset="0" stop-color="#fff"/>'
    '<stop offset=".4" stop-color="#fff" stop-opacity=".85"/>'
    '<stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>'
    '<filter id="heat-ramp" color-interpolation-filters="sRGB">'
    '<feColorMatrix type="matrix" values="0 0 0 1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1 0"/>'
    "<feComponentTransfer>"
    f'<feFuncR type="table" tableValues="{_ramp_table(0)}"/>'
    f'<feFuncG type="table" tableValues="{_ramp_table(1)}"/>'
    f'<feFuncB type="table" tableValues="{_ramp_table(2)}"/>'
    f'<feFuncA type="table" tableValues="{" ".join(str(a) for a in HEAT_ALPHA)}"/>'
    "</feComponentTransfer></filter>"
    "</defs></svg>"
)

# Map drawing sizes, in map image pixels (about 48 per metre). A moment
# by design (friction "learning") gets the smaller pin, so the unplanned
# ones stand out.
PIN_R = 44
SOFT_R = 34
DROP_R = 28
F9_R = 34
EVENT_KINDS = ("door", "lock", "pickup", "quest", "pause", "resume")

# The timeline: two markers closer than this share of the recording go
# on separate rows, up to STRIP_ROWS rows. The row heights feed the
# timeline's height, which the stage needs to size the floors.
STRIP_GAP = 0.035
STRIP_ROWS = 3
STRIP_ROW_PX = 22
TRACK_PX = 14
DROPS_PX = 16
EVENTS_PX = 8
TRACK_GAP_PX = 4
TIMELINE_PAD_PX = 17
BAR_LABEL_MIN_PCT = 4.0
TICK_STEPS = (30, 60, 120, 300, 600, 1200, 1800, 3600)


def _e(value):
    return html.escape(str(value), quote=True)


_LONG_TOKEN = re.compile(r"\S{24,}")


# Escaped text where a long node path or identifier ("BREAK_ROOM/kitchenSink/CabinetDoor")
# may wrap after its slashes and underscores, so a narrow column never splits a word.
def _breakable(value):
    def soften(match):
        return match.group(0).replace("/", "/<wbr>").replace("_", "_<wbr>")

    return _LONG_TOKEN.sub(soften, _e(value))


def _mss(seconds):
    total = int(seconds)
    return f"{total // 60}:{total % 60:02d}"


def _duration(seconds):
    total = int(seconds)
    if total < 60:
        return f"{total} s"
    return _mss(total)


def _span(start_s, end_s):
    start, end = _mss(start_s), _mss(end_s)
    return start if start == end else f"{start}-{end}"


def _plural(count, word):
    return f"{count} {word}" if count == 1 else f"{count} {word}s"


def world_to_px(meta, x, z):
    """Convert a world point to image pixels with the map's own JSON."""
    px = (x - meta["world_min_x"]) / (
        meta["world_max_x"] - meta["world_min_x"]
    ) * meta["px_width"]
    py = (z - meta["world_min_z"]) / (
        meta["world_max_z"] - meta["world_min_z"]
    ) * meta["px_height"]
    return px, py


def _px_per_m(meta):
    return meta["px_width"] / (meta["world_max_x"] - meta["world_min_x"])


# Load each floor's JSON and PNG. Returns a list of (meta, data URI) in
# floor order, or None and the first missing name. A map name is a bare
# filename, never a path.
def _load_floors(names, maps_dir):
    directory = Path(maps_dir) if maps_dir is not None else MAPS_DIR
    floors = []
    for name in names:
        if not isinstance(name, str) or not name or Path(name).name != name:
            return None, name
        json_path = directory / f"{name}.json"
        png_path = directory / f"{name}.png"
        if not json_path.is_file() or not png_path.is_file():
            return None, name
        meta = json.loads(json_path.read_text(encoding="utf-8"))
        encoded = base64.b64encode(png_path.read_bytes()).decode("ascii")
        floors.append((meta, f"data:image/png;base64,{encoded}"))
    return floors, None


def _floor_name(index):
    names = LABELS["floors"]
    return names[index] if index < len(names) else LABELS["floor_n"].format(n=index)


def _kind(kind):
    return LABELS["kinds"].get(
        kind, {"label": str(kind), "lower": str(kind), "class": "stuck"}
    )


# A moment by design (friction "learning") recedes on the map, the
# timeline and the list; the unplanned ones stand out.
def _is_soft(finding):
    rule = LABELS["friction"].get(finding["check"].get("friction"))
    return rule is not None and not rule["unplanned"]


def _shape(kind, extra=""):
    return (
        f'<svg class="sh" viewBox="-10 -10 20 20" aria-hidden="true" focusable="false">'
        f'<use href="#sh-{_kind(kind)["class"]}" x="-10" y="-10" width="20" height="20"/></svg>{extra}'
    )


def _pin_words(finding):
    return LABELS["card"]["pin"].format(
        rank=finding["rank"],
        kind=_kind(finding["kind"])["label"],
        time=_mss(finding["time_s"]),
    )


def _drop_words(finding):
    return LABELS["map"]["drop_pin"].format(
        kind=_kind(finding["kind"])["lower"], time=_mss(finding["time_s"])
    )


def _pin_title(finding):
    beat = finding.get("beat") or {}
    # A beat with no puzzle line is an area visit: the area alone.
    title = beat.get("puzzle") or beat.get("area")
    if not title:
        return LABELS["moments"]["fallback"]
    attempt = beat.get("attempt")
    if isinstance(attempt, int) and attempt > 1:
        return LABELS["moments"]["pin_attempt"].format(title=title, n=attempt)
    return title


def _models(findings):
    return ", ".join(
        sorted({f["check"]["model"] for f in findings if f["check"].get("model")})
    )


def _render_header(data):
    session = data["session"]
    player = session.get("player")
    heading = LABELS["session"].format(id=_e(session["id"]))
    if player:
        heading += f": {_e(player)}"

    words = LABELS["meta"]
    meta = []
    if session.get("level"):
        meta.append(f'<li><b>{words["level"]}</b>{_e(session["level"])}</li>')
    meta.append(
        f'<li><b>{words["recording"]}</b>'
        f'<span class="mono">{_e(session["recording"])}</span></li>'
    )
    meta.append(f'<li><b>{words["length"]}</b>{_mss(session["duration_s"])}</li>')
    models = _models(data["findings"])
    if models:
        meta.append(f'<li><b>{words["model"]}</b><span class="mono">{_e(models)}</span></li>')
    if session.get("recorded"):
        meta.append(f'<li><b>{words["date"]}</b>{_e(session["recorded"])}</li>')

    parts = [
        '<header class="head">',
        f"<h1>{heading}</h1>",
        f'<ul class="meta">{"".join(meta)}</ul>',
    ]
    summary = data.get("summary")
    if summary and summary.get("verdict"):
        parts.append(f'<p class="verdict">{_e(summary["verdict"])}</p>')
    parts.append("</header>")
    return parts


def _render_meter(friction):
    rule = LABELS["friction"].get(friction)
    if rule is None:
        return ""
    level = rule["level"]
    word = LABELS["meter"][level]
    bars = "".join(
        '<i class="on"></i>' if index <= level else "<i></i>" for index in range(1, 4)
    )
    aria = LABELS["meter_aria"].format(level=word.lower())
    return f'<span class="meter" role="img" aria-label="{_e(aria)}">{bars}</span>{_e(word)}'


# The worst places, from summary.problems. Each links to its first
# moment and lists its moments by rank.
def _render_problems(problems, by_id):
    words = LABELS["problems"]
    items = []
    for problem in problems:
        moments = [by_id[moment] for moment in problem["moments"] if moment in by_id]
        first = moments[0] if moments else None
        place = _e(problem["place"])
        if first is not None:
            place = f'<a class="place" href="#m{first["rank"]}">{place}</a>'
        else:
            place = f'<span class="place">{place}</span>'
        is_puzzle = bool(first and (first.get("beat") or {}).get("puzzle"))
        bits = [
            _render_meter(problem["friction"]),
            _e(_plural(problem["attempts"], words["attempt" if is_puzzle else "visit"])),
            _e(_plural(len(problem["moments"]), words["moment"])),
        ]
        if problem["lost_s"]:
            bits.append(_e(words["lost"].format(time=_mss(problem["lost_s"]))))
        resolved = problem["resolved"]
        if resolved == "solved":
            bits.append(f'<span class="status done">{_e(LABELS["resolved"]["solved"])}</span>')
        elif resolved == "abandoned":
            bits.append(f'<span class="status open">{_e(LABELS["abandoned"])}</span>')
        elif resolved == "mixed":
            bits.append(f'<span class="status">{_e(words["mixed"])}</span>')
        marks = "".join(
            f'<a class="mk k-{_kind(f["kind"])["class"]}" href="#m{f["rank"]}" '
            f'aria-label="{_e(_pin_words(f))}">{_shape(f["kind"], f"<b>{f['rank']}</b>")}</a>'
            for f in sorted(moments, key=lambda f: f["rank"])
        )
        line = "".join(f"<span>{bit}</span>" for bit in bits)
        items.append(
            f'<li class="problem">{place}'
            f'<span class="facts-line">{line}<span class="mks">{marks}</span></span></li>'
        )
    return [
        '<section class="problems" aria-labelledby="problems">',
        f'<h2 id="problems">{_e(LABELS["sections"]["problems"])}</h2>',
        f'<p class="sub">{_e(words["sub"])}</p>',
        f'<ol>{"".join(items)}</ol>',
        "</section>",
    ]


def _render_glance(summary, duration_s):
    tiles = LABELS["tiles"]
    parts = [
        '<section aria-labelledby="glance">',
        f'<h2 id="glance" class="vh">{LABELS["sections"]["glance"]}</h2>',
        '<div class="tiles">',
    ]
    if summary["lost_s"]:
        of_note = tiles["of"].format(duration=_mss(duration_s))
        parts.append(
            f'<div class="tile"><div class="n">{_mss(summary["lost_s"])}'
            f'<span class="note">{_e(of_note)}</span></div>'
            f'<div class="l">{_e(tiles["time_lost"])}'
            f'<span class="note">{_e(tiles["time_lost_note"])}</span></div></div>'
        )
    dropped_note = tiles["dropped_note"].format(dropped=summary["dropped"])
    parts.append(
        f'<div class="tile"><div class="n">{summary["kept"]}'
        f'<span class="note">{_e(tiles["count_note"])}</span></div>'
        f'<div class="l">{_e(tiles["kept"])}'
        f'<span class="note">{_e(dropped_note)}</span></div></div>'
    )
    parts.append("</div>")
    kinds = []
    for kind in KIND_ORDER:
        info = _kind(kind)
        count = summary["counts"][kind]
        css = ' class="zero"' if count == 0 else ""
        kinds.append(
            f'<li{css}><span class="k k-{info["class"]}" aria-hidden="true"></span>'
            f'<b>{count}</b>{_e(info["label"])}</li>'
        )
    parts.extend([f'<ul class="kinds">{"".join(kinds)}</ul>', "</section>"])
    return parts


def _first_rank(moments, id_to_rank):
    for moment in moments:
        if moment in id_to_rank:
            return id_to_rank[moment]
    return None


def _render_across(cross_player, id_to_rank):
    across = LABELS["across"]
    parts = [
        '<section aria-labelledby="across">',
        f'<h2 id="across">{LABELS["sections"]["across"]}</h2>',
        '<ul class="groups">',
    ]
    for group in cross_player:
        kind = group["kind"]
        affected = len(group["players"])
        verb = across["verbs"].get(kind)
        if verb:
            who = across["who"].format(n=affected, of=group["of"], verb=verb)
        else:
            who = across["who_other"].format(n=affected, of=group["of"], kind=kind)
        chips = []
        for player in group["players"]:
            target = _first_rank(player["moments"], id_to_rank)
            if player.get("here"):
                if target is not None and len(player["moments"]) > 1:
                    text = across["chip_moments"].format(
                        label=player["label"], n=len(player["moments"])
                    )
                else:
                    text = across["chip_time"].format(
                        label=player["label"], time=_mss(player["worst_t"])
                    )
                if target is not None:
                    chips.append(f'<a class="chip you" href="#m{target}">{_e(text)}</a>')
                else:
                    chips.append(f'<span class="chip you">{_e(text)}</span>')
            else:
                text = across["chip_time"].format(
                    label=player["label"], time=_mss(player["worst_t"])
                )
                chips.append(f'<span class="chip">{_e(text)}</span>')
        parts.append(
            f'<li class="group"><h3>{_e(group["place"])}</h3>'
            f'<p><span class="who">{_e(who)}</span></p>'
            f'<div class="chips">{"".join(chips)}</div></li>'
        )
    parts.extend(["</ul>", f'<p class="note">{_e(across["note"])}</p>', "</section>"])
    return parts


def _pct(time_s, duration_s):
    if duration_s <= 0:
        return 0.0
    return max(0.0, min(100.0, time_s / duration_s * 100))


# Rows for markers along the strip: a marker takes the first row whose
# last marker is at least STRIP_GAP of the recording earlier; when every
# row is full it shares the row with the most room.
def _stack(times, duration_s):
    lasts = []
    rows = []
    for time_s in times:
        share = time_s / duration_s if duration_s > 0 else 0.0
        row = next(
            (index for index, last in enumerate(lasts) if share - last >= STRIP_GAP),
            None,
        )
        if row is None and len(lasts) < STRIP_ROWS:
            lasts.append(share)
            row = len(lasts) - 1
        elif row is None:
            row = min(range(len(lasts)), key=lambda index: lasts[index])
        lasts[row] = share
        rows.append(row)
    return rows, max(1, len(lasts))


def _bar(start_s, end_s, duration_s, css, title):
    left = _pct(start_s, duration_s)
    width = max(0.0, _pct(end_s, duration_s) - left)
    return (
        f'<span class="{css}" style="left:{left:.2f}%;width:{width:.2f}%" '
        f'title="{_e(title)}"></span>'
    )


# The timeline under the panel: the rooms the player was in on one
# row (puzzle visits in the puzzle colour), one row per upper floor,
# the kept moments by rank, the dropped candidates, the game events as
# ticks, and a time axis. Returns the markup and its height in pixels,
# which the stage needs to size the floors. The script draws the map
# time on it and reads clicks and drags as a map time.
def _timeline_height(row_count, floor_count, has_drops, has_events):
    rows = [TRACK_PX, row_count * STRIP_ROW_PX, TRACK_PX]
    rows.extend(TRACK_PX for _floor in range(1, floor_count))
    if has_drops:
        rows.append(DROPS_PX)
    if has_events:
        rows.append(EVENTS_PX)
    return sum(rows) + TRACK_GAP_PX * (len(rows) - 1) + TIMELINE_PAD_PX


def _render_timeline(data, kept, dropped, floor_count):
    duration = data["session"]["duration_s"]
    words = LABELS["strip"]
    labs = []
    tracks = []

    bars = []
    for zone in data.get("zones") or []:
        end = zone["end_s"] if zone["end_s"] is not None else duration
        span = _span(max(0.0, zone["start_s"]), end)
        room = zone["zone"]
        if zone["puzzle"]:
            title = words["bar_puzzle"].format(room=room, puzzle=zone["puzzle"], span=span)
        else:
            title = words["bar"].format(room=room, span=span)
        css = "bar puzzle" if zone["puzzle"] else "bar"
        left = _pct(zone["start_s"], duration)
        width = max(0.0, _pct(end, duration) - left)
        # A short visit keeps its name for the tooltip only.
        text = _e(room) if width >= BAR_LABEL_MIN_PCT else ""
        bars.append(
            f'<span class="{css}" style="left:{left:.2f}%;width:{width:.2f}%" '
            f'data-s="{zone["start_s"]}" data-e="{end}" data-room="{_e(room)}" '
            f'title="{_e(title)}">{text}</span>'
        )
    labs.append(f"<span>{_e(words['rooms'])}</span>")
    tracks.append(f'<div class="track r-rooms">{"".join(bars)}</div>')

    route = data.get("route") or {}
    for floor in range(1, floor_count):
        name = _floor_name(floor)
        bars = [
            _bar(span["start_s"], span["end_s"], duration, "bar up",
                 words["bar"].format(room=name, span=_span(span["start_s"], span["end_s"])))
            for span in route.get("floor_spans", [])
            if span["floor"] == floor
        ]
        labs.append(f"<span>{_e(name)}</span>")
        tracks.append(f'<div class="track r-floor">{"".join(bars)}</div>')

    by_time = sorted(kept, key=lambda f: (f["time_s"], f["rank"]))
    rows, row_count = _stack([f["time_s"] for f in by_time], duration)
    height = row_count * STRIP_ROW_PX
    marks = []
    for finding, row in zip(by_time, rows):
        info = _kind(finding["kind"])
        label = _pin_words(finding)
        soft = " soft" if _is_soft(finding) else ""
        marks.append(
            f'<a class="mk{soft} k-{info["class"]}" href="#m{finding["rank"]}" '
            f'style="left:{_pct(finding["time_s"], duration):.2f}%;top:{row * STRIP_ROW_PX}px" '
            f'aria-label="{_e(label)}" title="{_e(label)}">'
            f'{_shape(finding["kind"], f"<b>{finding['rank']}</b>")}</a>'
        )
    labs.append(f'<span style="height:{height}px">{_e(words["moments"])}</span>')
    tracks.append(f'<div class="track r-marks" style="height:{height}px">{"".join(marks)}</div>')

    if dropped:
        drops = []
        for finding in dropped:
            info = _kind(finding["kind"])
            label = _drop_words(finding)
            drops.append(
                f'<a class="mk hollow k-{info["class"]}" href="#d-{_e(finding["id"])}" '
                f'style="left:{_pct(finding["time_s"], duration):.2f}%" '
                f'aria-label="{_e(label)}" title="{_e(label)}">{_shape(finding["kind"])}</a>'
            )
        labs.append(f'<span style="height:{DROPS_PX}px">{_e(words["dropped"])}</span>')
        tracks.append(f'<div class="track r-drops">{"".join(drops)}</div>')

    events = data.get("events") or []
    if events:
        ticks = "".join(
            f'<i class="tick" style="left:{_pct(event["t"], duration):.2f}%" '
            f'title="{_e(words["event"].format(time=_mss(event["t"]), label=event["label"]))}"></i>'
            for event in events
        )
        labs.append(f'<span style="height:{EVENTS_PX}px">{_e(words["events"])}</span>')
        tracks.append(f'<div class="track r-events">{ticks}</div>')

    step = next((s for s in TICK_STEPS if duration / s <= 10), TICK_STEPS[-1])
    ticks = []
    tick = 0
    while tick <= duration:
        ticks.append(f'<span style="left:{_pct(tick, duration):.2f}%">{_mss(tick)}</span>')
        tick += step
    labs.append("<span></span>")
    tracks.append(f'<div class="axis" aria-hidden="true">{"".join(ticks)}</div>')

    parts = [
        f'<section class="timeline" aria-label="{_e(words["aria"])}">',
        f'<div class="labs">{"".join(labs)}</div>',
        f'<div class="tracks" data-duration="{duration}">',
        *tracks,
        '<div class="past" hidden></div>'
        '<div class="band" hidden></div><div class="band" hidden></div>'
        '<div class="cursor" hidden></div>',
        "</div>",
        "</section>",
    ]
    return parts, _timeline_height(row_count, floor_count, bool(dropped), bool(events))


def _render_heat(spots, meta, top):
    if not spots:
        return []
    scale = _px_per_m(meta)
    blobs = []
    labels = []
    for spot in spots:
        cx, cy = world_to_px(meta, spot["x"], spot["z"])
        radius = spot["r_m"] * scale
        weight = 0.35 + 0.65 * spot["seconds"] / top
        blobs.append(
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{radius:.1f}" '
            f'fill="url(#heat-blob)" fill-opacity="{weight:.2f}"/>'
        )
        labels.append(
            f'<text class="halo-text" x="{cx:.1f}" y="{cy + 14:.1f}">{_mss(spot["seconds"])}</text>'
        )
    return [
        '<g class="heat" aria-hidden="true">',
        '<g filter="url(#heat-ramp)">',
        *blobs,
        "</g>",
        *labels,
        "</g>",
    ]


# Runs of consecutive route points on one floor: (floor, [points]).
def _route_runs(points):
    runs = []
    for point in points:
        if runs and runs[-1][0] == point[3]:
            runs[-1][1].append(point)
        else:
            runs.append((point[3], [point]))
    return runs


# One floor's share of the route: each run drawn as a casing and a line;
# the line carries the run's times for the script.
def _render_route(runs, floor, meta):
    parts = ['<g class="route" aria-hidden="true">']
    for run_floor, points in runs:
        if run_floor != floor:
            continue
        pixels = " ".join(
            "{:.1f},{:.1f}".format(*world_to_px(meta, point[1], point[2])) for point in points
        )
        stamps = " ".join(str(point[0]) for point in points)
        parts.append(f'<polyline class="case" points="{pixels}"/>')
        parts.append(f'<polyline class="line" data-t="{stamps}" points="{pixels}"/>')
    parts.append("</g>")
    return parts


def _render_ends(points, floor, meta):
    parts = ['<g class="ends" aria-hidden="true">']
    for point, css, word, dy in (
        (points[0], "start", LABELS["map"]["start"], -44),
        (points[-1], "end", LABELS["map"]["end"], 74),
    ):
        if point[3] != floor:
            continue
        x, y = world_to_px(meta, point[1], point[2])
        parts.append(
            f'<circle class="{css}" cx="{x:.1f}" cy="{y:.1f}" r="22"/>'
            f'<text class="halo-text" x="{x:.1f}" y="{y + dy:.1f}">{_e(word)}</text>'
        )
    parts.append("</g>")
    return parts


def _render_pins(kept, dropped, markers, floor, meta, id_to_rank):
    parts = ['<g class="pins">']
    for finding in dropped:
        at = finding.get("at")
        if at is None or at["floor"] != floor:
            continue
        info = _kind(finding["kind"])
        x, y = world_to_px(meta, at["x"], at["z"])
        parts.append(
            f'<a class="pin hollow k-{info["class"]}" id="pin-d-{_e(finding["id"])}" '
            f'href="#d-{_e(finding["id"])}" data-t="{finding["time_s"]}" '
            f'aria-label="{_e(_drop_words(finding))}" transform="translate({x:.1f} {y:.1f})">'
            f'<g class="scale"><circle class="ring" r="{DROP_R + 12}"/>'
            f'<use href="#sh-{info["class"]}" x="-{DROP_R}" y="-{DROP_R}" '
            f'width="{2 * DROP_R}" height="{2 * DROP_R}"/></g></a>'
        )
    for finding in kept:
        at = finding.get("at")
        if at is None or at["floor"] != floor:
            continue
        info = _kind(finding["kind"])
        rank = finding["rank"]
        x, y = world_to_px(meta, at["x"], at["z"])
        soft = _is_soft(finding)
        radius = SOFT_R if soft else PIN_R
        dy = (6 if soft else 8) if info["class"] == "bug" else 2
        css = f'pin k-{info["class"]}' + (" soft" if soft else "")
        parts.append(
            f'<a class="{css}" id="pin-m{rank}" href="#m{rank}" '
            f'data-t="{finding["time_s"]}" aria-label="{_e(_pin_words(finding))}" '
            f'transform="translate({x:.1f} {y:.1f})">'
            f'<g class="scale"><circle class="ring" r="{radius + 14}"/>'
            f'<use href="#sh-{info["class"]}" x="-{radius}" y="-{radius}" '
            f'width="{2 * radius}" height="{2 * radius}"/><text y="{dy}">{rank}</text></g></a>'
        )
    for index, marker in enumerate(markers, start=1):
        if marker["floor"] != floor:
            continue
        x, y = world_to_px(meta, marker["x"], marker["z"])
        moment = marker.get("moment")
        target = id_to_rank.get(moment) if moment else None
        label = LABELS["map"]["marker"].format(time=_mss(marker["t"]))
        body = (
            f'<use href="#sh-f9" x="-{F9_R}" y="-{F9_R}" width="{2 * F9_R}" height="{2 * F9_R}"/>'
            "<text>F9</text>"
        )
        if target is not None:
            parts.append(
                f'<a class="pin f9" id="pin-f{index}" href="#m{target}" data-t="{marker["t"]}" '
                f'aria-label="{_e(label)}" transform="translate({x:.1f} {y:.1f})">{body}</a>'
            )
        else:
            parts.append(
                f'<g class="pin f9" id="pin-f{index}" data-t="{marker["t"]}" '
                f'aria-label="{_e(label)}" transform="translate({x:.1f} {y:.1f})">{body}</g>'
            )
    parts.append("</g>")
    return parts


def _render_floor(data, index, meta, data_uri, runs, floor_count, kept, dropped, markers, id_to_rank, top):
    route = data["route"]
    width = meta["px_width"]
    height = meta["px_height"]
    level = data["session"].get("level") or LABELS["map"]["level"]
    alt = LABELS["map"]["alt"].format(level=level, floor=_floor_name(index).lower())
    parts = [
        f'<figure class="floor" data-floor="{index}" style="--ar:{width / height:.4f}">',
        f'<svg class="map" viewBox="0 0 {width} {height}" aria-labelledby="map-{index}-title">',
        f'<title id="map-{index}-title">{_e(alt)}</title>',
        f'<image class="bg" href="{data_uri}" x="0" y="0" width="{width}" height="{height}"/>',
    ]
    parts.extend(_render_heat([s for s in route["heat"] if s["floor"] == index], meta, top))
    parts.append('<g class="trail-layer">')
    parts.extend(_render_route(runs, index, meta))
    if route["points"]:
        parts.extend(_render_ends(route["points"], index, meta))
    parts.append('<g class="strong" aria-hidden="true"></g>')
    parts.extend(_render_pins(kept, dropped, markers, index, meta, id_to_rank))
    parts.append(
        '<g class="dot" visibility="hidden" aria-hidden="true">'
        '<circle class="halo" r="46"/><circle class="core" r="20"/>'
        '<text class="tag" x="34" y="-30"></text></g>'
    )
    parts.extend(["</g>", "</svg>"])
    if floor_count > 1:
        parts.append(f'<figcaption class="floor-label">{_e(_floor_name(index))}</figcaption>')
    parts.append("</figure>")
    return parts


def _render_toolbar(duration_s, has_heat, has_soft):
    words = LABELS["timeline"]
    focus = LABELS["focus"]
    total = int(duration_s)
    parts = ['<div class="toolbar">']
    if has_heat:
        parts.append(
            f'<div class="seg views" role="radiogroup" aria-label="{_e(words["view"])}">'
            '<label><input type="radio" name="view" value="trail" checked>'
            f'<span>{_e(words["view_trail"])}</span></label>'
            '<label><input type="radio" name="view" value="heat" class="view-heat">'
            f'<span>{_e(words["view_heat"])}</span></label></div>'
        )
    if has_soft:
        parts.append(
            f'<div class="seg focus" role="radiogroup" aria-label="{_e(focus["aria"])}" data-needs-script hidden>'
            '<label><input type="radio" name="focus" value="all" checked>'
            f'<span>{_e(focus["all"])}</span></label>'
            '<label><input type="radio" name="focus" value="unplanned">'
            f'<span>{_e(focus["unplanned"])}</span></label></div>'
        )
    readout = words["readout"].format(time=_mss(total), duration=_mss(total))
    parts.append(
        f'<output class="readout" data-needs-script hidden data-readout="{_e(words["readout"])}" '
        f'data-readout-window="{_e(words["readout_window"])}">{_e(readout)}</output>'
    )
    parts.append("</div>")
    return parts


# The side column beside the floors: the overview's one big action, the
# heat legend, the current moment's own words (the script clones its
# card), or the player's time and room while the session plays.
def _render_side(has_heat):
    panel = LABELS["panel"]
    play_svg = '<svg viewBox="0 0 10 10" aria-hidden="true"><path d="M1 0 L10 5 L1 10z"/></svg>'
    parts = [
        '<div class="side">',
        '<div class="mode side-whole">',
        f'<button type="button" class="btn big play-session" data-needs-script hidden>{play_svg}'
        f'<span>{_e(panel["play_session"])}</span></button>',
        f'<p class="hint" data-needs-script hidden>{_e(panel["hint"])}</p>',
        f'<p class="note keys" data-needs-script hidden>{_e(panel["keys"])}</p>',
        "</div>",
    ]
    if has_heat:
        heat = LABELS["heat"]
        stops = ", ".join(HEAT_RAMP)
        parts.append(
            '<div class="mode side-heat">'
            f'<p><b>{_e(heat["title"])}</b></p>'
            f'<div class="ramp" style="background:linear-gradient(90deg, {stops})" aria-hidden="true"></div>'
            f'<div class="ramp-ends"><span>{_e(heat["low"])}</span><span>{_e(heat["high"])}</span></div>'
            f'<p class="note">{_e(heat["note"])}</p>'
            "</div>"
        )
    parts.append('<div class="mode side-now" data-needs-script hidden></div>')
    parts.append(
        '<div class="mode side-session" data-needs-script hidden>'
        '<div><p class="now-t"></p><p class="now-where"></p></div>'
        f'<p class="now-last" data-last="{_e(panel["last"])}"></p>'
        "</div>"
    )
    parts.append("</div>")
    return parts


def _event_icon(kind):
    name = kind if kind in EVENT_KINDS else "other"
    return f'<svg aria-hidden="true" focusable="false"><use href="#ev-{name}"/></svg>'


# The moment the overview's clip shows, paused on its frame: the first
# problem's first moment, else the rank 1 moment; one with a clip.
def _first_moment(data, kept):
    problems = (data.get("summary") or {}).get("problems") or []
    by_id = {f["id"]: f for f in kept}
    order = [by_id[m] for p in problems for m in p["moments"] if m in by_id]
    order.extend(kept)
    return next((f for f in order if f.get("clip") is not None), None)


# The foot row under the floors and the side column: the stage's clip on
# the left (the first problem's frame in the overview, the current
# moment's clip once one is picked, black while the session travels);
# the legend or the game events on the right, and the transport row.
def _render_foot(data, kept, has_markers, has_drop_pins):
    words = LABELS["timeline"]
    panel = LABELS["panel"]
    map_words = LABELS["map"]
    card_words = LABELS["card"]
    play_svg = '<svg viewBox="0 0 10 10" aria-hidden="true"><path d="M1 0 L10 5 L1 10z"/></svg>'
    first = _first_moment(data, kept)
    first_attr = f' data-first="m{first["rank"]}"' if first is not None else ""
    kinds = "".join(
        f'<li><span class="k k-{_kind(kind)["class"]}" aria-hidden="true"></span>'
        f'{_e(_kind(kind)["label"])}</li>'
        for kind in KIND_ORDER
    )
    legend = [f'<li>{_e(map_words["route"])}</li>']
    if has_drop_pins:
        legend.append(f'<li>{_e(map_words["dropped"])}</li>')
    if has_markers:
        legend.append(f'<li>{_e(map_words["f9"])}</li>')
    events = "".join(
        f'<li data-t="{event["t"]}" hidden>{_event_icon(event.get("kind"))}<time>{_mss(event["t"])}</time>'
        f'<span>{_e(event["label"])}</span></li>'
        for event in data.get("events") or []
    )
    options = [f'<option value="0">{_e(words["trail_all"])}</option>'] + [
        f'<option value="{n}"{" selected" if n == words["trail_default"] else ""}>'
        f'{_e(words["trail_last"].format(n=n))}</option>'
        for n in words["windows"]
    ]
    return [
        '<div class="foot">',
        f'<figure class="stage-clip"{first_attr} data-needs-script hidden><video preload="metadata"></video>'
        f'<figcaption><span class="cap"></span><span class="sync">{_e(card_words["sync"])}</span></figcaption></figure>',
        '<div class="rest">',
        '<div class="mode foot-whole">',
        f'<ul class="legend">{kinds}</ul>',
        f'<ul class="legend">{"".join(legend)}</ul>',
        "</div>",
        '<div class="mode foot-now" data-needs-script hidden>',
        f'<div class="evrow" data-near="{_e(words["events_near"])}" '
        f'data-so-far="{_e(panel["events_so_far"])}" data-none="{_e(words["events_none"])}" '
        f'data-none-yet="{_e(panel["events_none_yet"])}">'
        '<span class="evh"></span>'
        f'<ol class="events">{events}</ol>'
        '<span class="none note" hidden></span>'
        "</div>",
        "</div>",
        "</div>",
        '<div class="nav" data-needs-script hidden>'
        f'<button type="button" class="btn play" aria-pressed="false" '
        f'data-play="{_e(words["play"])}" data-pause="{_e(words["pause"])}">{play_svg}'
        f'<span>{_e(words["play"])}</span></button>'
        f'<button type="button" class="btn prev">{_e(panel["previous"])}</button>'
        f'<button type="button" class="btn next">{_e(panel["next"])}</button>'
        f'<button type="button" class="btn overview">{_e(panel["overview"])}</button>'
        f'<label class="trail">{_e(words["trail"])} <select>{"".join(options)}</select></label>'
        f'<span class="count" data-count="{_e(panel["count"])}" data-count-dropped="{_e(panel["count_dropped"])}"></span>'
        "</div>",
        "</div>",
    ]


def _render_pane(data, floors, kept, dropped, markers, id_to_rank):
    route = data["route"]
    duration = data["session"]["duration_s"]
    has_heat = bool(route["heat"])
    runs = _route_runs(route["points"])
    top = max((spot["seconds"] for spot in route["heat"]), default=0) or 1
    parts = [
        f'<aside class="pane" data-mode="whole" data-duration="{duration}" aria-labelledby="where">',
        f'<h2 id="where" class="vh">{LABELS["sections"]["where"]}</h2>',
    ]
    parts.extend(_render_toolbar(duration, has_heat, any(_is_soft(f) for f in kept)))
    parts.append('<div class="stagebody"><div class="floors">')
    for index, (meta, data_uri) in enumerate(floors):
        parts.extend(
            _render_floor(data, index, meta, data_uri, runs, len(floors), kept, dropped, markers, id_to_rank, top)
        )
    parts.append("</div>")
    parts.extend(_render_side(has_heat))
    parts.append("</div>")
    has_drop_pins = any(f.get("at") is not None for f in dropped)
    parts.extend(_render_foot(data, kept, bool(markers), has_drop_pins))
    parts.append("</aside>")
    return parts


def _render_intent(friction):
    if friction is None:
        return ""
    rule = LABELS["friction"].get(friction)
    if rule is None:
        return f'<span class="intent">{_e(friction)}</span>'
    css = "intent unplanned" if rule["unplanned"] else "intent"
    return f'<span class="{css}">{_e(rule["tag"])}</span>'


def _render_status(check):
    resolved = check.get("resolved")
    if resolved is None or resolved == "unknown":
        return ""
    if resolved == "solved":
        after = check.get("resolved_after_s")
        if after is not None:
            text = LABELS["resolved"]["after"].format(time=_mss(after))
        else:
            text = LABELS["resolved"]["solved"]
        return f'<span class="status done">{_e(text)}</span>'
    if resolved == "abandoned":
        return f'<span class="status open">{_e(LABELS["abandoned"])}</span>'
    return f'<span class="status">{_e(resolved)}</span>'


def _render_friction_line(check):
    bits = []
    meter = _render_meter(check.get("friction"))
    if meter:
        bits.append(meter)
    status = _render_status(check)
    if status:
        bits.append(status)
    if not bits:
        return ""
    return f'<p class="fric">{" ".join(bits)}</p>'


# The times and words the script reads off a card or a dropped row: its
# visit or attempt span and its clip span (the map lights the route
# inside either), its floor, and what the moment box prints.
def _data_attrs(finding, label, place, floor_count, has_map):
    beat = finding.get("beat") or {}
    end = _moment_end(finding)
    visit = (
        _first_set(beat.get("attempt_start_s"), finding["time_s"]),
        _first_set(beat.get("attempt_end_s"), end),
    )
    attrs = [
        f'data-t="{finding["time_s"]}"',
        f'data-visit="{visit[0]} {visit[1]}"',
        f'data-kind="{_kind(finding["kind"])["class"]}"',
        f'data-label="{_e(label)}"',
    ]
    if finding.get("rank") is not None:
        attrs.append(f'data-rank="{finding["rank"]}"')
    clip = finding.get("clip")
    if clip is not None:
        attrs.append(f'data-clip="{clip["start_s"]} {clip["end_s"]}"')
    at = finding.get("at")
    if has_map and at is not None:
        attrs.append(f'data-floor="{at["floor"]}"')
        if floor_count > 1:
            floor = _floor_name(at["floor"])
            place = f"{place}, {floor}" if place else floor
    if place:
        attrs.append(f'data-place="{_e(place)}"')
    return " ".join(attrs)


def _render_clip(clip):
    words = LABELS["card"]
    caption = words["clip"].format(span=_span(clip["start_s"], clip["end_s"]))
    return (
        f'<figure class="clip"><video controls preload="metadata" src="{_e(clip["path"])}" '
        f'aria-label="{_e(caption)}"></video>'
        f'<figcaption><span>{_e(caption)}</span><span class="sync">{_e(words["sync"])}</span></figcaption></figure>'
    )


def _render_card(finding, markers_by_moment, floor_count, has_map):
    info = _kind(finding["kind"])
    rank = finding["rank"]
    check = finding["check"]
    at = finding.get("at")
    attrs = _data_attrs(finding, _pin_words(finding), _pin_title(finding), floor_count, has_map)
    css = f'card {info["class"]}' + (" soft" if _is_soft(finding) else "")
    parts = [f'<article class="{css}" id="m{rank}" {attrs}>']

    head = []
    number = _shape(finding["kind"], f"<b>{rank}</b>")
    if has_map and at is not None:
        label = LABELS["card"]["num_pin"].format(rank=rank)
        head.append(
            f'<a class="mk num-pin k-{info["class"]}" href="#pin-m{rank}" aria-label="{_e(label)}">{number}</a>'
        )
    else:
        head.append(f'<span class="mk num-pin k-{info["class"]}">{number}</span>')
    end_s = finding.get("end_s")
    if end_s is not None:
        head.append(
            f'<span class="time">{_span(finding["time_s"], end_s)} '
            f'<small>({_duration(end_s - finding["time_s"])})</small></span>'
        )
    else:
        head.append(f'<span class="time">{_mss(finding["time_s"])}</span>')
    head.append(
        f'<span class="badge"><span class="k k-{info["class"]}" '
        f'aria-hidden="true"></span>{_e(info["label"])}</span>'
    )
    intent = _render_intent(check.get("friction"))
    if intent:
        head.append(intent)
    if has_map and at is not None and at["floor"] > 0:
        head.append(f'<span class="floortag">{_e(_floor_name(at["floor"]))}</span>')
    parts.append(f'<div class="card-head">{"".join(head)}</div>')

    main = [f'<p class="summary">{_e(finding["summary"])}</p>']
    quote = finding.get("quote")
    if quote is None:
        main.append(f'<p class="quote none">{_e(LABELS["card"]["no_quote"])}</p>')
    else:
        main.append(f'<p class="quote">"{_e(quote)}"</p>')
    parts.append(f'<div class="card-main">{"".join(main)}</div>')

    clip = finding.get("clip")
    if clip is not None:
        parts.append(_render_clip(clip))

    facts = []
    if check.get("cause"):
        facts.append(f'<dt>{LABELS["card"]["cause"]}</dt><dd>{_breakable(check["cause"])}</dd>')
    if finding.get("game_state") is not None:
        facts.append(f'<dt>{LABELS["card"]["game"]}</dt><dd>{_breakable(finding["game_state"])}</dd>')
    facts.append(f'<dt>{LABELS["card"]["checker"]}</dt><dd>{_breakable(check["note"])}</dd>')
    bottom = [f'<dl class="facts">{"".join(facts)}</dl>']
    fric = _render_friction_line(check)
    if fric:
        bottom.append(fric)
    for marker in markers_by_moment.get(finding["id"], []):
        line = LABELS["card"]["f9"].format(time=_mss(marker["t"]))
        bottom.append(f'<p class="f9line"><b>F9</b>{_e(line)}</p>')
    parts.append(f'<div class="card-facts">{"".join(bottom)}</div>')
    parts.append("</article>")
    return "\n".join(parts)


# A puzzle beat groups by area and puzzle, its attempts inside. A beat
# with no puzzle is an area visit: one group per visit, no attempts.
def _beat_key(finding):
    beat = finding.get("beat")
    if not beat:
        return None
    if beat.get("puzzle_number") is None:
        return ("visit", beat.get("area"), beat.get("zone"), beat.get("attempt_start_s"))
    return (beat.get("area"), beat.get("puzzle"), beat.get("zone"), beat.get("puzzle_number"))


def _kept_groups(kept):
    groups = []
    by_key = {}
    for finding in kept:
        key = _beat_key(finding)
        group = by_key.get(key)
        if group is None:
            group = {"key": key, "findings": [], "attempts": {}}
            by_key[key] = group
            groups.append(group)
        group["findings"].append(finding)
        beat = finding.get("beat") or {}
        attempt_key = (
            beat.get("attempt"),
            beat.get("attempt_start_s"),
            beat.get("attempt_end_s"),
        )
        group["attempts"].setdefault(attempt_key, []).append(finding)
    return groups


# "Puzzle n: name" only for a beat that has both. An area visit shows
# the area alone.
def _group_title(beat):
    if not beat:
        return LABELS["moments"]["fallback"]
    area = beat.get("area") or beat.get("zone")
    puzzle = beat.get("puzzle")
    number = beat.get("puzzle_number")
    parts = []
    if area:
        parts.append(area)
    if puzzle and number is not None:
        parts.append(LABELS["moments"]["puzzle"].format(n=number, name=puzzle))
    return ", ".join(parts) or LABELS["moments"]["fallback"]


def _attempt_sort_key(attempt_key):
    attempt, start_s, _end_s = attempt_key
    return (
        float("inf") if attempt is None else attempt,
        float("inf") if start_s is None else start_s,
    )


# The first value that is not None: a stored time of 0 is a real time.
def _first_set(*values):
    return next(value for value in values if value is not None)


def _moment_end(finding):
    return _first_set(finding.get("end_s"), finding["time_s"])


def _group_span(findings):
    start = min(
        _first_set((f.get("beat") or {}).get("attempt_start_s"), f["time_s"])
        for f in findings
    )
    end = max(
        _first_set((f.get("beat") or {}).get("attempt_end_s"), _moment_end(f))
        for f in findings
    )
    return start, end


def _render_groups(kept, markers_by_moment, floor_count, has_map):
    groups = _kept_groups(kept)
    # Sections run in time order: by the earliest start, ties to the lower rank.
    groups.sort(
        key=lambda g: (_group_span(g["findings"])[0], min(f["rank"] for f in g["findings"]))
    )
    out = []
    for index, group in enumerate(groups, start=1):
        beat = group["findings"][0].get("beat") or {}
        attempt_keys = sorted(group["attempts"], key=_attempt_sort_key)
        start, end = _group_span(group["findings"])
        if any(key[0] is not None for key in attempt_keys):
            note = LABELS["moments"]["attempt_note"].format(
                attempts=_plural(len(attempt_keys), "attempt"),
                moments=_plural(len(group["findings"]), "moment"),
                span=_span(start, end),
            )
        else:
            note = LABELS["moments"]["note"].format(
                moments=_plural(len(group["findings"]), "moment"),
                span=_span(start, end),
            )
        out.append(f'<section class="moments-group" aria-labelledby="g{index}">')
        out.append(
            f'<h3 id="g{index}">{_e(_group_title(beat))}<span class="note">{_e(note)}</span></h3>'
        )
        for attempt_key in attempt_keys:
            findings = sorted(group["attempts"][attempt_key], key=lambda f: (f["time_s"], f["rank"]))
            attempt = attempt_key[0]
            if attempt is not None:
                attempt_start = _first_set(attempt_key[1], min(f["time_s"] for f in findings))
                attempt_end = _first_set(attempt_key[2], max(_moment_end(f) for f in findings))
                heading = LABELS["moments"]["attempt"].format(
                    n=attempt, span=_span(attempt_start, attempt_end)
                )
                out.append(f"<h4>{_e(heading)}</h4>")
            out.extend(
                _render_card(finding, markers_by_moment, floor_count, has_map)
                for finding in findings
            )
        out.append("</section>")
    return out


def _render_dropped(dropped, floor_count, has_map):
    items = []
    for finding in dropped:
        info = _kind(finding["kind"])
        label = _drop_words(finding)
        attrs = _data_attrs(finding, label, "", floor_count, has_map)
        shape = _shape(finding["kind"])
        if has_map and finding.get("at") is not None:
            number = (
                f'<a class="mk num-pin hollow k-{info["class"]}" href="#pin-d-{_e(finding["id"])}" '
                f'aria-label="{_e(label)}">{shape}</a>'
            )
        else:
            number = f'<span class="mk num-pin hollow k-{info["class"]}">{shape}</span>'
        reason = finding["check"].get("note")
        reason_html = ""
        if reason:
            reason_html = f'<p class="reason">{_e(LABELS["dropped"]["reason"].format(note=reason))}</p>'
        items.append(
            f'<article class="drop" id="d-{_e(finding["id"])}" {attrs}>'
            f'<div class="card-head">{number}<span class="time">{_mss(finding["time_s"])}</span>'
            f'<span class="badge k-{info["class"]}">'
            f'<span class="k k-{info["class"]}" aria-hidden="true"></span>{_e(info["label"])}</span>'
            f'<span class="intent dropped">{_e(LABELS["panel"]["dropped_tag"])}</span></div>'
            f'<div class="card-main"><p class="summary">{_e(finding["summary"])}</p>{reason_html}</div>'
            "</article>"
        )
    note = LABELS["dropped"]["note"].format(n=len(dropped))
    return [
        '<section class="dropped" aria-labelledby="dropped">',
        f'<h2 id="dropped">{LABELS["sections"]["dropped"]}</h2>',
        f'<p class="sub">{_e(note)}</p>',
        *items,
        "</section>",
    ]


# One state drives the stage: the current moment and the map time. The
# script reads every time, floor and word from the page and the data-
# attributes the renderer wrote, fills the side column with clones of
# the current card's own nodes, and computes no finding, time, position
# or count: it only compares the file's times with the map time.
SCRIPT = r"""
(function () {
  "use strict";
  var pane = document.querySelector(".pane");
  if (!pane) return;
  var page = document.querySelector(".page");
  document.documentElement.classList.add("js");
  var SPEED = 10;
  var NS = "http://www.w3.org/2000/svg";
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)");
  var DUR = Number(pane.getAttribute("data-duration"));
  function each(list, fn) { Array.prototype.forEach.call(list, fn); }
  function nums(el, name) { var v = el.getAttribute(name); return v ? v.split(" ").map(Number) : null; }
  function mss(s) { s = Math.max(0, Math.floor(s)); return Math.floor(s / 60) + ":" + ("0" + (s % 60)).slice(-2); }
  function svg(tag, attrs) { var n = document.createElementNS(NS, tag); for (var k in attrs) n.setAttribute(k, attrs[k]); return n; }
  function fill(text, vars) { return text.replace(/\{(\w+)\}/g, function (m, k) { return k in vars ? vars[k] : m; }); }

  // Floors and the route, read back from the drawn polylines.
  var FLOORS = [];
  each(pane.querySelectorAll(".floor"), function (fig) {
    var label = fig.querySelector(".floor-label");
    FLOORS[Number(fig.getAttribute("data-floor"))] = { fig: fig, strong: fig.querySelector(".strong"), dot: fig.querySelector(".dot"), name: label ? label.textContent : "",
      w: fig.querySelector("svg.map").viewBox.baseVal.width };
  });
  var RUNS = [], POINTS = [];
  each(pane.querySelectorAll(".route polyline.line"), function (line) {
    var floor = Number(line.closest(".floor").getAttribute("data-floor"));
    var run = { floor: floor, t: nums(line, "data-t"), xy: line.getAttribute("points").split(" ").map(function (p) { return p.split(",").map(Number); }) };
    RUNS.push(run);
    run.t.forEach(function (t, i) { POINTS.push({ t: t, xy: run.xy[i], floor: floor }); });
  });
  POINTS.sort(function (a, b) { return a.t - b.t; });
  // The last route point at or before t: the dot never sits between points.
  function pointAt(t) {
    var lo = 0, hi = POINTS.length - 1;
    if (!POINTS.length || t < POINTS[0].t) return null;
    while (lo < hi) { var mid = (lo + hi + 1) >> 1; if (POINTS[mid].t <= t) lo = mid; else hi = mid - 1; }
    return POINTS[lo];
  }

  var tracks = document.querySelector(".timeline .tracks");
  // Kept cards and dropped rows, in page order; KEPT in time order.
  var RECS = [], BY_ID = {};
  each(document.querySelectorAll(".card[data-t], .drop[data-t]"), function (el) {
    var clip = nums(el, "data-clip"), video = el.querySelector("video");
    var r = {
      el: el, id: el.id, t: Number(el.getAttribute("data-t")), kept: el.classList.contains("card"), soft: el.classList.contains("soft"),
      floor: el.hasAttribute("data-floor") ? Number(el.getAttribute("data-floor")) : null,
      spans: [nums(el, "data-visit"), clip].filter(Boolean), clip: clip,
      clipSrc: video ? video.getAttribute("src") : null, video: video,
      pin: document.getElementById("pin-" + el.id),
      mark: tracks ? tracks.querySelector('a[href="#' + el.id + '"]') : null
    };
    RECS.push(r);
    BY_ID[el.id] = r;
  });
  var KEPT = RECS.filter(function (r) { return r.kept; }).sort(function (a, b) { return a.t - b.t; });
  var DROPS = RECS.filter(function (r) { return !r.kept; });
  function shown() { return page.getAttribute("data-focus") === "unplanned" ? KEPT.filter(function (r) { return !r.soft; }) : KEPT; }
  function visible(r) { return r.kept && !(r.soft && page.getAttribute("data-focus") === "unplanned"); }

  var readout = pane.querySelector(".readout");
  var heatInput = pane.querySelector(".view-heat");
  var stage = pane.querySelector(".stage-clip"), sv = stage.querySelector("video"), cap = stage.querySelector(".cap");
  var sideNow = pane.querySelector(".side-now");
  var nowT = pane.querySelector(".now-t"), nowWhere = pane.querySelector(".now-where"), nowLast = pane.querySelector(".now-last");
  var evrow = pane.querySelector(".evrow"), evh = evrow.querySelector(".evh"), evItems = evrow.querySelectorAll(".events li"), evNone = evrow.querySelector(".none");
  var nav = pane.querySelector(".nav"), playBtn = nav.querySelector(".play"), prevBtn = nav.querySelector(".prev"), nextBtn = nav.querySelector(".next");
  var trailSel = nav.querySelector(".trail select"), count = nav.querySelector(".count");
  var bigPlay = pane.querySelector(".play-session");
  // The overview's clip: the first problem's moment, paused on its frame.
  var FIRST = BY_ID[stage.getAttribute("data-first")] || null;
  var roomBars = tracks ? tracks.querySelectorAll(".r-rooms .bar") : [];
  var past = tracks ? tracks.querySelector(".past") : null;
  var bands = tracks ? tracks.querySelectorAll(".band") : [];
  var cursor = tracks ? tracks.querySelector(".cursor") : null;

  // mode: whole (the overview), moment (S.cur is current), session (the map time S.t moves).
  // S.clip is the record whose clip plays, in S.clipEl; S.resume says the session goes on after it.
  var S = { mode: "whole", cur: null, t: DUR, trail: Number(trailSel.value), playing: false, clip: null, clipEl: null, clipT: null,
    resume: false, stopIdx: 0, stageFor: null, stageKey: "", sideFor: null, hold: 0 };
  function heatOn() { return !!(heatInput && heatInput.checked); }
  function inSpans(spans, t) { for (var i = 0; i < spans.length; i++) if (t >= spans[i][0] && t <= spans[i][1]) return true; return false; }
  function lastPassed(t) { var best = null; shown().forEach(function (r) { if (r.t <= t) best = r; }); return best; }
  function startOf(r) { return r.clip ? r.clip[0] : r.t; }
  function roomAt(t) {
    for (var i = 0; i < roomBars.length; i++) {
      var b = roomBars[i];
      if (t >= Number(b.getAttribute("data-s")) && t <= Number(b.getAttribute("data-e"))) return b.getAttribute("data-room");
    }
    return "";
  }

  // Draw the route points that pass the test, per run, strong or faint.
  function drawRoute(test, faint, every) {
    var first = null, last = null;
    RUNS.forEach(function (run) {
      var g = FLOORS[run.floor].strong, cur = [];
      function flush() {
        if (cur.length > 1) {
          var pts = cur.map(function (i) { return run.xy[i].join(","); }).join(" ");
          if (faint) { g.appendChild(svg("polyline", { "class": "faint", points: pts })); }
          else {
            g.appendChild(svg("polyline", { "class": "case", points: pts }));
            g.appendChild(svg("polyline", { "class": "line", points: pts }));
            for (var k = 2; k < cur.length - 1; k += every) {
              var a = run.xy[cur[k - 1]], b = run.xy[cur[k + 1]], p = run.xy[cur[k]];
              var dx = b[0] - a[0], dy = b[1] - a[1];
              if (dx * dx + dy * dy < 400) continue;
              g.appendChild(svg("path", { "class": "arrow", d: "M20 0 L-20 16 L-10 0 L-20 -16z",
                transform: "translate(" + p[0] + " " + p[1] + ") rotate(" + (Math.atan2(dy, dx) * 180 / Math.PI).toFixed(0) + ")" }));
            }
          }
        }
        cur = [];
      }
      run.t.forEach(function (t, i) {
        if (!test(t)) { flush(); return; }
        cur.push(i);
        if (!faint) {
          if (!first || t < first.t) first = { t: t, xy: run.xy[i], floor: run.floor };
          if (!last || t > last.t) last = { t: t, xy: run.xy[i], floor: run.floor };
        }
      });
      flush();
    });
    if (first && first !== last) FLOORS[first.floor].strong.appendChild(svg("circle", { "class": "start", cx: first.xy[0], cy: first.xy[1], r: 18 }));
    if (last && first !== last) FLOORS[last.floor].strong.appendChild(svg("circle", { "class": "end", cx: last.xy[0], cy: last.xy[1], r: 18 }));
  }

  // The map time: the clip's time while one plays, else the moment's, else the session's.
  function mapTime() {
    if (S.mode === "moment") return S.clipT != null ? S.clipT : S.cur.t;
    if (S.mode === "session") return S.t;
    return DUR;
  }
  // A game event is fresh for 1.5 s on screen: 15 s of map time at 10x, 3 s inside a clip.
  function freshWindow() { return S.clip ? 3 : 1.5 * SPEED; }

  function render() {
    var heat = heatOn();
    pane.setAttribute("data-mode", heat ? "heat" : S.mode);
    FLOORS.forEach(function (F) { F.strong.replaceChildren(); });
    var active = null, lit = null, dotT = null, lo = -Infinity;
    if (!heat && S.mode === "moment") {
      var r = S.cur;
      drawRoute(function (t) { return inSpans(r.spans, t); }, false, 4);
      active = r; lit = r.floor; dotT = mapTime();
    } else if (!heat && S.mode === "session") {
      if (S.trail > 0) { lo = S.t - S.trail; drawRoute(function (t) { return t <= lo; }, true, 0); }
      drawRoute(function (t) { return t > lo && t <= S.t; }, false, S.trail > 0 ? 3 : 8);
      active = lastPassed(S.t); dotT = S.t;
    }
    RECS.forEach(function (r) {
      if (!r.pin) return;
      r.pin.classList.toggle("is-focus", r === active && S.mode === "moment");
      r.pin.classList.toggle("is-quiet", S.mode === "moment" && r !== active);
      r.pin.classList.toggle("is-later", S.mode === "session" && r.t > S.t);
      if (r === active && r.pin !== r.pin.parentNode.lastElementChild) r.pin.parentNode.appendChild(r.pin);
    });
    var p = dotT == null ? null : pointAt(dotT), tag = freshEvent(dotT);
    FLOORS.forEach(function (F, fl) {
      var show = !!p && p.floor === fl, text = F.dot.querySelector(".tag");
      F.dot.setAttribute("visibility", show ? "visible" : "hidden");
      if (show) F.dot.setAttribute("transform", "translate(" + p.xy[0] + " " + p.xy[1] + ")");
      // The tag reads to the right of the dot, or to the left on the right half of the floor.
      var flip = show && p.xy[0] > F.w / 2;
      F.dot.classList.toggle("flip", flip);
      text.setAttribute("x", flip ? -34 : 34);
      text.textContent = show && tag ? tag : "";
    });
    if (p) lit = p.floor;
    FLOORS.forEach(function (F, fl) {
      F.fig.classList.toggle("lit", lit === fl && FLOORS.length > 1);
      F.fig.classList.toggle("quiet", lit != null && lit !== fl);
    });
    RECS.forEach(function (r) {
      r.el.classList.toggle("is-active", r === active && S.mode === "moment" && !heat);
      r.el.classList.toggle("is-playing", r === S.clip && S.clipEl === r.video);
      if (r.mark) r.mark.classList.toggle("is-active", r === active && !heat);
    });
    pane.classList.toggle("is-stage-playing", !!S.clip && S.clipEl === sv);
    renderPlayBtn();
    renderTime(heat, lo);
    renderPanel(heat, active, p);
  }

  // The latest game event inside the fresh window before t, for the dot's tag.
  function freshEvent(t) {
    if (t == null || S.mode === "whole") return "";
    if (S.mode === "session" && !S.playing) return "";
    if (S.mode === "moment" && !S.clip) return "";
    var best = null;
    each(evItems, function (li) {
      var et = Number(li.getAttribute("data-t"));
      if (et <= t && t - et < freshWindow() && (!best || et >= Number(best.getAttribute("data-t")))) best = li;
    });
    return best ? best.querySelector("span").textContent : "";
  }

  function place(el, a, b) { el.style.left = (a / DUR * 100) + "%"; if (b != null) el.style.width = Math.max(0, (b - a) / DUR * 100) + "%"; }
  function renderTime(heat, lo) {
    var t = heat ? DUR : mapTime(), spans = [];
    if (!heat && S.mode === "session") spans = [[Math.max(0, lo), S.t]];
    else if (!heat && S.mode === "moment") spans = S.cur.spans;
    var text = (!heat && S.mode === "session" && S.trail > 0 ? readout.getAttribute("data-readout-window") : readout.getAttribute("data-readout"))
      .replace("{start}", mss(Math.max(0, lo))).replace("{time}", mss(t)).replace("{duration}", mss(DUR));
    readout.textContent = text;
    each(bands, function (band, i) { band.hidden = !spans[i]; if (spans[i]) place(band, spans[i][0], spans[i][1]); });
    if (cursor) { cursor.hidden = heat || S.mode === "whole"; place(cursor, t); }
    if (past) { past.hidden = heat || S.mode === "whole"; place(past, 0, t); }
  }

  // The stage's clip shows one record's clip, paused on the moment's own
  // frame until something plays it, or nothing (black, no controls) when
  // r is null: the clip never points at a time the map does not.
  function loadStage(r) {
    // The overview captions the clip with its moment; a moment captions it with the clip's span.
    var key = (S.mode === "whole" ? "whole " : "moment ") + (r ? r.id : "");
    if (S.stageKey === key) return;
    S.stageKey = key; S.stageFor = r;
    if (r && r.clipSrc) {
      var cardCap = r.el.querySelector(".clip figcaption span");
      if (S.mode === "whole") {
        var a = document.createElement("a"); a.href = "#" + r.id; a.textContent = r.el.getAttribute("data-label");
        cap.replaceChildren(a);
      } else cap.textContent = cardCap ? cardCap.textContent : "";
      sv.setAttribute("controls", "");
      if (sv.getAttribute("src") !== r.clipSrc) { sv.setAttribute("src", r.clipSrc); S.seek = r.t - r.clip[0]; }
      else if (S.clipT == null) sv.currentTime = r.t - r.clip[0];
    } else {
      cap.textContent = "";
      sv.removeAttribute("controls");
      if (sv.hasAttribute("src")) { sv.removeAttribute("src"); sv.load(); }
    }
  }

  // The panel: the current moment's own words (clones of its card), or the
  // player's time and room; the game events row; the transport row.
  function renderPanel(heat, active, p) {
    var list = shown(), r = S.cur;
    nav.querySelector(".overview").disabled = S.mode === "whole";
    if (heat || S.mode === "whole") {
      loadStage(heat ? null : FIRST);
      count.textContent = "";
      prevBtn.disabled = true; nextBtn.disabled = !list.length || heat;
      nav.classList.remove("in-session");
      return;
    }
    if (S.mode === "moment") {
      if (S.sideFor !== r) {
        S.sideFor = r;
        var head = r.el.querySelector(".card-head"), nodes = [];
        var h = document.createElement("p"); h.className = "head";
        each(head.children, function (c) { if (!c.classList.contains("floortag")) h.appendChild(c.cloneNode(true)); });
        var where = document.createElement("span"); where.className = "where"; where.textContent = r.el.getAttribute("data-place") || ""; h.appendChild(where);
        nodes.push(h);
        each(r.el.querySelectorAll(".card-main, .card-facts"), function (block) { each(block.children, function (c) { nodes.push(c.cloneNode(true)); }); });
        sideNow.replaceChildren.apply(sideNow, nodes);
      }
      loadStage(r);
      var i = list.indexOf(r);
      if (i >= 0) count.textContent = fill(count.getAttribute("data-count"), { n: i + 1, of: list.length });
      else count.textContent = r.kept ? "" : fill(count.getAttribute("data-count-dropped"), { n: DROPS.indexOf(r) + 1, of: DROPS.length });
      prevBtn.disabled = i <= 0 && !(i < 0 && list.length);
      nextBtn.disabled = i >= list.length - 1 && !(i < 0 && list.length);
    } else {
      loadStage(null);
      nowT.textContent = mss(S.t);
      var bits = [roomAt(S.t)]; if (p && FLOORS[p.floor].name) bits.push(FLOORS[p.floor].name);
      nowWhere.textContent = bits.filter(Boolean).join(", ");
      nowLast.replaceChildren();
      if (active) {
        var a = document.createElement("a"); a.href = "#" + active.id; a.textContent = active.el.getAttribute("data-label");
        nowLast.append(fill(nowLast.getAttribute("data-last"), { label: "" }));
        nowLast.appendChild(a);
      }
      count.textContent = "";
      prevBtn.disabled = !list.length; nextBtn.disabled = !list.length;
    }
    // The events row: in a moment, the events of its visit and clip; in the session, the last ones passed.
    evh.textContent = evrow.getAttribute(S.mode === "session" ? "data-so-far" : "data-near");
    var on = [];
    each(evItems, function (li) {
      var t = Number(li.getAttribute("data-t"));
      var keep = S.mode === "session" ? t <= S.t : inSpans(S.cur.spans, t);
      li.hidden = !keep;
      if (keep) on.push(li);
      li.classList.toggle("later", keep && S.mode === "moment" && S.clipT != null && t > S.clipT);
      li.classList.toggle("fresh", keep && S.mode === "session" && S.playing && S.t - t < freshWindow());
    });
    if (S.mode === "session") on.slice(0, Math.max(0, on.length - 6)).forEach(function (li) { li.hidden = true; });
    evNone.textContent = evrow.getAttribute(S.mode === "session" ? "data-none-yet" : "data-none");
    evNone.hidden = on.length > 0;
    nav.classList.toggle("in-session", S.mode === "session");
  }

  // ---- Interactions ----
  function setPlaying(on) { S.playing = on; renderPlayBtn(); }
  // The button reads Pause while the session runs or the stage's clip plays.
  function renderPlayBtn() {
    var on = S.playing || (!!S.clip && S.clipEl === sv);
    playBtn.querySelector("span").textContent = playBtn.getAttribute(on ? "data-pause" : "data-play");
    playBtn.querySelector("path").setAttribute("d", on ? "M1 0 H4 V10 H1z M6 0 H9 V10 H6z" : "M1 0 L10 5 L1 10z");
    playBtn.setAttribute("aria-pressed", on ? "true" : "false");
  }
  function pauseClips(except) {
    RECS.forEach(function (r) { if (r.video && r.video !== except && !r.video.paused) r.video.pause(); });
    if (sv !== except && !sv.paused) sv.pause();
  }
  function showTrail() { if (heatOn()) pane.querySelector("input[name=view][value=trail]").checked = true; }
  function stopAll(keepView) { pauseClips(null); setPlaying(false); if (!keepView) showTrail(); S.clip = null; S.clipEl = null; S.clipT = null; S.resume = false; }
  function setCur(r) {
    if (S.mode === "moment" && S.cur === r) return;
    S.mode = "moment"; S.cur = r; S.clipT = null;
    render();
  }
  // From a pin, a mark, a problem, a card number, Previous or Next: light it and bring its card to the middle.
  function goTo(r, scroll) {
    // A link to a moment that "Unplanned only" hides shows every moment again.
    if (r.kept && !visible(r)) {
      page.setAttribute("data-focus", "all");
      var all = pane.querySelector("input[name=focus][value=all]");
      if (all) all.checked = true;
    }
    stopAll();
    S.mode = "moment"; S.cur = r; S.clipT = null;
    render();
    if (history.replaceState) history.replaceState(null, "", "#" + r.id);
    if (scroll) scrollTo(r);
  }
  // A scroll the page starts (a jump to a card, the overview's return to
  // the top) must not move "now": the scroll sync waits until that scroll
  // has ended (scrollend, or no scroll event for 250 ms, or 3 s at most).
  var own = 0, ownTimer = 0;
  function ownScroll() {
    own = performance.now() + 3000;
    clearTimeout(ownTimer);
    ownTimer = setTimeout(releaseScroll, 250);
  }
  function releaseScroll() { own = 0; clearTimeout(ownTimer); onScroll(); }
  var behavior = reduce.matches ? "auto" : "smooth";
  // The list follows the current moment while the stage stays on screen
  // (the wide layout); in the stacked layout the stage comes into view instead.
  function sticky() { return getComputedStyle(pane).position === "sticky"; }
  function scrollTo(r) {
    var target = sticky() ? r.el : pane, box = target.getBoundingClientRect();
    if (target === pane && box.top >= 0 && box.bottom <= window.innerHeight) return;
    ownScroll();
    target.scrollIntoView({ block: sticky() ? "center" : "start", behavior: behavior });
  }
  function toSession(t) {
    pauseClips(null); showTrail();
    S.mode = "session"; S.cur = null; S.clip = null; S.clipEl = null; S.clipT = null; S.resume = false;
    S.t = Math.max(0, Math.min(DUR, t)); S.hold = performance.now() + 1500;
    render();
  }
  // Back to the start: the whole route, and (from Overview or Escape) the page's top with the problems.
  function toOverview(top) {
    stopAll();
    S.mode = "whole"; S.cur = null; S.t = DUR;
    render();
    if (history.replaceState) history.replaceState(null, "", location.pathname + location.search);
    if (top && window.scrollY > 0) { ownScroll(); window.scrollTo({ top: 0, behavior: behavior }); }
  }
  function centered() {
    var mid = window.innerHeight / 2, last = null;
    for (var i = 0; i < RECS.length; i++) {
      var b = RECS[i].el.getBoundingClientRect();
      if (b.height === 0) continue;
      if (b.top > mid) break;
      last = RECS[i];
      if (b.bottom >= mid) return last;
    }
    return last;
  }
  // The moment in the middle of the screen becomes current while the reader scrolls on their own.
  function onScroll() {
    var now = performance.now();
    if (heatOn() || S.clip || S.playing || own || !sticky()) return;
    if (S.mode === "session" && now < S.hold) return;
    var r = centered();
    if (r) { setCur(r); return; }
    if (S.mode === "moment") toOverview(false);
  }
  var ticking = false;
  window.addEventListener("scroll", function () {
    if (own) {
      if (performance.now() < own) { clearTimeout(ownTimer); ownTimer = setTimeout(releaseScroll, 250); return; }
      own = 0;
    }
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(function () { ticking = false; onScroll(); });
  }, { passive: true });
  window.addEventListener("scrollend", function () { if (own) releaseScroll(); });

  document.addEventListener("click", function (e) {
    var a = e.target.closest && e.target.closest("a[href^='#']");
    if (!a || e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey) return;
    var id = a.getAttribute("href").slice(1);
    if (id.indexOf("pin-") === 0) id = id.slice(4);
    var r = BY_ID[id];
    if (!r) return;
    e.preventDefault();
    goTo(r, true);
  });

  // ---- The session: 10x between moments, each shown moment's clip at normal speed ----
  var last = 0, lastPoint = null;
  function startSession(from) {
    stopAll();
    S.mode = "session"; S.cur = null;
    S.t = Math.max(0, Math.min(DUR, from));
    var list = shown(); S.stopIdx = list.length;
    for (var i = 0; i < list.length; i++) if (list[i].t > S.t) { S.stopIdx = i; break; }
    setPlaying(true);
    last = performance.now();
    requestAnimationFrame(tick);
  }
  function tick(stamp) {
    if (!S.playing) return;
    S.t = Math.min(DUR, S.t + SPEED * (stamp - last) / 1000);
    last = stamp;
    var list = shown(), stop = list[S.stopIdx];
    if (stop && S.t >= startOf(stop)) { stopAt(stop); return; }
    var p = pointAt(S.t);
    if (p !== lastPoint) { lastPoint = p; render(); } else { renderTime(false, S.trail > 0 ? S.t - S.trail : -Infinity); renderPanel(false, lastPassed(S.t), p); }
    if (S.t >= DUR) setPlaying(false); else requestAnimationFrame(tick);
  }
  // The session reaches a moment: it becomes current and its clip plays from where the map is, then the session goes on.
  function stopAt(r) {
    setPlaying(false);
    S.mode = "moment"; S.cur = r; S.clipT = null; S.resume = true;
    render();
    if (history.replaceState) history.replaceState(null, "", "#" + r.id);
    scrollTo(r);
    if (r.clip) { S.seek = Math.max(0, S.t - r.clip[0]); playStage(); }
    else { S.wait = setTimeout(function () { if (S.cur === r && S.resume) resumeAfter(r); }, 1500); }
  }
  function resumeAfter(r) {
    var list = shown(), i = list.indexOf(r);
    S.resume = false;
    startSession(r.clip ? r.clip[1] : r.t);
    S.stopIdx = i + 1;
  }
  // Plays the stage's clip from S.seek. A clip whose metadata is still
  // loading starts from the loadedmetadata handler instead; a clip the
  // browser refuses to play (autoplay rules) lets the session go on.
  function playStage() {
    if (sv.readyState < 1) return;
    if (S.seek != null) { sv.currentTime = S.seek; S.seek = null; }
    var p = sv.play();
    if (p && p.catch) p.catch(function () { if (S.resume && S.cur === S.stageFor) resumeAfter(S.cur); });
  }

  playBtn.addEventListener("click", function () {
    if (S.playing) { setPlaying(false); S.hold = performance.now() + 400; render(); return; }
    if (S.clip && S.clipEl === sv) { S.resume = false; sv.pause(); return; }
    if (S.mode === "moment" && S.cur.clip && S.stageFor === S.cur && !sv.ended) { S.resume = true; playStage(); return; }
    if (S.mode === "moment") { var r = S.cur; S.resume = false; startSession(r.clip ? r.clip[1] : r.t); S.stopIdx = shown().indexOf(r) + 1; return; }
    startSession(S.mode === "session" && S.t < DUR ? S.t : 0);
  });
  bigPlay.addEventListener("click", function () { startSession(0); });
  function step(dir) {
    var list = shown();
    if (!list.length) return;
    var i = S.cur ? list.indexOf(S.cur) : -1, next = null;
    var base = S.cur ? S.cur.t : (S.mode === "session" ? S.t : -Infinity);
    if (dir > 0) next = i >= 0 ? list[i + 1] : list.filter(function (r) { return r.t > base; })[0];
    else next = i >= 0 ? list[i - 1] : list.filter(function (r) { return r.t < base; }).pop();
    if (next) goTo(next, true);
  }
  prevBtn.addEventListener("click", function () { step(-1); });
  nextBtn.addEventListener("click", function () { step(1); });
  nav.querySelector(".overview").addEventListener("click", function () { toOverview(true); });
  trailSel.addEventListener("change", function () { S.trail = Number(trailSel.value); render(); });
  each(pane.querySelectorAll("input[name=view]"), function (el) {
    el.addEventListener("change", function () {
      stopAll(true);
      if (heatOn()) { render(); return; }
      S.mode = "whole"; S.cur = null; render(); onScroll();
    });
  });
  each(pane.querySelectorAll("input[name=focus]"), function (el) {
    el.addEventListener("change", function () {
      page.setAttribute("data-focus", el.value);
      if (S.cur && !visible(S.cur) && S.cur.kept) toOverview(false); else render();
    });
  });

  // Clicking or dragging on the timeline sets the map time.
  if (tracks) {
    var dragging = false;
    function stripTime(e) { var b = tracks.getBoundingClientRect(); return (e.clientX - b.left) / b.width * DUR; }
    tracks.addEventListener("pointerdown", function (e) {
      if (e.button !== 0 || e.target.closest("a")) return;
      dragging = true;
      setPlaying(false); toSession(stripTime(e));
      // Keeps the drag when the pointer leaves the strip; never blocks the click.
      try { tracks.setPointerCapture(e.pointerId); } catch (err) { /* no capture */ }
    });
    tracks.addEventListener("pointermove", function (e) { if (dragging) toSession(stripTime(e)); });
    tracks.addEventListener("pointerup", function () { dragging = false; });
    tracks.addEventListener("pointercancel", function () { dragging = false; });
  }

  // Space plays and pauses, left and right step between moments, Escape returns to the overview.
  document.addEventListener("keydown", function (e) {
    if (e.defaultPrevented || e.altKey || e.ctrlKey || e.metaKey || e.shiftKey) return;
    var tag = (e.target.tagName || "").toLowerCase();
    if (e.key === "Escape" && S.mode !== "whole") { e.preventDefault(); toOverview(true); return; }
    if (tag === "input" || tag === "select" || tag === "textarea" || tag === "video" || e.target.isContentEditable) return;
    if (e.key === "ArrowRight") { e.preventDefault(); step(1); }
    else if (e.key === "ArrowLeft") { e.preventDefault(); step(-1); }
    else if (e.key === " " && tag !== "button") { e.preventDefault(); playBtn.click(); }
  });
  // A mouse click on the stage's own buttons and switches gives focus back to
  // the page, so the keys above keep working; keyboard users keep their focus.
  pane.addEventListener("click", function (e) {
    if (e.detail === 0 || !e.target.closest("button, label")) return;
    setTimeout(function () {
      var f = document.activeElement;
      if (f && pane.contains(f) && f.matches("button, input[type=radio]")) f.blur();
    }, 0);
  });

  // A playing clip holds the map on its moment and moves the dot:
  // map time = clip.start_s + video.currentTime. The stage's video and
  // each card's own video drive it the same way.
  function wire(v, recOf) {
    function follow() {
      var r = recOf();
      if (!r || S.clip !== r || S.clipEl !== v) return;
      S.clipT = r.clip[0] + v.currentTime;
      var p = pointAt(S.clipT);
      if (p !== lastPoint) { lastPoint = p; render(); } else renderPanel(false, r, p);
      if (!v.paused && !v.ended) requestAnimationFrame(follow);
    }
    v.addEventListener("play", function () {
      var r = recOf();
      if (!r || !r.clip) return;
      pauseClips(v); setPlaying(false); showTrail();
      if (v !== sv) S.resume = false;
      // Play on the overview's clip makes its moment current; the list follows.
      var fromWhole = S.mode === "whole";
      S.mode = "moment"; S.cur = r; S.clip = r; S.clipEl = v; S.clipT = r.clip[0] + v.currentTime; lastPoint = null;
      if (fromWhole) { render(); if (history.replaceState) history.replaceState(null, "", "#" + r.id); scrollTo(r); }
      follow();
    });
    function stop(e) {
      var r = recOf();
      // A clip that ends fires pause first, then ended: let ended handle it.
      if (e.type === "pause" && v.ended) return;
      if (S.clip !== r || S.clipEl !== v) return;
      S.clip = null; S.clipEl = null;
      if (e.type === "ended" && v === sv && S.resume) { resumeAfter(r); return; }
      render();
    }
    v.addEventListener("pause", stop);
    v.addEventListener("ended", stop);
    v.addEventListener("seeked", function () { var r = recOf(); if (r && S.cur === r && r.clip) { S.clipT = r.clip[0] + v.currentTime; render(); } });
  }
  RECS.forEach(function (r) { if (r.video && r.clip) wire(r.video, function () { return r; }); });
  wire(sv, function () { return S.stageFor; });
  sv.addEventListener("loadedmetadata", function () {
    if (S.seek == null) return;
    sv.currentTime = S.seek; S.seek = null;
    if (S.resume && S.cur === S.stageFor) playStage();
  });

  each(document.querySelectorAll("[data-needs-script]"), function (el) { el.removeAttribute("hidden"); });
  // A link to a moment (#m7, #d-f12) opens on that moment.
  var start = BY_ID[decodeURIComponent(location.hash.slice(1))];
  if (start) {
    S.mode = "moment"; S.cur = start; ownScroll();
    // After the browser's own jump to the fragment, which it repeats until the page has loaded.
    var open = function () { ownScroll(); (sticky() ? start.el : pane).scrollIntoView({ block: sticky() ? "center" : "start", behavior: "instant" }); };
    if (document.readyState === "complete") setTimeout(open, 0); else window.addEventListener("load", function () { setTimeout(open, 0); });
  }
  render();
  if (!start) onScroll();
})();
"""


def render_html(data, maps_dir=None):
    """Return the full HTML page for a checked findings dict."""
    session = data["session"]
    kept = sorted(
        (f for f in data["findings"] if f["check"]["verdict"] == "keep"),
        key=lambda f: f["rank"],
    )
    dropped = sorted(
        (f for f in data["findings"] if f["check"]["verdict"] == "drop"),
        key=lambda f: f["time_s"],
    )
    summary = data.get("summary")
    markers = data.get("markers") or []
    id_to_rank = {finding["id"]: finding["rank"] for finding in kept}
    by_id = {finding["id"]: finding for finding in kept}
    markers_by_moment = {}
    for marker in markers:
        moment = marker.get("moment")
        if moment:
            markers_by_moment.setdefault(moment, []).append(marker)

    route = data.get("route")
    floors = None
    if route is not None:
        floors, missing = _load_floors(route["maps"], maps_dir)
        if floors is None:
            print(LABELS["warning"].format(map=repr(missing)), file=sys.stderr)
    has_map = floors is not None
    floor_count = len(floors) if has_map else 0

    title = _e(LABELS["title"].format(id=session["id"]))
    if session.get("player"):
        title += ", " + _e(session["player"])
    if has_map:
        ratios = [meta["px_width"] / meta["px_height"] for meta, _uri in floors]
        timeline, timeline_h = _render_timeline(data, kept, dropped, floor_count)
        page_open = (
            f'<div class="page" data-focus="all" '
            f'style="--ars:{sum(ratios):.4f};--floors:{len(ratios)};--tl-h:{timeline_h}px">'
        )
    else:
        page_open = '<div class="page solo">'
    parts = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{title}</title>",
        "<style>",
        STYLE.strip(),
        "</style>",
        "</head>",
        "<body>",
        SVG_DEFS,
        page_open,
    ]
    parts.extend(_render_header(data))
    # The problems are their own grid row: beside the stage on a wide
    # screen, above it when the layout stacks.
    if summary is not None and summary.get("problems"):
        parts.extend(_render_problems(summary["problems"], by_id))
    parts.append('<main class="col">')
    if summary is not None:
        parts.extend(_render_glance(summary, session["duration_s"]))
    if data.get("cross_player"):
        parts.extend(_render_across(data["cross_player"], id_to_rank))

    parts.extend(
        [
            '<section aria-labelledby="moments">',
            f'<h2 id="moments">{LABELS["sections"]["moments"]}</h2>',
            f'<p class="sub">{_e(LABELS["moments"]["sub"])}</p>',
        ]
    )
    parts.extend(_render_groups(kept, markers_by_moment, floor_count, has_map))
    parts.append("</section>")
    if dropped:
        parts.extend(_render_dropped(dropped, floor_count, has_map))
    parts.append("</main>")
    if has_map:
        parts.extend(_render_pane(data, floors, kept, dropped, markers, id_to_rank))
        parts.extend(timeline)
    parts.append("</div>")
    if has_map:
        parts.append(f"<script>{SCRIPT}</script>")
    parts.extend(["</body>", "</html>", ""])
    return "\n".join(parts)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Render findings.json as HTML.")
    parser.add_argument("findings", help="path to findings.json")
    parser.add_argument("-o", "--output", required=True, help="path for the HTML page")
    args = parser.parse_args(argv)

    data = findings_module.load(args.findings)
    page = render_html(data)
    Path(args.output).write_text(page, encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
