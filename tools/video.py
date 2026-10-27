"""ffmpeg helpers: convert a recording, cut a clip, find the start flash."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# signalstats YAVG, on a 0 to 255 scale. A start flash is a short white pulse.
YAVG_JUMP = 100.0
FLASH_MIN_S = 0.15
FLASH_MAX_S = 0.4


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


# Find ffmpeg and run it, exiting with the stderr tail on failure.
def _run_ffmpeg(args):
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        print("ffmpeg not found. Install ffmpeg first.", file=sys.stderr)
        raise SystemExit(1)
    result = subprocess.run(
        [ffmpeg, *args], capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        print(f"ffmpeg failed: {result.stderr.strip()[-500:]}", file=sys.stderr)
        raise SystemExit(1)


# Convert any recording to a 720p-max H.264/AAC mp4 with ffmpeg.
def convert_video(recording: Path, output_path: Path, start=0.0, seconds=None) -> Path:
    command = ["-y", "-ss", str(start), "-i", str(recording)]
    if seconds is not None:
        command += ["-t", str(seconds)]
    command += [
        "-vf", "scale=-2:min(720\\,ih)",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-movflags", "+faststart",
        str(output_path),
    ]
    _run_ffmpeg(command)
    return output_path


# Extract the audio as the WAV the transcribe API takes: mono, 16-bit, 16 kHz.
def extract_audio(video, output_path, start=0.0, seconds=None) -> Path:
    command = ["-y", "-ss", str(start), "-i", str(video)]
    if seconds is not None:
        command += ["-t", str(seconds)]
    command += [
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-c:a",
        "pcm_s16le",
        str(output_path),
    ]
    _run_ffmpeg(command)
    return Path(output_path)


# Clip centered on time_s (from time_s - seconds/2), clamped to the recording.
# Returns the (start_s, end_s) actually used.
def cut_clip(recording, time_s, output_path, seconds=20.0):
    if seconds <= 0:
        raise ValueError(f"Clip length must be positive, got {seconds}.")
    duration = probe_duration(recording)
    if duration is None:
        raise ValueError(f"Cannot read the duration of {recording}.")
    start = time_s - seconds / 2.0
    end = time_s + seconds / 2.0
    if start < 0.0:
        start = 0.0
    if end > duration:
        end = duration
    if end <= start:
        raise ValueError(
            f"No clip around {time_s:g} s fits in a recording that is {duration:g} s long."
        )
    convert_video(recording, output_path, start=start, seconds=end - start)
    return (start, end)


# (pts_time, YAVG) for each frame in the first search_s seconds.
def _frame_yavgs(video, search_s):
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise ValueError("ffmpeg not found. Install ffmpeg first.")
    with tempfile.TemporaryDirectory(prefix="start-flash-") as tmp:
        stats_path = Path(tmp) / "stats.txt"
        command = [
            ffmpeg,
            "-hide_banner",
            "-nostdin",
            "-v",
            "error",
            "-i",
            str(video),
            "-t",
            str(search_s),
            "-vf",
            f"signalstats,metadata=print:key=lavfi.signalstats.YAVG:file={stats_path}",
            "-an",
            "-f",
            "null",
            "-",
        ]
        result = subprocess.run(
            command, capture_output=True, text=True, check=False, stdin=subprocess.DEVNULL
        )
        if result.returncode != 0:
            detail = result.stderr.strip()[-500:]
            raise ValueError(f"ffmpeg could not read {video}: {detail}")
        frames = []
        pts_time = None
        if stats_path.exists():
            for line in stats_path.read_text(encoding="utf-8", errors="replace").splitlines():
                time_match = re.search(r"pts_time:([0-9eE.+-]+)", line)
                if time_match:
                    pts_time = float(time_match.group(1))
                yavg_match = re.search(r"signalstats\.YAVG=([0-9eE.+-]+)", line)
                if yavg_match and pts_time is not None:
                    frames.append((pts_time, float(yavg_match.group(1))))
                    pts_time = None
        return frames


# Time of the first bright frame of a white pulse, or None.
def _first_white_pulse(frames):
    for index in range(1, len(frames)):
        start_t, start_y = frames[index]
        before = frames[index - 1][1]
        if start_y < before + YAVG_JUMP:
            continue
        floor = before + YAVG_JUMP
        drop_t = None
        held = True
        for later in range(index + 1, len(frames)):
            time_s, yavg = frames[later]
            if start_y - yavg >= YAVG_JUMP:
                drop_t = time_s
                break
            if yavg < floor:
                held = False
                break
        if not held or drop_t is None:
            continue
        duration = drop_t - start_t
        if FLASH_MIN_S <= duration <= FLASH_MAX_S:
            return start_t
    return None


# Time of the white pulse in the first search_s seconds: a jump of YAVG_JUMP,
# held for FLASH_MIN_S to FLASH_MAX_S, then a drop of YAVG_JUMP.
def find_start_flash(video, search_s=120.0):
    frames = _frame_yavgs(video, search_s)
    if not frames:
        raise ValueError(f"No frames in the first {search_s:g} seconds of {video}.")
    found = _first_white_pulse(frames)
    if found is None:
        raise ValueError(f"No white flash in the first {search_s:g} seconds of {video}.")
    return found
