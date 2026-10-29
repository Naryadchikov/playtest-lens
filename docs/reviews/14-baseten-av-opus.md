# 14: Baseten video plus audio (Opus cross-review)

Reviewer: Claude Opus 5.5, Cursor, fresh. I did not build this. Read only, at commit `3c5c920`. No API call, no Keychain. I did not watch the footage or open a clip, so nothing below says what is on screen. Every recommendation here is mine (Claude Opus 5.5), not Sasha's.

Files read: `runs/check/cogito-findings-baseten-av.json`, `runs/check/cogito-report-baseten-av.html`, review 13, and, to compare, `cogito-findings-open.json`, `cogito-findings-25.json` and `cogito-findings-modal-video.json`.

## The pick

**Ship video plus a separate wav on Baseten as the open path, but only once it runs through `analyzer/client.py` and the quote prompt is fixed. Do not ship this file as it stands. Until both are done, the frames plus transcript page (`cogito-report-open.html`) is still the safer open page.**

It beats Modal video on every line of Sasha's notes I can check, and it beats frames plus transcript on judgment: fewer false stucks, real times, one kept vent card. It loses to frames plus transcript on quotes, and quotes are what the page reads as proof.

| | Frames plus transcript (open) | Modal video, no voice | Baseten video plus wav (this run) |
|---|---|---|---|
| Kept | 18 of 36 | 11 of 22 | 16 of 27 |
| Kept with a quote | 18 | 0 | 5 |
| Candidate times on the 15 s frame grid | 18 | 0 | 2 |
| In `client.py`, cached | Yes | No | No (no `video_url` or `input_audio` in `analyzer/`, no cache entry after 00:05; costs are logged as `spark-av` and `check-av`) |

## Did the wav fix the voice gap I named?

**It fixes hearing. It does not fix quoting.** The model clearly hears him now: the quotes it does give match the transcript run closely ("Can I open? No oh wait I can spin it maybe I can bypass the lock this way", "I want another piece of paper should I be disappointed that I can't find it anywhere", "Oy oy", "That's actually bad"), and some checker notes rely on what he says.

Quotes are still too thin to ship. 5 of 16 keeps have one, and 3 of those 5 are the crash at the end. The gap is in what gets written down, not in what is heard:
- Hidden room (207 s): the note says "eliciting audible surprise", but the quote is null. The transcript run had "oh my god there was a hidden room".
- Bear trap (465 s): the note says "while player questions breaking it", but the quote is null.
- Vent: the only quote went onto the dropped card (431 s). The kept card (427 s) has none.
- Decoy laptop (185 s): kept with no quote. The transcript run had "Wait, why it said quest failed?".
- The 311 s candidate was dropped because the clip showed "no repeated closet opens". The transcript run quotes "I opened all the closets here. No page, no page." around 300 to 309 s. I can't tell from the files if that line falls inside the 301 to 321 s clip, so this may or may not be a wrong drop.

## Against Sasha's notes

| His note | This run | Read |
|---|---|---|
| Lobby door is world-building, not a medium stuck | No lobby door card. The 32.8 s candidate is dropped as normal orientation | Right, and the first run to get it right |
| CEO door solved on purpose | No CEO door stuck. The 113.5 s clip (103.5 to 123.5 s) became a suspected bug about a floating "Cutscene Trigger" label | Door right. The label card needs his eye: it could be a real leftover debug volume or a misread |
| Lockpick solved on purpose | No stuck on using it. But 54.5 s is kept as **stuck** on finding it in a cabinet, with `resolved: solved` and no quote | Same class of error: a quick success called stuck |
| Only Code Lock is a puzzle | The page shows only Code Lock (the checker's free-text puzzle names, such as "Retrieve Lockpick from Break Room", are not on the page) | Right on the page |
| Archive is his volume name for the break room | Labels mix "Break Room", "Archive Break Room" and "Archive" | His rename, as before |
| Vent missed or called a wall panel, before camera and trap | Kept once at 427 s, surprised, named "duct door" from the event log (lock cleared 429.2 s, door open 430.3 s). It comes before the bear trap (460 s). No camera card in this run | Best of the four runs. Two other cards for the same moment were dropped |
| Hidden room | Kept at 207.0 s, surprised. HiddenDoor event at 207.7 s. Called a "geometric lion head" sculpture | Within 1 s. The wording needs his eye |
| Map on the whole route, heat as a separate toggle | "From start" is on the page and heat is its own view | Met |

## Still wrong

1. **Three cards for one crash** (493.8, 496.2, 504.1 s), all kept as suspected bugs. The last one says "Unity/VS code-editor and Shader Graph". The game is Godot, and the transcript run said Godot. Any quality bar here counts a wrong engine name as wrong data.
2. **Two cards for the Code Lock** (345 s stuck, 353 s confused, clips overlapping).
3. **Kept stuck with `resolved: solved`** (54.5 s). The check returns both, and they contradict each other.
4. **Weak keeps without a voice behind them:** the fridge inventory "hesitation" (68.8 s) and the Quest Failed pause (152 s) rest only on the picture. I can't judge them without the clip.
5. **The `0:00` time-lost tile** is still on the page (`lost_s` is 0.0), as in review 12.

## A decision for Sasha (not a fix)

The host is not in question: this run stays on Baseten, the decided host. The open question is what feeds the open mode's voice:
- (a) The wav only, with no Voice Transcribe call. The open mode then runs on the open model alone, and nothing is billed to the $23.90 Meta pool. My recommendation (Claude Opus 5.5), if the quote fix below brings quotes back.
- (b) The wav plus the Voice Transcribe text in the transcript slot. It is the surest way to get quotes, but it adds a Meta API call to the open mode.

Modal: no reason left to move. This run beats it on his notes.

## Fixes still needed

In the prompts (DeepSeek, `analyzer/prompts/`):
1. When there is no text transcript, the `quote` field takes the player's words heard in the attached audio, word for word, and a note that relies on speech must carry that speech as a quote. This one change would have filled the hidden room, the bear trap and the decoy laptop.
2. A moment the player resolves within the clip is not stuck (54.5 s; same family as review 13's locked-door line).
3. Name the engine as Godot in the check prompt's context, or tell it not to name an engine.

In `analyzer/client.py` and the pipeline (DeepSeek, `analyzer/`):
1. Move `video_url` plus `input_audio` into the one client, with cache and cost lines, as the open-mode input. Today this run can't be replayed offline, and a rerun costs again (about $0.57).
2. Merge kept findings on the same moment into one card, carrying over the quote from any merged candidate (the crash, the Code Lock, and the vent quote that is now stuck on a dropped card).

Then rerun the open mode once through the client and let Sasha judge the page.

## What I did not check

I didn't watch any clip or listen to any wav, so I can't say whether the quotes are word for word, whether the "Cutscene Trigger" label or the lion-head sculpture are real, or whether the 311 s drop was wrong. I didn't read the one-off script, which is not in the repo. I ran nothing.
