# My Shorts editor: the Claude Code skill

This is the skill that edits my short-form videos: YouTube Shorts, Reels and TikToks. Every one comes out 9:16, 1080x1920, 60 seconds at most.

I record, drop the raw clip into Claude Code, and it hands me back a first version: the cut, the vertical frame, word-by-word captions, motion graphics, camera punches, sound effects and an upload-ready MP4. I watch it, give it notes, and anything worth keeping goes back into the skill. That last part is why it keeps getting better. Every rule in it came from a real note I gave on a real Short.

## What's inside

| File or folder | What it is |
|---|---|
| `youtube-shorts/` | The skill. `SKILL.md` is the rulebook Claude reads. `scripts/` are the tools it runs: cutting, the dead-air scan, reframing, the animation composer (the card look for landscape clips, marker strokes, a 3D die, self-drawing charts), captions, render checks and the upload-ready finish. `assets/` holds the fonts, emoji, sound effects and GSAP. `examples/clip-03/` is a finished Short to start from. `NOTES.md` is your running list of corrections, followed on every Short. |
| `SHORTS-GUIDE.md` | **Start here.** What was built, how each step works and why, the clip-03 story through three versions, the lessons, and a checklist for your next Short. |
| `SETUP.md` | How to set it up, step by step. Plan on 30 minutes. Most of it installs itself. |
| `PROMPTS.md` | The exact prompts I type, from setup to "save this to the skill". |
| `STYLE-GUIDE.md` | My look: colours, font, cards, motion, camera, sound and cuts. Change it to yours. |
| `LICENSES/` | The licences for the fonts, the emoji, the sound effects and the code parts adapted from an open-source starter kit. |

## Install in four steps

1. Set up Claude Code: `SETUP.md`, steps 1 to 6.
2. Put this folder inside the project folder you work in.
3. Type this into Claude Code:
   > Install the youtube-shorts skill from the WeAreNoCode-YouTube-Editor folder into this project's .claude/skills folder. Then check everything it needs, install what's missing, and run its tests.
4. Drop in a raw clip and use the first prompt from `PROMPTS.md`.

## What it costs to run

The skill itself is free, and so are most of the tools it uses (HyperFrames, FFmpeg, auto-editor, the Parakeet transcription). The $20 Claude plan is enough to set everything up and edit Shorts; a busy week of Shorts uses more. Epidemic Sound (music) is a paid tool I use. You can skip it and pull sounds from the free library the skill points to.

## Make it yours

The first version will look like my channel, because that's what it learned on. To make it look like yours:

1. Open `STYLE-GUIDE.md` and change the colours, the font and the rules you don't like.
2. Tell Claude: "Here's my style guide. Update the youtube-shorts skill to match it."
3. Edit a Short, give notes in plain words ("the text is too small", "no sound on this part"), and after each round say: "Save this to the skill."

That's how mine learned. Every note I've saved, it hasn't made that mistake again.

## Where to get help

Questions go in the free community: https://www.skool.com/wearenocode

## Licences

- The fonts are DM Sans, Rubik Mono One, Inter and Montserrat, under the SIL Open Font License (`LICENSES/OFL-DM-Sans.txt`, `LICENSES/OFL-Rubik-Mono-One.txt`, `LICENSES/OFL-Inter.txt`, `LICENSES/OFL-Montserrat.txt`).
- The emoji are Noto Emoji (`LICENSES/Noto-Emoji-LICENSE.txt`); the sound effects are from Pixabay (`LICENSES/Pixabay-SFX-CREDITS.md`).
- Some of the scripts started from an open-source starter kit under the MIT License. Its notice is in `LICENSES/MIT-starter-kit.txt` and stays with the code.
- No music, footage or logos ship with this kit. Use your own, or ones you have the rights to.
