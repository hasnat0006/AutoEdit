# Finding the moments in a long episode

## What makes a moment

- **It stands alone.** Someone scrolling in with no context gets it in the first 3 seconds. Start on a question, a
  bold claim, or the first line of a story; never mid-thought ("...pockets. They'll get there eventually").
- **The first 3 seconds (NOTES 13, from retention graphs).** The speaker on screen from frame 0 and the claim said
  by ~3 s. If the claim comes later in the source, cut in on it (or on the line just before it) instead of keeping
  the warm-up ("It is an honor to be sitting across from..."). A moment that opens on B-roll or a cutaway starts
  where the speaker is first seen. Note the claim's words in MOMENTS.md: `hookcheck.py --claim` needs them.
- **One idea, a payoff at the end.** A story with a twist (the audition overheard while making a sandwich), a reveal
  (a chair is a car), a rant with a mic-drop ("Keep it to yourself and enjoy it"), a demo (the Price voice), an
  emotional line followed by a laugh ("we gotta unplug the cameras after that").
- **15 to 60 s.** Under 60 is a hard limit; 20 to 45 is the sweet spot. Trim asides inside a moment (a job title, a
  code name) with extra pieces in keeps.txt rather than dropping the moment.
- **Fans' currency.** For a game or show: a character detail (a new beard), how something was made (mocap reality),
  anything players will recognise (battle-chatter lines).
- **Loops.** The best end leads back into the first line, so the replay feels seamless.

Loudness peaks (`energy.txt`) find laughter on a raw mix; on a compressed podcast mix they are flat and the transcript
does the work. Check `frames/overview.jpg` for the cutaways (game footage, B-roll) a moment can use.

## The shortlist (MOMENTS.md)

| # | In - out | Length | Who | The moment | Hook line | Why it works |
|---|---|---|---|---|---|---|

Rank by strength; note names to confirm (ASR mangles names: the Valeria actress came out "Maria / Marina / Mario")
and moments that need a careful cut (overlapping voices). Offer: cut 1 to 3 first, or all.

## Cutting

`keeps.txt` lines: `<id><letter> | <slug> | <first words> | <last words> | <search after s>`. Pieces of one clip play in
time order. `cutplan.py` snaps each edge to the quietest 10 ms in the gap; `checkcut.py` proves the edge words are
heard after the cut. A clip's join goes in a pause, never inside a word. The two edges that went wrong on CODPOD were
both found by transcribing the piece alone, not by the level chart.
