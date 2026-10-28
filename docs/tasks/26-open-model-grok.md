# 26: Why Muse Spark Open returned no moments

Grok 4.7 through Cursor, 2026-10-28. Read only. No API call.

## What was measured

The command was `tools/run-baseten.sh analyzer/spark_test.py recordings/cogito/cogito.mp4 --model meta-models/muse-spark-open-1026 --window-seconds 120`. The file `runs/spark_test/cogito-window120s-meta-models-muse-spark-open-1026.json` has `moments: []`. The recording is 512.3 s, so the windows start at 0, 120, 240, 360 and 480 s. Five cached replies, one per window: `output_text` is `[]`, `finish_reason` is `stop`, input tokens are 3592 each, output tokens are 342, 347, 358, 423 and 983. Cost $0.033. Contributor Spark (`muse-spark-1.2-contributor`) on the same video and the same windows found 26 moments.

## Why the answer is []

Open sends eight JPEG frames and `analyzer/prompts/spark_test.md`. It sends no video file and no audio. Baseten allows 8 images, so a clip longer than 60 s is spaced at duration/8: about one frame every 15 s on a 120 s window, and no sound. The prompt tells the model it is watching the screen and hearing the player think aloud, to skip any moment it cannot time, and to reply `[]` when there are none. Eight silent stills are that case.

Contributor Spark had the recording, sound included. 19 of its 26 moments have a quote, so most of what it reported was said out loud. The other seven have no quote, five of them in the first window, and Open still answered `[]` there. A null quote only means the words were not the point: that model still had the soundtrack and the motion. The last window is the tail, 32.3 s, about one frame every 4 s. Both contributor moments there have a quote, and that reply is `[]` too.

The token budget left these replies alone. Each one stopped with the two characters `[]`. Output tokens are 342 to 983, under the 4096 cap (`OPEN_MAX_TOKENS`). The tokens beyond that short answer are the reasoning, which this host counts as output. The call that ran out of room is a different cached one: the Talos check at 1500 output tokens, and its text is empty. This model can return a finding when the clip is a short check and the prompt includes the player's words (the cached Talos answer is 559 characters, `finish_reason` stop). These Cogito cache rows do not store the notes.

## A fair comparison on this same call

Same spark test, same model. No second pipeline.

Use a window of about 16 s, so the eight frames fall every 2 s, the spacing a check clip already uses. The 32 s tail was still `[]`, so a slightly shorter 120 s window does not make the comparison fair.

Send more frames only if Baseten accepts more than 8 images. It does not today. The 15 s gap is that limit.

Give it the words as text. This host does not understand audio (task 21). The check prompt already puts the Voice Transcribe transcript on this same call. The spark prompt does not.

Run one text-only probe: this prompt and no frames. If that answer is also `[]`, the frames did not change it.
