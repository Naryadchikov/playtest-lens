import json
import math
import re
import subprocess
from pathlib import Path

import pytest

from tools.video import cut_clip, find_start_flash, probe_duration


def _run(command):
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        tail = result.stderr.strip()[-800:]
        raise RuntimeError(f"{command[0]} failed: {tail}")
    return result


def _stream(path):
    result = _run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-count_frames",
            "-show_entries",
            "stream=width,height,nb_read_frames",
            "-of",
            "json",
            str(path),
        ]
    )
    stream = json.loads(result.stdout)["streams"][0]
    stream["nb_frames"] = stream["nb_read_frames"]
    return stream


def _frame_at(video, time_s, dest):
    _run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-nostdin",
            "-i",
            str(video),
            "-ss",
            f"{time_s:.3f}",
            "-frames:v",
            "1",
            str(dest),
        ]
    )


def _psnr(left, right):
    result = _run(
        [
            "ffmpeg",
            "-hide_banner",
            "-nostdin",
            "-i",
            str(left),
            "-i",
            str(right),
            "-lavfi",
            "psnr",
            "-f",
            "null",
            "-",
        ]
    )
    match = re.search(r"average:(inf|[0-9.]+)", result.stderr)
    if not match:
        raise RuntimeError(result.stderr.strip()[-800:])
    if match.group(1) == "inf":
        return float("inf")
    return float(match.group(1))


@pytest.fixture(scope="module")
def testsrc_60s(tmp_path_factory):
    path = tmp_path_factory.mktemp("testsrc") / "source.mp4"
    # One keyframe at the start, so a cut has to land on the right frame.
    _run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-nostdin",
            "-f",
            "lavfi",
            "-i",
            "testsrc=size=1280x720:rate=10:duration=60",
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-pix_fmt",
            "yuv420p",
            "-g",
            "9999",
            "-keyint_min",
            "9999",
            "-x264-params",
            "scenecut=0",
            str(path),
        ]
    )
    return path


def test_cut_clip_at_30s_runs_from_20_to_40_and_matches_that_frame(testsrc_60s, tmp_path):
    out = tmp_path / "clip.mp4"
    start, end = cut_clip(testsrc_60s, 30, out)
    assert start == pytest.approx(20.0, abs=1e-6)
    assert end == pytest.approx(40.0, abs=1e-6)
    assert probe_duration(out) == pytest.approx(20.0, abs=0.05)

    clip_frame = tmp_path / "clip.png"
    at_20 = tmp_path / "at20.png"
    at_19_9 = tmp_path / "at199.png"
    at_20_1 = tmp_path / "at201.png"
    _frame_at(out, 0, clip_frame)
    _frame_at(testsrc_60s, 20.0, at_20)
    _frame_at(testsrc_60s, 19.9, at_19_9)
    _frame_at(testsrc_60s, 20.1, at_20_1)
    match = _psnr(clip_frame, at_20)
    earlier = _psnr(clip_frame, at_19_9)
    later = _psnr(clip_frame, at_20_1)
    assert match > earlier, f"PSNR at 20.0 s was {match}, at 19.9 s was {earlier}"
    assert match > later, f"PSNR at 20.0 s was {match}, at 20.1 s was {later}"
    assert match >= 40, f"PSNR against the 20.0 s frame was {match}"


def test_cut_clip_at_5s_is_clamped_to_the_start(testsrc_60s, tmp_path):
    out = tmp_path / "clip.mp4"
    start, end = cut_clip(testsrc_60s, 5, out)
    assert start == pytest.approx(0.0, abs=1e-6)
    assert end == pytest.approx(15.0, abs=1e-6)
    assert probe_duration(out) == pytest.approx(15.0, abs=0.05)


def test_cut_clip_at_58s_is_clamped_to_the_end(testsrc_60s, tmp_path):
    duration = probe_duration(testsrc_60s)
    assert duration == pytest.approx(60.0, abs=0.1)
    out = tmp_path / "clip.mp4"
    start, end = cut_clip(testsrc_60s, 58, out)
    assert start == pytest.approx(48.0, abs=1e-6)
    assert end == pytest.approx(duration, abs=1e-6)
    assert probe_duration(out) == pytest.approx(end - start, abs=0.05)


# 60 fps, then drop every frame whose index mod 11 is 3.
# Frame 420 is t=7.0 and 420 % 11 == 2, so the flash frame stays.
_VFR = "select='not(eq(mod(n,11),3))',setpts=PTS"


def _vfr_h264(path: Path, size: str, video_filter: str):
    _run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-nostdin",
            "-f",
            "lavfi",
            "-i",
            f"color=c=black:s={size}:r=60:d=8",
            "-f",
            "lavfi",
            "-i",
            f"color=c=white:s={size}:r=60:d=8",
            "-filter_complex",
            video_filter,
            "-fps_mode",
            "vfr",
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-pix_fmt",
            "yuv420p",
            str(path),
        ]
    )


def _full_flash(path: Path, size: str):
    _vfr_h264(
        path,
        size,
        f"[0:v][1:v]overlay=enable='between(t,7,7.25)',{_VFR}",
    )


def _pointer_flash(path: Path, size: str):
    # Small black square on the white block, standing in for the mouse pointer.
    _vfr_h264(
        path,
        size,
        "[0:v][1:v]overlay=enable='between(t,7,7.25)',"
        "drawbox=x=120:y=90:w=16:h=22:color=black:t=fill:enable='between(t,7,7.25)',"
        f"{_VFR}",
    )


def _window_flash(path: Path, size: str):
    # Central block with 80% of the pixels, mid-grey (luma 128) around it,
    # white (luma 255) from 7.000 s to 7.250 s. ffv1 keeps those samples.
    width, height = (int(part) for part in size.split("x"))
    side_w = round(width * math.sqrt(0.8))
    side_h = round(height * math.sqrt(0.8))
    while side_w * side_h < 0.8 * width * height:
        side_w += 1
    x0 = (width - side_w) // 2
    y0 = (height - side_h) // 2
    x1 = x0 + side_w - 1
    y1 = y0 + side_h - 1
    expr = f"if(between(T,7,7.25)*between(X,{x0},{x1})*between(Y,{y0},{y1}),255,128)"
    _run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-nostdin",
            "-f",
            "lavfi",
            "-i",
            f"color=c=gray:s={size}:r=60:d=8,format=yuvj444p,"
            f"geq=lum='{expr}':cb=128:cr=128,{_VFR}",
            "-fps_mode",
            "vfr",
            "-c:v",
            "ffv1",
            "-pix_fmt",
            "yuvj444p",
            str(path),
        ]
    )


def _assert_flash_at_7s(path: Path, size: str):
    width, height = size.split("x")
    stream = _stream(path)
    assert stream["width"] == int(width)
    assert stream["height"] == int(height)
    # 8 s at 60 fps would be 480 frames. Fewer means frames were dropped.
    assert int(stream["nb_frames"]) < 8 * 60
    found = find_start_flash(path)
    assert found == pytest.approx(7.0, abs=1 / 60)


@pytest.mark.parametrize("size", ["1280x720", "1920x1080"])
def test_find_start_flash_on_full_white_pulse(tmp_path, size):
    path = tmp_path / "flash.mov"
    _full_flash(path, size)
    _assert_flash_at_7s(path, size)


@pytest.mark.parametrize("size", ["1280x720", "1920x1080"])
def test_find_start_flash_with_a_pointer_in_the_white(tmp_path, size):
    path = tmp_path / "flash.mov"
    _pointer_flash(path, size)
    _assert_flash_at_7s(path, size)


@pytest.mark.parametrize("size", ["1280x720", "1920x1080"])
def test_find_start_flash_on_a_window_over_grey(tmp_path, size):
    path = tmp_path / "flash.mkv"
    _window_flash(path, size)
    _assert_flash_at_7s(path, size)


@pytest.mark.parametrize("size", ["1280x720", "1920x1080"])
def test_find_start_flash_rejects_a_white_screen_held_for_3s(tmp_path, size):
    path = tmp_path / "held.mp4"
    _run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-nostdin",
            "-f",
            "lavfi",
            "-i",
            f"color=c=black:s={size}:r=30:d=4.5",
            "-f",
            "lavfi",
            "-i",
            f"color=c=white:s={size}:r=30:d=4.5",
            "-filter_complex",
            "[0:v][1:v]overlay=enable='between(t,0.5,3.5)'",
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-pix_fmt",
            "yuv420p",
            str(path),
        ]
    )
    with pytest.raises(ValueError, match="white flash"):
        find_start_flash(path)


def test_find_start_flash_rejects_white_menu_with_dark_text(tmp_path):
    path = tmp_path / "menu.mp4"
    # Block letters, held for several seconds. This ffmpeg build has no drawtext filter.
    letters = ",".join(
        [
            "drawbox=x=60:y=80:w=18:h=120:color=black:t=fill",
            "drawbox=x=60:y=80:w=90:h=18:color=black:t=fill",
            "drawbox=x=132:y=80:w=18:h=120:color=black:t=fill",
            "drawbox=x=96:y=80:w=18:h=70:color=black:t=fill",
            "drawbox=x=180:y=80:w=18:h=120:color=black:t=fill",
            "drawbox=x=180:y=80:w=80:h=18:color=black:t=fill",
            "drawbox=x=180:y=131:w=64:h=18:color=black:t=fill",
            "drawbox=x=180:y=182:w=80:h=18:color=black:t=fill",
            "drawbox=x=290:y=80:w=18:h=120:color=black:t=fill",
            "drawbox=x=372:y=80:w=18:h=120:color=black:t=fill",
            "drawbox=x=308:y=80:w=18:h=50:color=black:t=fill",
            "drawbox=x=326:y=112:w=18:h=50:color=black:t=fill",
            "drawbox=x=344:y=144:w=28:h=56:color=black:t=fill",
            "drawbox=x=420:y=80:w=18:h=110:color=black:t=fill",
            "drawbox=x=502:y=80:w=18:h=110:color=black:t=fill",
            "drawbox=x=420:y=182:w=100:h=18:color=black:t=fill",
        ]
    )
    _run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-nostdin",
            "-f",
            "lavfi",
            "-i",
            f"color=c=white:s=1280x720:r=30:d=4,{letters}",
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-pix_fmt",
            "yuv420p",
            str(path),
        ]
    )
    with pytest.raises(ValueError, match="white flash"):
        find_start_flash(path)
