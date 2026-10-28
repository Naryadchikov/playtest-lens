"""Define and check the findings.json format.

One function, load(path), is the single place that reads a findings
file. The pipeline writes it and the report page reads it through here,
so the two never disagree on the format.
"""

import json
from pathlib import Path

FORMAT_VERSION = 1
KINDS = ("confused", "stuck", "surprised", "suspected_bug")
VERDICTS = ("keep", "drop")


def _fail(field, problem):
    raise ValueError(f"{field}: {problem}")


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _require(obj, field, where):
    if not isinstance(obj, dict):
        _fail(where, "must be an object")
    if field not in obj:
        _fail(f"{where}.{field}" if where else field, "missing required field")
    return obj[field]


def _check_number(value, field):
    if not _is_number(value):
        _fail(field, "must be a number")
    return value


def _check_string(value, field):
    if not isinstance(value, str):
        _fail(field, "must be a string")
    return value


def _check_string_or_null(value, field):
    if value is not None and not isinstance(value, str):
        _fail(field, "must be a string or null")
    return value


def _check_int(value, field):
    if isinstance(value, bool) or not isinstance(value, int):
        _fail(field, "must be an integer")
    return value


def _check_bool(value, field):
    if not isinstance(value, bool):
        _fail(field, "must be true or false")
    return value


def _check_time(value, field, duration_s):
    _check_number(value, field)
    if not 0 <= value <= duration_s:
        _fail(field, f"must be within 0..{duration_s} (duration_s)")
    return value


def _check_time_or_null(value, field, duration_s):
    if value is not None:
        _check_time(value, field, duration_s)
    return value


# The optional blocks the report page draws: summary, route, markers and
# cross_player. A file without them is still valid.
def _check_optional_blocks(data):
    summary = data.get("summary")
    if summary is not None:
        if not isinstance(summary, dict):
            _fail("summary", "must be an object")
        _check_string(_require(summary, "verdict", "summary"), "summary.verdict")
        _check_number(_require(summary, "lost_s", "summary"), "summary.lost_s")
        counts = _require(summary, "counts", "summary")
        if not isinstance(counts, dict):
            _fail("summary.counts", "must be an object")
        for name in ("stuck", "confused", "surprised", "suspected_bug"):
            _check_int(
                _require(counts, name, "summary.counts"),
                f"summary.counts.{name}",
            )
        _check_int(_require(summary, "kept", "summary"), "summary.kept")
        _check_int(_require(summary, "dropped", "summary"), "summary.dropped")

    route = data.get("route")
    if route is not None:
        if not isinstance(route, dict):
            _fail("route", "must be an object")
        _check_string(_require(route, "scene", "route"), "route.scene")
        _check_string(_require(route, "map", "route"), "route.map")
        points = _require(route, "points", "route")
        if not isinstance(points, list):
            _fail("route.points", "must be a list")
        for index, point in enumerate(points):
            where = f"route.points[{index}]"
            if not isinstance(point, list) or len(point) != 3:
                _fail(where, "must be [t, x, z]")
            for axis, value in zip(("t", "x", "z"), point):
                _check_number(value, f"{where}.{axis}")
        heat = _require(route, "heat", "route")
        if not isinstance(heat, list):
            _fail("route.heat", "must be a list")
        for index, spot in enumerate(heat):
            where = f"route.heat[{index}]"
            if not isinstance(spot, dict):
                _fail(where, "must be an object")
            for name in ("x", "z", "r_m", "seconds"):
                _check_number(
                    _require(spot, name, where), f"{where}.{name}"
                )

    markers = data.get("markers")
    if markers is not None:
        if not isinstance(markers, list):
            _fail("markers", "must be a list")
        for index, marker in enumerate(markers):
            where = f"markers[{index}]"
            if not isinstance(marker, dict):
                _fail(where, "must be an object")
            for name in ("t", "x", "z"):
                _check_number(_require(marker, name, where), f"{where}.{name}")
            _check_string_or_null(
                _require(marker, "moment", where), f"{where}.moment"
            )

    cross_player = data.get("cross_player")
    if cross_player is not None:
        if not isinstance(cross_player, list):
            _fail("cross_player", "must be a list")
        for index, group in enumerate(cross_player):
            where = f"cross_player[{index}]"
            if not isinstance(group, dict):
                _fail(where, "must be an object")
            _check_string(_require(group, "place", where), f"{where}.place")
            _check_string(_require(group, "kind", where), f"{where}.kind")
            _check_int(_require(group, "of", where), f"{where}.of")
            players = _require(group, "players", where)
            if not isinstance(players, list):
                _fail(f"{where}.players", "must be a list")
            for player_index, player in enumerate(players):
                player_where = f"{where}.players[{player_index}]"
                if not isinstance(player, dict):
                    _fail(player_where, "must be an object")
                _check_string(
                    _require(player, "label", player_where),
                    f"{player_where}.label",
                )
                moments = _require(player, "moments", player_where)
                if not isinstance(moments, list):
                    _fail(f"{player_where}.moments", "must be a list")
                for moment in moments:
                    _check_string(moment, f"{player_where}.moments")
                _check_number(
                    _require(player, "worst_t", player_where),
                    f"{player_where}.worst_t",
                )
                _check_bool(
                    _require(player, "here", player_where),
                    f"{player_where}.here",
                )


def load(path):
    """Read and check a findings file, returning the parsed dict.

    Raises ValueError naming the bad field on the first problem found.
    """
    text = Path(path).read_text(encoding="utf-8")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"findings file: invalid JSON ({exc})") from exc

    if not isinstance(data, dict):
        _fail("findings file", "must be a JSON object")

    fmt = _require(data, "format", "")
    if isinstance(fmt, bool) or not isinstance(fmt, int) or fmt != FORMAT_VERSION:
        _fail("format", f"must be {FORMAT_VERSION}")

    session = _require(data, "session", "")
    if not isinstance(session, dict):
        _fail("session", "must be an object")
    _check_string(_require(session, "id", "session"), "session.id")
    _check_string(_require(session, "recording", "session"), "session.recording")
    duration_s = _check_number(
        _require(session, "duration_s", "session"), "session.duration_s"
    )
    if duration_s < 0:
        _fail("session.duration_s", "must be 0 or more")
    _check_time_or_null(
        _require(session, "start_flash_s", "session"),
        "session.start_flash_s",
        duration_s,
    )
    for name in ("player", "level", "recorded"):
        if name in session:
            _check_string(session[name], f"session.{name}")

    _check_optional_blocks(data)

    findings = _require(data, "findings", "")
    if not isinstance(findings, list):
        _fail("findings", "must be a list")

    seen_ids = set()
    for index, finding in enumerate(findings):
        where = f"findings[{index}]"
        if not isinstance(finding, dict):
            _fail(where, "must be an object")

        finding_id = _check_string(_require(finding, "id", where), f"{where}.id")
        if finding_id in seen_ids:
            _fail(f"{where}.id", f"duplicate id {finding_id!r}")
        seen_ids.add(finding_id)

        rank = _require(finding, "rank", where)
        if rank is not None and (
            isinstance(rank, bool) or not isinstance(rank, int)
        ):
            _fail(f"{where}.rank", "must be an integer or null")

        _check_time(_require(finding, "time_s", where), f"{where}.time_s", duration_s)
        _check_time_or_null(
            _require(finding, "end_s", where), f"{where}.end_s", duration_s
        )

        kind = _require(finding, "kind", where)
        if kind not in KINDS:
            _fail(f"{where}.kind", f"must be one of {', '.join(KINDS)}")

        _check_string(_require(finding, "summary", where), f"{where}.summary")
        _check_string_or_null(_require(finding, "quote", where), f"{where}.quote")
        _check_string_or_null(
            _require(finding, "game_state", where), f"{where}.game_state"
        )

        clip = _require(finding, "clip", where)
        if clip is not None:
            if not isinstance(clip, dict):
                _fail(f"{where}.clip", "must be an object or null")
            _check_string(
                _require(clip, "path", f"{where}.clip"), f"{where}.clip.path"
            )
            _check_time(
                _require(clip, "start_s", f"{where}.clip"),
                f"{where}.clip.start_s",
                duration_s,
            )
            _check_time(
                _require(clip, "end_s", f"{where}.clip"),
                f"{where}.clip.end_s",
                duration_s,
            )

        sources = _require(finding, "sources", where)
        if not isinstance(sources, list) or not sources:
            _fail(f"{where}.sources", "must be a list with at least one entry")
        for source in sources:
            if not isinstance(source, str):
                _fail(f"{where}.sources", "must contain only strings")

        check = _require(finding, "check", where)
        if not isinstance(check, dict):
            _fail(f"{where}.check", "must be an object")
        verdict = _require(check, "verdict", f"{where}.check")
        if verdict not in VERDICTS:
            _fail(
                f"{where}.check.verdict",
                f"must be one of {', '.join(VERDICTS)}",
            )
        _check_string(_require(check, "note", f"{where}.check"), f"{where}.check.note")
        _check_string(
            _require(check, "model", f"{where}.check"), f"{where}.check.model"
        )

        if "resolved_after_s" in check and check["resolved_after_s"] is not None:
            _check_number(
                check["resolved_after_s"], f"{where}.check.resolved_after_s"
            )

        at = finding.get("at")
        if at is not None:
            if not isinstance(at, dict):
                _fail(f"{where}.at", "must be an object")
            _check_number(_require(at, "x", f"{where}.at"), f"{where}.at.x")
            _check_number(_require(at, "z", f"{where}.at"), f"{where}.at.z")

        if verdict == "keep" and rank is None:
            _fail(f"{where}.rank", "kept findings must have a rank")
        if verdict == "drop" and rank is not None:
            _fail(f"{where}.rank", "dropped findings must have a null rank")

    return data
