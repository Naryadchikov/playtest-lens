# Report page design notes (for the implementer)

Mockup: `report-mockup.html` (fictional data). Copy its CSS and markup. The page only renders `findings.json`; it computes nothing. Proposal by Claude Sonnet 5.5 (Claude Code in T3 Code); the look is Sasha's to judge.

## Layout since task 30 (2026-11-01)
Mockup B with parts of C (docs/tasks/30-report-build.md); built by Claude Opus 5.5 (Claude Code in T3 Code), the look is Sasha's to judge.
- `div.page`: the write-up column (`main.col`) scrolls; the map pane (`aside.pane`) is sticky on the right. Under 1100 px the pane stacks above the column and does not stick.
- Column, in order: header (session, recording, length, model, date), verdict, `section.problems` (from `summary.problems`), tiles and the kinds row, `section.strip`, across players, the moments, `section.dropped`.
- Strip: one row per room (`zones`, puzzle visits in the puzzle colour), one row per upper floor (`route.floor_spans`), the kept moments as rank markers stacked into up to 3 rows, the dropped candidates as hollow shapes, a time axis. Clicking or dragging on it sets the map time.
- Pane: toolbar (Timeline / Heat map, Play, Trail, readout), the slider, one `figure.floor` per map file side by side at its own aspect, and the moment box (`.box-whole` legend, `.box-heat` legend, `.box-now` current moment and game events).
- Moments: today's grouping (`_render_groups`), every section open as `section.moments-group > h3`, attempts as `h4`, cards as `article.card#m<rank>` with the clip beside the text from 900 px. Dropped: `article.drop#d-<id>` with today's reason line.
- Script: the card in the middle of the screen is current (its pin grows, its visit and clip spans are drawn strong over a faint route, its floor is outlined). Play runs the session at 10x. A playing clip holds the map on its moment and moves the dot to the last route point at or before `clip.start_s + currentTime`. Left and right arrows step between kept moments. A `#m<rank>` or `#d-<id>` link opens on that moment. Without script every moment, clip, floor and the whole route still show.

## Tokens (CSS custom properties, light then dark via prefers-color-scheme)
- Surfaces: `--bg #f5f6f8 / #0f131b`, `--surface #fff / #171c27`, `--sunk #eceef2 / #202636`, `--line #d6dae3 / #2c3344`.
- Ink: `--ink #151a24 / #e8ecf4`, `--ink2 #434b5c / #b0b8c8`, `--muted #596175 / #909ab0`.
- One accent: `--accent #2f45c7 / #8da2ff`, `--accent-tint #e6e9fb / #232b52`.
- Kinds (color AND shape AND text): stuck `#c2410c / #ff8a5c` square; confused `#946200 / #f2c14e` circle; surprised `#0f766e / #4fd1c5` diamond; bug (suspected_bug) `#a3195b / #ff7aa8` triangle. Tints `--t-*` are the badge backgrounds. Map pins always use the bright dark-mode colors (the map is dark).
- Spacing `--s1..s6` = 4, 8, 12, 16, 24, 40 px. Type `--fs-s .8125rem`, `-b .9375rem`, `-m 1.125rem`, `-l 1.5rem`, `-xl 2rem`. System fonts only.
- Not run: the dataviz palette validator (no node here). Check kind colors with `validate_palette.js` before release.

## Components (class names as in the mockup)
- `header` > `h1`, `ul.meta`, `p.verdict`. **Today:** session id, recording, duration. **New:** player label, level, date, verdict sentence.
- `.tiles` > `.tile` (`.n` number, `.l` label with `span.k.k-<kind>`); `.tile.wide` for time lost and kept/dropped. **Today:** kept/dropped, kind counts (count them from findings). **New:** time lost (sum `end_s - time_s` of stuck and confused kept findings; precompute as `summary.lost_s`).
- `ul.groups` > `li.group` > `h3`, `p` (`span.who`), `div.chips` > `a.chip.you` / `span.chip`. **New:** `cross_player` groups.
- `section#where` > `div.where` > `figure.map` (`img` + `svg viewBox="0 0 {px_width} {px_height}"`) and `aside.legend` (legend `ul` and `ol.pinlist`). Layers in order: heat, route, pins.
- `details.puzzle[open]` > `summary`, `div.puzzle-body` > `h4` (attempt) > `article.card.<kind>#m<rank>`. Card children: `.card-body`, then the clip. On screens 900 px and wider the clip sits to the right of the body (Claude Opus 5.5, 2026-10-31). Body children in order: `.card-head` (`a.num-pin`, `.time`, `.badge`, `.intent[.unplanned]`), `p.summary`, `blockquote/p.quote[.none]`, `dl.facts` (Game, Checker), `p.fric` (`.meter` of 3 `i`, level word, `.status.done|.open`), optional `p.f9line`. The clip (`.clip`, a `<video>` on the real page) is the body's next sibling, not inside it.
- Groups: area, then puzzle, then attempt, from `beat`. Cards sorted by `time_s`. Since task 30 every group is open (`section.moments-group`), so scrolling can light each moment.
- Dropped: since task 30, a visible `section.dropped`, one `article.drop` per dropped finding with `check.note` as the reason, and a hollow pin on the map.

## Map overlay
- Since task 30 each floor is its own map file (`route.maps`, ground first) drawn at its own aspect; route points, heat spots, pins and F9 markers go on the floor the file names. Mapping from `report/maps/<map>.json`: `px = (x - world_min_x)/(world_max_x - world_min_x) * px_width`, `py = (z - world_min_z)/(world_max_z - world_min_z) * px_height`. Draw in image pixel units (`viewBox` = `px_width px_height`), so the SVG scales with the `img`.
- Route: one `polyline` drawn twice (dark casing 16, light line 7), arrow triangles every 4th point rotated along the segment, start circle (white) and end circle (dark). Arrows, not a gradient, carry direction.
- Heat: one `circle` per hot spot, `radialGradient` fill (one hue, opacity falls to 0) plus a dashed ring and a label with time spent. Never color alone.
- Pins: `<a class="pin <kind>" id="pin-m<rank>" href="#m<rank>">` with `<use href="#sh-<kind>">` and the rank as text. Card number links back with `#pin-m<rank>`. Highlight uses `:target` only, no JavaScript. Pin position = finding `at`, else the route point nearest `time_s`.
- F9 pins: dashed hexagon, text "F9", link to the moment that contains the key press time.
- Keep pins at least about 55 image px apart (nudge overlaps in the analyzer, not the page).

## Data the page needs
Today's `findings.json` already has: session.id/recording/duration_s, per finding id, rank, time_s, end_s, kind, summary, quote, clip, game_state, check.verdict/note/friction/resolved/puzzle/area, beat.*. Rank and beat give the grouping and order.

Needs new fields (the analyzer computes, the page draws):
```json
"session": {"player": "Player 2", "level": "Lobby", "recorded": "2026-10-29"},
"summary": {"verdict": "plain sentence", "lost_s": 285},
"route": {"scene": "res://...", "maps": ["lobby", "lobby_upper"],
          "points": [[t, x, z, floor], ...],
          "heat": [{"x": 3.5, "z": -0.6, "r_m": 2.1, "seconds": 70, "floor": 0}],
          "floor_spans": [{"floor": 1, "start_s": 120.0, "end_s": 185.5}]},
"markers": [{"t": 115.0, "x": 2.4, "z": 0.5, "floor": 0, "moment": "f5"}],
"zones": [{"zone": "North room", "puzzle": "weighted plates", "start_s": 180.0, "end_s": 600.0}],
"events": [{"t": 101.0, "kind": "door", "label": "HALL/BadgeDoor opened"}],
"summary": {"problems": [{"place": "North room, weighted plates", "moments": ["f2", "f1"], "attempts": 2,
                          "lost_s": 130, "friction": "blocked", "resolved": "abandoned"}]},
"cross_player": [{"place": "North room, Puzzle 2: weighted plates", "kind": "stuck",
                  "players": [{"label": "Player 2", "moments": ["f1"], "worst_t": 345}], "of": 3}]
```
Per finding, new optional: `at: {"x": -4.0, "z": -12.1, "floor": 0}` (dropped findings too, since task 30), `check.resolved_after_s` (number or null, the mockup says "Resolved after 0:28" or "Unresolved"), no `check.intent`: the tag and the 3-step meter come from today's `check.friction` (`learning`, `stuck`, `blocked`; see docs/tasks/23-report-redesign.md). `check.resolved` exists today (boolean); the page needs the number to show the delay.
Page rules: a missing optional field hides its element, never a placeholder. No `route` means no map section. Format all seconds as m:ss; spans as `5:45-7:10` with a plain hyphen.

## Rules
No em dashes or spaced en dashes. Escape every string. Respect `prefers-color-scheme` and `prefers-reduced-motion`. The mockup's print styles are brief; keep them.

## Adapted from Anthropic's frontend-design skill (2026-10-28)
Sasha asked for it to be loaded and adapted. Proposal by Claude Opus 5.5 (Cursor); the tokens, kind shapes, system fonts and "never color alone" above stay. Taken from it: spend the boldness in one place (the map), show one thing at a time (timeline or heat map, never both), dim what is outside the selected span instead of hiding it, motion only to answer an action (a short opacity change), sentence case and plain action names ("Show all moments"). Not taken: a display typeface, a new palette, a hero.
