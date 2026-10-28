"""ffmpeg helpers: convert a recording, cut a clip, find the start flash."""

from __future__ import annotations

import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# Open-weights requests send frames instead of video. A check clip gets one
# frame per 2 s, a long window from the candidate pass one per 4 s. Baseten
# rejects a request with more than 8 images, so when a clip would need more
# the spacing widens until the frames cover the whole clip.
CHECK_FRAME_INTERVAL_S = 2.0
WINDOW_FRAME_INTERVAL_S = 4.0
LONG_CLIP_S = 60.0
FRAME_MAX_SIDE = 768
MAX_FRAMES_PER_REQUEST = 8

# signalstats YAVG, on a 0 to 255 scale. A start flash is a short white pulse.
YAVG_JUMP = 100.0
# The pulse must actually be white, not just brighter than before:
# a dark grey pulse (10 to 120) jumps by more than YAVG_JUMP but is no flash.
YAVG_WHITE_MIN = 200.0
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


# (width, height) of the first video stream, or (None, None) if unreadable.
def _probe_size(path):
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return None, None
    result = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height",
            "-of",
            "json",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None, None
    try:
        stream = json.loads(result.stdout)["streams"][0]
        return int(stream["width"]), int(stream["height"])
    except (ValueError, KeyError, IndexError, TypeError):
        return None, None


# Frame spacing and cap for a clip of duration_s. Widening the spacing
# on a long clip keeps the frames spread over it, not bunched at the start.
def _frame_plan(duration_s):
    base = WINDOW_FRAME_INTERVAL_S if duration_s > LONG_CLIP_S else CHECK_FRAME_INTERVAL_S
    return max(base, duration_s / MAX_FRAMES_PER_REQUEST), MAX_FRAMES_PER_REQUEST


# Sample evenly spaced JPEG frames from a clip, long side at most
# FRAME_MAX_SIDE. Returns the frame paths in time order.
def sample_frames(video, output_dir, *, interval_s=None, max_frames=None):
    duration = probe_duration(video)
    if duration is None:
        raise ValueError(f"Cannot read the duration of {video}.")
    plan_interval, plan_max = _frame_plan(duration)
    interval_s = plan_interval if interval_s is None else interval_s
    max_frames = plan_max if max_frames is None else max_frames
    if interval_s <= 0 or max_frames <= 0:
        raise ValueError("Frame interval and count must be positive.")
    count = min(max_frames, max(1, math.ceil(duration / interval_s)))
    width, height = _probe_size(video)
    if not width or not height:
        raise ValueError(f"Cannot read the size of {video}.")
    if width >= height:
        scale = f"{min(FRAME_MAX_SIDE, width)}:-2"
    else:
        scale = f"-2:{min(FRAME_MAX_SIDE, height)}"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    _run_ffmpeg(
        [
            "-y",
            "-hide_banner",
            "-nostdin",
            "-loglevel",
            "error",
            "-i",
            str(video),
            "-vf",
            f"fps=1/{interval_s:g},scale={scale}",
            "-frames:v",
            str(count),
            "-q:v",
            "3",
            str(output_dir / "frame-%03d.jpg"),
        ]
    )
    frames = sorted(output_dir.glob("frame-*.jpg"))
    if not frames:
        raise ValueError(f"ffmpeg wrote no frames from {video}.")
    return frames


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
        if start_y < before + YAVG_JUMP or start_y < YAVG_WHITE_MIN:
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
