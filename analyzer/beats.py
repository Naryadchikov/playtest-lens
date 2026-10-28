"""Group kept findings into Areas, Puzzles, Attempts and Sub-beats.

Sasha, 2026-10-28, on the Talos report: moments are the wrong unit.
An Area is the larger place or objective. A Puzzle is one challenge
inside it. An Attempt is one visit to that Puzzle: the player may
leave, solve something else, and come back for Attempt 2. A Sub-beat
is one kept finding, as before.

Grouping is deterministic, no model call. With an event log, zone
intervals from telemetry volumes (zone_enter and zone_exit) bound the
Attempts. Without a log, a sustained stretch of activity in another
Puzzle, or a gap over ATTEMPT_GAP_S, ends an Attempt.

With a log, only a volume whose puzzle line is set is a Puzzle (Sasha,
2026-10-28: "we should stop treating everything as puzzle"). A moment
in a volume with an empty puzzle line, or outside every volume, is an
Area visit: its beat has area, zone and the visit's span, and puzzle,
puzzle_number and attempt are null. Without a log nothing changes.

`python -m analyzer.beats` re-runs this step alone on a findings file.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from analyzer import findings as findings_module
from analyzer import log_candidates

# Proposal (Muse Wonder, orchestrator, 2026-10-28), not Sasha's number:
# a longer silence than this, in the same place, reads as a new visit.
ATTEMPT_GAP_S = 180.0


def _zone_at(zones, time_s):
    for zone in zones or []:
        if zone["start_s"] <= time_s and (zone["end_s"] is None or time_s <= zone["end_s"]):
            return zone
    return None


# Zone intervals from a session log's telemetry events, in video time.
def zone_intervals(events, video_flash_s):
    if not events or video_flash_s is None:
        return []
    first_flash = next((e for e in events if e.get("event") == "sync_flash"), None)
    if first_flash is None:
        return []
    offset = video_flash_s - float(first_flash["t"])
    # Keyed by name and puzzle line: two boxes with one name and
    # different puzzle lines overlap in real scenes.
    open_zones = {}
    intervals = []
    for event in events:
        video_t = round(float(event["t"]) + offset, 2)
        key = (event.get("zone", ""), event.get("puzzle", ""))
        if event.get("event") == "zone_enter":
            open_zones[key] = {
                "zone": event.get("zone", ""),
                "puzzle": event.get("puzzle", ""),
                "start_s": video_t,
                "end_s": None,
            }
        elif event.get("event") == "zone_exit":
            zone = open_zones.pop(key, None)
            if zone is not None:
                zone["end_s"] = video_t
                intervals.append(zone)
    intervals.extend(open_zones.values())
    return sorted(intervals, key=lambda zone: zone["start_s"])


_STOPWORDS = {"and", "the", "a", "an", "of", "with", "on", "in", "by", "at", "near", "over", "into", "through", "onto", "under", "between", "across", "from", "for", "to", "puzzle"}


def _tokens(label: str):
    words = re.sub(r"[^a-z0-9]+", " ", (label or "").lower()).split()
    tokens = set()
    for word in words:
        if word in _STOPWORDS or len(word) < 2:
            continue
        # One stem for plurals: hexahedrons and hexahedron are one token.
        if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
            word = word[:-1]
        tokens.add(word)
    return tokens


def _norm(label):
    return re.sub(r"[^a-z0-9]+", " ", (label or "").lower()).strip()


def _overlap(left, right):
    if not left or not right:
        return 0.0
    return len(left & right) / min(len(left), len(right))


_AREA_GENERIC = {"puzzle", "area", "zone", "room"}

_COLORS = {"yellow", "blue", "green", "red", "purple", "orange", "white", "black", "gold", "silver"}


# Colour-named areas are different areas when their colours differ.
def _area_conflict(raw_tokens, area_tokens):
    raw_colors = raw_tokens & _COLORS
    area_colors = area_tokens & _COLORS
    return bool(raw_colors and area_colors and not (raw_colors & area_colors))


# The colour boundary is one-way: a moment the checker placed in a
# colour-named area never joins an area or puzzle filed under a
# colourless name, so a generic parent ("Temple Ruins", "Puzzle
# Area") never absorbs its colour-named children ("Yellow Temple
# Ruins", "Blue Temple Ruins") and collapses them together. A
# colourless wording ("Static Pressure temple corridor") can still
# join the coloured area or puzzle it belongs to.
def _colour_unmatched(raw_tokens, other_tokens):
    return bool(raw_tokens & _COLORS) and not (other_tokens & _COLORS)


class _Areas:
    def __init__(self):
        self.areas = []

    def resolve(self, label, create=True, exact_only=False):
        key = _norm(label)
        for area in self.areas:
            if area["key"] == key:
                return area
        if exact_only:
            # A telemetry volume's name is exact: it never fuzzy-joins
            # a longer checker area ("East Lab" is not "East Lab Wing").
            if not create:
                return None
            area = {"label": label or "Unknown area", "key": key, "tokens": _tokens(label), "next_number": 1, "last_time": None}
            self.areas.append(area)
            return area
        tokens = _tokens(label)
        matches = []
        for area in self.areas:
            if _area_conflict(tokens, area["tokens"]):
                continue
            if _colour_unmatched(tokens, area["tokens"]):
                continue
            # Same area when one name is a shorter form of the other
            # ("temple ruins" inside "Egyptian temple ruins"), or when
            # two distinctive words agree. Generic words alone never
            # merge areas: Yellow Puzzle Area is not Blue Puzzle Area,
            # and neither collapses into a bare "Puzzle Area": the
            # shorter name needs at least two words of its own.
            smaller = tokens if len(tokens) <= len(area["tokens"]) else area["tokens"]
            if len(smaller) >= 2 and (tokens <= area["tokens"] or area["tokens"] <= tokens):
                matches.append(area)
                continue
            distinctive = (tokens & area["tokens"]) - _AREA_GENERIC
            if len(distinctive) >= 2 and _overlap(tokens, area["tokens"]) >= 0.5:
                matches.append(area)
        if matches:
            # Several areas can contain a colourless wording ("Temple
            # Ruins" fits the Yellow and the Blue room): the one the
            # player was most recently in is the likelier, never the
            # first one created.
            return max(
                matches,
                key=lambda a: (-1.0 if a["last_time"] is None else a["last_time"], self.areas.index(a)),
            )
        if not create:
            return None
        area = {"label": label or "Unknown area", "key": key, "tokens": tokens, "next_number": 1, "last_time": None}
        self.areas.append(area)
        return area


def _new_state(areas, area, puzzle_label):
    return {
        "area": area["label"],
        "area_ref": area,
        "label": puzzle_label,
        "key": _norm(puzzle_label),
        # The canonical label's words only, never grown by joins: a
        # joined label's new words would otherwise arm the next join
        # and chain three different puzzles into one.
        "tokens": _tokens(puzzle_label),
        # Numbered lazily, at the first kept finding: a puzzle the
        # checker only ever dropped never takes a number on the page.
        "puzzle_number": None,
        "attempt_count": 0,
        "last_time": None,
        "last_kept_time": None,
    }


# The state's puzzle number inside its area, assigned on first use.
def _number_for(state):
    if state["puzzle_number"] is None:
        area = state["area_ref"]
        state["puzzle_number"] = area["next_number"]
        area["next_number"] += 1
    return state["puzzle_number"]


_DISTINCTIVE = {"fan", "jammer", "hexahedron", "cube", "barrier", "keypad", "laser", "pressure"}


def _resolve_state(states, areas, finding, time_s, zone=None):
    if zone is not None:
        # Inside a telemetry volume, the designer's names win over
        # anything the checker called this moment.
        raw_area = zone["zone"] or finding["check"].get("area")
        raw_puzzle = zone["puzzle"] or zone["zone"] or finding["check"].get("puzzle")
    else:
        raw_area = finding["check"].get("area")
        raw_puzzle = finding["check"].get("puzzle") or finding.get("game_state") or finding["summary"]
    puzzle_key = _norm(raw_puzzle)
    tokens = _tokens(raw_puzzle)
    if zone is not None:
        # Inside a volume the designer's label is the whole truth:
        # no fuzzy join and no chaining can pull the moment into a
        # puzzle the checker happened to mention in its summary.
        area = areas.resolve(raw_area, exact_only=True)
        state = next(
            (s for s in states if s["area_ref"] is area and s["key"] == puzzle_key),
            None,
        )
        if state is not None:
            return state
        state = _new_state(areas, area, raw_puzzle)
        states.append(state)
        return state
    # An identical label is the same puzzle at any distance, in any
    # area wording that shares a real word with it: the checker names
    # areas loosely, puzzles more reliably. A label in a plainly
    # different area (Blue, not Yellow) is a different puzzle.
    raw_area_tokens = _tokens(raw_area) if raw_area else set()
    # The same label in two colour rooms joins the most recent one:
    # the first match would record a return to a room the player
    # left, with a fresh attempt number to match.
    exact_matches = [
        s
        for s in states
        if s["key"] == puzzle_key
        and not _area_conflict(raw_area_tokens, s["area_ref"]["tokens"])
        and not _colour_unmatched(raw_area_tokens, s["area_ref"]["tokens"])
        and (
            not raw_area_tokens
            or (raw_area_tokens & s["area_ref"]["tokens"]) - _AREA_GENERIC
        )
    ]
    exact = max(exact_matches, key=lambda s: s["last_time"] or -1.0, default=None)
    area = areas.resolve(raw_area or raw_puzzle, create=False)
    # Chaining: a kept moment seconds after a puzzle's last moment,
    # talking about the same distinctive object in a nearby area
    # wording, is that puzzle even when the checker named this step
    # differently. An identical label always wins over it (below):
    # chaining only rescues a step the checker named differently.
    # Dropped moments never chain: they mark departures instead.
    if finding["check"].get("verdict") == "keep":
        combined = _tokens(
            f"{raw_puzzle} {finding.get('summary') or ''} {finding.get('game_state') or ''}"
        )
        chained = None
        for candidate in states:
            # Only a puzzle with a kept moment can chain: a puzzle the
            # checker only dropped is a departure marker, not a magnet.
            if candidate["last_kept_time"] is None or time_s - candidate["last_kept_time"] > 60.0:
                continue
            if _area_conflict(raw_area_tokens, candidate["area_ref"]["tokens"]):
                continue
            if _colour_unmatched(raw_area_tokens, candidate["area_ref"]["tokens"]):
                continue
            if _area_conflict(tokens, candidate["tokens"]):
                continue
            nearby = (area is not None and candidate["area_ref"] is area) or bool(
                (raw_area_tokens & candidate["area_ref"]["tokens"]) - _AREA_GENERIC
            )
            if not nearby:
                continue
            if combined & candidate["tokens"] & _DISTINCTIVE:
                if chained is None or candidate["last_kept_time"] > chained["last_kept_time"]:
                    chained = candidate
        # An identical label always wins over chaining: chaining only
        # rescues a step the checker named differently.
        if chained is not None and (exact is None or exact is chained):
            return chained
    if exact is not None:
        return exact
    # A dropped, solved clip is a different puzzle the player finished
    # in between, unless its label matches a neighbour strongly: then
    # it is that puzzle's own finishing moment, not a departure.
    drop_solved = (
        finding["check"].get("verdict") == "drop"
        and finding["check"].get("resolved") == "solved"
    )
    best_state = None
    best_rank = None
    best_shared = 0
    best_overlap = 0.0
    for candidate in states:
        if candidate["last_time"] is None or time_s - candidate["last_time"] > 300.0:
            continue
        if _area_conflict(raw_area_tokens, candidate["area_ref"]["tokens"]):
            continue
        if _colour_unmatched(raw_area_tokens, candidate["area_ref"]["tokens"]):
            continue
        if _area_conflict(tokens, candidate["tokens"]):
            continue
        shared_tokens = tokens & candidate["tokens"]
        shared = len(shared_tokens)
        overlap = _overlap(tokens, candidate["tokens"])
        same_area = area is not None and candidate["area_ref"] is area
        # One shared word never joins two puzzles: barrier words
        # repeat. Across area wordings the bar is higher, and the
        # match must include a strong object word: blue and cube
        # alone appear in half the game.
        if shared < 2 or overlap < (0.34 if same_area else 0.5):
            continue
        if not same_area and not (shared_tokens & {"fan", "hexahedron", "jammer", "keypad"}):
            continue
        rank = (overlap, 1 if same_area else 0)
        if best_rank is None or rank > best_rank:
            best_rank = rank
            best_state = candidate
            best_shared = shared
            best_overlap = overlap
    if best_state is not None and (
        not drop_solved or (best_shared >= 3 and best_overlap >= 0.6)
    ):
        return best_state
    if area is None:
        area = areas.resolve(raw_area or raw_puzzle)
    state = _new_state(areas, area, raw_puzzle)
    states.append(state)
    return state

# Add a "beat" field to every kept finding, in place. Dropped findings
# get no beat, but their times still mark where one Attempt ended and
# another began. Returns the findings list.
#
# One pass in time order over every finding, kept and dropped. A
# telemetry zone interval bounds its Attempt exactly; outside zones,
# an Attempt ends when the player finishes another puzzle, spends a
# kept moment on another puzzle, or is gone longer than ATTEMPT_GAP_S.
def assign_beats(findings, zones=None):
    activity = sorted(findings, key=lambda f: f["time_s"])
    areas = _Areas()
    states = []
    resolved = []
    for finding in activity:
        zone = _zone_at(zones, finding["time_s"]) if zones else None
        state = _resolve_state(states, areas, finding, finding["time_s"], zone=zone)
        state["last_time"] = finding["time_s"]
        state["area_ref"]["last_time"] = finding["time_s"]
        if finding["check"]["verdict"] == "keep":
            state["last_kept_time"] = finding["time_s"]
        resolved.append((finding, state, zone))

    segments = []
    last_end_by_state = {}
    for finding, state, zone in resolved:
        time_s = finding["time_s"]
        zone_start = zone["start_s"] if zone is not None else None
        if (
            segments
            and segments[-1]["state"] is state
            and segments[-1]["zone_start"] == zone_start
            and time_s - segments[-1]["end_s"] <= ATTEMPT_GAP_S
        ):
            segments[-1]["end_s"] = time_s
            segments[-1]["findings"].append(finding)
        else:
            segments.append(
                {
                    "state": state,
                    "start_s": time_s,
                    "end_s": time_s,
                    "findings": [finding],
                    "zone_start": zone_start,
                    "zone_end": zone["end_s"] if zone is not None else None,
                    "split_by_gap": (
                        id(state) in last_end_by_state
                        and time_s - last_end_by_state[id(state)] > ATTEMPT_GAP_S
                    ),
                }
            )
        last_end_by_state[id(state)] = segments[-1]["end_s"]
    for segment in segments:
        # A finished other puzzle, or one kept moment of another
        # puzzle, is a real departure. One dropped, unsolved moment
        # is not: it may just be the checker glancing elsewhere.
        segment["substantial"] = (
            len(segment["findings"]) >= 2
            or any(f["check"]["verdict"] == "keep" for f in segment["findings"])
            or any(
                f["check"].get("verdict") == "drop"
                and f["check"].get("resolved") == "solved"
                for f in segment["findings"]
            )
        )

    current_by_state = {}
    zone_occurrences = {}
    departed = set()
    for segment in segments:
        state = segment["state"]
        state_id = id(state)
        current = current_by_state.get(state_id)
        starts_new = (
            current is None
            or segment["split_by_gap"]
            or state_id in departed
            or segment["zone_start"] != current["zone_start"]
        )
        if starts_new:
            occ_key = (state_id, segment["zone_start"])
            if segment["zone_start"] is not None and occ_key in zone_occurrences:
                current = zone_occurrences[occ_key]
            else:
                state["attempt_count"] += 1
                current = {
                    "state": state,
                    "attempt": state["attempt_count"],
                    "zone_start": segment["zone_start"],
                    "start_s": (
                        segment["zone_start"]
                        if segment["zone_start"] is not None
                        else segment["start_s"]
                    ),
                    "end_s": (
                        segment["zone_end"]
                        if segment["zone_end"] is not None
                        else segment["end_s"]
                    ),
                    "count": 0,
                }
                if segment["zone_start"] is not None:
                    zone_occurrences[occ_key] = current
            current_by_state[state_id] = current
        elif current["zone_start"] is None:
            current["end_s"] = segment["end_s"]
        elif current["end_s"] is None or segment["end_s"] > current["end_s"]:
            current["end_s"] = segment["end_s"]
        segment["occurrence"] = current
        departed.discard(state_id)
        if segment["substantial"]:
            for other_id in current_by_state:
                if other_id != state_id:
                    departed.add(other_id)

    # Attempts and puzzles are numbered as shown, in time order: a
    # visit with no kept finding takes no number. With a log, only a
    # moment inside a volume with a puzzle line is a Puzzle moment;
    # every other kept moment is an Area visit with no puzzle number
    # and no attempt, and takes no number from the puzzles.
    shown_attempts = {}
    shown_counts = {}
    for segment in segments:
        occurrence = segment["occurrence"]
        state = segment["state"]
        for finding in segment["findings"]:
            if finding["check"]["verdict"] != "keep":
                continue
            zone = _zone_at(zones, finding["time_s"]) if zones else None
            is_puzzle = not zones or (zone is not None and bool(zone["puzzle"]))
            number = attempt = puzzle = None
            if is_puzzle:
                if id(occurrence) not in shown_attempts:
                    shown_counts[id(state)] = shown_counts.get(id(state), 0) + 1
                    shown_attempts[id(occurrence)] = shown_counts[id(state)]
                puzzle = state["label"]
                number = _number_for(state)
                attempt = shown_attempts[id(occurrence)]
            occurrence["count"] += 1
            finding["beat"] = {
                "area": state["area"],
                "puzzle": puzzle,
                "zone": (zone["zone"] or None) if zone is not None else None,
                "puzzle_number": number,
                "attempt": attempt,
                "attempt_start_s": occurrence["start_s"],
                "attempt_end_s": occurrence["end_s"],
                "index": occurrence["count"],
            }
    return findings


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Re-run the beats step on a findings file, from a session log. No model call."
    )
    parser.add_argument("findings", help="findings JSON to regroup")
    parser.add_argument("--log", required=True, help="session event log (JSONL)")
    parser.add_argument(
        "--video-flash-s",
        type=float,
        required=True,
        help="video time of the first sync_flash",
    )
    parser.add_argument("-o", "--out", default=None, help="output path (required, never the input)")
    args = parser.parse_args(argv)

    if not args.out:
        print("-o is required: this tool never overwrites its input file.", file=sys.stderr)
        return 1
    out_path = Path(args.out)
    if out_path.resolve() == Path(args.findings).resolve():
        print("-o must differ from the input file: this tool never overwrites its input.", file=sys.stderr)
        return 1

    data = findings_module.load(args.findings)
    events = log_candidates.load_log(args.log)
    zones = zone_intervals(events, args.video_flash_s) if events else []
    assign_beats(data["findings"], zones=zones)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    # Prove the regrouped file is still in the one format.
    findings_module.load(out_path)
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
