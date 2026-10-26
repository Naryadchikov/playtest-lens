# Playtest Lens

Watching playtest recordings takes hours, so small teams skip it or skim it. Playtest Lens watches the recordings with Meta's models and finds where players got confused or stuck, checks each moment before reporting it, and combines what it found across players.

**Status:** being built for the Meta Global AI Developer Hackathon, from its kickoff on 2026-10-26 to 2026-11-04. How to run it comes here once it runs.

## Built with

- Meta Model API: Muse Spark, Voice Transcribe; Muse Spark Open for the open-weights mode.
- Test game: the COGITO demo by Phazorknight (MIT), as a submodule. See [docs/PRIOR_WORK.md](docs/PRIOR_WORK.md).
- Godot 4.7.2, Python 3.13, ffmpeg.
- Built with coding agents run from T3 Code: Muse Code (Meta) on Muse Wonder, Grok through Cursor, and Claude Code. Which agent built what is in [docs/tasks/](docs/tasks/).

## License

MIT. See [LICENSE](LICENSE).
