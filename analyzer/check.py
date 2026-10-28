"""Check each candidate moment on its own 20-second clip.

One path (PLAN.md): candidates from the windowed Spark pass, then this
check, then findings.json. The checker never sees the picker's chain of
thought, only the candidate line, the clip, its transcript and the log
slice. It answers keep or drop with evidence. Dropped moments stay in
the file, listed, not hidden.

Run as: tools/run-analyzer.sh analyzer/check.py <recording> <candidates.json>
    [--model muse-wonder-1.0] [--out <findings.json>] [--log <session.jsonl>]
    [--video-flash-s S] [--limit N]
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analyzer import client as client_module  # noqa: E402
from analyzer import findings as findings_module  # noqa: E402
from analyzer import log_candidates  # noqa: E402
from tools.video import cut_clip, extract_audio  # noqa: E402

PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "check.md"
CLIP_SECONDS = 20.0


# Parse and validate the checker's JSON reply. Raises ValueError.
def parse_check(text: str):
    if not text or not text.strip():
        raise ValueError("Checker reply was empty: no JSON found.")
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    try:
        data = json.loads(cleaned)
    except ValueError as exc:
        raise ValueError(f"Checker reply is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("Checker reply JSON must be an object.")
    if data.get("verdict") not in ("keep", "drop"):
        raise ValueError(f"Checker reply has an invalid verdict: {data.get('verdict')!r}.")
    if not isinstance(data.get("note"), str) or not data["note"].strip():
        raise ValueError("Checker reply has no note.")
    if not isinstance(data.get("summary"), str) or not data["summary"].strip():
        raise ValueError("Checker reply has no summary.")
    if "quote" not in data or not (data["quote"] is None or isinstance(data["quote"], str)):
        raise ValueError("Checker reply has an invalid quote.")
    if "game_state" not in data or not (
        data["game_state"] is None or isinstance(data["game_state"], str)
    ):
        raise ValueError("Checker reply has an invalid game_state.")
    return data


# Fill the check prompt for one candidate.
def build_prompt(template: str, candidate, transcript: str, log_slice: str) -> str:
    return template.format(
        time_s=candidate["time_s"],
        kind=candidate["kind"],
        reason=candidate["reason"],
        quote=candidate.get("quote") or "null",
        transcript=transcript.strip() or "(nothing transcribed)",
        log_slice=log_slice.strip() or "(no event log for this session)",
    )


# Clip path as stored in findings.json: relative to the findings
# file, so the report page next to it finds the clip.
def store_clip_path(clip_path, findings_path) -> str:
    clip_path = Path(clip_path)
    try:
        return clip_path.relative_to(Path(findings_path).parent).as_posix()
    except ValueError:
        return clip_path.name


# Round a time for the findings file without passing the duration.
def clamp_time(value, duration_s):
    rounded = round(float(value), 2)
    if duration_s:
        return min(rounded, float(duration_s))
    return rounded


LOG_KIND_TO_FINDING_KIND = {
    "death": "stuck",
    "retry": "stuck",
    "idle": "stuck",
    "backtrack": "stuck",
    "looking_around": "confused",
}


# Spark candidates plus event-log candidates, by time. A log candidate
# within 5 s of a Spark candidate is dropped: the video moment already
# covers it, and the checker sees the log slice either way.
def merge_candidates(spark_candidates, log_cands):
    merged = [dict(candidate, _source="spark") for candidate in spark_candidates]
    spark_times = [float(candidate["time_s"]) for candidate in spark_candidates]
    for candidate in log_cands:
        if any(abs(float(candidate["time_s"]) - spark_t) <= 5.0 for spark_t in spark_times):
            continue
        merged.append(
            {
                "time_s": candidate["time_s"],
                "kind": LOG_KIND_TO_FINDING_KIND[candidate["kind"]],
                "reason": candidate["detail"],
                "quote": None,
                "_source": "event_log",
            }
        )
    return sorted(merged, key=lambda item: float(item["time_s"]))


# Event-log lines whose video time falls in [start_s, end_s], as text.
def log_slice_text(events, video_flash_s, start_s, end_s) -> str:
    if not events or video_flash_s is None:
        return ""
    first_flash = next((e for e in events if e.get("event") == "sync_flash"), None)
    if first_flash is None:
        return ""
    offset = video_flash_s - float(first_flash["t"])
    lines = []
    for event in events:
        video_t = float(event["t"]) + offset
        if start_s <= video_t <= end_s:
            lines.append(f"[video {video_t:.1f}s] " + json.dumps(event, sort_keys=True))
    return "\n".join(lines)


# A quote counts only when it appears in the transcript (the player's
# actual words from Voice Transcribe), never as the checker's invention.
def verified_quote(quote, transcript):
    if not quote:
        return None
    normal = " ".join(transcript.split()).lower()
    wanted = " ".join(quote.split()).lower().strip(" .")
    if wanted and wanted in normal:
        return quote
    return None


# Check every candidate. The callables are injected so tests run
# offline: clip_for(candidate) -> (clip_path, start_s, end_s),
# transcript_for(clip_path) -> str, call_for(clip_path, prompt) -> reply dict,
# slice_for(candidate, clip_start, clip_end) -> log text for the clip span.
def run_checks(candidates, *, model, clip_for, transcript_for, call_for, template, slice_for=None, duration_s=None):
    findings = []
    kept = 0
    for index, candidate in enumerate(candidates, start=1):
        clip_path, clip_start, clip_end = clip_for(candidate)
        transcript = transcript_for(clip_path)
        log_slice = slice_for(candidate, clip_start, clip_end) if slice_for else ""
        prompt = build_prompt(template, candidate, transcript, log_slice)
        reply = call_for(clip_path, prompt)
        verdict = parse_check(client_module.extract_text(reply))
        if verdict["verdict"] == "keep":
            kept += 1
            rank = kept
        else:
            rank = None
        findings.append(
            {
                "id": f"f{index}",
                "rank": rank,
                "time_s": clamp_time(candidate["time_s"], duration_s),
                "end_s": None,
                "kind": candidate["kind"],
                "summary": verdict["summary"],
                "quote": verified_quote(verdict["quote"], transcript),
                "clip": {"path": str(clip_path), "start_s": clip_start, "end_s": clip_end},
                "game_state": verdict["game_state"],
                "sources": [candidate.get("_source", "spark")],
                "check": {"verdict": verdict["verdict"], "note": verdict["note"], "model": model},
            }
        )
    return findings


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Check each Spark candidate on its own 20-second clip and write findings.json."
    )
    parser.add_argument("recording", help="Path to the playtest recording")
    parser.add_argument("candidates", help="Candidates JSON written by spark_test.py (windowed)")
    parser.add_argument("--model", default="muse-wonder-1.0", help="Checker model id")
    parser.add_argument("--out", default=None, help="Findings path (default runs/check/<recording stem>-findings.json)")
    parser.add_argument("--log", default=None, help="Optional session event log (JSONL)")
    parser.add_argument("--video-flash-s", type=float, default=None, help="Video time of the first sync_flash, when --log is given")
    parser.add_argument("--limit", type=int, default=None, help="Check only the first N candidates")
    parser.add_argument("--include-log-candidates", action="store_true", help="Also check event-log candidates (needs --log and --video-flash-s)")
    args = parser.parse_args(argv)

    client_module.require_api_key()

    recording = Path(args.recording)
    if not recording.exists():
        print(f"Recording not found: {recording}", file=sys.stderr)
        return 1
    candidates_data = json.loads(Path(args.candidates).read_text(encoding="utf-8"))
    candidates = candidates_data["moments"]
    if args.include_log_candidates and not args.log:
        print("--include-log-candidates needs --log and --video-flash-s.", file=sys.stderr)
        return 1
    duration_s = float(candidates_data.get("duration_s") or 0.0)
    if duration_s <= 0:
        print("Candidates file has no duration_s, so findings times cannot be checked.", file=sys.stderr)
        return 1

    events = log_candidates.load_log(args.log) if args.log else []
    if args.log:
        if args.video_flash_s is None:
            print("--log needs --video-flash-s: the video time of the first sync_flash.", file=sys.stderr)
            return 1
        if not any(e.get("event") == "sync_flash" for e in events):
            print("The log has no sync_flash line, so log times cannot map to video time.", file=sys.stderr)
            return 1
        if duration_s and not 0 <= args.video_flash_s <= duration_s:
            print("--video-flash-s is outside the recording.", file=sys.stderr)
            return 1

    if args.include_log_candidates:
        try:
            candidates = merge_candidates(
                candidates, log_candidates.find_candidates(events, args.video_flash_s)
            )
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 1
    if args.limit:
        candidates = candidates[: args.limit]

    template = PROMPT_PATH.read_text(encoding="utf-8")
    out_path = Path(args.out) if args.out else Path("runs/check") / f"{recording.stem}-findings.json"
    clips_dir = out_path.parent / f"{recording.stem}-clips"
    clips_dir.mkdir(parents=True, exist_ok=True)

    def clip_for(candidate):
        target = clips_dir / f"c{candidate['time_s']:08.2f}.mp4"
        start, end = cut_clip(recording, float(candidate["time_s"]), target, seconds=CLIP_SECONDS)
        return target, clamp_time(start, duration_s), clamp_time(end, duration_s)

    def slice_for(candidate, clip_start, clip_end):
        text = log_slice_text(events, args.video_flash_s, clip_start, clip_end)
        if events and not text:
            return "(event log provided; no log lines in this clip)"
        return text

    def transcript_for(clip_path):
        with tempfile.TemporaryDirectory(prefix="check-audio-") as tmp:
            wav = extract_audio(clip_path, Path(tmp) / "clip.wav")
            reply = client_module.transcribe(wav, purpose=f"check:{clip_path.name}")
        return reply.get("transcript") or ""

    def call_for(clip_path, prompt):
        return client_module.call_model(
            model=args.model, prompt=prompt, video_path=clip_path, purpose=f"check:{recording.name}"
        )

    findings = run_checks(
        candidates,
        model=args.model,
        clip_for=clip_for,
        transcript_for=transcript_for,
        call_for=call_for,
        template=template,
        slice_for=slice_for,
        duration_s=duration_s,
    )

    for finding in findings:
        if finding["clip"] is not None:
            finding["clip"]["path"] = store_clip_path(finding["clip"]["path"], out_path)

    data = {
        "format": 1,
        "session": {
            "id": recording.stem,
            "recording": recording.name,
            "duration_s": duration_s,
            "start_flash_s": args.video_flash_s,
        },
        "findings": findings,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    # Prove the file the report will read is in the one format.
    findings_module.load(out_path)
    kept = sum(1 for f in findings if f["check"]["verdict"] == "keep")
    print(f"Wrote {len(findings)} findings ({kept} kept, {len(findings) - kept} dropped) to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
