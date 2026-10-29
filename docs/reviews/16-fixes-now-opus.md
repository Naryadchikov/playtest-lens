Reviewer: fresh reviewer, Claude Opus 5.5, Cursor, base commit 3c5c920 (uncommitted work on main, task docs/tasks/27-fixes-now.md, author Claude Sonnet 5.5).

**PASS**

## What I checked

- `.venv/bin/python -m pytest -q --deselect tests/test_transcribe.py::test_extract_audio_from_say_clip`: 184 passed, 1 deselected, exit 0.
- `rg -n "image_url|sample_frames|_frame_plan|clip_start_s|planned challenge" analyzer tools report tests README.md`: no output. The only remaining "frame" hits in `tools/video.py` are the start flash detector (`_frame_yavgs`, `_first_white_pulse`), which is not a model path.
- One open path: `_call_open_model` in `analyzer/client.py` is the only `meta-models/` request builder. It sends exactly `video_url`, `input_audio` (wav) and `text`, caches by model, prompt, video sha256, wav sha256 and max_tokens, appends one cost line per real call and one for an empty answer, and never caches an empty answer. No frame helper, no flag, no host switch is left.
- Every model call still goes through `analyzer/client.py`; `spark_test.py` and `check.py` call only `call_model` and `transcribe`.
- `verified_quote` is unchanged in the diff and still applied in `run_checks`. The check prompt now asks for quotes "heard in the audio and also in the transcript", which narrows, not weakens.
- `engine_name` reads `session_start.godot_version`; `build_prompt` defaults to "unknown"; `{engine}` is the only new placeholder and the JSON braces stay doubled. `spark_test.md` names no engine and carries both "not stuck" rules and the audio quote rule.
- `merge_same_moment` is called once in `main`, after `run_checks` and before `zone_intervals` / `assign_beats`; `spatial.enrich` builds the summary afterwards, so `kept`, `dropped` and `lost_s` see the merged list. The chain rule, quote-first keeper, untouched dropped findings and 1..n rank renumbering match the brief; the test covers all four bullets and loads through `findings.load`.
- `report/render.py` only hides the tile on a falsy `lost_s` read from the file; it computes nothing. `end_s` is still `None` from the check. "by design" carries the proposal comment.
- README commands match the real wrappers (`exec "$python" "$@"`) and the candidates file name pattern. Builder line drops only "on Muse Wonder".
- No key, token or private path in the diff. `game` untouched by this diff.

## The dropped `image_url` assertion

Enough. `assert [part["type"] for part in content] == ["video_url", "input_audio", "text"]` is an exact equality on the whole type list, so any `image_url` part (or any extra part at all) fails it. It is strictly stronger than "no part has type image_url".

## Blocking findings

None.

## Nits

1. `analyzer/client.py`, `_call_open_model`: the cache key includes the sha256 of a wav that ffmpeg writes fresh each call. ffmpeg stamps its own version into the wav header (the `Lavf` encoder tag), so an ffmpeg upgrade changes the wav bytes and turns every cached open reply into a miss, which is a paid rerun on Baseten. Adding `-bitexact` (or `-map_metadata -1 -fflags +bitexact`) to `extract_audio`, or keying on the video hash alone since the wav is derived from it, would remove that. Not blocking: same machine, same ffmpeg, same bytes.
2. `analyzer/client.py`, `_call_open_model`: the wav is extracted before the cache lookup, so a fully cached rerun still needs ffmpeg and runs it once per call. Follows from the brief's code; only matters if offline reruns without ffmpeg are expected.
3. `analyzer/check.py`, `merge_same_moment`: a merged-away finding's 20 s clip is still written under `runs/` and never referenced by `findings.json`. Harmless (git-ignored), just orphan files.
4. `tests/test_open_backend.py`: one blank line, not two, before `def test_different_wav_bytes_are_a_cache_miss`. The test could also assert the second request's `input_audio.data` decodes to `b"other-wav-bytes"`, to prove the new wav is what was sent, not only that a call happened.
5. `tests/test_open_backend.py`: the fixture comment "A fake extract_audio that writes the wav bytes held in the returned box." is fine, but nothing tests the real `extract_audio` call inside `_call_open_model` (the author says so). Sasha's paid rerun is the first real exercise of that line.
