"""Render a findings.json file as one self-contained HTML page.

The page only renders what the file holds. It computes nothing beyond
formatting seconds as m:ss, and the order of kept findings comes from
the file's rank field.
"""

import argparse
import html
from pathlib import Path

from analyzer import findings as findings_module


def _mss(seconds):
    total = int(seconds)
    return f"{total // 60}:{total % 60:02d}"


def _esc(value):
    return html.escape(str(value), quote=True)


def _render_finding(finding):
    parts = ['<article class="finding">']
    friction = finding["check"].get("friction")
    kind_label = finding["kind"] + (f" · {friction}" if friction else "")
    parts.append(
        f'<p class="meta">{_esc(_mss(finding["time_s"]))} · {_esc(kind_label)}</p>'
    )
    parts.append(f"<h3>{_esc(finding['summary'])}</h3>")
    if finding["quote"] is not None:
        parts.append(f"<blockquote>{_esc(finding['quote'])}</blockquote>")
    if finding["game_state"] is not None:
        parts.append(f'<p class="game-state">{_esc(finding["game_state"])}</p>')
    parts.append(f'<p class="check">{_esc(finding["check"]["note"])}</p>')
    if finding["clip"] is not None:
        parts.append(
            f'<video controls src="{_esc(finding["clip"]["path"])}"></video>'
        )
    parts.append("</article>")
    return "\n".join(parts)


def render_html(data):
    """Return the full HTML page for a checked findings dict."""
    session = data["session"]
    kept = sorted(
        (f for f in data["findings"] if f["check"]["verdict"] == "keep"),
        key=lambda f: f["rank"],
    )
    dropped = [f for f in data["findings"] if f["check"]["verdict"] == "drop"]

    parts = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        f"<title>Session {_esc(session['id'])}</title>",
        "<style>",
        "body { font-family: sans-serif; margin: 2em auto; max-width: 44em; padding: 0 1em; }",
        ".finding { border-top: 1px solid #ccc; padding: 1em 0; }",
        ".meta { color: #555; }",
        ".beat { background: #ececec; padding: 0.6em 0.8em; margin: 1.4em 0 0.4em; }",
        "blockquote { margin: 0.5em 0; padding-left: 1em; border-left: 3px solid #ccc; }",
        "video { max-width: 100%; }",
        "</style>",
        "</head>",
        "<body>",
        f"<h1>Session {_esc(session['id'])}</h1>",
        f'<p class="meta">{_esc(session["recording"])}</p>',
        "<h2>Findings</h2>",
    ]
    # Headers follow the file's rank order: a header opens when the
    # beat changes, and never pulls a later moment forward.
    current_key = None
    for finding in kept:
        beat = finding.get("beat")
        if beat:
            key = (
                beat.get("area"),
                beat.get("puzzle"),
                beat.get("zone"),
                beat.get("puzzle_number"),
                beat.get("attempt"),
                beat.get("attempt_start_s"),
                beat.get("attempt_end_s"),
            )
            if key != current_key:
                current_key = key
                area = beat.get("area") or beat.get("zone") or beat.get("puzzle") or "Beat"
                puzzle = beat.get("puzzle")
                start_s = beat.get("attempt_start_s")
                end_s = beat.get("attempt_end_s")
                if start_s is None:
                    start_s = finding["time_s"]
                if end_s is None:
                    end_s = finding["time_s"]
                label = _esc(area)
                if puzzle and puzzle != area:
                    if beat.get("puzzle_number"):
                        label += f" · Puzzle {_esc(beat['puzzle_number'])}: {_esc(puzzle)}"
                    else:
                        label += f" · {_esc(puzzle)}"
                elif puzzle and beat.get("puzzle_number"):
                    label += f" · Puzzle {_esc(beat['puzzle_number'])}"
                label += f" · Attempt {_esc(beat.get('attempt'))} · {_esc(_mss(start_s))}–{_esc(_mss(end_s))}"
                parts.append(f'<h2 class="beat">{label}</h2>')
        parts.append(_render_finding(finding))
    parts.append("<h2>Dropped</h2>")
    parts.extend(_render_finding(f) for f in dropped)
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
