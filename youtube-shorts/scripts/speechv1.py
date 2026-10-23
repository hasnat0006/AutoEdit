"""speechv1.py: read auto-editor's v1 speech export into (start, end) seconds.

auto-editor 29 writes no "timebase" into the v1 export, so its frame counts must be divided by the source's own frame
rate (a 23.976 fps podcast read as 30 fps puts every chunk at 80% of its real time). Order: the file's timebase, then
ffprobe on the file's "source", then 30.
"""
import json, os, subprocess


def fps_of(d, path=""):
    if d.get("timebase"):
        num, den = [int(x) for x in str(d["timebase"]).split("/")]
        return num / den
    src = d.get("source", "")
    # "source" is relative to wherever auto-editor ran: try it as given, then from each folder above the export
    cands, here = [src], os.path.dirname(os.path.abspath(path))
    while src and not os.path.isabs(src):
        cands.append(os.path.join(here, src))
        if os.path.dirname(here) == here:
            break
        here = os.path.dirname(here)
    cands.append(os.path.join(os.path.dirname(os.path.abspath(path)), "raw", os.path.basename(src)))
    for cand in cands:
        if cand and os.path.exists(cand):
            out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                  "stream=r_frame_rate", "-of", "csv=p=0", cand], capture_output=True, text=True).stdout
            try:
                num, den = [int(x) for x in out.strip().split("/")]
                if num and den:
                    return num / den
            except ValueError:
                pass
    return 30.0


def chunks(path):
    d = json.load(open(path))
    fps = fps_of(d, path)
    return [(a / fps, b / fps) for a, b, sp in d["chunks"] if sp not in (99999, 0)]
