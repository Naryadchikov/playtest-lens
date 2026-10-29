# 27: Lock the open path, and four fixes before Sasha's rerun

Author of this brief: Claude Opus 5.5, Cursor, 2026-10-29. Implementer: Claude Sonnet 5.5 (today's exception). Reviewer: Claude Opus 5.5, fresh. Base commit: `3c5c920` on `main`.

Sasha, Cursor chat, 2026-10-29: "Apply all the fixes, lock the best open model approach, then I rerun things on my end and we iterate on report again, go." He also said that when several open-model setups are still worth trying, Opus plans, Sonnet implements and Opus reviews, in a loop. He reruns the full session himself once the code is locked, so **this task makes no paid call**.

Follow `.claude/skills/change-analyzer/SKILL.md` for `analyzer/`, then `.claude/skills/validate-change/SKILL.md` before you report. Read `AGENTS.md` first.

Hard rules for this task:
- No model call, no Voice Transcribe call, no network. Tests use fakes.
- Never run `security`, never read the Keychain, never read `~/.config/`. Never print a key.
- Never run `rm`. Delete code by editing files.
- Do not touch `game/`. Do not read any held-out notes.
- Do not commit. Edit files only; the orchestrator commits.
- No em dashes and no spaced en dashes anywhere you write.

## The lock (Claude Opus 5.5's recommendation, which Sasha told us to lock)

The open-weights mode is: **Baseten, `meta-models/muse-spark-open-1026`, one client, each request carries the mp4 as `video_url` plus the clip's audio as a separate `input_audio` wav, and the existing Voice Transcribe text stays in the prompt and in `verified_quote()`.** Contributor Spark is unchanged: it already gets the video file with its sound.

Why, from what was measured (reviews 14 and 15 in `docs/reviews/`):
- Baseten accepts `video_url` (`data:video/mp4;base64,...`) plus a separate `input_audio` (plain base64, `format: "wav"`). The audio inside the mp4 is ignored: a 20 s clip alone replied HEARD NOTHING; the same clip plus the wav quoted him.
- Modal video without a transcript lost his notes. The open model does not go to Modal.
- Frames plus transcript quoted well and judged worse (a 15 s time grid, false stucks). Video plus wav judged best but quoted on only 5 of 16 keeps.
- Sasha, T3 Code chat, 2026-10-26 (DECISIONS.md): "Voice Transcribe stays, used per candidate: transcribe each 20-second clip, so the report's quotes are what I actually said and the check gets my words as text." `verified_quote()` drops any quote not in that transcript, so a wav-only check would store no quotes. **Do not remove or weaken `verified_quote`.**

There is one open path after this task. No frame path, no host switch, no flag that brings frames back.

## Fix 1: the open client sends video plus wav

File: `analyzer/client.py`.

Replace `_call_open_model` so every `meta-models/` call (the Spark candidate windows and the check) sends the video and a wav, never frames:

```python
# Video and its audio as a wav, plus the prompt, to one Baseten chat call.
# Baseten ignores the sound inside the mp4, so the wav goes as its own part.
def _call_open_model(
    *, model, prompt, video_path, purpose, cache_dir, costs_path, client, api_key
) -> dict:
    with tempfile.TemporaryDirectory(prefix="open-audio-") as tmp:
        wav_bytes = extract_audio(video_path, Path(tmp) / "clip.wav").read_bytes()
    video_bytes = Path(video_path).read_bytes()
    request = {
        "model": model,
        "prompt": prompt,
        "video_sha256": hashlib.sha256(video_bytes).hexdigest(),
        "wav_sha256": hashlib.sha256(wav_bytes).hexdigest(),
        "max_tokens": OPEN_MAX_TOKENS,
    }
    canonical = json.dumps(request, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    key = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    cache_file = cache_dir / f"{key}.json"
    if cache_file.exists():
        return json.loads(cache_file.read_text(encoding="utf-8"))

    if client is None:
        client = _make_open_client(api_key)
    content = [
        {"type": "video_url", "video_url": {"url": "data:video/mp4;base64," + base64.b64encode(video_bytes).decode("ascii")}},
        {"type": "input_audio", "input_audio": {"data": base64.b64encode(wav_bytes).decode("ascii"), "format": "wav"}},
        {"type": "text", "text": prompt},
    ]
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": content}],
        max_tokens=OPEN_MAX_TOKENS,
    )
    reply = _open_reply_to_dict(response)
    # (keep the existing "no answer text" block, the cache write and the cost line exactly as they are)
```

Also in `analyzer/client.py`:
- Import `extract_audio` from `tools.video`; drop the imports of `_frame_plan`, `probe_duration` and `sample_frames`.
- Delete `_image_data_url`.
- Remove the `clip_start_s` parameter from `call_model` and from the `_call_open_model` call. It only labelled frames. The required keyword arguments of `call_model` (`model`, `prompt`, `video_path`, `purpose`, and the optional `cache_dir`, `costs_path`, `client`, `api_key`) stay as they are, so existing callers and tests keep working.
- Update the module docstring ("goes to Baseten instead, frames only") and the comment above `call_model` ("as sampled frames") to say video plus a wav.
- Cost line: unchanged (`_append_cost_line`, one line per real call, one for an empty answer).

File: `tools/video.py`. The frame helpers have no caller left. Delete `CHECK_FRAME_INTERVAL_S`, `WINDOW_FRAME_INTERVAL_S`, `LONG_CLIP_S`, `FRAME_MAX_SIDE`, `MAX_FRAMES_PER_REQUEST` and their comment, `_probe_size`, `_frame_plan` and `sample_frames`. Before deleting, run `rg -n "_probe_size|_frame_plan|sample_frames|FRAME_|LONG_CLIP_S" --glob '!game/**'` and confirm only these definitions, `analyzer/client.py` and `tests/test_open_backend.py` use them. If anything else does, stop and report.

File: `analyzer/spark_test.py`, `_moments_for_cut`. Keep the Voice Transcribe call for `meta-models/` and the transcript in the prompt. Drop the frame sentence and `clip_start`:

```python
    call_prompt = prompt
    # The open model hears the wav; the transcript is the text quotes are checked against.
    if str(model).startswith("meta-models/"):
        wav = extract_audio(converted, Path(tmp_dir) / f"audio-{start:g}.wav")
        spoken = client_module.transcribe(
            wav, purpose=f"spark_test:{recording.name}"
        ).get("transcript") or ""
        call_prompt = (
            "What the player said in this clip (Voice Transcribe, may be empty):\n"
            + (spoken.strip() or "(nothing transcribed)")
            + "\n\n"
            + prompt
        )
    try:
        reply = client_module.call_model(
            model=model,
            prompt=call_prompt,
            video_path=converted,
            purpose=f"spark_test:{recording.name}",
        )
```

`analyzer/check.py` needs no client change: its `call_for` already passes the clip, and `transcript_for` already feeds the prompt and `verified_quote`.

Tests, file `tests/test_open_backend.py`. No network, no ffmpeg in the client tests:
- Replace the `frames` fixture with a `wav` fixture that monkeypatches `client.extract_audio` to write `b"wav-bytes"` to the given output path and return it as a `Path`. The video stays a tiny file written in `tmp_path` (`b"video-bytes"`, as `_video` does today). No binary goes into `tests/fixtures/`.
- Rewrite `test_open_request_shape` to the new shape: one user message; content types in order `video_url`, `input_audio`, `text`; the video URL starts with `data:video/mp4;base64,` and decodes to `b"video-bytes"`; `input_audio.data` decodes to `b"wav-bytes"` and `format` is `"wav"`; the text part is the prompt; no part has type `image_url`.
- Add: a second call with the same video but different wav bytes is a cache miss and makes a new call (the wav is in the cache key). The existing same-input test still proves a cache hit with no call and one cost line.
- Delete `test_open_request_labels_frames_when_the_clip_has_a_start`, `test_sample_frames_count_and_long_side`, `test_sample_frames_caps_a_long_clip_at_eight`, `_jpeg_size` and the `sample_frames` import.
- Keep, on the `wav` fixture: routing and marker strip, reply to `extract_text` and usage, one cost line per call, missing Baseten key, empty answer not cached.

If `tests/test_spark_test.py` asserts the old open-model prompt text or passes `clip_start_s`, update it to the new text and call.

## Fix 2: the prompts

File: `analyzer/prompts/check.md`. Add this paragraph right after the first paragraph (the one ending "Judge only what this 20-second clip shows."):

```
The game runs in {engine}. An editor or debugger on screen is that engine. Do not name a different engine.

The clip comes with the player's voice. Quote the player's words from the audio, word for word, and only words that are also in the transcript below.
```

Add these two sentences at the end of the "Decide keep or drop." paragraph:

```
A locked door with no puzzle behind it, which the player leaves, is not stuck. A moment the player solves inside the clip is not stuck.
```

In the reply JSON line, change the `quote` description from `"the player's exact words at the moment, or null"` to `"the player's exact words at the moment, heard in the audio and also in the transcript, or null"`. Keep the doubled braces.

File: `analyzer/prompts/spark_test.md`. This prompt is read raw (no `.format`, its JSON uses single braces) and `spark_test.py` has no log, so it cannot fill `{engine}`. It gets the same rule without a name. After the first line add:

```
An editor or debugger on screen is the game's own engine. Do not name an engine.
```

Replace the quote rule and add two rules:

```
- quote is the player's exact words at that moment, heard in the audio, word for word, or null if they said nothing relevant.
- A locked door with no puzzle behind it, which the player leaves, is not stuck.
- A moment the player solves inside the video is not stuck.
```

File: `analyzer/check.py`. Add one helper and thread `engine` through:

```python
# The engine named in the log's session_start, for the check prompt.
def engine_name(events) -> str:
    for event in events:
        if event.get("event") == "session_start" and event.get("godot_version"):
            return f"Godot {event['godot_version']}"
    return "unknown"


def build_prompt(template: str, candidate, transcript: str, log_slice: str, outline: str = "", engine: str = "unknown") -> str:
    return template.format(
        time_s=candidate["time_s"],
        kind=candidate["kind"],
        reason=candidate["reason"],
        quote=candidate.get("quote") or "null",
        transcript=transcript.strip() or "(nothing transcribed)",
        log_slice=log_slice.strip() or "(no event log for this session)",
        outline=outline.strip() or "(no session outline)",
        engine=engine,
    )
```

`run_checks` gains `engine="unknown"` as a keyword argument and passes it to `build_prompt`. In `main`, pass `engine=engine_name(events)` to `run_checks` (`events` is `[]` without `--log`, which gives "unknown"). With `tests/fixtures/session_log.jsonl` the value is `Godot 4.7.2-stable (official)`.

Tests, `tests/test_check.py`: `engine_name` on the session log fixture gives `Godot 4.7.2-stable (official)`; on `[]` gives `unknown`; `build_prompt(..., engine="Godot 4.7.2")` puts `The game runs in Godot 4.7.2.` in the prompt; the existing `build_prompt` call without `engine` still formats (no `KeyError`) and says `unknown`.

## Fix 3: one card per moment

File: `analyzer/check.py`. One function, called once in `main`, right after `run_checks` returns and before `beats_module.zone_intervals` / `beats_module.assign_beats`:

```python
    findings = run_checks(...)
    findings = merge_same_moment(findings)
    zones = beats_module.zone_intervals(events, args.video_flash_s) if events else []
```

The rule: merge only kept findings that share a `kind` and sit within 8 seconds of the previous kept finding of that kind (a chain, so 493.8, 496.2 and 504.1 s are one group). In each group keep the first one that has a `quote`, else the earliest. Take nothing else from the others: no union of quotes, notes, sources or clips. The others leave the list. Dropped findings stay where they are, untouched. Then renumber `rank` 1, 2, 3 over the kept findings in list order.

```python
MERGE_WINDOW_S = 8.0


# Kept findings of one kind within MERGE_WINDOW_S of the previous one are
# one moment seen twice: keep the one with a quote, else the earliest.
def merge_same_moment(findings):
    kept = sorted(
        (f for f in findings if f["check"]["verdict"] == "keep"),
        key=lambda f: f["time_s"],
    )
    groups = []
    open_group = {}
    for finding in kept:
        group = open_group.get(finding["kind"])
        if group and finding["time_s"] - group[-1]["time_s"] <= MERGE_WINDOW_S:
            group.append(finding)
        else:
            group = [finding]
            groups.append(group)
            open_group[finding["kind"]] = group
    merged_away = set()
    for group in groups:
        keeper = next((f for f in group if f["quote"]), group[0])
        merged_away.update(id(f) for f in group if f is not keeper)
    result = [f for f in findings if id(f) not in merged_away]
    rank = 0
    for finding in result:
        if finding["check"]["verdict"] == "keep":
            rank += 1
            finding["rank"] = rank
    return result
```

Tests, `tests/test_check.py` (build the findings by hand in the `run_checks` shape):
- Three kept `suspected_bug` findings at 100.0, 104.0 and 108.0 s, only the middle one with a quote, become one finding: the 104.0 s one, rank 1.
- A kept `stuck` at 200.0 s and a kept `surprised` at 206.0 s both stay.
- A dropped finding at 102.0 s stays, rank `None`.
- Ranks of the kept ones are 1, 2, 3, and the result loads through `analyzer.findings.load` when wrapped as in `test_run_checks_keeps_and_drops_into_valid_findings`.

## Fix 4: the page

File: `report/render.py`.
- In `_render_tiles`, render the time-lost tile only when `summary["lost_s"]` is not 0. Do not compute or invent `end_s` anywhere; `check.py` still writes `end_s: None`.
- In `LABELS["friction"]["learning"]`, change the tag `"planned challenge?"` to `"by design"`, with this comment on the line above it: `# Proposal (Claude Opus 5.5, 2026-10-29), not Sasha's wording.` The wording is Claude Opus 5.5's proposal, not Sasha's decision.

Tests, `tests/test_report.py`: change the `("learning", 1, "planned challenge?", False)` row to `"by design"`. Add one test: a copy of the redesign fixture with `summary.lost_s` set to 0 renders no `Time lost to being stuck or confused`; the fixture as it is (285) still renders it.

## Fix 5: README

File: `README.md`. Replace "How to run it comes here once it runs." so the status line ends at "to 2026-11-04." and add a `## Run it` section after the status line with exactly the commands below (real modules and flags at the base commit). Do not add a video link.

````
## Run it

You need Python 3.13 with `requirements.txt` in `.venv`, and ffmpeg. The keys live in the macOS Keychain; the two scripts below read them for one process only.

Normal mode, Muse Spark contributor:

```
tools/run-analyzer.sh analyzer/spark_test.py <recording.mp4> --window-seconds 120
tools/run-analyzer.sh analyzer/check.py <recording.mp4> runs/spark_test/<stem>-window120s-muse-spark-1.2-contributor.json --log <session.jsonl> --video-flash-s <seconds> --out runs/check/<stem>-findings.json
.venv/bin/python -m report.render runs/check/<stem>-findings.json -o runs/check/<stem>-report.html
```

Open-weights mode, Muse Spark Open on Baseten (the video and the audio go to the open model; Voice Transcribe supplies the text that quotes are checked against):

```
tools/run-baseten.sh analyzer/spark_test.py <recording.mp4> --window-seconds 120 --model meta-models/muse-spark-open-1026
tools/run-baseten.sh analyzer/check.py <recording.mp4> runs/spark_test/<stem>-window120s-meta-models-muse-spark-open-1026.json --model meta-models/muse-spark-open-1026 --log <session.jsonl> --video-flash-s <seconds> --out runs/check/<stem>-findings-open.json
.venv/bin/python -m report.render runs/check/<stem>-findings-open.json -o runs/check/<stem>-report-open.html
```

`--video-flash-s` is the video time of the game's start flash: `.venv/bin/python -c "from tools.video import find_start_flash; print(find_start_flash('<recording.mp4>'))"`. The check writes the areas, the route, the heat and the summary from the log. To redo only the areas on an existing file: `.venv/bin/python -m analyzer.beats <findings.json> --log <session.jsonl> --video-flash-s <seconds> -o <new findings.json>`.
````

Before writing it, confirm each flag with `--help` on `analyzer/spark_test.py`, `analyzer/check.py`, `analyzer.beats` and `report.render` (these do not need a key: run them as `.venv/bin/python analyzer/check.py --help` and so on; `--help` exits before the key check). If one differs, use the real flag and say so in your report.

Builder line: change "Built with coding agents run from T3 Code: Muse Code (Meta) on Muse Wonder, Grok through Cursor, and Claude Code." to "Built with coding agents run from T3 Code: Muse Code (Meta), Grok through Cursor, and Claude Code." Nothing else in that line.

## Out of scope

A full paid rerun, any model or transcribe call, Modal, a host switch, an upper-floor map, the public checklist, `game/`, filling `end_s`, any page wording beyond "by design", `DECISIONS.md`, `AGENTS.md`, `PLAN.md`, `STATUS.md`, `docs/design/`.

## Files Sonnet may touch

- `analyzer/client.py`
- `analyzer/spark_test.py`
- `analyzer/check.py`
- `analyzer/prompts/check.md`
- `analyzer/prompts/spark_test.md`
- `tools/video.py` (deletions only)
- `report/render.py`
- `tests/test_open_backend.py`
- `tests/test_check.py`
- `tests/test_report.py`
- `tests/test_spark_test.py` (only if it asserts the old open prompt or `clip_start_s`)
- `README.md`
- this file (the "What came back" section only)

## Checks

```
.venv/bin/python -m pytest -q
rg -n "image_url|sample_frames|_frame_plan|clip_start_s|planned challenge" analyzer tools report tests README.md
rg -n "\x{2014}| \x{2013} " analyzer/prompts README.md docs/tasks/27-fixes-now.md
git diff --stat
```

## Done means

1. `pytest -q` passes, with the same deselects as before (report the passed and deselected counts). No test touches the network or the Keychain.
2. The first `rg` prints nothing: no frame path, no `clip_start_s`, no old tag is left. The second `rg` prints nothing.
3. A `meta-models/` call sends exactly one `video_url`, one `input_audio` wav and the prompt, and caches by model, prompt, video bytes and wav bytes (proven by the new tests).
4. `verified_quote` is unchanged and still applied to every check quote.
5. The check prompt names the engine from `session_start`, or "unknown"; the Spark prompt names none; both carry the two "not stuck" rules and the audio quote rule.
6. `merge_same_moment` is called once, between `run_checks` and `assign_beats`, and its tests pass.
7. The page hides the time-lost tile at 0, shows "by design" with the proposal comment, and `end_s` is still `None` from the check.
8. The README has the run commands for both modes and no Muse Wonder in the builder line.
9. Nothing committed, nothing outside the list above changed (`git status` shows `game` as it was).

## Report back

End with: files changed, the commands and their exit codes or counts, and what you did not check. Do not paste the files.

A 120 s window as one `video_url` plus a wav already succeeded on Baseten on 2026-10-29 (the lobby session, five windows, page `runs/check/cogito-report-baseten-av.html`). Do not probe it again and do not fall back to frames. That run was outside this client, which is why the client change is still required.

## What came back

Claude Sonnet 5.5, Cursor, 2026-10-29. Nothing committed. No model call, no network, no Keychain.

Files changed: `analyzer/client.py`, `analyzer/spark_test.py`, `analyzer/check.py`, `analyzer/prompts/check.md`, `analyzer/prompts/spark_test.md`, `tools/video.py` (deletions only, plus the now unused `import math`), `report/render.py`, `tests/test_open_backend.py`, `tests/test_check.py`, `tests/test_report.py`, `README.md`, and this section. `tests/test_spark_test.py` needed no change (it never asserted the old open prompt or `clip_start_s`). `game` shows ` m` in `git status` as it did before the task.

What was done:
- Fix 1: `_call_open_model` sends `video_url`, `input_audio` (wav) and the text, and caches by model, prompt, video bytes and wav bytes. `clip_start_s`, `_image_data_url` and the frame helpers and constants in `tools/video.py` are gone. The pre-delete `rg` showed only the brief's expected users (`analyzer/client.py`, `tests/test_open_backend.py`, and the definitions). `verified_quote` is untouched.
- Fix 2: both prompts and `engine_name` / `engine` threading as written.
- Fix 3: `merge_same_moment`, called once in `main` between `run_checks` and `zone_intervals` / `assign_beats`.
- Fix 4: the time-lost tile is skipped when `summary["lost_s"]` is 0; the tag is `by design` with the proposal comment; `end_s` is still `None`.
- Fix 5: `## Run it` section and the builder line. `--help` on `analyzer/spark_test.py`, `analyzer/check.py`, `analyzer.beats` and `report.render` showed every flag in the brief exists as written, and the candidates file name `<stem>-window120s-<model with / as ->.json` matches `spark_test.py`.

Checks:
- `.venv/bin/python -m pytest -q`: 184 passed, 1 failed. The one failure is `tests/test_transcribe.py::test_extract_audio_from_say_clip` (`probe_duration` returned None in the sandbox), as the task predicted.
- `.venv/bin/python -m pytest -q --deselect tests/test_transcribe.py::test_extract_audio_from_say_clip`: 184 passed, 1 deselected.
- First `rg` (image_url, sample_frames, _frame_plan, clip_start_s, planned challenge): no output, exit 1. I dropped the brief's "no part has type `image_url`" assertion from `test_open_request_shape` because its literal would match the rg; the exact type list `video_url, input_audio, text` already proves no image part.
- Second `rg` (em dash, spaced en dash in `analyzer/prompts`, `README.md`, this file): no output, exit 1.

Not checked: a real Baseten call (by instruction); the real `extract_audio` inside `_call_open_model` (tests fake it); the say-clip test (sandbox); the report page in a browser; the effect of the new prompt text on real findings.

What the orchestrator changed: recorded the lock in DECISIONS.md, put the review nits in docs/FOLLOWUPS.md, and updated STATUS.md. No product code after the PASS.

## What came back: the prompt rewrite

Claude Opus 5.5, Cursor, 2026-10-29, at Sasha's request (Opus, not Sonnet, owns the prompt wording). Nothing committed. No model call, no network, no Keychain. Base: `31e07d7`.

Files changed: `analyzer/prompts/check.md`, `analyzer/prompts/spark_test.md`, and this section. No test asserted the replaced sentences, so no test changed; `The game runs in {engine}.` is kept, which `test_build_prompt_names_the_engine` asserts.

The rules Sonnet added this morning are rewritten as one instruction each, and Sasha's 2026-10-28 report notes (DECISIONS.md) are encoded as rules, not quoted:
- Check prompt: the editor or debugger on screen is `{engine}`, never another engine. A quote is copied word for word from the Voice Transcribe text; the audio only places the moment; no transcript words means `quote` is null. Stuck means not getting past something during the clip; a locked door with nothing behind it that the player leaves, a problem solved inside the clip, and learning how a thing works and then doing it are not stuck; getting past it only later still counts as stuck here. Surprised is a real reaction, not a staged reveal the player saw coming; when unsure, drop. The area is the zone the event log names when it names one, else the plain room on screen, never an invented biome, region or multi-room name. The puzzle is null for most moments: only a real puzzle (a lock, a code, a specific device) counts, never walking, a door, a pickup or looking around; the log's puzzle name wins. The old sentence "Do not drop a moment only because the player eventually progressed" is replaced by the "only later" stuck rule; the bug rule keeps its own "even when the player then moves on". The JSON shape is unchanged, braces still doubled.
- Spark prompt: never name a game engine, even with an editor on screen. Quote the words as said; when a transcript is prepended (open mode), copy from it and add nothing. The same three not-stuck cases and the surprise rule (when unsure, leave it out). Same JSON array shape, single braces.

Checks: `.venv/bin/python -m pytest -q --deselect tests/test_transcribe.py::test_extract_audio_from_say_clip`: 184 passed, 1 deselected. `build_prompt` on the new template formats with no `KeyError` and leaves no stray brace before the reply line. The em dash and spaced en dash `rg` on `analyzer/prompts` and this file: no output.

Not checked: the effect on real findings (no run, so no before and after findings in `runs/` yet; Sasha's rerun is that run); whether real logs put a zone name inside a clip's 20 s log slice, since `zone_enter` may fall before the clip.

## What came back: clip crossings

Claude Opus 5.5, Cursor, 2026-10-29, at Sasha's request ("ask opus to solve it somehow, that we have clip splits, maybe there is some nice method of how to do some crossing or whatever, let it solve the problem."). Nothing committed. No model call, no network, no Keychain. Base: `75777b5`.

Method, one idea for both cuts: carry what is still true across the cut.
- Candidate pass: the 120 s windows now overlap by `WINDOW_OVERLAP_S = 20.0`, the check clip's length, so they start at 0, 100, 200, ... Any 20 s moment, at an old edge or a new one, lies whole inside one window. Each window is still 120 s; windows stop once one reaches the end. A 930 s recording takes 10 calls instead of 8 (about 20% more candidate cost). A window of 20 s or less is refused with a clear message. `merge_window_moments` is unchanged: its 5 s cross-window repeat drop now catches a moment both overlapping windows report. Only its comment changed ("seam" to "overlap").
- Check pass: `log_slice_text` opens with one line per zone still open at the clip start (entered before it, not exited before it), taken from `beats.zone_intervals`, not a second tracker. The line looks like `[video 111.0s, before this clip, still open] {"event": "zone_enter", "puzzle": "Keypad door", "zone": "Laboratory"}`. Lines inside the clip are as before. No prompt sentence changed: the check prompt already says to use the log's zone and puzzle names, and the carried line says itself that it comes from before the clip.

Files: `analyzer/spark_test.py` (`WINDOW_OVERLAP_S`, `window_starts`, the CLI guard), `analyzer/check.py` (`log_slice_text`), `tests/test_spark_test.py`, `tests/test_check.py`, this section. `verified_quote` and both prompts are untouched.

Tests: `test_window_starts_cover_the_recording` asserted the old hard edge on purpose, so it is now `test_window_starts_cover_the_recording_with_overlap` (the new starts, the short case and the refusal). New: a 20 s clip around moments at 98, 101, 119, 121, 238, 242, 505 and 915 s fits whole in some window; a `zone_enter` before the clip with no zone event inside still names the Laboratory and Keypad door at the top of the slice, and a zone closed before the clip is not carried; a `zone_enter` inside the clip prints exactly as before.

Checks: `.venv/bin/python -m pytest -q --deselect tests/test_transcribe.py::test_extract_audio_from_say_clip`: 187 passed, 1 deselected.

Not checked: a real run. The new window starts change the request hashes, so a rerun of the candidate pass misses the cache from window 2 on and is billed again (about 20% more calls than before). I did not check whether the 5 s repeat drop holds when two overlapping windows place one moment more than 5 s apart; `merge_same_moment` (8 s, same kind) after the check is the backstop, and no threshold was retuned. Carried state is zones only; no other event (an item held, a puzzle half solved) is carried, since nothing in the log tracks it today.
