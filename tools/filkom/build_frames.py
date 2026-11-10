#!/usr/bin/env python3
"""Rakit frame Fasilkom × Lab Pertanian Cerdas × Dies Natalis 62 UNEJ lewat PhotoCraft, lalu lubangi slot foto.

Tiap frame: public/frames/<id>-<layout>.webp + sumber .pcraft berlayer di sumber/,
dan geometri slot foto/teks di src/js/themeFrames.json.
Jalankan setelah build_logos.py dan build_art.py.
"""
import json, os, random, sys
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw
from pc import *

OUT = f"{ROOT}/public/frames"
os.makedirs(OUT, exist_ok=True)
BASE = {"4-cut": (640, 1920, 1, 4, 1.0), "grid-2x2": (1200, 1300, 2, 2, 1.45), "single": (800, 900, 1, 1, 1.15)}
# Rasio lebar:tinggi slot foto yang dituju; tinggi kanvas menyesuaikan header dan footer tiap desain
TARGET = {"4-cut": 1.65, "grid-2x2": 1.45, "single": 1.4}


class _Layouts(dict):
    """LAYOUTS[layout] memberi (W, H, cols, rows, u); H bisa ditimpa per desain lewat HEIGHT."""

    def __getitem__(self, k):
        W, H, c, r, u = BASE[k]
        return W, HEIGHT.get((getattr(CURRENT, "fid", None), k), H), c, r, u


import threading
HEIGHT, CURRENT = {}, threading.local()
LAYOUTS = _Layouts({k: None for k in BASE})
MONO = "IBM Plex Mono"
HERO = f"{LAB}/bg-hero.png"


def grad(stops, angle=-90):
    return {"gradient": {"stops": [[t, c] for t, c in stops], "angle": angle}}


def slots(layout, top, bottom, side, gap):
    W, H, cols, rows, _ = LAYOUTS[layout]
    pw = (W - side * 2 - gap * (cols - 1)) // cols
    ph = (H - top - bottom - gap * (rows - 1)) // rows
    return [dict(x=side + c * (pw + gap), y=top + r * (ph + gap), w=pw, h=ph) for r in range(rows) for c in range(cols)]


def aspect(name):
    w, h = size_of(asset(name))
    return w / h


def logo_row(d, x, cy, h, names, gap, align="left", name="logo"):
    """Deret logo setinggi h; logo lebar (wordmark) dikecilkan agar seimbang dengan logo bulat."""
    sizes = []
    for n in names:
        k = 0.62 if aspect(n) > 2.5 else 1.0
        sizes.append((n, h * k * aspect(n), h * k))
    total = sum(w for _, w, _ in sizes) + gap * (len(sizes) - 1)
    cx = x if align == "left" else (x - total / 2 if align == "center" else x - total)
    for n, w, hh in sizes:
        d.img(n, cx + w / 2, cy, h=hh, name=f"{name} {n.replace('logo_', '')}")
        cx += w + gap
    return total


def foot_text(x, y0, y1, maxw, ts, tc, ds, dc, lines=1, align="left", font=None):
    """Judul dan tanggal ditaruh di tengah bidang [y0, y1]."""
    block = lines * ts * 1.2 + ds * 1.3
    top = y0 + max(0, (y1 - y0) - block) / 2
    t = dict(x=x, y=top + ts * 0.85, size=ts, color=tc, align=align, maxWidth=maxw, lines=lines)
    dd = dict(x=x, y=top + lines * ts * 1.2 + ds * 1.1, size=ds, color=dc, align=align)
    t["font"], dd["font"] = (font, font) if font else ("display", "serif")
    return dict(title=t, date=dd)


def traces(d, W, H, step, color, n, seed, sw, opacity):
    """Jalur PCB acak dengan node bulat di ujung, menggemakan logo Lab."""
    rnd = random.Random(seed)
    for _ in range(n):
        x, y = rnd.randrange(0, int(W / step) + 1) * step, rnd.randrange(0, int(H / step) + 1) * step
        pts = [[x, y]]
        for _ in range(rnd.randint(2, 4)):
            k = rnd.choice(["h", "v", "d"])
            L = rnd.randint(1, 3) * step
            sx, sy = rnd.choice([-1, 1]), rnd.choice([-1, 1])
            x, y = (x + sx * L, y) if k == "h" else ((x, y + sy * L) if k == "v" else (x + sx * L, y + sy * L))
            pts.append([x, y])
        d.line(pts, color, sw, name="jalur pcb", opacity=opacity)
        d.ellipse(*pts[-1], step * 0.2, step * 0.2, None, stroke=color, sw=sw, opacity=opacity, name="node pcb", align="center")
        d.ellipse(*pts[0], step * 0.09, step * 0.09, color, opacity=opacity, name="titik pcb")


def quote(d, lines, cx, y, size, colors, maxw, align="center", lh=1.18, name="kutipan"):
    """Kalimat motivasi Fraunces italic, tiap baris boleh beda warna. Kembalikan y bawah."""
    size = min(fit(l, SERIF, 600, size, maxw) for l in lines)
    for n, (l, c) in enumerate(zip(lines, colors)):
        d.text(cx, y + size * 0.8 + n * size * lh, l, size, c, 600, align, font=SERIF, italic=True, name=f"{name} {n + 1}")
    return y + size * (0.8 + (len(lines) - 1) * lh) + size * 0.3


def heading(d, s, x, y, size, color, maxw, align="left", weight=800, track=0, name=None):
    size = fit(s, DISPLAY, weight, size, maxw, track)
    d.text(x, y, s, size, color, weight, align, track=track, font=DISPLAY, name=name or s[:24])
    return size


def scatter(d, names, area_list, count, seed, wmin, wmax, opacity=1.0, rot=True):
    """Taburan elemen kecil (kilau, daun) di bidang-bidang margin."""
    rnd = random.Random(seed)
    for i in range(count):
        x0, y0, x1, y1 = area_list[i % len(area_list)]
        if x1 - x0 < 4 or y1 - y0 < 4:
            continue
        d.img(rnd.choice(names), rnd.uniform(x0, x1), rnd.uniform(y0, y1), w=rnd.uniform(wmin, wmax),
              rot=rnd.uniform(-40, 40) if rot else 0, opacity=opacity, name="taburan")


def margins(S, W, H, pad=6):
    """Bidang kosong di kiri, kanan, dan sela antar foto."""
    xs0 = min(s["x"] for s in S)
    xs1 = max(s["x"] + s["w"] for s in S)
    y0 = min(s["y"] for s in S)
    y1 = max(s["y"] + s["h"] for s in S)
    return [(pad, y0, xs0 - pad, y1), (xs1 + pad, y0, W - pad, y1)]


# ---------------------------------------------------------------------------
# 1. TUMBUH BERSAMA: Lab Pertanian Cerdas, zaitun gelap, jalur PCB, Si Tunas
# ---------------------------------------------------------------------------
def f_lab(layout):
    W, H, _, _, u = LAYOUTS[layout]
    side = {"4-cut": 36, "grid-2x2": 54, "single": 46}[layout]
    gap = {"4-cut": 16, "grid-2x2": 24, "single": 0}[layout]
    d = Doc(W, H)
    d.rect(0, 0, W, H, grad([(0, "#2E3819"), (0.5, "#1E2611"), (1, "#141A0A")]), name="latar zaitun")
    traces(d, W, H, 40 * u, LEAF, int(W * H / 22000), 5, 3 * u, 0.3)
    pw = W + 20
    d.img("pennants_lab", W / 2, 22 * u, w=pw, name="bendera")
    y = 56 * u
    lg = 112 * u
    d.ellipse(side + lg / 2, y + lg / 2, lg / 2 + 5 * u, lg / 2 + 5 * u, CREAM, name="alas logo")
    d.img("logo_lab", side + lg / 2, y + lg / 2, w=lg, name="logo lab")
    tx = side + lg + 20 * u
    mw = W - tx - side
    s1 = heading(d, "LAB PERTANIAN", tx, y + 40 * u, 40 * u, LIME, mw)
    heading(d, "CERDAS", tx, y + 40 * u + s1 * 1.15, s1, WHITE, mw)
    sub_y = y + 40 * u + s1 * 2.15 + 8 * u
    d.text(tx, sub_y, "FASILKOM · UNIVERSITAS JEMBER", fit("FASILKOM · UNIVERSITAS JEMBER", "Montserrat", 700, 13 * u, mw, 160),
           GOLD, 700, track=160, name="sub")
    y = max(y + lg + 18 * u, sub_y + 16 * u)
    d.rect(side, y, W - side * 2, 3 * u, LIME, name="garis lime")
    for x in (side, W - side):
        d.ellipse(x, y + 1.5 * u, 7 * u, 7 * u, LIME, name="node")
    y = quote(d, ["Tumbuh bersama teknologi,", "berbuah untuk negeri."], W / 2, y + 14 * u, 30 * u, [CREAM, LIME], W - side * 2)
    top = round(y + 14 * u)
    bottom = {"4-cut": 400, "grid-2x2": 340, "single": 300}[layout]
    S = slots(layout, top, bottom, side, gap)
    r = round(14 * u)
    d.top()
    for s in S:
        d.rect(s["x"] - 3, s["y"] - 3, s["w"] + 6, s["h"] + 6, None, r=r + 3, stroke=LIME, sw=3, name="bingkai lime")
    band = 44 * u
    d.rect(0, H - band, W, band, LIME, name="pita lime")
    tg = "SMART FARMING  ·  IoT  ·  DATA"
    d.text(W / 2, H - band / 2 + 6 * u, tg, fit(tg, "Montserrat", 700, 15 * u, W - 40, 160), INK, 700, "center", track=160, name="tagline")
    th = bottom - band - 40 * u
    tw = th * aspect("tunas")
    tcx = W - side - tw / 2 + 8 * u
    d.bottom_img("tunas", tcx, H - band + 6 * u, h=th, figure=True, name="si tunas", shadow=0.4)
    fy = H - bottom
    d.img("sparkle_lime", tcx - tw * 0.55, fy + 40 * u, w=34 * u, name="kilau")
    d.img("sparkle", side + 8 * u, fy + 26 * u, w=24 * u, name="kilau")
    d.img("leaf_b", 8 * u, H - band - 24 * u, w=80 * u, rot=-30, opacity=0.95, name="daun")
    lh = 40 * u
    logo_row(d, side + 40 * u, H - band - 18 * u - lh / 2, lh, ["logo_fasilkom_putih", "logo_unej"], 14 * u)
    t = foot_text(side, fy + 30 * u, H - band - 30 * u - lh, W - side * 2 - tw, 24 * u, CREAM, 17 * u, LIME,
                  lines=2 if layout == "4-cut" else 1)
    return d, S, r, t


# ---------------------------------------------------------------------------
# 2. MENANAM IDE: Fasilkom resmi, putih bersih, laptop bertunas, pita abu
# ---------------------------------------------------------------------------
def f_fasilkom(layout):
    W, H, _, _, u = LAYOUTS[layout]
    side = {"4-cut": 34, "grid-2x2": 54, "single": 44}[layout]
    gap = {"4-cut": 16, "grid-2x2": 24, "single": 0}[layout]
    hw = W - side * 2
    hh = hw / aspect("logo_header")
    d = Doc(W, H)
    d.rect(0, 0, W, H, grad([(0, "#FFFFFF"), (1, "#ECEEE5")]), name="latar")
    d.img("code_mark", W - 30 * u, H * 0.45, w=300 * u, opacity=0.05, name="watermark </>")
    d.img("code_mark", 20 * u, H * 0.2, w=200 * u, opacity=0.04, name="watermark </>")
    d.img("logo_header", W / 2, 22 * u + hh / 2, w=hw, name="header resmi fasilkom")
    y = 22 * u + hh + 16 * u
    d.rect(side, y, hw * 0.62, 5 * u, RED, name="garis merah")
    d.rect(side + hw * 0.62, y, hw * 0.38, 5 * u, GOLD, name="garis emas")
    lh = 54 * u
    ly = y + 16 * u + lh / 2
    d.img("logo_lab", side + lh / 2, ly, h=lh, name="logo lab")
    mw = hw - lh - 12 * u
    ts = heading(d, "LAB PERTANIAN CERDAS", side + lh + 12 * u, ly + 2 * u, 22 * u, "#3A3B3D", mw)
    d.text(side + lh + 12 * u, ly + 22 * u, "Fakultas Ilmu Komputer · Universitas Jember", fit("Fakultas Ilmu Komputer · Universitas Jember", "Montserrat", 600, 13 * u, mw), OLIVE, 600, name="sub lab")
    y = ly + lh / 2 + 10 * u
    y = quote(d, ["Menanam ide hari ini,", "menuai inovasi esok hari."], W / 2, y, 30 * u, ["#3A3B3D", RED], hw)
    top = round(y + 14 * u)
    bottom = {"4-cut": 420, "grid-2x2": 320, "single": 290}[layout]
    S = slots(layout, top, bottom, side, gap)
    r = round(10 * u)
    for s in S:
        d.rect(s["x"] - 6, s["y"] - 6, s["w"] + 12, s["h"] + 12, WHITE, r=r + 6, stroke="#D3D6CA", sw=2, name="bingkai foto", shadow=0.18)
    d.top()
    band = 46 * u
    d.rect(0, H - band, W, band, "#3A3B3D", name="pita abu")
    d.rect(0, H - band, W * 0.16, band, RED, name="pita merah")
    d.rect(W * 0.16, H - band, W * 0.05, band, GOLD, name="pita emas")
    tg = "INNOVATE TO ELEVATE"
    d.text(W * 0.6, H - band / 2 + 6 * u, tg, fit(tg, "Montserrat", 700, 15 * u, W * 0.7, 320), WHITE, 700, "center", track=320, name="tagline")
    fy = H - bottom
    if layout == "4-cut":
        th = 190
        tw = th * aspect("tunas")
        d.bottom_img("tunas", W - side - tw / 2 + 6, H - band + 4, h=th, figure=True, name="si tunas")
        lw = 220
        d.bottom_img("laptop", side + lw / 2, H - band - 2, w=lw, figure=True, name="laptop bertunas")
        d.img("sparkle_red", side + lw + 30, H - band - 120, w=30, name="kilau")
        d.img("sparkle", side + lw + 60, H - band - 70, w=20, name="kilau")
        t = foot_text(side, fy + 16, H - band - th - 10, hw, 24, "#3A3B3D", 17, RED, lines=2)
    else:
        th = bottom - band - 30 * u
        tw = th * aspect("tunas")
        d.bottom_img("tunas", W - side - tw / 2 + 8 * u, H - band + 4 * u, h=th, figure=True, name="si tunas")
        lw = th * 0.95 * aspect("laptop")
        d.bottom_img("laptop", W - side - tw - lw / 2 - 4 * u, H - band - 2, w=lw, figure=True, name="laptop bertunas")
        d.img("code_mark", side + 28 * u, fy + 34 * u, w=56 * u, name="aksen </>")
        d.img("sparkle_red", W - side - tw - lw - 20 * u, fy + 40 * u, w=26 * u, name="kilau")
        t = foot_text(side, fy + 56 * u, H - band - 10 * u, W - side * 2 - tw - lw - 30 * u, 24 * u, "#3A3B3D", 17 * u, RED, lines=2)
    return d, S, r, t


# ---------------------------------------------------------------------------
# 3. BENIH MIMPI: foto irigasi asli Lab, drone, sensor, tunas
# ---------------------------------------------------------------------------
def f_ladang(layout):
    W, H, _, _, u = LAYOUTS[layout]
    side = {"4-cut": 40, "grid-2x2": 58, "single": 50}[layout]
    gap = {"4-cut": 22, "grid-2x2": 30, "single": 0}[layout]
    d = Doc(W, H)
    d.cover(HERO, pos=0.6, name="ladang irigasi")
    d.rect(0, 0, W, H, grad([(0, "#0E1508"), (0.3, "#1B260E"), (0.7, "#1B260E"), (1, "#0B1006")]), opacity=0.64, name="redup")
    lh = 50 * u
    logo_row(d, side, 30 * u + lh / 2, lh, ["logo_fasilkom_putih", "logo_unej", "logo_lab"], 14 * u)
    dw = min(W * 0.34, 210 * u)
    d.img("drone", W - side - dw / 2, 30 * u + lh / 2 + 4 * u, w=dw, name="drone", shadow=0.4)
    y = 30 * u + lh + 18 * u
    y = quote(d, ["Dari benih kecil,", "tumbuh mimpi besar."], side, y, 44 * u, [WHITE, LIME], W - side * 2, align="left", lh=1.12)
    sub = "LABORATORIUM PERTANIAN CERDAS"
    d.text(side, y + 18 * u, sub, fit(sub, "Montserrat", 700, 13 * u, W - side * 2, 200), "#D8E3B5", 700, track=200, name="sub")
    top = round(y + 40 * u)
    bottom = {"4-cut": 330, "grid-2x2": 300, "single": 260}[layout]
    S = slots(layout, top, bottom, side, gap)
    r = round(8 * u)
    for s in S:
        b = round(9 * u)
        d.rect(s["x"] - b, s["y"] - b, s["w"] + b * 2, s["h"] + b * 2, CREAM, r=r + b, name="bingkai krem", shadow=0.4)
    d.top()
    d.img("leaf_a", 10 * u, H - bottom + 4 * u, w=110 * u, rot=50, name="daun kiri", shadow=0.3)
    d.img("leaf_c", W - 6 * u, top + 30 * u, w=90 * u, rot=-150, name="daun kanan atas", shadow=0.3)
    sh = bottom - 40 * u
    d.bottom_img("sensor", W - side - 26 * u, H + sh * 0.2, h=sh, rot=8, figure=True, name="sensor tanah", shadow=0.4)
    spw = 120 * u
    d.bottom_img("sprout", W - side - 110 * u, H + 4, w=spw, figure=True, name="tunas", shadow=0.3)
    fy = H - bottom
    d.img("sparkle_lime", side + 8 * u, fy + 34 * u, w=26 * u, name="kilau")
    t = foot_text(side + 30 * u, fy + 30 * u, H - 20 * u, W - side * 2 - 200 * u, 25 * u, WHITE, 17 * u, LIME,
                  lines=2 if layout == "4-cut" else 1)
    return d, S, r, t


# ---------------------------------------------------------------------------
# 4. PANEN DATA: dashboard IoT, bingkai kamera, gauge sensor
# ---------------------------------------------------------------------------
def f_dash(layout):
    W, H, cols, _, u = LAYOUTS[layout]
    side = {"4-cut": 30, "grid-2x2": 48, "single": 40}[layout]
    gap = {"4-cut": 18, "grid-2x2": 26, "single": 0}[layout]
    d = Doc(W, H)
    d.rect(0, 0, W, H, grad([(0, "#141A0C"), (1, "#0B0E06")]), name="layar")
    step = 32 * u
    for i in range(int(W / step) + 1):
        d.line([[i * step, 0], [i * step, H]], "#2A3519", 1.2, name="grid", opacity=0.6, cap="butt")
    for j in range(int(H / step) + 1):
        d.line([[0, j * step], [W, j * step]], "#2A3519", 1.2, name="grid", opacity=0.6, cap="butt")
    hb = 104 * u
    d.rect(side, 18 * u, W - side * 2, hb, "#1C2412", r=14 * u, stroke="#3C4A26", sw=2, name="bar atas")
    lg = hb - 22 * u
    cy = 18 * u + hb / 2
    d.ellipse(side + 11 * u + lg / 2, cy, lg / 2 + 3 * u, lg / 2 + 3 * u, CREAM, name="alas logo")
    d.img("logo_lab", side + 11 * u + lg / 2, cy, w=lg, name="logo lab")
    tx = side + lg + 26 * u
    pw = 92 * u
    mw = W - side - 20 * u - pw - tx
    heading(d, "PANEN DATA", tx, cy + 2 * u, 30 * u, LIME, mw)
    sub = "lab.pertanian.cerdas // fasilkom.unej"
    d.text(tx, cy + 26 * u, sub, fit(sub, MONO, 600, 12.5 * u, mw), "#8E9A73", 600, font=MONO, name="sub")
    px = W - side - 12 * u - pw
    d.rect(px, cy - 15 * u, pw, 30 * u, "#3A1A10", r=15 * u, stroke=RED, sw=2, name="pil live")
    d.ellipse(px + 18 * u, cy, 6 * u, 6 * u, RED, name="titik live")
    d.text(px + 30 * u, cy + 6 * u, "LIVE", 16 * u, "#FFD7C8", 700, font=MONO, name="live")
    y = 18 * u + hb + 10 * u
    y = quote(d, ["Data hari ini, panen esok hari."], W / 2, y, 26 * u, [CREAM], W - side * 2)
    top = round(y + 12 * u)
    bottom = {"4-cut": 470, "grid-2x2": 330, "single": 300}[layout]
    S = slots(layout, top, bottom, side, gap)
    r = round(6 * u)
    d.top()
    for i, s in enumerate(S):
        L, t = 30 * u, 4 * u
        x0, y0, x1, y1 = s["x"] + 10 * u, s["y"] + 10 * u, s["x"] + s["w"] - 10 * u, s["y"] + s["h"] - 10 * u
        for (ax, ay, sx, sy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
            d.line([[ax, ay + sy * L], [ax, ay], [ax + sx * L, ay]], LIME, t, name="sudut bidik", cap="square")
        d.rect(x0 + 8 * u, y0 + 8 * u, 96 * u, 26 * u, "#0B0E06", r=6 * u, opacity=0.7, name="label kamera")
        d.text(x0 + 16 * u, y0 + 27 * u, f"CAM-0{i + 1}", 15 * u, LIME, 700, font=MONO, name=f"cam {i + 1}")
        d.ellipse(x1 - 66 * u, y0 + 21 * u, 7 * u, 7 * u, RED, name="rec")
        d.text(x1 - 54 * u, y0 + 27 * u, "REC", 15 * u, WHITE, 700, font=MONO, name="rec")
        d.rect(s["x"] - 2, s["y"] - 2, s["w"] + 4, s["h"] + 4, None, r=r + 2, stroke="#3C4A26", sw=2, name="tepi panel")
    fy = H - bottom
    lh = 34 * u
    if layout == "4-cut":
        gw = (W - side * 2 - 16) / 2
        gh = gw / aspect("gauge_lembap")
        gy = H - 20 - gh / 2
        d.img("gauge_lembap", side + gw / 2, gy, w=gw, figure=True, name="gauge kelembapan")
        d.img("gauge_suhu", W - side - gw / 2, gy, w=gw, figure=True, name="gauge suhu")
        tb = H - 30 - gh
        logo_row(d, side, tb - lh / 2 - 6, lh, ["logo_fasilkom_putih", "logo_unej"], 12)
        cw = 70
        d.img("chip", W - side - cw / 2, tb - cw / 2 - 4, w=cw, figure=True, name="chip")
        t = foot_text(side, fy + 16 * u, tb - lh - 18, W - side * 2, 22 * u, LIME, 15 * u, "#C9D4A8", lines=2, font="mono")
    else:
        gh = bottom - 44 * u
        gw = gh * aspect("gauge_lembap")
        n = 2 if layout == "grid-2x2" else 1
        for k, g in enumerate(["gauge_suhu", "gauge_lembap"][-n:]):
            d.img(g, W - side - gw / 2 - k * (gw + 14 * u), H - 22 * u - gh / 2, w=gw, figure=True, name=g)
        tw = W - side * 2 - n * (gw + 14 * u)
        lw = logo_row(d, side, H - 30 * u - lh / 2, lh, ["logo_fasilkom_putih", "logo_unej"], 12 * u)
        cw = 52 * u
        d.img("chip", side + lw + 18 * u + cw / 2, H - 30 * u - lh / 2, w=cw, figure=True, name="chip")
        t = foot_text(side, fy + 18 * u, H - 40 * u - lh, tw - 10 * u, 22 * u, LIME, 15 * u, "#C9D4A8", lines=2, font="mono")
    return d, S, r, t


# ---------------------------------------------------------------------------
# 5. AKAR KUAT: kebun hidroponik cerah, pipa NFT dan selada
# ---------------------------------------------------------------------------
def f_hidro(layout):
    W, H, _, _, u = LAYOUTS[layout]
    side = {"4-cut": 44, "grid-2x2": 60, "single": 50}[layout]
    gap = {"4-cut": 24, "grid-2x2": 32, "single": 0}[layout]
    d = Doc(W, H)
    d.rect(0, 0, W, H, grad([(0, "#F6F8EA"), (1, "#DCEBB8")]), name="latar")
    d.img("sun", W - 24 * u, 30 * u, w=170 * u, opacity=0.95, name="matahari")
    lg = 64 * u
    y = 26 * u
    d.img("logo_lab", side + lg / 2, y + lg / 2, w=lg, name="logo lab")
    lh = 30 * u
    logo_row(d, side + lg + 14 * u, y + lg / 2, lh, ["logo_fasilkom", "logo_unej"], 12 * u)
    y += lg + 14 * u
    y = quote(d, ["Akar yang kuat,", "masa depan yang hijau."], side, y, 40 * u, [OLIVE_D, D_GRN2], W - side * 2 - 40 * u, align="left", lh=1.12)
    sub = "KEBUN HIDROPONIK · LAB PERTANIAN CERDAS"
    d.text(side, y + 16 * u, sub, fit(sub, "Montserrat", 700, 13 * u, W - side * 2, 140), OLIVE, 700, track=140, name="sub")
    top = round(y + 40 * u)
    bottom = {"4-cut": 400, "grid-2x2": 380, "single": 330}[layout]
    S = slots(layout, top, bottom, side, gap)
    r = round(18 * u)
    scatter(d, ["droplet", "leaf_c", "sparkle_lime"], margins(S, W, H), int(H / 160), 9, 18 * u, 32 * u, 0.9)
    for s in S:
        b = round(10 * u)
        d.rect(s["x"] - b, s["y"] - b, s["w"] + b * 2, s["h"] + b * 2, WHITE, r=r + b, stroke=INK, sw=3 * u, name="bingkai stiker", shadow=0.15)
    d.top()
    pw = W + 40 * u
    key = "hidro_wide" if layout != "4-cut" else "hidro"
    ph = pw / aspect(key)
    d.bottom_img(key, W / 2, H + ph * 0.1, w=pw, figure=True, name="pipa hidroponik")
    fy = H - bottom
    d.img("sparkle", side, fy + 30 * u, w=26 * u, name="kilau")
    d.img("sparkle_red", W - side, fy + 50 * u, w=20 * u, name="kilau")
    t = foot_text(W / 2, fy + 12 * u, H - ph * 0.9, W - side * 2 - 40 * u, 24 * u, OLIVE_D, 17 * u, RED, align="center")
    return d, S, r, t


# ---------------------------------------------------------------------------
# 7. DIES NATALIS KE-62 UNEJ: krem meriah, bendera, logo Dies, tema resmi
# ---------------------------------------------------------------------------
def f_dies(layout):
    W, H, _, _, u = LAYOUTS[layout]
    side = {"4-cut": 36, "grid-2x2": 56, "single": 46}[layout]
    gap = {"4-cut": 16, "grid-2x2": 24, "single": 0}[layout]
    d = Doc(W, H)
    d.rect(0, 0, W, H, grad([(0, "#FFFDF6"), (1, "#FAF3E0")]), name="latar krem")
    # angka 62 raksasa samar di latar
    big = H * 0.34 if layout == "4-cut" else H * 0.6
    d.text(W / 2, H * 0.62 + big * 0.36, "62", big, D_YEL, 800, "center", font=DISPLAY, opacity=0.13, name="62 latar")
    # sapuan daun hijau seperti logo Dies
    d.path([dict(anchor=[W * 0.35, H], out=[W * 0.6, H - 160 * u]), dict(anchor=[W + 10, H - 210 * u], **{"in": [W * 0.85, H - 220 * u]}),
            [W + 10, H]], grad([(0, D_GRN), (1, D_GRN2)], 0), opacity=0.16, name="sapuan daun")
    d.img("pennants_dies", W / 2, 24 * u, w=W + 20, name="bendera")
    y = 60 * u
    lh = 54 * u
    w = logo_row(d, W / 2, y + lh / 2, lh, ["logo_unej", "logo_fasilkom", "logo_lab"], 18 * u, align="center")
    y += lh + 18 * u
    mw = W - side * 2
    s = "SELAMAT"
    d.text(W / 2, y + 14 * u, s, 15 * u, D_RED, 700, "center", track=500, font="Montserrat", name="selamat")
    hs = heading(d, "DIES NATALIS KE-62", W / 2, y + 14 * u + 44 * u, 40 * u, D_GRN2, mw, "center")
    y = y + 14 * u + 44 * u + 10 * u
    s2 = "UNIVERSITAS JEMBER · 10 NOV 1964–2026"
    d.text(W / 2, y + 16 * u, s2, fit(s2, "Montserrat", 700, 14 * u, mw, 120), "#3A3B3D", 700, "center", track=120, name="universitas")
    y += 26 * u
    d.rect(W / 2 - 40 * u, y, 26 * u, 4 * u, D_RED, name="aksen")
    d.rect(W / 2 - 13 * u, y, 26 * u, 4 * u, D_YEL, name="aksen")
    d.rect(W / 2 + 14 * u, y, 26 * u, 4 * u, D_GRN, name="aksen")
    y = quote(d, ["Menumbuhkan Pengetahuan,", "Menciptakan Dampak"], W / 2, y + 10 * u, 30 * u, [D_GRN2, D_RED], mw)
    top = round(y + 14 * u)
    bottom = {"4-cut": 360, "grid-2x2": 330, "single": 300}[layout]
    S = slots(layout, top, bottom, side, gap)
    r = round(12 * u)
    scatter(d, ["sparkle", "sparkle_red", "sparkle_lime"], margins(S, W, H), int(H / 150), 21, 14 * u, 26 * u)
    for s in S:
        d.rect(s["x"] - 7, s["y"] - 7, s["w"] + 14, s["h"] + 14, WHITE, r=r + 7, stroke=D_YEL, sw=4, name="bingkai kuning", shadow=0.16)
    d.top()
    band = 40 * u
    third = W / 3
    for i, c in enumerate((D_RED, D_YEL, D_GRN)):
        d.rect(i * third, H - band, third + 1, band, c, name="pita")
    tg = "EXCELLENCE · DISCOVERY · UNIVERSALITY"
    d.rect(W / 2 - text_w(tg, "Montserrat", 700, fit(tg, "Montserrat", 700, 13 * u, W - 60, 120), 120) / 2 - 16 * u, H - band + 7 * u,
           text_w(tg, "Montserrat", 700, fit(tg, "Montserrat", 700, 13 * u, W - 60, 120), 120) + 32 * u, band - 14 * u, WHITE, r=(band - 14 * u) / 2, name="pil tagline")
    d.text(W / 2, H - band / 2 + 5 * u, tg, fit(tg, "Montserrat", 700, 13 * u, W - 60, 120), "#3A3B3D", 700, "center", track=120, name="tagline")
    fy = H - bottom
    dh = bottom - band - 34 * u
    dw = dh * aspect("logo_dies")
    d.img("logo_dies", side + dw / 2, H - band - 16 * u - dh / 2, h=dh, figure=True, name="logo dies natalis 62")
    if layout != "4-cut":
        th = bottom - band - 24 * u
        tw = th * aspect("tunas_cheer")
        d.bottom_img("tunas_cheer", W - side - tw / 2 + 6 * u, H - band + 4 * u, h=th, figure=True, name="si tunas", shadow=0.25)
        tx, tmw = side + dw + 24 * u, W - side * 2 - dw - tw - 30 * u
    else:
        tx, tmw = side + dw + 20, W - side * 2 - dw - 20
    t = foot_text(tx, fy + 20 * u, H - band - 16 * u, tmw, 22 * u, D_GRN2, 17 * u, D_RED, lines=3 if layout == "4-cut" else 2)
    return d, S, r, t


def perf_col(h, w, pw, ph, step, color=(240, 232, 210, 255)):
    key = f"{GEN}/perf_{h}_{w}_{pw}_{ph}_{step}.png"
    if not os.path.exists(key):
        s = 3
        im = Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0))
        dr = ImageDraw.Draw(im)
        y = (step - ph) // 2
        while y + ph < h:
            x0 = (w - pw) // 2
            dr.rounded_rectangle([x0 * s, y * s, (x0 + pw) * s, (y + ph) * s], 6 * s, fill=color)
            y += step
        im.resize((w, h), Image.LANCZOS).save(key)
    return key


def f_film(layout):
    W, H, cols, _, u = LAYOUTS[layout]
    top, bottom = {"4-cut": (120, 340), "grid-2x2": (150, 300), "single": (120, 270)}[layout]
    pad = round(52 * u)
    gap = {"4-cut": 14, "grid-2x2": pad * 2 - 20, "single": 0}[layout]
    S = slots(layout, top, bottom, pad, gap)
    r = round(5 * u)
    d = Doc(W, H)
    d.rect(0, 0, W, H, grad([(0, "#1A1708"), (1, "#0B0C07")]), name="film")
    pc = perf_col(H, round(46 * u), round(24 * u), round(30 * u), round(56 * u))
    for x in (pad / 2, W - pad / 2):
        d.img(pc, x, H / 2, w=round(46 * u), name="lubang film")
    if cols == 2:
        mid = perf_col(H - bottom, round(46 * u), round(24 * u), round(30 * u), round(56 * u))
        d.img(mid, W / 2, (H - bottom) / 2, w=round(46 * u), name="lubang film tengah")
    lx = pad + 4
    d.text(lx, top * 0.44, "LABPC 400", 31 * u, "#F2B441", 700, font=MONO, name="judul film")
    d.text(lx, top * 0.44 + 25 * u, "SETIAP TUNAS PUNYA CERITA", 12 * u, "#C9A25A", 600, font=MONO, track=40, name="sub film")
    lg = top * 0.62
    d.img("logo_lab", W - pad - lg / 2 - 4 * u, top * 0.48, w=lg, name="logo lab")
    d.top()
    for i, s in enumerate(S):
        d.text(s["x"] + 6 * u, s["y"] + s["h"] - 8 * u, f"▶ {i + 1}A", 13 * u, "#F2B441", 700, font=MONO, name=f"nomor {i + 1}")
    fy = H - bottom
    th = bottom - 22 * u
    tw = th * aspect("tunas_cheer")
    d.bottom_img("tunas_cheer", W - pad - tw / 2 + 14 * u, H - 8 * u, h=th, figure=True, name="si tunas", shadow=0.5)
    d.img("sparkle", W - pad - tw - 10 * u, fy + 40 * u, w=26 * u, name="kilau")
    lh = 32 * u
    logo_row(d, lx, H - 24 * u - lh / 2, lh, ["logo_fasilkom_putih", "logo_unej"], 12 * u)
    t = foot_text(lx, fy + 20 * u, H - 40 * u - lh, W - pad * 2 - tw + 10 * u, 25 * u, "#F2B441", 14 * u, "#E6D6AE",
                  lines=3 if layout == "4-cut" else 2, font="mono")
    return d, S, r, t


FRAMES = [
    ("dies", "Dies Natalis 62", f_dies, "#FAF3E0"),
    ("lab", "Tumbuh Bersama", f_lab, "#1E2611"),
    ("fasilkom", "Menanam Ide", f_fasilkom, "#F4F5EF"),
    ("benih", "Benih Mimpi", f_ladang, "#1B260E"),
    ("panen-data", "Panen Data", f_dash, "#0F130A"),
    ("akar", "Akar Kuat", f_hidro, "#E8F0D0"),
    ("film", "Cerita Tunas", f_film, "#0B0C07"),
]


def build(fid, fn, layout):
    CURRENT.fid = fid
    d, S, r, text = fn(layout)
    # Hitung ulang tinggi kanvas agar slot foto memakai rasio TARGET
    _, H0, cols, rows, _ = LAYOUTS[layout]
    top = S[0]["y"]
    gap_y = (S[cols]["y"] - S[0]["y"] - S[0]["h"]) if rows > 1 else 0
    bottom = H0 - (S[-1]["y"] + S[-1]["h"])
    ph = round(S[0]["w"] / TARGET[layout])
    HEIGHT[(fid, layout)] = top + bottom + rows * ph + gap_y * (rows - 1)
    d, S, r, text = fn(layout)
    W, H = d.w, d.h
    for x0, y0, x1, y1, nm in d.figures:
        for s in S:
            if x0 < s["x"] + s["w"] and x1 > s["x"] and y0 < s["y"] + s["h"] and y1 > s["y"]:
                raise RuntimeError(f"{fid}-{layout}: {nm} menimpa foto")
    new = dict(width=W, height=H, background="transparent", name=f"{fid}-{layout}")
    tag = f"{fid}-{layout}"
    uf, of = f"{TMP}/{tag}-u.png", f"{TMP}/{tag}-o.png"
    run(d.under, new, uf)
    run(d.over, new, of) if d.over else Image.new("RGBA", (W, H)).save(of)
    holder = [("shape.create", dict(kind="roundedRect", rect=[s["x"], s["y"], s["w"], s["h"]], radii=r, fill="#8C9772", name=f"FOTO {i + 1}")) for i, s in enumerate(S)]
    run(d.under + holder + d.over, new, f"{SRC}/{tag}.pcraft")
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
    under.save(f"{OUT}/{tag}.webp", "WEBP", quality=90, alpha_quality=100, method=6)
    rnd = lambda o: {k: (round(v, 1) if isinstance(v, float) else v) for k, v in o.items()}
    return fid, layout, dict(src=f"./frames/{tag}.webp", width=W, height=H, radius=r, photos=S,
                             title=rnd(text["title"]), date=rnd(text["date"]))


def main(only=None):
    path = f"{ROOT}/src/js/themeFrames.json"
    prev = json.load(open(path)) if os.path.exists(path) else {}
    with ThreadPoolExecutor(max_workers=6) as ex:
        jobs = [ex.submit(build, fid, fn, lay) for fid, _, fn, _ in FRAMES if not only or fid in only for lay in LAYOUTS]
        res = [j.result() for j in jobs]
    manifest = {fid: dict(id=fid, name=name, bg=bg, layouts=dict(prev.get(fid, {}).get("layouts", {}))) for fid, name, _, bg in FRAMES}
    for fid, layout, data in res:
        manifest[fid]["layouts"][layout] = data
    json.dump(manifest, open(path, "w"), indent=1)
    print("selesai", len(res))


if __name__ == "__main__":
    main(set(sys.argv[1:]) or None)
