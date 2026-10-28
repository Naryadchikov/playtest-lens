"""Route, heat, pins, markers and summary computed from a session log.

One path: the log is already loaded by log_candidates.load_log and the
findings are already checked. This module only adds the optional fields
the report page draws (route, markers, summary, finding.at), and makes
no model call. analyzer/check.py calls it once after assign_beats when
a log is given, and `python -m analyzer.spatial` re-runs it alone on an
existing findings file.

Which map: the report draws one map per report, the one whose scene
held the most time with position samples. Without a matching map file
no route, no pin and no marker is written, and one stderr line names
the scene. One map per report is a known limit (docs/FOLLOWUPS.md).

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
import sys
from pathlib import Path

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

KIND_ORDER = ("stuck", "confused", "surprised", "suspected_bug")

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


# Map name and meta for a scene path, from report/maps/*.json.
def _maps():
    maps = {}
    if not MAPS_DIR.is_dir():
        return maps
    for path in sorted(MAPS_DIR.glob("*.json")):
        meta = json.loads(path.read_text(encoding="utf-8"))
        scene = meta.get("scene")
        if isinstance(scene, str) and scene not in maps:
            maps[scene] = (path.stem, meta)
    return maps


# The scene the report draws: the most time with samples, then its map
# file. Ties go to the scene seen first. An unmapped scene that holds
# the most time gives no map at all, and one stderr line names it.
def _choose_scene(samples, scene_order):
    if not scene_order:
        print(
            "the log names no scene: no route, at or markers written",
            file=sys.stderr,
        )
        return None, None, None
    scene_times = _scene_times(samples, scene_order)
    scene = max(
        scene_order,
        key=lambda name: (scene_times.get(name, 0.0), -scene_order.index(name)),
    )
    maps = _maps()
    if scene in maps:
        map_name, meta = maps[scene]
        return scene, map_name, meta
    print(
        f"no map file for scene {scene!r}: no route, at or markers written",
        file=sys.stderr,
    )
    return None, None, None


# Keep the first and the last sample, and at least ROUTE_MIN_STEP_S
# between the others. When the last sample is closer than that to the
# one before, the one before it is dropped unless it is the first.
def _downsample(samples):
    if not samples:
        return []
    kept = [samples[0]]
    for sample in samples[1:-1]:
        if sample["t"] - kept[-1]["t"] >= ROUTE_MIN_STEP_S:
            kept.append(sample)
    last = samples[-1]
    if last is not kept[-1]:
        if len(kept) > 1 and last["t"] - kept[-1]["t"] < ROUTE_MIN_STEP_S:
            kept.pop()
        kept.append(last)
    return kept


def _cell_key(x, z):
    return (math.floor(x / HEAT_CELL_M), math.floor(z / HEAT_CELL_M))


# Heat spots from time spent: each pair of consecutive samples in one
# visit adds min(dt, SAMPLE_MAX_GAP_S) to the earlier sample's cell.
# Cells at or over HEAT_MIN_S merge with their 8-neighbours into one
# spot; the centre of mass and the rms distance are weighted by that
# time. The six longest spots are kept, biggest first.
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
            _cell_key(previous["x"], previous["z"]),
            {"seconds": 0.0, "sum_x": 0.0, "sum_z": 0.0},
        )
        cell["seconds"] += weight
        cell["sum_x"] += weight * previous["x"]
        cell["sum_z"] += weight * previous["z"]

    hot = {key: cell for key, cell in cells.items() if cell["seconds"] >= HEAT_MIN_S}
    seen = set()
    spots = []
    for key in sorted(hot):
        if key in seen:
            continue
        seen.add(key)
        component = []
        stack = [key]
        while stack:
            cell_key = stack.pop()
            component.append(cell_key)
            for step_x in (-1, 0, 1):
                for step_z in (-1, 0, 1):
                    if step_x == 0 and step_z == 0:
                        continue
                    neighbour = (cell_key[0] + step_x, cell_key[1] + step_z)
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
        spots.append(
            {
                "x": round(centre_x, 2),
                "z": round(centre_z, 2),
                "r_m": round(max(HEAT_MIN_R_M, rms), 2),
                "seconds": round(total, 2),
            }
        )
    spots.sort(key=lambda spot: (-spot["seconds"], spot["x"], spot["z"]))
    return spots[:HEAT_MAX_SPOTS]


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


# Move later-ranked pins apart in image space, a fixed 60 px step along
# +x then +z, checked against the pins already placed. Drawing aid only.
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
        finding["at"] = {"x": round(x, 2), "z": round(z, 2)}
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
                "moment": moment,
            }
        )
    return entries


# Union length of the kept stuck and confused spans, overlaps once.
def _lost_s(findings):
    spans = []
    for finding in findings:
        if finding["check"]["verdict"] != "keep":
            continue
        if finding["kind"] not in ("stuck", "confused"):
            continue
        end_s = finding.get("end_s")
        if end_s is None or end_s <= finding["time_s"]:
            continue
        spans.append((finding["time_s"], float(end_s)))
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
    }


def enrich(data, events, video_flash_s):
    """Add route, markers, summary and finding.at to a findings dict.

    Returns the same dict, changed in place. Raises ValueError when the
    log has no sync_flash line. Running it twice gives the same file.
    """
    offset = _offset(events, video_flash_s)
    samples, marker_lines, scene_order = _collect(events, offset)
    findings = data.get("findings", [])
    scene, map_name, meta = _choose_scene(samples, scene_order)

    if scene is None:
        data.pop("route", None)
        data.pop("markers", None)
        for finding in findings:
            finding.pop("at", None)
    else:
        in_scene = [sample for sample in samples if sample["scene"] == scene]
        route_samples = [
            sample for sample in in_scene if sample["t"] >= video_flash_s
        ]
        data["route"] = {
            "scene": scene,
            "map": map_name,
            "points": [
                [sample["t"], round(sample["x"], 2), round(sample["z"], 2)]
                for sample in _downsample(route_samples)
            ],
            "heat": _heat(route_samples),
        }

        kept = []
        for finding in findings:
            if finding["check"]["verdict"] != "keep":
                finding.pop("at", None)
                continue
            kept.append(finding)
            nearest = _nearest(in_scene, finding["time_s"])
            if nearest is None:
                finding.pop("at", None)
            else:
                finding["at"] = {
                    "x": round(nearest["x"], 2),
                    "z": round(nearest["z"], 2),
                }
        pinned = sorted(
            (finding for finding in kept if finding.get("at") is not None),
            key=lambda finding: finding["rank"],
        )
        _nudge(pinned, meta)
        data["markers"] = _markers(marker_lines, in_scene, kept, scene)

    data["summary"] = _summary(findings)
    return data


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Add the route, heat, markers and summary fields to a findings file, from a session log."
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

    data = findings_module.load(args.findings)
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
