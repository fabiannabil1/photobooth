#!/usr/bin/env python3
"""Stiker, virtual background, aset UI, dan ikon PWA. Jalankan setelah build_logos.py dan build_art.py."""
import base64, io, json, math, os, random
import numpy as np
from PIL import Image
from scipy import ndimage as ni
from pc import *
from build_frames import aspect

PUB = f"{ROOT}/public"
for sub in ("stickers", "brand", "backgrounds", "icons"):
    os.makedirs(f"{PUB}/{sub}", exist_ok=True)


def grad(stops, angle=-90):
    return {"gradient": {"stops": [[t, c] for t, c in stops], "angle": angle}}


def fit_im(im, side):
    r = min(1, side / max(im.size))
    return im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)


def diecut(im, w):
    pad = w + 3
    base = Image.new("RGBA", (im.width + pad * 2, im.height + pad * 2), (0, 0, 0, 0))
    base.paste(im, (pad, pad), im)
    a = np.asarray(base.split()[3]) > 40
    ring = np.clip(w + 0.5 - ni.distance_transform_edt(~a), 0, 1)
    white = Image.fromarray(np.dstack([np.full(a.shape + (3,), 255, np.uint8), (ring * 255).astype(np.uint8)]), "RGBA")
    white.alpha_composite(base)
    return white


# --- Stiker -----------------------------------------------------------------------------------
STICKERS = [
    ("dies62", "Dies Natalis 62", "logo_dies", 16),
    ("ucapan-dies", "Selamat Dies!", "bub_dies", 0),
    ("tunas", "Si Tunas", "tunas", 12),
    ("tunas-senang", "Tunas Senang", "tunas_cheer", 12),
    ("logo-lab", "Logo Lab", "logo_lab", 10),
    ("logo-fasilkom", "Fasilkom", "logo_fasilkom", 18),
    ("logo-unej", "UNEJ", "logo_unej", 10),
    ("halo", "Halo Fasilkom", "bub_halo", 0),
    ("tani-cerdas", "Tani Cerdas", "bub_tani", 0),
    ("terus-tumbuh", "Terus Tumbuh", "bub_tumbuh", 0),
    ("panen-data", "Panen Data", "bub_panen", 0),
    ("innovate", "Innovate", "bub_innovate", 0),
    ("laptop", "Laptop Bertunas", "laptop", 12),
    ("drone", "Drone", "drone", 12),
    ("sensor", "Sensor Tanah", "sensor", 12),
    ("chip", "Chip AGRI-32", "chip", 12),
    ("gauge", "Kelembapan", "gauge_lembap", 10),
    ("tunas-kecil", "Tunas", "sprout", 12),
    ("hidroponik", "Hidroponik", "hidro", 10),
    ("kode", "</>", "code_mark", 12),
    ("wifi", "Sinyal", "wifi", 12),
    ("kilau", "Kilau", "sparkle", 0),
]
manifest = []
for sid, label, src, cut in STICKERS:
    im = Image.open(asset(src)).convert("RGBA")
    im = im.crop(im.getbbox())
    im = fit_im(im, 420)
    if cut:
        im = diecut(im, cut)
    im = fit_im(im, 360)
    im.save(f"{PUB}/stickers/{sid}.webp", "WEBP", quality=90, alpha_quality=100, method=6)
    manifest.append(dict(id=sid, label=label, src=f"./stickers/{sid}.webp", width=im.width, height=im.height))
json.dump(manifest, open(f"{ROOT}/src/js/themeStickers.json", "w"), indent=1)

# --- UI ---------------------------------------------------------------------------------------
fit_im(Image.open(asset("logo_lab")), 160).save(f"{PUB}/brand/logo.webp", "WEBP", quality=92, alpha_quality=100, method=6)
fit_im(Image.open(asset("logo_fasilkom_putih")), 520).save(f"{PUB}/brand/fasilkom.webp", "WEBP", quality=92, alpha_quality=100, method=6)
fit_im(Image.open(asset("logo_unej")), 140).save(f"{PUB}/brand/unej.webp", "WEBP", quality=92, alpha_quality=100, method=6)
fit_im(Image.open(asset("logo_dies")), 220).save(f"{PUB}/brand/dies62.webp", "WEBP", quality=92, alpha_quality=100, method=6)
fit_im(Image.open(asset("tunas")), 760).save(f"{PUB}/brand/maskot.webp", "WEBP", quality=92, alpha_quality=100, method=6)
fit_im(Image.open(asset("tunas_cheer")), 760).save(f"{PUB}/brand/maskot-senang.webp", "WEBP", quality=92, alpha_quality=100, method=6)

# --- Virtual background 1920x1080 (subjek berdiri di tengah: isi diletakkan di sisi) ---------------
BW, BH = 1920, 1080


def bg(name, d):
    out = f"{GEN}/{name}.png"
    run(d.under + d.over, dict(width=BW, height=BH, name=name), f"{SRC}/bg-{name}.pcraft", out)
    Image.open(out).convert("RGB").save(f"{PUB}/backgrounds/{name}.jpg", quality=86)


# 1. Ladang irigasi asli dari web Lab
hero = Image.open(f"{LAB}/bg-hero.png").convert("RGB")
r = max(BW / hero.width, BH / hero.height)
hero = hero.resize((round(hero.width * r), round(hero.height * r)), Image.LANCZOS)
hero.crop(((hero.width - BW) // 2, (hero.height - BH) // 2, (hero.width - BW) // 2 + BW, (hero.height - BH) // 2 + BH)).save(f"{PUB}/backgrounds/filkom-ladang.jpg", quality=86)

# 2. Panggung Dies Natalis 62
d = Doc(BW, BH)
d.rect(0, 0, BW, BH, grad([(0, "#FFFDF6"), (1, "#F6ECD2")]), name="latar krem")
d.text(BW / 2, BH * 0.86, "62", 900, D_YEL, 800, "center", font=DISPLAY, opacity=0.12, name="62 latar")
d.path([dict(anchor=[BW * 0.45, BH], out=[BW * 0.7, BH - 260]), dict(anchor=[BW + 10, BH - 330], **{"in": [BW * 0.9, BH - 340]}), [BW + 10, BH]],
       grad([(0, D_GRN), (1, D_GRN2)], 0), opacity=0.2, name="sapuan daun")
d.path([dict(anchor=[-10, BH - 240], out=[BW * 0.15, BH - 300]), dict(anchor=[BW * 0.5, BH], **{"in": [BW * 0.3, BH - 120]}), [-10, BH]],
       grad([(0, D_YEL), (1, "#F5B800")], 0), opacity=0.25, name="sapuan kuning")
d.img("pennants_dies", BW / 2, 50, w=BW + 40, name="bendera")
d.img("logo_dies", 300, 560, h=640, name="logo dies natalis 62", shadow=0.15)
x = BW - 110
for n in reversed(["logo_unej", "logo_fasilkom", "logo_lab"]):
    w = 74 * (0.62 if aspect(n) > 2.5 else 1) * aspect(n)
    d.img(n, x - w / 2, 190, w=w, name=n)
    x -= w + 22
d.text(BW - 110, 300, "SELAMAT", 26, D_RED, 700, "right", track=500, name="selamat")
d.text(BW - 110, 372, "DIES NATALIS", 62, D_GRN2, 800, "right", font=DISPLAY, name="dies natalis")
d.text(BW - 110, 446, "KE-62", 62, D_RED, 800, "right", font=DISPLAY, name="ke-62")
d.text(BW - 110, 500, "UNIVERSITAS JEMBER · 1964–2026", 22, "#3A3B3D", 700, "right", track=120, name="unej")
d.text(BW - 110, 576, "Menumbuhkan Pengetahuan,", 40, D_GRN2, 600, "right", font=SERIF, italic=True, name="tema 1")
d.text(BW - 110, 626, "Menciptakan Dampak", 40, D_RED, 600, "right", font=SERIF, italic=True, name="tema 2")
d.bottom_img("tunas_cheer", BW - 260, BH - 40, h=330, name="si tunas", shadow=0.2)
SPK = [(640, 260), (700, 520), (620, 760), (560, 980), (90, 1000), (300, 1030), (1290, 300), (1240, 700),
       (1380, 860), (1860, 760), (1840, 960), (1500, 1010), (760, 380), (1180, 520)]
for i, (x, y) in enumerate(SPK):
    d.img(["sparkle", "sparkle_red", "sparkle_lime"][i % 3], x, y, w=26 + (i * 7) % 20, rot=(i * 17) % 40 - 20, name="kilau")
bg("filkom-dies62", d)

# 3. Dinding step-and-repeat Lab x Fasilkom
d = Doc(BW, BH)
d.rect(0, 0, BW, BH, grad([(0, "#253014"), (1, "#141A0A")]), name="dinding zaitun")
colw, rowh = 340, 220
for row in range(6):
    for col in range(7):
        x = col * colw + (colw / 2 if row % 2 else 0) - 60
        y = row * rowh + 20
        k = (row + col) % 3
        if k == 0:
            d.ellipse(x, y, 62, 62, CREAM, name="alas")
            d.img("logo_lab", x, y, w=112, name="logo lab")
        elif k == 1:
            d.img("logo_fasilkom_putih", x, y, w=230, name="fasilkom")
        else:
            d.text(x, y - 2, "TUMBUH BERSAMA", 24, LIME, 800, "center", font=DISPLAY, name="tumbuh")
            d.text(x, y + 30, "Lab Pertanian Cerdas", 20, CREAM, 600, "center", font=SERIF, italic=True, name="lab")
bg("filkom-dinding", d)

# 4. Kebun pintar ilustrasi: langit, bukit, hidroponik, drone, Si Tunas
d = Doc(BW, BH)
d.rect(0, 0, BW, BH, grad([(0, "#8FD0F0"), (0.7, "#E4F4E8")]), name="langit")
d.img("sun", 1700, 170, w=260, name="matahari")
for (x0, h0, c) in ((0, 640, "#B9D77A"), (700, 600, "#9DC35A"), (-300, 760, "#86AE45")):
    d.path([dict(anchor=[x0 - 200, BH], out=[x0 + 100, h0 - 40]), dict(anchor=[x0 + 700, h0], **{"in": [x0 + 400, h0 - 60]}, out=[x0 + 1100, h0 + 40]),
            dict(anchor=[x0 + 1700, BH], **{"in": [x0 + 1400, h0 + 30]})], c, name="bukit")
d.path([[0, 860], [BW, 820], [BW, BH], [0, BH]], grad([(0, "#6E9A34"), (1, "#4C7224")]), name="tanah")
for i in range(9):
    y = 880 + i * 24
    d.line([[0, y], [BW, y - 40 + i * 2]], "#5E862C", 6, opacity=0.5, name="baris tanam")
d.img("drone", 420, 230, w=360, name="drone", shadow=0.25)
d.img("wifi", 640, 130, w=110, rot=20, name="sinyal")
d.bottom_img("hidro_wide", 360, 1000, w=640, name="hidroponik kiri")
d.bottom_img("hidro_wide", 1560, 1000, w=640, name="hidroponik kanan")
d.bottom_img("sensor", 760, 1060, h=240, rot=-6, name="sensor")
d.bottom_img("tunas", 1130, 975, h=300, name="si tunas", shadow=0.25)
d.img("gauge_lembap", 230, 520, w=300, name="gauge", shadow=0.3)
d.img("bub_tani", 1330, 600, w=300, name="tani cerdas")
bg("filkom-kebun", d)

# --- Ikon PWA: Si Tunas di lingkaran zaitun ------------------------------------------------------
tun = Image.open(asset("tunas_cheer")).convert("RGBA")


def icon(size, scale, bg_col=None, round_bg=True):
    c = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    if bg_col:
        lay = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        from PIL import ImageDraw
        dr = ImageDraw.Draw(lay)
        if round_bg:
            dr.ellipse([0, 0, size - 1, size - 1], fill=bg_col)
        else:
            dr.rectangle([0, 0, size, size], fill=bg_col)
        c.alpha_composite(lay)
    t = tun.copy()
    t.thumbnail((round(size * scale), round(size * scale)), Image.LANCZOS)
    c.alpha_composite(t, ((size - t.width) // 2, (size - t.height) // 2 + round(size * 0.02)))
    return c


icon(192, 0.78, "#E9F2C9").save(f"{PUB}/icons/icon-192.png")
icon(512, 0.78, "#E9F2C9").save(f"{PUB}/icons/icon-512.png")
icon(512, 0.62, "#1E2611", round_bg=False).convert("RGB").save(f"{PUB}/icons/icon-maskable-512.png")
icon(180, 0.78, "#E9F2C9", round_bg=False).convert("RGB").save(f"{PUB}/icons/apple-touch-icon.png")
buf = io.BytesIO()
icon(96, 0.8, "#E9F2C9").save(buf, "PNG", optimize=True)
data = base64.b64encode(buf.getvalue()).decode()
open(f"{PUB}/icons/favicon.svg", "w").write(
    f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 96 96"><image width="96" height="96" xlink:href="data:image/png;base64,{data}"/></svg>\n')
print("brand ok", len(manifest), "stiker")
