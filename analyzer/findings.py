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


def _check_time(value, field, duration_s):
    _check_number(value, field)
    if not 0 <= value <= duration_s:
        _fail(field, f"must be within 0..{duration_s} (duration_s)")
    return value


def _check_time_or_null(value, field, duration_s):
    if value is not None:
        _check_time(value, field, duration_s)
    return value


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

        if verdict == "keep" and rank is None:
            _fail(f"{where}.rank", "kept findings must have a rank")
        if verdict == "drop" and rank is not None:
            _fail(f"{where}.rank", "dropped findings must have a null rank")

    return data
