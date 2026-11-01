# Playtest guide

Thank you for playing. It takes about 20 minutes, on a Windows PC with a microphone.

## Before you start

1. Read [CONSENT.md](CONSENT.md). You will reply "I agree" (and your choice there) when you send your recording.
2. Start recording **with your microphone on**, before you open the game:
   - **Xbox Game Bar** (built into Windows): press **Win+Alt+R** while the game is in front. Press it again to stop. Check that the microphone is on in Game Bar's capture settings (Win+G, then the gear). Videos are saved in `Videos\Captures`.
   - **OBS**, if you already use it: record the game with your microphone.
   - **Streaming** instead (Twitch, YouTube or Discord): tell Sasha before you start so he can record your stream. You still send the log file after.
3. Unzip the build and double-click `PlaytestBuild.exe`. If Windows warns about an unknown app, choose "More info", then "Run anyway".
4. When you press New Game, the screen flashes white and beeps once. Keep that in the recording: it lines up your video with the game's log.

## While you play

- **Think out loud.** Say what you're looking at, what you're trying to do, and what you expect to happen. If you're confused, say so. There are no wrong answers: we're testing the game, not you.
- Don't ask for help, and don't look anything up.
- Your goal is to run around the lobby room and complete 2 quests that you can read in inventory menu. Start screen recording before you open the game, and stop it once the game is quit from the main menu.

Stop when you finish the task, or after 20 minutes, whichever comes first.

## After

1. Quit the game from its menu (this finishes the log), then stop the recording.
2. Find the newest log file. Its name is the date and time, and it ends in `.jsonl`. Paste `%APPDATA%\Godot\app_userdata\Cogito\playtest_lens` into the address bar of a File Explorer window and press Enter.
3. Send the video and the log through a file link (Google Drive, Dropbox or WeTransfer; the video is too big for email), with "I agree" and your choice from CONSENT.md.
