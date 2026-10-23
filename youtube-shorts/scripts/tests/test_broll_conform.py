"""broll-conform.py on synthetic media: a 24 fps clip with sound and a still both come out as a 9:16 cutaway."""
import os, unittest
from .helpers import run, scratch, ffmpeg, probe, needs_ffmpeg


@needs_ffmpeg
class BrollConform(unittest.TestCase):
    def test_clip_is_30fps_silent_and_trimmed(self):
        d = scratch(self)
        src, out = os.path.join(d, "gen.mp4"), os.path.join(d, "broll", "desk.mp4")
        ffmpeg("-f", "lavfi", "-i", "testsrc2=s=1280x720:r=24", "-f", "lavfi", "-i", "sine=f=440:r=48000", "-t", "5",
               "-c:v", "libx264", "-c:a", "aac", "-shortest", src)
        r = run("broll-conform.py", "--in", src, "--out", out, "--start", "0.5", "--dur", "3.5")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        streams, dur = probe(out)
        self.assertNotIn("audio", streams)
        self.assertAlmostEqual(dur, 3.5, delta=0.05)
        self.assertIn("1080x1920, 30/1 fps", r.stdout)
        self.assertTrue(os.path.exists(out + ".sheet.png"))

    def test_still_becomes_a_push(self):
        d = scratch(self)
        src, out = os.path.join(d, "frame.png"), os.path.join(d, "still.mp4")
        ffmpeg("-f", "lavfi", "-i", "testsrc2=s=1024x1024", "-frames:v", "1", src)
        r = run("broll-conform.py", "--in", src, "--out", out, "--dur", "2")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertAlmostEqual(probe(out)[1], 2.0, delta=0.05)

    def test_half_frame_for_a_split(self):
        d = scratch(self)
        src, out = os.path.join(d, "gen.mp4"), os.path.join(d, "half.mp4")
        ffmpeg("-f", "lavfi", "-i", "testsrc2=s=1280x720:r=30", "-t", "2", "-c:v", "libx264", src)
        r = run("broll-conform.py", "--in", src, "--out", out, "--half", "--focus", "0.2")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("1080x960, 30/1 fps", r.stdout)
        self.assertIn('"type": "split"', r.stdout)

    def test_too_long_is_refused(self):
        d = scratch(self)
        src = os.path.join(d, "gen.mp4")
        ffmpeg("-f", "lavfi", "-i", "testsrc2=s=640x360:r=24", "-t", "2", "-c:v", "libx264", src)
        r = run("broll-conform.py", "--in", src, "--out", os.path.join(d, "x.mp4"), "--dur", "5")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("is longer", r.stderr)


if __name__ == "__main__":
    unittest.main()
