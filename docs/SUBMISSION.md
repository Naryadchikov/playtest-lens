# The submission form

The Cerebral Valley form, as Sasha shared it on 2026-11-02. The text below is a draft by Claude Opus 5.5 (Claude Code in T3 Code) for Sasha to rewrite; the words he submits are his.

## Before pressing Submit

- The repo must be public: "Public GitHub Repository" is required. Order on the day: the green light, both repos public and Pages on, a signed-out check, the X post, then the form.
- The Most Viral field takes the X post's link, so the post goes up first.
- The form has no field for the live demo or for the open-weights prize: the demo link is in the description, and Muse Spark Open on Baseten is in the two Meta fields and the partner feedback.
- The permission box grants Meta and Cerebral Valley the right to "use, publish, share, and promote the submitted materials". The video and the site carry the testers' voices; Sasha confirmed on 2026-11-03 that both testers agree their videos may be used.

## Fields

- **Team Name:** Sasha's pick.
- **Team Members:** Aleksandr Nariadchikov (solo).
- **Track:** Indie Developer Track. **Problem statement:** Build for Your World (PLAN.md).
- **Public GitHub Repository:** https://github.com/Naryadchikov/playtest-lens
- **3-Minute Demo Video:** the YouTube link.
- **The survey questions** (likelihood, opinion, obstacles, comparisons): Sasha's own answers.

## Project Description (draft)

Watching a playtest takes as long as the playtest, so small teams skip it, and the moment a player got lost is never seen by the person who built the room. Playtest Lens watches it for you. A small Godot add-on logs what the player does and lines the log up with the screen recording. Meta's Muse Spark watches the video and listens to the player thinking out loud. A second Spark pass checks every moment against its clip, the player's words and the event log. You get one page: where the player was confused, stuck or surprised, on the level's map, with the clip and their own words. On a held-out playtest nothing was tuned on, it found where the player was slowed and flagged a possible bug. Live demo: https://naryadchikov.github.io/playtest-lens-demo/

## Describe your use of Meta products (draft)

- Muse Spark 1.2 (contributor) through the Meta Model API. The recording goes in as 2-minute windows of video with sound, one request each, and Spark lists moments worth a look. A second Spark call per moment gets the 20-second clip, the transcript and that slice of the game's event log. It must keep or drop the moment with evidence: what happened, the friction, whether the player got past it, and the likely cause in the level.
- Muse Voice Transcribe writes down each clip's speech. A quote reaches the page only if the transcript holds it.
- Muse Spark Open (meta-models/muse-spark-open-1026) on Baseten runs the same pipeline as an open-weights mode.
- Muse Code helped build the first days.

## Why are Meta's models important to your solution? (draft)

A playtest is video and voice at once, and the voice is half the signal: what a stuck player says tells you why. Muse Spark 1.2 takes video with its sound in one request, so finding moments needs no frame sampling and no separate speech pipeline. At the contributor price, a 21-minute session costs about $0.18, cheap enough to run on every playtest. When an early open-weights run saw the video without the voice, it did worst against the developer's notes. Voice Transcribe gives an independent record of the words, so no quote is invented. Muse Spark Open lets a studio run the same analysis on open weights, which matters for unreleased game footage.

## Partner feedback (draft)

Baseten: Muse Spark Open ran through Baseten's OpenAI-compatible endpoint with no client changes. Two things cost us time. The audio inside a video_url is ignored, so we send the clip's audio as a separate input_audio wav, found by trial. Reasoning tokens count against max_tokens: on a 2-minute window even 4096 ran out before the answer, so we use 8192. A documented video-plus-audio example for this model would have saved the trial and error.
