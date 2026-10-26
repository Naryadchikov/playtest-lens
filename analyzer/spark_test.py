"""Send one playtest recording to Muse Spark and save confused, stuck or surprised moments.

Run as: tools/run-analyzer.sh analyzer/spark_test.py <recording> [--model muse-spark-1.3] [--seconds N]
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analyzer import client as client_module  # noqa: E402

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


# Duration in seconds from ffprobe, or None if it cannot be read.
def probe_duration(path):
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return None
    result = subprocess.run(
        [ffprobe, "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    try:
        return float(json.loads(result.stdout)["format"]["duration"])
    except (ValueError, KeyError, TypeError):
        return None


# Convert any recording to a 720p-max H.264/AAC mp4 with ffmpeg.
def convert_video(recording: Path, output_path: Path, seconds=None) -> Path:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        print("ffmpeg not found. Install ffmpeg first.", file=sys.stderr)
        raise SystemExit(1)
    command = [ffmpeg, "-y", "-i", str(recording)]
    if seconds is not None:
        command += ["-t", str(seconds)]
    command += [
        "-vf", "scale=-2:min(720\\,ih)",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-movflags", "+faststart",
        str(output_path),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        print(f"ffmpeg failed: {result.stderr.strip()[-500:]}", file=sys.stderr)
        raise SystemExit(1)
    return output_path


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Send a playtest recording to Muse Spark and save moments where the player was confused, stuck or surprised."
    )
    parser.add_argument("recording", help="Path to the playtest recording (.mov, .mp4, ...)")
    parser.add_argument("--model", default="muse-spark-1.3", help="Model id (default: muse-spark-1.3)")
    parser.add_argument("--seconds", type=int, default=None, help="Keep only the first N seconds")
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
        converted = convert_video(recording, Path(tmp) / "converted.mp4", seconds=args.seconds)
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
    try:
        moments = parse_moments(raw_text)
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
