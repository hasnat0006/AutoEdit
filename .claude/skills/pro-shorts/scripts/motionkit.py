"""motionkit.py: the building blocks of the pro-shorts motion style, so a clip's builder says WHAT happens, not how.

    import sys; sys.path.insert(0, ".claude/skills/pro-shorts/scripts"); from motionkit import Kit
    k = Kit(seed="clip-id", window=json.load(open("window.json")), beats="beats.json")

Every move follows the same principles (why each exists is in references/motion.md):
  anticipation before a move, overshoot and settle after it (back / elastic eases), squash on an impact, motion blur
  while travelling fast, a secondary detail on every hit (a burst of rays, sparkles), and a tie to the footage.

Layers: k.behind(html) sits BETWEEN the footage and the cut-out people (needs depth/subject.webm); k.front(html) sits
over everything but the captions. Coordinates are frame px (1080x1920); the picture is k.WY .. k.WY + k.WH.
"""
import json, math, os, random

DEFS = """<svg width="0" height="0" style="position:absolute"><defs>
  <linearGradient id="gold" x1="0" y1="0" x2="0.4" y2="1"><stop offset="0" stop-color="#FFE98A"/><stop offset=".45" stop-color="#F7B500"/><stop offset="1" stop-color="#B87400"/></linearGradient>
  <linearGradient id="goldDark" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#D99300"/><stop offset="1" stop-color="#8A5600"/></linearGradient>
  <linearGradient id="steel" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#8E959C"/><stop offset=".35" stop-color="#F4F6F8"/><stop offset="1" stop-color="#7C838A"/></linearGradient>
  <linearGradient id="heart" x1="0" y1="0" x2="0.3" y2="1"><stop offset="0" stop-color="#FF7A7A"/><stop offset="1" stop-color="#D3141C"/></linearGradient>
  <linearGradient id="cigar" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#A86B3C"/><stop offset=".3" stop-color="#7A4421"/><stop offset="1" stop-color="#3E200D"/></linearGradient>
  <radialGradient id="ember" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#FFF2A8"/><stop offset=".45" stop-color="#FF7A1A"/><stop offset="1" stop-color="#C21E00"/></radialGradient>
</defs></svg>"""

CSS = """<style>
  .fxl { position:absolute; left:0; top:0; width:1080px; height:1920px; pointer-events:none; }
  .fxl .el { position:absolute; opacity:0; will-change:transform, filter; }
  .fxl svg { display:block; overflow:visible; }
  .fxl .ov { position:absolute; left:0; top:0; }
  .fxl .ln { fill:none; stroke-linecap:round; stroke-linejoin:round; stroke-dasharray:100 102; stroke-dashoffset:100; }
  .fxl .ray { fill:none; stroke-linecap:round; stroke-dasharray:45 400; stroke-dashoffset:45; opacity:0; }
  .fxl .word { position:absolute; left:0; right:0; text-align:center; font-family:"SubFont", sans-serif; font-weight:700;
    line-height:1; letter-spacing:.02em; color:#FFFFFF; }
  .fxl .spk { position:absolute; opacity:0; }
  .fxl .card { position:absolute; display:flex; align-items:center; gap:18px; width:440px; padding:18px 24px 18px 18px; border-radius:30px;
    background:rgba(255,255,255,.97); opacity:0; will-change:transform, filter; }
  .fxl .card .av { width:62px; height:62px; border-radius:50%; flex:none; color:#fff; font:700 30px/62px "SubFont", sans-serif; text-align:center; }
  .fxl .card .nm { font:700 22px/1.1 "SubFont", sans-serif; color:#6B7280; margin-bottom:6px; }
  .fxl .card .bd { font:700 36px/1.05 "SubFont", sans-serif; color:#111111; letter-spacing:-.01em; }
  .fxl .num { position:absolute; font:700 116px/1 "SubFont", sans-serif; color:#FFFFFF; letter-spacing:-.02em; opacity:0;
    font-variant-numeric:tabular-nums; will-change:transform; }
</style>"""

# ---- shaded icons (filled, gradient, highlight: never a bare outline) -------------------------------------------
TROPHY = ('<svg viewBox="0 0 260 300" width="%(w)d" height="%(h)d">'
          '<path d="M52 48 C8 48 8 124 66 128" style="fill:none;stroke:url(#gold);stroke-width:16px;stroke-linecap:round"/>'
          '<path d="M208 48 C252 48 252 124 194 128" style="fill:none;stroke:url(#gold);stroke-width:16px;stroke-linecap:round"/>'
          '<path d="M48 28 L212 28 L205 100 C197 152 166 180 130 184 C94 180 63 152 55 100 Z" fill="url(#gold)"/>'
          '<path d="M70 44 C66 82 74 124 98 154" style="fill:none;stroke:rgba(255,255,255,.55);stroke-width:10px;stroke-linecap:round"/>'
          '<path d="M130 70 L139 92 L162 92 L144 106 L151 128 L130 115 L109 128 L116 106 L98 92 L121 92 Z" fill="#FFF3B0"/>'
          '<rect x="116" y="182" width="28" height="40" fill="url(#goldDark)"/>'
          '<rect x="74" y="218" width="112" height="34" rx="9" fill="url(#goldDark)"/><rect x="92" y="228" width="76" height="14" rx="4" fill="#5C3A00"/></svg>')
HEART = ('<svg viewBox="0 0 180 170" width="%(w)d" height="%(h)d">'
         '<path d="M90 158 C40 122 6 94 6 58 C6 28 30 8 56 8 C72 8 84 18 90 30 C96 18 108 8 124 8 C150 8 174 28 174 58 C174 94 140 122 90 158 Z" fill="url(#heart)"/>'
         '<ellipse cx="50" cy="46" rx="18" ry="10" transform="rotate(-32 50 46)" fill="rgba(255,255,255,.5)"/></svg>')
PADLOCK = ('<svg viewBox="0 0 220 260" width="%(w)d" height="%(h)d">'
           '<g class="shackle"><path d="M62 124 L62 80 C62 18 158 18 158 80 L158 124" style="fill:none;stroke:url(#steel);stroke-width:24px;stroke-linecap:round"/></g>'
           '<rect x="28" y="112" width="164" height="132" rx="28" fill="url(#gold)"/>'
           '<rect x="44" y="124" width="28" height="104" rx="14" fill="rgba(255,255,255,.28)"/>'
           '<circle cx="110" cy="166" r="17" fill="#4A3300"/><rect x="104" y="172" width="12" height="36" rx="5" fill="#4A3300"/></svg>')
CIGAR = ('<svg viewBox="0 0 320 90" width="%(w)d" height="%(h)d">'
         '<rect x="10" y="18" width="250" height="56" rx="26" fill="url(#cigar)"/>'
         '<rect x="26" y="26" width="220" height="10" rx="5" fill="rgba(255,255,255,.22)"/>'
         '<rect x="60" y="16" width="44" height="60" rx="6" fill="url(#gold)"/><rect x="70" y="38" width="24" height="16" rx="3" fill="#8A1C1C"/>'
         '<rect x="250" y="20" width="44" height="52" rx="10" fill="#B9B4AC"/><rect x="254" y="26" width="34" height="8" rx="4" fill="rgba(255,255,255,.4)"/>'
         '<ellipse class="ember" cx="298" cy="46" rx="16" ry="26" fill="url(#ember)"/></svg>')
X_MARK = ('<svg class="ov" viewBox="0 0 260 300" width="%(w)d" height="%(h)d">'
          '<path id="%(id)s-x1" class="ln" pathLength="100" d="M22 30 L238 266" style="stroke:#FF3B30;stroke-width:24px"/>'
          '<path id="%(id)s-x2" class="ln" pathLength="100" d="M238 30 L22 266" style="stroke:#FF3B30;stroke-width:24px"/></svg>')
NO_SIGN = ('<svg class="ov" viewBox="0 0 700 300" width="%(w)d" height="%(h)d">'
           '<path id="%(id)s-ring" class="ln" pathLength="100" d="M350 28 C540 26 672 80 670 150 C668 222 540 274 350 272 C160 274 30 222 30 150 C30 80 160 28 352 30" style="stroke:#FF3B30;stroke-width:18px"/>'
           '<path id="%(id)s-slash" class="ln" pathLength="100" d="M128 256 L572 44" style="stroke:#FF3B30;stroke-width:20px"/></svg>')


class Kit:
    def __init__(self, seed, window, beats=None):
        self.r = random.Random(seed)
        self.WY, self.WH, self.D = int(window["y"]), int(window["h"]), float(window.get("duration", 60))
        self.shots = window.get("shots", [])
        b = json.load(open(beats)) if beats and os.path.exists(beats) else []
        b = b["beats"] if isinstance(b, dict) else b
        self.beats = [x["time"] for x in b]; self.strong = [x["time"] for x in b if x["strength"] > 0.5]
        self.js, self.rays, self._behind, self._front, self.sounds = [], {"front": [], "behind": []}, [], [], []

    # ---- timing -------------------------------------------------------------------------------------------------
    def beat(self, t, within=0.13, strong=False):
        """the nearest beat to t when it is close enough (the speech wins otherwise): snap every move a word does not pin"""
        pool = self.strong if strong else self.beats
        if not pool: return t
        b = min(pool, key=lambda x: abs(x - t)); return round(b, 3) if abs(b - t) <= within else t
    def beats_between(self, a, b, strong=True):
        return [x for x in (self.strong if strong else self.beats) if a < x < b]
    def sound(self, src, at, volume, dur=0.6, why=""):
        if "scribble" in src: raise SystemExit("the scribble sound is banned (youtube-shorts/NOTES.md 12)")
        if volume > 0.18: raise SystemExit("sound %s at %.2f is too loud: keep sounds 0.05 to 0.15 (youtube-shorts/NOTES.md 19)" % (src, volume))
        self.sounds.append({"src": "sfx/" + src, "at": round(at, 3), "dur": dur, "volume": volume}); return at

    # ---- layers -------------------------------------------------------------------------------------------------
    def behind(self, html): self._behind.append(html)
    def front(self, html): self._front.append(html)
    def J(self, s): self.js.append(s)

    # ---- elements -----------------------------------------------------------------------------------------------
    def el(self, eid, x, y, w, h, inner, layer="front"):
        (self._behind if layer == "behind" else self._front).append(
            '<div class="el" id="%s" style="left:%dpx;top:%dpx;width:%dpx;height:%dpx">%s</div>' % (eid, x, y, w, h, inner))
    def icon(self, eid, kind, cx, cy, w, layer="front", x_mark=False):
        """a shaded icon (trophy | heart | padlock | cigar) centred on (cx, cy); x_mark adds a hidden red X to slam later"""
        art, ar = {"trophy": (TROPHY, 300 / 260.0), "heart": (HEART, 170 / 180.0), "padlock": (PADLOCK, 260 / 220.0), "cigar": (CIGAR, 90 / 320.0)}[kind]
        h = int(w * ar); inner = '<div id="%s-art">%s</div>' % (eid, art % {"w": w, "h": h})
        if x_mark: inner += X_MARK % {"w": w, "h": h, "id": eid}
        self.el(eid, cx - w // 2, cy - h // 2, w, h, inner, layer); return h
    def big_word(self, eid, text, cy, size=196, layer="behind", no_sign=False):
        """a word across the frame (behind the people: it reads through the gaps), optionally with a red no-sign"""
        w, h = 960, int(960 * 300 / 700.0)
        inner = '<div class="word" id="%s-word" style="top:%dpx;font-size:%dpx">%s</div>' % (eid, int(h / 2 - size * 0.52), size, text)
        if no_sign: inner += NO_SIGN % {"w": w, "h": h, "id": eid}
        self.el(eid, 60, cy - h // 2, w, h, inner, layer)
    def card(self, eid, x, y, name, text, color, layer="front"):
        """a comment card (avatar, @name, text): real-looking UI reads as designed; keep colours >= 3:1 against white"""
        (self._behind if layer == "behind" else self._front).append(
            '<div class="card" id="%s" style="left:%dpx;top:%dpx"><div class="av" style="background:%s">%s</div>'
            '<div class="tx"><div class="nm">@%s</div><div class="bd">%s</div></div></div>' % (eid, x, y, color, name[0].upper(), name, text))
    def number(self, eid, x, y, start_text, layer="front"):
        (self._behind if layer == "behind" else self._front).append('<div class="num" id="%s" style="left:%dpx;top:%dpx">%s</div>' % (eid, x, y, start_text))
    def star(self, sid, x, y, s, layer="front"):
        (self._behind if layer == "behind" else self._front).append(
            '<div class="spk" id="%s" style="left:%dpx;top:%dpx;width:%dpx;height:%dpx"><svg viewBox="-20 -20 40 40" width="%d" height="%d">'
            '<path d="M0 -20 C2.5 -3 3 -2.5 20 0 C3 2.5 2.5 3 0 20 C-2.5 3 -3 2.5 -20 0 C-3 -2.5 -2.5 -3 0 -20Z" fill="#FFF4C2"/></svg></div>' % (sid, x - s // 2, y - s // 2, s, s, s, s))

    # ---- secondary motion ---------------------------------------------------------------------------------------
    def burst(self, bid, cx, cy, t, n=8, r0=90, r1=170, color="#FFFFFF", width=6, a0=0, a1=360, dur=0.32, layer="front"):
        """rays that shoot out once on an impact; hidden except while firing (round caps leave dots otherwise)"""
        for i in range(n):
            a = math.radians(a0 + (a1 - a0) * (i + 0.5) / n + self.r.uniform(-8, 8)); q0, q1 = r0 * self.r.uniform(0.9, 1.1), r1 * self.r.uniform(0.85, 1.1)
            self.rays[layer].append('<path id="%s-%d" class="ray" pathLength="100" d="M%.1f %.1f L%.1f %.1f" style="stroke:%s;stroke-width:%dpx"/>'
                                    % (bid, i, cx + q0 * math.cos(a), cy + q0 * math.sin(a), cx + q1 * math.cos(a), cy + q1 * math.sin(a), color, width))
        sel = '[id^="%s-"]' % bid
        self.J("tl.set('%s', { opacity: 1 }, %.3f);" % (sel, t))
        self.J("tl.fromTo('%s', { strokeDashoffset: 45 }, { strokeDashoffset: -100, duration: %.2f, ease: 'power2.out', stagger: 0.012 }, %.3f);" % (sel, dur, t))
        self.J("tl.set('%s', { opacity: 0 }, %.3f);" % (sel, t + dur + 0.012 * n + 0.02))
    def twinkle(self, sel, t):
        self.J("tl.fromTo('%s', { opacity: 0, scale: 0, rotation: -40 }, { keyframes: [{ opacity: 1, scale: 1.2, rotation: 0, duration: 0.16, ease: 'back.out(3)' }, { opacity: 0, scale: 0, rotation: 30, duration: 0.22, ease: 'power2.in', delay: 0.08 }] }, %.3f);" % (sel, t - 0.04))

    # ---- primary moves ------------------------------------------------------------------------------------------
    def show(self, sel, t): self.J("tl.set('%s', { opacity: 1 }, %.3f);" % (sel, t))
    def hide(self, sel, t): self.J("tl.set('%s', { opacity: 0 }, %.3f);" % (sel, t))
    def draw(self, pid, t, dur=0.22, ease="power3.out"):
        self.J("tl.fromTo('#%s', { strokeDashoffset: 100 }, { strokeDashoffset: 0, duration: %.2f, ease: '%s' }, %.3f);" % (pid, dur, ease, t))
    def slam(self, sel, land):
        """in from big and blurred, impact on `land` (a squash, then an elastic settle)"""
        self.J("tl.fromTo('%s', { scale: 1.9, opacity: 0, filter: 'blur(18px)' }, { scale: 1, opacity: 1, filter: 'blur(0px)', duration: 0.26, ease: 'power4.in' }, %.3f);" % (sel, land - 0.26))
        self.squash(sel, land)
    def squash(self, sel, t, origin="50% 50%"):
        self.J("tl.to('%s', { keyframes: [{ scaleX: 1.12, scaleY: 0.86, duration: 0.06, transformOrigin: '%s' }, { scaleX: 0.96, scaleY: 1.05, duration: 0.10 }, { scaleX: 1, scaleY: 1, duration: 0.24, ease: 'elastic.out(1, 0.5)' }] }, %.3f);" % (sel, origin, t))
    def pop(self, sel, t, overshoot=1.32):
        """from nothing, anticipation-free: over (overshoot), under, settle"""
        self.J("tl.fromTo('%s', { opacity: 0, scale: 0, rotation: -20 }, { keyframes: [{ opacity: 1, scale: %.2f, rotation: 6, duration: 0.2, ease: 'power3.out' }, { scale: 0.94, rotation: 0, duration: 0.12 }, { scale: 1, duration: 0.14 }] }, %.3f);" % (sel, overshoot, t))
    def fly_from(self, sel, from_xy, to_xy, t, rot=0, dur=0.42):
        """shoots out of a point in the picture (a mouth, a hand) small and blurred, lands with overshoot"""
        dx, dy = from_xy[0] - to_xy[0], from_xy[1] - to_xy[1]
        self.J("tl.fromTo('%s', { opacity: 0, x: %d, y: %d, scale: 0.2, rotation: %.1f, filter: 'blur(10px)' }, { opacity: 1, x: 0, y: 0, scale: 1, rotation: %.1f, filter: 'blur(0px)', duration: %.2f, ease: 'back.out(1.6)' }, %.3f);" % (sel, dx, dy, rot * 4, rot, dur, t))
    def slide_in(self, sel, land, dx=-230, dur=0.34):
        """out from behind something (a shoulder, with depth) under motion blur, landing on `land`"""
        self.J("tl.set('%s', { opacity: 1, x: %d, rotation: -12, filter: 'blur(12px)' }, %.3f);" % (sel, dx, land - dur - 0.04))
        self.J("tl.to('%s', { x: 0, rotation: 0, filter: 'blur(0px)', duration: %.2f, ease: 'back.out(1.5)' }, %.3f);" % (sel, dur, land - dur))
    def slide_out(self, sel, t, dx=-260):
        self.J("tl.to('%s', { keyframes: [{ x: 14, duration: 0.10, ease: 'power2.out' }, { x: %d, rotation: -14, filter: 'blur(10px)', duration: 0.30, ease: 'power3.in' }] }, %.3f);" % (sel, dx, t))
        self.hide(sel, t + 0.42)
    def drop_in(self, sel, land, h=520):
        """falls in from above with motion blur, lands with a squash on the bottom edge"""
        self.show(sel, land - 0.36)
        self.J("tl.fromTo('%s', { y: -%d, filter: 'blur(14px)', scaleY: 1.18 }, { y: 0, filter: 'blur(0px)', scaleY: 1, duration: 0.34, ease: 'power3.in' }, %.3f);" % (sel, h, land - 0.34))
        self.squash(sel, land, origin="50% 100%")
    def x_slam(self, eid, t):
        """the red X on an icon (made with x_mark=True): anticipation squash, two strokes, the icon greys out"""
        self.J("tl.to('#%s', { scaleX: 1.06, scaleY: 0.92, duration: 0.07, ease: 'power2.out', transformOrigin: '50%% 100%%' }, %.3f);" % (eid, t - 0.08))
        self.draw(eid + "-x1", t, 0.07, "power4.in"); self.draw(eid + "-x2", t + 0.09, 0.07, "power4.in")
        self.J("tl.to('#%s', { scaleX: 1, scaleY: 1, duration: 0.3, ease: 'elastic.out(1, 0.4)' }, %.3f);" % (eid, t + 0.04))
        self.J("tl.fromTo('#%s .ov', { scale: 1.5, transformOrigin: '50%% 50%%' }, { scale: 1, duration: 0.18, ease: 'power3.out', immediateRender: false }, %.3f);" % (eid, t))
        self.J("tl.to('#%s-art', { filter: 'grayscale(1) brightness(.8)', duration: 0.25 }, %.3f);" % (eid, t + 0.2))
    def delete(self, sels, t, gap=0.06):
        """squash flat and vanish, one after another (a deleted comment)"""
        for k, s in enumerate(sels):
            self.J("tl.to('%s', { keyframes: [{ scaleX: 1.12, scaleY: 0.86, duration: 0.07 }, { scaleX: 0, scaleY: 1.2, opacity: 0, filter: 'blur(6px)', duration: 0.16, ease: 'power3.in' }] }, %.3f);" % (s, t + k * gap))
    def exit_fall(self, sel, t):
        """a lift (anticipation), then shrink, tip and fall out under blur"""
        self.J("tl.to('%s', { keyframes: [{ scale: 1.05, y: -12, duration: 0.10, ease: 'power2.out' }, { scale: 0.2, y: 60, rotation: -10, opacity: 0, filter: 'blur(10px)', duration: 0.26, ease: 'power3.in' }] }, %.3f);" % (sel, t))
    def pulse_on_beats(self, sel, a, b, scale=1.05, strong=True):
        """a held element breathes with the music: a heart that beats, a lock that pulses"""
        for t in self.beats_between(a, b, strong):
            self.J("tl.to('%s', { keyframes: [{ scale: %.3f, duration: 0.05 }, { scale: 1, duration: 0.24, ease: 'power2.out' }] }, %.3f);" % (sel, scale, t))
    def count(self, sel, frm, to, t, dur, fmt_commas=True):
        """a number that runs from frm to to (a like count to 0), one proxy tween on the timeline"""
        self.J("""(function () { const el = document.querySelector('%s'); const o = { v: %d };
          tl.fromTo(o, { v: %d }, { v: %d, duration: %.3f, ease: 'power3.in', immediateRender: false,
            onUpdate: function () { el.textContent = Math.round(o.v)%s; } }, %.3f);
          tl.set(el, { textContent: '%s' }, 0); })();""" % (sel, frm, frm, to, dur, ".toLocaleString('en-US')" if fmt_commas else "", t, "{:,}".format(frm) if fmt_commas else frm))

    # ---- catalog ports + clip-world elements (NOTES 14-15) ----------------------------------------------------------
    # Ported from the HyperFrames catalog (`scripts/catalog.py search/fetch`) or proven on a Short, re-timed onto this
    # one timeline, sized for 9:16 and stripped to the house rules (plain text, SubFont, no glow/shadow/stroke).
    def img64(self, path):
        """a local photo as a data URI (B-roll lives in the page; resize to ~600 px first)"""
        import base64
        ext = os.path.splitext(path)[1].lower().lstrip(".").replace("jpg", "jpeg")
        return "data:image/%s;base64,%s" % (ext, base64.b64encode(open(path, "rb").read()).decode())
    def fly_right(self, sel, land, dx=420):
        """in from the right under blur, overshoot, settle on `land`"""
        self.J("tl.fromTo('%s', { opacity: 0, x: %d, rotation: 4, filter: 'blur(14px)' }, { opacity: 1, x: 0, rotation: 0, filter: 'blur(0px)', duration: 0.34, ease: 'back.out(1.6)' }, %.3f);" % (sel, dx, land - 0.34))
    def rise(self, sel, t, dy=24):
        self.J("tl.fromTo('%s', { opacity: 0, y: %d, filter: 'blur(8px)' }, { opacity: 1, y: 0, filter: 'blur(0px)', duration: 0.26, ease: 'power3.out' }, %.3f);" % (sel, dy, t))

    def photo_card(self, eid, src, name, team, bar="linear-gradient(#2B2F38,#111317)", x=70, y=226, w=300, photo_h=336, pos="50% 12%"):
        """B-roll of the person being talked about (NOTES 14): a rounded real photo with a name bar in team colours.
        Approved on clash-06 v3. `src` from img64(); fly_right() it in on the name, slide_out() when the topic moves on."""
        self.front('<div class="el" id="%s" style="left:%dpx;top:%dpx;width:%dpx;height:%dpx;border-radius:26px;overflow:hidden;background:%s">'
                   '<img src="%s" style="display:block;width:%dpx;height:%dpx;object-fit:cover;object-position:%s">'
                   '<div style="height:76px;padding:12px 18px 0;box-sizing:border-box">'
                   '<div style="font:700 27px/1.1 SubFont,sans-serif;color:#FFFFFF;white-space:nowrap">%s</div>'
                   '<div style="font:700 20px/1.3 SubFont,sans-serif;color:rgba(255,255,255,.85);letter-spacing:.1em">%s</div></div></div>'
                   % (eid, x, y, w, photo_h + 76, bar, src, w, photo_h, pos, name, team))

    def type_beat(self, eid, label, lines, times, x=400, top=300, size=110, accent="#FFD400"):
        """kinetic type beside a photo card (the 'THE NIGHT BEFORE / 10 BEERS' beat, approved on clash-06): a small grey
        label rises, then each big line slams on its word. lines = ["JUNIOR +", "SENIOR [YEAR]"] ([..] = accent);
        times = [label_t, line1_t, line2_t, ...]. Returns the element ids for exits (exit_fall each)."""
        ids = ["%s0" % eid]
        self.front('<div class="el" id="%s0" style="left:%dpx;top:%dpx;width:640px;font:700 30px/1 SubFont,sans-serif;color:#C9CDD2;letter-spacing:.12em;white-space:nowrap">%s</div>' % (eid, x, top, label))
        y = top + 50
        for i, line in enumerate(lines):
            html = line.replace("[", '<span style="color:%s">' % accent).replace("]", "</span>")
            self.front('<div class="el" id="%s%d" style="left:%dpx;top:%dpx;width:660px;font:700 %dpx/1 SubFont,sans-serif;color:#FFFFFF;letter-spacing:-.02em;white-space:nowrap">%s</div>' % (eid, i + 1, x, y, size, html))
            ids.append("%s%d" % (eid, i + 1)); y += int(size * 1.04)
        self.rise("#" + ids[0], times[0])
        for i, t in enumerate(times[1:]):
            self.slam("#" + ids[i + 1], t)
        return ["#" + i for i in ids]

    def checklist(self, eid, header, rows, x=396, y=250, w=614):
        """a real-looking notes/checklist card that ticks off each line as it is said (clash-06 v2/v3).
        rows = [(text, t_in, t_check), ...]; header = small grey caps line. One click-soft per tick."""
        body = ""
        for i, (text, t_in, t_ck) in enumerate(rows):
            rid = "%s-r%d" % (eid, i)
            body += ('<div id="%s" style="position:absolute;left:28px;top:%dpx;height:64px;display:flex;align-items:center;gap:18px;opacity:0">'
                     '<svg viewBox="0 0 44 44" width="44" height="44"><circle cx="22" cy="22" r="20" fill="#E5E7EB"/>'
                     '<circle id="%s-on" cx="22" cy="22" r="20" fill="#16A34A" style="opacity:0"/>'
                     '<path id="%s-ck" class="ln" pathLength="100" d="M12 23 L19 30 L32 15" style="stroke:#FFFFFF;stroke-width:5px"/></svg>'
                     '<div style="font:700 38px/1 SubFont,sans-serif;color:#111111;letter-spacing:-.01em">%s</div></div>' % (rid, 66 + i * 68, rid, rid, text))
        self.front('<div class="el" id="%s" style="left:%dpx;top:%dpx;width:%dpx;height:%dpx;border-radius:30px;background:#FFFFFF">'
                   '<div style="position:absolute;left:28px;top:22px;font:700 22px/1 SubFont,sans-serif;color:#6B7280;letter-spacing:.12em">%s</div>%s</div>'
                   % (eid, x, y, w, 96 + len(rows) * 68, header, body))
        self.J("tl.fromTo('#%s', { opacity: 0, x: 60, scale: 0.92, filter: 'blur(10px)' }, { opacity: 1, x: 0, scale: 1, filter: 'blur(0px)', duration: 0.3, ease: 'back.out(1.6)' }, %.3f);" % (eid, rows[0][1] - 0.36))
        for i, (text, t_in, t_ck) in enumerate(rows):
            rid = "%s-r%d" % (eid, i)
            self.J("tl.fromTo('#%s', { opacity: 0, x: -20 }, { opacity: 1, x: 0, duration: 0.24, ease: 'power3.out' }, %.3f);" % (rid, t_in))
            self.J("tl.to('#%s-on', { opacity: 1, duration: 0.08 }, %.3f);" % (rid, t_ck))
            self.draw(rid + "-ck", t_ck + 0.04, 0.16)
            self.J("tl.fromTo('#%s svg', { scale: 0.6, transformOrigin: '50%% 50%%' }, { scale: 1, duration: 0.3, ease: 'back.out(3)', immediateRender: false }, %.3f);" % (rid, t_ck))
            self.sound("click-soft.wav", t_ck, 0.26, 0.32)

    def lower_third(self, eid, kicker, name, t_in, t_out, x=60, y=None, accent="#FFD400", size=64):
        """ported from catalog block `lt-kicker-name`: an accent kicker tag drops in, the name rises, an accent baseline
        draws under it; reverses out. For naming a speaker or a guest the first time they appear. Default spot: the black
        band just above the picture (y = WY - 170), clear of faces and the subtitle line. Text plain (no text-shadow)."""
        y = self.WY - 170 if y is None else y
        self.front('<div class="el" id="%s" style="left:%dpx;top:%dpx;opacity:1;display:flex;flex-direction:column;align-items:flex-start;gap:12px">'
                   '<div style="overflow:hidden"><span id="%s-k" style="display:inline-block;font:700 24px/1 SubFont,sans-serif;color:#111317;background:%s;padding:8px 14px;letter-spacing:.1em;white-space:nowrap">%s</span></div>'
                   '<div id="%s-n" style="font:700 %dpx/1 SubFont,sans-serif;color:#FFFFFF;letter-spacing:-.015em;white-space:nowrap;opacity:0">%s</div>'
                   '<div id="%s-b" style="height:6px;width:100%%;background:%s;border-radius:3px;transform-origin:0%% 50%%"></div></div>'
                   % (eid, x, y, eid, accent, kicker, eid, size, name, eid, accent))
        self.J("tl.fromTo('#%s-k', { y: -44 }, { y: 0, duration: 0.42, ease: 'back.out(2)' }, %.3f);" % (eid, t_in))
        self.J("tl.fromTo('#%s-n', { y: 34, opacity: 0 }, { y: 0, opacity: 1, duration: 0.45, ease: 'back.out(1.5)' }, %.3f);" % (eid, t_in + 0.22))
        self.J("tl.fromTo('#%s-b', { scaleX: 0 }, { scaleX: 1, duration: 0.5, ease: 'power4.out' }, %.3f);" % (eid, t_in + 0.4))
        self.J("tl.to('#%s-b', { scaleX: 0, duration: 0.3, ease: 'power2.in' }, %.3f);" % (eid, t_out))
        self.J("tl.to('#%s-n', { y: -16, opacity: 0, duration: 0.32, ease: 'power2.in' }, %.3f);" % (eid, t_out + 0.05))
        self.J("tl.to('#%s-k', { y: -44, duration: 0.3, ease: 'power2.in' }, %.3f);" % (eid, t_out + 0.07))
        self.hide("#" + eid, t_out + 0.5)

    def post_card(self, eid, name, handle, text, likes, t_in, t_like=None, likes_after=None, avatar=None, x=90, y=230, w=900):
        """ported from catalog block `x-post`: a dark X/Twitter post card (avatar, name, @handle, text, like count) that
        scales in; on t_like the heart fills pink and the count ticks up. Real UI for when someone quotes a post/comment.
        avatar = img64() of a photo, else an initial on a colour. Exit with slide_out / exit_fall."""
        av = ('<img src="%s" style="width:64px;height:64px;border-radius:32px;object-fit:cover">' % avatar if avatar else
              '<div style="width:64px;height:64px;border-radius:32px;background:#1D9BF0;font:700 30px/64px SubFont,sans-serif;color:#FFFFFF;text-align:center">%s</div>' % name[0].upper())
        self.front('<div class="el" id="%s" style="left:%dpx;top:%dpx;width:%dpx;padding:30px 34px 24px;box-sizing:border-box;border-radius:24px;background:#15202B;border:1px solid #38444D">'
                   '<div style="display:flex;gap:16px;align-items:center;margin-bottom:18px">%s<div>'
                   '<div style="font:700 30px/1.1 SubFont,sans-serif;color:#FFFFFF">%s</div><div style="font:700 24px/1.2 SubFont,sans-serif;color:#8B98A5">@%s</div></div></div>'
                   '<div style="font:700 40px/1.2 SubFont,sans-serif;color:#FFFFFF;letter-spacing:-.01em">%s</div>'
                   '<div style="display:flex;align-items:center;gap:12px;margin-top:20px;font:700 26px/1 SubFont,sans-serif;color:#8B98A5">'
                   '<svg viewBox="0 0 24 24" width="30" height="30"><path d="M12 21 C6 16.5 2.5 13.4 2.5 9.4 C2.5 6.6 4.6 4.5 7.3 4.5 C9.2 4.5 10.9 5.5 12 7.1 C13.1 5.5 14.8 4.5 16.7 4.5 C19.4 4.5 21.5 6.6 21.5 9.4 C21.5 13.4 18 16.5 12 21 Z" fill="#8B98A5"/>'
                   '<path id="%s-hf" d="M12 21 C6 16.5 2.5 13.4 2.5 9.4 C2.5 6.6 4.6 4.5 7.3 4.5 C9.2 4.5 10.9 5.5 12 7.1 C13.1 5.5 14.8 4.5 16.7 4.5 C19.4 4.5 21.5 6.6 21.5 9.4 C21.5 13.4 18 16.5 12 21 Z" fill="#F91880" style="opacity:0"/></svg>'
                   '<span id="%s-lk">%s</span></div></div>'
                   % (eid, x, y, w, av, name, handle, text, eid, eid, likes))
        self.J("tl.fromTo('#%s', { opacity: 0, y: 50, scale: 0.9, filter: 'blur(10px)' }, { opacity: 1, y: 0, scale: 1, filter: 'blur(0px)', duration: 0.34, ease: 'back.out(1.6)' }, %.3f);" % (eid, t_in))
        if t_like is not None:
            self.J("tl.to('#%s-hf', { opacity: 1, duration: 0.12 }, %.3f);" % (eid, t_like))
            self.J("tl.fromTo('#%s-hf', { scale: 0.5, transformOrigin: '50%% 50%%' }, { scale: 1, duration: 0.3, ease: 'back.out(3)', immediateRender: false }, %.3f);" % (eid, t_like))
            self.J("tl.to('#%s-lk', { color: '#F91880', duration: 0.12 }, %.3f);" % (eid, t_like))
            if likes_after:
                self.J("tl.set('#%s-lk', { textContent: '%s' }, %.3f);" % (eid, likes_after, t_like))

    # ---- the minimal recipe (NOTES 19-21, approved on clashcam-05) -------------------------------------------------
    def band_broll(self, eid, src, name, sub, t_in, t_out, pos="50% 20%", bar="linear-gradient(#2B2F38,#111317)", x=330, vol=0.09,
                   y=80, w=420, photo_h=460):
        """a B-roll photo card in the black band above the picture: plain fade-up in, fade out, one quiet pop.
        Keep t_out - t_in <= 3 s (NOTES 18). Two side by side: x=110 and x=550. While the hook holds the band, a small
        pair fits above it: y=40, w=260, photo_h=230, x=270 and x=550 (clashcam-03 v3)."""
        self.photo_card(eid, src, name, sub, bar=bar, x=x, y=y, w=w, photo_h=photo_h, pos=pos)
        self.J("tl.fromTo('#%s', { opacity: 0, y: 30 }, { opacity: 1, y: 0, duration: 0.3, ease: 'power2.out' }, %.3f);" % (eid, t_in - 0.15))
        self.J("tl.to('#%s', { opacity: 0, y: -20, duration: 0.25, ease: 'power2.in' }, %.3f);" % (eid, t_out))
        if vol:
            self.sound("pop.wav", t_in, vol, 0.3)

    @staticmethod
    def shot_camera(shots, end, zoomblur=()):
        """gentle camera from the shot list: shots = [(start, (x, y), creep_zoom), ...]; a reset and one slow creep per
        shot; a shot whose start is in `zoomblur` comes in on a zoom-blur instead of a hard reset."""
        ops = []
        for i, (t0, (x, y), z) in enumerate(shots):
            t1 = shots[i + 1][0] if i + 1 < len(shots) else end
            if t0 in zoomblur:
                ops += [["zoomblur", t0, x, y], ["creep", t0 + 0.27, t1 - 0.05, z, x, y]]
            else:
                ops += [["set", t0, 1.0], ["creep", t0 + 0.02, t1 - 0.05, z, x, y]]
        return ops

    # ---- output ---------------------------------------------------------------------------------------------------
    def write(self, captions_path, camera, extra=None):
        """merge the elements, camera and sounds into captions.json (subtitles.py reads it). Warns on sounds < 0.3 s apart."""
        S = json.load(open(captions_path, encoding="utf-8"))
        behind = '<div class="fxl" id="fxbehind"><svg class="ov" viewBox="0 0 1080 1920" width="1080" height="1920">%s</svg>%s</div>' % ("".join(self.rays["behind"]), "".join(self._behind))
        front = DEFS + CSS + '<div class="fxl" id="fx"><svg class="ov" viewBox="0 0 1080 1920" width="1080" height="1920">%s</svg>%s</div>' % ("".join(self.rays["front"]), "".join(self._front))
        S.update({"window": {"y": self.WY, "h": self.WH}, "camera": camera, "sfx": False,
                  "sounds": sorted(self.sounds, key=lambda s: s["at"]), "raw_html": front, "raw_js": "\n        ".join(self.js)})
        here = os.path.dirname(os.path.abspath(captions_path))
        if self._behind or self.rays["behind"]:
            if not os.path.exists(os.path.join(here, "depth", "subject.webm")):
                raise SystemExit("elements behind the people need depth/subject.webm (prep.py --depth)")
            S.update({"subject": "depth/subject.webm", "behind_html": behind})
        S.update(extra or {})
        json.dump(S, open(captions_path, "w", encoding="utf-8"), indent=1)
        at = [s["at"] for s in S["sounds"]]
        close = [(a, b) for a, b in zip(at, at[1:]) if b - a < 0.3]
        print("captions.json: %d camera ops, %d sounds, %d tweens%s" % (len(camera), len(at), len(self.js), ("; SOUNDS UNDER 0.3 s APART: %s" % close) if close else ""))
