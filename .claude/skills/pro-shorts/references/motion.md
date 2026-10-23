# Motion: why the style looks professional

The creator's verdict on v2 (single-colour outline icons drawing themselves on, one easing, floating in the black
band) was "very simple, it doesn't feel professional". v3 to v5 fixed it with the rules below. Each has a reason;
when a new idea doesn't fit a rule, keep the reason.

## The look of an element

- **Designed, not drawn.** A filled shape with a gradient and a highlight reads as a designed object; an outline
  reads as clip-art. The kit's icons (`TROPHY`, `HEART`, `PADLOCK` in motionkit.py) use `#gold`, `#goldDark`,
  `#steel`, `#heart` gradients plus a white highlight stripe at 30 to 55% opacity. New icons follow that recipe.
- **Real UI where the idea is the internet.** "Posting spoilers" became comment cards (avatar circle, @name in grey
  22 px, text in near-black 36 px on a white card, radius 30); "nobody's impressed" became a like count. Viewers
  recognise UI instantly, and it looks produced. Avatar colours need 3:1 against the white initial (the lint warns).
- **Bold sizes.** A big word spans the frame (196 px across 960 px); an icon is ~230 px; a count 116 px. Small
  elements (the 140 px icons of v2) read as decoration.
- **Text stays plain** (NOTES 7): no stroke, no shadow, no glow. Legibility comes from where it sits (the black band,
  or behind the people where the background is dark) and from size.

## The motion of an element

Every move has four parts. Leaving any out is what made v2 look cheap.

1. **Anticipation**: a small move the other way first. Before the X lands the trophy squashes (scaleY 0.92) for
   0.07 s; before an exit the element lifts 10 to 14 px. It tells the eye something is about to happen.
2. **The move, with motion blur** when it travels fast: `filter: blur(10 to 18px)` at the start, 0 on arrival
   (the slam, the slide out from behind a shoulder, the padlock falling, a card flying out of a mouth).
3. **Overshoot**: `back.out(1.5 to 1.8)` for slides and fly-ins, scale keyframes 1.32 → 0.94 → 1 for pops.
4. **Settle**: `elastic.out(1, 0.4 to 0.5)` after an impact; nothing just stops.

Plus:
- **Squash and stretch on impact**: scaleX 1.12 to 1.2, scaleY 0.8 to 0.86 for 0.06 s, origin at the contact edge
  (`50% 100%` for something landing).
- **Secondary motion on every hit**: a burst of 7 to 12 rays (`k.burst`, white, the accent or red; hidden except
  while firing, since round caps leave dots), sparkles that twinkle (`k.twinkle`), a bob, a beat.
- **Timing**: entrances 0.2 to 0.45 s, impacts 0.06 to 0.1 s, strokes drawn in 0.07 to 0.24 s (`power4.in` for a
  slash, `power3.out` for a ring). Exits are faster than entrances.
- **Exits are moves too**: a tip-and-fall (`exit_fall`), a slide back behind someone, a squash-flat delete. Never just a fade.

## Placement and depth

- **Behind the people** (`layer="behind"`, needs `depth/subject.webm`): things that belong in the scene. A big word
  across a wide shot reads through the gaps between the guests; an object slides out from behind a shoulder and back.
- **In front**: things that come at the viewer: comment cards, a like count, a padlock that drops in.
- **From the footage**: a card flies out of the speaker's mouth (`fly_from(BARRY, ...)`); an object rises from behind
  a shoulder. Graphics that touch the picture feel like part of the edit; graphics floating apart feel pasted on.
- **The band above a letterboxed picture** (y ~200 to 660) is the home for front elements; keep out of the top
  200 px (YouTube's icons) and the subtitle line.

## One element per idea

Read the transcript for the 4 to 6 ideas a viewer should see: the thing named ("spoilers", "an award"), the
action ("this happened" x3), the reaction ("no one's impressed"), the payoff ("keep it to yourself"). One element
each, on its word, gone before the next idea. A mid-clip moment with no element still gets the footage (a shake on
"bothered"). Leave the rest to the subtitles.

## Review

Stills lie about motion. After each render, `strips.py` the frames around every element (12 fps) and every
transition (30 fps): look for a move that has no anticipation or settle, blur left on, a burst's dots left behind, an
element that is too dark or hazy, a layer misaligned during a punch.

## Depth: when a word belongs behind the people (learned on codpod12-01/05/08)

A word or object behind the cut-out only works where there is open background for it. Check the shot on
`shots.png` before choosing the layer:
- **A single centred speaker** (a host shot): a wide word behind them loses its middle letters ("VOICE" survived,
  "CHANGING" read as "CH  GING"). Keep words behind a single to 5 letters, or put them in the band.
- **A two-shot** (people at both sides): a word across the frame loses its first and last letters ("LOW" read as
  "OW", "IMMERSIVE" lost two letters to a lamp and a shoulder). Use the black band above the picture instead.
- **Objects** (a chair, a car, a cigar, a heart) behind the people work well when placed in a real gap (beside a
  single, between two people) and when they exit *behind* someone (the car driving off behind the host).
- Never put a front element over a face (the v1 balloon sat on Barry's face): start it beside the person.
