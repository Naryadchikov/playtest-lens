"""Render a findings.json file as one self-contained HTML page.

The page only renders what the file holds. It computes nothing beyond
formatting seconds as m:ss, converting a route or pin world point to
image pixels with the map's JSON, and the structural counts a group or
a pin list needs. Section and card order come from the file's times
and beat fields: sections by their start, cards by time, ties by rank.

One small inline script drives the map's time control. It only shows
or hides route points, arrows, pins and markers, and dims cards and pin
rows, by the times the file holds (written into data-t attributes), and
moves a dot to an existing route point. It never makes a finding, a
time, a position or a count. Without script the page shows the whole
route. The heat map view is a CSS switch (:has), so it needs no script.

The look follows docs/design/report-mockup.html. All page wording lives
in LABELS, so changing a string never means touching the markup.
"""

from __future__ import annotations

import argparse
import base64
import html
import json
import math
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
    },
    "sections": {
        "glance": "At a glance",
        "across": "Across players",
        "where": "Where it happened",
        "moments": "The moments",
        "dropped": "Dropped moments",
    },
    "tiles": {
        "time_lost": "Time lost to being stuck or confused",
        "kept": "Moments checked against the video and the event log",
        "of": "of {duration}",
        "count_note": "{kept} kept, {dropped} dropped",
    },
    "kinds": {
        "stuck": {
            "label": "Stuck",
            "lower": "stuck",
            "class": "stuck",
            "shape": "sh-stuck",
        },
        "confused": {
            "label": "Confused",
            "lower": "confused",
            "class": "confused",
            "shape": "sh-confused",
        },
        "surprised": {
            "label": "Surprised",
            "lower": "surprised",
            "class": "surprised",
            "shape": "sh-surprised",
        },
        "suspected_bug": {
            "label": "Suspected bug",
            "lower": "suspected bug",
            "class": "bug",
            "shape": "sh-bug",
        },
    },
    "friction": {
        "learning": {"level": 1, "tag": "planned challenge?", "unplanned": False},
        "stuck": {"level": 2, "tag": "unplanned", "unplanned": True},
        "blocked": {"level": 3, "tag": "unplanned", "unplanned": True},
    },
    "meter": {0: "None", 1: "Low", 2: "Medium", 3: "High"},
    "resolved": {"solved": "Resolved", "after": "Resolved after {time}"},
    "abandoned": "Abandoned",
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
        "attempt": "Attempt {n} ({start}-{end})",
        "attempt_note": "{attempts}, {moments}, {span}",
        "note": "{moments}, {span}",
    },
    "card": {
        "game": "Game",
        "checker": "Checker",
        "no_quote": "No spoken comment.",
        "f9": "Player pressed F9 at {time}",
        "num_pin": "Show moment {rank} on the map",
        "pin": "Moment {rank}, {kind}, {time}",
    },
    "map": {
        "alt": "Top-down plan of the {level} level. The timeline view draws the player's route and numbered pins on top; the heat map view shows where the player spent time.",
        "title": "Route and pins on the {level} map",
        "level": "level",
        "marker": "F9 marker at {time}",
        "figcaption": "Pins are numbered by rank; the list beside the map gives each pin's kind and time.",
        "legend": {
            "route": ("<svg viewBox=\"0 0 28 20\" aria-hidden=\"true\"><path d=\"M3 10H25\" stroke=\"#dbe7ff\" stroke-width=\"3\"/><path d=\"M18 5L26 10L18 15z\" fill=\"#fff\"/></svg>", "Route, arrows point the way walked (start circle to end circle)"),
            "f9": ("<svg viewBox=\"0 0 28 20\" aria-hidden=\"true\"><polygon points=\"14,2 22,6 22,14 14,18 6,14 6,6\" fill=\"#0b1020\" stroke=\"#fff\" stroke-dasharray=\"3 2\"/></svg>", "F9: the player flagged confusion"),
        },
        "legend_title": "Map legend and pin list",
    },
    # Proposals (Claude Opus 5.5 plan, task 25, 2026-10-28), not Sasha's wording.
    # "view", "trail", "readout_window", "span_note" and "show_all" are
    # proposals by Claude Opus 5.5 (Cursor, task 26, 2026-10-28). The
    # window lengths come from Sasha's "10 sec, 15, 30, etc." (Cursor
    # chat, 2026-10-28); 60 is the brief's.
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
        "span_note": "Moments in {span} are lit. The rest are dimmed.",
        "show_all": "Show all moments",
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
  --accent: #2f45c7; --accent-tint: #e6e9fb;
  --k-stuck: #c2410c; --k-confused: #946200; --k-surprised: #0f766e; --k-bug: #a3195b;
  --t-stuck: #fbe9e0; --t-confused: #f7edd2; --t-surprised: #d9f1ee; --t-bug: #f9dfea;
  --s1: 4px; --s2: 8px; --s3: 12px; --s4: 16px; --s5: 24px; --s6: 40px;
  --fs-s: .8125rem; --fs-b: .9375rem; --fs-m: 1.125rem; --fs-l: 1.5rem; --fs-xl: 2rem;
  --font: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  --mono: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #0f131b; --surface: #171c27; --sunk: #202636;
    --ink: #e8ecf4; --ink2: #b0b8c8; --muted: #909ab0; --line: #2c3344;
    --accent: #8da2ff; --accent-tint: #232b52;
    --k-stuck: #ff8a5c; --k-confused: #f2c14e; --k-surprised: #4fd1c5; --k-bug: #ff7aa8;
    --t-stuck: #3a2219; --t-confused: #382e12; --t-surprised: #12322f; --t-bug: #3b1a2a;
  }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--ink); font: var(--fs-b)/1.5 var(--font); }
main { max-width: 1040px; margin: 0 auto; padding: var(--s5) var(--s4) var(--s6); }
a { color: var(--accent); }
a:focus-visible, summary:focus-visible, button:focus-visible, input:focus-visible { outline: 3px solid var(--accent); outline-offset: 2px; border-radius: 3px; }
h1 { font-size: var(--fs-xl); line-height: 1.2; margin: 0 0 var(--s2); }
h2 { font-size: var(--fs-l); margin: var(--s6) 0 var(--s3); }
h3 { font-size: var(--fs-m); margin: 0 0 var(--s1); }
h4 { font-size: var(--fs-b); margin: var(--s4) 0 var(--s2); color: var(--ink2); }
.sub { color: var(--muted); font-size: var(--fs-s); margin: 0 0 var(--s3); }
.note { color: var(--muted); font-size: var(--fs-s); }
.mock { background: var(--accent-tint); border-radius: 6px; padding: var(--s2) var(--s3); font-size: var(--fs-s); margin-bottom: var(--s4); }

/* header */
.meta { display: flex; flex-wrap: wrap; gap: var(--s1) var(--s5); margin: 0 0 var(--s4); padding: 0; list-style: none; color: var(--ink2); font-size: var(--fs-s); }
.meta b { color: var(--muted); font-weight: 600; margin-right: var(--s1); }
.verdict { font-size: var(--fs-m); font-weight: 600; margin: 0; padding: var(--s3) var(--s4); background: var(--surface); border: 1px solid var(--line); border-left: 6px solid var(--accent); border-radius: 6px; }

/* kind shapes, shared by tiles, badges, legend */
.k { display: inline-block; width: .85em; height: .85em; background: var(--c); flex: none; }
.k-stuck { --c: var(--k-stuck); }
.k-confused { --c: var(--k-confused); border-radius: 50%; }
.k-surprised { --c: var(--k-surprised); clip-path: polygon(50% 0, 100% 50%, 50% 100%, 0 50%); }
.k-bug { --c: var(--k-bug); clip-path: polygon(50% 0, 100% 100%, 0 100%); }

/* at a glance */
.tiles { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: var(--s3); }
.tile { background: var(--surface); border: 1px solid var(--line); border-radius: 6px; padding: var(--s3) var(--s4); }
.tile .n { font-size: var(--fs-xl); font-weight: 700; line-height: 1.1; font-variant-numeric: tabular-nums; }
.tile .l { display: flex; align-items: center; gap: var(--s2); color: var(--ink2); font-size: var(--fs-s); margin-top: var(--s1); }
.tile.wide { grid-column: span 2; }

/* across players */
.groups { list-style: none; margin: 0; padding: 0; display: grid; gap: var(--s3); }
.group { background: var(--surface); border: 1px solid var(--line); border-radius: 6px; padding: var(--s3) var(--s4); display: grid; gap: var(--s2); }
.group p { margin: 0; color: var(--ink2); }
.group .who { font-weight: 600; color: var(--ink); }
.chips { display: flex; flex-wrap: wrap; gap: var(--s2); align-items: center; }
.chip { display: inline-flex; align-items: center; gap: var(--s1); padding: 2px var(--s3); border: 1px solid var(--line); border-radius: 999px; font-size: var(--fs-s); background: var(--sunk); color: var(--ink2); text-decoration: none; }
.chip.you { background: var(--accent-tint); border-color: var(--accent); color: var(--ink); }
a.chip:hover { border-color: var(--accent); }

/* map */
.where { display: grid; grid-template-columns: minmax(0, 480px) 1fr; gap: var(--s5); align-items: start; }
.mapcol { min-width: 0; }
.map { position: relative; margin: 0; border: 1px solid var(--line); border-radius: 6px; overflow: hidden; background: #0a0d14; }
.map img, .map svg { display: block; width: 100%; height: auto; }
.map svg { position: absolute; inset: 0; height: 100%; }
.maphead { display: flex; justify-content: flex-end; margin-bottom: var(--s2); }
.seg { display: inline-flex; flex-wrap: wrap; gap: 2px; padding: 2px; border: 1px solid var(--line); border-radius: 6px; background: var(--sunk); }
.seg label { position: relative; padding: 2px var(--s3); border-radius: 4px; font-size: var(--fs-s); font-weight: 600; color: var(--ink2); white-space: nowrap; cursor: pointer; }
.seg input { position: absolute; inset: 0; margin: 0; opacity: 0; cursor: pointer; }
.seg label:has(input:checked) { background: var(--surface); color: var(--ink); box-shadow: 0 0 0 1px var(--line); }
.seg label:has(input:focus-visible) { outline: 3px solid var(--accent); outline-offset: 1px; }
.timeline { display: grid; gap: var(--s2); margin-top: var(--s2); }
.timeline[hidden], [data-needs-script][hidden] { display: none; }
.tl-row { display: flex; flex-wrap: wrap; align-items: center; gap: var(--s2) var(--s3); }
.timeline button { font: inherit; font-size: var(--fs-s); font-weight: 600; min-width: 5em; padding: var(--s1) var(--s3); border: 1px solid var(--line); border-radius: 6px; background: var(--surface); color: var(--ink); cursor: pointer; }
.timeline input[type=range] { flex: 1 1 8em; min-width: 0; accent-color: var(--accent); }
.timeline output, .tl-label { font-size: var(--fs-s); color: var(--ink2); font-variant-numeric: tabular-nums; white-space: nowrap; }
.later { display: none; }
.pinlist .dim, .card.dim { opacity: .4; }
details.puzzle.quiet > summary { opacity: .5; }

/* heat map view: the plan muted, the whole-session heat on top, nothing else */
.map .heat, .legend-heat { display: none; }
.where:has(.view-heat:checked) .map .heat { display: inline; }
.where:has(.view-heat:checked) .legend-heat { display: block; }
.where:has(.view-heat:checked) :is(.trail, .legend-trail, .timeline) { display: none; }
.where:has(.view-heat:checked) .map img { filter: grayscale(1) brightness(.5); }
.heat .halo { font-size: 30px; }
.legend-h { font-weight: 600; color: var(--ink); margin: 0 0 var(--s2); }
.ramp { height: 12px; border-radius: 3px; }
.ramp-ends { display: flex; justify-content: space-between; color: var(--ink2); margin: var(--s1) 0 var(--s3); }
.legend .kinds { flex-wrap: wrap; gap: var(--s1) var(--s3); }
.legend .kinds span { display: inline-flex; align-items: center; gap: var(--s1); }
.span-note { position: sticky; top: var(--s2); z-index: 1; display: flex; flex-wrap: wrap; align-items: center; gap: var(--s2) var(--s3); margin: 0 0 var(--s3); padding: var(--s2) var(--s3); border: 1px solid var(--accent); border-radius: 6px; background: var(--accent-tint); font-size: var(--fs-s); }
.span-note[hidden] { display: none; }
.span-note button { font: inherit; font-weight: 600; padding: 0 var(--s2); border: 1px solid var(--accent); border-radius: 4px; background: var(--surface); color: var(--accent); cursor: pointer; }
.now { pointer-events: none; }
.pin { cursor: pointer; --pf: #ff8a5c; }
.pin.confused { --pf: #f2c14e; } .pin.surprised { --pf: #4fd1c5; } .pin.bug { --pf: #ff7aa8; }
.pin .shape { fill: var(--pf); stroke: #fff; stroke-width: 6; }
.pin text { font: 700 38px var(--font); fill: #0b1020; text-anchor: middle; pointer-events: none; }
.pin:focus { outline: none; }
.pin:focus-visible .shape, .pin:target .shape, .pin:hover .shape { stroke: #3d5afe; stroke-width: 14; paint-order: stroke; }
.pin.f9 .shape { fill: #0b1020; stroke: #fff; stroke-width: 6; stroke-dasharray: 10 7; }
.pin.f9 text { fill: #fff; font-size: 28px; }
.halo { font: 700 40px var(--font); fill: #fff; stroke: #0a0d14; stroke-width: 9; paint-order: stroke; text-anchor: middle; }
.legend { background: var(--surface); border: 1px solid var(--line); border-radius: 6px; padding: var(--s3) var(--s4); font-size: var(--fs-s); }
.legend ul { list-style: none; margin: 0 0 var(--s3); padding: 0; display: grid; gap: var(--s2); }
.legend li { display: flex; align-items: center; gap: var(--s2); color: var(--ink2); }
.legend svg { width: 28px; height: 20px; flex: none; background: #0a0d14; border-radius: 3px; }
.pinlist { margin: 0; padding: 0; list-style: none; display: grid; gap: var(--s1); }
.pinlist a { display: flex; gap: var(--s2); align-items: center; color: var(--ink); text-decoration: none; padding: 2px var(--s2); border-radius: 4px; }
.pinlist a:hover { background: var(--sunk); }
.pinlist .num { font-weight: 700; min-width: 1.4em; font-variant-numeric: tabular-nums; }
.pinlist time { color: var(--muted); margin-left: auto; font-variant-numeric: tabular-nums; }

/* moments */
details.puzzle { background: var(--surface); border: 1px solid var(--line); border-radius: 6px; margin-bottom: var(--s3); }
details.puzzle > summary { cursor: pointer; padding: var(--s3) var(--s4); font-weight: 600; list-style-position: inside; }
details.puzzle > summary .note { font-weight: 400; margin-left: var(--s2); }
.puzzle-body { padding: 0 var(--s4) var(--s4); }
.card { border: 1px solid var(--line); border-left: 6px solid var(--c); border-radius: 6px; padding: var(--s3) var(--s4); margin-bottom: var(--s3); background: var(--bg); scroll-margin-top: var(--s4); display: grid; gap: var(--s2); }
.card:target { outline: 3px solid var(--accent); outline-offset: 2px; }
.card.stuck { --c: var(--k-stuck); } .card.confused { --c: var(--k-confused); }
.card.surprised { --c: var(--k-surprised); } .card.bug { --c: var(--k-bug); }
.card-head { display: flex; flex-wrap: wrap; gap: var(--s2) var(--s3); align-items: center; }
.num-pin { display: inline-grid; place-items: center; min-width: 28px; height: 28px; border-radius: 50%; background: var(--ink); color: var(--bg); font-weight: 700; text-decoration: none; font-size: var(--fs-s); }
.time { font-variant-numeric: tabular-nums; font-weight: 600; }
.time small { color: var(--muted); font-weight: 400; }
.badge { display: inline-flex; align-items: center; gap: var(--s1); padding: 1px var(--s2); border-radius: 4px; font-size: var(--fs-s); font-weight: 600; background: var(--tint); color: var(--ink); border: 1px solid var(--c); }
.stuck .badge { --tint: var(--t-stuck); } .confused .badge { --tint: var(--t-confused); }
.surprised .badge { --tint: var(--t-surprised); } .bug .badge { --tint: var(--t-bug); }
.intent { font-size: var(--fs-s); padding: 1px var(--s2); border-radius: 4px; border: 1px dashed var(--muted); color: var(--ink2); }
.intent.unplanned { border-style: solid; border-color: var(--ink2); font-weight: 600; }
.to-map { margin-left: auto; font-size: var(--fs-s); }
.summary { font-size: var(--fs-m); font-weight: 600; margin: 0; line-height: 1.35; }
.quote { margin: 0; padding-left: var(--s3); border-left: 3px solid var(--line); color: var(--ink2); font-style: italic; }
.quote.none { font-style: normal; color: var(--muted); }
.facts { display: grid; grid-template-columns: max-content 1fr; gap: var(--s1) var(--s3); margin: 0; font-size: var(--fs-s); color: var(--ink2); }
.facts dt { color: var(--muted); font-weight: 600; }
.facts dd { margin: 0; }
.fric { display: flex; align-items: center; gap: var(--s2); font-size: var(--fs-s); }
.meter { display: inline-flex; gap: 2px; }
.meter i { width: 14px; height: 8px; border: 1px solid var(--ink2); border-radius: 2px; }
.meter i.on { background: var(--ink2); }
.status { font-weight: 600; }
.status.open::before { content: "\\25CB  "; } .status.done::before { content: "\\2713  "; }
.f9line { font-size: var(--fs-s); color: var(--ink2); margin: 0; }
.f9line b { border: 1px dashed var(--ink2); border-radius: 4px; padding: 0 var(--s1); margin-right: var(--s1); }
.clip { display: grid; place-items: center; border-radius: 4px; background: repeating-linear-gradient(135deg, var(--sunk) 0 10px, transparent 10px 20px), var(--sunk); color: var(--muted); font-size: var(--fs-s); border: 1px solid var(--line); }
.clip.video { display: block; background: none; }
.clip.video video { display: block; width: 100%; height: auto; border-radius: 4px; }
.dropped li { margin-bottom: var(--s2); }
@media (max-width: 760px) { .where { grid-template-columns: 1fr; } .tiles { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (prefers-reduced-motion: no-preference) { .pin .shape, a.chip { transition: stroke-width .15s, border-color .15s; } .card, .pinlist li { transition: opacity .2s; } html { scroll-behavior: smooth; } }
@media print {
  body { background: #fff; color: #000; } main { max-width: none; padding: 0; }
  .card, .group, .tile { break-inside: avoid; } .clip, .to-map { display: none; }
  .map { max-width: 300px; }
  .timeline, .maphead, .span-note, [data-needs-script] { display: none; }
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


# Heat spots are drawn as white blobs whose opacity is their weight; the
# filter turns that opacity into the color scale.
HEAT_DEFS = (
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

SVG_DEFS = f"""<defs>
          {HEAT_DEFS}
          <symbol id="sh-stuck" overflow="visible"><rect x="-30" y="-30" width="60" height="60" rx="6"/></symbol>
          <symbol id="sh-confused" overflow="visible"><circle r="34"/></symbol>
          <symbol id="sh-surprised" overflow="visible"><polygon points="0,-44 44,0 0,44 -44,0"/></symbol>
          <symbol id="sh-bug" overflow="visible"><polygon points="0,-42 42,32 -42,32"/></symbol>
          <symbol id="sh-f9" overflow="visible"><polygon points="0,-38 33,-19 33,19 0,38 -33,19 -33,-19"/></symbol>
        </defs>"""


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
    return f"{_mss(start_s)}-{_mss(end_s)}"


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


# Load the map's JSON and PNG. Returns (meta, data URI), or None when
# either file is missing. A map name is a bare filename, never a path.
def _load_map(map_name, maps_dir):
    if not isinstance(map_name, str) or not map_name or Path(map_name).name != map_name:
        return None
    directory = Path(maps_dir) if maps_dir is not None else MAPS_DIR
    json_path = directory / f"{map_name}.json"
    png_path = directory / f"{map_name}.png"
    if not json_path.is_file() or not png_path.is_file():
        return None
    meta = json.loads(json_path.read_text(encoding="utf-8"))
    encoded = base64.b64encode(png_path.read_bytes()).decode("ascii")
    return meta, f"data:image/png;base64,{encoded}"


def _kind(kind):
    return LABELS["kinds"].get(
        kind,
        {"label": str(kind), "lower": str(kind), "class": "stuck", "shape": "sh-stuck"},
    )


def _pin_title(finding):
    beat = finding.get("beat") or {}
    # A beat with no puzzle line is an area visit: the area alone.
    title = beat.get("puzzle") or beat.get("area")
    if not title:
        return LABELS["moments"]["fallback"]
    attempt = beat.get("attempt")
    if isinstance(attempt, int) and attempt > 1:
        return f"{title}, attempt {attempt}"
    return title


def _render_header(data):
    session = data["session"]
    player = session.get("player")
    heading = LABELS["session"].format(id=_e(session["id"]))
    if player:
        heading += f": {_e(player)}"

    meta = []
    if session.get("level"):
        meta.append(
            f'<li><b>{LABELS["meta"]["level"]}</b>{_e(session["level"])}</li>'
        )
    meta.append(
        f'<li><b>{LABELS["meta"]["recording"]}</b>'
        f'<span style="font-family:var(--mono)">{_e(session["recording"])}</span></li>'
    )
    meta.append(
        f'<li><b>{LABELS["meta"]["length"]}</b>{_mss(session["duration_s"])}</li>'
    )
    if session.get("recorded"):
        meta.append(
            f'<li><b>{LABELS["meta"]["date"]}</b>{_e(session["recorded"])}</li>'
        )

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


def _render_tiles(summary, duration_s):
    parts = [
        f'<section aria-labelledby="glance">',
        f'<h2 id="glance">{LABELS["sections"]["glance"]}</h2>',
        '<div class="tiles">',
    ]
    for kind in KIND_ORDER:
        info = _kind(kind)
        parts.append(
            f'<div class="tile"><div class="n">{summary["counts"][kind]}</div>'
            f'<div class="l"><span class="k k-{info["class"]}" aria-hidden="true"></span>'
            f'{_e(info["label"])}</div></div>'
        )
    of_note = LABELS["tiles"]["of"].format(duration=_mss(duration_s))
    parts.append(
        f'<div class="tile wide"><div class="n">{_mss(summary["lost_s"])} '
        f'<span class="note">{_e(of_note)}</span></div>'
        f'<div class="l">{_e(LABELS["tiles"]["time_lost"])}</div></div>'
    )
    count_note = LABELS["tiles"]["count_note"].format(
        kept=summary["kept"], dropped=summary["dropped"]
    )
    parts.append(
        f'<div class="tile wide"><div class="n">{summary["kept"]} '
        f'<span class="note">{_e(count_note)}</span></div>'
        f'<div class="l">{_e(LABELS["tiles"]["kept"])}</div></div>'
    )
    parts.extend(["</div>", "</section>"])
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
            who = across["who_other"].format(
                n=affected, of=group["of"], kind=kind
            )
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
                    chips.append(
                        f'<a class="chip you" href="#m{target}">{_e(text)}</a>'
                    )
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
    parts.extend(
        ["</ul>", f'<p class="note">{_e(across["note"])}</p>', "</section>"]
    )
    return parts


def _render_heat(route, meta):
    if not route["heat"]:
        return []
    scale = _px_per_m(meta)
    top = max(spot["seconds"] for spot in route["heat"]) or 1
    blobs = []
    labels = []
    for spot in route["heat"]:
        cx, cy = world_to_px(meta, spot["x"], spot["z"])
        radius = spot["r_m"] * scale
        weight = 0.35 + 0.65 * spot["seconds"] / top
        blobs.append(
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{radius:.1f}" '
            f'fill="url(#heat-blob)" fill-opacity="{weight:.2f}"/>'
        )
        labels.append(
            f'<text class="halo" x="{cx:.1f}" y="{cy + 11:.1f}">'
            f'{_mss(spot["seconds"])}</text>'
        )
    return [
        '<g class="heat" aria-hidden="true">',
        '<g filter="url(#heat-ramp)">',
        *blobs,
        "</g>",
        *labels,
        "</g>",
    ]


def _route_pixels(route, meta):
    return [world_to_px(meta, point[1], point[2]) for point in route["points"]]


def _render_arrows(pixels, times):
    arrows = []
    for index in range(4, len(pixels), 4):
        x0, y0 = pixels[index - 1]
        x1, y1 = pixels[index]
        if x0 == x1 and y0 == y1:
            continue
        angle = math.degrees(math.atan2(y1 - y0, x1 - x0))
        arrows.append(
            f'<path data-t="{times[index]}" d="M-16,-12L16,0L-16,12z" '
            f'transform="translate({x1:.1f} {y1:.1f}) rotate({angle:.0f}) scale(1.3)"/>'
        )
    return arrows


def _render_route(route, meta):
    pixels = _route_pixels(route, meta)
    if len(pixels) < 2:
        return []
    points = " ".join(f"{x:.1f},{y:.1f}" for x, y in pixels)
    times = [point[0] for point in route["points"]]
    stamps = " ".join(str(t) for t in times)
    start_x, start_y = pixels[0]
    end_x, end_y = pixels[-1]
    parts = [
        '<g aria-hidden="true" fill="none" stroke-linejoin="round" stroke-linecap="round">',
        f'<polyline data-t="{stamps}" stroke="#0a0d14" stroke-width="16" points="{points}"/>',
        f'<polyline data-t="{stamps}" stroke="#dbe7ff" stroke-width="7" points="{points}"/>',
    ]
    arrows = _render_arrows(pixels, times)
    if arrows:
        parts.append(
            '<g fill="#fff" stroke="#0a0d14" stroke-width="4">'
            + "".join(arrows)
            + "</g>"
        )
    parts.append(
        f'<circle cx="{start_x:.1f}" cy="{start_y:.1f}" r="24" fill="#fff" '
        'stroke="#0a0d14" stroke-width="6"/>'
        f'<text x="{start_x:.1f}" y="{start_y + 58:.1f}" class="halo" '
        'style="font-size:34px">start</text>'
        f'<g data-t="{times[-1]}">'
        f'<circle cx="{end_x:.1f}" cy="{end_y:.1f}" r="24" fill="#0a0d14" '
        'stroke="#fff" stroke-width="6"/>'
        f'<text x="{end_x:.1f}" y="{end_y + 68:.1f}" class="halo" '
        'style="font-size:34px" dx="-70">end</text></g>'
    )
    parts.append("</g>")
    return parts


# The player's place at the slider's time: the script moves it to a
# route point. Drawn last so pins never cover it.
NOW_DOT = '<circle class="now later" r="22" fill="#3d5afe" stroke="#fff" stroke-width="7"/>'


def _render_pins(pinned, meta):
    parts = []
    for finding in pinned:
        info = _kind(finding["kind"])
        rank = finding["rank"]
        x, y = world_to_px(meta, finding["at"]["x"], finding["at"]["z"])
        label = LABELS["card"]["pin"].format(
            rank=rank, kind=info["label"], time=_mss(finding["time_s"])
        )
        text_y = 22 if info["class"] == "bug" else 13
        parts.append(
            f'<a class="pin {info["class"]}" id="pin-m{rank}" href="#m{rank}" '
            f'data-t="{finding["time_s"]}" '
            f'aria-label="{_e(label)}" transform="translate({x:.1f} {y:.1f})">'
            f'<use href="#{info["shape"]}" class="shape"/>'
            f'<text y="{text_y}">{rank}</text></a>'
        )
    return parts


def _render_markers(markers, meta, id_to_rank):
    parts = []
    for index, marker in enumerate(markers, start=1):
        x, y = world_to_px(meta, marker["x"], marker["z"])
        moment = marker.get("moment")
        target = id_to_rank.get(moment) if moment else None
        label = LABELS["map"]["marker"].format(time=_mss(marker["t"]))
        transform = f'translate({x:.1f} {y:.1f})'
        if target is not None:
            parts.append(
                f'<a class="pin f9" id="pin-f{index}" href="#m{target}" '
                f'data-t="{marker["t"]}" '
                f'aria-label="{_e(label)}" transform="{transform}">'
                '<use href="#sh-f9" class="shape"/><text y="10">F9</text></a>'
            )
        else:
            parts.append(
                f'<g class="pin f9" id="pin-f{index}" data-t="{marker["t"]}" '
                f'aria-label="{_e(label)}" transform="{transform}">'
                '<use href="#sh-f9" class="shape"/><text y="10">F9</text></g>'
            )
    return parts


def _render_legend(timeline, has_markers):
    legend = LABELS["map"]["legend"]
    items = [f'<li>{legend["route"][0]}{_e(legend["route"][1])}</li>']
    if timeline:
        items.append(
            '<li data-needs-script hidden><svg viewBox="0 0 28 20" aria-hidden="true">'
            '<circle cx="14" cy="10" r="6" fill="#3d5afe" stroke="#fff" stroke-width="2"/></svg>'
            f'{_e(LABELS["timeline"]["legend"])}</li>'
        )
    if has_markers:
        items.append(f'<li>{legend["f9"][0]}{_e(legend["f9"][1])}</li>')
    kinds = "".join(
        f'<span><span class="k k-{_kind(kind)["class"]}"></span>{_e(_kind(kind)["label"])}</span>'
        for kind in KIND_ORDER
    )
    items.append(f'<li class="kinds">{kinds}</li>')
    return items


def _render_heat_legend():
    words = LABELS["heat"]
    stops = ", ".join(HEAT_RAMP)
    return (
        '<div class="legend-heat">'
        f'<p class="legend-h">{_e(words["title"])}</p>'
        f'<div class="ramp" style="background:linear-gradient(90deg, {stops})" aria-hidden="true"></div>'
        f'<div class="ramp-ends"><span>{_e(words["low"])}</span><span>{_e(words["high"])}</span></div>'
        f'<p class="note">{_e(words["note"])}</p>'
        "</div>"
    )


# The map's view switch. It works by CSS alone (:has), so a reader
# without script can still open the heat map.
def _render_views():
    words = LABELS["timeline"]
    return (
        '<div class="maphead">'
        f'<div class="seg views" role="radiogroup" aria-label="{_e(words["view"])}">'
        '<label><input type="radio" name="view" value="trail" checked> '
        f'{_e(words["view_trail"])}</label>'
        '<label><input type="radio" name="view" value="heat" class="view-heat"> '
        f'{_e(words["view_heat"])}</label>'
        "</div></div>"
    )


# The time control's markup. It is hidden until the script runs, so a
# reader without script, or a print, sees the whole map and no dead
# controls. Wording reaches the script through data- attributes.
def _render_timeline(duration_s):
    words = LABELS["timeline"]
    total = int(duration_s)
    lengths = [
        '<label><input type="radio" name="trail" value="0" checked> '
        f'{_e(words["trail_all"])}</label>'
    ] + [
        f'<label><input type="radio" name="trail" value="{n}"> '
        f'{_e(words["trail_last"].format(n=n))}</label>'
        for n in words["windows"]
    ]
    return (
        f'<div class="timeline" hidden data-needs-script data-play="{_e(words["play"])}" '
        f'data-pause="{_e(words["pause"])}" data-readout="{_e(words["readout"])}" '
        f'data-readout-window="{_e(words["readout_window"])}">'
        '<div class="tl-row">'
        f'<button type="button">{_e(words["play"])}</button>'
        f'<input type="range" min="0" max="{total}" step="1" value="{total}" '
        f'aria-label="{_e(words["slider"])}">'
        f'<output>{_e(words["readout"].format(time=_mss(total), duration=_mss(total)))}</output>'
        "</div>"
        '<div class="tl-row">'
        f'<span class="tl-label" id="trail-label">{_e(words["trail"])}</span>'
        f'<div class="seg" role="radiogroup" aria-labelledby="trail-label">{"".join(lengths)}</div>'
        "</div></div>"
    )


# Shown by the script while a time is selected; says which span is lit.
def _render_span_note():
    words = LABELS["timeline"]
    return (
        f'<p class="span-note" hidden data-text="{_e(words["span_note"])}">'
        f'<span></span><button type="button">{_e(words["show_all"])}</button></p>'
    )


# Show or hide by the file's times, move the dot to a route point, dim
# cards and pin rows outside the lit span. No wording, no computing of
# findings, times, positions or counts.
SCRIPT = """
(function () {
  var box = document.querySelector(".timeline");
  var map = document.getElementById("map");
  if (!box || !map) return;
  var SPEED = 10;
  var each = function (list, fn) { Array.prototype.forEach.call(list, fn); };
  var slider = box.querySelector("input[type=range]");
  var button = box.querySelector("button");
  var readout = box.querySelector("output");
  var heatView = document.querySelector(".view-heat");
  var note = document.querySelector(".span-note");
  var now = map.querySelector(".now");
  var max = Number(slider.max);
  var routes = Array.prototype.map.call(map.querySelectorAll("polyline[data-t]"), function (el) {
    return { el: el, pts: el.getAttribute("points").split(" "), t: el.getAttribute("data-t").split(" ").map(Number) };
  });
  var timed = map.querySelectorAll(".trail [data-t]:not(polyline)");
  var listed = document.querySelectorAll(".pinlist [data-t]");
  var cards = document.querySelectorAll(".card[data-t]");
  var groups = document.querySelectorAll("details.puzzle");
  var current = max, span = 0, playing = false, last = 0;
  function mss(s) { s = Math.floor(s); return Math.floor(s / 60) + ":" + ("0" + (s % 60)).slice(-2); }
  function count(times, t) { var n = 0; while (n < times.length && times[n] <= t) n++; return n; }
  function show(t) {
    var lo = span > 0 ? t - span : -Infinity;
    var n = 0;
    routes.forEach(function (r) {
      n = count(r.t, t);
      r.el.setAttribute("points", r.pts.slice(count(r.t, lo), n).join(" "));
    });
    if (now) {
      now.classList.toggle("later", n === 0);
      if (n > 0) {
        var xy = routes[0].pts[n - 1].split(",");
        now.setAttribute("cx", xy[0]);
        now.setAttribute("cy", xy[1]);
      }
    }
    function inside(el) { var at = Number(el.getAttribute("data-t")); return at > lo && at <= t; }
    each(timed, function (el) { el.classList.toggle("later", !inside(el)); });
    each(listed, function (el) { el.classList.toggle("dim", !inside(el)); });
    var lit = !(heatView && heatView.checked) && (span > 0 || t < max);
    each(cards, function (el) {
      var end = Number(el.getAttribute("data-end") || el.getAttribute("data-t"));
      el.classList.toggle("dim", lit && !(Number(el.getAttribute("data-t")) <= t && end > lo));
    });
    each(groups, function (el) { el.classList.toggle("quiet", lit && !el.querySelector(".card:not(.dim)")); });
    var from = mss(Math.max(0, lo));
    var text = box.getAttribute(span > 0 ? "data-readout-window" : "data-readout")
      .replace("{start}", from).replace("{time}", mss(t)).replace("{duration}", mss(max));
    readout.textContent = text;
    slider.setAttribute("aria-valuetext", text);
    if (note) {
      note.hidden = !lit;
      note.querySelector("span").textContent = note.getAttribute("data-text").replace("{span}", from + "-" + mss(t));
    }
  }
  function setPlaying(on) {
    playing = on;
    button.textContent = box.getAttribute(on ? "data-pause" : "data-play");
  }
  function tick(stamp) {
    if (!playing) return;
    current = Math.min(max, current + SPEED * (stamp - last) / 1000);
    last = stamp;
    slider.value = Math.floor(current);
    show(current);
    if (current >= max) setPlaying(false); else requestAnimationFrame(tick);
  }
  button.addEventListener("click", function () {
    if (playing) { setPlaying(false); return; }
    if (current >= max) current = 0;
    setPlaying(true);
    last = performance.now();
    requestAnimationFrame(tick);
  });
  slider.addEventListener("input", function () {
    setPlaying(false);
    current = Number(slider.value);
    show(current);
  });
  each(box.querySelectorAll("input[name=trail]"), function (el) {
    el.addEventListener("change", function () { span = Number(el.value); show(current); });
  });
  // The heat map is its own view: it stops play and lights every card.
  each(document.querySelectorAll("input[name=view]"), function (el) {
    el.addEventListener("change", function () { setPlaying(false); show(current); });
  });
  if (note) note.querySelector("button").addEventListener("click", function () {
    setPlaying(false);
    current = max;
    slider.value = max;
    span = 0;
    box.querySelector("input[name=trail][value='0']").checked = true;
    show(current);
  });
  each(document.querySelectorAll("[data-needs-script]"), function (el) { el.removeAttribute("hidden"); });
  show(current);
})();
"""


def _render_map_section(data, map_state, pinned, markers, id_to_rank, timeline):
    route = data["route"]
    meta, data_uri = map_state
    width = meta["px_width"]
    height = meta["px_height"]
    level = data["session"].get("level") or LABELS["map"]["level"]
    alt = LABELS["map"]["alt"].format(level=_e(level))
    title = LABELS["map"]["title"].format(level=_e(level))

    parts = [
        '<section aria-labelledby="where">',
        f'<h2 id="where">{LABELS["sections"]["where"]}</h2>',
        '<div class="where">',
        '<div class="mapcol">',
    ]
    has_heat = bool(route["heat"])
    if has_heat:
        parts.append(_render_views())
    parts.extend([
        f'<figure class="map" id="map">',
        f'<img src="{data_uri}" width="{width}" height="{height}" alt="{alt}">',
        f'<svg viewBox="0 0 {width} {height}" aria-labelledby="map-title">',
        f'<title id="map-title">{title}</title>',
        SVG_DEFS,
        "<!-- heat map view only: whole-session time spent, a label on each spot so it is not color alone -->",
    ])
    parts.extend(_render_heat(route, meta))
    parts.append('<g class="trail">')
    parts.append("<!-- route: casing plus line, arrows show direction, S and E mark start and end -->")
    parts.extend(_render_route(route, meta))
    parts.append("<!-- kept findings, numbered by rank -->")
    parts.extend(_render_pins(pinned, meta))
    if markers:
        parts.append("<!-- F9 markers: the player pressed F9 to flag confusion -->")
        parts.extend(_render_markers(markers, meta, id_to_rank))
    if timeline:
        parts.append(NOW_DOT)
    parts.append("</g>")
    parts.append("</svg>")
    parts.append(
        '<figcaption class="sr-only" style="position:absolute;left:-9999px">'
        f'{_e(LABELS["map"]["figcaption"])}</figcaption>'
    )
    parts.append("</figure>")
    if timeline:
        parts.append(_render_timeline(data["session"]["duration_s"]))
    parts.append("</div>")

    parts.append(
        f'<aside class="legend" aria-label="{_e(LABELS["map"]["legend_title"])}">'
    )
    if has_heat:
        parts.append(_render_heat_legend())
    parts.append('<div class="legend-trail">')
    parts.append(f'<ul>{"".join(_render_legend(timeline, bool(markers)))}</ul>')
    parts.append('<ol class="pinlist">')
    for finding in pinned:
        info = _kind(finding["kind"])
        rank = finding["rank"]
        parts.append(
            f'<li data-t="{finding["time_s"]}"><a href="#m{rank}"><span class="num">{rank}</span>'
            f'<span class="k k-{info["class"]}"></span>{_e(_pin_title(finding))}'
            f'<time>{_mss(finding["time_s"])}</time></a></li>'
        )
    parts.extend(["</ol>", "</div>", "</aside>", "</div>", "</section>"])
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
    friction = check.get("friction")
    if friction is not None:
        rule = LABELS["friction"].get(friction)
        if rule is not None:
            level = rule["level"]
            word = LABELS["meter"][level]
            bars = "".join(
                '<i class="on"></i>' if index <= level else "<i></i>"
                for index in range(1, 4)
            )
            bits.append(
                f'<span class="meter" role="img" aria-label="Friction: '
                f'{_e(word.lower())}">{bars}</span>{_e(word)}'
            )
    status = _render_status(check)
    if status:
        bits.append(status)
    if not bits:
        return ""
    return f'<p class="fric">{" ".join(bits)}</p>'


def _render_card(finding, markers_by_moment, pins_available):
    info = _kind(finding["kind"])
    rank = finding["rank"]
    check = finding["check"]
    end = finding.get("end_s")
    end_attr = f' data-end="{end}"' if end is not None else ""
    parts = [
        f'<article class="card {info["class"]}" id="m{rank}" '
        f'data-t="{finding["time_s"]}"{end_attr}>'
    ]

    head = []
    if pins_available and finding.get("at") is not None:
        label = LABELS["card"]["num_pin"].format(rank=rank)
        head.append(
            f'<a class="num-pin" href="#pin-m{rank}" aria-label="{_e(label)}">{rank}</a>'
        )
    else:
        head.append(f'<span class="num-pin">{rank}</span>')

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
    parts.append(f'<div class="card-head">{"".join(head)}</div>')

    parts.append(f'<p class="summary">{_e(finding["summary"])}</p>')
    quote = finding.get("quote")
    if quote is None:
        parts.append(f'<p class="quote none">{_e(LABELS["card"]["no_quote"])}</p>')
    else:
        parts.append(f'<p class="quote">"{_e(quote)}"</p>')

    facts = []
    if finding.get("game_state") is not None:
        facts.append(
            f'<dt>{LABELS["card"]["game"]}</dt><dd>{_e(finding["game_state"])}</dd>'
        )
    facts.append(
        f'<dt>{LABELS["card"]["checker"]}</dt><dd>{_e(check["note"])}</dd>'
    )
    parts.append(f'<dl class="facts">{"".join(facts)}</dl>')

    fric = _render_friction_line(check)
    if fric:
        parts.append(fric)

    for marker in markers_by_moment.get(finding["id"], []):
        line = LABELS["card"]["f9"].format(time=_mss(marker["t"]))
        parts.append(f'<p class="f9line"><b>F9</b>{_e(line)}</p>')

    clip = finding.get("clip")
    if clip is not None:
        parts.append(
            f'<div class="clip video"><video controls '
            f'src="{_e(clip["path"])}"></video></div>'
        )
    parts.append("</article>")
    return "\n".join(parts)


# A puzzle beat groups by area and puzzle, its attempts inside. A beat
# with no puzzle is an area visit: one group per visit, no attempts.
def _beat_key(finding):
    beat = finding.get("beat")
    if not beat:
        return None
    if beat.get("puzzle_number") is None:
        return (
            "visit",
            beat.get("area"),
            beat.get("zone"),
            beat.get("attempt_start_s"),
        )
    return (
        beat.get("area"),
        beat.get("puzzle"),
        beat.get("zone"),
        beat.get("puzzle_number"),
    )


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
        parts.append(f"Puzzle {number}: {puzzle}")
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


def _render_groups(kept, markers_by_moment, pins_available):
    groups = _kept_groups(kept)
    if not groups:
        return []
    open_group = min(groups, key=lambda g: min(f["rank"] for f in g["findings"]))
    # Sections run in time order: by the earliest start, ties to the lower rank.
    groups.sort(
        key=lambda g: (
            _group_span(g["findings"])[0],
            min(f["rank"] for f in g["findings"]),
        )
    )
    out = []
    for group in groups:
        beat = group["findings"][0].get("beat") or {}
        attempt_keys = sorted(group["attempts"], key=_attempt_sort_key)
        start, end = _group_span(group["findings"])
        moments_note = LABELS["moments"]["note"].format(
            moments=_plural(len(group["findings"]), "moment"),
            span=_span(start, end),
        )
        if any(key[0] is not None for key in attempt_keys):
            note = LABELS["moments"]["attempt_note"].format(
                attempts=_plural(len(attempt_keys), "attempt"),
                moments=_plural(len(group["findings"]), "moment"),
                span=_span(start, end),
            )
        else:
            note = moments_note
        opened = " open" if group is open_group else ""
        out.append(f'<details class="puzzle"{opened}>')
        out.append(
            f'<summary>{_e(_group_title(beat))}'
            f'<span class="note">{_e(note)}</span></summary>'
        )
        out.append('<div class="puzzle-body">')
        for attempt_key in attempt_keys:
            findings = group["attempts"][attempt_key]
            attempt = attempt_key[0]
            findings = sorted(findings, key=lambda f: (f["time_s"], f["rank"]))
            if attempt is not None:
                attempt_start = _first_set(
                    attempt_key[1], min(f["time_s"] for f in findings)
                )
                attempt_end = _first_set(
                    attempt_key[2], max(_moment_end(f) for f in findings)
                )
                out.append(
                    f'<h4>{_e(LABELS["moments"]["attempt"].format(n=attempt, start=_mss(attempt_start), end=_mss(attempt_end)))}</h4>'
                )
            out.extend(
                _render_card(finding, markers_by_moment, pins_available)
                for finding in findings
            )
        out.extend(["</div>", "</details>"])
    return out


def _render_dropped(dropped):
    items = []
    for finding in dropped:
        info = _kind(finding["kind"])
        reason = finding["check"].get("note")
        note_html = ""
        if reason:
            note_html = (
                f' <span class="note">'
                f'{_e(LABELS["dropped"]["reason"].format(note=reason))}</span>'
            )
        items.append(
            f'<li><b>{_mss(finding["time_s"])}, {_e(info["lower"])}.</b> '
            f'{_e(finding["summary"])}{note_html}</li>'
        )
    note = LABELS["dropped"]["note"].format(n=len(dropped))
    return [
        '<section aria-labelledby="dropped">',
        f'<h2 id="dropped">{LABELS["sections"]["dropped"]}</h2>',
        "<details>",
        f"<summary>{_e(note)}</summary>",
        f'<ul class="dropped">{"".join(items)}</ul>',
        "</details>",
        "</section>",
    ]


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
    markers_by_moment = {}
    for marker in markers:
        moment = marker.get("moment")
        if moment:
            markers_by_moment.setdefault(moment, []).append(marker)

    route = data.get("route")
    map_state = None
    if route is not None:
        map_state = _load_map(route["map"], maps_dir)
        if map_state is None:
            print(
                LABELS["warning"].format(map=repr(route["map"])),
                file=sys.stderr,
            )
    pins_available = map_state is not None
    # The time control needs a drawn route: without one the page has no script.
    timeline = pins_available and len(route["points"]) >= 2
    pinned = [
        finding for finding in kept if finding.get("at") is not None
    ] if pins_available else []

    parts = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{_e(LABELS['title'].format(id=session['id']))}"
        f"{', ' + _e(session['player']) if session.get('player') else ''}</title>",
        "<style>",
        STYLE.strip(),
        "</style>",
        "</head>",
        "<body>",
        "<main>",
    ]
    parts.extend(_render_header(data))

    if summary is not None:
        parts.extend(_render_tiles(summary, session["duration_s"]))
    if data.get("cross_player"):
        parts.extend(_render_across(data["cross_player"], id_to_rank))
    if map_state is not None:
        parts.extend(
            _render_map_section(
                data, map_state, pinned, markers, id_to_rank, timeline
            )
        )

    parts.extend(
        [
            '<section aria-labelledby="moments">',
            f'<h2 id="moments">{LABELS["sections"]["moments"]}</h2>',
            f'<p class="sub">{_e(LABELS["moments"]["sub"])}</p>',
        ]
    )
    if timeline:
        parts.append(_render_span_note())
    parts.extend(_render_groups(kept, markers_by_moment, pins_available))
    parts.append("</section>")

    if dropped:
        parts.extend(_render_dropped(dropped))

    parts.append("</main>")
    if timeline:
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
