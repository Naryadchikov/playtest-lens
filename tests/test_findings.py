import json
from pathlib import Path

import pytest

from analyzer import findings

SAMPLE = Path(__file__).parent / "fixtures" / "findings_sample.json"


def _sample_data():
    return json.loads(SAMPLE.read_text(encoding="utf-8"))


def _write(tmp_path, data):
    path = tmp_path / "findings.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_load_accepts_sample():
    data = findings.load(SAMPLE)
    assert data["format"] == 1
    assert data["session"]["id"] == "sample-01"
    assert len(data["findings"]) == 6


def test_load_rejects_missing_time_s(tmp_path):
    data = _sample_data()
    del data["findings"][0]["time_s"]
    with pytest.raises(ValueError, match=r"time_s"):
        findings.load(_write(tmp_path, data))


def test_load_rejects_bad_kind(tmp_path):
    data = _sample_data()
    data["findings"][0]["kind"] = "bored"
    with pytest.raises(ValueError, match=r"kind"):
        findings.load(_write(tmp_path, data))


def test_load_rejects_duplicate_id(tmp_path):
    data = _sample_data()
    data["findings"][1]["id"] = data["findings"][0]["id"]
    with pytest.raises(ValueError, match=r"id"):
        findings.load(_write(tmp_path, data))


def test_load_rejects_time_past_end(tmp_path):
    data = _sample_data()
    data["findings"][0]["time_s"] = data["session"]["duration_s"] + 1
    with pytest.raises(ValueError, match=r"time_s"):
        findings.load(_write(tmp_path, data))
