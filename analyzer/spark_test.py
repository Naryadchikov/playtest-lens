"""Send one playtest recording to Muse Spark and save confused, stuck or surprised moments.

Run as: tools/run-analyzer.sh analyzer/spark_test.py <recording> [--model muse-spark-1.3] [--start S] [--seconds N]
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


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Send a playtest recording to Muse Spark and save moments where the player was confused, stuck or surprised."
    )
    parser.add_argument("recording", help="Path to the playtest recording (.mov, .mp4, ...)")
    parser.add_argument("--model", default="muse-spark-1.3", help="Model id (default: muse-spark-1.3)")
    parser.add_argument("--start", type=float, default=0.0, help="Start the cut S seconds into the recording")
    parser.add_argument("--seconds", type=int, default=None, help="Keep only N seconds from the start of the cut")
    args = parser.parse_args(argv)

    # Fail before any conversion or upload when the key is missing.
    client_module.require_api_key()

    recording = Path(args.recording)
    if not recording.exists():
        print(f"Recording not found: {recording}", file=sys.stderr)
        return 1

    prompt = PROMPT_PATH.read_text(encoding="utf-8")
    input_hash = client_module.file_content_hash(recording)

    with tempfile.TemporaryDirectory(prefix="spark-test-") as tmp:
        converted = convert_video(
            recording, Path(tmp) / "converted.mp4", start=args.start, seconds=args.seconds
        )
        duration = probe_duration(converted)
        converted_hash = client_module.file_content_hash(converted)
        try:
            reply = client_module.call_model(
                model=args.model,
                prompt=prompt,
                video_path=converted,
                purpose=f"spark_test:{recording.name}",
            )
        except SystemExit:
            raise
        except Exception as exc:
            print(f"Model call failed: {exc}", file=sys.stderr)
            return 1

    raw_text = client_module.extract_text(reply)
    output_dir = Path("runs/spark_test")
    stem = recording.stem
    if args.start or args.seconds:
        stem += f"-from{args.start:g}s-{args.seconds or 'end'}"
    try:
        moments = to_recording_time(parse_moments(raw_text), args.start)
    except ValueError as exc:
        output_dir.mkdir(parents=True, exist_ok=True)
        raw_path = output_dir / f"{stem}-{args.model}.raw.txt"
        raw_path.write_text(raw_text, encoding="utf-8")
        print(f"Invalid model reply: {exc} Raw reply saved to {raw_path}", file=sys.stderr)
        return 1

    input_tokens, output_tokens, cost = client_module.usage_and_cost(args.model, reply)
    usage = {"input_tokens": input_tokens, "output_tokens": output_tokens, "cost_usd": cost}

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{stem}-{args.model}.json"
    output_path.write_text(
        json.dumps(
            {
                "recording": recording.name,
                "start_s": args.start,
                "model": args.model,
                "input_hash": input_hash,
                "video_hash": converted_hash,
                "duration_s": duration,
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
