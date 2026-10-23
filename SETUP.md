# Setup: from zero to your first Short

About 30 minutes. You click through steps 1 to 6. Claude does the installing in step 7.

## 1. Get the Claude desktop app

Download it from Anthropic's site (claude.com/download) and install it. Sign in with Google or with an email and password. If it's your first time in Claude, go through the first-run setup it offers.

## 2. Pick a plan

You need a paid plan. The $20 plan is enough to set all of this up and edit Shorts. Editing a lot of them every week uses more.

## 3. Open Claude Code

Click **New**. On the left you'll see Claude (chat and Cowork) and Claude Code. Pick **Claude Code**.

## 4. Four settings before you start

- **Local**, so it works on your own computer, where your footage is.
- **Your folder.** Click the folder picker and create a new one, for example "Shorts". Everything happens in there: your clips, the skill, the renders.
- **Permissions on Auto**, so it can run without asking you yes or no a thousand times.
- **The latest model** for the setup. Setup is the important part. You can switch to a cheaper model afterwards.

## 5. Let it use the browser

Bottom left: **Settings**, then **Claude Code**, and turn on the browser setting. The skill uses it to find screenshots, logos and posts to show on screen while you talk about them.

## 6. Connect your tools

**Customize**, then **Connectors**. Search, click the plus, and log in when the browser opens. You'll see a check mark when it's connected.

- **Epidemic Sound**, if you use it for music and sound effects.

It's optional. Without it, the skill uses its own sound-effect kit and the free HyperFrames sound library.

## 7. Install the skill

Put the `WeAreNoCode-YouTube-Editor` folder inside your project folder. Then type:

> Install the youtube-shorts skill from the WeAreNoCode-YouTube-Editor folder into this project's .claude/skills folder. Then check everything it needs, install what's missing, and run its tests.

Claude installs the rest itself: FFmpeg (the tool that joins and encodes video), HyperFrames (it draws the animations and renders the frames), auto-editor and Parakeet (they find where you speak and write down every word with its exact time), plus a few Python packages. If it can't find HyperFrames, search "HyperFrames" (it's on GitHub, and it's in the Connectors list too).

When the tests pass, open a **new** thread. Skills load at the start of a thread.

## 8. Your first Short

Start small: one 30 to 60 second clip. Drop the raw clip in and use the first prompt in `PROMPTS.md`. Then watch it and give it notes.

## How to record so it edits well

- Record vertical on your phone (1080x1920 or 4K vertical, 30 fps). Landscape works too: in 4K with you near the centre, or any landscape clip with the card look.
- Eyes in the top third of the frame. Keep the bottom quarter and the right edge clear; that's where the app's buttons sit.
- Mess up a line? Pause two seconds and say the whole sentence again. The skill keeps your last take and cuts the rest.
- Keep the file flat: no zooms, captions, filters or transitions baked in. The skill adds those.
- Script to about 140 words for 60 seconds. The cut always comes out shorter than the read.
