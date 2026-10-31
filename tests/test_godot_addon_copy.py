"""The add-on's source is godot/addons/playtest_lens; the COGITO fork in game/
carries a copy for the demo build. The two must stay byte for byte the same."""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "godot" / "addons" / "playtest_lens"
COPY = ROOT / "game" / "addons" / "playtest_lens"


def _files(folder):
    return {
        path.relative_to(folder): path.read_bytes()
        for path in folder.rglob("*")
        if path.is_file() and path.name != ".DS_Store"
    }


def test_fork_copy_of_the_addon_matches_the_source():
    if not COPY.is_dir():
        pytest.skip("game/ submodule is not checked out")
    source, copy = _files(SOURCE), _files(COPY)
    assert sorted(map(str, source)) == sorted(map(str, copy))
    changed = [str(name) for name in source if source[name] != copy[name]]
    assert changed == []
