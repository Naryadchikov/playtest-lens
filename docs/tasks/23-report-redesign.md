# 23: Report page redesign (render only)

**Author:** DeepSeek V4.1 Flash 1017 on Modal, through `tools/run-modal-agent.sh deepseek` run inside its own worktree `.worktrees/ds-23` (branch `ds/23-report`).
**Briefed by:** the orchestrator, Claude Sonnet 5.5 in Claude Code in T3 Code, 2026-10-28.
**Reviewer:** Grok 4.7 xhigh through Cursor, fresh.
**Base commit:** the commit that adds this file.

## Why

The report page today is plain. Sasha (T3 Code chat, 2026-10-28): "you might load and give deepseek claude code design skill for making html reports prettier, or maybe even can spawn quick subagent with claude code sonnet on medium or high to do quick mocup as one time thing." and (same chat) "do the redesign and mocup and ask deepseek then to finish the work." Earlier (DECISIONS.md, editor rendering): "lets do simple version as you suggest first, then we can try and do more in depth later if we have time, yes" (the report-side SVG route and heat first). A Sonnet subagent made a one-time mockup with made-up data. The look is Sasha's to judge; build it as drawn, keep every label string in one place so he can change wording, and do not restyle on your own.

## Outcome

`report/render.py` renders a findings file as the page drawn in `docs/design/report-mockup.html`, using the design notes in `docs/design/DESIGN_NOTES.md`. Read both first. Copy the mockup's CSS and markup structure; replace the made-up content with the file's content.

## The rules that bind this page

- **The page only renders the file** (AGENTS.md, "The analyzer's rules"). It computes no finding, no time, no count and no ranking. Every number and sentence shown comes from `findings.json`. The two allowed transforms: formatting seconds as m:ss, and converting a route or pin world point (x, z) to image pixels with the map's own JSON (`report/maps/<map>.json`, the convention is written in it). The analyzer fills the new fields later (task 23b); until then they come from the test fixture.
- **A missing optional field hides its element.** Never a placeholder, never a guess. No `route` means no map section. No `at` on a finding means no pin for it (the card still shows). No `summary` means no verdict line and no tiles. No `cross_player` means no "Across players" section.
- Escape every string that comes from the file. No JavaScript at all (the mockup needs none; `:target` does the highlighting). No network fetch, no web font.
- Output stays one self-contained HTML file, except clips: `<video controls src=...>` with the relative path from the file, as today. The map picture is embedded as a base64 data URI read from `report/maps/<map>.png` (about 46 KB for the Lobby). If the map file is missing, render the page without the map section and print one warning line to stderr.
- No em dashes or spaced en dashes in any file you write or any text the page shows. Spans are written `5:45-7:10` with a plain hyphen.

## Format changes (`analyzer/findings.py`, format stays `1`, all new fields optional)

Accept and type-check these, and fail with a clear `ValueError` naming the field when the type is wrong. A file without them stays valid.

```
session.player (string), session.level (string), session.recorded (string)
summary: {verdict: string, lost_s: number, counts: {stuck, confused, surprised, suspected_bug: int},
          kept: int, dropped: int}
route: {scene: string, map: string, points: [[t, x, z], ...],
        heat: [{x, z, r_m, seconds}, ...]}
markers: [{t, x, z, moment: finding id or null}]        # F9 presses
cross_player: [{place: string, kind: string, of: int,
                players: [{label: string, moments: [finding ids], worst_t: number, here: bool}]}]
finding.at: {x, z}
finding.check.resolved_after_s: number or null
```

There is no new `intent` field. Today's `check.friction` (values `learning`, `stuck`, `blocked`, written by the checker) drives the meter and the tag, and `check.resolved` (`solved`, `abandoned`, `unknown`) drives the status. One small table in `render.py` holds all label strings: friction `learning` is meter 1 with the tag "planned challenge?", `stuck` is meter 2 and `blocked` is meter 3, both with the tag "unplanned". Status: `solved` shows "Resolved after m:ss" when `resolved_after_s` is a number, else "Resolved"; `abandoned` shows "Abandoned"; `unknown` shows no status. An unexpected value shows its text and no meter. This page change must not alter the checker or its prompt.

Pin ids and links: a finding's pin is `pin-m<rank>`, its card `m<rank>`, as in the mockup. Pin numbers are the finding's `rank`. A marker links to `#m<rank of its moment>` when `moment` names a kept finding, otherwise it has no link. The "Where it happened" list beside the map lists kept findings that have an `at`, in rank order.

Pin overlap: the page does not move pins (the analyzer will nudge them). Do not add collision code.

## Files you own

`report/render.py` (rewrite as needed), `report/__init__.py`, `analyzer/findings.py` (only the optional-field checks above), `tests/test_report.py`, `tests/test_findings.py`, a new fixture `tests/fixtures/findings_redesign.json`. Touch nothing else. Do not commit; do not edit `docs/design/`.

The new fixture is fictional and follows the mockup's story (the Lobby, 9 kept and 3 dropped moments, three attempts at the plates puzzle, a route of about 40 points, heat spots, F9 markers, a cross-player block). You may reuse the mockup's invented text. It must validate with `analyzer.findings.load`. Keep `tests/fixtures/findings_sample.json` and `findings_sample_b.json` valid and rendering (they lack the new fields: that is the "missing field" test).

## Checks that prove it

1. `.venv/bin/python -m pytest -q` passes, with no API call (the suite already runs offline).
2. Tests that matter (focused, no slop): every kept finding's summary, quote and time appears in the page; the page's order and grouping follow `rank` and `beat`; a missing optional field hides its element (render the old fixtures and check there is no map, no tiles, no "Across players"); every string is escaped (a fixture value with `<script>` renders as text); route and pin pixels equal the mapping from the map JSON for two known points; the three `check.friction` and three `check.resolved` mappings; invalid new fields raise a `ValueError` naming the field.
3. Render the new fixture to `runs/redesign/page.html` and report its size. Open it in a browser with a throwaway profile only if one is available to you; otherwise say you could not. Do not use the default browser profile.
4. A grep of your diff finds no em dash, no spaced en dash, no key or path of this machine.

## Done means

The tests pass; the page for the fixture contains the same sections as the mockup in the same order; the old fixtures still render. Report in at most 20 lines: files changed, commands run with exit codes, the output path and size, what you did not check, and anything in the notes or the mockup that you found inconsistent (say so, do not silently change it).

## After

The orchestrator reads the diff, commits it with the author trailer, and starts a Grok review. Task 23b (not this task): the analyzer computes the new fields from the session log (route points, heat spots, `at`, markers, `summary`, `cross_player`) and the checker adds `resolved_after_s`; that touches the checker prompt and goes through the change-analyzer skill, so Sasha is asked first.

## What came back

DeepSeek rebuilt `report/render.py` (about 1000 lines, labels in one `LABELS` table) and added the optional-field checks to `analyzer/findings.py`, a fictional fixture `tests/fixtures/findings_redesign.json` and tests (141 passed). Six places where the notes and the brief disagreed were reported and the brief won. Grok review round 1: NOT PASS, 3 blocking (an unescaped `session.id`, a stored time of 0 treated as missing, cards sorted by time instead of rank). The orchestrator fixed them (about 25 lines plus tests) and round 2 passed (docs/reviews/08-report-redesign-grok-round2.md). Merged as e33c046. Not checked by anyone: the page in a browser (no screenshot yet), dark mode, print. The fixture page renders to `runs/redesign/page.html`.
