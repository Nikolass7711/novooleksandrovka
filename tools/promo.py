#!/usr/bin/env python3
"""Green Park — «живий» монтаж: реальні фото + 3D-візуалізації ремонту.

Можливості: плавні наїзди/панорами, перехід «до/після» шторкою зі світловою лінією, світлові
спалахи, кінетичні титри (слово за словом), теплі світлові відблиски, зерно, віньєтка,
обов'язкові підписи «Візуалізація можливого інтер'єру».

  python3 tools/promo.py promo/master_60_16x9.json [--music renders/music.wav]
"""
import argparse
import json
import math
import os
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_DIR = "/usr/share/fonts/opentype/inter"
F = {
    "display": os.path.join(FONT_DIR, "InterDisplay-Light.otf"),
    "display_med": os.path.join(FONT_DIR, "InterDisplay-Medium.otf"),
    "light": os.path.join(FONT_DIR, "Inter-Light.otf"),
    "medium": os.path.join(FONT_DIR, "Inter-Medium.otf"),
    "semibold": os.path.join(FONT_DIR, "Inter-SemiBold.otf"),
}
CREAM = (247, 243, 234)
LABELS = {
    "interior": "Візуалізація можливого інтер’єру",
    "landscape": "Концепція благоустрою",
}


def smooth(p):
    p = min(1.0, max(0.0, p))
    return p * p * (3 - 2 * p)


def ease_out(p):
    p = min(1.0, max(0.0, p))
    return 1 - (1 - p) ** 3


def ease_io(p):
    p = min(1.0, max(0.0, p))
    return 0.5 - 0.5 * math.cos(math.pi * p)


# ------------------------------------------------------------------ images
_img = {}


def grade_photo(im, warm=0.03, contrast=1.06, sat=1.04, lift=0.0):
    im = ImageEnhance.Contrast(im).enhance(contrast)
    im = ImageEnhance.Color(im).enhance(sat)
    a = np.asarray(im).astype(np.float32) / 255
    a[..., 0] *= 1 + warm
    a[..., 2] *= 1 - warm
    if lift:
        a = a * (1 - lift) + lift
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))


def load(src, W, H, grade):
    key = (src, W, H, json.dumps(grade, sort_keys=True))
    if key in _img:
        return _img[key]
    p = os.path.join(ROOT, src)
    im = ImageOps.exif_transpose(Image.open(p)).convert("RGB")
    iw, ih = im.size
    cover = min(iw / W, ih / H)
    if cover > 1.6:
        s = 1.6 / cover
        im = im.resize((int(iw * s), int(ih * s)), Image.LANCZOS)
    if grade is not False:
        im = grade_photo(im, **(grade or {}))
    _img[key] = im
    return im


def view(im, W, H, cx, cy, z):
    iw, ih = im.size
    asp = W / H
    if iw / ih > asp:
        ch0, cw0 = ih, ih * asp
    else:
        cw0, ch0 = iw, iw / asp
    cw, ch = cw0 / z, ch0 / z
    x0 = min(max(cx * iw - cw / 2, 0), iw - cw)
    y0 = min(max(cy * ih - ch / 2, 0), ih - ch)
    out = im.transform((W, H), Image.EXTENT, (x0, y0, x0 + cw, y0 + ch), Image.BICUBIC)
    return np.asarray(out).astype(np.float32) / 255


def still_frame(s, layer, W, H, p):
    """layer: dict(src, from:[cx,cy,z], to:[cx,cy,z], grade)"""
    im = load(layer["src"], W, H, layer.get("grade"))
    f = layer.get("from", [0.5, 0.5, 1.0])
    t = layer.get("to", [0.5, 0.5, 1.08])
    e = ease_io(p) if s.get("ease", "io") == "io" else p
    cx, cy, z = (f[i] + (t[i] - f[i]) * e for i in range(3))
    return view(im, W, H, cx, cy, z)


# ------------------------------------------------------------------ text
_txt = {}


def word_images(text, font_key, size, color=CREAM, tracking=0.0):
    key = (text, font_key, size, color, tracking)
    if key in _txt:
        return _txt[key]
    fnt = ImageFont.truetype(F[font_key], int(size))
    words = []
    for w in text.split(" "):
        bbox = fnt.getbbox(w)
        tw = int(bbox[2] - bbox[0] + size * 0.1 + tracking * len(w) * size)
        th = int(size * 1.35)
        img = Image.new("RGBA", (tw + 8, th), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        if tracking:
            x = 4
            for ch in w:
                d.text((x - bbox[0], size * 0.08), ch, font=fnt, fill=color + (255,))
                x += fnt.getlength(ch) + tracking * size
        else:
            d.text((4 - bbox[0], size * 0.08), w, font=fnt, fill=color + (255,))
        adv = fnt.getlength(w) + (tracking * len(w) * size if tracking else 0)
        words.append((np.asarray(img).astype(np.float32) / 255, adv))
    space = fnt.getlength(" ") * 1.05
    _txt[key] = (words, space)
    return _txt[key]


def composite(frame, rgba, x, y, alpha=1.0):
    h, w = rgba.shape[:2]
    H, W = frame.shape[:2]
    x, y = int(round(x)), int(round(y))
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    sub = rgba[y0 - y:y1 - y, x0 - x:x1 - x]
    a = sub[..., 3:4] * alpha
    frame[y0:y1, x0:x1] = frame[y0:y1, x0:x1] * (1 - a) + sub[..., :3] * a


def shadow_band(frame, y0, y1, strength=0.35):
    """М'яке затемнення під титром (градієнт по вертикалі)."""
    H = frame.shape[0]
    y0, y1 = max(0, int(y0)), min(H, int(y1))
    if y1 <= y0:
        return
    n = y1 - y0
    prof = np.sin(np.linspace(0, math.pi, n)) ** 1.2 * strength
    frame[y0:y1] *= (1 - prof)[:, None, None]


def draw_kinetic(frame, t, item, W, H, vertical):
    """item: text, t0, t1, style (title|sub|kicker|cta|logo), pos [x,y] у частках, align."""
    t0, t1 = item.get("t0", 0), item.get("t1", 99)
    if t < t0 - 0.01 or t > t1 + 0.6:
        return
    style = item.get("style", "title")
    base = W if vertical else H
    sizes = {"title": 0.105 if vertical else 0.085, "sub": 0.05 if vertical else 0.036,
             "kicker": 0.034 if vertical else 0.024, "cta": 0.085 if vertical else 0.068,
             "logo": 0.13 if vertical else 0.1, "big": 0.16 if vertical else 0.13}
    fk = {"title": "display", "sub": "light", "kicker": "semibold", "cta": "display", "logo": "display_med",
          "big": "display"}[style]
    size = base * sizes[style] * item.get("scale", 1.0)
    tracking = 0.18 if style == "kicker" else 0.0
    words, space = word_images(item["text"].upper() if style == "kicker" else item["text"], fk, size,
                               tuple(item.get("color", CREAM)), tracking)
    maxw = W * (0.84 if vertical else 0.8)
    # розкладка по рядках
    lines, cur, cw = [], [], 0
    for wimg in words:
        ww = wimg[1]
        if cur and cw + space + ww > maxw:
            lines.append((cur, cw))
            cur, cw = [], 0
        cw += (space if cur else 0) + ww
        cur.append(wimg)
    if cur:
        lines.append((cur, cw))
    lh = size * 1.18
    px, py = item.get("pos", [0.07, 0.72] if not vertical else [0.5, 0.6])
    align = item.get("align", "center" if vertical else "left")
    total_h = lh * len(lines)
    y = py * H - total_h / 2
    if item.get("band", True) and style in ("title", "sub", "cta", "big", "logo"):
        a_band = min(1, max(0, (t - t0) / 0.5)) * min(1, max(0, (t1 + 0.5 - t) / 0.5))
        if a_band > 0:
            shadow_band(frame, y - lh * 1.2, y + total_h + lh * 1.2, 0.38 * a_band)
    k = 0
    stagger = item.get("stagger", 0.07)
    for li, (ws, lw) in enumerate(lines):
        x = px * W - (lw / 2 if align == "center" else 0)
        for wimg, adv in ws:
            st = t0 + k * stagger
            pin = ease_out((t - st) / 0.55)
            pout = 1 - smooth((t - t1) / 0.45)
            a = pin * pout
            if a > 0.002:
                dy = (1 - pin) * size * 0.45 - (1 - pout) * size * 0.2
                composite(frame, wimg, x, y + li * lh + dy, a)
            x += adv + space
            k += 1
    if item.get("rule"):
        rp = ease_out((t - t0 - 0.2) / 0.8) * (1 - smooth((t - t1) / 0.4))
        if rp > 0:
            rw = int(W * 0.12 * rp)
            ry = int(y + total_h + lh * 0.25)
            rx = int(px * W - (rw / 2 if align == "center" else 0))
            frame[ry:ry + max(2, int(base * 0.0025)), rx:rx + rw] = np.array(CREAM) / 255


_lab = {}


def draw_label(frame, text, W, H, vertical, alpha=1.0):
    key = (text, W, H)
    if key not in _lab:
        base = W if vertical else H
        fnt = ImageFont.truetype(F["medium"], int(base * (0.026 if vertical else 0.021)))
        tw = fnt.getlength(text)
        pad = fnt.size * 0.65
        img = Image.new("RGBA", (int(tw + 2 * pad), int(fnt.size + 1.5 * pad)), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([0, 0, img.size[0] - 1, img.size[1] - 1], radius=img.size[1] / 2, fill=(18, 20, 18, 140))
        d.text((pad, pad * 0.6), text, font=fnt, fill=CREAM + (240,))
        arr = np.asarray(img).astype(np.float32) / 255
        if vertical:
            pos = ((W - img.size[0]) / 2, H * 0.115)
        else:
            pos = (W * 0.955 - img.size[0], H * 0.055)
        _lab[key] = (arr, pos)
    arr, pos = _lab[key]
    composite(frame, arr, pos[0], pos[1], alpha)


# ------------------------------------------------------------------ effects
class FX:
    def __init__(self, W, H, seed=3):
        self.W, self.H = W, H
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        self.xx, self.yy = xx / W, yy / H
        cx, cy = self.xx - 0.5, (self.yy - 0.5) * H / W
        r = np.sqrt(cx * cx + cy * cy)
        self.vignette = (1 - 0.32 * np.clip((r - 0.28) / 0.5, 0, 1) ** 1.6)[..., None]
        self.rng = np.random.default_rng(seed)
        self.grain_bank = [self.rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32) for _ in range(6)]

    def leak(self, frame, t, strength, hue=(1.0, 0.62, 0.32)):
        if strength <= 0:
            return frame
        cx = 0.15 + 0.7 * (0.5 + 0.5 * math.sin(t * 0.37))
        cy = 0.2 + 0.25 * math.sin(t * 0.23 + 1)
        d = ((self.xx - cx) ** 2 + ((self.yy - cy) * self.H / self.W) ** 2)
        g = np.exp(-d / 0.06)[..., None] * strength
        col = np.array(hue, dtype=np.float32)
        return 1 - (1 - frame) * (1 - g * col)  # screen

    def flash(self, frame, a):
        if a <= 0:
            return frame
        col = np.array([1.0, 0.93, 0.82], dtype=np.float32)
        return frame * (1 - a) + col * a

    def wipe(self, A, B, p, angle=-18, soft=0.05, glow=True):
        """Шторка «до → після»: лінія рухається зліва направо під кутом, зі світлим краєм."""
        a = math.radians(angle)
        u = self.xx * math.cos(a) + self.yy * math.sin(a) * self.H / self.W
        u = (u - u.min()) / (u.max() - u.min())
        pos = -soft + (1 + 2 * soft) * p
        m = np.clip((pos - u) / soft + 0.5, 0, 1)[..., None]
        out = A * (1 - m) + B * m
        if glow and 0 < p < 1:
            g = np.exp(-((u - pos) / 0.012) ** 2)[..., None] * 0.85
            out = 1 - (1 - out) * (1 - g * np.array([1.0, 0.9, 0.75], dtype=np.float32))
        return out

    def grain(self, frame, k, amount=0.011):
        g = self.grain_bank[k % len(self.grain_bank)]
        g = np.repeat(np.repeat(g, 2, 0), 2, 1)[:self.H, :self.W, None]
        return frame + g * amount * (0.4 + 0.6 * frame)


# ------------------------------------------------------------------ render
def shot_image(s, t_rel, W, H):
    p = t_rel / s["dur"]
    if s["kind"] == "card":
        col = np.array(s.get("color", [0.11, 0.13, 0.11]), dtype=np.float32)
        return np.ones((H, W, 3), np.float32) * col
    if s["kind"] == "beforeafter":
        A = still_frame(s, s["before"], W, H, p)
        B = still_frame(s, s["after"], W, H, p)
        w0, w1 = s.get("wipe", [0.3, 0.75])
        return ("wipe", A, B, smooth((p - w0) / (w1 - w0)))
    return still_frame(s, s, W, H, p)


def render(tl, out, music=None):
    W, H, fps = tl["w"], tl["h"], tl.get("fps", 25)
    vertical = H > W
    fx = FX(W, H)
    shots = tl["shots"]
    t = 0.0
    for i, s in enumerate(shots):
        x = s.get("xfade", 0.0) if i else 0.0
        t -= x
        s["_t0"] = t
        t += s["dur"]
    total = t
    n = int(round(total * fps))
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps),
           "-i", "-"]
    if music:
        cmd += ["-i", music, "-af", f"afade=t=out:st={total - 2.5}:d=2.5", "-c:a", "aac", "-b:a", "192k", "-shortest"]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "20", "-maxrate", "16M", "-bufsize", "32M", "-pix_fmt", "yuv420p", "-colorspace", "bt709",
            "-color_primaries", "bt709", "-color_trc", "bt709", "-movflags", "+faststart", out]
    enc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for fi in range(n):
        tt = fi / fps
        act = [s for s in shots if s["_t0"] <= tt < s["_t0"] + s["dur"]] or [shots[-1]]

        def img_of(s):
            r = shot_image(s, tt - s["_t0"], W, H)
            if isinstance(r, tuple):
                return fx.wipe(r[1], r[2], r[3], angle=s.get("angle", -18))
            return r

        frame = img_of(act[0])
        lab_a = 1.0
        if len(act) > 1:
            b = act[1]
            x = max(1e-6, b.get("xfade", 0.0))
            a = smooth((tt - b["_t0"]) / x)
            tr = b.get("trans", "dissolve")
            fb = img_of(b)
            if tr == "flash":
                frame = fx.flash(frame * (1 - a) + fb * a, math.sin(math.pi * a) * 0.75)
            elif tr == "push":
                off = int(W * a)
                frame = np.concatenate([frame[:, off:], fb[:, :off]], axis=1) if off > 0 else frame
            else:
                frame = frame * (1 - a) + fb * a
        # підписи: показуємо, якщо активний кадр (або той, що з'являється) — візуалізація
        for s in act:
            lab = s.get("label")
            if lab:
                tl_ = tt - s["_t0"]
                la = 1.0
                if s["kind"] == "beforeafter":
                    w0, _ = s.get("wipe", [0.3, 0.75])
                    la = smooth((tl_ / s["dur"] - w0) / 0.08)
                draw_label(frame, LABELS.get(lab, lab), W, H, vertical, la)
                break
        for s in shots:
            for item in s.get("text", []):
                it = dict(item)
                it["t0"] = s["_t0"] + item.get("t0", 0)
                it["t1"] = s["_t0"] + item.get("t1", s["dur"] - 0.4)
                draw_kinetic(frame, tt, it, W, H, vertical)
        leak = tl.get("leak", 0.18)
        for s in act:
            leak = s.get("leak", leak)
        frame = fx.leak(frame, tt, leak)
        dim = 1.0
        for s in act:
            dim = s.get("dim", dim)
        frame = frame * fx.vignette * dim
        frame = fx.grain(frame, fi)
        if tt < 0.6:
            frame = frame * smooth(tt / 0.6)
        if tt > total - 0.8:
            frame = frame * smooth((total - tt) / 0.8)
        enc.stdin.write((np.clip(frame, 0, 1) * 255).astype(np.uint8).tobytes())
    enc.stdin.close()
    enc.wait()
    return total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("timelines", nargs="+")
    ap.add_argument("--music")
    ap.add_argument("--outdir", default=os.path.join(ROOT, "renders", "promo"))
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    for p in a.timelines:
        tl = json.load(open(p, encoding="utf-8"))
        name = os.path.splitext(os.path.basename(p))[0]
        out = os.path.join(a.outdir, name + ".mp4")
        d = render(tl, out, a.music)
        print(f"{name}: {d:.1f} s → {out}")


if __name__ == "__main__":
    main()
