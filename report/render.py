"""Render a findings.json file as one self-contained HTML page.

The page only renders what the file holds. It computes nothing beyond
formatting seconds as m:ss, converting a route or pin world point to
image pixels with the map's JSON, and the structural counts a group or
a pin list needs. Group order and card order come from the file's
rank and beat fields.

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
        "sub": "Grouped by area, puzzle and attempt. The worst puzzle is open. Time is from the recording's start flash.",
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
        "alt": "Top-down plan of the {level} level. The player's route, a heat layer where they lingered, and numbered pins are drawn on top.",
        "title": "Route and pins on the {level} map",
        "level": "level",
        "marker": "F9 marker at {time}",
        "figcaption": "Pins are numbered by rank; the list beside the map gives each pin's kind and time.",
        "legend": [
            ("<svg viewBox=\"0 0 28 20\" aria-hidden=\"true\"><path d=\"M3 10H25\" stroke=\"#dbe7ff\" stroke-width=\"3\"/><path d=\"M18 5L26 10L18 15z\" fill=\"#fff\"/></svg>", "Route, arrows point the way walked (start circle to end circle)"),
            ("<svg viewBox=\"0 0 28 20\" aria-hidden=\"true\"><circle cx=\"14\" cy=\"10\" r=\"8\" fill=\"#ff6b3d\" fill-opacity=\".6\" stroke=\"#ffb199\" stroke-dasharray=\"3 2\"/></svg>", "Lingered or looped, dashed ring with time spent"),
            ("<svg viewBox=\"0 0 28 20\" aria-hidden=\"true\"><polygon points=\"14,2 22,6 22,14 14,18 6,14 6,6\" fill=\"#0b1020\" stroke=\"#fff\" stroke-dasharray=\"3 2\"/></svg>", "F9: the player flagged confusion"),
        ],
        "legend_title": "Map legend and pin list",
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
a:focus-visible, summary:focus-visible { outline: 3px solid var(--accent); outline-offset: 2px; border-radius: 3px; }
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
.tiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: var(--s3); }
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
.map { position: relative; margin: 0; border: 1px solid var(--line); border-radius: 6px; overflow: hidden; background: #0a0d14; }
.map img, .map svg { display: block; width: 100%; height: auto; }
.map svg { position: absolute; inset: 0; height: 100%; }
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
@media (max-width: 760px) { .where { grid-template-columns: 1fr; } .tile.wide { grid-column: auto; } }
@media (prefers-reduced-motion: no-preference) { .pin .shape, a.chip { transition: stroke-width .15s, border-color .15s; } html { scroll-behavior: smooth; } }
@media print {
  body { background: #fff; color: #000; } main { max-width: none; padding: 0; }
  .card, .group, .tile { break-inside: avoid; } .clip, .to-map { display: none; }
  .map { max-width: 300px; }
}
"""

SVG_DEFS = """<defs>
          <radialGradient id="heat"><stop offset="0" stop-color="#ff6b3d" stop-opacity=".8"/><stop offset=".6" stop-color="#ff6b3d" stop-opacity=".4"/><stop offset="1" stop-color="#ff6b3d" stop-opacity="0"/></radialGradient>
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
    puzzle = beat.get("puzzle") or beat.get("area")
    if not puzzle:
        return LABELS["moments"]["fallback"]
    attempt = beat.get("attempt")
    if isinstance(attempt, int) and attempt > 1:
        return f"{puzzle}, attempt {attempt}"
    return puzzle


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
    parts = ['<g aria-hidden="true">']
    for spot in route["heat"]:
        cx, cy = world_to_px(meta, spot["x"], spot["z"])
        radius = spot["r_m"] * scale
        parts.append(
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{radius:.1f}" fill="url(#heat)"/>'
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{radius:.1f}" fill="none" '
            'stroke="#ffb199" stroke-width="5" stroke-dasharray="14 10"/>'
        )
        parts.append(
            f'<text class="halo" x="{cx:.1f}" y="{cy - radius - 15:.1f}">'
            f'{_mss(spot["seconds"])}</text>'
        )
    parts.append("</g>")
    return parts


def _route_pixels(route, meta):
    return [world_to_px(meta, point[1], point[2]) for point in route["points"]]


def _render_arrows(pixels):
    arrows = []
    for index in range(4, len(pixels), 4):
        x0, y0 = pixels[index - 1]
        x1, y1 = pixels[index]
        if x0 == x1 and y0 == y1:
            continue
        angle = math.degrees(math.atan2(y1 - y0, x1 - x0))
        arrows.append(
            f'<path d="M-16,-12L16,0L-16,12z" '
            f'transform="translate({x1:.1f} {y1:.1f}) rotate({angle:.0f}) scale(1.3)"/>'
        )
    return arrows


def _render_route(route, meta):
    pixels = _route_pixels(route, meta)
    if len(pixels) < 2:
        return []
    points = " ".join(f"{x:.1f},{y:.1f}" for x, y in pixels)
    start_x, start_y = pixels[0]
    end_x, end_y = pixels[-1]
    parts = [
        '<g aria-hidden="true" fill="none" stroke-linejoin="round" stroke-linecap="round">',
        f'<polyline stroke="#0a0d14" stroke-width="16" points="{points}"/>',
        f'<polyline stroke="#dbe7ff" stroke-width="7" points="{points}"/>',
    ]
    arrows = _render_arrows(pixels)
    if arrows:
        parts.append(
            '<g fill="#fff" stroke="#0a0d14" stroke-width="4">'
            + "".join(arrows)
            + "</g>"
        )
    parts.append(
        f'<circle cx="{start_x:.1f}" cy="{start_y:.1f}" r="24" fill="#fff" '
        'stroke="#0a0d14" stroke-width="6"/>'
        f'<circle cx="{end_x:.1f}" cy="{end_y:.1f}" r="24" fill="#0a0d14" '
        'stroke="#fff" stroke-width="6"/>'
        f'<text x="{start_x:.1f}" y="{start_y + 58:.1f}" class="halo" '
        'style="font-size:34px">start</text>'
        f'<text x="{end_x:.1f}" y="{end_y + 68:.1f}" class="halo" '
        'style="font-size:34px" dx="-70">end</text>'
    )
    parts.append("</g>")
    return parts


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
                f'aria-label="{_e(label)}" transform="{transform}">'
                '<use href="#sh-f9" class="shape"/><text y="10">F9</text></a>'
            )
        else:
            parts.append(
                f'<g class="pin f9" id="pin-f{index}" '
                f'aria-label="{_e(label)}" transform="{transform}">'
                '<use href="#sh-f9" class="shape"/><text y="10">F9</text></g>'
            )
    return parts


def _render_legend():
    items = []
    for graphic, text in LABELS["map"]["legend"]:
        items.append(f"<li>{graphic}{_e(text)}</li>")
    for kind in KIND_ORDER:
        info = _kind(kind)
        items.append(
            f'<li><span class="k k-{info["class"]}"></span>{_e(info["label"])}</li>'
        )
    return items


def _render_map_section(data, map_state, pinned, markers, id_to_rank):
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
        f'<figure class="map" id="map">',
        f'<img src="{data_uri}" width="{width}" height="{height}" alt="{alt}">',
        f'<svg viewBox="0 0 {width} {height}" aria-labelledby="map-title">',
        f'<title id="map-title">{title}</title>',
        SVG_DEFS,
        "<!-- heat layer: one blob per place the player lingered, plus a dashed ring so it is not color alone -->",
    ]
    parts.extend(_render_heat(route, meta))
    parts.append("<!-- route: casing plus line, arrows show direction, S and E mark start and end -->")
    parts.extend(_render_route(route, meta))
    parts.append("<!-- kept findings, numbered by rank -->")
    parts.extend(_render_pins(pinned, meta))
    if markers:
        parts.append("<!-- F9 markers: the player pressed F9 to flag confusion -->")
        parts.extend(_render_markers(markers, meta, id_to_rank))
    parts.append("</svg>")
    parts.append(
        '<figcaption class="sr-only" style="position:absolute;left:-9999px">'
        f'{_e(LABELS["map"]["figcaption"])}</figcaption>'
    )
    parts.append("</figure>")

    parts.append(
        f'<aside class="legend" aria-label="{_e(LABELS["map"]["legend_title"])}">'
    )
    parts.append(f'<ul>{"".join(_render_legend())}</ul>')
    parts.append('<ol class="pinlist">')
    for finding in pinned:
        info = _kind(finding["kind"])
        rank = finding["rank"]
        parts.append(
            f'<li><a href="#m{rank}"><span class="num">{rank}</span>'
            f'<span class="k k-{info["class"]}"></span>{_e(_pin_title(finding))}'
            f'<time>{_mss(finding["time_s"])}</time></a></li>'
        )
    parts.extend(["</ol>", "</aside>", "</div>", "</section>"])
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
    parts = [f'<article class="card {info["class"]}" id="m{rank}">']

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


def _beat_key(finding):
    beat = finding.get("beat")
    if not beat:
        return None
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


def _group_title(beat):
    if not beat:
        return LABELS["moments"]["fallback"]
    area = beat.get("area") or beat.get("zone")
    puzzle = beat.get("puzzle")
    number = beat.get("puzzle_number")
    parts = []
    if area:
        parts.append(area)
    if puzzle and puzzle != area:
        if number is not None:
            parts.append(f"Puzzle {number}: {puzzle}")
        else:
            parts.append(puzzle)
    elif number is not None:
        parts.append(f"Puzzle {number}")
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
            findings = sorted(findings, key=lambda f: f["rank"])
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
            _render_map_section(data, map_state, pinned, markers, id_to_rank)
        )

    parts.extend(
        [
            '<section aria-labelledby="moments">',
            f'<h2 id="moments">{LABELS["sections"]["moments"]}</h2>',
            f'<p class="sub">{_e(LABELS["moments"]["sub"])}</p>',
        ]
    )
    parts.extend(_render_groups(kept, markers_by_moment, pins_available))
    parts.append("</section>")

    if dropped:
        parts.extend(_render_dropped(dropped))

    parts.extend(["</main>", "</body>", "</html>", ""])
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
