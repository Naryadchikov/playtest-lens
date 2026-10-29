# 15: Where things stand (Opus overview)

Claude Opus 5.5, Cursor. Read only, 2026-10-29. No API call, no footage watched. Every recommendation here is mine (Claude Opus 5.5), not your decision.

## Where things stand

The product works end to end, in two modes, on one session. It is not a submission yet: the repo is private, the README has no run steps, there is no video and no second player. The deadline is Wed Nov 4, 9:00 PM Eastern (3:00 AM Stockholm). The plan freezes Tue Nov 3.

## Normal mode

Muse Spark contributor gets the video and your voice. On the 8:32 COGITO lobby session it kept about 20 moments and dropped 11, with clips, quotes, a map and heat (`runs/check/cogito-report-26.html`). It is the page to show, after four fixes: the first screen says 0:00 time lost, two crash cards call the game Unity, one search is split over many cards, and seven cards say "planned challenge?".

## Open-weights mode

In the product today: Muse Spark Open on Baseten sees up to 8 frames plus the Voice Transcribe text. 18 kept of 36, a quote on every keep, but times often sit on a 15 second grid. Safe to show now (`runs/check/cogito-report-open.html`).

Best experiment: Baseten with the video plus a separate wav (the sound inside the mp4 is ignored). 16 kept of 27, about $0.57. It matches your notes best: no false stuck at the lobby door, CEO door or lockpick, hidden room at 207s, vent once, crash caught. But only 5 of 16 keeps have a quote, and it runs outside the one client. Modal video without a transcript: drop it.

Your open choice: wav alone (nothing billed to the Meta pool) or wav plus Voice Transcribe text (surer quotes). My recommendation: wav alone if the quote fix brings quotes back, otherwise add the text.

## Fix before we submit

Agent work (my recommendations):
1. Hide the time-lost tile, or fill `end_s`.
2. Tell the check the game is Godot; rerun the crash cards.
3. Merge cards on the same moment, keeping any quote.
4. Replace "planned challenge?" with a word you pick.
5. Move video plus wav into `analyzer/client.py` with cache and cost lines, fix the quote prompt, rerun once. If it slips, ship frames plus transcript.
6. README: run steps, both modes, the video link, drop Muse Wonder.
7. The public checklist on the final commit.

Only you:
- Finish the volumes and push `playtest-lens`.
- A second player, and your blind notes on that session.
- Look at two cards: the Cutscene Trigger label at 1:53, and the hidden-room sculpture called a lion head.
- Record the 3-minute video.
- Make the repo public, last.

## What you should do

On Windows:
1. Finish the volumes, push `playtest-lens`, copy the video and log to the Mac.
2. Send a second player the build today or tomorrow. This is the biggest gap. Ask whether they mind that Meta may train on the recording.

Back on the Mac:
3. Answer two questions: wav alone or wav plus text, and the word for "planned challenge?".
4. Watch the two cards (1:53, hidden room).
5. Write blind notes on the second session, then run it and score it.
6. Freeze Tue Nov 3. Record from the page: one stuck moment, one drop, the map, then the open page.
7. Public checklist, flip to public, submit Wed Nov 4 well before evening.

Ignore until after the deadline: an upper-floor map, shorter quotes, a one-command run, the trail nits, an agentic-prize angle, moving the open host to Modal.
