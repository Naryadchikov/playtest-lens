# 05: Check the demo assets' licenses

**Author:** Grok 4.7 (xhigh, fast) through Cursor, T3 Code subagent, in the main checkout (it edits one doc and reads `game/`).
**Briefed by:** the orchestrator, Claude Opus 5.5 in Claude Code in T3 Code, 2026-10-26.
**Base commit:** given in the prompt that starts the task.

## Goal

One outcome: every item in `docs/PRIOR_WORK.md`, "Demo assets to check", has its license from a source you can link, or stays "unknown", and a short list names what Sasha must decide on.

Sasha (T3 Code chat, 2026-10-26): "Yes, the read-only Grok task. Kenney's site says all its assets are CC0, so link that page for the Kenney items. Whatever is still unknown after the credits page, or has a non-commercial license, gets replaced with a CC0 asset or cut before Friday's build. Show me that list before anything is cut or replaced."

## Sources

- COGITO's credits page: https://codeberg.org/Phazorknight/Cogito/wiki/Credits%2C-Contributors%2C-License (the raw text: https://codeberg.org/Phazorknight/Cogito/wiki/raw/Credits%2C-Contributors%2C-License). Read it word for word.
- Kenney: https://kenney.nl/support says "Yes, all game assets on the asset pages are public domain licensed (CC0)." Link that page for every Kenney item.
- A freesound or Pixabay page named on the credits page, when the credits page doesn't state the license. Open it and quote its license.

## Files you own

- `docs/PRIOR_WORK.md`, only its "Demo assets to check" section.

Touch nothing in `game/` (task 03 is changing it at the same time) and nothing else. Don't commit.

## What to do

1. For each item in the section: the license and the link it comes from. Keep the facts-only style. Where a source states an author or a credit line, add it.
2. Add a list at the end of the section, "To decide (Sasha)": every asset whose license is still unknown, non-commercial (any NC), or no-derivatives (ND), with its path, what uses it (grep `game/` for the file name in `.tscn`, `.tres`, `.gd` files), and why it's listed. Cut or replace nothing.
3. Note separately the assets that need a credit line (CC BY and similar), with the line the license asks for.

## Done means

- No item in the section says "unknown" where the credits page or a linked page answers it.
- The "To decide (Sasha)" list, each with what uses it.

## Report back

The file changed, the pages you read, the "To decide" list in short form, and what you didn't check. No file dumps.

## Rules

- Do not call any t3-code tools. Never run rm. Never use `--yolo` or turn off approvals or the sandbox.
- Read-only on everything but the one section. Download nothing into the repo.
- No em dashes or spaced en dashes in anything you write.

## What came back

(The orchestrator fills this in after the task.)

## What the orchestrator changed

(The orchestrator fills this in after the task.)
