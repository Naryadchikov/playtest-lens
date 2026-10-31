# 31: The logging add-on as a real Godot plugin

Author of this brief: Claude Opus 5.5 (orchestrator, Claude Code in T3 Code), 2026-10-31. Implementer: a Claude Opus 5.5 subagent. Reviewer: a fresh Grok 4.7 xhigh. Base: the fork `game/` on branch `playtest-lens` at `1bd0281`.

Follow `.claude/skills/godot-addon-change/SKILL.md`.

## Why

Sasha, T3 Code chat, 2026-10-31: "overall I agree about godot open source addon bit". The proposal he agreed to: turn `addons/playtest_lens` into a real Godot plugin, with `plugin.cfg`, a README, a 5-minute install guide and a small adapter example for a game that is not COGITO. Today the folder has no README and no `plugin.cfg`, and it is wired by hand through two autoload lines in `project.godot`, so no other Godot developer could pick it up.

## The outcome

A developer with their own Godot 4.7 game copies `addons/playtest_lens/` into it, enables the plugin, sets the player path, and gets the same log this project's analyzer reads.

- `addons/playtest_lens/plugin.cfg` and a small `EditorPlugin` script that adds the logger autoload when the plugin is enabled and removes it when disabled (the standard `add_autoload_singleton` pattern). The game itself must still run with the add-on passive: it listens and writes, never changes gameplay, timing or input.
- `addons/playtest_lens/README.md`: the problem in one line, then what it logs (one example line per event type, matching the schema the analyzer reads: in the main repo, `docs/LOG_SCHEMA.md`; link it as `https://github.com/Naryadchikov/playtest-lens/blob/main/docs/LOG_SCHEMA.md`), install in five steps, the player path setting, telemetry volumes (designer zones with an optional puzzle line), the start flash and beep that line up video and log, the F9 marker, where logs are written on Windows and Mac (`docs/TESTER_GUIDE.md` in the main repo has the paths), privacy (nothing that names a person or a machine), and how to send your own game events from your code. English, plain, no em dashes and no spaced en dashes.
- A small, generic adapter example in the README (or a short example script in the add-on folder): how a game that is not COGITO reports a door, a pickup or a quest step through the logger's existing API. If the logger has no public call for that yet, add the smallest one that the COGITO adapter (`addons/playtest_lens_cogito/adapter.gd`) can also use, so there is one path.
- `addons/playtest_lens/LICENSE`: MIT, "Copyright (c) 2026 Aleksandr Nariadchikov" (his name for copyright, DECISIONS.md 2026-10-28).
- Keep the fork's existing autoload lines working. Do not commit `project.godot`: it has an uncommitted change that is not yours (a `[playtest_lens] player_path` section); leave it as it is, and say in your report whether the add-on needs that setting and what its default is.

## Done means

- The add-on's headless tests pass with `/Applications/Godot.app/Contents/MacOS/Godot` (the standard 4.7.2 build only, never `Godot_mono.app`); the skill names the commands. Paste the command lines and their exit codes.
- The plugin enables and disables without errors in a headless editor run, if that can be shown headless; otherwise say so.
- No COGITO script changes. No gameplay change.

## Rules

- Files you may change: `game/addons/playtest_lens/**` and, only for the one-path API above, `game/addons/playtest_lens_cogito/adapter.gd`. Nothing in the main repo: another author is changing `analyzer/`, `report/` and `tests/` right now.
- Do not call any t3-code tools. Never run rm. Do not commit. No network, no model calls, no Keychain.
- Never copy anything from `recordings/` or `runs/`.

## Report (short)

Files changed; the test commands and exit codes; what you did not check; whether `project.godot` needs anything from the developer.
