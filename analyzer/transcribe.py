"""Transcribe the audio of one clip with Muse Voice Transcribe.

Run as: tools/run-analyzer.sh -m analyzer.transcribe <video> [--start S] [--seconds N]
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analyzer import client as client_module  # noqa: E402
from tools.video import extract_audio  # noqa: E402


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Transcribe the audio of one clip with Muse Voice Transcribe."
    )
    parser.add_argument("video", help="Path to the video clip (.mp4, .mov, ...)")
    parser.add_argument(
        "--start", type=float, default=0.0, help="Start S seconds into the video"
    )
    parser.add_argument(
        "--seconds",
        type=float,
        default=20,
        help="Keep only N seconds from the start of the cut (default: 20)",
    )
    args = parser.parse_args(argv)

    # Fail before any ffmpeg or network work when the key is missing.
    client_module.require_api_key()

    video = Path(args.video)
    if not video.exists():
        print(f"Video not found: {video}", file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory(prefix="transcribe-") as tmp:
        audio_path = extract_audio(
            video, Path(tmp) / "audio.wav", start=args.start, seconds=args.seconds
        )
        reply = client_module.transcribe(
            audio_path,
            purpose=f"transcribe:{video.name}",
        )

    output_dir = Path("runs/transcribe")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{video.stem}-from{args.start:g}s-{args.seconds:g}.json"
    payload = {
        **reply,
        "video": video.name,
        "start_s": args.start,
        "seconds": args.seconds,
    }
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote transcript to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
