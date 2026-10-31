"""Render a findings.json file as one self-contained HTML page.

The page only renders what the file holds. It computes nothing beyond
formatting seconds as m:ss, converting a world point to image pixels
with each floor's map JSON, placing times along the session strip, and
the structural counts a group needs. Section and card order come from
the file's times and beat fields: sections by their start, cards by
time, ties by rank.

Layout (task 30, from mockup B): the write-up scrolls on the left and
the map pane stays on the right, with every floor of the scene side by
side. One inline script drives the pane: the moment in the middle of
the screen lights its pin and its visit on the map, Play runs the whole
session, a playing clip moves the dot, and the session strip and the
slider set the map's time. It only shows, hides and highlights what the
page already drew, by the times the file holds (written into data-
attributes), and moves a dot to an existing route point. It never makes
a finding, a time, a position or a count. Without script the page shows
every moment with its clip and every floor with the whole route; the
heat map view is a CSS switch (:has), so it needs no script.

All page wording lives in LABELS, so changing a string never means
touching the markup.
"""

from __future__ import annotations

import argparse
import base64
import html
import json
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
        "time_lost": "Time lost to being stuck or confused",
        "kept": "Moments checked against the video and the event log",
        "of": "of {duration}",
        "count_note": "{kept} kept, {dropped} dropped",
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
        "lost": "{time} lost",
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
        "checker": "Checker",
        "no_quote": "No spoken comment.",
        "f9": "Player pressed F9 at {time}",
        "num_pin": "Show moment {rank} on the map",
        "pin": "Moment {rank}, {kind}, {time}",
        # Proposals (Claude Opus 5.5, 2026-11-01, from mockup B), not Sasha's wording.
        "clip": "Clip {span}",
        "sync": "Map follows the clip",
    },
    # Proposals (Claude Opus 5.5, 2026-11-01, from mockup B), not Sasha's wording.
    "strip": {
        "aria": "Session strip: rooms the player was in, time on the upper floor, kept moments and dropped candidates, over the whole recording.",
        "moments": "Moments",
        "dropped": "Dropped",
        "bar": "{room} {span}",
        "bar_puzzle": "{room}, {puzzle} {span}",
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
        "hint": "Scroll the moments to light each one on the map. Play runs the whole session.",
        "drop_pin": "Dropped, {kind}, {time}",
    },
    # Proposals (Claude Opus 5.5 plan, task 25, 2026-10-28), not Sasha's wording.
    # "view", "trail", "readout_window" and "show_all" are proposals by
    # Claude Opus 5.5 (Cursor, task 26, 2026-10-28). The window lengths
    # come from Sasha's "10 sec, 15, 30, etc." (Cursor chat,
    # 2026-10-28); 60 is the brief's.
    "timeline": {
        "view": "Map view",
        "view_trail": "Timeline",
        "view_heat": "Heat map",
        "play": "Play",
        "pause": "Pause",
        "slider": "Time in the recording",
        "readout": "{time} of {duration}",
        "readout_window": "{start}-{time} of {duration}",
        "trail": "Trail",
        "trail_all": "From start",
        "trail_last": "{n} s",
        "windows": (10, 15, 30, 60),
        "legend": "Where the player is at the slider's time",
        "show_all": "Show all moments",
        # Proposals (Claude Opus 5.5, 2026-11-01, from mockup B), not Sasha's wording.
        "events_near": "Game events in this moment's visit and clip",
        "events_up_to": "Game events up to {time}",
        "events_none": "No game events in this span.",
    },
    # Proposals by Claude Opus 5.5 (Cursor, task 26, 2026-10-28), not Sasha's wording.
    "heat": {
        "title": "Time spent, whole session",
        "low": "Less",
        "high": "More",
        "note": "Each number is the time spent at that spot. The route and pins are in the timeline view.",
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

/* Two columns: the write-up scrolls, the map pane stays. */
.page { --floor-h: max(420px, calc(100vh - 236px)); --pane-w: calc(var(--floor-h) * var(--ars) + (var(--floors) - 1) * 10px);
  display: grid; grid-template-columns: minmax(0, 1fr) var(--pane-w); gap: var(--s5); padding: 0 var(--s5); max-width: 1880px; margin: 0 auto; }
.page.solo { grid-template-columns: minmax(0, 1fr); max-width: 1120px; }
.col { padding: var(--s5) 0 50vh; min-width: 0; }
.page.solo .col { padding-bottom: var(--s6); }

/* header */
.meta { display: flex; flex-wrap: wrap; gap: var(--s1) var(--s5); margin: 0 0 var(--s4); padding: 0; list-style: none; color: var(--ink2); font-size: var(--fs-s); }
.meta b { color: var(--muted); font-weight: 600; margin-right: var(--s1); }
.verdict { font-size: var(--fs-m); font-weight: 600; margin: 0 0 var(--s4); padding: var(--s3) var(--s4); background: var(--surface); border: 1px solid var(--line); border-left: 6px solid var(--accent); border-radius: 6px; }

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

/* problems */
.problems ol { list-style: none; margin: 0; padding: 0; display: grid; gap: var(--s2); }
.problem { background: var(--surface); border: 1px solid var(--line); border-left: 6px solid var(--k-stuck); border-radius: 6px; padding: var(--s2) var(--s4); display: grid; gap: 2px; }
.problem a.place { font-weight: 700; color: var(--ink); text-decoration: none; font-size: var(--fs-m); }
.problem a.place:hover { text-decoration: underline; }
.problem .facts-line { display: flex; flex-wrap: wrap; align-items: center; gap: var(--s1) var(--s4); font-size: var(--fs-s); color: var(--ink2); }
.problem .facts-line > span { display: inline-flex; align-items: center; gap: var(--s2); }
.problem .mks { display: inline-flex; flex-wrap: wrap; gap: 2px; }

/* rank markers: strip, problems, card numbers */
.mk { position: relative; display: inline-grid; place-items: center; width: 22px; height: 22px; flex: none; color: #0b1020; text-decoration: none; }
.mk svg.sh { position: absolute; inset: 0; }
.mk b { position: relative; font: 700 11px var(--font); }
.k-surprised.mk b, .k-bug.mk b { font-size: 10px; }
.k-bug.mk b { top: 2px; }
a.mk:hover svg.sh use, a.mk:focus-visible svg.sh use { stroke: var(--ink); stroke-width: 2.4; }

/* at a glance */
.tiles { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--s3); margin: 0 0 var(--s3); }
.tile { background: var(--surface); border: 1px solid var(--line); border-radius: 6px; padding: var(--s2) var(--s4); }
.tile .n { font-size: var(--fs-l); font-weight: 700; line-height: 1.25; font-variant-numeric: tabular-nums; }
.tile .n .note { margin-left: var(--s1); font-weight: 600; }
.tile .l { color: var(--ink2); font-size: var(--fs-s); }
.kinds { list-style: none; margin: 0 0 var(--s4); padding: 0; display: flex; flex-wrap: wrap; gap: var(--s2) var(--s5); font-size: var(--fs-s); color: var(--ink2); }
.kinds li { display: inline-flex; align-items: center; gap: 6px; }
.kinds b { color: var(--ink); font-size: var(--fs-b); }
.kinds .zero, .kinds .zero b { color: var(--muted); }
.kinds .zero .k { opacity: .45; }

/* session strip */
.strip { display: grid; grid-template-columns: max-content minmax(0, 1fr); gap: 0 var(--s3); background: var(--surface); border: 1px solid var(--line); border-radius: 6px; padding: var(--s3); margin: 0 0 var(--s4); }
.labs, .tracks { display: flex; flex-direction: column; gap: 4px; }
.labs span { height: 12px; line-height: 12px; font-size: 11px; font-weight: 600; color: var(--ink2); max-width: 150px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.labs span.r-marks, .labs span.r-drops { display: flex; align-items: center; }
.tracks { position: relative; cursor: crosshair; touch-action: none; }
.track { position: relative; height: 12px; border-radius: 2px; background: var(--sunk); }
.r-floor { margin-top: 4px; }
.r-drops { height: 18px !important; }
.track.r-marks, .track.r-drops { background: none; }
.bar { position: absolute; top: 0; bottom: 0; min-width: 2px; border-radius: 2px; background: var(--bar); }
.bar.puzzle { background: var(--bar-puzzle); }
.bar.up { background: var(--muted); opacity: .55; }
.track .mk { position: absolute; margin-left: -11px; }
.track.r-drops .mk { width: 14px; height: 14px; margin-left: -7px; top: 2px; }
.axis { position: relative; height: 16px; font: 11px var(--mono); color: var(--muted); }
.axis span { position: absolute; top: 2px; transform: translateX(-50%); white-space: nowrap; }
.axis span:first-child { transform: none; }
.tracks .band { position: absolute; top: 0; bottom: 20px; background: var(--accent); opacity: .18; pointer-events: none; min-width: 2px; }
.tracks .cursor { position: absolute; top: 0; bottom: 20px; width: 2px; margin-left: -1px; background: var(--accent); pointer-events: none; }

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
.card, .drop { position: relative; display: grid; grid-template-columns: minmax(0, 1fr); grid-template-areas: "head" "main" "clip" "facts"; column-gap: var(--s4); margin: 0 0 var(--s3); padding: var(--s3) var(--s4); background: var(--surface); border: 1px solid var(--line); border-left: 6px solid var(--c); border-radius: 8px; scroll-margin-top: 30vh; transition: border-color .2s, box-shadow .2s; }
.card.stuck { --c: var(--k-stuck); } .card.confused { --c: var(--k-confused); }
.card.surprised { --c: var(--k-surprised); } .card.bug { --c: var(--k-bug); }
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
.facts { display: grid; grid-template-columns: max-content 1fr; gap: var(--s1) var(--s3); margin: 0; font-size: var(--fs-s); color: var(--ink2); }
.facts dt { color: var(--muted); font-weight: 600; }
.facts dd { margin: 0; }
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

/* dropped */
.drop { --c: var(--line); border-style: dashed; border-left-style: solid; background: transparent; }
.drop .summary { font-size: var(--fs-b); color: var(--ink2); }
.reason { margin: 0; font-size: var(--fs-s); color: var(--ink); padding: var(--s1) var(--s2); background: var(--sunk); border-radius: 6px; }
.drop .num-pin { width: 18px; height: 18px; }

/* the pane */
.pane { position: sticky; top: 0; height: 100vh; min-height: 640px; display: flex; flex-direction: column; gap: 8px; padding: 12px 0; }
.toolbar { display: flex; align-items: center; gap: var(--s2) var(--s3); flex-wrap: wrap; min-height: 34px; }
.seg { display: inline-flex; border: 1px solid var(--line); border-radius: 8px; background: var(--surface); padding: 2px; }
.seg label { position: relative; }
.seg input { position: absolute; inset: 0; margin: 0; opacity: 0; cursor: pointer; }
.seg span { display: block; padding: 3px 12px; border-radius: 6px; font-size: var(--fs-s); font-weight: 600; color: var(--ink2); }
.seg input:checked + span { background: var(--accent); color: var(--on-accent); }
.seg input:focus-visible + span { outline: 3px solid var(--accent); outline-offset: 2px; }
.btn { font: 600 var(--fs-s) var(--font); color: var(--ink); background: var(--surface); border: 1px solid var(--line); border-radius: 8px; padding: 4px 12px; cursor: pointer; display: inline-flex; align-items: center; gap: 6px; }
.btn:hover { border-color: var(--accent); }
.btn svg { width: 10px; height: 10px; fill: currentColor; }
.trail { font-size: var(--fs-s); color: var(--ink2); display: inline-flex; gap: 6px; align-items: center; white-space: nowrap; }
.trail select { font: inherit; color: var(--ink); background: var(--surface); border: 1px solid var(--line); border-radius: 6px; padding: 2px 4px; }
.readout { font-family: var(--mono); font-size: var(--fs-s); color: var(--ink2); white-space: nowrap; margin-left: auto; font-variant-numeric: tabular-nums; }
.scrub input { display: block; width: 100%; margin: 0; accent-color: var(--accent); }
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
.pin text { font: 700 40px var(--font); fill: #0b1020; text-anchor: middle; dominant-baseline: central; pointer-events: none; }
.pin.f9 use { fill: #0b1020; stroke: #ffffff; stroke-width: 1.2; stroke-dasharray: 2.4 1.6; }
.pin.f9 text { fill: #ffffff; font-size: 28px; }
.pin:focus { outline: none; }
.pin:focus-visible use, .pin:hover use, html:not(.js) .pin:target use { stroke: #8da2ff; stroke-width: 3; }
.pin .ring { fill: none; stroke: #ffffff; stroke-width: 6; opacity: 0; }
.pin.is-quiet .scale { opacity: .5; }
.pin.is-later { visibility: hidden; }
.pin.is-focus .scale { transform: scale(1.5); }
.pin.is-focus .ring { opacity: 1; }
.dot .halo { fill: #8da2ff; opacity: .35; }
.dot .core { fill: #8da2ff; stroke: #ffffff; stroke-width: 7; }
.halo-text { font: 700 40px var(--font); fill: #ffffff; stroke: #0a0d14; stroke-width: 9; paint-order: stroke; text-anchor: middle; }

/* heat map view: the plan muted, the whole-session heat on top, nothing else */
.map .heat, .box-heat { display: none; }
.pane:has(.view-heat:checked) .map .heat { display: inline; }
.pane:has(.view-heat:checked) .box-heat { display: block; }
.pane:has(.view-heat:checked) :is(.trail-layer, .box-whole, .box-now) { display: none; }
.pane:has(.view-heat:checked) :is(.play, .trail, .scrub) { visibility: hidden; }
.pane:has(.view-heat:checked) .bg { filter: grayscale(1) brightness(.5); }
.ramp { height: 10px; border-radius: 3px; max-width: 220px; }
.ramp-ends { display: flex; justify-content: space-between; max-width: 220px; color: var(--ink2); margin: 2px 0 var(--s1); }

/* the moment box */
.box { flex: 1 1 auto; min-height: 96px; overflow: auto; background: var(--surface); border: 1px solid var(--line); border-radius: 8px; padding: var(--s2) var(--s3); font-size: var(--fs-s); }
.box p { margin: 0 0 4px; }
.box .legend { display: flex; flex-wrap: wrap; gap: 4px var(--s4); list-style: none; margin: 0 0 4px; padding: 0; color: var(--ink2); }
.box .legend li { display: inline-flex; align-items: center; gap: 6px; }
.pane[data-mode="whole"] .box-now, .pane:not([data-mode="whole"]) .box-whole { display: none; }
.box-now .head { display: flex; flex-wrap: wrap; align-items: center; gap: 4px var(--s2); font-weight: 700; font-size: var(--fs-b); }
.box-now .head .where { font-weight: 400; color: var(--ink2); }
.box-now .evh { display: flex; align-items: center; gap: var(--s3); color: var(--ink2); font-weight: 600; }
.box-now .evh .btn { padding: 1px 8px; }
.pane:not([data-mode="session"]) .showall { display: none; }
.events { list-style: none; margin: 0; padding: 0; columns: 2; column-gap: var(--s5); }
.events li { break-inside: avoid; display: flex; gap: var(--s2); color: var(--ink2); padding: 1px 4px; border-radius: 4px; transition: background-color 1.2s, opacity .2s; }
.events time { color: var(--muted); flex: none; min-width: 3.2em; font-family: var(--mono); }
.events li.later { opacity: .45; }
.events li.fresh { background: var(--accent-tint); color: var(--ink); transition: none; }

@media (prefers-reduced-motion: no-preference) { html { scroll-behavior: smooth; } }
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { transition: none !important; animation: none !important; } }
@media (max-width: 1100px) {
  .page { grid-template-columns: minmax(0, 1fr); --floor-h: min(70vh, calc((100vw - 2 * var(--s5) - 20px - (var(--floors) - 1) * 10px) / var(--ars))); }
  .pane { order: -1; position: static; height: auto; min-height: 0; }
  .col { padding-bottom: var(--s6); }
  .box { max-height: 140px; }
}
@media print {
  body { background: #fff; color: #000; }
  .page { grid-template-columns: 1fr; }
  .pane { position: static; height: auto; }
  .card, .drop, .tile, .problem { break-inside: avoid; }
  .clip, .toolbar, .scrub, .box, .strip { display: none; }
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

# Map drawing sizes, in map image pixels (about 48 per metre).
PIN_R = 40
DROP_R = 28
F9_R = 34

# The session strip: two markers closer than this share of the
# recording go on separate rows, up to STRIP_ROWS rows.
STRIP_GAP = 0.035
STRIP_ROWS = 3
STRIP_ROW_PX = 22
TICK_STEPS = (30, 60, 120, 300, 600, 1200, 1800, 3600)


def _e(value):
    return html.escape(str(value), quote=True)


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
        "<header>",
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
            f'<div class="l">{_e(tiles["time_lost"])}</div></div>'
        )
    count_note = tiles["count_note"].format(
        kept=summary["kept"], dropped=summary["dropped"]
    )
    parts.append(
        f'<div class="tile"><div class="n">{summary["kept"]}'
        f'<span class="note">{_e(count_note)}</span></div>'
        f'<div class="l">{_e(tiles["kept"])}</div></div>'
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


# The session strip: one row per room, one per upper floor, the kept
# moments by rank, the dropped candidates, and a time axis. The script
# draws the map time on it and reads clicks and drags as a map time.
def _render_strip(data, kept, dropped, floor_count):
    duration = data["session"]["duration_s"]
    words = LABELS["strip"]
    labs = []
    tracks = []

    rooms = {}
    for zone in data.get("zones") or []:
        rooms.setdefault(zone["zone"], []).append(zone)
    for room, visits in rooms.items():
        bars = []
        for zone in visits:
            end = zone["end_s"] if zone["end_s"] is not None else duration
            span = _span(max(0.0, zone["start_s"]), end)
            if zone["puzzle"]:
                title = words["bar_puzzle"].format(room=room, puzzle=zone["puzzle"], span=span)
            else:
                title = words["bar"].format(room=room, span=span)
            css = "bar puzzle" if zone["puzzle"] else "bar"
            bars.append(_bar(zone["start_s"], end, duration, css, title))
        labs.append(f'<span title="{_e(room)}">{_e(room)}</span>')
        tracks.append(f'<div class="track">{"".join(bars)}</div>')

    route = data.get("route") or {}
    for floor in range(1, floor_count):
        name = _floor_name(floor)
        bars = [
            _bar(span["start_s"], span["end_s"], duration, "bar up",
                 words["bar"].format(room=name, span=_span(span["start_s"], span["end_s"])))
            for span in route.get("floor_spans", [])
            if span["floor"] == floor
        ]
        labs.append(f'<span class="r-floor">{_e(name)}</span>')
        tracks.append(f'<div class="track r-floor">{"".join(bars)}</div>')

    by_time = sorted(kept, key=lambda f: (f["time_s"], f["rank"]))
    rows, row_count = _stack([f["time_s"] for f in by_time], duration)
    height = row_count * STRIP_ROW_PX
    marks = []
    for finding, row in zip(by_time, rows):
        info = _kind(finding["kind"])
        label = _pin_words(finding)
        marks.append(
            f'<a class="mk k-{info["class"]}" href="#m{finding["rank"]}" '
            f'style="left:{_pct(finding["time_s"], duration):.2f}%;top:{row * STRIP_ROW_PX}px" '
            f'aria-label="{_e(label)}" title="{_e(label)}">'
            f'{_shape(finding["kind"], f"<b>{finding['rank']}</b>")}</a>'
        )
    labs.append(f'<span class="r-marks" style="height:{height}px">{_e(words["moments"])}</span>')
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
        labs.append(f'<span class="r-drops">{_e(words["dropped"])}</span>')
        tracks.append(f'<div class="track r-drops">{"".join(drops)}</div>')

    step = next((s for s in TICK_STEPS if duration / s <= 10), TICK_STEPS[-1])
    ticks = []
    tick = 0
    while tick <= duration:
        ticks.append(f'<span style="left:{_pct(tick, duration):.2f}%">{_mss(tick)}</span>')
        tick += step
    labs.append("<span></span>")
    tracks.append(f'<div class="axis" aria-hidden="true">{"".join(ticks)}</div>')

    return [
        f'<section class="strip" aria-label="{_e(words["aria"])}">',
        f'<div class="labs">{"".join(labs)}</div>',
        f'<div class="tracks" data-duration="{duration}">',
        *tracks,
        '<div class="band" hidden></div><div class="band" hidden></div>'
        '<div class="cursor" hidden></div>',
        "</div>",
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
        dy = 8 if info["class"] == "bug" else 2
        parts.append(
            f'<a class="pin k-{info["class"]}" id="pin-m{rank}" href="#m{rank}" '
            f'data-t="{finding["time_s"]}" aria-label="{_e(_pin_words(finding))}" '
            f'transform="translate({x:.1f} {y:.1f})">'
            f'<g class="scale"><circle class="ring" r="{PIN_R + 14}"/>'
            f'<use href="#sh-{info["class"]}" x="-{PIN_R}" y="-{PIN_R}" '
            f'width="{2 * PIN_R}" height="{2 * PIN_R}"/><text y="{dy}">{rank}</text></g></a>'
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
        '<circle class="halo" r="46"/><circle class="core" r="20"/></g>'
    )
    parts.extend(["</g>", "</svg>"])
    if floor_count > 1:
        parts.append(f'<figcaption class="floor-label">{_e(_floor_name(index))}</figcaption>')
    parts.append("</figure>")
    return parts


def _render_toolbar(duration_s, has_heat):
    words = LABELS["timeline"]
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
    options = [f'<option value="0">{_e(words["trail_all"])}</option>'] + [
        f'<option value="{n}">{_e(words["trail_last"].format(n=n))}</option>'
        for n in words["windows"]
    ]
    readout = words["readout"].format(time=_mss(total), duration=_mss(total))
    parts.append(
        f'<button type="button" class="btn play" data-needs-script hidden aria-pressed="false" '
        f'data-play="{_e(words["play"])}" data-pause="{_e(words["pause"])}">'
        '<svg viewBox="0 0 10 10" aria-hidden="true"><path d="M1 0 L10 5 L1 10z"/></svg>'
        f'<span>{_e(words["play"])}</span></button>'
        f'<label class="trail" data-needs-script hidden>{_e(words["trail"])} '
        f'<select>{"".join(options)}</select></label>'
        f'<output class="readout" data-needs-script hidden data-readout="{_e(words["readout"])}" '
        f'data-readout-window="{_e(words["readout_window"])}">{_e(readout)}</output>'
    )
    parts.append("</div>")
    parts.append(
        '<div class="scrub" data-needs-script hidden>'
        f'<input type="range" min="0" max="{total}" step="1" value="{total}" '
        f'aria-label="{_e(words["slider"])}"></div>'
    )
    return parts


# Under the floors: the legend for the whole route, the heat legend for
# the heat view, and the current moment with its game events.
def _render_box(data, has_heat, has_markers, has_drop_pins):
    words = LABELS["timeline"]
    map_words = LABELS["map"]
    kinds = "".join(
        f'<li><span class="k k-{_kind(kind)["class"]}" aria-hidden="true"></span>'
        f'{_e(_kind(kind)["label"])}</li>'
        for kind in KIND_ORDER
    )
    parts = [
        '<div class="box">',
        '<div class="box-whole">',
        f'<ul class="legend">{kinds}</ul>',
        f'<p class="note">{_e(map_words["route"])}</p>',
    ]
    if has_drop_pins:
        parts.append(f'<p class="note">{_e(map_words["dropped"])}</p>')
    if has_markers:
        parts.append(f'<p class="note">{_e(map_words["f9"])}</p>')
    parts.append(f'<p data-needs-script hidden>{_e(map_words["hint"])}</p>')
    parts.append("</div>")
    if has_heat:
        heat = LABELS["heat"]
        stops = ", ".join(HEAT_RAMP)
        parts.append(
            '<div class="box-heat">'
            f'<p><b>{_e(heat["title"])}</b></p>'
            f'<div class="ramp" style="background:linear-gradient(90deg, {stops})" aria-hidden="true"></div>'
            f'<div class="ramp-ends"><span>{_e(heat["low"])}</span><span>{_e(heat["high"])}</span></div>'
            f'<p class="note">{_e(heat["note"])}</p>'
            "</div>"
        )
    events = "".join(
        f'<li data-t="{event["t"]}" hidden><time>{_mss(event["t"])}</time>'
        f'<span>{_e(event["label"])}</span></li>'
        for event in data.get("events") or []
    )
    parts.append(
        f'<div class="box-now" data-needs-script hidden data-near="{_e(words["events_near"])}" '
        f'data-up-to="{_e(words["events_up_to"])}" aria-live="off">'
        '<p class="head"><span class="k" aria-hidden="true"></span><span class="what"></span>'
        '<span class="where"></span></p>'
        '<p class="evh"><span></span>'
        f'<button type="button" class="btn showall">{_e(words["show_all"])}</button></p>'
        f'<ol class="events">{events}</ol>'
        f'<p class="none note" hidden>{_e(words["events_none"])}</p>'
        "</div>"
    )
    parts.append("</div>")
    return parts


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
    parts.extend(_render_toolbar(duration, has_heat))
    parts.append('<div class="floors">')
    for index, (meta, data_uri) in enumerate(floors):
        parts.extend(
            _render_floor(data, index, meta, data_uri, runs, len(floors), kept, dropped, markers, id_to_rank, top)
        )
    parts.append("</div>")
    has_drop_pins = any(f.get("at") is not None for f in dropped)
    parts.extend(_render_box(data, has_heat, bool(markers), has_drop_pins))
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
    parts = [f'<article class="card {info["class"]}" id="m{rank}" {attrs}>']

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
    if finding.get("game_state") is not None:
        facts.append(f'<dt>{LABELS["card"]["game"]}</dt><dd>{_e(finding["game_state"])}</dd>')
    facts.append(f'<dt>{LABELS["card"]["checker"]}</dt><dd>{_e(check["note"])}</dd>')
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
            f'<span class="k k-{info["class"]}" aria-hidden="true"></span>{_e(info["label"])}</span></div>'
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


# Which moment is current, the map's time, the dot, the strong route.
# It reads every time, floor and word from the page and the data-
# attributes the renderer wrote, and computes no finding, time, position
# or count: it only compares the file's times with the map time.
SCRIPT = r"""
(function () {
  "use strict";
  var pane = document.querySelector(".pane");
  if (!pane) return;
  document.documentElement.classList.add("js");
  var SPEED = 10;
  var NS = "http://www.w3.org/2000/svg";
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)");
  var DUR = Number(pane.getAttribute("data-duration"));
  function each(list, fn) { Array.prototype.forEach.call(list, fn); }
  function nums(el, name) { var v = el.getAttribute(name); return v ? v.split(" ").map(Number) : null; }
  function mss(s) { s = Math.max(0, Math.floor(s)); return Math.floor(s / 60) + ":" + ("0" + (s % 60)).slice(-2); }
  function svg(tag, attrs) { var n = document.createElementNS(NS, tag); for (var k in attrs) n.setAttribute(k, attrs[k]); return n; }

  // Floors and the route, read back from the drawn polylines.
  var FLOORS = [];
  each(pane.querySelectorAll(".floor"), function (fig) {
    FLOORS[Number(fig.getAttribute("data-floor"))] = { fig: fig, strong: fig.querySelector(".strong"), dot: fig.querySelector(".dot") };
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

  // Kept cards and dropped rows, in page order.
  var RECS = [], BY_ID = {};
  each(document.querySelectorAll(".card[data-t], .drop[data-t]"), function (el) {
    var clip = nums(el, "data-clip");
    var r = {
      el: el, id: el.id, t: Number(el.getAttribute("data-t")), kept: el.classList.contains("card"),
      floor: el.hasAttribute("data-floor") ? Number(el.getAttribute("data-floor")) : null,
      spans: [nums(el, "data-visit"), clip].filter(Boolean),
      clipStart: clip ? clip[0] : null, video: el.querySelector("video"),
      pin: document.getElementById("pin-" + el.id)
    };
    RECS.push(r);
    BY_ID[el.id] = r;
  });
  var KEPT = RECS.filter(function (r) { return r.kept; });

  var playBtn = pane.querySelector(".play");
  var trailSel = pane.querySelector(".trail select");
  var readout = pane.querySelector(".readout");
  var slider = pane.querySelector(".scrub input");
  var heatInput = pane.querySelector(".view-heat");
  var box = pane.querySelector(".box-now");
  var evItems = box.querySelectorAll(".events li");
  var tracks = document.querySelector(".strip .tracks");
  var bands = tracks ? tracks.querySelectorAll(".band") : [];
  var cursor = tracks ? tracks.querySelector(".cursor") : null;

  var S = { mode: "whole", cur: null, t: DUR, trail: 0, playing: false, clip: null, clipT: null, lock: 0, hold: 0 };
  function heatOn() { return !!(heatInput && heatInput.checked); }
  function inSpans(spans, t) { for (var i = 0; i < spans.length; i++) if (t >= spans[i][0] && t <= spans[i][1]) return true; return false; }
  function lastPassed(t) { var best = null; KEPT.forEach(function (r) { if (r.t <= t && (!best || r.t >= best.t)) best = r; }); return best; }

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

  function render() {
    var heat = heatOn();
    pane.setAttribute("data-mode", heat ? "heat" : S.mode);
    FLOORS.forEach(function (F) { F.strong.replaceChildren(); });
    var active = null, lit = null, dotT = null, lo = -Infinity;
    if (!heat && S.mode === "moment") {
      var r = S.cur;
      drawRoute(function (t) { return inSpans(r.spans, t); }, false, 4);
      active = r; lit = r.floor;
      if (S.clipT != null) dotT = S.clipT;
    } else if (!heat && S.mode === "session") {
      if (S.trail > 0) { lo = S.t - S.trail; drawRoute(function (t) { return t <= lo; }, true, 0); }
      drawRoute(function (t) { return t > lo && t <= S.t; }, false, S.trail > 0 ? 3 : 8);
      active = lastPassed(S.t); dotT = S.t;
    }
    RECS.forEach(function (r) {
      if (!r.pin) return;
      r.pin.classList.toggle("is-focus", r === active);
      r.pin.classList.toggle("is-quiet", S.mode === "moment" && r !== active);
      r.pin.classList.toggle("is-later", S.mode === "session" && r.t > S.t);
      if (r === active && r.pin !== r.pin.parentNode.lastElementChild) r.pin.parentNode.appendChild(r.pin);
    });
    var p = dotT == null ? null : pointAt(dotT);
    FLOORS.forEach(function (F, fl) {
      var show = !!p && p.floor === fl;
      F.dot.setAttribute("visibility", show ? "visible" : "hidden");
      if (show) F.dot.setAttribute("transform", "translate(" + p.xy[0] + " " + p.xy[1] + ")");
    });
    if (p) lit = p.floor;
    FLOORS.forEach(function (F, fl) {
      F.fig.classList.toggle("lit", lit === fl && FLOORS.length > 1);
      F.fig.classList.toggle("quiet", lit != null && lit !== fl);
    });
    RECS.forEach(function (r) {
      r.el.classList.toggle("is-active", r === active && !heat);
      r.el.classList.toggle("is-playing", r === S.clip);
    });
    renderTime(heat, active, lo);
    renderBox(heat, active, lo);
  }

  function place(el, a, b) { el.style.left = (a / DUR * 100) + "%"; if (b != null) el.style.width = Math.max(0, (b - a) / DUR * 100) + "%"; }
  function renderTime(heat, active, lo) {
    var t = DUR, spans = [];
    if (!heat && S.mode === "session") { t = S.t; spans = [[Math.max(0, lo), S.t]]; }
    else if (!heat && S.mode === "moment") { t = S.clipT != null ? S.clipT : S.cur.t; spans = S.cur.spans; }
    var text = (!heat && S.mode === "session" && S.trail > 0 ? readout.getAttribute("data-readout-window") : readout.getAttribute("data-readout"))
      .replace("{start}", mss(Math.max(0, lo))).replace("{time}", mss(t)).replace("{duration}", mss(DUR));
    readout.textContent = text;
    slider.value = Math.floor(t);
    slider.setAttribute("aria-valuetext", text);
    each(bands, function (band, i) { band.hidden = !spans[i]; if (spans[i]) place(band, spans[i][0], spans[i][1]); });
    if (cursor) { cursor.hidden = heat || S.mode === "whole"; place(cursor, t); }
  }

  // The moment box: the current moment and its game events, or, in a
  // session, the last moment passed and the events up to the map time.
  function renderBox(heat, active, lo) {
    if (heat || S.mode === "whole") return;
    var head = box.querySelector(".head");
    head.querySelector(".k").className = "k" + (active ? " k-" + active.el.getAttribute("data-kind") : "");
    head.querySelector(".what").textContent = active ? active.el.getAttribute("data-label") : "";
    head.querySelector(".where").textContent = active ? (active.el.getAttribute("data-place") || "") : "";
    box.querySelector(".evh span").textContent = S.mode === "session"
      ? box.getAttribute("data-up-to").replace("{time}", mss(S.t)) : box.getAttribute("data-near");
    var shown = 0;
    each(evItems, function (li) {
      var t = Number(li.getAttribute("data-t"));
      var on = S.mode === "session" ? t <= S.t : inSpans(S.cur.spans, t);
      li.hidden = !on;
      li.classList.toggle("later", on && S.mode === "moment" && S.clipT != null && t > S.clipT);
      li.classList.toggle("fresh", S.mode === "session" && S.playing && S.t - t < 1.5 * SPEED);
      if (on) shown++;
    });
    box.querySelector(".none").hidden = shown > 0;
    if (S.mode === "session") { var list = pane.querySelector(".box"); list.scrollTop = list.scrollHeight; }
  }

  // ---- Interactions ----
  function setPlaying(on) {
    S.playing = on;
    playBtn.querySelector("span").textContent = playBtn.getAttribute(on ? "data-pause" : "data-play");
    playBtn.querySelector("path").setAttribute("d", on ? "M1 0 H4 V10 H1z M6 0 H9 V10 H6z" : "M1 0 L10 5 L1 10z");
    playBtn.setAttribute("aria-pressed", on ? "true" : "false");
  }
  function pauseClips(except) { RECS.forEach(function (r) { if (r.video && r !== except && !r.video.paused) r.video.pause(); }); }
  function showTrail() { if (heatOn()) pane.querySelector("input[name=view][value=trail]").checked = true; }
  function setCur(r) {
    if (S.mode === "moment" && S.cur === r) return;
    S.mode = "moment"; S.cur = r; S.clipT = null;
    render();
  }
  // From a pin, the strip, a problem or a number: light it, and bring its card to the middle.
  function goTo(r, scroll) {
    pauseClips(null); setPlaying(false); showTrail();
    S.mode = "moment"; S.cur = r; S.clip = null; S.clipT = null;
    render();
    if (history.replaceState) history.replaceState(null, "", "#" + r.id);
    if (scroll) {
      S.lock = performance.now() + (reduce.matches ? 150 : 900);
      r.el.scrollIntoView({ block: "center", behavior: reduce.matches ? "auto" : "smooth" });
    }
  }
  function toSession(t) {
    pauseClips(null); showTrail();
    S.mode = "session"; S.cur = null; S.clip = null; S.clipT = null;
    S.t = Math.max(0, Math.min(DUR, t)); S.hold = performance.now() + 1500;
    render();
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
  function onScroll() {
    var now = performance.now();
    if (heatOn() || S.clip || now < S.lock) return;
    if (S.mode === "session" && (S.playing || now < S.hold)) return;
    var r = centered();
    if (r) { setCur(r); return; }
    if (S.mode !== "whole") { S.mode = "whole"; S.cur = null; S.clipT = null; render(); }
  }
  var ticking = false;
  window.addEventListener("scroll", function () {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(function () { ticking = false; onScroll(); });
  }, { passive: true });

  document.addEventListener("click", function (e) {
    var a = e.target.closest && e.target.closest("a[href^='#']");
    if (!a || e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey) return;
    var id = a.getAttribute("href").slice(1), scroll = true;
    if (id.indexOf("pin-") === 0) { id = id.slice(4); scroll = false; }
    var r = BY_ID[id];
    if (!r) return;
    e.preventDefault();
    goTo(r, scroll);
  });

  var last = 0, lastPoint = null;
  function tick(stamp) {
    if (!S.playing) return;
    S.t = Math.min(DUR, S.t + SPEED * (stamp - last) / 1000);
    last = stamp;
    var p = pointAt(S.t);
    if (p !== lastPoint) { lastPoint = p; render(); } else renderTime(false, null, S.trail > 0 ? S.t - S.trail : -Infinity);
    if (S.t >= DUR) setPlaying(false); else requestAnimationFrame(tick);
  }
  playBtn.addEventListener("click", function () {
    if (S.playing) { setPlaying(false); S.hold = performance.now() + 400; render(); return; }
    pauseClips(null); showTrail();
    if (S.mode !== "session" || S.t >= DUR) S.t = 0;
    S.mode = "session"; S.cur = null; S.clip = null; S.clipT = null;
    setPlaying(true);
    last = performance.now();
    requestAnimationFrame(tick);
  });
  slider.addEventListener("input", function () { setPlaying(false); toSession(Number(slider.value)); });
  trailSel.addEventListener("change", function () { S.trail = Number(trailSel.value); render(); });
  each(pane.querySelectorAll("input[name=view]"), function (el) {
    el.addEventListener("change", function () {
      setPlaying(false); pauseClips(null);
      if (heatOn()) { render(); return; }
      S.mode = "whole"; S.cur = null; render(); onScroll();
    });
  });
  box.querySelector(".showall").addEventListener("click", function () {
    setPlaying(false); S.mode = "whole"; S.cur = null; S.t = DUR; render(); onScroll();
  });

  // Clicking or dragging on the strip sets the map time.
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

  // Left and right arrows step between kept moments.
  document.addEventListener("keydown", function (e) {
    if (e.defaultPrevented || e.altKey || e.ctrlKey || e.metaKey || e.shiftKey) return;
    if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
    var tag = (e.target.tagName || "").toLowerCase();
    if (tag === "input" || tag === "select" || tag === "textarea" || tag === "video" || e.target.isContentEditable) return;
    if (!KEPT.length) return;
    var i = S.cur && S.cur.kept ? KEPT.indexOf(S.cur) : -1, next = null;
    var base = S.cur ? S.cur.t : (S.mode === "session" ? S.t : -Infinity);
    if (e.key === "ArrowRight") next = i >= 0 ? KEPT[i + 1] : KEPT.filter(function (r) { return r.t > base; })[0];
    else next = i >= 0 ? KEPT[i - 1] : KEPT.filter(function (r) { return r.t < base; }).pop();
    if (!next) return;
    e.preventDefault();
    goTo(next, true);
  });

  // A playing clip holds the map on its moment and moves the dot:
  // map time = clip.start_s + video.currentTime.
  RECS.forEach(function (r) {
    var v = r.video;
    if (!v || r.clipStart == null) return;
    function follow() {
      if (S.clip !== r) return;
      S.clipT = r.clipStart + v.currentTime;
      var p = pointAt(S.clipT);
      if (p !== lastPoint) { lastPoint = p; render(); } else renderBox(false, r, -Infinity);
      if (!v.paused && !v.ended) requestAnimationFrame(follow);
    }
    v.addEventListener("play", function () {
      pauseClips(r); setPlaying(false); showTrail();
      S.mode = "moment"; S.cur = r; S.clip = r; lastPoint = null;
      follow();
    });
    function stop() { if (S.clip === r) { S.clip = null; render(); } }
    v.addEventListener("pause", stop);
    v.addEventListener("ended", stop);
    v.addEventListener("seeked", function () { if (S.cur === r) { S.clipT = r.clipStart + v.currentTime; render(); } });
  });

  each(document.querySelectorAll("[data-needs-script]"), function (el) { el.removeAttribute("hidden"); });
  // A link to a moment (#m7, #d-f12) opens on that moment.
  var start = BY_ID[decodeURIComponent(location.hash.slice(1))];
  if (start) {
    S.mode = "moment"; S.cur = start; S.lock = performance.now() + 1200;
    start.el.scrollIntoView({ block: "center", behavior: "instant" });
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
        page_open = (
            f'<div class="page" style="--ars:{sum(ratios):.4f};--floors:{len(ratios)}">'
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
        '<main class="col">',
    ]
    parts.extend(_render_header(data))
    if summary is not None and summary.get("problems"):
        parts.extend(_render_problems(summary["problems"], by_id))
    if summary is not None:
        parts.extend(_render_glance(summary, session["duration_s"]))
    if has_map:
        parts.extend(_render_strip(data, kept, dropped, floor_count))
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
