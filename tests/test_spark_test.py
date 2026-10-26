import pytest

from analyzer.spark_test import parse_moments


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
