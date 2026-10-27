import pytest

from analyzer.spark_test import merge_window_moments, parse_moments, to_recording_time, window_starts


def test_parser_accepts_good_reply():
    text = '[{"time_s": 12.5, "kind": "stuck", "reason": "Player retries the door.", "quote": "it wont open"}, {"time_s": 30, "kind": "surprised", "reason": "Enemy appears.", "quote": null}]'
    moments = parse_moments(text)
    assert len(moments) == 2
    assert moments[0]["time_s"] == 12.5
    assert moments[1]["quote"] is None


def test_parser_rejects_no_json():
    with pytest.raises(ValueError, match="not valid JSON"):
        parse_moments("I found no moments, sorry.")


def test_parser_rejects_moment_without_time():
    with pytest.raises(ValueError, match="no time_s"):
        parse_moments('[{"kind": "confused", "reason": "Lost.", "quote": null}]')


def test_parser_rejects_bad_kind():
    with pytest.raises(ValueError, match="invalid kind"):
        parse_moments('[{"time_s": 1, "kind": "bored", "reason": "x", "quote": null}]')


def test_window_starts_cover_the_recording():
    assert window_starts(930.0, 120.0) == [0.0, 120.0, 240.0, 360.0, 480.0, 600.0, 720.0, 840.0]
    assert window_starts(100.0, 120.0) == [0.0]


def test_merge_window_moments_sorts_and_dedupes_near_repeats():
    early = [{"time_s": 119.0, "kind": "stuck", "reason": "Edge.", "quote": None}]
    late = [
        {"time_s": 122.0, "kind": "stuck", "reason": "Same moment again.", "quote": None},
        {"time_s": 200.0, "kind": "confused", "reason": "Later.", "quote": None},
    ]
    merged = merge_window_moments([late, early])
    assert [m["time_s"] for m in merged] == [119.0, 200.0]


def test_merge_window_moments_seam_drop_keeps_next_in_new_window():
    first = [{"time_s": 839.0, "kind": "stuck", "reason": "Edge.", "quote": None}]
    second = [
        {"time_s": 841.0, "kind": "stuck", "reason": "Same moment again.", "quote": None},
        {"time_s": 843.0, "kind": "surprised", "reason": "New moment.", "quote": None},
    ]
    merged = merge_window_moments([first, second])
    assert [m["time_s"] for m in merged] == [839.0, 843.0]


def test_merge_window_moments_keeps_close_moments_inside_one_window():
    window = [
        {"time_s": 10.0, "kind": "stuck", "reason": "One.", "quote": None},
        {"time_s": 14.0, "kind": "surprised", "reason": "Two.", "quote": None},
    ]
    merged = merge_window_moments([window])
    assert [m["time_s"] for m in merged] == [10.0, 14.0]


def test_times_shifted_to_the_whole_recording():
    moments = parse_moments('[{"time_s": 12.5, "kind": "stuck", "reason": "Door.", "quote": null}]')
    assert to_recording_time(moments, 300)[0]["time_s"] == 312.5
