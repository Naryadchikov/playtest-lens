# 26: Muse Spark Open, why it returned [] and the Modal option (Opus investigation)

Author: Claude Opus 5.5, Cursor subagent, read only, 2026-10-28. No paid call, no Keychain read. Grok's parallel take is 26-open-model-grok.md.

## Why [] is the likely result
The open run got far less input than the contributor run, and the prompt gave it a sanctioned way out.
1. **No audio.** The prompt says "the game screen with the player's voice thinking aloud" and asks for quotes. Think-aloud confusion is mostly spoken. `_call_open_model` sends only images and text; the contributor got the whole video with sound.
2. **8 stills per 120 s.** `_frame_plan` gives max(4 s, 120/8) = one frame every 15 s. Stuck or confused is a change over time (backtracking, repeated attempts), which 8 far-apart stills rarely show.
3. **Frames carry no times.** The content list is 8 `image_url` parts and the prompt, with no label saying which second each frame is. The prompt then says "Never guess a time: if you cannot place a moment, leave it out" and "If there are no such moments, reply with []". A careful model that cannot place a moment obeys and returns [].
4. **It was not cut off.** finish_reason stop and 342 to 983 output tokens: it reasoned, then chose []. Raising max_tokens won't change this.

So [] says little about the model yet; it says the request gave it no sound, no motion and no clock.

## What a one-window comparison should change
Use one 120 s window where the contributor run found the most moments, and keep the prompt, the frames and max_tokens fixed except for the one change being tested. Each step is one call, about $0.01 to $0.05.
1. **Same request on Modal and Baseten.** If both give [], the cause is the input, not the host. (Baseten serves `meta-models/muse-spark-open-1026`, Modal serves `meta-models/Muse-Spark-Open-816B-A42B`; the docs don't say whether these are the same checkpoint.)
2. **Times on the frames.** Put a text part such as `frame at 37.5 s` before each image. This is the cheapest fix and works on both hosts.
3. **Denser frames around one known moment.** A 16 s cut centred on a contributor moment, 8 frames at 2 s. It tests whether motion matters, inside the 8-frame cap.
4. **Audio (Modal only, if the shape is confirmed).** Modal lists Text, Image, Video, Audio input for this model. Adding the window's audio, or its Voice Transcribe text with times, is the change most likely to match the contributor. Transcribe text bills to the Meta pool, so it needs Sasha's yes.
Compare each result to the contributor's moments in that window by time (within 5 s) and kind.

## Modal: what the public docs say
- **Listed: yes.** `modal.com/docs/guide/supported-models` lists "Muse Spark Open" under Shared Endpoint models: Text, Image, Audio; $1.25 per Mtok in, $0.15 cached, $4.25 out. The library page (`modal.com/library/meta/muse-spark-open`) adds Video and says Shared only (no Dedicated Endpoint).
- **Model id:** `meta-models/Muse-Spark-Open-816B-A42B` (from the library page's create command). The docs say to set `model` in requests "to the value shown in the dashboard's request examples", or read it from `GET /v1/models`. Confirm it there before the first call.
- **Create (free; not done):** `modal endpoint create --shared --model meta-models/Muse-Spark-Open-816B-A42B`. Our workspace has no Muse endpoint yet; this needs Sasha's yes.
- **Call shape:** OpenAI-compatible Chat Completions (`POST <endpoint URL>/v1/chat/completions`), Responses API or Anthropic Messages, with `Authorization: Bearer <proxy token id>.<secret>`. The same proxy token as `tools/run-modal-agent.sh` should work. The URL comes from the dashboard; by our existing pattern it would be `https://naryadchikov--ep-<name>-server.us-west.modal.direct`, which is a guess until the dashboard shows it.
- **Not documented:** how to pass audio or video in a chat message (e.g. `input_audio` or `video_url` parts). The docs show only text examples. Don't build the audio step on a guessed shape: test it with one small call first, or ask Meta's or Modal's docs.
- **Billing catch:** the shared-endpoints page says "Credits included with your plan cannot be used for Shared Endpoint usage." So the $30 free plan credit won't pay for this, and every call bills Sasha's own balance (the $100 kept for Muse Open). The same rule also applies to the DeepSeek, GLM and Kimi shared endpoints. Worth checking against Modal's usage view.

## Suggested next step (proposal, Claude Opus 5.5)
Sasha approves creating the Modal endpoint. The open client gets a host switch and per-frame time labels (DeepSeek, analyzer/client.py). Then run comparison steps 1 and 2 on one window, under $0.20 total.
