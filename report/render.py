"""Render a findings.json file as one self-contained HTML page.

The page only renders what the file holds. It computes nothing beyond
formatting seconds as m:ss, converting a world point to image pixels
with each floor's map JSON, placing times along the timeline, and the
structural counts a group heading needs.

Layout (task 37, Claude Fable 5.1, the mix Sasha picked from the task
36 mocks): two modes, never both on screen.

Read is a calm document to scroll: the verdict, the top problems with
the level's map beside them (every moment pinned, the whole route
faint, the counts as the legend, a "Time spent" switch for the heat),
then every moment in time order under its place heading with a still
frame each, then the dropped candidates in their own quiet section.

Watch is the player, opened by any moment or by Play the session: the
clip about two thirds of the screen with the player's words as the
headline, the summary and the likely cause under it; the map about one
third, one floor at a time following the player, the last 30 s of the
route strong over the whole route faint, the room, the floor and the
last game event above it, the game events just before under it; a slim
timeline along the bottom. Play runs the session at 10x between
moments and stops only at the unplanned ones (friction stuck or
blocked); Previous and Next reach every kept moment. Back or Escape
returns to the same place in Read.

One inline script drives Watch from one state: the current moment and
the map time. It reads every time, floor and word off the page and the
data-attributes the renderer wrote, fills the caption with clones of
the moment's own nodes, and computes no finding, time, position or
count: it only compares the file's times with the map time. Without
script the page is Read alone, every moment with its still frame.

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
# A line marked "Proposal" is not Sasha's wording.
LABELS = {
    "title": "Playtest Lens: session {id}",
    "session": "Session {id}",
    "kinds": {
        "stuck": {"label": "Stuck", "lower": "stuck", "class": "stuck"},
        "confused": {"label": "Confused", "lower": "confused", "class": "confused"},
        "surprised": {"label": "Surprised", "lower": "surprised", "class": "surprised"},
        "suspected_bug": {"label": "Suspected bug", "lower": "suspected bug", "class": "bug"},
    },
    "friction": {
        # "by design" is Sasha's decided word (2026-11-01). "unplanned" stays.
        "learning": {"level": 1, "tag": "by design", "unplanned": False},
        "stuck": {"level": 2, "tag": "unplanned", "unplanned": True},
        "blocked": {"level": 3, "tag": "unplanned", "unplanned": True},
    },
    "meter": {0: "None", 1: "Low", 2: "Medium", 3: "High"},
    "meter_aria": "Friction: {level}",
    "resolved": {"solved": "Resolved", "after": "Resolved after {time}"},
    "abandoned": "Abandoned",
    # Proposals (Claude Opus 5.5, 2026-11-01, from mockup B), not Sasha's wording.
    "floors": ("Ground floor", "Upper floor"),
    "floor_n": "Floor {n}",
    # Single words the counts and the pins use; pluralised by _plural.
    "words": {
        "attempt": "attempt",
        "visit": "visit",
        "moment": "moment",
        # Proposal (Claude Fable 5.1, 2026-11-01), not Sasha's wording. Links to the Dropped section.
        "dropped": "{n} dropped",
        "f9": "F9",
    },
    "head": {
        # Proposals (Claude Fable 5.1, 2026-11-01), not Sasha's wording.
        "line": "{length} recording, {kept} moments kept, {dropped}.",
        "lost": "{time} stuck or blocked.",
        "model": "Analyzed with {model}.",
        "play_session": "Play the session",
        "play_hint": "Runs at 10x between moments and stops at each unplanned one to play its clip. Previous and Next reach every moment.",
    },
    # Proposals (Claude Opus 5.5, 2026-11-01), not Sasha's wording.
    "problems": {
        "title": "Top problems",
        "sub": "Places where the player was stuck or blocked, worst first.",
        # Proposal (Claude Fable 5.1, 2026-11-01), not Sasha's wording.
        "lost": "{time} stuck",
        "mixed": "Partly resolved",
    },
    # The first-screen map. Proposals (Claude Fable 5.1, 2026-11-01), not
    # Sasha's wording; "Time spent" follows his answer 1 ("time spent").
    "overview": {
        "alt": "Top-down plan of the level, {floor}: every moment pinned by rank, the player's whole route faint.",
        "floor_switch": "Floor",
        "heat": "Time spent",
        "heat_note": "Each number is the time spent at that spot.",
        "lost": "{time} stuck or blocked",
    },
    "across": {
        "title": "Across players",
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
        "title": "The moments",
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
        "pin": "Moment {rank}, {kind}, {time}",
        "drop_pin": "Dropped, {kind}, {time}",
        # Proposal (Claude Fable 5.1, 2026-11-01), not Sasha's wording: a pin clamped to the map's edge.
        "edge_pin": "{label}, outside the mapped area",
        "clip": "Clip {span}",
        # Proposals (Claude Fable 5.1, 2026-11-01), not Sasha's wording.
        "more": "Game state and the checker's note",
        "watch": "Watch moment {rank}",
        "watch_dropped": "Watch the dropped candidate at {time}",
        "dropped_tag": "Dropped by the check",
    },
    "dropped": {
        "title": "Dropped moments",
        "note": "{n} candidates the check did not keep",
        "reason": "Reason: {note}",
    },
    "foot": {
        # Proposal (Claude Fable 5.1, 2026-11-01), not Sasha's wording.
        "pipeline": "How this page was made: {model} proposed moments from the video and the transcript; each was checked against its clip and the event log, and the page shows the file that check wrote.",
        "recording": "Recording",
    },
    # Proposals (Claude Fable 5.1, 2026-11-01), not Sasha's wording, except
    # "Previous", "Next", "Play", "Pause", "Moment {n} of {of}", "Dropped
    # {n} of {of}", "Game events so far" and "No game events yet.", which
    # are today's.
    "watch": {
        "back": "Back",
        "previous": "Previous",
        "next": "Next",
        "play": "Play",
        "pause": "Pause",
        "count": "Moment {n} of {of}",
        "count_dropped": "Dropped {n} of {of}",
        "clip": "Clip",
        "before": "Before this moment",
        "so_far": "Game events so far",
        "none_yet": "No game events yet.",
        "where": "{room}, {floor}",
        "between": "Between rooms",
        "off_map": "Outside the mapped area",
        "off_map_note": "This moment is outside the mapped area. Its pin sits at the map's edge.",
        "floor_switch": "Floor",
        "up_next": "Up next: moment {rank} at {time}, {place}",
        "up_next_head": "Up next",
        "walking": "Walking to the next unplanned moment",
        "end": "End of the session",
        "paused": "Paused. Press Play or pick a moment.",
        "keys": "Space plays and pauses. Left and right arrows step between moments. Escape goes back.",
        "tl_aria": "Timeline: the rooms, the moments by rank, the dropped candidates. Click to set the map's time.",
        "room_bar": "{room} {span}",
        "room_bar_puzzle": "{room}, {puzzle} {span}",
        "map_alt": "Top-down plan of the level, {floor}, with the player's route and the moments pinned.",
        "marker": "F9 marker at {time}",
    },
    "warning": "warning: map {map} not found; the page has no map",
}

STYLE = r"""
:root {
  color-scheme: light dark;
  --bg: #f5f6f8; --surface: #ffffff; --sunk: #eceef2;
  --ink: #151a24; --ink2: #434b5c; --muted: #596175; --line: #d6dae3;
  --accent: #2f45c7; --accent-tint: #e6e9fb; --on-accent: #ffffff;
  --k-stuck: #c2410c; --k-confused: #946200; --k-surprised: #0f766e; --k-bug: #a3195b;
  --t-stuck: #fbe9e0; --t-confused: #f7edd2; --t-surprised: #d9f1ee; --t-bug: #f9dfea;
  /* Pins always use the bright colors: the map is dark in both schemes. */
  --p-stuck: #ff8a5c; --p-confused: #f2c14e; --p-surprised: #4fd1c5; --p-bug: #ff7aa8;
  --bar: #c3c9d5; --bar-puzzle: #9aa6e8; --map-bg: #0a0d14;
  --s1: 4px; --s2: 8px; --s3: 12px; --s4: 16px; --s5: 24px; --s6: 40px;
  --fs-s: .8125rem; --fs-b: .9375rem; --fs-m: 1.125rem; --fs-l: 1.5rem; --fs-xl: 2rem;
  --font: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  --mono: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
  --bar-h: 52px; --tl-h: 104px;
}
@media (prefers-color-scheme: dark) {
  html .mk.k-confused b, html .tm.k-confused b { color: #1b1300; }
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
html { background: var(--bg); color: var(--ink); font: var(--fs-b)/1.5 var(--font); }
html.watching { overflow: hidden; }
body { margin: 0; }
h1, h2, h3, h4 { line-height: 1.2; margin: 0; }
p { margin: 0; }
a { color: var(--accent); }
button { font: inherit; color: inherit; cursor: pointer; }
.vh { position: absolute !important; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }
.mono { font-family: var(--mono); font-size: var(--fs-s); }
.ic { width: .85em; height: .85em; fill: currentColor; stroke: currentColor; stroke-width: 1.4; stroke-linejoin: round; vertical-align: -.05em; margin-right: .4em; }
.back .ic { fill: none; }
button:focus-visible, a:focus-visible, summary:focus-visible, input:focus-visible + span { outline: 2px solid var(--accent); outline-offset: 2px; }

/* kind shapes, rank marks, badges, tags: shape plus word everywhere, never color alone */
.sh { width: 1em; height: 1em; display: inline-block; vertical-align: -.15em; fill: currentColor; overflow: visible; }
.mk { display: inline-grid; place-items: center; width: 1.6rem; height: 1.6rem; position: relative; border: 0; background: none; padding: 0; color: var(--k); flex: none; }
.mk .sh { width: 1.6rem; height: 1.6rem; }
.mk b { position: absolute; font-size: .72rem; font-weight: 700; color: #fff; font-family: var(--mono); }
.mk.k-bug b { top: .45rem; }
.mk.k-confused b { color: #fff; }
.mk.hollow .sh { fill: none; stroke: currentColor; stroke-width: 1.6; }
.k-stuck { --k: var(--k-stuck); --t: var(--t-stuck); --p: var(--p-stuck); } .k-confused { --k: var(--k-confused); --t: var(--t-confused); --p: var(--p-confused); }
.k-surprised { --k: var(--k-surprised); --t: var(--t-surprised); --p: var(--p-surprised); } .k-bug { --k: var(--k-bug); --t: var(--t-bug); --p: var(--p-bug); }
.badge { display: inline-flex; align-items: center; gap: .35em; font-size: var(--fs-s); font-weight: 600; color: var(--ink2); }
.badge .k { width: .6em; height: .6em; border-radius: 50%; background: var(--k); display: inline-block; }
.badge .k-stuck { border-radius: 1px; } .badge .k-surprised { transform: rotate(45deg); border-radius: 1px; }
.badge .k-bug { width: 0; height: 0; background: none; border-left: .35em solid transparent; border-right: .35em solid transparent; border-bottom: .6em solid var(--k); }
.intent { font-size: var(--fs-s); color: var(--muted); border: 1px dashed var(--line); border-radius: 4px; padding: 0 .45em; }
.intent.unplanned { color: var(--ink); border-style: solid; border-color: var(--ink2); font-weight: 600; }
.intent.dropped { border-style: solid; }
.time { font-family: var(--mono); font-size: var(--fs-s); color: var(--ink2); font-variant-numeric: tabular-nums; }
.meter { display: inline-flex; gap: 2px; margin-right: .4em; vertical-align: -1px; }
.meter i { width: 10px; height: 8px; background: var(--sunk); border: 1px solid var(--line); border-radius: 1px; }
.meter i.on { background: var(--ink2); border-color: var(--ink2); }
.status { font-weight: 600; } .status.done { color: var(--k-surprised); } .status.open { color: var(--k-stuck); }
.status.done::before { content: "\2713\00a0"; } .status.open::before { content: "\2717\00a0"; }
.facts-line { display: flex; flex-wrap: wrap; gap: .25em 1em; align-items: center; color: var(--muted); font-size: var(--fs-s); }
.facts-line .mks { display: inline-flex; gap: .2em; flex-wrap: wrap; }
.facts { display: grid; grid-template-columns: auto minmax(0, 1fr); gap: .2em 1em; margin: var(--s2) 0 0; font-size: var(--fs-s); }
.facts dt { color: var(--muted); font-weight: 600; } .facts dd { margin: 0; color: var(--ink2); overflow-wrap: anywhere; }
.primary { background: var(--accent); color: var(--on-accent); border: 0; border-radius: 8px; padding: .55em 1.1em; font-weight: 600; }
.primary:hover { filter: brightness(1.08); }

/* ------------------------------------------------------------ Read */
.read { max-width: 1180px; margin: 0 auto; padding: var(--s6) var(--s5) 80px; }
.head h1 { font-size: var(--fs-l); font-weight: 700; color: var(--ink2); }
.head .model { color: var(--muted); font-size: var(--fs-s); margin-top: var(--s1); }
.head .verdict { font-size: var(--fs-xl); font-weight: 700; line-height: 1.2; margin-top: var(--s3); letter-spacing: -.01em; max-width: 36ch; }
.head .meta { color: var(--muted); margin-top: var(--s2); }
.head .start { margin-top: var(--s5); display: flex; align-items: center; gap: var(--s4); flex-wrap: wrap; }
.head .hint { color: var(--muted); font-size: var(--fs-s); max-width: 44em; }
.read h2 { font-size: var(--fs-m); font-weight: 700; margin-top: var(--s6); scroll-margin-top: var(--s4); }
.read .sub { color: var(--muted); font-size: var(--fs-s); margin-top: var(--s1); }
/* The first screen: the problems with the level beside them. */
.first { display: grid; grid-template-columns: minmax(0, 1fr) minmax(280px, 36%); gap: var(--s5) var(--s6); align-items: start; margin-top: var(--s4); }
.first h2 { margin-top: var(--s4); }
.problems ol { list-style: none; counter-reset: p; margin: var(--s4) 0 0; padding: 0; display: grid; gap: var(--s2); }
.problems li { counter-increment: p; display: grid; grid-template-columns: 1.6rem 1fr; gap: .2em var(--s3); align-items: baseline; background: var(--surface); border: 1px solid var(--line); border-radius: 10px; padding: var(--s3) var(--s4); }
.problems li::before { content: counter(p); font-family: var(--mono); color: var(--muted); font-weight: 600; grid-row: span 2; }
.problems .place { border: 0; background: none; padding: 0; text-align: left; font-size: var(--fs-m); font-weight: 700; color: var(--accent); text-decoration: underline; text-underline-offset: .15em; }
.problems .place:hover { text-decoration-thickness: 2px; }
.problems .mk:hover { transform: scale(1.1); }
.ovmap { margin: var(--s4) 0 0; display: grid; gap: var(--s2); }
.ovmap .floor { margin: 0; background: var(--map-bg); border-radius: 10px; overflow: hidden; display: grid; place-items: center; }
.ovmap.multi .floor { display: none; }
.ovmap .floor svg { display: block; width: 100%; height: auto; max-height: min(78vh, 900px); }
.ovmap .legend { list-style: none; margin: 0; padding: 0; display: flex; flex-wrap: wrap; gap: var(--s1) var(--s4); font-size: var(--fs-s); color: var(--ink2); align-items: center; }
.ovmap .legend li { display: inline-flex; align-items: center; gap: .35em; }
.ovmap .legend b { font-variant-numeric: tabular-nums; }
.ovmap .legend .lost b { font-family: var(--mono); }
.ovmap .tools { display: flex; justify-content: space-between; align-items: center; gap: var(--s3); flex-wrap: wrap; }
.floors-switch, .heatsw { display: inline-flex; border: 1px solid var(--line); border-radius: 6px; overflow: hidden; margin: 0; padding: 0; }
.floors-switch label, .heatsw { position: relative; }
.floors-switch input, .heatsw input { position: absolute; inset: 0; margin: 0; opacity: 0; cursor: pointer; }
.floors-switch span, .floors-switch button, .heatsw span { display: block; border: 0; background: var(--surface); padding: .2em .7em; font-size: var(--fs-s); color: var(--muted); cursor: pointer; }
.floors-switch input:checked + span, .floors-switch button[aria-pressed="true"], .heatsw input:checked + span { background: var(--accent-tint); color: var(--ink); font-weight: 600; }
.heatnote { font-size: var(--fs-s); color: var(--muted); display: none; }
.ovmap:has(#heat:checked) .heatnote { display: block; }
/* The time-spent switch: the heat shows, the route and the pins step back. */
.map .heat { display: none; }
.ovmap:has(#heat:checked) .map .heat { display: inline; }
.ovmap:has(#heat:checked) .map :is(.route, .pins) { opacity: .12; }
.ovmap:has(#heat:checked) .map .bg { filter: grayscale(1) brightness(.6); }
.halo-text { font: 700 40px var(--font); fill: #ffffff; stroke: #0a0d14; stroke-width: 9; paint-order: stroke; text-anchor: middle; }
/* across players */
.groups { list-style: none; margin: var(--s3) 0 0; padding: 0; display: grid; gap: var(--s2); }
.groups .group { background: var(--surface); border: 1px solid var(--line); border-radius: 10px; padding: var(--s3) var(--s4); display: grid; gap: var(--s1); }
.groups h3 { font-size: var(--fs-b); }
.group .who { font-weight: 600; }
.chips { display: flex; flex-wrap: wrap; gap: var(--s2); align-items: center; }
.chip { display: inline-flex; align-items: center; gap: var(--s1); padding: 2px var(--s3); border: 1px solid var(--line); border-radius: 999px; font-size: var(--fs-s); background: var(--sunk); color: var(--ink2); text-decoration: none; }
.chip.you { background: var(--accent-tint); border-color: var(--accent); color: var(--ink); }
a.chip:hover { border-color: var(--accent); }
.across .note { color: var(--muted); font-size: var(--fs-s); margin-top: var(--s2); }
/* the moments */
.moments-group { margin-top: var(--s5); }
.moments-group > h3 { font-size: var(--fs-s); text-transform: uppercase; letter-spacing: .06em; color: var(--muted); padding-top: var(--s3); border-top: 1px solid var(--line); display: flex; flex-wrap: wrap; gap: .2em var(--s3); align-items: baseline; }
.moments-group > h3 .note { text-transform: none; letter-spacing: 0; font-weight: 400; }
.moments-group h4 { font-size: var(--fs-s); color: var(--muted); font-weight: 600; margin-top: var(--s4); }
.m, .d { display: grid; grid-template-columns: 220px minmax(0, 1fr); gap: var(--s4); margin-top: var(--s4); align-items: start; scroll-margin-top: var(--s5); }
.m:target, .d:target { outline: 2px solid var(--accent); outline-offset: 6px; border-radius: 4px; }
.m.soft .summary { font-weight: 500; color: var(--ink2); }
.m .summary { font-size: var(--fs-m); font-weight: 600; margin-top: var(--s1); line-height: 1.35; }
.d .summary { color: var(--ink2); margin-top: var(--s1); }
.body { min-width: 0; display: flex; flex-direction: column; }
.body > * + * { margin-top: var(--s2); }
.body .mhead + .summary { margin-top: var(--s1); }
.mhead { display: flex; align-items: center; gap: var(--s2); flex-wrap: wrap; }
.mhead .place { font-size: var(--fs-s); color: var(--muted); }
.quote { color: var(--ink2); font-style: italic; border-left: 3px solid var(--line); padding-left: var(--s3); }
.quote.none { color: var(--muted); border-color: transparent; padding-left: 0; }
.cause { font-size: var(--fs-b); color: var(--ink2); }
.cause .lab { font-weight: 700; color: var(--ink); margin-right: .4em; }
.fric { font-size: var(--fs-s); color: var(--muted); display: flex; gap: 1em; align-items: center; flex-wrap: wrap; }
.f9line { font-size: var(--fs-s); color: var(--ink2); }
.f9line b { border: 1px dashed var(--ink2); border-radius: 4px; padding: 0 var(--s1); margin-right: var(--s1); }
.more { font-size: var(--fs-s); }
.more summary { color: var(--muted); cursor: pointer; width: max-content; }
.more[open] summary { color: var(--ink2); }
.reason { color: var(--muted); font-size: var(--fs-s); }
.watchbtn { position: relative; display: block; width: 100%; aspect-ratio: 16 / 9; padding: 0; border: 1px solid var(--line); border-radius: 8px; overflow: hidden; background: #000; color: #fff; }
.watchbtn .still { width: 100%; height: 100%; object-fit: cover; display: block; }
.watchbtn .playglyph { position: absolute; inset: 0; display: grid; place-items: center; }
.watchbtn .playglyph svg { width: 36px; height: 36px; fill: #fff; filter: drop-shadow(0 1px 3px rgba(0,0,0,.6)); opacity: .9; }
.watchbtn:hover .playglyph svg { transform: scale(1.1); opacity: 1; }
.watchbtn .cliplen { position: absolute; right: 6px; bottom: 5px; font: 600 11px/1 var(--mono); color: #fff; background: rgba(0,0,0,.55); padding: 3px 5px; border-radius: 3px; }
.watchbtn.none { background: var(--sunk); border-style: dashed; }
.watchbtn.none .playglyph svg { fill: var(--muted); filter: none; }
.d .watchbtn { opacity: .8; }
.foot { margin-top: var(--s6); padding-top: var(--s4); border-top: 1px solid var(--line); color: var(--muted); font-size: var(--fs-s); display: grid; gap: var(--s2); }

/* ----------------------------------------------------------- Watch */
.watch { position: fixed; inset: 0; background: var(--bg); display: grid; grid-template-columns: minmax(0, 1fr); grid-template-rows: var(--bar-h) minmax(0, 1fr) var(--tl-h); z-index: 10; }
.bar { display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; padding: 0 var(--s4); border-bottom: 1px solid var(--line); background: var(--surface); gap: var(--s3); }
.bar .back { justify-self: start; border: 1px solid var(--line); background: var(--sunk); border-radius: 8px; padding: .4em .9em .4em .7em; font-weight: 600; }
.bar .count { font-family: var(--mono); font-size: var(--fs-s); color: var(--ink2); text-align: center; font-variant-numeric: tabular-nums; }
.bar .nav { justify-self: end; display: flex; gap: var(--s2); }
.bar .nav button { border: 1px solid var(--line); background: var(--sunk); border-radius: 8px; padding: .4em .9em; font-weight: 600; }
.bar .nav button:disabled { opacity: .4; cursor: default; }
.bar button { white-space: nowrap; }
/* The main control keeps the accent: this rule outranks .bar .nav button. */
.bar .nav .primary { border-color: transparent; min-width: 6em; background: var(--accent); color: var(--on-accent); }
#play .when-playing { display: none; } .watch.playing #play .when-paused { display: none; } .watch.playing #play .when-playing { display: inline; }
.main { display: grid; grid-template-columns: minmax(0, 2fr) minmax(0, 1fr); gap: var(--s5); padding: var(--s4) var(--s5); min-height: 0; }
.screen { display: grid; grid-template-rows: auto minmax(0, 1fr); gap: var(--s3); min-width: 0; min-height: 0; }
.clipbox { position: relative; background: #000; border-radius: 10px; overflow: hidden; width: min(100%, calc((100vh - var(--bar-h) - var(--tl-h) - 256px) * 16 / 9)); aspect-ratio: 16 / 9; justify-self: center; }
.clipbox video { width: 100%; height: 100%; display: block; background: #000; }
.travel { position: absolute; inset: 0; background: rgba(8, 10, 16, .78); color: #fff; display: grid; align-content: center; justify-items: center; gap: var(--s2); text-align: center; padding: var(--s4); }
.travel .big { font: 700 clamp(2rem, 6vw, 4rem)/1 var(--mono); letter-spacing: -.02em; font-variant-numeric: tabular-nums; }
.travel .what { font-size: var(--fs-m); opacity: .9; }
.travel .prog { width: min(60%, 360px); height: 4px; background: rgba(255,255,255,.25); border-radius: 2px; overflow: hidden; }
.travel .prog i { display: block; height: 100%; background: #fff; width: 0; }
/* The caption: the moment's own nodes, the quote first as the headline. */
.caption { overflow: auto; padding-right: var(--s2); display: flex; flex-direction: column; gap: var(--s2); }
.caption .mhead { order: -2; }
.caption .quote:not(.none) { order: -1; font-size: clamp(1.15rem, 1.7vw, 1.6rem); font-weight: 700; font-style: normal; line-height: 1.3; color: var(--ink); border-left: 4px solid var(--accent); }
.caption .summary { font-size: var(--fs-m); font-weight: 500; color: var(--ink2); }
.caption .quote.none { font-size: var(--fs-s); }
/* While the session walks, the column previews the next stop. */
.caption .upnext { order: -3; font-size: var(--fs-s); text-transform: uppercase; letter-spacing: .06em; color: var(--muted); font-weight: 600; }
.side { display: grid; grid-template-rows: auto minmax(0, 1fr) auto; gap: var(--s3); min-height: 0; min-width: 0; }
.context { display: grid; gap: 2px; }
.context .where { font-weight: 700; font-size: var(--fs-m); min-height: 1.3em; }
.context .lastev { font-size: var(--fs-s); color: var(--muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; min-height: 1.3em; }
.context .lastev time { font-family: var(--mono); margin-right: .6em; }
.context .offmap { font-size: var(--fs-s); color: var(--ink2); border-left: 3px dashed var(--line); padding-left: var(--s2); margin-top: var(--s1); }
.context .floors-switch { margin-top: var(--s1); justify-self: start; }
.maps { min-height: 0; display: grid; }
.maps .floor { margin: 0; min-height: 0; background: var(--map-bg); border-radius: 10px; overflow: hidden; display: grid; place-items: center; }
.maps .floor svg { max-height: 100%; max-width: 100%; height: 100%; width: auto; display: block; }
/* The whole route recedes (no casing, thin and faint); the 30 s trail stays loud. */
.route .line { fill: none; stroke: #c9d2ea; stroke-opacity: .22; stroke-width: 5; stroke-linejoin: round; stroke-linecap: round; }
.strong polyline { fill: none; stroke: #fff; stroke-width: 14; stroke-linejoin: round; stroke-linecap: round; }
.strong .case { stroke: #000; stroke-opacity: .6; stroke-width: 24; }
/* Only a pin's own disc takes a click: the decoration never does. */
.route, .strong, .dot, .heat, .pin .ring, .pin .edge-mark { pointer-events: none; }
.pin .hit { fill: transparent; stroke: none; }
.pin { cursor: pointer; color: var(--p); opacity: .6; }
.pin use { fill: var(--p); stroke: #000; stroke-opacity: .55; stroke-width: 2; }
.pin .ring { fill: none; stroke: #fff; stroke-width: 6; opacity: 0; }
.pin .edge-mark { fill: none; stroke: #fff; stroke-width: 4; stroke-dasharray: 10 8; opacity: .9; }
.pin text { font: 700 44px var(--mono); fill: #10131a; text-anchor: middle; dominant-baseline: middle; pointer-events: none; }
.pin.soft text { font-size: 34px; }
.pin.hollow use { fill: none; stroke: var(--p); stroke-width: 4; }
.pin.f9 use { fill: #0b1020; stroke: #ffffff; stroke-width: 1.2; stroke-dasharray: 2.4 1.6; }
.pin.f9 text { fill: #ffffff; font-size: 28px; }
.ovmap .pin { opacity: .9; }
.pin:hover, .pin:focus-visible { opacity: 1; }
.pin.cur { opacity: 1; } .pin.cur .ring { opacity: 1; }
.pin.cur use { stroke-width: 3; }
.dot .halo { fill: #fff; fill-opacity: .25; } .dot .core { fill: #fff; stroke: #10131a; stroke-width: 4; }
.before h2 { font-size: var(--fs-s); text-transform: uppercase; letter-spacing: .06em; color: var(--muted); font-weight: 600; }
.events { list-style: none; margin: var(--s1) 0 0; padding: 0; font-size: var(--fs-s); color: var(--ink2); display: grid; gap: 2px; }
.events time { font-family: var(--mono); color: var(--muted); margin-right: .7em; }
.before .none { font-size: var(--fs-s); color: var(--muted); margin-top: var(--s1); }
/* Between moments the map is the thing: the columns trade places in width. */
.watch.travelling .main { grid-template-columns: minmax(0, 1fr) minmax(0, 2fr); }
.watch.travelling .clipbox { width: 100%; }
@media (prefers-reduced-motion: no-preference) {
  .main { transition: grid-template-columns .35s ease; }
  .pin, .watchbtn .playglyph svg, .problems .mk { transition: opacity .15s, transform .15s; }
}
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { transition: none !important; animation: none !important; } }

/* -------------------------------------------------------- Timeline */
.tl { border-top: 1px solid var(--line); background: var(--surface); padding: var(--s2) var(--s5) var(--s1); }
.track { position: relative; height: 100%; cursor: pointer; }
.r-rooms { position: relative; height: 18px; }
.room { position: absolute; top: 0; height: 18px; background: var(--bar); border-radius: 3px; font: 600 11px/18px var(--font); color: var(--ink); padding: 0 5px; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
.room.puzzle { background: var(--bar-puzzle); }
.r-marks { position: relative; height: calc(var(--rows) * 24px); margin-top: 6px; }
.tm { position: absolute; top: calc(var(--row) * 24px); transform: translateX(-50%); width: 22px; height: 22px; padding: 0; border: 0; background: none; display: grid; place-items: center; color: var(--k); }
.tm .sh { width: 22px; height: 22px; } .tm.soft .sh { width: 16px; height: 16px; }
.tm b { position: absolute; font: 700 10px var(--mono); color: #fff; } .tm.k-confused b { color: #fff; } .tm.soft b { font-size: 9px; } .tm.k-bug b { top: 8px; }
.tm.hollow .sh { fill: none; stroke: currentColor; stroke-width: 2; width: 14px; height: 14px; }
.tm:hover, .tm.cur { transform: translateX(-50%) scale(1.25); }
.tm.cur::after { content: ""; position: absolute; inset: -4px; border: 2px solid var(--ink); border-radius: 50%; }
.r-axis { position: relative; height: 16px; margin-top: 4px; font: 11px/16px var(--mono); color: var(--muted); }
.r-axis span { position: absolute; transform: translateX(-50%); }
.r-axis span::before { content: ""; position: absolute; left: 50%; top: -5px; width: 1px; height: 4px; background: var(--line); }
.past { position: absolute; left: 0; top: 0; bottom: 0; width: 0; background: var(--accent); opacity: .08; pointer-events: none; }
.cursor { position: absolute; top: -4px; bottom: 0; width: 2px; background: var(--accent); transform: translateX(-1px); display: none; pointer-events: none; }
.cursor.on { display: block; }

@media (max-width: 1100px) {
  .main { grid-template-columns: minmax(0, 5fr) minmax(0, 2fr); gap: var(--s4); padding: var(--s3) var(--s4); }
}
@media (max-width: 900px) {
  .first { grid-template-columns: 1fr; }
  .ovmap .floor svg { max-height: 70vh; }
}
@media (max-width: 720px) {
  /* One column in normal flow: the clip, the words, then the map, never on top of each other. */
  .main, .watch.travelling .main { display: block; overflow: auto; }
  .screen { display: flex; flex-direction: column; gap: var(--s3); }
  .clipbox, .watch.travelling .clipbox { width: 100%; flex: none; }
  .caption { overflow: visible; }
  .side { grid-template-rows: auto 60vh auto; margin-top: var(--s4); }
  .bar { grid-template-columns: auto 1fr auto; }
  .bar .count { display: none; }
  /* Half the axis labels on a narrow track, so they never collide. */
  .r-axis span:nth-child(even) { display: none; }
}
@media (max-width: 640px) {
  .m, .d { grid-template-columns: 1fr; }
  .read { padding: var(--s5) var(--s4) 60px; }
  .head .verdict { font-size: var(--fs-l); }
}
@media (max-width: 420px) {
  .bar { padding: 0 var(--s2); gap: var(--s2); }
  .bar button { padding: .4em .6em; }
}
@media print { .watch { display: none !important; } .watchbtn, .playglyph { display: none; } .m, .d { grid-template-columns: 1fr; } }
"""

# The heat map's color scale, cool and sparse to hot, as on public
# shooter heatmaps. One list feeds the SVG filter.
HEAT_RAMP = ("#2b59ff", "#18c1e6", "#3ddc84", "#f5d327", "#fb7a1c", "#e8231f")
HEAT_ALPHA = (0, .5, .65, .78, .86, .92)


def _ramp_table(channel):
    return " ".join(
        f"{int(color[1 + 2 * channel:3 + 2 * channel], 16) / 255:.3f}"
        for color in HEAT_RAMP
    )


# Shapes in a -10..10 box, drawn by <use> at any size; heat spots are
# white blobs whose opacity is their weight, and the filter turns that
# opacity into the color scale. One hidden SVG holds them, and each
# floor's picture once, so the overview map and Watch share it.
SVG_DEFS = (
    '<symbol id="sh-stuck" viewBox="-10 -10 20 20" overflow="visible"><rect x="-8" y="-8" width="16" height="16" rx="1.5"/></symbol>'
    '<symbol id="sh-confused" viewBox="-10 -10 20 20" overflow="visible"><circle r="8.8"/></symbol>'
    '<symbol id="sh-surprised" viewBox="-10 -10 20 20" overflow="visible"><polygon points="0,-10 10,0 0,10 -10,0"/></symbol>'
    '<symbol id="sh-bug" viewBox="-10 -10 20 20" overflow="visible"><polygon points="0,-9.5 10,8.5 -10,8.5"/></symbol>'
    '<symbol id="sh-f9" viewBox="-10 -10 20 20" overflow="visible"><polygon points="0,-9.5 8.2,-4.75 8.2,4.75 0,9.5 -8.2,4.75 -8.2,-4.75"/></symbol>'
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
)

PLAY_GLYPH = '<svg class="ic" viewBox="0 0 12 12" aria-hidden="true"><path d="M3 1.5l7 4.5-7 4.5z"/></svg>'

# Map drawing sizes, in map image pixels (about 48 per metre). A moment
# by design (friction "learning") gets the smaller pin, so the unplanned
# ones stand out.
PIN_R = 44
SOFT_R = 34
DROP_R = 28
F9_R = 34

# The timeline: two marks closer than this share of the recording go on
# separate rows, up to STRIP_ROWS rows.
STRIP_GAP = 0.03
STRIP_ROWS = 2
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


def _span(start_s, end_s):
    start, end = _mss(start_s), _mss(end_s)
    return start if start == end else f"{start}-{end}"


def _plural(count, word):
    return f"{count} {word}" if count == 1 else f"{count} {word}s"


# The first value that is not None: a stored time of 0 is a real time.
def _first_set(*values):
    return next(value for value in values if value is not None)


def _moment_end(finding):
    return _first_set(finding.get("end_s"), finding["time_s"])


def world_to_px(meta, x, z):
    """Convert a world point to image pixels with the map's own JSON."""
    px = (x - meta["world_min_x"]) / (meta["world_max_x"] - meta["world_min_x"]) * meta["px_width"]
    py = (z - meta["world_min_z"]) / (meta["world_max_z"] - meta["world_min_z"]) * meta["px_height"]
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
    return LABELS["kinds"].get(kind, {"label": str(kind), "lower": str(kind), "class": "stuck"})


# A moment by design (friction "learning") recedes on the map, the
# timeline and the list; the unplanned ones stand out, and Play the
# session stops only at them.
def _is_soft(finding):
    rule = LABELS["friction"].get(finding["check"].get("friction"))
    return rule is not None and not rule["unplanned"]


def _is_stop(finding):
    rule = LABELS["friction"].get(finding["check"].get("friction"))
    return rule is not None and rule["unplanned"]


def _shape(kind, extra=""):
    return (
        f'<svg class="sh" viewBox="-10 -10 20 20" aria-hidden="true" focusable="false">'
        f'<use href="#sh-{_kind(kind)["class"]}" x="-10" y="-10" width="20" height="20"/></svg>{extra}'
    )


def _pin_words(finding):
    return LABELS["card"]["pin"].format(
        rank=finding["rank"], kind=_kind(finding["kind"])["label"], time=_mss(finding["time_s"])
    )


def _drop_words(finding):
    return LABELS["card"]["drop_pin"].format(
        kind=_kind(finding["kind"])["lower"], time=_mss(finding["time_s"])
    )


# Where a moment happened, in words: the puzzle or the area, the attempt
# when past the first, and the floor when the level has more than one.
def _place(finding, floor_count):
    beat = finding.get("beat") or {}
    title = beat.get("puzzle") or beat.get("area") or finding["check"].get("area")
    if not title:
        title = LABELS["moments"]["fallback"]
    attempt = beat.get("attempt")
    if isinstance(attempt, int) and attempt > 1:
        title = LABELS["moments"]["pin_attempt"].format(title=title, n=attempt)
    at = finding.get("at")
    if floor_count > 1 and at is not None:
        title = f"{title}, {_floor_name(at['floor'])}"
    return title


def _models(findings):
    return ", ".join(sorted({f["check"]["model"] for f in findings if f["check"].get("model")}))


def _render_meter(friction):
    rule = LABELS["friction"].get(friction)
    if rule is None:
        return ""
    level = rule["level"]
    word = LABELS["meter"][level]
    bars = "".join('<i class="on"></i>' if index <= level else "<i></i>" for index in range(1, 4))
    aria = LABELS["meter_aria"].format(level=word.lower())
    return f'<span class="meter" role="img" aria-label="{_e(aria)}">{bars}</span>{_e(word)}'


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
    bits = [bit for bit in (_render_meter(check.get("friction")), _render_status(check)) if bit]
    return f'<p class="fric">{" ".join(bits)}</p>' if bits else ""


# ------------------------------------------------------------------ Read

# The counts the page prints: the summary's when the file has one, else
# the lists' lengths (a file without a summary has no other count).
def _counts(data, kept, dropped):
    summary = data.get("summary") or {}
    return summary.get("kept", len(kept)), summary.get("dropped", len(dropped))


# "{n} dropped" as a link to the Dropped section (a scroll, never Watch).
def _dropped_link(count):
    return f'<a href="#dropped">{_e(LABELS["words"]["dropped"].format(n=count))}</a>'


def _render_header(data, kept, dropped):
    session = data["session"]
    summary = data.get("summary") or {}
    words = LABELS["head"]
    heading = LABELS["session"].format(id=_e(session["id"]))
    if session.get("player"):
        heading += f": {_e(session['player'])}"
    parts = ['<header class="head">', f"<h1>{heading}</h1>"]
    models = _models(data["findings"])
    if models:
        model_line = _e(words["model"]).replace("{model}", f'<span class="mono">{_e(models)}</span>')
        parts.append(f'<p class="model">{model_line}</p>')
    if summary.get("verdict"):
        parts.append(f'<p class="verdict">{_e(summary["verdict"])}</p>')
    kept_count, dropped_count = _counts(data, kept, dropped)
    line = _e(words["line"].format(length=_mss(session["duration_s"]), kept=kept_count, dropped="{dropped}"))
    line = line.replace("{dropped}", _dropped_link(dropped_count) if dropped else _e(LABELS["words"]["dropped"].format(n=dropped_count)))
    if summary.get("lost_s"):
        line += " " + _e(words["lost"].format(time=_mss(summary["lost_s"])))
    parts.append(f'<p class="meta">{line}</p>')
    if any(f.get("clip") is not None for f in kept):
        parts.append(
            f'<p class="start" data-needs-script hidden><button type="button" class="primary" id="play-session">'
            f'{PLAY_GLYPH}{_e(words["play_session"])}</button><span class="hint">{_e(words["play_hint"])}</span></p>'
        )
    parts.append("</header>")
    return parts


# The worst places, from summary.problems. Each opens its first moment
# and lists its moments by rank.
def _render_problems(problems, by_id):
    words = LABELS["problems"]
    items = []
    for problem in problems:
        moments = [by_id[moment] for moment in problem["moments"] if moment in by_id]
        first = moments[0] if moments else None
        place = _e(problem["place"])
        if first is not None:
            place = f'<a class="place" href="#m{first["rank"]}" data-open="{_e(first["id"])}">{place}</a>'
        else:
            place = f'<span class="place">{place}</span>'
        is_puzzle = bool(first and (first.get("beat") or {}).get("puzzle"))
        bits = [
            _render_meter(problem["friction"]),
            _e(_plural(problem["attempts"], LABELS["words"]["attempt" if is_puzzle else "visit"])),
            _e(_plural(len(problem["moments"]), LABELS["words"]["moment"])),
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
            f'<a class="mk k-{_kind(f["kind"])["class"]}" href="#m{f["rank"]}" data-open="{_e(f["id"])}" '
            f'aria-label="{_e(_pin_words(f))}">{_shape(f["kind"], f"<b>{f['rank']}</b>")}</a>'
            for f in sorted(moments, key=lambda f: f["rank"])
        )
        line = "".join(f"<span>{bit}</span>" for bit in bits)
        items.append(f'<li>{place}<span class="facts-line">{line}<span class="mks">{marks}</span></span></li>')
    return [
        '<section class="problems" aria-labelledby="problems">',
        f'<h2 id="problems">{_e(words["title"])}</h2>',
        f'<p class="sub">{_e(words["sub"])}</p>',
        f'<ol>{"".join(items)}</ol>',
        "</section>",
    ]


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
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{radius:.1f}" fill="url(#heat-blob)" fill-opacity="{weight:.2f}"/>'
        )
        labels.append(f'<text class="halo-text" x="{cx:.1f}" y="{cy + 14:.1f}">{_mss(spot["seconds"])}</text>')
    return ['<g class="heat" aria-hidden="true">', '<g filter="url(#heat-ramp)">', *blobs, "</g>", *labels, "</g>"]


# Runs of consecutive route points on one floor: (floor, [points]).
def _route_runs(points):
    runs = []
    for point in points:
        if runs and runs[-1][0] == point[3]:
            runs[-1][1].append(point)
        else:
            runs.append((point[3], [point]))
    return runs


# One floor's share of the route: each run drawn as one faint line that
# carries the run's times for the script's dot and trail.
def _render_route(runs, floor, meta):
    parts = ['<g class="route" aria-hidden="true">']
    for run_floor, points in runs:
        if run_floor != floor:
            continue
        pixels = " ".join("{:.1f},{:.1f}".format(*world_to_px(meta, p[1], p[2])) for p in points)
        stamps = " ".join(str(p[0]) for p in points)
        parts.append(f'<polyline class="line" data-t="{stamps}" points="{pixels}"/>')
    parts.append("</g>")
    return parts


# Where a pin is drawn: its own pixels on the map, or, for a point outside
# the drawn area (another scene at the map's edge), clamped just inside
# the edge and marked, so the moment is visible and says so.
def _pin_spot(meta, at, radius):
    x, y = world_to_px(meta, at["x"], at["z"])
    width, height = meta["px_width"], meta["px_height"]
    outside = x < 0 or y < 0 or x > width or y > height
    if outside:
        margin = radius + 8
        x = min(max(x, margin), width - margin)
        y = min(max(y, margin), height - margin)
    return x, y, outside


# A pin: a transparent disc first (the one thing that takes the click, so
# a hollow pin and a pin under a neighbour's ring still hit their own
# <a>), the focus ring, the edge mark when clamped, then the shape.
def _pin_open(css, href, finding, label, radius, meta):
    x, y, outside = _pin_spot(meta, finding["at"], radius)
    if outside:
        css += " edge"
        label = LABELS["card"]["edge_pin"].format(label=label)
    body = f'<circle class="hit" r="{radius}"/><circle class="ring" r="{radius + 14}"/>'
    if outside:
        body += f'<circle class="edge-mark" r="{radius + 6}"/>'
    return (
        f'<a class="{css}" href="{href}" data-open="{_e(finding["id"])}" '
        f'aria-label="{_e(label)}" transform="translate({x:.1f} {y:.1f})">{body}'
    )


def _render_pins(kept, dropped, markers, floor, meta, id_to_rank):
    parts = ['<g class="pins">']
    for finding in dropped:
        at = finding.get("at")
        if at is None or at["floor"] != floor:
            continue
        info = _kind(finding["kind"])
        parts.append(
            _pin_open(f'pin hollow k-{info["class"]}', f'#d-{_e(finding["id"])}', finding, _drop_words(finding), DROP_R, meta)
            + f'<use href="#sh-{info["class"]}" x="-{DROP_R}" y="-{DROP_R}" width="{2 * DROP_R}" height="{2 * DROP_R}"/></a>'
        )
    for finding in kept:
        at = finding.get("at")
        if at is None or at["floor"] != floor:
            continue
        info = _kind(finding["kind"])
        rank = finding["rank"]
        soft = _is_soft(finding)
        radius = SOFT_R if soft else PIN_R
        dy = (6 if soft else 8) if info["class"] == "bug" else 2
        css = f'pin k-{info["class"]}' + (" soft" if soft else "")
        parts.append(
            _pin_open(css, f"#m{rank}", finding, _pin_words(finding), radius, meta)
            + f'<use href="#sh-{info["class"]}" x="-{radius}" y="-{radius}" width="{2 * radius}" height="{2 * radius}"/>'
            f'<text y="{dy}">{rank}</text></a>'
        )
    for marker in markers:
        if marker["floor"] != floor:
            continue
        x, y = world_to_px(meta, marker["x"], marker["z"])
        target = id_to_rank.get(marker.get("moment")) if marker.get("moment") else None
        label = _e(LABELS["watch"]["marker"].format(time=_mss(marker["t"])))
        body = (
            f'<circle class="hit" r="{F9_R}"/><use href="#sh-f9" x="-{F9_R}" y="-{F9_R}" width="{2 * F9_R}" height="{2 * F9_R}"/>'
            f'<text>{_e(LABELS["words"]["f9"])}</text>'
        )
        at = f'transform="translate({x:.1f} {y:.1f})"'
        if target is not None:
            parts.append(
                f'<a class="pin f9" href="#m{target}" data-open="{_e(marker["moment"])}" aria-label="{label}" {at}>{body}</a>'
            )
        else:
            parts.append(f'<g class="pin f9" aria-label="{label}" {at}>{body}</g>')
    parts.append("</g>")
    return parts


# One floor of a map: the picture (shared through its id), the heat for
# the overview only, the route, the strong trail and the dot for Watch,
# the pins. Watch hides every floor but the first with the attribute the
# script toggles; the overview's radios and CSS pick the floor instead.
def _render_floor(index, meta, runs, kept, dropped, markers, id_to_rank, alt, hidden, heat=(), top=1):
    width, height = meta["px_width"], meta["px_height"]
    parts = [
        f'<div class="floor" data-floor="{index}" data-name="{_e(_floor_name(index))}"{" hidden" if hidden else ""}>',
        f'<svg class="map" viewBox="0 0 {width} {height}" role="img" aria-label="{_e(alt)}">',
        f'<use class="bg" href="#map-img-{index}"/>',
    ]
    parts.extend(_render_heat([s for s in heat if s["floor"] == index], meta, top))
    parts.extend(_render_route(runs, index, meta))
    parts.append('<g class="strong" aria-hidden="true"></g>')
    parts.extend(_render_pins(kept, dropped, markers, index, meta, id_to_rank))
    parts.append(
        '<g class="dot" visibility="hidden" aria-hidden="true"><circle class="halo" r="46"/><circle class="core" r="20"/></g>'
    )
    parts.extend(["</svg>", "</div>"])
    return parts


def _floor_switch_css(floor_count):
    if floor_count < 2:
        return ""
    return "".join(
        f'.ovmap:has(.ov-floor[value="{i}"]:checked) .floor[data-floor="{i}"] {{ display: grid; }}'
        for i in range(floor_count)
    )


# The first-screen map: every moment pinned, the whole route faint, the
# counts as the legend, the floor switch and the "Time spent" switch.
# Radios and a checkbox, so it works without script.
def _render_overview_map(data, floors, kept, dropped, markers, id_to_rank):
    words = LABELS["overview"]
    route = data["route"]
    summary = data.get("summary") or {}
    runs = _route_runs(route["points"])
    first_floor = route["points"][0][3] if route["points"] else 0
    top = max((spot["seconds"] for spot in route["heat"]), default=0) or 1
    parts = [f'<figure class="ovmap{" multi" if len(floors) > 1 else ""}" id="ovmap">']
    tools = []
    if len(floors) > 1:
        radios = "".join(
            f'<label><input type="radio" class="ov-floor" name="ov-floor" value="{i}"{" checked" if i == first_floor else ""}>'
            f'<span>{_e(_floor_name(i))}</span></label>'
            for i in range(len(floors))
        )
        tools.append(f'<span class="floors-switch" role="radiogroup" aria-label="{_e(words["floor_switch"])}">{radios}</span>')
    if route["heat"]:
        tools.append(f'<label class="heatsw"><input type="checkbox" id="heat"><span>{_e(words["heat"])}</span></label>')
    if tools:
        parts.append(f'<div class="tools">{"".join(tools)}</div>')
    for index, (meta, _uri) in enumerate(floors):
        alt = words["alt"].format(floor=_floor_name(index).lower())
        parts.extend(_render_floor(index, meta, runs, kept, dropped, markers, id_to_rank, alt, False, route["heat"], top))
    legend = []
    counts = summary.get("counts") or {}
    for kind in KIND_ORDER:
        count = counts.get(kind, 0)
        if count:
            info = _kind(kind)
            legend.append(f'<li><span class="mk k-{info["class"]}">{_shape(kind)}</span><b>{count}</b> {_e(info["label"])}</li>')
    if dropped:
        legend.append(
            f'<li><span class="mk hollow k-{_kind(dropped[0]["kind"])["class"]}">{_shape(dropped[0]["kind"])}</span>'
            f'{_dropped_link(_counts(data, kept, dropped)[1])}</li>'
        )
    if summary.get("lost_s"):
        legend.append(f'<li class="lost">{_e(words["lost"].format(time=_mss(summary["lost_s"])))}</li>')
    if legend:
        parts.append(f'<ul class="legend">{"".join(legend)}</ul>')
    if route["heat"]:
        parts.append(f'<p class="heatnote">{_e(words["heat_note"])}</p>')
    parts.append("</figure>")
    return parts


def _first_rank(moments, id_to_rank):
    for moment in moments:
        if moment in id_to_rank:
            return id_to_rank[moment]
    return None


def _render_across(cross_player, id_to_rank):
    across = LABELS["across"]
    parts = [
        '<section class="across" aria-labelledby="across">',
        f'<h2 id="across">{_e(across["title"])}</h2>',
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
                    text = across["chip_moments"].format(label=player["label"], n=len(player["moments"]))
                else:
                    text = across["chip_time"].format(label=player["label"], time=_mss(player["worst_t"]))
                if target is not None:
                    chips.append(f'<a class="chip you" href="#m{target}">{_e(text)}</a>')
                else:
                    chips.append(f'<span class="chip you">{_e(text)}</span>')
            else:
                text = across["chip_time"].format(label=player["label"], time=_mss(player["worst_t"]))
                chips.append(f'<span class="chip">{_e(text)}</span>')
        parts.append(
            f'<li class="group"><h3>{_e(group["place"])}</h3>'
            f'<p><span class="who">{_e(who)}</span></p>'
            f'<div class="chips">{"".join(chips)}</div></li>'
        )
    parts.extend(["</ul>", f'<p class="note">{_e(across["note"])}</p>', "</section>"])
    return parts


# The times and words the script reads off a moment's row: its time, its
# clip span, its floor, the place it prints, and whether Play the
# session stops there (an unplanned kept moment).
def _data_attrs(finding, label, place):
    attrs = [
        f'data-id="{_e(finding["id"])}"',
        f'data-t="{finding["time_s"]}"',
        f'data-kind="{_kind(finding["kind"])["class"]}"',
        f'data-label="{_e(label)}"',
        f'data-place="{_e(place)}"',
    ]
    if finding.get("rank") is not None:
        attrs.append(f'data-rank="{finding["rank"]}"')
    if finding["check"]["verdict"] == "keep" and _is_stop(finding):
        attrs.append("data-stop")
    clip = finding.get("clip")
    if clip is not None:
        attrs.append(f'data-clip="{clip["start_s"]} {clip["end_s"]}"')
    at = finding.get("at")
    if at is not None:
        attrs.append(f'data-floor="{at["floor"]}"')
    return " ".join(attrs)


# A still frame: the clip paused on the moment's own frame, no controls;
# a button that opens Watch on this moment. The seek is the one time the
# page derives: the moment's time inside its clip.
def _render_still(finding, aria):
    clip = finding.get("clip")
    glyph = f'<span class="playglyph" aria-hidden="true">{PLAY_GLYPH}</span>'
    if clip is None:
        return f'<button type="button" class="watchbtn none" data-open="{_e(finding["id"])}" aria-label="{_e(aria)}">{glyph}</button>'
    at = max(0.0, min(finding["time_s"] - clip["start_s"], clip["end_s"] - clip["start_s"]))
    caption = LABELS["card"]["clip"].format(span=_span(clip["start_s"], clip["end_s"]))
    return (
        f'<button type="button" class="watchbtn" data-open="{_e(finding["id"])}" aria-label="{_e(aria)}">'
        f'<video class="still" muted playsinline preload="metadata" tabindex="-1" aria-hidden="true" '
        f'src="{_e(clip["path"])}#t={at:.1f}"></video>{glyph}'
        f'<span class="cliplen">{_e(caption)}</span></button>'
    )


def _render_head_row(finding, mark):
    info = _kind(finding["kind"])
    end_s = finding.get("end_s")
    time = _span(finding["time_s"], end_s) if end_s is not None else _mss(finding["time_s"])
    return [
        mark,
        f'<span class="time">{time}</span>',
        f'<span class="badge"><span class="k k-{info["class"]}" aria-hidden="true"></span>{_e(info["label"])}</span>',
    ]


def _render_moment(finding, markers_by_moment, floor_count):
    info = _kind(finding["kind"])
    check = finding["check"]
    rank = finding["rank"]
    words = LABELS["card"]
    attrs = _data_attrs(finding, _pin_words(finding), _place(finding, floor_count))
    css = f'm {info["class"]}' + (" soft" if _is_soft(finding) else "")
    head = _render_head_row(finding, f'<span class="mk k-{info["class"]}">{_shape(finding["kind"], f"<b>{rank}</b>")}</span>')
    intent = _render_intent(check.get("friction"))
    if intent:
        head.append(intent)
    body = [f'<p class="mhead">{"".join(head)}</p>', f'<p class="summary">{_e(finding["summary"])}</p>']
    quote = finding.get("quote")
    if quote is None:
        body.append(f'<p class="quote none">{_e(words["no_quote"])}</p>')
    else:
        body.append(f'<p class="quote">"{_e(quote)}"</p>')
    if check.get("cause"):
        body.append(f'<p class="cause"><span class="lab">{_e(words["cause"])}</span>{_breakable(check["cause"])}</p>')
    fric = _render_friction_line(check)
    if fric:
        body.append(fric)
    for marker in markers_by_moment.get(finding["id"], []):
        body.append(f'<p class="f9line"><b>{_e(LABELS["words"]["f9"])}</b>{_e(words["f9"].format(time=_mss(marker["t"])))}</p>')
    facts = []
    if finding.get("game_state") is not None:
        facts.append(f'<dt>{_e(words["game"])}</dt><dd>{_breakable(finding["game_state"])}</dd>')
    facts.append(f'<dt>{_e(words["checker"])}</dt><dd>{_breakable(check["note"])}</dd>')
    body.append(f'<details class="more"><summary>{_e(words["more"])}</summary><dl class="facts">{"".join(facts)}</dl></details>')
    return (
        f'<article class="{css}" id="m{rank}" {attrs}>'
        f'{_render_still(finding, words["watch"].format(rank=rank))}'
        f'<div class="body">{"".join(body)}</div></article>'
    )


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
        attempt_key = (beat.get("attempt"), beat.get("attempt_start_s"), beat.get("attempt_end_s"))
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
    return (float("inf") if attempt is None else attempt, float("inf") if start_s is None else start_s)


def _group_span(findings):
    start = min(_first_set((f.get("beat") or {}).get("attempt_start_s"), f["time_s"]) for f in findings)
    end = max(_first_set((f.get("beat") or {}).get("attempt_end_s"), _moment_end(f)) for f in findings)
    return start, end


# The kept moments under their place headings (Area, Puzzle, Attempt),
# the headings in time order, the moments by time inside.
def _render_moments(kept, markers_by_moment, floor_count):
    words = LABELS["moments"]
    out = [
        '<section class="moments" aria-labelledby="moments">',
        f'<h2 id="moments">{_e(words["title"])}</h2>',
        f'<p class="sub">{_e(words["sub"])}</p>',
    ]
    groups = _kept_groups(kept)
    groups.sort(key=lambda g: (_group_span(g["findings"])[0], min(f["rank"] for f in g["findings"])))
    for index, group in enumerate(groups, start=1):
        beat = group["findings"][0].get("beat") or {}
        attempt_keys = sorted(group["attempts"], key=_attempt_sort_key)
        start, end = _group_span(group["findings"])
        if any(key[0] is not None for key in attempt_keys):
            note = words["attempt_note"].format(
                attempts=_plural(len(attempt_keys), LABELS["words"]["attempt"]),
                moments=_plural(len(group["findings"]), LABELS["words"]["moment"]),
                span=_span(start, end),
            )
        else:
            note = words["note"].format(moments=_plural(len(group["findings"]), LABELS["words"]["moment"]), span=_span(start, end))
        out.append(f'<section class="moments-group" aria-labelledby="g{index}">')
        out.append(f'<h3 id="g{index}">{_e(_group_title(beat))}<span class="note">{_e(note)}</span></h3>')
        for attempt_key in attempt_keys:
            findings = sorted(group["attempts"][attempt_key], key=lambda f: (f["time_s"], f["rank"]))
            attempt = attempt_key[0]
            if attempt is not None:
                attempt_start = _first_set(attempt_key[1], min(f["time_s"] for f in findings))
                attempt_end = _first_set(attempt_key[2], max(_moment_end(f) for f in findings))
                out.append(f'<h4>{_e(words["attempt"].format(n=attempt, span=_span(attempt_start, attempt_end)))}</h4>')
            out.extend(_render_moment(f, markers_by_moment, floor_count) for f in findings)
        out.append("</section>")
    out.append("</section>")
    return out


def _render_dropped(dropped, floor_count, dropped_count):
    words = LABELS["card"]
    items = []
    for finding in dropped:
        info = _kind(finding["kind"])
        attrs = _data_attrs(finding, _drop_words(finding), _place(finding, floor_count))
        head = _render_head_row(finding, f'<span class="mk hollow k-{info["class"]}">{_shape(finding["kind"])}</span>')
        head.append(f'<span class="intent dropped">{_e(words["dropped_tag"])}</span>')
        body = [f'<p class="mhead">{"".join(head)}</p>', f'<p class="summary">{_e(finding["summary"])}</p>']
        reason = finding["check"].get("note")
        if reason:
            body.append(f'<p class="reason">{_breakable(LABELS["dropped"]["reason"].format(note=reason))}</p>')
        if finding.get("game_state") is not None:
            body.append(
                f'<details class="more"><summary>{_e(words["more"])}</summary><dl class="facts">'
                f'<dt>{_e(words["game"])}</dt><dd>{_breakable(finding["game_state"])}</dd></dl></details>'
            )
        items.append(
            f'<article class="d" id="d-{_e(finding["id"])}" {attrs}>'
            f'{_render_still(finding, words["watch_dropped"].format(time=_mss(finding["time_s"])))}'
            f'<div class="body">{"".join(body)}</div></article>'
        )
    return [
        '<section class="dropped" aria-labelledby="dropped">',
        f'<h2 id="dropped">{_e(LABELS["dropped"]["title"])}</h2>',
        f'<p class="sub">{_e(LABELS["dropped"]["note"].format(n=dropped_count))}</p>',
        *items,
        "</section>",
    ]


def _render_footer(data):
    words = LABELS["foot"]
    session = data["session"]
    models = _models(data["findings"])
    parts = ['<footer class="foot">']
    if models:
        parts.append(f"<p>{_e(words['pipeline'].format(model=models))}</p>")
    parts.append(f'<p class="mono">{_e(words["recording"])}: {_e(session["recording"])}</p>')
    parts.append("</footer>")
    return parts


# ----------------------------------------------------------------- Watch

def _pct(time_s, duration_s):
    if duration_s <= 0:
        return 0.0
    return max(0.0, min(100.0, time_s / duration_s * 100))


# Rows for marks along the timeline: a mark takes the first row whose
# last mark is at least STRIP_GAP of the recording earlier; when every
# row is full it shares the row with the most room.
def _stack(times, duration_s):
    lasts = []
    rows = []
    for time_s in times:
        share = time_s / duration_s if duration_s > 0 else 0.0
        row = next((i for i, last in enumerate(lasts) if share - last >= STRIP_GAP), None)
        if row is None and len(lasts) < STRIP_ROWS:
            lasts.append(share)
            row = len(lasts) - 1
        elif row is None:
            row = min(range(len(lasts)), key=lambda i: lasts[i])
        lasts[row] = share
        rows.append(row)
    return rows


# The timeline under Watch: the rooms the player was in (puzzle visits
# in the puzzle colour), the kept moments by rank and the dropped
# candidates hollow, a time axis. The script draws the map time on it
# and reads a click as a map time.
def _render_timeline(data, kept, dropped):
    duration = data["session"]["duration_s"]
    words = LABELS["watch"]
    parts = [f'<div class="tl" id="tl" aria-label="{_e(words["tl_aria"])}">', '<div class="track" id="track">', '<div class="r-rooms">']
    for zone in data.get("zones") or []:
        end = zone["end_s"] if zone["end_s"] is not None else duration
        if end - zone["start_s"] < 0.5:
            continue
        left, right = _pct(zone["start_s"], duration), _pct(end, duration)
        span = _span(max(0.0, zone["start_s"]), end)
        if zone["puzzle"]:
            title = words["room_bar_puzzle"].format(room=zone["zone"], puzzle=zone["puzzle"], span=span)
        else:
            title = words["room_bar"].format(room=zone["zone"], span=span)
        text = _e(zone["zone"]) if right - left >= BAR_LABEL_MIN_PCT else ""
        parts.append(
            f'<span class="room{" puzzle" if zone["puzzle"] else ""}" data-s="{zone["start_s"]}" data-e="{end}" '
            f'data-room="{_e(zone["zone"])}" style="left:{left:.2f}%;width:{right - left:.2f}%" title="{_e(title)}">{text}</span>'
        )
    parts.append("</div>")
    marks = sorted(kept + dropped, key=lambda f: (f["time_s"], f["rank"] or 0))
    rows = _stack([f["time_s"] for f in marks], duration)
    parts.append(f'<div class="r-marks" style="--rows:{max(rows) + 1 if rows else 1}">')
    for finding, row in zip(marks, rows):
        info = _kind(finding["kind"])
        is_drop = finding["check"]["verdict"] == "drop"
        css = f'tm k-{info["class"]}' + (" hollow" if is_drop else (" soft" if _is_soft(finding) else ""))
        label = _drop_words(finding) if is_drop else _pin_words(finding)
        body = _shape(finding["kind"], "" if is_drop else f"<b>{finding['rank']}</b>")
        parts.append(
            f'<button type="button" class="{css}" data-open="{_e(finding["id"])}" '
            f'style="left:{_pct(finding["time_s"], duration):.2f}%;--row:{row}" '
            f'aria-label="{_e(label)}" title="{_e(label)}">{body}</button>'
        )
    parts.append("</div>")
    step = next((s for s in TICK_STEPS if duration / s <= 12), TICK_STEPS[-1])
    ticks = "".join(
        f'<span style="left:{_pct(t, duration):.2f}%">{_mss(t)}</span>' for t in range(0, int(duration) + 1, step)
    )
    parts.append(f'<div class="r-axis" aria-hidden="true">{ticks}</div>')
    parts.append('<div class="past" id="past"></div><div class="cursor" id="cursor"></div>')
    parts.append("</div></div>")
    return parts


def _render_watch(data, floors, kept, dropped, markers, id_to_rank):
    words = LABELS["watch"]
    session = data["session"]
    attrs = " ".join(
        f'data-w-{key.replace("_", "-")}="{_e(words[key])}"'
        for key in ("count", "count_dropped", "where", "between", "off_map", "up_next", "up_next_head", "walking", "end", "paused", "before", "so_far")
    )
    parts = [
        f'<div class="watch" id="watch" role="dialog" aria-modal="true" aria-labelledby="w-count" '
        f'data-duration="{session["duration_s"]}" {attrs} hidden>',
        '<div class="bar">',
        f'<button type="button" class="back" id="back"><svg class="ic" viewBox="0 0 12 12" aria-hidden="true"><path d="M7.5 1.5L3 6l4.5 4.5"/></svg>{_e(words["back"])}</button>',
        '<p class="count" id="w-count" aria-live="polite"></p>',
        '<div class="nav">',
        f'<button type="button" id="prev">{_e(words["previous"])}</button>',
        f'<button type="button" id="play" class="primary" aria-pressed="false"><span class="when-paused">{_e(words["play"])}</span><span class="when-playing">{_e(words["pause"])}</span></button>',
        f'<button type="button" id="next">{_e(words["next"])}</button>',
        "</div></div>",
        '<div class="main">',
        f'<section class="screen" aria-label="{_e(words["clip"])}">',
        '<div class="clipbox">',
        '<video id="clip" controls playsinline preload="auto"></video>',
        '<div class="travel" id="travel" hidden><p class="big" id="travel-time"></p><p class="what" id="travel-what"></p><div class="prog"><i id="travel-prog"></i></div></div>',
        "</div>",
        '<div class="caption" id="caption"></div>',
        "</section>",
        '<aside class="side">',
        '<div class="context"><p class="where" id="where"></p><p class="lastev" id="lastev"></p>',
        f'<p class="offmap" id="offmap" hidden>{_e(words["off_map_note"])}</p>',
    ]
    if len(floors) > 1:
        buttons = "".join(
            f'<button type="button" data-show-floor="{i}" aria-pressed="{"true" if i == 0 else "false"}">{_e(_floor_name(i))}</button>'
            for i in range(len(floors))
        )
        parts.append(f'<p class="floors-switch" role="group" aria-label="{_e(words["floor_switch"])}">{buttons}</p>')
    parts.append("</div>")
    if floors:
        runs = _route_runs(data["route"]["points"])
        parts.append('<div class="maps">')
        for index, (meta, _uri) in enumerate(floors):
            alt = words["map_alt"].format(floor=_floor_name(index).lower())
            parts.extend(_render_floor(index, meta, runs, kept, dropped, markers, id_to_rank, alt, index > 0))
        parts.append("</div>")
    parts.append(f'<div class="before"><h2 id="before-h">{_e(words["before"])}</h2><ol id="before" class="events">')
    for event in data.get("events") or []:
        parts.append(f'<li data-t="{event["t"]}" hidden><time>{_mss(event["t"])}</time>{_e(event["label"])}</li>')
    parts.append(f'</ol><p class="none" id="before-none">{_e(words["none_yet"])}</p></div>')
    parts.append("</aside></div>")
    parts.extend(_render_timeline(data, kept, dropped))
    parts.append(f'<p class="vh" id="keys">{_e(words["keys"])}</p>')
    parts.append("</div>")
    return parts


# One state drives Watch: the current moment and the map time. The script
# reads every time, floor and word from the page and the data-attributes
# the renderer wrote, fills the caption with clones of the moment's own
# nodes, and computes no finding, time, position or count: it only
# compares the file's times with the map time.
SCRIPT = r"""
(function () {
  "use strict";
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var NS = "http://www.w3.org/2000/svg";
  var read = $("#read"), watch = $("#watch");
  document.documentElement.classList.add("js");
  $$("[data-needs-script]").forEach(function (el) { el.removeAttribute("hidden"); });
  if (!watch) return;
  var video = $("#clip"), travel = $("#travel"), caption = $("#caption"), count = $("#w-count");
  var where = $("#where"), lastev = $("#lastev"), offmap = $("#offmap"), beforeHead = $("#before-h");
  var prevBtn = $("#prev"), nextBtn = $("#next");
  var playBtn = $("#play"), cursor = $("#cursor"), past = $("#past"), track = $("#track");
  var beforeNone = $("#before-none");
  var duration = +watch.dataset.duration, SPEED = 10, TRAIL = 30, EVENTS_SHOWN = 4;
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var W = {};
  Object.keys(watch.dataset).forEach(function (k) { if (k.indexOf("w") === 0 && k.length > 1) W[k.charAt(1).toLowerCase() + k.slice(2)] = watch.dataset[k]; });

  function mss(t) { t = Math.max(0, Math.floor(t)); return Math.floor(t / 60) + ":" + ("0" + (t % 60)).slice(-2); }
  function fmt(s, o) { return s.replace(/\{(\w+)\}/g, function (m, k) { return k in o ? o[k] : m; }); }
  function el(tag, cls, text) { var n = document.createElement(tag); if (cls) n.className = cls; if (text != null) n.textContent = text; return n; }

  // The floors, their drawn size, and the route, read back from the drawn polylines.
  var floors = $$(".maps .floor", watch);
  var boxes = floors.map(function (f) { var vb = $("svg", f).getAttribute("viewBox").split(" "); return { w: +vb[2], h: +vb[3] }; });
  function offMap(p) { var b = boxes[p.floor]; return !b || p.x < 0 || p.y < 0 || p.x > b.w || p.y > b.h; }
  var points = [];
  $$(".route polyline.line", watch).forEach(function (line) {
    var floor = +line.closest(".floor").dataset.floor;
    var xy = line.getAttribute("points").split(" ");
    line.dataset.t.split(" ").forEach(function (t, i) { var p = xy[i].split(","); points.push({ t: +t, x: +p[0], y: +p[1], floor: floor }); });
  });
  points.sort(function (a, b) { return a.t - b.t; });
  var rooms = $$(".room", watch).map(function (r) { return { s: +r.dataset.s, e: +r.dataset.e, name: r.dataset.room }; });
  var events = $$("#before li", watch);

  // Records: one per moment and dropped candidate, read off the document.
  var recs = $$("article.m, article.d", read).map(function (a) {
    var still = $("video.still", a);
    return { el: a, id: a.dataset.id, key: a.id, rank: a.dataset.rank ? +a.dataset.rank : null, t: +a.dataset.t,
      clip: a.dataset.clip ? a.dataset.clip.split(" ").map(Number) : null,
      src: still ? still.getAttribute("src").replace(/#t=.*$/, "") : null,
      floor: a.dataset.floor ? +a.dataset.floor : 0, dropped: a.classList.contains("d"),
      stop: a.hasAttribute("data-stop"), place: a.dataset.place,
      off: !!$('.maps .pin.edge[data-open="' + a.dataset.id + '"]', watch) };
  });
  var byId = {}; recs.forEach(function (r) { byId[r.id] = r; });
  var kept = recs.filter(function (r) { return !r.dropped; }).sort(function (a, b) { return a.t - b.t; });
  var stops = kept.filter(function (r) { return r.stop; });
  var allDropped = recs.filter(function (r) { return r.dropped; }).sort(function (a, b) { return a.t - b.t; });

  var S = { open: false, cur: null, t: points.length ? points[0].t : 0, playing: false, travelling: false, nextRec: null, from: 0,
    opener: null, y: 0, floor: 0, hold: null, holdFloor: null, raf: null, last: 0 };

  // --- the map ---
  // The last route point at or before t: the dot never sits between points.
  function pointAt(t) {
    if (!points.length) return null;
    var lo = 0, hi = points.length - 1;
    if (t <= points[0].t) return points[0];
    while (hi - lo > 1) { var mid = (lo + hi) >> 1; if (points[mid].t <= t) lo = mid; else hi = mid; }
    return points[hi].t <= t ? points[hi] : points[lo];
  }
  function showFloor(i) {
    S.floor = i;
    floors.forEach(function (f, j) { f.hidden = j !== i; });
    $$("[data-show-floor]", watch).forEach(function (b) { b.setAttribute("aria-pressed", String(+b.dataset.showFloor === i)); });
  }
  function polyline(cls, pts) { var n = document.createElementNS(NS, "polyline"); if (cls) n.setAttribute("class", cls); n.setAttribute("points", pts.join(" ")); return n; }
  function drawMap() {
    var p = pointAt(S.t);
    // The floor follows the player; a floor the reader picked holds until the player changes floor.
    if (p) {
      if (S.hold !== null && p.floor !== S.holdFloor) { S.hold = null; }
      var want = S.hold !== null ? S.hold : p.floor;
      if (want !== S.floor) showFloor(want);
    }
    floors.forEach(function (f, i) {
      var dot = $(".dot", f), strong = $(".strong", f);
      while (strong.firstChild) strong.removeChild(strong.firstChild);
      if (!p || p.floor !== i) { dot.setAttribute("visibility", "hidden"); return; }
      dot.setAttribute("visibility", "visible");
      dot.setAttribute("transform", "translate(" + p.x + " " + p.y + ")");
      // The last 30 s on this floor, one run per stay: a floor change starts a new run.
      var runs = [], pts = [];
      for (var k = 0; k < points.length; k++) {
        var q = points[k];
        if (q.t < S.t - TRAIL || q.t > S.t) continue;
        if (q.floor !== i) { if (pts.length) runs.push(pts); pts = []; continue; }
        pts.push(q.x + "," + q.y);
      }
      if (pts.length) runs.push(pts);
      runs.forEach(function (run) { if (run.length > 1) strong.appendChild(polyline("case", run)); });
      runs.forEach(function (run) { if (run.length > 1) strong.appendChild(polyline("", run)); });
    });
    $$(".pin.cur, .tm.cur", watch).forEach(function (n) { n.classList.remove("cur"); });
    if (S.cur) $$('[data-open="' + S.cur.id + '"]', watch).forEach(function (n) { n.classList.add("cur"); });
  }
  function roomAt(t) {
    for (var i = rooms.length - 1; i >= 0; i--) if (rooms[i].s <= t && t <= rooms[i].e) return rooms[i].name;
    return "";
  }
  function drawContext() {
    var p = pointAt(S.t), room = roomAt(S.t);
    var floorName = floors.length > 1 && p ? floors[p.floor].dataset.name : "";
    // A player outside the drawn map is said to be there, never put in a room.
    if (p && offMap(p)) room = W.offMap;
    if (S.cur && !S.travelling && S.cur.place) where.textContent = S.cur.place;
    else if (!rooms.length && !room) where.textContent = floorName;
    else if (floorName) where.textContent = fmt(W.where, { room: room || W.between, floor: floorName });
    else where.textContent = room || W.between;
    offmap.hidden = !(S.cur && S.cur.off);
    beforeHead.textContent = S.travelling ? W.soFar : W.before;
    // The latest event at or before the map time goes in the line above the map;
    // the list holds the ones before it, so no event shows twice.
    var shown = 0, last = null;
    for (var i = events.length - 1; i >= 0; i--) {
      var t = +events[i].dataset.t, past = t <= S.t;
      if (past && last === null) { last = i; events[i].hidden = true; continue; }
      var ok = past && shown < EVENTS_SHOWN;
      events[i].hidden = !ok;
      if (ok) shown++;
    }
    beforeNone.hidden = shown > 0;
    // The latest game event at or before the map time, however old: its time says when.
    while (lastev.firstChild) lastev.removeChild(lastev.firstChild);
    if (last !== null) {
      var tm = el("time", "", mss(+events[last].dataset.t)); lastev.appendChild(tm);
      lastev.appendChild(document.createTextNode(events[last].lastChild.textContent));
    }
  }
  function drawTimeline() {
    var pct = Math.max(0, Math.min(100, 100 * S.t / Math.max(1, duration)));
    past.style.width = pct + "%";
    cursor.style.left = pct + "%";
    cursor.classList.toggle("on", S.open);
  }
  function render() { drawMap(); drawContext(); drawTimeline(); }

  // --- the caption: clones of the moment's own nodes ---
  // While the session walks, the same column previews the next stop: its
  // head, quote, summary and likely cause under "Up next".
  function fillCaption(r, preview) {
    while (caption.firstChild) caption.removeChild(caption.firstChild);
    var sel = preview ? ".body > .mhead, .body > .summary, .body > .quote, .body > .cause" : ".body > *";
    if (preview) caption.appendChild(el("p", "upnext", W.upNextHead));
    $$(sel, r.el).forEach(function (n) { caption.appendChild(n.cloneNode(true)); });
    var head = $(".mhead", caption);
    if (preview) { if (head && r.place) head.appendChild(el("span", "place", r.place)); return; }
    if (r.dropped) { var d = $("details", caption); if (d) d.open = true; }
    var list = r.dropped ? allDropped : kept;
    var at = list.indexOf(r);
    count.textContent = fmt(r.dropped ? W.countDropped : W.count, { n: at + 1, of: list.length });
    prevBtn.disabled = at <= 0; nextBtn.disabled = at >= list.length - 1;
  }

  // --- the one state ---
  function setPlayingFlag(on) { S.playing = on; watch.classList.toggle("playing", on); playBtn.setAttribute("aria-pressed", String(on)); }
  // Opening remembers where the reader was. Focus lands on Play, so Space
  // plays or pauses and never presses Back.
  function openWatch(opener) {
    if (S.open) return;
    S.open = true; S.opener = opener || null; S.y = window.scrollY;
    watch.hidden = false; read.inert = true; read.setAttribute("aria-hidden", "true");
    document.documentElement.classList.add("watching");
    playBtn.focus();
  }
  // Back returns to where the reader came from: a problem, a badge, a pin or
  // Play on the first screen gets that scroll position and focus back; a still
  // in the list, a chip or a link lands on the current moment's row.
  function closeWatch() {
    stopTravel(); video.pause(); setPlayingFlag(false);
    watch.hidden = true; read.inert = false; read.removeAttribute("aria-hidden");
    document.documentElement.classList.remove("watching");
    S.open = false;
    if (history.replaceState) history.replaceState(null, "", location.pathname + location.search);
    var fromFirst = S.opener && read.contains(S.opener) && !S.opener.closest("article.m, article.d");
    if (fromFirst) {
      window.scrollTo(0, S.y);
      S.opener.focus({ preventScroll: true });
    } else if (S.cur && S.cur.el) {
      S.cur.el.scrollIntoView({ block: "center", behavior: reduce ? "auto" : "smooth" });
      var b = $(".watchbtn", S.cur.el); (b || S.opener || document.body).focus({ preventScroll: true });
    } else if (S.opener) S.opener.focus();
  }
  function showMoment(r, autoplay) {
    stopTravel();
    S.cur = r; S.travelling = false; watch.classList.remove("travelling"); travel.hidden = true;
    S.t = r.clip ? r.clip[0] : r.t; S.hold = null;
    fillCaption(r, false); video.controls = true;
    if (history.replaceState) history.replaceState(null, "", "#" + r.key);
    if (r.src) {
      // A seek on a clip that just loaded makes both engines pause it a moment later.
      if (video.getAttribute("src") !== r.src) { video.setAttribute("src", r.src); video.load(); }
      else if (video.currentTime > 0) video.currentTime = 0;
      if (autoplay) { var p = video.play(); if (p && p.catch) p.catch(function () {}); }
    } else { video.removeAttribute("src"); video.load(); }
    render();
  }
  // The next unplanned moment after a time: the only kind Play stops at.
  function nextStop(t) { for (var i = 0; i < stops.length; i++) if (stops[i].t > t + 0.01) return stops[i]; return null; }
  function target(r) { return r.clip ? r.clip[0] : r.t; }
  function startTravel(fromT, afterT) {
    var next = nextStop(afterT != null ? afterT : fromT);
    if (next && S.playing && target(next) <= fromT) { showMoment(next, true); return; }
    S.t = fromT; S.from = fromT; S.cur = null; S.travelling = true; S.nextRec = next;
    watch.classList.add("travelling"); video.pause(); video.controls = false;
    travel.hidden = false;
    if (next) fillCaption(next, true); else while (caption.firstChild) caption.removeChild(caption.firstChild);
    count.textContent = next ? W.walking : W.end;
    prevBtn.disabled = false; nextBtn.disabled = !next;
    if (next && next.src) { video.setAttribute("src", next.src); video.load(); }
    else { video.removeAttribute("src"); video.load(); }
    S.last = 0;
    drawTravel(); render();
    if (S.playing) S.raf = requestAnimationFrame(tick);
  }
  function stopTravel() { if (S.raf) cancelAnimationFrame(S.raf); S.raf = null; }
  function drawTravel() {
    $("#travel-time").textContent = mss(S.t);
    var what = $("#travel-what"), prog = $("#travel-prog");
    if (!S.nextRec) { what.textContent = W.end; prog.style.width = "100%"; return; }
    var to = target(S.nextRec);
    what.textContent = (S.playing ? "" : W.paused + " ") + fmt(W.upNext, { rank: S.nextRec.rank, time: mss(S.nextRec.t), place: S.nextRec.place });
    prog.style.width = Math.max(0, Math.min(100, 100 * (S.t - S.from) / Math.max(1, to - S.from))) + "%";
  }
  function tick(now) {
    if (!S.playing || !S.travelling) return;
    if (S.last) S.t += (now - S.last) / 1000 * SPEED;
    S.last = now;
    var to = S.nextRec ? target(S.nextRec) : duration;
    if (S.t >= to) {
      if (S.nextRec) { showMoment(S.nextRec, true); return; }
      S.t = duration; setPlayingFlag(false); drawTravel(); render(); return;
    }
    drawTravel(); render();
    S.raf = requestAnimationFrame(tick);
  }
  function setPlaying(on) {
    setPlayingFlag(on);
    if (S.travelling) { stopTravel(); if (on) { S.last = 0; S.raf = requestAnimationFrame(tick); } drawTravel(); }
    else if (S.cur && S.cur.src) { if (on) { var p = video.play(); if (p && p.catch) p.catch(function () {}); } else video.pause(); }
    else if (on) startTravel(S.t);
  }
  // Previous and Next step through the list the counter names: every kept
  // moment, by design or not, or every dropped candidate from one of those.
  // Between moments they step through the kept ones by time.
  function step(dir) {
    var list = S.cur && S.cur.dropped ? allDropped : kept;
    if (!list.length) return;
    var i;
    if (S.cur) i = list.indexOf(S.cur) + dir;
    else { i = 0; while (i < list.length && list[i].t <= S.t) i++; if (dir < 0) i--; }
    i = Math.max(0, Math.min(list.length - 1, i));
    showMoment(list[i], S.playing);
  }

  // --- the video drives the map: map time = clip.start_s + currentTime ---
  // An event counts only for the clip showMoment loaded: a late event from the
  // clip before it (Next while it ran) must not move the session on.
  function loadedClip() { return !!(S.cur && S.cur.src && !S.travelling && video.currentSrc === new URL(S.cur.src, location.href).href); }
  function follow() { if (loadedClip() && S.cur.clip) { S.t = S.cur.clip[0] + video.currentTime; render(); } }
  video.addEventListener("timeupdate", follow);
  // A seek within the first moments of a freshly loaded clip makes both engines
  // pause it; when the reader meant to keep playing, resume.
  video.addEventListener("seeked", function () {
    follow();
    if (S.playing && loadedClip() && video.paused && !video.ended) { var p = video.play(); if (p && p.catch) p.catch(function () {}); }
  });
  video.addEventListener("play", function () { if (loadedClip()) setPlayingFlag(true); });
  video.addEventListener("pause", function () {
    var atEnd = video.ended || (video.duration && video.currentTime >= video.duration - 0.1);
    if (loadedClip() && !atEnd) setPlayingFlag(false);
  });
  video.addEventListener("ended", function () {
    if (!video.ended || !loadedClip()) return;
    if (S.playing) startTravel(S.cur.clip ? S.cur.clip[1] : S.cur.t, S.cur.t);
    else setPlayingFlag(false);
  });

  // --- wiring ---
  document.addEventListener("click", function (e) {
    var open = e.target.closest("[data-open]");
    if (open) { var r = byId[open.dataset.open]; if (!r) return; e.preventDefault(); openWatch(open); showMoment(r, true); return; }
    var fb = e.target.closest("[data-show-floor]");
    if (fb) { var p = pointAt(S.t); S.hold = +fb.dataset.showFloor; S.holdFloor = p ? p.floor : S.hold; showFloor(S.hold); return; }
    var art = e.target.closest("article.m, article.d");
    if (art && !e.target.closest("details, a, button")) { var r2 = byId[art.dataset.id]; if (r2) { openWatch($(".watchbtn", art)); showMoment(r2, true); } }
  });
  var playSession = $("#play-session");
  if (playSession) playSession.addEventListener("click", function (e) { openWatch(e.currentTarget); setPlayingFlag(true); startTravel(points.length ? points[0].t : 0); });
  $("#back").addEventListener("click", closeWatch);
  $("#prev").addEventListener("click", function () { step(-1); });
  $("#next").addEventListener("click", function () { step(1); });
  playBtn.addEventListener("click", function () { setPlaying(!S.playing); });
  track.addEventListener("click", function (e) {
    if (e.target.closest(".tm")) return;
    var box = track.getBoundingClientRect();
    var t = Math.max(0, Math.min(duration, (e.clientX - box.left) / box.width * duration));
    var wasPlaying = S.playing; setPlayingFlag(false);
    startTravel(t); if (wasPlaying) setPlaying(true);
  });
  // Capture phase: the clip's own controls keep Escape otherwise. Arrows and
  // Space inside the clip, a field or a button keep their native meaning.
  document.addEventListener("keydown", function (e) {
    if (!S.open) return;
    var inControl = e.target.closest("video, select, input, textarea");
    if (e.key === "Escape") { e.preventDefault(); closeWatch(); }
    else if (inControl) return;
    else if (e.key === "ArrowRight") { e.preventDefault(); step(1); }
    else if (e.key === "ArrowLeft") { e.preventDefault(); step(-1); }
    else if (e.key === " " && !e.target.closest("button, summary, a")) { e.preventDefault(); setPlaying(!S.playing); }
  }, true);
  // A #m3 or #d-f12 link opens Watch on that moment, paused; an empty hash closes it.
  function openFromHash() {
    var hash = decodeURIComponent(location.hash.replace(/^#/, ""));
    var a0 = hash && document.getElementById(hash), r0 = a0 && byId[a0.dataset.id];
    if (r0) { openWatch(null); showMoment(r0, false); }
    else if (!hash && S.open) closeWatch();
  }
  window.addEventListener("hashchange", openFromHash);
  openFromHash();
})();
"""


def render_html(data, maps_dir=None):
    """Return the full HTML page for a checked findings dict."""
    session = data["session"]
    kept = sorted((f for f in data["findings"] if f["check"]["verdict"] == "keep"), key=lambda f: (f["time_s"], f["rank"]))
    dropped = sorted((f for f in data["findings"] if f["check"]["verdict"] == "drop"), key=lambda f: f["time_s"])
    summary = data.get("summary")
    markers = data.get("markers") or []
    id_to_rank = {f["id"]: f["rank"] for f in kept}
    by_id = {f["id"]: f for f in kept}
    markers_by_moment = {}
    for marker in markers:
        if marker.get("moment"):
            markers_by_moment.setdefault(marker["moment"], []).append(marker)

    route = data.get("route")
    floors = []
    if route is not None:
        loaded, missing = _load_floors(route["maps"], maps_dir)
        if loaded is None:
            print(LABELS["warning"].format(map=repr(missing)), file=sys.stderr)
        else:
            floors = loaded
    floor_count = len(floors)

    title = _e(LABELS["title"].format(id=session["id"]))
    if session.get("player"):
        title += ", " + _e(session["player"])
    images = "".join(
        f'<image id="map-img-{i}" href="{uri}" x="0" y="0" width="{meta["px_width"]}" height="{meta["px_height"]}"/>'
        for i, (meta, uri) in enumerate(floors)
    )
    parts = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{title}</title>",
        "<style>",
        STYLE.strip(),
        _floor_switch_css(floor_count),
        "</style>",
        "</head>",
        "<body>",
        f'<svg class="vh" width="0" height="0" aria-hidden="true" focusable="false"><defs>{SVG_DEFS}{images}</defs></svg>',
        '<div class="read" id="read">',
    ]
    parts.extend(_render_header(data, kept, dropped))
    problems = (summary or {}).get("problems") or []
    if problems or floors:
        parts.append('<div class="first">')
        if problems:
            parts.extend(_render_problems(problems, by_id))
        if floors:
            parts.extend(_render_overview_map(data, floors, kept, dropped, markers, id_to_rank))
        parts.append("</div>")
    if data.get("cross_player"):
        parts.extend(_render_across(data["cross_player"], id_to_rank))
    parts.extend(_render_moments(kept, markers_by_moment, floor_count))
    if dropped:
        parts.extend(_render_dropped(dropped, floor_count, _counts(data, kept, dropped)[1]))
    parts.extend(_render_footer(data))
    parts.append("</div>")
    parts.extend(_render_watch(data, floors, kept, dropped, markers, id_to_rank))
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
