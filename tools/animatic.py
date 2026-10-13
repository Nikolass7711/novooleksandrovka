#!/usr/bin/env python3
"""Green Park — рендер аніматика/чорнового монтажу з таймлайну JSON.

Таймлайн описує кадри (shots). Типи кадрів:
  photo  — реальне фото з assets/photos, плавний наїзд/панорама (Ken Burns).
  video  — реальне відео з assets/video (in/out). Якщо файлу немає — картка-заглушка.
  ai     — місце для AI-візуалізації: показує реальний вихідний ракурс (знебарвлений)
           з описом, що має бути згенеровано. У фінальній збірці замінюється рендером
           (поле "render": шлях до готового зображення/відео в assets/ai).
  gap    — прогалина в матеріалі: картка з переліком, що потрібно дознімати.
  card   — фінальна/титрова картка на тлі фото або кольору.

Запуск:
  python3 tools/animatic.py timelines/master_90_16x9.json            # mp4 + csv + srt
  python3 tools/animatic.py timelines/*.json --release                # без службових міток
"""
import argparse
import csv
import json
import math
import os
import subprocess

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PHOTOS = os.path.join(ROOT, "assets", "photos")
VIDEOS = os.path.join(ROOT, "assets", "video")
AI_DIR = os.path.join(ROOT, "assets", "ai")
RENDERS = os.path.join(ROOT, "renders")

FONT_DIR = "/usr/share/fonts/opentype/inter"
FONTS = {
    "display": os.path.join(FONT_DIR, "InterDisplay-Light.otf"),
    "light": os.path.join(FONT_DIR, "Inter-Light.otf"),
    "medium": os.path.join(FONT_DIR, "Inter-Medium.otf"),
    "semibold": os.path.join(FONT_DIR, "Inter-SemiBold.otf"),
}

TEXT = (246, 243, 236)
AMBER = (232, 190, 110)
CARD_BG = (30, 35, 31)

# Обов'язкові підписи (на весь час кадру) — див. docs/05_post_spec.md
LABELS = {
    "interior": "Візуалізація можливого інтер’єру",
    "landscape": "Концепція благоустрою",
    "visual": "Візуалізація",
    "people": "Ілюстративна сцена",
}


def font(kind, size):
    return ImageFont.truetype(FONTS[kind], max(8, int(size)))


def ease(p, kind="sine"):
    p = min(1.0, max(0.0, p))
    if kind == "linear":
        return p
    return 0.5 - 0.5 * math.cos(math.pi * p)


# ---------------------------------------------------------------- grading
def grade(img, g):
    """М'яка «теплая європейська» корекція фото з iPhone (SDR-базовий шар HEIC)."""
    g = g or {}
    warm = g.get("warm", 0.025)
    img = ImageEnhance.Contrast(img).enhance(g.get("contrast", 1.04))
    img = ImageEnhance.Color(img).enhance(g.get("sat", 1.03))
    img = ImageEnhance.Brightness(img).enhance(g.get("bright", 1.0))
    if warm:
        r, gg, b = img.split()
        r = r.point(lambda v: min(255, int(v * (1 + warm))))
        b = b.point(lambda v: int(v * (1 - warm)))
        img = Image.merge("RGB", (r, gg, b))
    return img


_cache = {}


def load_photo(name, out_w, out_h, g=None, path=None):
    key = (name, out_w, out_h, json.dumps(g, sort_keys=True), path)
    if key in _cache:
        return _cache[key]
    p = path or os.path.join(PHOTOS, name + ".jpg")
    img = ImageOps.exif_transpose(Image.open(p)).convert("RGB")
    # масштаб: кадр «cover» при zoom=1 має бути ~1.35x від вихідного розміру
    W, H = img.size
    cover = min(W / out_w, H / out_h)  # px джерела на px виходу при zoom=1
    target = 1.35
    if cover > target:
        s = target / cover
        img = img.resize((max(1, int(W * s)), max(1, int(H * s))), Image.LANCZOS)
    img = grade(img, g)
    _cache[key] = img
    return img


def crop_rect(img, out_w, out_h, cx, cy, zoom):
    W, H = img.size
    aspect = out_w / out_h
    if W / H > aspect:
        ch0, cw0 = H, H * aspect
    else:
        cw0, ch0 = W, W / aspect
    cw, ch = cw0 / zoom, ch0 / zoom
    x0 = min(max(cx * W - cw / 2, 0), W - cw)
    y0 = min(max(cy * H - ch / 2, 0), H - ch)
    return (x0, y0, x0 + cw, y0 + ch)


MOVES = {
    # (from, to): [cx, cy, zoom]
    "static": ([0.5, 0.5, 1.02], [0.5, 0.5, 1.02]),
    "push": ([0.5, 0.5, 1.00], [0.5, 0.5, 1.10]),
    "push-slow": ([0.5, 0.5, 1.00], [0.5, 0.5, 1.05]),
    "pull": ([0.5, 0.5, 1.10], [0.5, 0.5, 1.00]),
    "pan-r": ([0.46, 0.5, 1.08], [0.54, 0.5, 1.08]),
    "pan-l": ([0.54, 0.5, 1.08], [0.46, 0.5, 1.08]),
    "rise": ([0.5, 0.56, 1.08], [0.5, 0.46, 1.08]),
}


def move_params(shot):
    m = shot.get("move", "push-slow")
    if isinstance(m, dict):
        f, t = m["from"], m["to"]
    else:
        f, t = MOVES[m]
    fx = shot.get("focus")
    if fx and not isinstance(m, dict):  # зсув пресету на точку інтересу
        f = [f[0] - 0.5 + fx[0], f[1] - 0.5 + fx[1], f[2]]
        t = [t[0] - 0.5 + fx[0], t[1] - 0.5 + fx[1], t[2]]
    return f, t


# ---------------------------------------------------------------- text
def wrap(draw, text, fnt, max_w):
    out = []
    for para in text.split("\n"):
        words, line = para.split(" "), ""
        for w in words:
            test = (line + " " + w).strip()
            if draw.textlength(test, font=fnt) <= max_w or not line:
                line = test
            else:
                out.append(line)
                line = w
        out.append(line)
    return out


_text_cache = {}


def text_layer(W, H, text, style, vertical):
    """Повертає RGBA-шар W×H з текстом у безпечній зоні."""
    key = (W, H, text, style, vertical)
    if key in _text_cache:
        return _text_cache[key]
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    base = W if vertical else H
    if style == "main":
        fnt = font("display", base * (0.082 if vertical else 0.066))
    elif style == "sub":
        fnt = font("light", base * (0.046 if vertical else 0.034))
    elif style == "cta":
        fnt = font("display", base * (0.084 if vertical else 0.07))
    elif style == "logo":
        fnt = font("semibold", base * (0.10 if vertical else 0.085))
    else:  # small / info
        fnt = font("light", base * (0.036 if vertical else 0.026))

    margin_x = W * (0.08 if vertical else 0.07)
    lines = wrap(d, text, fnt, W - 2 * margin_x)
    lh = fnt.size * 1.22
    block_h = lh * len(lines)
    if vertical:  # центр; поза зонами інтерфейсу соцмереж (верх 12%, низ 22%)
        anchor_y = {"main": 0.58, "sub": 0.66, "cta": 0.50, "logo": 0.40, "small": 0.70}[style]
        y = H * anchor_y - block_h / 2
        align = "center"
    else:
        anchor_y = {"main": 0.70, "sub": 0.80, "cta": 0.48, "logo": 0.36, "small": 0.86}[style]
        y = H * anchor_y - block_h / 2
        align = "center" if style in ("cta", "logo") else "left"

    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if style in ("main", "sub", "cta", "logo"):
        # м'яка затемнена смуга під текстом для читабельності на будь-якому тлі
        top, bot = int(y - block_h * 0.9), int(y + block_h * 1.9)
        band_h = max(2, bot - top)
        prof = Image.new("L", (1, band_h))
        prof.putdata([int(70 * math.sin(math.pi * i / (band_h - 1))) for i in range(band_h)])
        shadow.paste(Image.new("RGBA", (W, band_h), (10, 12, 10, 255)), (0, top), prof.resize((W, band_h)))
    sd = ImageDraw.Draw(shadow)
    for i, ln in enumerate(lines):
        tw = d.textlength(ln, font=fnt)
        x = (W - tw) / 2 if align == "center" else margin_x
        yy = y + i * lh
        sd.text((x, yy + fnt.size * 0.04), ln, font=fnt, fill=(0, 0, 0, 150))
        d.text((x, yy), ln, font=fnt, fill=TEXT + (255,))
    shadow = shadow.filter(ImageFilter.GaussianBlur(fnt.size * 0.18))
    out = Image.alpha_composite(shadow, lay)
    _text_cache[key] = out
    return out


def label_layer(W, H, text, vertical):
    key = ("label", W, H, text, vertical)
    if key in _text_cache:
        return _text_cache[key]
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    fnt = font("medium", (W if vertical else H) * (0.030 if vertical else 0.024))
    tw = d.textlength(text, font=fnt)
    pad = fnt.size * 0.6
    if vertical:
        x1 = (W + tw) / 2 + pad
        y0 = H * 0.13
    else:
        x1 = W * 0.95
        y0 = H * 0.06
    x0 = x1 - tw - 2 * pad
    d.rounded_rectangle([x0, y0, x1, y0 + fnt.size + 1.4 * pad], radius=fnt.size * 0.5, fill=(20, 22, 20, 150))
    d.text((x0 + pad, y0 + pad * 0.62), text, font=fnt, fill=TEXT + (255,))
    _text_cache[key] = lay
    return lay


def dev_layer(W, H, text):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    fnt = font("medium", max(W, H) * 0.011)
    tw = d.textlength(text, font=fnt)
    d.rectangle([0, 0, tw + 16, fnt.size + 12], fill=(0, 0, 0, 170))
    d.text((8, 5), text, font=fnt, fill=(255, 220, 90, 255))
    return lay


# ---------------------------------------------------------------- cards
def info_card(W, H, kicker, title, body, bg=None, color=AMBER):
    if bg is None:
        img = Image.new("RGB", (W, H), CARD_BG)
    else:
        img = bg.copy()
    d = ImageDraw.Draw(img, "RGBA")
    vertical = H > W
    base = W if vertical else H
    mx = W * 0.08
    box_w = W - 2 * mx
    fk = font("semibold", base * (0.034 if vertical else 0.028))
    ft = font("display", base * (0.06 if vertical else 0.05))
    fb = font("light", base * (0.034 if vertical else 0.028))
    lines_t = wrap(d, title, ft, box_w)
    lines_b = wrap(d, body, fb, box_w) if body else []
    h = fk.size * 1.8 + len(lines_t) * ft.size * 1.2 + fb.size * 0.8 + len(lines_b) * fb.size * 1.35
    y = (H - h) / 2
    pad = base * 0.04
    d.rounded_rectangle([mx - pad, y - pad, W - mx + pad, y + h + pad], radius=pad * 0.6, fill=(15, 18, 16, 205))
    d.text((mx, y), kicker, font=fk, fill=color + (255,))
    y += fk.size * 1.8
    for ln in lines_t:
        d.text((mx, y), ln, font=ft, fill=TEXT + (255,))
        y += ft.size * 1.2
    y += fb.size * 0.8
    for ln in lines_b:
        d.text((mx, y), ln, font=fb, fill=(215, 212, 204, 255))
        y += fb.size * 1.35
    return img


def ai_base(img):
    g = ImageOps.grayscale(img).convert("RGB")
    g = ImageEnhance.Brightness(g).enhance(0.55)
    tint = Image.new("RGB", g.size, (60, 80, 70))
    return Image.blend(g, tint, 0.25)


# ---------------------------------------------------------------- video
class VideoReader:
    def __init__(self, path, t_in, dur, W, H, fps, stabilize):
        hdr = probe_hdr(path)
        vf = []
        if hdr:
            vf.append("zscale=t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,"
                      "tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p")
        if stabilize:
            vf.append("deshake")
        vf.append(f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H}")
        vf.append(f"fps={fps}")
        cmd = ["ffmpeg", "-v", "error", "-ss", str(t_in), "-t", str(dur + 0.5), "-i", path,
               "-vf", ",".join(vf), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
        self.p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        self.size = (W, H)
        self.last = Image.new("RGB", (W, H), (0, 0, 0))

    def next(self):
        n = self.size[0] * self.size[1] * 3
        buf = self.p.stdout.read(n)
        if len(buf) == n:
            self.last = Image.frombytes("RGB", self.size, buf)
        return self.last

    def close(self):
        try:
            self.p.kill()
        except Exception:
            pass


def probe_hdr(path):
    try:
        out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                              "stream=color_transfer", "-of", "csv=p=0", path],
                             capture_output=True, text=True).stdout.strip()
        return out in ("arib-std-b67", "smpte2084")
    except Exception:
        return False


def find_video(name):
    for ext in ("", ".MOV", ".mov", ".mp4", ".MP4"):
        p = os.path.join(VIDEOS, name + ext)
        if os.path.isfile(p):
            return p
    return None


def find_ai(shot):
    r = shot.get("render")
    if r:
        p = os.path.join(ROOT, r)
        if os.path.isfile(p):
            return p
    return None


# ---------------------------------------------------------------- render
class Renderer:
    def __init__(self, tl, release):
        self.tl = tl
        self.W, self.H = tl["w"], tl["h"]
        self.fps = tl.get("fps", 25)
        self.vertical = self.H > self.W
        self.release = release
        self.readers = {}
        t = 0.0
        for i, s in enumerate(tl["shots"]):
            x = s.get("xfade", 0.0) if i else 0.0
            t -= x
            s["_start"] = t
            t += s["dur"]
        self.total = t

    def shot_frame(self, s, t_rel):
        W, H = self.W, self.H
        p = t_rel / s["dur"]
        kind = s["kind"]
        if kind == "video":
            path = find_video(s["src"])
            if path:
                key = id(s)
                if key not in self.readers:
                    self.readers[key] = VideoReader(path, s.get("in", 0), s["dur"], W, H, self.fps,
                                                    s.get("stabilize", True))
                frame = self.readers[key].next()
            else:
                bg = None
                if s.get("still"):
                    bg = ai_base(self.photo_frame(s["still"], s, p))
                frame = info_card(W, H, "ВІДЕО-ВИХІДНИК · " + s["src"],
                                  s.get("desc", ""),
                                  "Підставляється з assets/video/ (in "
                                  + f"{s.get('in', 0):.1f} c, {s['dur']:.1f} c). " + s.get("need", ""),
                                  bg=bg, color=(140, 200, 230))
        elif kind == "photo":
            frame = self.photo_frame(s["src"], s, p)
        elif kind == "ai":
            rp = find_ai(s)
            if rp and rp.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                frame = self.photo_frame(None, s, p, path=rp)
            else:
                base = ai_base(self.photo_frame(s.get("src"), s, p)) if (s.get("src") or s.get("path")) else None
                frame = info_card(W, H, "AI-КАДР · " + s["id"] + (" · ракурс " + s["src"] if s.get("src") else ""),
                                  s.get("desc", ""), s.get("prompt_ref", ""), bg=base, color=AMBER)
        elif kind == "gap":
            frame = info_card(W, H, "ПОТРІБЕН МАТЕРІАЛ · " + s["id"], s.get("desc", ""), s.get("need", ""),
                              color=(235, 120, 100))
        elif kind == "card":
            if s.get("src") or s.get("path"):
                frame = self.photo_frame(s.get("src"), s, p)
                frame = ImageEnhance.Brightness(frame).enhance(s.get("dim", 0.6))
            else:
                frame = Image.new("RGB", (W, H), CARD_BG)
        else:
            raise ValueError(kind)

        frame = frame.convert("RGBA")
        lab = s.get("label")
        if lab:
            frame = Image.alpha_composite(frame, label_layer(W, H, LABELS.get(lab, lab), self.vertical))
        for ti in s.get("titles", []):
            a = self.fade_alpha(t_rel, ti.get("t0", 0), ti.get("t1", s["dur"]),
                                ti.get("fade_in", ti.get("fade", 0.45)), ti.get("fade_out", ti.get("fade", 0.45)))
            if a <= 0:
                continue
            lay = text_layer(W, H, ti["text"], ti.get("style", "main"), self.vertical)
            if a < 1:
                lay = lay.copy()
                lay.putalpha(lay.getchannel("A").point(lambda v: int(v * a)))
            frame = Image.alpha_composite(frame, lay)
        if not self.release:
            status = s.get("status", "")
            src = s.get("src", "") or "—"
            frame = Image.alpha_composite(frame, dev_layer(W, H, f"{s['id']} · {kind.upper()} · {src} · {status}"))
        return frame.convert("RGB")

    @staticmethod
    def fade_alpha(t, t0, t1, fi, fo):
        if t < t0 or t > t1:
            return 0.0
        return min(1.0, (t - t0) / fi if fi else 1.0, (t1 - t) / fo if fo else 1.0)

    def photo_frame(self, name, s, p, path=None):
        if path is None and s.get("path"):
            path = os.path.join(ROOT, s["path"])
        img = load_photo(name, self.W, self.H, s.get("grade"), path=path)
        f, t = move_params(s)
        e = ease(p, s.get("ease", "sine"))
        cx, cy, z = (f[i] + (t[i] - f[i]) * e for i in range(3))
        box = crop_rect(img, self.W, self.H, cx, cy, z)
        return img.transform((self.W, self.H), Image.EXTENT, box, Image.BICUBIC)

    def render(self, out_mp4):
        W, H, fps = self.W, self.H, self.fps
        n = int(round(self.total * fps))
        cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
               "-r", str(fps), "-i", "-", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
               "-shortest", "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p",
               "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
               "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", out_mp4]
        enc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        shots = self.tl["shots"]
        for fi in range(n):
            t = fi / fps
            active = [s for s in shots if s["_start"] <= t < s["_start"] + s["dur"]]
            if not active:
                active = [shots[-1]]
            frame = self.shot_frame(active[0], t - active[0]["_start"])
            if len(active) > 1:
                b = active[1]
                x = max(1e-6, b.get("xfade", 0.0))
                a = min(1.0, (t - b["_start"]) / x)
                frame = Image.blend(frame, self.shot_frame(b, t - b["_start"]), a)
            # закрити відеоридери кадрів, що завершились
            for s in shots:
                if id(s) in self.readers and t >= s["_start"] + s["dur"]:
                    self.readers.pop(id(s)).close()
            enc.stdin.write(frame.tobytes())
        enc.stdin.close()
        enc.wait()


# ---------------------------------------------------------------- tables
def tc(t, fps=25):
    t = max(0.0, t)
    m, s = divmod(t, 60)
    return f"{int(m):02d}:{s:05.2f}"


PROCESS = {
    "photo": "стабілізація не потрібна; кольорокорекція; м'який наїзд/паралакс",
    "video": "HDR→Rec.709, стабілізація, кольорокорекція",
    "ai": "AI-візуалізація з того ж ракурсу (див. docs/04_ai_prompts.md)",
    "gap": "дознімати / отримати від замовника",
    "card": "титр/логотип на монтажі",
}


def write_tables(tl, base):
    rows = []
    for s in tl["shots"]:
        titles = " / ".join(t["text"].replace("\n", " ") for t in s.get("titles", []))
        lab = LABELS.get(s.get("label"), s.get("label") or "")
        rows.append({
            "shot": s["id"],
            "in": tc(s["_start"]),
            "out": tc(s["_start"] + s["dur"]),
            "dur_s": f"{s['dur']:.1f}",
            "kind": s["kind"],
            "source": s.get("src", ""),
            "object": s.get("object", tl.get("object", "")),
            "processing": s.get("process", PROCESS[s["kind"]]),
            "titles": titles,
            "label": lab,
            "status": s.get("status", ""),
            "note": s.get("desc", ""),
        })
    with open(base + ".csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    vo = tl.get("vo", [])
    if vo:
        with open(base + "_vo.srt", "w", encoding="utf-8") as f:
            for i, v in enumerate(vo, 1):
                def s(t):
                    h, r = divmod(t, 3600)
                    m, sec = divmod(r, 60)
                    return f"{int(h):02d}:{int(m):02d}:{int(sec):02d},{int(round((sec % 1) * 1000)):03d}"
                f.write(f"{i}\n{s(v['start'])} --> {s(v['end'])}\n{v['text']}\n\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("timelines", nargs="+")
    ap.add_argument("--release", action="store_true", help="без службових міток (для показу)")
    ap.add_argument("--tables-only", action="store_true")
    a = ap.parse_args()
    os.makedirs(RENDERS, exist_ok=True)
    for path in a.timelines:
        with open(path, encoding="utf-8") as f:
            tl = json.load(f)
        r = Renderer(tl, a.release)
        name = os.path.splitext(os.path.basename(path))[0]
        base = os.path.join(RENDERS, name)
        write_tables(tl, base)
        print(f"{name}: {r.total:.1f} s, {len(tl['shots'])} кадрів")
        if not a.tables_only:
            r.render(base + ("_release" if a.release else "_animatic") + ".mp4")


if __name__ == "__main__":
    main()
