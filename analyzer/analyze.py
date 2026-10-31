"""One command: a playtest recording and its event log in, a report page out.

Runs the one pipeline in order: find the game's start flash in the video,
the candidate pass (spark_test, 120 s windows), the check (with the log,
which also writes areas, route, floors, heat and the summary), and the
page. Every model call still goes through analyzer/client.py, so a rerun
on the same input is served from runs/cache/ and costs nothing.

Normal mode (Contributor Spark 1.2):
    tools/run-analyzer.sh analyzer/analyze.py <recording> --log <session.jsonl>
Open-weights mode (Muse Spark Open on Baseten; quotes still checked with Voice Transcribe):
    tools/run-baseten.sh analyzer/analyze.py <recording> --log <session.jsonl> --model meta-models/muse-spark-open-1026
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analyzer import check, log_candidates, spark_test  # noqa: E402
from report import render  # noqa: E402
from tools.video import find_start_flash  # noqa: E402

DEFAULT_MODEL = "muse-spark-1.2-contributor"
WINDOW_S = 120


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Analyze one playtest: recording and log in, report page out.")
    parser.add_argument("recording", help="the playtest recording (.mkv, .mp4, .mov)")
    parser.add_argument("--log", required=True, help="the game's session log (JSONL) for this recording")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"candidate and check model (default {DEFAULT_MODEL})")
    parser.add_argument("--out-dir", default="runs/check", help="where the findings and the page go (default runs/check)")
    parser.add_argument("--video-flash-s", type=float, default=None, help="video time of the start flash, if the automatic search fails")
    args = parser.parse_args(argv)

    recording = Path(args.recording)
    if not recording.exists():
        print(f"Recording not found: {recording}", file=sys.stderr)
        return 1
    if not Path(args.log).exists():
        print(f"Log not found: {args.log}", file=sys.stderr)
        return 1

    # The check maps log times to video times through the first sync_flash line;
    # without one, stop before the candidate pass spends a model call.
    if not any(event.get("event") == "sync_flash" for event in log_candidates.load_log(args.log)):
        print(f"{args.log} has no sync_flash line, so its times cannot be lined up with the video.", file=sys.stderr)
        return 1

    flash_s = args.video_flash_s
    if flash_s is None:
        try:
            flash_s = find_start_flash(recording)
        except (ValueError, RuntimeError) as exc:
            print(f"{exc} Pass --video-flash-s with the time of the game's white start flash.", file=sys.stderr)
            return 1
    print(f"Start flash at {flash_s:.2f} s")

    slug = args.model.replace("/", "-")
    out_dir = Path(args.out_dir)
    candidates = out_dir / f"{recording.stem}-{slug}-candidates.json"
    findings = out_dir / f"{recording.stem}-{slug}-findings.json"
    page = out_dir / f"{recording.stem}-{slug}-report.html"

    steps = (
        (spark_test.main, [str(recording), "--window-seconds", str(WINDOW_S), "--model", args.model, "--out", str(candidates)]),
        (check.main, [str(recording), str(candidates), "--model", args.model, "--log", args.log,
                      "--video-flash-s", repr(flash_s), "--out", str(findings)]),
        (render.main, [str(findings), "-o", str(page)]),
    )
    for step, step_args in steps:
        code = step(step_args)
        if code:
            return code
    print(f"Report: {page}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
