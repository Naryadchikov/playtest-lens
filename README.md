# Playtest Lens

Watching playtest recordings takes hours, so small teams skip it or skim it. Playtest Lens watches the recordings with Meta's models and finds where players got confused or stuck, checks each moment before reporting it, and combines what it found across players.

**Status:** being built for the Meta Global AI Developer Hackathon, from its kickoff on 2026-10-26 to 2026-11-04.

## Run it

You need Python 3.13 with `requirements.txt` in `.venv`, and ffmpeg. The keys live in the macOS Keychain; the two scripts below read them for one process only.

Normal mode, Muse Spark contributor:

```
tools/run-analyzer.sh analyzer/spark_test.py <recording.mp4> --window-seconds 120
tools/run-analyzer.sh analyzer/check.py <recording.mp4> runs/spark_test/<stem>-window120s-muse-spark-1.2-contributor.json --log <session.jsonl> --video-flash-s <seconds> --out runs/check/<stem>-findings.json
.venv/bin/python -m report.render runs/check/<stem>-findings.json -o runs/check/<stem>-report.html
```

Open-weights mode, Muse Spark Open on Baseten (the video and the audio go to the open model; Voice Transcribe supplies the text that quotes are checked against):

```
tools/run-baseten.sh analyzer/spark_test.py <recording.mp4> --window-seconds 120 --model meta-models/muse-spark-open-1026
tools/run-baseten.sh analyzer/check.py <recording.mp4> runs/spark_test/<stem>-window120s-meta-models-muse-spark-open-1026.json --model meta-models/muse-spark-open-1026 --log <session.jsonl> --video-flash-s <seconds> --out runs/check/<stem>-findings-open.json
.venv/bin/python -m report.render runs/check/<stem>-findings-open.json -o runs/check/<stem>-report-open.html
```

`--video-flash-s` is the video time of the game's start flash: `.venv/bin/python -c "from tools.video import find_start_flash; print(find_start_flash('<recording.mp4>'))"`. The check writes the areas, the route, the heat and the summary from the log. To redo only the areas on an existing file: `.venv/bin/python -m analyzer.beats <findings.json> --log <session.jsonl> --video-flash-s <seconds> -o <new findings.json>`.

## Built with

- Meta Model API: Muse Spark, Voice Transcribe; Muse Spark Open for the open-weights mode.
- Test game: the COGITO demo by Phazorknight (MIT), from codeberg.org/Phazorknight/Cogito at 676be6d. It's the submodule at `game/`, from Sasha's copy, [cogito-playtest-lens](https://github.com/Naryadchikov/cogito-playtest-lens). See [docs/PRIOR_WORK.md](docs/PRIOR_WORK.md).
- Godot 4.7.2, Python 3.13, ffmpeg.
- Built with coding agents run from T3 Code: Muse Code (Meta), Grok through Cursor, and Claude Code. Which agent built what is in [docs/tasks/](docs/tasks/).

## License

MIT. See [LICENSE](LICENSE).
