# 21: Open-weights backend (Muse Spark Open on Baseten)

**Author:** DeepSeek V4.1 Flash 1017 on Modal, through `tools/run-modal-agent.sh deepseek`, in `.worktrees/ds-21` on branch `ds/21-open-weights`.
**Reviewer:** Grok 4.7 (xhigh, fast) through Cursor, a fresh thread.
**Base commit:** ecce194 on `main`.

## Why

Sasha, T3 Code chat, 2026-10-28: "I think for Muse Open and open weight thing lets use Baseten and compete in the another prize category." The hackathon has a bonus prize for the best build on Meta's open-weight models. The product's pipeline (candidates, check, beats, report) stays one path; the open-weights mode only changes which model answers a clip. Sasha, 2026-10-28: "And then as seperate thing we will have open model mode, so I can call it as well and try to compete in several hakaton categories."

## Facts you can rely on

Baseten is OpenAI compatible (from Baseten's email to Sasha, 2026-10-28):

```python
from openai import OpenAI
client = OpenAI(base_url="https://inference.baseten.co/v1", api_key=KEY)
response = client.chat.completions.create(
    model="meta-models/muse-spark-open-1026",
    messages=[{"role": "user", "content": "Hello!"}],
)
```

"Use exactly meta-models/muse-spark-open-1026. Your key only works with this hackathon model." The key is in the macOS Keychain (service `BASETEN_API_KEY`). It reaches Python only through `tools/run-baseten.sh <script> [args]` (a sibling of `tools/run-analyzer.sh`), as the environment variable `BASETEN_API_KEY`, for that one process. A first text call worked; its reply came back with a stray `<|start|>assistant` marker and reasoning tokens counted in `usage`, so check the raw reply and strip what is not the answer.

## Probe results (orchestrator, 2026-10-28, already done: do not repeat them)

- **Images work.** `{"type":"image_url","image_url":{"url":"data:image/jpeg;base64,<b64>"}}` inside the user message `content` list, next to a `{"type":"text",...}` part. A 512 px JPEG cost about 180 prompt tokens and the model described it correctly.
- **Audio does not work on Baseten.** `{"type":"input_audio","input_audio":{"data":"<plain b64 wav>","format":"wav"}}` is accepted (prompt tokens grow, about 12 per second) but the model answers that it received no audio. A data URL there gives a 400, `audio_url` is ignored, `file` is a 400. So the open-weights mode sends **frames only**; the player's words reach the model as text inside the prompt (the check prompt already carries the transcript from Voice Transcribe). Do not send audio.
- **Replies have reasoning.** `message.content` holds the answer and `message.reasoning_content` the model's notes; use only `content`, and give `max_tokens` enough room (at least 1500, the reasoning counts against it: with 400 the content came back empty). A reply can start with a stray marker such as `<|start|>assistant`: strip it from the text.
- The response is a normal OpenAI `chat.completions` object (`usage.prompt_tokens`, `usage.completion_tokens`).

## Goal

`client.call_model(model="meta-models/muse-spark-open-1026", prompt=..., video_path=..., purpose=...)` works at every existing call site (`analyzer/spark_test.py`, `analyzer/check.py`) with no change to them, and returns a dict that `extract_text` and `usage_and_cost` already read. One path: do not copy the pipeline.

1. **Routing.** In `analyzer/client.py`, a model id that starts with `meta-models/` takes the open-weights backend: it cuts the video's frames, sends one `chat.completions` call to Baseten, and wraps the reply so `extract_text` finds the text (`output_text`) and `usage_and_cost` finds `input_tokens` and `output_tokens`. Everything else stays as it is.
2. **Frames.** In `tools/video.py`, a helper that samples N frames from a clip (JPEG, long side at most 768 px, evenly spaced, default 1 frame per 2 s, at most 12 frames per request) with ffmpeg. For a 2-minute window (the Spark candidate pass) use 1 frame per 4 s, still at most 30 frames. No audio. Do not probe Baseten for limits beyond the one live proof below.
3. **Key.** `BASETEN_API_KEY` from the environment, with a clear stop message if it is missing, like `require_api_key`. Never print, log, write or put the key in a URL or an exception text.
4. **Cache and cost.** The reply is cached in `runs/cache/` by a hash of the request (model, prompt, frame hashes) and each real call appends a line to `runs/costs.jsonl` with the model id, tokens and a `cost_usd` from a `PRICES` entry. Baseten's price for this model is unknown to us: look it up in Baseten's public pricing or model page (WebFetch is allowed) and say where you found it; if you cannot find it, set the entry to `None` and say so in your report.
5. **Tests** in `tests/test_client.py` (or a new `tests/test_open_backend.py`), offline, with a fake client: routing by prefix, request shape, the wrapped reply, cache hit with no call, missing key, one cost line per real call. The existing suite still passes: `.venv/bin/python -m pytest -q`.
6. **One live proof**, one only: run the checking pass on one cached Talos clip through the open model:
   `tools/run-baseten.sh analyzer/check.py recordings/spike/talos.mp4 runs/check/talos-candidates.json --model meta-models/muse-spark-open-1026 --limit 1 --out runs/check/talos-findings-open-probe.json`
   It must produce a parsed finding or a clear failure message you can read. Total live Baseten spend for the task: under $1 (about 5 small calls at most).

## Files you own

`analyzer/client.py`, `tools/video.py`, `tests/test_client.py`, a new `tests/test_open_backend.py`, `tools/run-baseten.sh` (already there; change only if it is wrong), and this file. Nothing else. Do not touch `analyzer/beats.py`, `report/`, `game/`, `DECISIONS.md`, `AGENTS.md`, `PLAN.md` or `STATUS.md`.

## Rules (from AGENTS.md, repeated because you will not see the conversation)

- Never print, log, write, export or echo a key or token. Never read `~/.config/` or any credential file. Never run `security` yourself: only `tools/run-baseten.sh` reads the Keychain.
- Never run `rm` or delete anything. Do not commit; leave the diff in the worktree.
- No em dashes and no spaced en dashes in anything you write. English only. Comments brief, above the function, in the style of the file you edit.
- Fix the case that happened; no speculative options. One module talks to the models; one path.
- `runs/`, `recordings/` and `.venv` are symlinks to the main checkout and are git-ignored: leave them alone.
- Do not call any t3-code tools.

## Done means

- The offline suite passes (`.venv/bin/python -m pytest -q`), output pasted.
- The live proof ran once; its output file path and `runs/costs.jsonl` line are named.
- Work in this order and write code early: first the `tools/video.py` helper and the routing, then tests, then the one live proof. Do not spend turns re-reading files you have already read.
- A final report of at most 25 lines: files changed, commands run, evidence paths, probe results (what Baseten accepts), the price found and where, and what you did not check.

## What came back

DeepSeek, second run (the first ran out of its 30 turns on exploring and changed nothing; the orchestrator did the Baseten probes and the rerun had 90 turns). `meta-models/` ids route to Baseten in `analyzer/client.py`, frames only, with `sample_frames` in `tools/video.py`; 110 tests passed. Baseten takes at most 8 images per request, and the reasoning counts against `max_tokens` (4096 works, 1500 returned an empty answer). Price $1.25 in, $4.25 out per million (baseten.co/pricing). The live proof ran the checking pass through the open model on one Talos clip with Voice Transcribe stubbed: one kept finding, $0.026 for two charged calls.

Grok 4.7 review: PASS, no blockers. Orchestrator changes (commit 39cbb63): an empty answer now raises and is not cached (its tokens are still costed); `tools/run-baseten.sh` also exports the Meta key when it is in the Keychain, because the check transcribes each clip with Voice Transcribe; contributor prices ($0.10 in, $0.20 out, from Meta's pricing page); one test. Non-blocking notes in docs/FOLLOWUPS.md. Not yet done: the side-by-side run of the open model and the hosted pass on the Talos clips.
