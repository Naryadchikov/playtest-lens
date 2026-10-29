# 13: Which open path to ship (Opus cross-review)

Reviewer: Claude Opus 5.5, Cursor, fresh. I did not build this. Read only, commit `3c5c920`, no API call, no Keychain. I did not watch the footage or open a clip, so nothing below says what is on screen. Every recommendation here is mine (Claude Opus 5.5), not Sasha's.

## The pick

**Keep Baseten as the open host and keep sending the player's words as text. Add video only if Baseten accepts it. Do not ship the Modal video run as it stands.**

"More context is better" holds, but on these three reports the context that mattered most was the voice, not the video. The Modal run had the real video and no voice: 0 of 22 moments have a quote, and the checker notes say "no verbal reaction" and "transcript is empty". It did worst on Sasha's own notes (table below). The Baseten run had only 8 frames, but it had the Voice Transcribe text, and it kept the hidden room, named the crash as Godot, and quoted him. Video helps with motion and timing. It does not replace hearing him.

**Why we "cannot" send video to Baseten:** that is not proven. Task 21 tried images (they work, at most 8 per request), `input_audio` (accepted but ignored), `audio_url` (ignored) and `file` (400). It never tried `video_url`. The product has never sent Baseten a video file. A `video_url` probe may be running now. Its result is not in the repo, so I don't know the outcome.

How to decide:
1. If Baseten accepts `video_url` and the model describes the 20 s lobby-door clip correctly: send video plus the transcript text on Baseten. The decided host stays.
2. If it does not: ship Baseten frames plus the transcript (the current open page), with the timing and duplicate fixes below.
3. Run Modal video **with** the transcript only if Sasha wants to know whether motion beats frames once both have his words. It is about $0.50 of his Modal balance. It changes the pick only if it wins on his notes and he moves the host.

## The host decision (Sasha's)

Sasha, 2026-10-28 (DECISIONS.md): "I think for Muse Open and open weight thing lets use Baseten and compete in the another prize category." Moving to Modal reverses that, so only he can do it.

| | Baseten (decided) | Modal |
|---|---|---|
| What it takes | Up to 8 images (measured). `video_url` untested | `video_url` with a base64 mp4 (measured) |
| Times | Frame labels. 18 of the 25 open Spark candidates are exact multiples of 15 s (the frame spacing on a 120 s window). They are kept as is: the lobby door at 30 s (36 s contributor, 37 s Modal), the hidden room at 210 s (HiddenDoor event at 207.7 s) | Times are not tied to a frame grid: 37, 204, 342 s |
| Money | Hackathon Baseten credits. The open run cost about $1.26 in `runs/costs.jsonl` | Sasha's own balance, not plan credits. About $0.50 a session |
| In the product | `analyzer/client.py`, cached and costed | **Not in the repo.** No `video_url` in any tracked file, no Modal line in `runs/costs.jsonl`, no cache entry after 00:05, a new source label `spark-open-video`. It ran outside the one client |
| Prize fit | The hackathon's sponsored key ("only works with this hackathon model") | Not checked whether the open-weights prize treats a Modal shared endpoint the same way |

If Modal were picked, it has to go into `client.py` as a host switch with cache and cost lines (a DeepSeek task), not stay a script.

## Sasha's notes against the three reports

The ground truth is his notes, as recorded in DECISIONS.md and the brief. This is a list of what each report did. It is not a score.

| His note | Contributor (video and voice) | Baseten (frames and transcript) | Modal (video, no transcript) |
|---|---|---|---|
| Lobby door is world-building, "not really stuck flag with medium sevirity" | Kept, stuck, 36 s | Kept, confused, 30 s | Kept, stuck, 37 s |
| CEO door "really wrong"; lockpick "without a real struggle" | Both kept as stuck (117, 125 s) | CEO door kept as stuck (114 s) | Both dropped (118, 124 s); 114 s kept as confused about the key behind the glass |
| Only Code Lock is a puzzle | `cogito-findings-25.json` names 24 different puzzles | Code Lock only | Code Lock only |
| "Archive" is his volume name for the break room | Break-room moments labeled Archive | Same | Same |
| Vent: missed, or called a wall panel; should come before camera and trap | 425 s "wall panel", surprised | Two cards for one moment: 420 s stuck and 422 s surprised, "duct door" | 413 s confused about a "trash can" and a "floor hatch"; the opening at 428 s dropped |
| Hidden room (he said "Oh my god there was a hidden room") | Kept, 212 s | Kept, 210 s | Dropped at 213 s: "no audible surprise" |
| Crash at the end | Kept twice, but says Unity | Kept twice, says Godot | Nothing in the last 32 s |

What video fixed: the CEO door and lockpick, where seeing a quick success beat a stuck-sounding "can't can't can't". What losing the voice broke: the hidden room, every quote, and probably the crash.

## Gaps that stay wrong even with video

1. **No voice on the Modal check.** The checker's transcript slot was empty. Whether the mp4 sent to Modal carried an audio track, and whether the model hears it, is not recorded. Fix: fill the same transcript slot the Baseten path already fills. This is pipeline, not host.
2. **A locked door with no puzzle behind it becomes "stuck".** All three runs do it. That's the prompt, not the input. Fix: one line in the check prompt for this case (a locked door with no puzzle volume, which the player leaves, is not stuck). How the page should explain why a door is locked is Sasha's call.
3. **One moment, two cards.** Baseten keeps 180 s twice (confused and surprised, same quote) and the vent twice. Fix: merge kept findings at the same time and place into one card.
4. **Frame-grid times on Baseten.** These fail the 1 s quality bar by design. Prompts can't fix this. Either video (the host or probe question) or let the check, whose 20 s clip has labeled frames 2.5 s apart, return a corrected time that replaces the candidate's.
5. **Vent wording.** Three models describe it three ways. I can't say which is right without the clip. Sasha's eye on that one card settles it.

## Fixes before the deadline that change the page

Prompt and pipeline (DeepSeek, `analyzer/`), in order:
1. The locked-door line in the check prompt (gap 2). Rerun from cache plus the changed check calls only.
2. Merge same-moment cards (gap 3).
3. If Baseten stays on frames: the check returns the time (gap 4). If video is chosen on either host: the transcript goes into both the candidate and the check prompt (gap 1). On Modal, it also has to move into `client.py` first.

Volumes (Sasha, on Windows, his decision): he already decided to rename "Archive" to the break room himself ("will do it myself after we done the full new round"). Add a puzzle volume only where he wants one, for example the CEO laptop, which he said "could be" a puzzle.

Already met on all three pages: the map opens on the whole route (slider at 8:32, "From start"), and heat is a separate view.

Not about the open model, from review 12: the `0:00` time-lost tile and the contributor's "Unity" cards are on every page.

## What I did not check

I didn't watch any clip or read the Modal script, which isn't in the repo. I didn't see the Baseten `video_url` probe result or check Modal's prize eligibility, and I ran nothing.

## After this review (orchestrator, Grok 4.7, 2026-10-29)

The probe Opus was waiting on finished before this file was read back. Baseten accepts `video_url`. The same 20 second lobby-door clip (4.1 MB, audio track included) returned stuck at 36 s on the locked door, confused at 41 s on the red button, and confused at 30 s while wandering. Finish reason stop, 3,416 input tokens, 1,595 output tokens. Every quote was null, same as the Modal video replies.

That meets Opus's rule 1 for the picture: the decided host can take the video. It does not show that the model hears the voice inside the file. The open path to try next is Baseten video plus the Voice Transcribe text, inside `analyzer/client.py`, with cache and cost lines. A full session that way has not been run.
