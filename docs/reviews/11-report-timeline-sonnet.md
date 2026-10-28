Reviewer: Claude Sonnet 5.5 high, Cursor. Reviewed: uncommitted work by Claude Opus 5.5 medium (`report/render.py`, `tests/test_report.py`, `docs/design/DESIGN_NOTES.md`, "What came back" in `docs/tasks/25-report-plan.md`), 2026-10-28.

NOT PASS, 1 blocking finding.

## What I ran

- `.venv/bin/python -m pytest -q tests/test_report.py`: 32 passed.
- `.venv/bin/python -m pytest -q` (full suite): 180 passed, 2 failed. `tests/test_spatial.py::test_enriched_file_loads_and_renders` fails because of this diff (finding 1). `tests/test_transcribe.py::test_extract_audio_from_say_clip` fails on `assert (None is not None)` in audio extraction; it touches nothing in this diff and I did not find its cause (likely the machine or sandbox), so I do not count it.
- Re-rendered `runs/check/cogito-findings-25.json` to a temp file: exit 0, byte-identical to `runs/check/cogito-report-26.html`.
- Static check of the page and script: no `innerHTML`, `eval(`, `javascript:`, `fetch(` or `XMLHttpRequest`; no network URL in the page. One inline script.
- Browser: Cursor's browser tab on a local static server (`runs/check` on 127.0.0.1), state read through `Runtime.evaluate`, screenshots taken. The static server (python http.server, port 8765, started by me) has stopped.
  - Open: slider 512 (end), "From start", all 18 pins lit, route 464 points, no card dimmed, span note hidden, heat group `display: none`.
  - 15 s trail at 430 s: readout "6:55-7:10 of 8:32"; only `pin-m17` (7:05) lit on the map; the pin list dims every row but 17; only card `m17` undimmed; the route is cut to 14 points; note reads "Moments in 6:55-7:10 are lit. The rest are dimmed."
  - Heat map: route group, pins, time controls, trail legend and span note all `display: none` (0 trail elements with a size); the heat group shows 3 spots labeled 2:12, 0:25, 0:15 (the same as `route.heat` in the file), the plan is grey, the legend has a Less to More bar. No card is dimmed.
  - Back to Timeline: the same 15 s view returned, controls back. 60 s at 125 s: pins 2, 3, 4, 5 lit (times in (65, 125]), same four cards lit. "Show all moments": slider 512, trail "From start", 18 pins, 0 dimmed cards, note hidden.
- Not checked: Play in a window, the light theme, print, keyboard use, a narrow screen, a browser without `:has`, a file with F9 markers in the browser (the test covers the markup only).

## Blocking findings

1. `tests/test_spatial.py:311`: `assert 'fill="url(#heat)"' in page` is a stale assertion. This diff renamed the gradient to `heat-blob` (and now draws the heat through `heat-ramp`), so the test fails: `pytest -q tests/test_spatial.py::test_enriched_file_loads_and_renders`. The "What came back" entry says the full suite was not run, which is how it slipped through. The fix is one line (assert `fill="url(#heat-blob)"` or `class="heat"`), but offline tests must pass before the change counts as done (AGENTS.md quality bar).

## Nits

1. `report/render.py` `_render_route`: the start circle and "start" label have no `data-t`, so in a 10, 15, 30 or 60 s window the start point (far from the player) stays on the map. It is the one element left that is not in (T - Y, T]. Seen in the 15 s screenshot (start circle at the top while the dot is at the bottom). Sasha's rule is "only what is relevant at a time"; hide it when a window is selected, or call it deliberate.
2. `docs/design/DESIGN_NOTES.md` and the task note say outside-span things are "dimmed, not hidden". That holds for cards and pin-list rows. On the map the pins, arrows, F9 markers and route points outside the window are hidden (`.later { display: none }`), not dim. The behavior matches Sasha's map rule; the wording is off, and the brief's "pins outside that window are dim" is only true for the list.
3. `report/render.py` `_render_heat`: blob opacity is `0.35 + 0.65 * seconds / top`, a visual scale worked out at render time from the file's `seconds`. It is not a finding, time, position or count, and the label on each spot is the file's value, so it fits the rule. Worth one line in the docstring so the next reader does not mistake it for derived data.
4. `report/render.py` CSS: the whole view switch depends on `:has`. In a browser without it the Heat map radio does nothing and the checked segment has no highlight. The author listed this as unchecked. Acceptable for the demo browsers; a line in `docs/FOLLOWUPS.md` would do.
5. `tests/test_report.py` `test_trail_offers_from_start_and_the_window_lengths`: `assert "t - span" in script` matches a source string, so it passes for any script containing that text. The window math is only proved by my browser run, not by a test. A JavaScriptCore stub run (as in `runs/check/25-stub.js`) would pin the (T - Y, T] rule.
6. Heat map view still shows the full moments list with no pin numbers on the map to match. That follows Sasha's "no numbered pins"; only noting that the cards are not tied to the heat view at all.

## Orchestrator

The blocking assertion is updated to `fill="url(#heat-blob)"`. `pytest -q tests/test_spatial.py::test_enriched_file_loads_and_renders tests/test_open_backend.py` passed (11). The nits are left.
