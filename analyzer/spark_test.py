"""Send one playtest recording to Muse Spark and save confused, stuck or surprised moments.

Run as: tools/run-analyzer.sh analyzer/spark_test.py <recording> [--model muse-spark-1.2-contributor] [--start S] [--seconds N]
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analyzer import client as client_module  # noqa: E402
from tools.video import convert_video, probe_duration  # noqa: E402

KINDS = ("confused", "stuck", "surprised")
PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "spark_test.md"


# Parse and validate the model's JSON reply. Raises ValueError with a clear message.
def parse_moments(text: str):
    if not text or not text.strip():
        raise ValueError("Model reply was empty: no JSON found.")
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    try:
        data = json.loads(cleaned)
    except ValueError as exc:
        raise ValueError(f"Model reply is not valid JSON: {exc}") from exc
    if isinstance(data, dict) and "moments" in data:
        data = data["moments"]
    if not isinstance(data, list):
        raise ValueError("Model reply JSON must be a list of moments.")
    for index, moment in enumerate(data):
        if not isinstance(moment, dict):
            raise ValueError(f"Moment {index} is not an object.")
        if "time_s" not in moment or moment["time_s"] is None:
            raise ValueError(f"Moment {index} has no time_s.")
        if isinstance(moment["time_s"], bool) or not isinstance(moment["time_s"], (int, float)):
            raise ValueError(f"Moment {index} has a non-numeric time_s.")
        if moment.get("kind") not in KINDS:
            raise ValueError(f"Moment {index} has an invalid kind: {moment.get('kind')!r}.")
        if not isinstance(moment.get("reason"), str) or not moment["reason"].strip():
            raise ValueError(f"Moment {index} has no reason.")
        if "quote" not in moment or not (moment["quote"] is None or isinstance(moment["quote"], str)):
            raise ValueError(f"Moment {index} has an invalid quote.")
    return data


# Shift the model's times (seconds into the cut) to seconds into the whole recording.
def to_recording_time(moments, start):
    return [{**moment, "time_s": round(moment["time_s"] + start, 2)} for moment in moments]


# Start times of the windows that cover a recording of duration_s.
def window_starts(duration_s, window_s):
    starts = []
    start = 0.0
    while start < duration_s:
        starts.append(round(start, 2))
        start += window_s
    return starts


# Merge per-window moments by recording time. A moment within 5 s of
# the last kept one is dropped only when it comes from a different
# window (the same moment seen twice at a seam), never inside a window.
def merge_window_moments(windows):
    tagged = [
        (moment["time_s"], window_index, moment)
        for window_index, window in enumerate(windows)
        for moment in window
    ]
    merged = []
    anchor = None
    for _time, window_index, moment in sorted(tagged, key=lambda item: item[0]):
        if (
            anchor is not None
            and window_index != anchor[1]
            and moment["time_s"] - anchor[0] <= 5.0
        ):
            # A seam repeat: drop it, but it becomes the anchor, so the
            # next moment from its own window is judged on its own.
            anchor = (moment["time_s"], window_index)
            continue
        merged.append((moment["time_s"], window_index, moment))
        anchor = (moment["time_s"], window_index)
    return [moment for _time, _window, moment in merged]


# One cut through the model: convert, call, parse, shift to recording time.
# Returns (moments, usage) or raises ValueError on a bad reply.
def _moments_for_cut(recording, prompt, model, start, seconds, tmp_dir, stem):
    converted = convert_video(
        recording, Path(tmp_dir) / f"converted-{start:g}.mp4", start=start, seconds=seconds
    )
    try:
        reply = client_module.call_model(
            model=model,
            prompt=prompt,
            video_path=converted,
            purpose=f"spark_test:{recording.name}",
        )
    except SystemExit:
        raise
    except Exception as exc:
        raise ValueError(f"Model call failed: {exc}") from exc
    raw_text = client_module.extract_text(reply)
    try:
        moments = to_recording_time(parse_moments(raw_text), start)
    except ValueError as exc:
        output_dir = Path("runs/spark_test")
        output_dir.mkdir(parents=True, exist_ok=True)
        raw_path = output_dir / f"{stem}-{model.replace('/', '-')}.raw.txt"
        raw_path.write_text(raw_text, encoding="utf-8")
        raise ValueError(f"Invalid model reply: {exc} Raw reply saved to {raw_path}") from exc
    input_tokens, output_tokens, cost = client_module.usage_and_cost(model, reply)
    usage = {"input_tokens": input_tokens, "output_tokens": output_tokens, "cost_usd": cost}
    return moments, usage, client_module.file_content_hash(converted), probe_duration(converted)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Send a playtest recording to Muse Spark and save moments where the player was confused, stuck or surprised."
    )
    parser.add_argument("recording", help="Path to the playtest recording (.mov, .mp4, ...)")
    parser.add_argument("--model", default="muse-spark-1.2-contributor", help="Model id (default: muse-spark-1.2-contributor)")
    parser.add_argument("--start", type=float, default=0.0, help="Start the cut S seconds into the recording")
    parser.add_argument("--seconds", type=int, default=None, help="Keep only N seconds from the start of the cut")
    parser.add_argument("--window-seconds", type=float, default=None, help="Split the recording into windows of N seconds, one call each, and merge (the candidate pass; ignores --start/--seconds)")
    args = parser.parse_args(argv)

    # Fail before any conversion or upload when the key is missing.
    client_module.require_api_key()

    recording = Path(args.recording)
    if not recording.exists():
        print(f"Recording not found: {recording}", file=sys.stderr)
        return 1

    prompt = PROMPT_PATH.read_text(encoding="utf-8")
    input_hash = client_module.file_content_hash(recording)
    output_dir = Path("runs/spark_test")
    stem = recording.stem

    if args.window_seconds is not None:
        if args.window_seconds <= 0:
            print("Window length must be positive.", file=sys.stderr)
            return 1
        duration = probe_duration(recording)
        if duration is None:
            print(f"Cannot read the duration of {recording}.", file=sys.stderr)
            return 1
        stem += f"-window{args.window_seconds:g}s"
        windows = []
        total = {"input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0}
        # No single converted file in window mode: video_hash stays null.
        converted_hash = None
        with tempfile.TemporaryDirectory(prefix="spark-test-") as tmp:
            for start in window_starts(duration, args.window_seconds):
                try:
                    moments, usage, _hash, _dur = _moments_for_cut(
                        recording, prompt, args.model, start, args.window_seconds, tmp, stem
                    )
                except ValueError as exc:
                    print(str(exc), file=sys.stderr)
                    return 1
                windows.append(moments)
                total["input_tokens"] += usage["input_tokens"]
                total["output_tokens"] += usage["output_tokens"]
                if usage["cost_usd"] is None:
                    total["cost_usd"] = None
                elif total["cost_usd"] is not None:
                    total["cost_usd"] += usage["cost_usd"]
        moments = merge_window_moments(windows)
        usage = total
    else:
        if args.start or args.seconds:
            stem += f"-from{args.start:g}s-{args.seconds or 'end'}"
        with tempfile.TemporaryDirectory(prefix="spark-test-") as tmp:
            try:
                moments, usage, converted_hash, duration = _moments_for_cut(
                    recording, prompt, args.model, args.start, args.seconds, tmp, stem
                )
            except ValueError as exc:
                print(str(exc), file=sys.stderr)
                return 1

    output_dir.mkdir(parents=True, exist_ok=True)
    # Model ids can contain a slash (meta-models/muse-spark-open-1026). A slash
    # in the file name makes the write look for a folder that is not there.
    output_path = output_dir / f"{stem}-{args.model.replace('/', '-')}.json"
    output_path.write_text(
        json.dumps(
            {
                "recording": recording.name,
                "start_s": args.start,
                "model": args.model,
                "input_hash": input_hash,
                "video_hash": converted_hash,
                "duration_s": duration,
                "window_s": args.window_seconds,
                "usage": usage,
                "moments": moments,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Wrote {len(moments)} moments to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
