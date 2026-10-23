# Style guide

This is my look, the one the skill is set to. Fill in the "Yours" column, then tell Claude: "Here's my style guide. Update the youtube-shorts skill to match it." Leave a row empty and it keeps mine.

Where it lives: the colours and font are at the top of `youtube-shorts/scripts/compose.py` (the `:root` colour tokens and the font files). Every rule below is written into `youtube-shorts/SKILL.md`. You don't need to open either; Claude does it.

## Colours

| Role | Mine | Yours |
|---|---|---|
| Highlight (key words, ticks, bars) | Cyan `#0AF0F0` | |
| Deep anchor (gradient end, a word-highlight block with white text) | Blue `#0005EE` | |
| Punchline (the payoff word, the last step of a diagram) | Magenta `#CD00EE` | |
| Money and stakes (dollar figures, warnings) | Amber `#FFB904` | |
| Text | White `#FFFFFF` | |

Two rules I learned the hard way: highlighted words are never dark blue (it disappears on dark footage), and only one gradient per frame.

## Font

| | Mine | Yours |
|---|---|---|
| Font | DM Sans, weights 400, 500 and 700; Rubik Mono One for the card look's headlines (in `youtube-shorts/assets/fonts`) | |
| Headlines | 700, with a thin stroke in the same colour to make it heavier | |
| Big numbers | Every digit written out (`$1,000`, never `$1K`), counting up, amber for money | |

## Cards and text on screen

| | Mine | Yours |
|---|---|---|
| Card style | Frosted glass: light glass on dark scenes, dark glass on a bright room | |
| Default for words | One line at the bottom, key words in the highlight colour | |
| Lists | Never a list panel. Each item becomes its own thing: pills next to my head, a diagram, one animation per number | |
| Picture changes | At least every 4 s (every 2.5 s in the first 5 s): a card, a cutaway, a punch, a split. Captions don't count | |
| A person or job I mention | 3 seconds of B-roll of that person doing it | |
| An app I name | A clean, designed window of it, not a screenshot | |
| A website or post I name | The real page, in a browser window, scrolling | |

## Motion

| | Mine | Yours |
|---|---|---|
| Things coming in | 0.4 s, soft ease out. No bounces, no flips | |
| Things leaving | 0.3 s | |
| Timing | Every animation lands on the word it belongs to, 0.15 to 0.25 s before I say it | |
| Variety | Never the same type of animation twice in a row | |
| Busy check | About 1.5 overlays and 1 camera move per 10 seconds, one hero element at a time | |

## Camera

| | Mine | Yours |
|---|---|---|
| Zoom anchor | The top of the frame, so my head never gets cropped | |
| Punch-in on a key word | 106 to 112%, 0.3 s; one jump cut in three | |
| Slow creep across a thought | 104 to 108% over 3 to 6 seconds | |
| At every cut | Back to 100% | |

## Sound

| | Mine | Yours |
|---|---|---|
| Default | Silence on the full-frame look: one or two sounds per Short. The card look gets a sound on every animated element | |
| Allowed | A pop when a logo lands, a light click when a cursor clicks, typing only when someone types, a cha-ching at very low volume for money | |
| Never | A whoosh under text | |
| Music | Optional, per Short: looped under the whole Short, ducked under my voice. Always keep a no-music version too | |

## Cuts

| | Mine | Yours |
|---|---|---|
| Retakes | Keep the last take of every line | |
| Pauses | Nothing longer than about 0.4 s after a sentence | |
| Live demos | Show the result, not the waiting | |
| Flash cuts | Never | |
