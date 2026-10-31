"""Route, floors, heat, pins, markers, zones, events and summary from a log.

One path: the log is already loaded by log_candidates.load_log and the
findings are already checked. This module only adds the optional fields
the report page draws (route, markers, zones, events, summary,
finding.at), and makes no model call. analyzer/check.py calls it once
after assign_beats when a log is given, and `python -m analyzer.spatial`
re-runs it alone on an existing findings file.

Which map: the report draws one scene, the one that held the most time
with position samples. A scene may have several map files, one per
floor: they share the scene and are ordered by `y_floor_min` (none for
the ground floor). A sample is on the highest floor whose `y_floor_min`
is at or below its height. Without a matching map file no route, no pin
and no marker is written, and one stderr line names the scene. One
scene per report is a known limit (docs/FOLLOWUPS.md).

All times are video seconds, mapped through the first sync_flash the
same way log_candidates.find_candidates does. Coordinates are world
metres, rounded to 2 decimals. Pause and resume lines close a visit:
positions between them are ignored, and heat never bridges a pause.

The thresholds and the pin nudge below are a proposal (Claude Sonnet
5.5, 2026-10-28), not Sasha's decision. Pin positions are a drawing
aid: a nudge keeps two numbered labels legible, it does not change
where the player was.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

from analyzer import beats
from analyzer import findings as findings_module
from analyzer import log_candidates

MAPS_DIR = Path(__file__).resolve().parent.parent / "report" / "maps"

HEAT_CELL_M = 2.0
HEAT_MIN_S = 15.0
HEAT_MIN_R_M = 1.5
HEAT_MAX_SPOTS = 6
ROUTE_MIN_STEP_S = 1.0
# A longer gap than this has no samples in it: for heat it counts as one
# step, and for map choice it is not time with samples.
SAMPLE_MAX_GAP_S = 2.0
POSITION_NEAR_S = 3.0
PIN_SEPARATION_PX = 55.0
PIN_STEP_PX = 60.0
PIN_NUDGE_LIMIT = 100

# The top-level fields enrich writes. The command line drops them first.
OWNED_BLOCKS = ("route", "markers", "zones", "events", "summary")

KIND_ORDER = ("stuck", "confused", "surprised", "suspected_bug")

# The problems block (summary.problems). Proposal by Claude Opus 5.5,
# 2026-11-01, not Sasha's rule: Sasha decides the numbers.
PROBLEM_FRICTION = ("blocked", "stuck")
PROBLEMS_MAX = 5

# Sasha owns the wording; the page only prints it.
VERDICT = {
    "found": "{kept} {noun} worth a look: {parts}.",
    "nouns": ("moment", "moments"),
    "none": "No problem moments found.",
    "kinds": {
        "stuck": "{n} stuck",
        "confused": "{n} confused",
        "surprised": "{n} surprised",
        "suspected_bug": "{n} suspected bug",
    },
}

# Game event lines the page lists, and their labels, from the log's own
# values only. A door or lock path is the scene's node path
# ("BREAK_ROOM/kitchenSink/CabinetDoor"): its first segment is the room
# and its second the thing the designer placed; the rest is the prefab's
# own parts. The label names the thing in words and the room in
# parentheses: "Kitchen sink opened (Break room)". Proposal (Claude
# Fable 5.1, 2026-11-01), not Sasha's wording; the templates were Claude
# Opus 5.5's (2026-11-01).
EVENT_WORDS = {
    "door": {True: "{name} opened", False: "{name} closed"},
    "lock": {True: "{name} locked", False: "{name} unlocked"},
    "pickup": "Picked up {item}",
    "quest": "{quest} {step}",
    "pause": "Paused",
    "resume": "Resumed",
    "where": "{label} ({room})",
}

# Word boundaries in a node name: underscores, camel case, and a run of
# digits with the letters stuck to it ("Body3D" is "Body" and "3D").
_WORD = re.compile(r"[A-Z]+(?![a-z])|[A-Z]?[a-z]+|\d+[A-Za-z]*")


# "kitchenCabinet4" -> "Kitchen cabinet 4"; "UPPER_OFFICE_CEO" -> "Upper
# office CEO" (a short all-caps token is an abbreviation and stays).
def _words(name):
    tokens = _WORD.findall(str(name))
    if not tokens:
        return str(name)
    out = []
    for index, token in enumerate(tokens):
        if token.isupper() and len(token) <= 3 and index > 0:
            out.append(token)
        else:
            out.append(token.capitalize() if index == 0 else token.lower())
    return " ".join(out)


def _offset(events, video_flash_s):
    first_flash = next((e for e in events if e.get("event") == "sync_flash"), None)
    if first_flash is None:
        raise ValueError(
            "log has no sync_flash line, so log times cannot be mapped to video time"
        )
    return float(video_flash_s) - float(first_flash["t"])


# One pass over the log: position samples with video time and scene,
# marker lines with video time and scene, and the scenes in first-seen
# order. A visit counter rises at every scene, pause and resume line so
# heat never bridges a scene load or a pause.
def _collect(events, offset):
    scene = None
    paused = False
    visit = 0
    samples = []
    markers = []
    scene_order = []
    for event in events:
        kind = event.get("event")
        if kind == "scene":
            scene = event.get("scene")
            if scene not in scene_order:
                scene_order.append(scene)
            visit += 1
        elif kind == "pause":
            paused = True
            visit += 1
        elif kind == "resume":
            paused = False
            visit += 1
        elif kind == "position":
            if paused:
                continue
            samples.append(
                {
                    "scene": scene,
                    "t": round(float(event["t"]) + offset, 2),
                    "x": float(event["x"]),
                    "y": None if event.get("y") is None else float(event["y"]),
                    "z": float(event["z"]),
                    "visit": visit,
                }
            )
        elif kind == "marker":
            markers.append(
                {"scene": scene, "t": round(float(event["t"]) + offset, 2)}
            )
    return samples, markers, scene_order


# Time with samples per scene: consecutive samples in one visit, capped
# at SAMPLE_MAX_GAP_S so a long silence counts as one step, not as time
# spent there.
def _scene_times(samples, scene_order):
    totals = {scene: 0.0 for scene in scene_order}
    for previous, current in zip(samples, samples[1:]):
        if current["scene"] is None:
            continue
        if (
            previous["scene"] != current["scene"]
            or previous["visit"] != current["visit"]
        ):
            continue
        step = current["t"] - previous["t"]
        if step > 0:
            totals[current["scene"]] += min(step, SAMPLE_MAX_GAP_S)
    return totals


# Each scene's floors, from report/maps/*.json: a list of (map name,
# meta), the ground floor (no y_floor_min) first, then by y_floor_min.
def _maps():
    maps = {}
    if not MAPS_DIR.is_dir():
        return maps
    for path in sorted(MAPS_DIR.glob("*.json")):
        meta = json.loads(path.read_text(encoding="utf-8"))
        scene = meta.get("scene")
        if isinstance(scene, str):
            maps.setdefault(scene, []).append((path.stem, meta))
    for floors in maps.values():
        floors.sort(
            key=lambda floor: (
                floor[1].get("y_floor_min") is not None,
                floor[1].get("y_floor_min") or 0.0,
            )
        )
    return maps


# The scene the report draws: the most time with samples, then its map
# files. Ties go to the scene seen first. An unmapped scene that holds
# the most time gives no map at all, and one stderr line names it.
def _choose_scene(samples, scene_order):
    if not scene_order:
        print(
            "the log names no scene: no route, at or markers written",
            file=sys.stderr,
        )
        return None, None
    scene_times = _scene_times(samples, scene_order)
    scene = max(
        scene_order,
        key=lambda name: (scene_times.get(name, 0.0), -scene_order.index(name)),
    )
    maps = _maps()
    if scene in maps:
        return scene, maps[scene]
    print(
        f"no map file for scene {scene!r}: no route, at or markers written",
        file=sys.stderr,
    )
    return None, None


# The highest floor whose y_floor_min is at or below y. A sample with
# no height is on the ground floor.
def _floor_of(y, floors):
    floor = 0
    if y is None:
        return floor
    for index, (_name, meta) in enumerate(floors):
        floor_min = meta.get("y_floor_min")
        if floor_min is not None and floor_min <= y:
            floor = index
    return floor


# Runs of consecutive route samples on one floor. A run ends where the
# next one starts, so the spans tile the route's time.
def _floor_spans(samples):
    spans = []
    for sample in samples:
        if spans and spans[-1]["floor"] == sample["floor"]:
            continue
        if spans:
            spans[-1]["end_s"] = sample["t"]
        spans.append(
            {"floor": sample["floor"], "start_s": sample["t"], "end_s": sample["t"]}
        )
    if spans:
        spans[-1]["end_s"] = samples[-1]["t"]
    return spans


# Keep the first and the last sample, every sample where the floor
# changes (so each floor span has a route point), and at least
# ROUTE_MIN_STEP_S between the others. When the last sample is closer
# than that to the one before, the one before it is dropped unless it is
# the first or a floor change.
def _downsample(samples):
    if not samples:
        return []
    kept = [samples[0]]
    for sample in samples[1:-1]:
        if (
            sample["t"] - kept[-1]["t"] >= ROUTE_MIN_STEP_S
            or sample["floor"] != kept[-1]["floor"]
        ):
            kept.append(sample)
    last = samples[-1]
    if last is not kept[-1]:
        if (
            len(kept) > 1
            and last["t"] - kept[-1]["t"] < ROUTE_MIN_STEP_S
            and kept[-1]["floor"] == kept[-2]["floor"]
        ):
            kept.pop()
        kept.append(last)
    return kept


def _cell_key(x, z):
    return (math.floor(x / HEAT_CELL_M), math.floor(z / HEAT_CELL_M))


# Heat spots from time spent, per floor: each pair of consecutive
# samples in one visit adds min(dt, SAMPLE_MAX_GAP_S) to the earlier
# sample's cell on the earlier sample's floor, so a room upstairs never
# mixes with the room below it. Cells at or over HEAT_MIN_S merge with
# their 8-neighbours on the same floor into one spot; the centre of
# mass and the rms distance are weighted by that time. Each floor keeps
# its six longest spots; the list runs by floor, biggest first.
def _heat(samples):
    cells = {}
    for previous, current in zip(samples, samples[1:]):
        if previous["visit"] != current["visit"]:
            continue
        step = current["t"] - previous["t"]
        if step <= 0:
            continue
        weight = min(step, SAMPLE_MAX_GAP_S)
        cell = cells.setdefault(
            (previous["floor"], *_cell_key(previous["x"], previous["z"])),
            {"seconds": 0.0, "sum_x": 0.0, "sum_z": 0.0},
        )
        cell["seconds"] += weight
        cell["sum_x"] += weight * previous["x"]
        cell["sum_z"] += weight * previous["z"]

    hot = {key: cell for key, cell in cells.items() if cell["seconds"] >= HEAT_MIN_S}
    seen = set()
    by_floor = {}
    for key in sorted(hot):
        if key in seen:
            continue
        seen.add(key)
        component = []
        stack = [key]
        while stack:
            cell_key = stack.pop()
            component.append(cell_key)
            floor, cell_x, cell_z = cell_key
            for step_x in (-1, 0, 1):
                for step_z in (-1, 0, 1):
                    if step_x == 0 and step_z == 0:
                        continue
                    neighbour = (floor, cell_x + step_x, cell_z + step_z)
                    if neighbour in hot and neighbour not in seen:
                        seen.add(neighbour)
                        stack.append(neighbour)
        total = sum(hot[cell_key]["seconds"] for cell_key in component)
        centre_x = sum(hot[cell_key]["sum_x"] for cell_key in component) / total
        centre_z = sum(hot[cell_key]["sum_z"] for cell_key in component) / total
        spread = 0.0
        for cell_key in component:
            cell = hot[cell_key]
            cell_x = cell["sum_x"] / cell["seconds"]
            cell_z = cell["sum_z"] / cell["seconds"]
            spread += cell["seconds"] * (
                (cell_x - centre_x) ** 2 + (cell_z - centre_z) ** 2
            )
        rms = math.sqrt(spread / total)
        by_floor.setdefault(key[0], []).append(
            {
                "x": round(centre_x, 2),
                "z": round(centre_z, 2),
                "r_m": round(max(HEAT_MIN_R_M, rms), 2),
                "seconds": round(total, 2),
                "floor": key[0],
            }
        )
    spots = []
    for floor in sorted(by_floor):
        floor_spots = by_floor[floor]
        floor_spots.sort(key=lambda spot: (-spot["seconds"], spot["x"], spot["z"]))
        spots.extend(floor_spots[:HEAT_MAX_SPOTS])
    return spots


# The nearest sample within POSITION_NEAR_S, earlier wins a tie.
def _nearest(samples, time_s):
    best = None
    best_key = None
    for sample in samples:
        distance = abs(sample["t"] - time_s)
        if distance > POSITION_NEAR_S:
            continue
        key = (distance, sample["t"])
        if best_key is None or key < best_key:
            best_key = key
            best = sample
    return best


# Move later pins apart in image space, a fixed 60 px step along +x
# then +z, checked against the pins already placed on the same floor.
# Drawing aid only: the floor never changes.
def _nudge(pinned, meta):
    scale_x = meta["px_width"] / (meta["world_max_x"] - meta["world_min_x"])
    scale_z = meta["px_height"] / (meta["world_max_z"] - meta["world_min_z"])
    step_x = PIN_STEP_PX / scale_x
    step_z = PIN_STEP_PX / scale_z
    placed = []
    for finding in pinned:
        x = finding["at"]["x"]
        z = finding["at"]["z"]
        for attempt in range(PIN_NUDGE_LIMIT):
            too_close = any(
                math.hypot((x - other_x) * scale_x, (z - other_z) * scale_z)
                < PIN_SEPARATION_PX
                for other_x, other_z in placed
            )
            if not too_close:
                break
            if attempt % 2 == 0:
                x = round(x + step_x, 2)
            else:
                z = round(z + step_z, 2)
        finding["at"] = {"x": round(x, 2), "z": round(z, 2), "floor": finding["at"]["floor"]}
        placed.append((finding["at"]["x"], finding["at"]["z"]))


# One entry per F9 marker line in the route's scene, linked to the kept
# finding whose padded span holds it, when there is one.
def _markers(marker_lines, samples, kept, scene):
    entries = []
    for line in marker_lines:
        if line["scene"] != scene:
            continue
        nearest = _nearest(samples, line["t"])
        if nearest is None:
            continue
        moment = None
        best_key = None
        for finding in kept:
            end_s = finding.get("end_s")
            if end_s is None:
                end_s = finding["time_s"]
            start = finding["time_s"] - 5.0
            end = max(end_s, finding["time_s"]) + 5.0
            if not start <= line["t"] <= end:
                continue
            key = (abs(finding["time_s"] - line["t"]), finding["time_s"])
            if best_key is None or key < best_key:
                best_key = key
                moment = finding["id"]
        entries.append(
            {
                "t": round(line["t"], 2),
                "x": round(nearest["x"], 2),
                "z": round(nearest["z"], 2),
                "floor": nearest["floor"],
                "moment": moment,
            }
        )
    return entries


# Time the player spent stuck or blocked: the union length of the
# attempt or visit spans (beat.attempt_start_s to beat.attempt_end_s)
# of the kept findings whose check.friction is stuck or blocked, each
# overlap counted once. A finding with no usable beat span falls back
# to its own time_s to end_s. "by design" (learning) moments never
# count, and a single moment counts its whole visit, never zero.
# Proposal (Claude Fable 5.1, 2026-11-01), not Sasha's rule: it replaces
# the first rule (the length of merged stuck and confused moments),
# which counted a single moment as zero and a learning moment as lost.
LOST_FRICTION = ("stuck", "blocked")


def _lost_span(finding):
    beat = finding.get("beat") or {}
    start = beat.get("attempt_start_s")
    end = beat.get("attempt_end_s")
    if start is None or end is None or end <= start:
        start, end = finding["time_s"], finding.get("end_s")
    if end is None or end <= start:
        return None
    return (float(start), float(end))


def _lost_s(findings):
    spans = []
    for finding in findings:
        if finding["check"]["verdict"] != "keep":
            continue
        if finding["check"].get("friction") not in LOST_FRICTION:
            continue
        span = _lost_span(finding)
        if span is not None:
            spans.append(span)
    lost = 0.0
    current_start = None
    current_end = None
    for start, end in sorted(spans):
        if current_end is None or start > current_end:
            if current_end is not None:
                lost += current_end - current_start
            current_start, current_end = start, end
        else:
            current_end = max(current_end, end)
    if current_end is not None:
        lost += current_end - current_start
    return round(lost, 2)


# The worst places for the problems block: kept findings by area and
# puzzle across visits (a puzzle by area and puzzle, an area without a
# puzzle by area), only places with a kept finding at stuck or blocked
# friction. Worst friction first, then time stuck (the lost_s rule),
# then the earliest moment; at most PROBLEMS_MAX. A finding without a
# beat has no place and is left out.
def _problems(findings):
    places = {}
    for finding in sorted(findings, key=lambda f: f["time_s"]):
        beat = finding.get("beat")
        if finding["check"]["verdict"] != "keep" or not beat or not beat.get("area"):
            continue
        key = (beat["area"], beat.get("puzzle"))
        places.setdefault(key, []).append(finding)
    problems = []
    for (area, puzzle), group in places.items():
        frictions = {f["check"].get("friction") for f in group}
        worst = next((name for name in PROBLEM_FRICTION if name in frictions), None)
        if worst is None:
            continue
        outcomes = {f["check"].get("resolved") for f in group} & {"solved", "abandoned"}
        if len(outcomes) == 2:
            resolved = "mixed"
        elif outcomes:
            resolved = outcomes.pop()
        else:
            resolved = "unknown"
        visits = {
            (f["beat"].get("attempt"), f["beat"].get("attempt_start_s")) for f in group
        }
        lost_s = _lost_s(group)
        order = (PROBLEM_FRICTION.index(worst), -lost_s, group[0]["time_s"])
        problems.append(
            (
                order,
                {
                    "place": f"{area}, {puzzle}" if puzzle else area,
                    "moments": [f["id"] for f in group],
                    "attempts": len(visits),
                    "lost_s": lost_s,
                    "friction": worst,
                    "resolved": resolved,
                },
            )
        )
    problems.sort(key=lambda entry: entry[0])
    return [problem for _order, problem in problems[:PROBLEMS_MAX]]


def _summary(findings):
    counts = {kind: 0 for kind in KIND_ORDER}
    kept = 0
    dropped = 0
    for finding in findings:
        verdict = finding["check"]["verdict"]
        if verdict == "keep":
            kept += 1
            counts[finding["kind"]] += 1
        elif verdict == "drop":
            dropped += 1
    if kept:
        parts = ", ".join(
            VERDICT["kinds"][kind].format(n=counts[kind])
            for kind in KIND_ORDER
            if counts[kind]
        )
        noun = VERDICT["nouns"][kept != 1]
        verdict = VERDICT["found"].format(kept=kept, noun=noun, parts=parts)
    else:
        verdict = VERDICT["none"]
    return {
        "verdict": verdict,
        "lost_s": _lost_s(findings),
        "counts": counts,
        "kept": kept,
        "dropped": dropped,
        "problems": _problems(findings),
    }


# One label per game event line, from the line's own values.
def _event_label(event):
    kind = event["event"]
    words = EVENT_WORDS[kind]
    if kind in ("door", "lock"):
        segments = [part for part in str(event.get("path", "")).split("/") if part]
        state = bool(event.get("open" if kind == "door" else "locked"))
        name = _words(segments[1] if len(segments) > 1 else segments[0] if segments else "")
        label = words[state].format(name=name)
        if len(segments) > 1:
            label = EVENT_WORDS["where"].format(label=label, room=_words(segments[0]))
        return label
    if kind == "pickup":
        return words.format(item=event.get("item", ""))
    if kind == "quest":
        return words.format(quest=_words(event.get("quest", "")), step=event.get("step", ""))
    return words


# Door, pickup, quest, lock, pause and resume lines in video time,
# inside the recording.
def _events(events, offset, duration_s):
    entries = []
    for event in events:
        if event.get("event") not in EVENT_WORDS:
            continue
        t = round(float(event["t"]) + offset, 2)
        if not 0 <= t <= duration_s:
            continue
        entries.append({"t": t, "kind": event["event"], "label": _event_label(event)})
    return entries


def enrich(data, events, video_flash_s):
    """Add route, markers, zones, events, summary and finding.at.

    Returns the same dict, changed in place. Raises ValueError when the
    log has no sync_flash line. Running it twice gives the same file.
    """
    offset = _offset(events, video_flash_s)
    samples, marker_lines, scene_order = _collect(events, offset)
    findings = data.get("findings", [])
    scene, floors = _choose_scene(samples, scene_order)

    if scene is None:
        data.pop("route", None)
        data.pop("markers", None)
        for finding in findings:
            finding.pop("at", None)
    else:
        in_scene = [sample for sample in samples if sample["scene"] == scene]
        for sample in in_scene:
            sample["floor"] = _floor_of(sample["y"], floors)
        route_samples = [
            sample for sample in in_scene if sample["t"] >= video_flash_s
        ]
        data.pop("route", None)
        data["route"] = {
            "scene": scene,
            "maps": [name for name, _meta in floors],
            "points": [
                [sample["t"], round(sample["x"], 2), round(sample["z"], 2), sample["floor"]]
                for sample in _downsample(route_samples)
            ],
            "heat": _heat(route_samples),
            "floor_spans": _floor_spans(route_samples),
        }

        kept = []
        for finding in findings:
            if finding["check"]["verdict"] == "keep":
                kept.append(finding)
            nearest = _nearest(in_scene, finding["time_s"])
            if nearest is None:
                finding.pop("at", None)
            else:
                finding["at"] = {
                    "x": round(nearest["x"], 2),
                    "z": round(nearest["z"], 2),
                    "floor": nearest["floor"],
                }
        # Kept pins by rank, then dropped ones by time, so a dropped
        # pin moves aside and a kept pin never does for it.
        pinned = sorted(
            (finding for finding in findings if finding.get("at") is not None),
            key=lambda finding: (
                finding["rank"] is None,
                finding["rank"] or 0,
                finding["time_s"],
            ),
        )
        for floor, (_name, meta) in enumerate(floors):
            _nudge([f for f in pinned if f["at"]["floor"] == floor], meta)
        data["markers"] = _markers(marker_lines, in_scene, kept, scene)

    # The room visits the strip draws, the same intervals beats uses.
    data["zones"] = beats.zone_intervals(events, video_flash_s)
    data["events"] = _events(events, offset, data["session"]["duration_s"])
    data["summary"] = _summary(findings)
    return data


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Add the route, floors, heat, markers, zones, events and summary fields to a findings file, from a session log."
    )
    parser.add_argument("findings", help="finding JSON to enrich")
    parser.add_argument("--log", required=True, help="session event log (JSONL)")
    parser.add_argument(
        "--video-flash-s",
        type=float,
        required=True,
        help="video time of the first sync_flash",
    )
    parser.add_argument(
        "-o",
        "--out",
        default=None,
        help="output path (default: the findings file, rewritten)",
    )
    args = parser.parse_args(argv)

    # The blocks this step owns are rewritten from the log, so a file
    # written in an older format of them still upgrades here.
    data = findings_module.read(args.findings)
    if isinstance(data, dict):
        for name in OWNED_BLOCKS:
            data.pop(name, None)
        for finding in data.get("findings") or []:
            if isinstance(finding, dict):
                finding.pop("at", None)
    findings_module.check(data)
    events = log_candidates.load_log(args.log)
    try:
        enrich(data, events, args.video_flash_s)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    out_path = Path(args.out) if args.out else Path(args.findings)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    # Prove the enriched file is still in the one format.
    findings_module.load(out_path)
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
