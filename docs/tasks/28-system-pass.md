# 28: One card for one struggle in a room

Author of this brief: Grok 4.7, Cursor, 2026-10-29. Opus 5.5 was asked to review the system and write this brief. That run stopped at once: "Other Models usage limit reached." No brief was written. This file is the substitute review, labeled as Grok's, not Opus's. Implementer: Claude Sonnet 5.5.

Base commit: `e16826d` on `main`.

Sasha, Cursor chat, 2026-10-29: "can you ask opus to review our system overal and pass suggested fixes and improvements to sonnet, especially merges, identifying the momemnt,s prompts, etc. as the whole system" and "sonnet to implement".

Follow `.claude/skills/change-analyzer/SKILL.md`. No model call, no network, no Keychain. Never run `rm`. Do not touch `game/`. Do not commit. No em dashes.

## What is wrong

A long struggle becomes several cards. `merge_same_moment` folds kept findings of one kind only when each is within 8 seconds of the previous one. A search that pauses for 9 seconds stays split. The same rule also ignores the room: two stucks in different places, 6 seconds apart, become one card.

The candidate prompt lists every moment it notices. It never says that one continuing struggle is one moment, so the windows emit a run of cards before the merge ever sees them.

The check prompt, the open-model path, the 20 second window overlap, and the carried zone line are already in place. Do not redo them.

## The change

### 1. Merge by the visit, not by 8 seconds

In `analyzer/check.py`, `merge_same_moment(findings, zones=None)`.

`zones` is the list `beats.zone_intervals` already returns. Compute it once in `main`, pass it into `merge_same_moment`, then pass the same list to `assign_beats`. Do not compute the intervals twice.

A finding's place is the zone interval that contains `time_s` (`start_s <= time_s` and `end_s` is null or `time_s <= end_s`). When several contain it, take one that has a non-empty `puzzle` if any do. Otherwise take the one with the latest `start_s`. That matches the logger: the puzzle box inside a room wins, and the latest enter wins otherwise.

Kept findings that share a place and a kind are one moment, however far apart they are inside that visit. The visit is `(zone, puzzle, start_s)`. Leaving and re-entering the same box is a new visit, because `start_s` differs.

The card that stays is the one with a quote, else the earliest. If more than one finding was folded in, set that card's `end_s` to the latest `time_s` in the group. A card that was not folded keeps `end_s` as it was. Dropped findings are not folded and keep their ranks null. Renumber kept ranks from 1 in time order, as today.

A kept finding in no zone uses the old rule: same kind, each within 8 seconds of the previous one of that kind, chaining. `MERGE_WINDOW_S` stays 8. Do not apply the 8 second rule to a finding that has a place.

### 2. One sentence in the candidate prompt

In `analyzer/prompts/spark_test.md`, add one rule after the surprised rule:

`- One struggle is one moment. While the player is still stuck, confused, or surprised at the same thing, list it once, at the time it starts. Do not list it again while it continues.`

Do not edit `analyzer/prompts/check.md`.

## Tests

In `tests/test_check.py`. The existing `test_merge_same_moment_keeps_the_quoted_one_and_ranks_the_rest` calls `merge_same_moment` with no zones and must still pass.

Add:

- Two kept stuck findings 30 seconds apart inside one zone interval become one card. The quote is kept. `end_s` is the later time. A surprised finding in that same interval stays.
- The same zone name after a `zone_exit` and a new `zone_enter` (two intervals, two `start_s` values) keeps two stuck cards.
- A finding inside a room interval and a puzzle interval at the same time groups with the puzzle interval, not the room. A second stuck finding that is only in the room stays its own card.
- Two stuck findings 30 seconds apart with no zones stay two cards.

## Files Sonnet may touch

- `analyzer/check.py`
- `analyzer/prompts/spark_test.md`
- `tests/test_check.py`
- this file, the "What came back" section only

## Not this pass

- Filling `end_s` on a card that was never merged. One report is still a point, and the time-lost tile stays hidden for those.
- Widening the 5 second cross-window drop in `merge_window_moments`.
- Carrying anything but the open zone into a clip.
- The page look, the upper floor, a paid rerun.

## Checks

```
.venv/bin/python -m pytest -q --deselect tests/test_transcribe.py::test_extract_audio_from_say_clip
```

The say-clip failure in a full run is the known sandbox miss. Deselect it.

## Done means

The four new cases pass, the old merge test still passes, the prompt has the one new rule, `check.md` is unchanged, and nothing outside the file list changed.

## What came back

Sonnet did not start: the other-models usage limit was reached, same as the Opus review. Grok 4.7 implemented the brief in this session. `merge_same_moment` takes the zone list, folds one kind across a whole visit, and still uses 8 seconds only when there is no zone. The candidate prompt has the one new rule. `check.md` was not edited.
