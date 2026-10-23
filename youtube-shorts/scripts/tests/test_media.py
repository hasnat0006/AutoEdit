"""The ffmpeg tests: apply-cut stays on the frame grid, verify-render catches a 2-frame black flash, missing BT.709 tags
and a Short over 60 s. All media is synthesised with lavfi (testsrc2, sine, color)."""
import os, random, unittest
from .helpers import ffmpeg, load, needs_ffmpeg, probe, read, run, scratch, write

TAGS = ["-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv", "-movflags", "+write_colr"]


@needs_ffmpeg
class ApplyCut(unittest.TestCase):
    def test_duration_within_one_frame_over_many_segments(self):
        d = scratch(self)
        src = os.path.join(d, "raw.mp4")
        ffmpeg("-f", "lavfi", "-i", "testsrc2=size=160x90:rate=30:duration=45", "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=45",
               "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", src)
        rnd, kept, t = random.Random(5), [], 0.37
        while len(kept) < 80:                               # 80 short segments at times that are never on the frame grid
            dur = rnd.uniform(0.18, 0.45)
            kept.append({"start": round(t, 3), "end": round(t + dur, 3)}); t += dur + rnd.uniform(0.05, 0.2)
        cl = write(os.path.join(d, "cut-list.json"), {"kept": kept})
        out = os.path.join(d, "public", "input-video.mp4"); os.makedirs(os.path.dirname(out))
        r = run("apply-cut.py", "--input", src, "--cut-list", cl, "--out", out, "--preset", "ultrafast")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        cm = load(os.path.join(d, "cut-map.json"))
        streams, _ = probe(out)
        self.assertLessEqual(abs(streams["video"] - cm["flat_duration"]), 1 / 30 + 1e-6)
        self.assertLessEqual(abs(streams["video"] - streams["audio"]), 0.12)
        self.assertAlmostEqual(cm["flat_duration"], sum(s["frames"] for s in cm["segments"]) / 30, places=3)
        for s in cm["segments"]:                             # every boundary sits on the source grid
            self.assertAlmostEqual(s["src_start"] * 30, round(s["src_start"] * 30), places=2)


@needs_ffmpeg
class VerifyRender(unittest.TestCase):
    def render(self, d, name, vf=None, tags=True, dur=6):
        path = os.path.join(d, name)
        ffmpeg("-f", "lavfi", "-i", "testsrc2=size=180x320:rate=30:duration=%d" % dur, "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=%d" % dur,
               # ffmpeg 9: frame colour properties override the output flags on an encode, so tag the frames too
               *(["-vf", ",".join(f for f in (("setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709" if tags else None), vf) if f)]
                 if (vf or tags) else []), "-c:v", "libx264", "-preset", "ultrafast", "-b:v", "1M", "-pix_fmt", "yuv420p",
               *(TAGS if tags else []), "-c:a", "aac", "-shortest", path)
        return path

    def verify(self, d, path, *extra, dur=6):
        index = write(os.path.join(d, "public", "index.html"), '<div id="stage" data-composition-id="t" data-start="0" data-duration="%d.000">\n'
                      '<div class="card-host clip" id="host-a" data-start="1.200" data-duration="2" data-anchor="x"></div>\n</div>\n' % dur)
        out = os.path.join(d, "check", os.path.basename(path) + ".md")
        return run("verify-render.py", "--render", path, "--index", index, "--res", "180x320", "--out", out, *extra), out

    def test_over_sixty_seconds_fails(self):
        d = scratch(self)
        r, out = self.verify(d, self.render(d, "long.mp4", dur=61), dur=61)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("| Short length | FAIL | 61.00 s | <= 60 s |", read(out))

    def test_clean_render_passes(self):
        d = scratch(self)
        r, out = self.verify(d, self.render(d, "clean.mp4"))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(os.path.exists(os.path.join(os.path.dirname(out), "render-sheet.png")))
        self.assertIn("**PASS**", read(out))

    def test_two_frame_black_flash_fails(self):
        d = scratch(self)
        r, out = self.verify(d, self.render(d, "flash.mp4", vf="drawbox=x=0:y=0:w=iw:h=ih:color=black:t=fill:enable='between(n,60,61)'"))
        self.assertEqual(r.returncode, 1, r.stdout)
        md = read(out)
        self.assertIn("| Black frames | FAIL |", md)
        self.assertIn("2.000 - 2.067 s (0.067 s, 2 frames): flash", md)

    def test_missing_bt709_tags_fail(self):
        d = scratch(self)
        r, out = self.verify(d, self.render(d, "untagged.mp4", tags=False))
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("| Colour tags | FAIL |", read(out))

    def test_clipped_word_fails(self):
        d = scratch(self)
        kept = write(os.path.join(d, "flat.json"), [{"text": w, "start": i * 0.4, "end": i * 0.4 + 0.3} for i, w in enumerate("so the product is great".split())])
        heard = write(os.path.join(d, "heard.json"), {"words": [{"text": w, "start": i * 0.4, "end": i * 0.4 + 0.3} for i, w in enumerate("So product is great.".split())]})
        r, out = self.verify(d, self.render(d, "clean.mp4"), "--words", heard, "--kept", kept)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("**the**", read(out))


if __name__ == "__main__":
    unittest.main()
