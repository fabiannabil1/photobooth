#!/usr/bin/env python3
"""Rakit frame Promahadesa lewat PhotoCraft (layer .pcraft bisa diedit), lalu lubangi slot foto.

Tiap frame: <id>-<layout>.webp di public/frames + sumber .pcraft di ~/Pictures/PhotoCraft/photobooth_promaha,
dan geometri slot foto/teks di src/js/promahaFrames.json.
"""
import json, os, random, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw, ImageEnhance

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
WORK = "/home/bian/Pictures/PhotoCraft/photobooth_promaha"
A = f"{WORK}/assets"
GEN = f"{WORK}/assets/gen"
TMP = f"{WORK}/_tmp"
OUT = f"{ROOT}/public/frames"
CLI = "/home/bian/.local/bin/photocraft-cli"
for d in (GEN, TMP, OUT, f"{WORK}/sumber"):
    os.makedirs(d, exist_ok=True)

NAVY, DEEP, TELANG, SKY = "#0E1F4D", "#081434", "#2747C7", "#BFE4F7"
LIME, LEAF, GOLD, CREAM, WHITE = "#A8CF45", "#3C8D2F", "#D9B24C", "#FFF8E7", "#FFFFFF"
AMBER, BLUE = "#F2B441", "#0D57A0"
LAYOUTS = {"4-cut": (640, 1920, 1, 4, 1.0), "grid-2x2": (1200, 1300, 2, 2, 1.45), "single": (800, 900, 1, 1, 1.15)}
SIZE_CACHE = {}


def size_of(path):
    if path not in SIZE_CACHE:
        with Image.open(path) as im:
            SIZE_CACHE[path] = im.size
    return SIZE_CACHE[path]


class Doc:
    """Daftar perintah PhotoCraft, terpisah antara lapisan di bawah foto dan di atas foto."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.under, self.over = [], []
        self.cur = self.under

    def top(self):
        self.cur = self.over

    def cmd(self, cid, **p):
        self.cur.append((cid, p))

    def rect(self, x, y, w, h, fill, r=0, stroke=None, sw=0, name=None, opacity=None):
        p = dict(kind="roundedRect" if r else "rect", rect=[x, y, w, h], fill=fill, name=name or "bidang")
        if r:
            p["radii"] = r
        if stroke:
            p["stroke"] = dict(width=sw, color=stroke, align="inside")
        self.cmd("shape.create", **p)
        if opacity is not None:
            self.cmd("layer.setProps", opacity=opacity)

    def ellipse(self, cx, cy, rx, ry, fill, stroke=None, sw=0, opacity=None, name="lingkaran"):
        p = dict(kind="ellipse", rect=[cx - rx, cy - ry, rx * 2, ry * 2], fill=fill, name=name)
        if stroke:
            p["stroke"] = dict(width=sw, color=stroke, align="center")
        self.cmd("shape.create", **p)
        if opacity is not None:
            self.cmd("layer.setProps", opacity=opacity)

    def img(self, path, cx, cy, w=None, h=None, rot=0, shadow=None, opacity=None, name=None):
        if not path.startswith("/"):
            path = f"{A}/{path}.png"
        iw, ih = size_of(path)
        scale = 100 * (w / iw if w else h / ih)
        self.cmd("file.placeEmbedded", path=path, scale=round(scale, 3), center=[cx, cy], fit=False)
        self.cmd("layer.setProps", name=name or os.path.basename(path).split(".")[0])
        if rot:
            self.cmd("edit.transform", rotate=rot)
        if opacity is not None:
            self.cmd("layer.setProps", opacity=opacity)
        if shadow:
            self.cmd("layer.layerStyle.dropShadow", color="#050A1E", opacity=shadow, distance=6, size=14, angle=90)

    def bottom_img(self, path, cx, bottom, h=None, w=None, **k):
        if not path.startswith("/"):
            path = f"{A}/{path}.png"
        iw, ih = size_of(path)
        hh = h if h else w * ih / iw
        self.img(path, cx, bottom - hh / 2, w=w, h=h, **k)

    def text(self, x, y, s, size, color=WHITE, weight=700, align="left", track=0, font="Montserrat", name=None, rot=0):
        self.cmd("type.create", x=x, y=y, text=s, font=font, weight=weight, size=size, color=color,
                 align=align, tracking=track, name=name or s[:24])
        if rot:
            self.cmd("edit.transform", rotate=rot)

    def cover(self, path, x=0, y=0, w=None, h=None, pos=0.5, tint=None, name=None):
        """Letakkan gambar menutup bidang, dipotong dulu supaya ukuran pas."""
        w, h = w or self.w, h or self.h
        src = path if path.startswith("/") else (f"{A}/{path}.png")
        key = f"{GEN}/cov_{os.path.basename(src).split('.')[0]}_{w}x{h}_{int(pos*100)}{'_t' + tint.strip('#') if tint else ''}.png"
        if not os.path.exists(key):
            im = Image.open(src).convert("RGBA")
            r = max(w / im.width, h / im.height)
            nw, nh = round(im.width * r), round(im.height * r)
            im = im.resize((nw, nh), Image.LANCZOS)
            left, topy = (nw - w) // 2, round((nh - h) * pos)
            im = im.crop((left, topy, left + w, topy + h))
            if tint:
                ov = Image.new("RGBA", im.size, tint + "AA")
                im = Image.alpha_composite(im, ov)
            im.save(key)
        self.img(key, x + w / 2, y + h / 2, w=w, name=name)


def perf_col(h, w=44, pw=24, ph=30, step=58, color=(245, 240, 224, 255)):
    key = f"{GEN}/perf_{h}_{w}_{pw}_{ph}_{step}.png"
    if not os.path.exists(key):
        s = 3
        im = Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        y = (step - ph) // 2
        while y + ph < h:
            x0 = (w - pw) // 2
            d.rounded_rectangle([x0 * s, y * s, (x0 + pw) * s, (y + ph) * s], 6 * s, fill=color)
            y += step
        im.resize((w, h), Image.LANCZOS).save(key)
    return key


def bunting(w, count):
    key = f"{GEN}/bunting_{w}_{count}.png"
    if not os.path.exists(key):
        s = 3
        h = round(w / count * 1.05) + 18
        im = Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        cols = ["#2747C7", "#A8CF45", "#D9B24C", "#E1533F"]
        tri = w / count
        sag = lambda t: 6 + 10 * (1 - (2 * t - 1) ** 2)
        for i in range(count):
            x0, x1 = i * tri + 3, (i + 1) * tri - 3
            y0, y1 = sag(x0 / w), sag(x1 / w)
            d.polygon([(x0 * s, y0 * s), (x1 * s, y1 * s), ((x0 + x1) / 2 * s, (max(y0, y1) + tri * 0.95) * s)],
                      fill=cols[i % 4], outline="#0E1F4D", width=2 * s)
        pts = [(t * s, sag(t / w) * s) for t in range(0, w + 1, 6)]
        d.line(pts, fill="#0E1F4D", width=2 * s)
        im.resize((w, h), Image.LANCZOS).save(key)
    return key


def village():
    key = f"{GEN}/desa.png"
    if not os.path.exists(key):
        base = Image.new("RGBA", (2000, 1280), (0, 0, 0, 0))
        for n in ("bg_c_far", "bg_c_mid", "bg_c_near", "bg_c_road"):
            base.alpha_composite(Image.open(f"{A}/{n}.png").convert("RGBA"))
        base.crop(base.getbbox()).save(key)
    return key


def slots(layout, top, bottom, side, gap):
    W, H, cols, rows, _ = LAYOUTS[layout]
    pw = (W - side * 2 - gap * (cols - 1)) // cols
    ph = (H - top - bottom - gap * (rows - 1)) // rows
    return [dict(x=side + c * (pw + gap), y=top + r * (ph + gap), w=pw, h=ph) for r in range(rows) for c in range(cols)]


# ---------------------------------------------------------------------------
# 1. KADER PANTAU: navy dan lime, seperti X-banner
# ---------------------------------------------------------------------------
def f_pantau(layout):
    W, H, _, _, u = LAYOUTS[layout]
    top, bottom = {"4-cut": (176, 330), "grid-2x2": (214, 300), "single": (176, 256)}[layout]
    side = {"4-cut": 36, "grid-2x2": 54, "single": 46}[layout]
    gap = {"4-cut": 16, "grid-2x2": 24, "single": 0}[layout]
    S = slots(layout, top, bottom, side, gap)
    r = round(12 * u)
    d = Doc(W, H)
    d.rect(0, 0, W, H, {"gradient": {"stops": [[0, DEEP], [0.45, NAVY], [1, "#142C6B"]], "angle": 90}}, name="latar navy")
    d.ellipse(W + 30 * u, 40 * u, 210 * u, 210 * u, None, stroke=GOLD, sw=2 * u, opacity=0.35, name="cincin emas")
    d.ellipse(-40 * u, H - 90 * u, 230 * u, 230 * u, None, stroke=LIME, sw=2 * u, opacity=0.25, name="cincin lime")
    d.bottom_img("fg_aloe", 110 * u, H + 10, w=300 * u, opacity=0.55, name="lidah buaya")
    lg = top - 44 * u
    d.img("logo", side + lg / 2, top / 2 - 2, w=lg, name="logo promaha")
    tx = side + lg + 18 * u
    d.text(tx, top / 2 - 12 * u, "PROMAHADESA", 45 * u * (0.82 if layout == "4-cut" else 1), LIME, name="judul")
    d.text(tx, top / 2 + 17 * u, "Desa Kamal  ·  Universitas Jember", 15.5 * u, WHITE, 600)
    d.text(tx, top / 2 + 42 * u, "TIM KADER PANTAU", 12.5 * u, GOLD, 700, track=240)
    d.rect(side, top - 13 * u, W - side * 2, 3 * u, LIME, name="garis lime")
    d.top()
    for s in S:
        d.rect(s["x"] - 3, s["y"] - 3, s["w"] + 6, s["h"] + 6, None, r=r + 3, stroke=GOLD, sw=3, name="bingkai emas")
    fy = H - bottom
    mh = bottom + 30 * u
    d.bottom_img("maskot_stand_dc", W - side - mh * 0.33, H - 46 * u + 8, h=mh - 40 * u, shadow=45, name="maskot")
    d.rect(0, H - 44 * u, W, 44 * u, LIME, name="pita lime")
    d.text(W / 2, H - 15 * u, "Pantau bersama, desa sehat!", 19 * u, NAVY, 700, "center", name="slogan")
    title_w = W - side * 2 - mh * 0.72
    return d, S, r, dict(
        title=dict(x=side, y=fy + 58 * u, size=26 * u, color=WHITE, align="left", maxWidth=title_w, lines=2),
        date=dict(x=side, y=fy + 132 * u, size=15 * u, color=LIME, align="left"),
    ), [("@promahadesa_kamal2026", side, fy + 160 * u, 13 * u, "#AEB9D6")]


# ---------------------------------------------------------------------------
# 2. DESA KAMAL: langit, rumah dusun, maskot naik sepeda
# ---------------------------------------------------------------------------
def f_desa(layout):
    W, H, _, _, u = LAYOUTS[layout]
    top, bottom = {"4-cut": (150, 370), "grid-2x2": (196, 450), "single": (150, 350)}[layout]
    side = {"4-cut": 44, "grid-2x2": 58, "single": 50}[layout]
    gap = {"4-cut": 22, "grid-2x2": 30, "single": 0}[layout]
    S = slots(layout, top, bottom, side, gap)
    r = round(8 * u)
    d = Doc(W, H)
    d.rect(0, 0, W, H, {"gradient": {"stops": [[0, "#6FBFEF"], [0.55, SKY], [1, "#EAF7FC"]], "angle": 90}}, name="langit")
    d.ellipse(W - 70 * u, 64 * u, 40 * u, 40 * u, "#FFE27A", stroke="#F6C445", sw=4 * u, name="matahari")
    rnd = random.Random(7)
    for i in range(int(H / 300) + 2):
        y = (i + 0.4) * (H - top - bottom * 0.6) / (int(H / 300) + 2) + top
        d.img("cloud_a" if i % 2 else "cloud_b", rnd.choice([-10, W + 10]), y, w=rnd.uniform(150, 210) * u, opacity=0.9, name="awan")
    d.img(bunting(W, 11 if layout == "4-cut" else 15), W / 2, 34 * u, w=W, name="bendera")
    sw = min(W - 2 * side, 500 * u)
    sy = 62 * u
    d.rect((W - sw) / 2, sy, sw, top - sy - 18 * u, CREAM, r=14 * u, stroke=NAVY, sw=4 * u, name="papan judul")
    lh = top - sy - 26 * u
    d.img("logo", (W - sw) / 2 + 12 * u + lh / 2, sy + (top - sy - 18 * u) / 2, w=lh, name="logo promaha")
    cx = (W - sw) / 2 + lh + 24 * u
    d.text(cx, sy + (top - sy - 18 * u) / 2 - 1 * u, "PROMAHADESA KAMAL", 24.5 * u, NAVY, name="judul")
    d.text(cx, sy + (top - sy - 18 * u) / 2 + 18 * u, "Desa Sehat dan Sejahtera", 13.5 * u, LEAF, 600)
    for s in S:
        b = round(9 * u)
        d.rect(s["x"] - b, s["y"] - b, s["w"] + b * 2, s["h"] + b * 2, WHITE, r=r + b, stroke=NAVY, sw=3, name="bingkai foto")
    # Ladang desa di dasar
    d.top()
    vw, vh = size_of(village())
    sh = W * vh / vw
    d.bottom_img(village(), W / 2, H + sh * 0.15, w=W, name="desa kamal")
    d.bottom_img("maskot_bike", W * 0.8, H - 8 * u, h=min(bottom * 0.62, 240 * u), shadow=20, name="maskot sepeda")
    fy = H - bottom
    return d, S, r, dict(
        title=dict(x=side, y=fy + 58 * u, size=24 * u, color=NAVY, align="left", maxWidth=W - side * 2, lines=1),
        date=dict(x=side, y=fy + 88 * u, size=15 * u, color=BLUE, align="left"),
    ), []


# ---------------------------------------------------------------------------
# 3. KEBUN TOGA: pot jahe, kunyit, serai, telang di papan kayu
# ---------------------------------------------------------------------------
def f_toga(layout):
    W, H, _, _, u = LAYOUTS[layout]
    top, bottom = {"4-cut": (166, 396), "grid-2x2": (206, 320), "single": (160, 290)}[layout]
    side = {"4-cut": 46, "grid-2x2": 60, "single": 52}[layout]
    gap = {"4-cut": 24, "grid-2x2": 32, "single": 0}[layout]
    S = slots(layout, top, bottom, side, gap)
    r = round(6 * u)
    d = Doc(W, H)
    d.cover("bg_e", name="daun")
    d.rect(0, 0, W, H, {"gradient": {"stops": [[0, "#0B3A22"], [1, "#0F4F2C"]], "angle": 90}}, opacity=0.55, name="redup")
    d.text(side, top * 0.46, "Kebun TOGA", 47 * u, CREAM, name="judul")
    d.text(side, top * 0.46 + 29 * u, "PROMAHADESA  ·  DESA KAMAL  ·  UNEJ 2026", 12.5 * u, LIME, 700, track=120)
    for s in S:
        b = round(9 * u)
        d.rect(s["x"] - b, s["y"] - b, s["w"] + b * 2, s["h"] + b * 2, CREAM, r=r + b, name="bingkai krem")
    d.top()
    for i, s in enumerate(S):
        d.img("tape", s["x"] + s["w"] / 2 + (-16 if i % 2 else 16) * u, s["y"] - 4 * u, w=92 * u, rot=-4 if i % 2 else 3, opacity=0.92, name="selotip")
    d.bottom_img("fg_vine", 16 * u, top + 200 * u, h=270 * u, shadow=25, name="sulur telang")
    d.bottom_img("fg_vine_flip", W - 18 * u, H - bottom * 0.64, h=280 * u, shadow=25, name="sulur telang")
    d.img("maskot_head", W - 92 * u, top * 0.52, w=170 * u, shadow=45, name="kepala maskot")
    shelf = H - 44 * u
    d.rect(-6, shelf, W + 12, 30 * u, "#B56A35", r=5 * u, stroke=NAVY, sw=4 * u, name="papan kayu")
    d.rect(-6, shelf + 30 * u, W + 12, 18 * u, "#0B3A22", name="bayangan papan")
    n = ["pot_jahe", "pot_kunyit", "pot_serai", "pot_telang"]
    ph = min(bottom * 0.42, 150 * u)
    for i, a in enumerate(n):
        d.bottom_img(a, W * (0.11 + i * 0.205), shelf + 3, h=ph * (1.12 if a == "pot_telang" else 1), shadow=30, name=a)
    d.bottom_img("fg_aloe", W * 0.9, shelf + 3, w=132 * u, shadow=30, name="lidah buaya")
    fy = H - bottom
    return d, S, r, dict(
        title=dict(x=W / 2, y=fy + 52 * u, size=24 * u, color=CREAM, align="center", maxWidth=W - side * 2, lines=1),
        date=dict(x=W / 2, y=fy + 80 * u, size=14.5 * u, color=LIME, align="center"),
    ), []


# ---------------------------------------------------------------------------
# 4. BLUE BLOOM: nila bunga telang dan dua produk desa
# ---------------------------------------------------------------------------
def f_bloom(layout):
    W, H, _, _, u = LAYOUTS[layout]
    top, bottom = {"4-cut": (168, 356), "grid-2x2": (206, 300), "single": (158, 270)}[layout]
    side = {"4-cut": 40, "grid-2x2": 56, "single": 48}[layout]
    gap = {"4-cut": 18, "grid-2x2": 26, "single": 0}[layout]
    S = slots(layout, top, bottom, side, gap)
    r = round(26 * u)
    d = Doc(W, H)
    d.rect(0, 0, W, H, {"gradient": {"stops": [[0, "#1B2FA8"], [0.5, "#17227E"], [1, "#2A1A7C"]], "angle": 100}}, name="nila")
    rnd = random.Random(11)
    for i in range(int(14 * max(1, H * W / 1228800) + 4)):
        d.img("petal", rnd.uniform(0, W), rnd.uniform(0, H), w=rnd.uniform(26, 52) * u, rot=rnd.uniform(-170, 170), opacity=rnd.uniform(0.25, 0.6), name="kelopak")
    d.text(W / 2, top * 0.47, "BLUE BLOOM × ALOEBITE", 33 * u, WHITE, 700, "center", name="judul")
    d.text(W / 2, top * 0.47 + 27 * u, "Produk inovasi warga Desa Kamal", 15 * u, "#C8D6FF", 600, "center")
    d.rect(W / 2 - 28 * u, top * 0.47 + 42 * u, 56 * u, 3 * u, GOLD, name="aksen emas")
    d.top()
    for s in S:
        d.rect(s["x"] - 4, s["y"] - 4, s["w"] + 8, s["h"] + 8, None, r=r + 4, stroke=WHITE, sw=4, name="bingkai putih")
    mh = bottom * 0.68
    d.bottom_img("maskot_head", W / 2, H - 16 * u, h=mh, shadow=50, name="kepala maskot")
    ph = bottom * 0.5
    d.bottom_img("ic_bottle_dc", W * 0.15, H - 18 * u, h=ph, rot=-7, shadow=40, name="aloebite")
    d.bottom_img("ic_tea_dc", W * 0.85, H - 18 * u, h=ph * 0.92, rot=7, shadow=40, name="blue bloom")
    fy = H - bottom
    return d, S, r, dict(
        title=dict(x=W / 2, y=fy + 40 * u, size=22 * u, color=WHITE, align="center", maxWidth=W - side * 2, lines=1),
        date=dict(x=W / 2, y=fy + 66 * u, size=14 * u, color=LIME, align="center"),
    ), []


# ---------------------------------------------------------------------------
# 5. STRIP KAMERA: rol film negatif Promaha 400
# ---------------------------------------------------------------------------
def f_film(layout):
    W, H, cols, _, u = LAYOUTS[layout]
    top, bottom = {"4-cut": (112, 330), "grid-2x2": (140, 280), "single": (112, 250)}[layout]
    pad = round(52 * u)
    gap = {"4-cut": 14, "grid-2x2": pad * 2 - 20, "single": 0}[layout]
    S = slots(layout, top, bottom, pad, gap)
    r = round(5 * u)
    d = Doc(W, H)
    d.rect(0, 0, W, H, "#0A0C14", name="film")
    d.rect(0, 0, W, H, {"gradient": {"stops": [[0, "#1A1408"], [1, "#0A0C14"]], "angle": 90}}, opacity=0.8, name="warna film")
    pc = perf_col(H, w=round(46 * u), pw=round(24 * u), ph=round(30 * u), step=round(56 * u))
    xs = [pad / 2, W - pad / 2]
    for x in xs:
        d.img(pc, x, H / 2, w=round(46 * u), name="lubang film")
    if cols == 2:
        # Lubang tengah berhenti di atas area judul
        mid = perf_col(H - bottom, w=round(46 * u), pw=round(24 * u), ph=round(30 * u), step=round(56 * u))
        d.img(mid, W / 2, (H - bottom) / 2, w=round(46 * u), name="lubang film tengah")
    mono = "IBM Plex Mono"
    lx = pad + 4
    d.text(lx, top * 0.42, "PROMAHA 400", 30 * u, AMBER, 700, font=mono, name="judul film")
    d.text(lx, top * 0.42 + 26 * u, "DESA KAMAL · UNEJ 2026 · KADER PANTAU", 11.5 * u, "#C9A25A", 600, font=mono, track=30)
    d.img("logo", W - pad - 38 * u, top * 0.48, w=78 * u, name="logo promaha")
    d.top()
    for i, s in enumerate(S):
        n = i + 1
        d.text(s["x"] + 6 * u, s["y"] + s["h"] - 8 * u, f"▶ {n}A", 13 * u, AMBER, 700, font=mono, name=f"nomor {n}")
    fy = H - bottom
    mh = bottom + 36 * u
    d.bottom_img("maskot_kamera_dc", W - pad - mh * 0.34 - 6 * u, H - 8 * u, h=mh, shadow=55, name="maskot kamera")
    return d, S, r, dict(
        title=dict(x=lx, y=fy + 62 * u, size=25 * u, color=AMBER, align="left", maxWidth=W - pad * 2 - mh * 0.72, lines=3, font="mono"),
        date=dict(x=lx, y=fy + 164 * u, size=14 * u, color="#E6D6AE", align="left", font="mono"),
    ), []


# ---------------------------------------------------------------------------
# 6. EXPO UNEJ: edisi acara, logo mitra asli dan pemandangan banner
# ---------------------------------------------------------------------------
def f_expo(layout):
    W, H, _, _, u = LAYOUTS[layout]
    top, bottom = {"4-cut": (216, 350), "grid-2x2": (272, 310), "single": (220, 280)}[layout]
    side = {"4-cut": 34, "grid-2x2": 52, "single": 44}[layout]
    gap = {"4-cut": 14, "grid-2x2": 22, "single": 0}[layout]
    S = slots(layout, top, bottom, side, gap)
    r = round(12 * u)
    d = Doc(W, H)
    d.rect(0, 0, W, H, {"gradient": {"stops": [[0, "#D7EFFB"], [1, "#F4FBFE"]], "angle": 90}}, name="latar")
    lw = W - side * 2
    lgh = lw * 290 / 2047
    d.rect(side, 14 * u, lw, lgh + 16 * u, WHITE, r=(lgh + 16 * u) / 2, name="pil logo")
    pill = lgh + 16 * u
    lgw = lgh * 0.92
    d.img("logo", W - side - pill / 2, 14 * u + pill / 2, w=lgw, name="logo promaha")
    x0, x1 = side + pill * 0.42, W - side - pill / 2 - lgw / 2 - 8 * u
    d.img("logos_mitra", (x0 + x1) / 2, 14 * u + pill / 2, w=x1 - x0, name="logo mitra")
    y0 = 14 * u + lgh + 16 * u
    t = (top - y0) / 2
    d.text(W / 2, y0 + t * 0.62, "LESSON LEARNED & TEMU DESA BINAAN", 23 * u * (0.92 if layout == "4-cut" else 1), NAVY, 700, "center", name="acara")
    d.rect(W / 2 - 190 * u, y0 + t * 0.82, 380 * u, 26 * u, BLUE, r=13 * u, name="pil biru")
    d.text(W / 2, y0 + t * 0.82 + 18 * u, "EXPO · SARASEHAN · DESA BINAAN AWARD", 13 * u, WHITE, 700, "center")
    for s in S:
        d.rect(s["x"] - 6, s["y"] - 6, s["w"] + 12, s["h"] + 12, WHITE, r=r + 6, stroke="#9CCBE8", sw=2, name="bingkai foto")
    d.top()
    band = 38 * u
    sh = W * 200 / 1600 * 1.55
    d.cover(f"{A}/expo_scene.jpg", 0, round(H - band - sh), W, round(sh), name="pemandangan desa")
    d.rect(0, H - band, W, band, BLUE, name="pita biru")
    d.text(W / 2, H - band / 2 + 6 * u, "3 NOVEMBER 2026  ·  UNIVERSITAS JEMBER", 15 * u, WHITE, 700, "center", name="tanggal acara")
    mh = bottom * 0.88
    d.bottom_img("maskot_stand", W - side - mh * 0.3, H - band - 2, h=mh, shadow=40, name="maskot")
    fy = H - bottom
    return d, S, r, dict(
        title=dict(x=side, y=fy + 48 * u, size=23 * u, color=NAVY, align="left", maxWidth=W - side * 2 - mh * 0.68, lines=2),
        date=dict(x=side, y=fy + 106 * u, size=14 * u, color=BLUE, align="left"),
    ), []


FRAMES = [
    ("pantau", "Kader PANTAU", f_pantau, NAVY),
    ("film", "Strip Kamera", f_film, "#0A0C14"),
    ("desa", "Desa Kamal", f_desa, SKY),
    ("toga", "Kebun TOGA", f_toga, "#0F4F2C"),
    ("bloom", "Blue Bloom", f_bloom, "#17227E"),
    ("expo", "Expo UNEJ", f_expo, "#D7EFFB"),
]


def run(steps, new, out):
    args = [CLI, "run", "--new", json.dumps(new)]
    for cid, p in steps:
        args += ["--cmd", cid, "--params", json.dumps(p)]
    args += ["--out", out]
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(f"{out}: {r.stderr[-600:]}")
    bad = [l for l in r.stderr.splitlines() if "not installed" in l]
    if bad:
        print("PERINGATAN", out, bad[0][:120], file=sys.stderr)


def build(fid, name, fn, bg, layout):
    d, S, r, text, extras = fn(layout)
    W, H = d.w, d.h
    d.cur = d.under
    for s, x, y, size, col in extras:
        d.text(x, y, s, size, col, 600)
    new = dict(width=W, height=H, background="transparent", name=f"{fid}-{layout}")
    tag = f"{fid}-{layout}"
    uf, of = f"{TMP}/{tag}-u.png", f"{TMP}/{tag}-o.png"
    run(d.under, new, uf)
    run(d.over, new, of) if d.over else Image.new("RGBA", (W, H)).save(of)
    placeholder = [("shape.create", dict(kind="roundedRect", rect=[s["x"], s["y"], s["w"], s["h"]], radii=r, fill="#7F8FA9", name=f"FOTO {i+1}")) for i, s in enumerate(S)]
    run(d.under + placeholder + d.over, new, f"{WORK}/sumber/{tag}.pcraft")
    under = Image.open(uf).convert("RGBA")
    ss = 4
    mask = Image.new("L", (W * ss, H * ss), 255)
    md = ImageDraw.Draw(mask)
    for s in S:
        md.rounded_rectangle([s["x"] * ss, s["y"] * ss, (s["x"] + s["w"]) * ss - 1, (s["y"] + s["h"]) * ss - 1], r * ss, fill=0)
    mask = mask.resize((W, H), Image.LANCZOS)
    a = under.split()[3]
    under.putalpha(Image.composite(a, Image.new("L", (W, H), 0), mask))
    under.alpha_composite(Image.open(of).convert("RGBA"))
    path = f"{OUT}/{tag}.webp"
    under.save(path, "WEBP", quality=90, alpha_quality=100, method=6)
    rnd = lambda o: {k: (round(v, 1) if isinstance(v, float) else v) for k, v in o.items()}
    return fid, layout, dict(src=f"./frames/{tag}.webp", width=W, height=H, radius=r, photos=S, title=rnd(text["title"]), date=rnd(text["date"]))


def main(only=None):
    jobs, manifest = [], {}
    with ThreadPoolExecutor(max_workers=6) as ex:
        for fid, name, fn, bg in FRAMES:
            if only and fid not in only:
                continue
            for layout in LAYOUTS:
                jobs.append(ex.submit(build, fid, name, fn, bg, layout))
        res = [j.result() for j in jobs]
    path = f"{ROOT}/src/js/promahaFrames.json"
    prev = json.load(open(path)) if os.path.exists(path) else {}
    for fid, name, fn, bg in FRAMES:
        manifest[fid] = dict(id=fid, name=name, bg=bg, layouts=dict(prev.get(fid, {}).get("layouts", {})))
    for fid, layout, data in res:
        manifest[fid]["layouts"][layout] = data
    json.dump(manifest, open(path, "w"), indent=1)
    print("selesai", len(res))


if __name__ == "__main__":
    main(set(sys.argv[1:]) or None)
