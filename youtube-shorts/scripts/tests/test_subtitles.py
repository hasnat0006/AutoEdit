"""subtitles.py (captions over a finished edit): the page keeps the clip's own size, words land on their times,
punch phrases stay on one line, and the automatic sounds keep their spacing."""
import os, re, unittest
from .helpers import run, scratch, write, read, ffmpeg, needs_ffmpeg

TEXT = "Like the guy in sandals. I just hate 'em. A mugger comes in and I'm in a hoodie."
WORDS = [{"text": w, "start": round(0.3 + 0.32 * i, 3), "end": round(0.55 + 0.32 * i, 3)} for i, w in enumerate(TEXT.split())]


@needs_ffmpeg
class Subtitles(unittest.TestCase):
    def build(self, spec, size="1080x1920", words=WORDS):
        d = scratch(self)
        clip = os.path.join(d, "edit.mp4")
        ffmpeg("-f", "lavfi", "-i", "color=c=gray:s=%s:r=30:d=6" % size, "-f", "lavfi", "-i", "sine=f=220:d=6",
               "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", clip)
        write(os.path.join(d, "transcript.json"), words)
        sp = write(os.path.join(d, "captions.json"), dict({"transcript": "transcript.json"}, **spec))
        r = run("subtitles.py", "--video", clip, "--spec", sp, "--out", os.path.join(d, "public"))
        page = read(os.path.join(d, "public", "index.html")) if r.returncode == 0 else ""
        return r, page, d

    def test_page_keeps_the_clip_shape_and_copies_it(self):
        r, page, d = self.build({}, size="1920x1080")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('data-width="1920" data-height="1080"', page)
        self.assertIn('data-has-audio="true"', page)
        self.assertTrue(os.path.exists(os.path.join(d, "public", "input-video.mp4")))
        self.assertTrue(os.path.exists(os.path.join(d, "public", "fonts", "Inter-700.woff2")))

    def test_every_word_lands_on_its_time(self):
        r, page, _ = self.build({})
        self.assertEqual(r.returncode, 0, r.stderr)
        n = len(re.findall(r'<span class="w[^"]*" id="l\d+-w\d+"', page))
        self.assertEqual(n, len(WORDS))
        self.assertIn("%.3f);" % (WORDS[4]["start"] - 0.03), page)        # "sandals." rises 30 ms before it is said

    def test_lines_break_at_sentences_and_stay_short(self):
        r, page, _ = self.build({"max_words": 3})
        self.assertEqual(r.returncode, 0, r.stderr)
        for line in re.findall(r'<span class="row">(.*?)</span></div>', page):
            self.assertLessEqual(line.count('class="w'), 3)
        self.assertNotRegex(page, r"sandals\.</span> <span")              # nothing follows a sentence end on its line

    def test_two_rows_split_evenly_and_never_on_a_punch(self):
        i = TEXT.split().index("hate")
        r, page, _ = self.build({"rows": 2, "max_words": 3, "max_chars": 18, "punch": ["%d-%d" % (i, i + 1)]})
        self.assertEqual(r.returncode, 0, r.stderr)
        caps = re.findall(r'<span class="row">(.*?)</span></div>', page)
        self.assertTrue(any("<br>" in c for c in caps))
        for c in caps:
            self.assertLessEqual(c.count("<br>"), 1)
            for row in c.split("<br>"):
                self.assertLessEqual(row.count('class="w'), 3)
        punch = re.search(r'<div class="line punch"[^>]*>(.*?)</div>', page).group(1)
        self.assertNotIn("<br>", punch)

    def test_punch_phrase_is_one_big_line(self):
        i = TEXT.split().index("hate")
        r, page, _ = self.build({"punch": ["%d-%d" % (i, i + 1)]})
        self.assertEqual(r.returncode, 0, r.stderr)
        m = re.search(r'<div class="line punch" id="(l\d+)"[^>]*font-size:(\d+)px">(.*?)</div>', page)
        self.assertIsNotNone(m)
        self.assertEqual(int(m.group(2)), round(78 * 1.45))
        self.assertEqual(m.group(3).count('class="w'), 2)                  # "hate" and "'em." together

    def test_emphasis_by_word_and_index(self):
        r, page, _ = self.build({"em": ["sandals", 1], "sfx": False})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(page.count('class="w em"'), 2)
        self.assertNotIn("<audio", page)

    def test_auto_sounds_keep_their_spacing(self):
        r, page, _ = self.build({"em": ["guy", "in", "sandals", "mugger", "hoodie"], "punch": [8]})
        self.assertEqual(r.returncode, 0, r.stderr)
        starts = sorted(float(x) for x in re.findall(r'<audio id="sfx-\d+" src="sfx/[^"]+" data-start="([0-9.]+)"', page))
        self.assertTrue(starts)
        self.assertIn("whoosh-short.wav", page)
        for a, b in zip(starts, starts[1:]):
            self.assertGreaterEqual(b - a, 0.3)
        clicks = sorted(float(x) for x in re.findall(r'src="sfx/click-soft.wav" data-start="([0-9.]+)"', page))
        for a, b in zip(clicks, clicks[1:]):
            self.assertGreaterEqual(b - a, 2.0)

    def test_caption_free_window(self):
        r, page, _ = self.build({"off": [[1.5, 3.0]]})
        self.assertEqual(r.returncode, 0, r.stderr)
        for t in re.findall(r"tl\.set\('#l\d+', \{ visibility: 'visible'[^}]*\}, ([0-9.]+)\);", page):
            self.assertFalse(1.5 <= float(t) < 3.0)

    def test_hook_is_on_the_first_frame(self):
        r, page, _ = self.build({"hook": {"text": "Stop playing college|football at 26", "em": ["26"], "y": 470}})
        self.assertEqual(r.returncode, 0, r.stderr)
        m = re.search(r'<div id="hook" style="top:470px;[^"]*">(.*?)</div>\n', page)
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1).count('class="hk-row"'), 2)
        self.assertIn('<span class="hk-w em">26</span>', m.group(1))
        self.assertNotRegex(page, r"tl\.\w+\('#hook'")                    # no entrance, held to the end: no tween at all

    def test_camera_moves_the_picture_inside_its_window(self):
        r, page, _ = self.build({"window": {"y": 675, "h": 570},
                                 "camera": [["punch", 1.0, 1.12, 300, 795], ["shake", 2.0, 10, 0.2], ["flash", 2.0, 0.3], ["release", 3.0, 0.4]]})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('<div id="win" style="top:675px;height:570px"><div id="cam"><video id="clip"', page)
        self.assertIn('style="top:-675px"', page)
        self.assertIn("transformOrigin: '300px 120px'", page)              # the face, in window coordinates
        self.assertIn("tl.to('#cam', { scale: 1.120, duration: 0.26, ease: 'expo.out' }, 1.000);", page)
        self.assertRegex(page, r"tl\.fromTo\('#flash', \{ opacity: 0\.30 \}")
        self.assertIn("tl.to('#cam', { x: 0, y: 0, rotation: 0", page)       # every shake settles back to centre

    def test_preset_fills_what_the_spec_leaves_out(self):
        r, page, _ = self.build({"preset": "box", "size": 60})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('class="line hl"', page)                            # the preset's style
        self.assertIn("text-transform:uppercase;", page)
        self.assertIn("font-size:60px", page)                              # the spec's own size wins
        r, _, _ = self.build({"preset": "nope"})
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("no subtitle preset", r.stderr)

    def test_every_preset_builds_every_word(self):
        i = TEXT.split().index("hate")
        for name in ("clean", "box", "bounce", "karaoke", "wipe", "calm"):
            r, page, _ = self.build({"preset": name, "em": ["sandals"], "punch": ["%d-%d" % (i, i + 1)]})
            self.assertEqual(r.returncode, 0, name + r.stderr)
            self.assertEqual(len(re.findall(r'<span class="w[^"]*" id="l\d+-w\d+"', page)), len(WORDS), name)
            for underline in ('class="bar"', 'class="ul"', "-bar'", " .ul'"):  # no underline under any word
                self.assertNotIn(underline, page, name)

    def test_text_is_plain(self):
        r, page, _ = self.build({})
        css = page.split("<style>")[1].split("</style>")[0]
        for banned in ("text-shadow", "-webkit-text-stroke", "drop-shadow"):
            self.assertNotIn(banned, css)


if __name__ == "__main__":
    unittest.main()
