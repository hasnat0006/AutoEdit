"""reframe.py (any flat cut -> 1080x1920, same duration) and finish.py (loudness, music bed, tags, Shorts checks)."""
import json, os, subprocess, unittest
from .helpers import ffmpeg, needs_ffmpeg, probe, run, scratch


def stream(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=width,height,r_frame_rate,color_primaries,nb_frames", "-of", "json", path], capture_output=True, text=True, check=True)
    return json.loads(r.stdout)["streams"][0]


@needs_ffmpeg
class Reframe(unittest.TestCase):
    def test_landscape_becomes_vertical_and_keeps_its_length(self):
        d = scratch(self)
        src, out = os.path.join(d, "flat.mp4"), os.path.join(d, "public", "input-video.mp4")
        ffmpeg("-f", "lavfi", "-i", "testsrc2=s=640x360:r=25:d=3", "-f", "lavfi", "-i", "sine=f=440:sample_rate=48000:d=3",
               "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", src)
        r = run("reframe.py", "--in", src, "--out", out, "--keys", "0:0.3,1.5:0.7", "--preset", "ultrafast")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        v = stream(out)
        self.assertEqual((v["width"], v["height"], v["r_frame_rate"], v["color_primaries"]), (1080, 1920, "30/1", "bt709"))
        streams, _ = probe(out)
        self.assertAlmostEqual(streams["video"], 3.0, delta=0.05)
        self.assertIn("audio", streams)
        self.assertIn("2 window position(s)", r.stdout)
        self.assertIn("WARN the window is upscaled", r.stdout)       # 202x360 -> 1080x1920 is soft, and it says so

    def test_vertical_is_scaled_without_a_warning(self):
        d = scratch(self)
        src, out = os.path.join(d, "phone.mp4"), os.path.join(d, "v.mp4")
        ffmpeg("-f", "lavfi", "-i", "testsrc2=s=2160x3840:r=30:d=1", "-f", "lavfi", "-i", "sine=f=440:sample_rate=48000:d=1",
               "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", src)
        r = run("reframe.py", "--in", src, "--out", out, "--preset", "ultrafast")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual((stream(out)["width"], stream(out)["height"]), (1080, 1920))
        self.assertNotIn("WARN", r.stdout)

    def test_position_outside_the_frame_is_refused(self):
        d = scratch(self)
        src = os.path.join(d, "flat.mp4")
        ffmpeg("-f", "lavfi", "-i", "testsrc2=s=320x180:r=30:d=1", "-c:v", "libx264", "-preset", "ultrafast", src)
        r = run("reframe.py", "--in", src, "--out", os.path.join(d, "o.mp4"), "--x", "1.4")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("outside 0..1", r.stderr)


@needs_ffmpeg
class Finish(unittest.TestCase):
    def render(self, d, size="1080x1920", dur=4):
        path = os.path.join(d, "render-raw.mp4")
        ffmpeg("-f", "lavfi", "-i", "color=c=0x334455:s=%s:r=30:d=%s" % (size, dur), "-f", "lavfi",
               "-i", "sine=f=330:sample_rate=48000:d=%s,volume=-26dB" % dur, "-c:v", "libx264", "-preset", "ultrafast",
               "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", path)
        return path

    def lufs(self, path):
        err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-vn", "-af", "ebur128", "-f", "null", "-"],
                             capture_output=True, text=True).stderr
        return float(err[err.rfind("I:"):].split()[1])

    def test_voice_to_minus_14_picture_untouched(self):
        d = scratch(self)
        src, out = self.render(d), os.path.join(d, "final.mp4")
        r = run("finish.py", "--in", src, "--out", out)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertAlmostEqual(self.lufs(out), -14.0, delta=1.0)
        self.assertEqual(stream(out)["nb_frames"], stream(src)["nb_frames"])     # stream copy: same frames
        self.assertEqual(stream(out)["color_primaries"], "bt709")

    def test_music_bed_keeps_the_length(self):
        d = scratch(self)
        src, out, bed = self.render(d), os.path.join(d, "final.mp4"), os.path.join(d, "bed.mp3")
        ffmpeg("-f", "lavfi", "-i", "sine=f=110:sample_rate=44100:d=1.5", bed)     # shorter than the Short: it loops
        r = run("finish.py", "--in", src, "--out", out, "--music", bed)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("ducked", r.stdout)
        streams, _ = probe(out)
        self.assertAlmostEqual(streams["audio"], 4.0, delta=0.06)
        self.assertAlmostEqual(self.lufs(out), -14.0, delta=1.0)                  # the bed does not push the mix over
        self.assertFalse([f for f in os.listdir(d) if f.endswith(".mix.wav")])   # the intermediate is cleaned up

    def test_not_a_short_fails(self):
        d = scratch(self)
        r = run("finish.py", "--in", self.render(d, size="320x180"), "--out", os.path.join(d, "final.mp4"))
        self.assertEqual(r.returncode, 1)
        self.assertIn("FAIL 320x180 is not 1080x1920", r.stdout)


if __name__ == "__main__":
    unittest.main()
