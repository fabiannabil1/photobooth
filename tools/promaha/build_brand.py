#!/usr/bin/env python3
"""Stiker, virtual background, logo UI, dan ikon PWA Promahadesa. Jalankan setelah build_assets.py."""
import base64, io, json, os, subprocess
from PIL import Image
import importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(f"{HERE}/../..")
PC = "/home/bian/Pictures/PhotoCraft"
WORK = f"{PC}/photobooth_promaha"
A = f"{WORK}/assets"
CLI = "/home/bian/.local/bin/photocraft-cli"
PUB = f"{ROOT}/public"
for d in ("stickers", "brand", "backgrounds", "icons"):
    os.makedirs(f"{PUB}/{d}", exist_ok=True)
NAVY, LIME, GOLD, CREAM = "#0E1F4D", "#A8CF45", "#D9B24C", "#FFF8E7"


def run(new, steps, *outs):
    args = [CLI, "run", "--new", json.dumps(new)]
    for c, p in steps:
        args += ["--cmd", c, "--params", json.dumps(p)]
    for o in outs:
        subprocess.run(args + ["--out", o], check=True, capture_output=True)


def fit(im, side):
    r = min(1, side / max(im.size))
    return im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)


def diecut(im, w):
    import numpy as np
    from scipy import ndimage as ni
    pad = w + 3
    base = Image.new("RGBA", (im.width + pad * 2, im.height + pad * 2), (0, 0, 0, 0))
    base.paste(im, (pad, pad), im)
    a = np.asarray(base.split()[3]) > 40
    ring = np.clip(w + 0.5 - ni.distance_transform_edt(~a), 0, 1)
    white = Image.fromarray(np.dstack([np.full(a.shape + (3,), 255, np.uint8), (ring * 255).astype(np.uint8)]), "RGBA")
    white.alpha_composite(base)
    return white


# --- Stiker teks: gelembung ucapan digambar di PhotoCraft ---------------------------------------
def bubble(name, text, fill, color, w, tail="left"):
    h = 150
    tx = 70 if tail == "left" else w - 110
    tail_path = dict(subpaths=[dict(closed=True, knots=[[tx, h - 34], [tx + 62, h - 34], [tx + (0 if tail == "left" else 62), h + 34]])])
    steps = [
        ("shape.create", dict(kind="path", path=tail_path, fill=fill, stroke=dict(width=8, color=NAVY, align="center", join="round"), name="ekor")),
        ("shape.create", dict(kind="roundedRect", rect=[8, 8, w - 16, h - 28], radii=48, fill=fill, stroke=dict(width=8, color=NAVY, align="inside"), name="gelembung")),
        ("shape.create", dict(kind="rect", rect=[tx + 7, h - 32, 48, 12], fill=fill, name="sambung ekor")),
        ("type.create", dict(x=w / 2, y=(h - 20) / 2 + 22, text=text, font="Montserrat", weight=700, size=46, color=color, align="center", name="teks")),
    ]
    f = f"{WORK}/assets/gen/{name}.png"
    run(dict(width=w, height=h + 40, background="transparent", name=name), steps, f)
    return Image.open(f)


bubbles = {
    "halo": bubble("halo", "Halo, Desa Kamal!", CREAM, NAVY, 560),
    "sehat": bubble("sehat", "Desa Sehat!", LIME, NAVY, 400, "right"),
    "pantau": bubble("pantau", "Pantau Bersama", "#2747C7", "#FFFFFF", 520),
}

STICKERS = [
    ("maskot", "Maskot", f"{A}/maskot_stand.png", 14),
    ("maskot-kamera", "Maskot Kamera", f"{A}/maskot_kamera.png", 14),
    ("maskot-kepala", "Kepala Maskot", f"{A}/maskot_head.png", 14),
    ("maskot-sepeda", "Maskot Sepeda", f"{A}/maskot_bike.png", 14),
    ("logo", "Logo Promaha", f"{A}/logo.png", 0),
    ("halo", "Halo!", bubbles["halo"], 0),
    ("sehat", "Desa Sehat", bubbles["sehat"], 0),
    ("pantau", "Pantau Bersama", bubbles["pantau"], 0),
    ("aplikasi", "Aplikasi PANTAU", f"{PC}/maskot_parts/ic_phone.png", 22),
    ("kaki", "Skrining Kaki", f"{PC}/maskot_parts/ic_foot.png", 22),
    ("aloebite", "Aloebite", f"{PC}/maskot_parts/ic_bottle.png", 22),
    ("blue-bloom", "Blue Bloom", f"{PC}/maskot_parts/ic_tea.png", 22),
    ("kader", "Kader", f"{PC}/maskot_parts/ic_kader.png", 22),
    ("toga", "TOGA", f"{PC}/maskot_parts/ic_plant.png", 22),
    ("telang", "Bunga Telang", f"{PC}/maskot_art/pot_telang.png", 8),
    ("lidah-buaya", "Lidah Buaya", f"{PC}/maskot_art/fg_aloe.png", 8),
]
manifest = []
for sid, label, src, cut in STICKERS:
    im = src if isinstance(src, Image.Image) else Image.open(src)
    im = im.convert("RGBA")
    im = im.crop(im.getbbox())
    if cut:
        im = diecut(im, cut)
    im = fit(im, 360)
    im.save(f"{PUB}/stickers/{sid}.webp", "WEBP", quality=90, alpha_quality=100, method=6)
    manifest.append(dict(id=sid, label=label, src=f"./stickers/{sid}.webp", width=im.width, height=im.height))
json.dump(manifest, open(f"{ROOT}/src/js/promahaStickers.json", "w"), indent=1)

# --- UI ------------------------------------------------------------------------------------------
fit(Image.open(f"{A}/logo.png"), 160).save(f"{PUB}/brand/logo.webp", "WEBP", quality=92, alpha_quality=100, method=6)
fit(Image.open(f"{A}/maskot_stand.png"), 760).save(f"{PUB}/brand/maskot.webp", "WEBP", quality=92, alpha_quality=100, method=6)

# --- Virtual background ---------------------------------------------------------------------------
BW, BH = 1920, 1080
# 1. Backdrop resmi 3x2 dari PDF
pdf = "/home/bian/Documents/Promahadesa/BACKDROP 3X2 (2).pdf"
subprocess.run(["pdftoppm", "-r", "60", "-png", "-singlefile", pdf, f"{A}/gen/backdrop_src"], check=True)
b = Image.open(f"{A}/gen/backdrop_src.png").convert("RGB")
r = BW / b.width
b = b.resize((BW, round(b.height * r)), Image.LANCZOS)
top = (b.height - BH) // 2
b.crop((0, top, BW, top + BH)).save(f"{PUB}/backgrounds/promaha-backdrop.jpg", quality=86)

# 2. Panorama desa
scene = Image.new("RGBA", (2000, 1280), (0, 0, 0, 0))
for n in ("bg_c_far", "bg_c_mid", "bg_c_near", "bg_c_road"):
    scene.alpha_composite(Image.open(f"{A}/{n}.png").convert("RGBA"))
scene = scene.crop(scene.getbbox())
scene_h = round(BW * scene.height / scene.width)
gen_scene = f"{A}/gen/panorama_scene.png"
scene.resize((BW, scene_h), Image.LANCZOS).save(gen_scene)
steps = [
    ("shape.create", dict(kind="rect", rect=[0, 0, BW, BH], fill=dict(gradient=dict(stops=[[0, "#62B6EE"], [0.72, "#CDEBFA"]], angle=90)), name="langit")),
    ("shape.create", dict(kind="ellipse", rect=[1560, 80, 170, 170], fill="#FFE27A", stroke=dict(width=8, color="#F6C445", align="center"), name="matahari")),
]
for f, x, y, s in [("cloud_a", 300, 180, 140), ("cloud_b", 880, 120, 110), ("cloud_a", 1360, 320, 90), ("cloud_b", 620, 390, 70)]:
    steps.append(("file.placeEmbedded", dict(path=f"{A}/{f}.png", scale=s, center=[x, y], fit=False)))
steps.append(("file.placeEmbedded", dict(path=gen_scene, scale=100, center=[BW / 2, BH - scene_h / 2], fit=False)))
run(dict(width=BW, height=BH, name="panorama"), steps, f"{WORK}/sumber/bg-panorama-desa.pcraft", f"{A}/gen/panorama.png")
Image.open(f"{A}/gen/panorama.png").convert("RGB").save(f"{PUB}/backgrounds/promaha-desa.jpg", quality=86)

# 3. Dinding step-and-repeat: logo dan nama program berselang-seling
steps = [("shape.create", dict(kind="rect", rect=[0, 0, BW, BH], fill=dict(gradient=dict(stops=[[0, "#081434"], [1, "#142C6B"]], angle=90)), name="dinding navy"))]
logo_w = Image.open(f"{A}/logo_192.png").width
colw, rowh = 320, 216
for row in range(6):
    for col in range(7):
        x = col * colw + (colw / 2 if row % 2 else 0) - 60
        y = row * rowh - 30
        if (row + col) % 2 == 0:
            steps.append(("file.placeEmbedded", dict(path=f"{A}/logo_192.png", scale=100 * 120 / logo_w, center=[x, y], fit=False)))
        else:
            steps.append(("type.create", dict(x=x, y=y - 2, text="KADER PANTAU", font="Montserrat", weight=700, size=30, color=LIME, align="center", name="nama")))
            steps.append(("type.create", dict(x=x, y=y + 26, text="Desa Kamal · UNEJ 2026", font="Montserrat", weight=600, size=18, color="#FFFFFF", align="center", name="sub")))
run(dict(width=BW, height=BH, name="step-repeat"), steps, f"{WORK}/sumber/bg-step-repeat.pcraft", f"{A}/gen/step.png")
Image.open(f"{A}/gen/step.png").convert("RGB").save(f"{PUB}/backgrounds/promaha-dinding.jpg", quality=86)

# --- Ikon PWA -------------------------------------------------------------------------------------
logo = Image.open(f"{A}/logo.png").convert("RGBA")
def icon(size, scale=1.0, bg=None):
    c = Image.new("RGBA", (size, size), bg or (0, 0, 0, 0))
    l = fit(logo, round(size * scale))
    if max(logo.size) < size * scale:
        l = logo.resize((round(size * scale), round(size * scale * logo.height / logo.width)), Image.LANCZOS)
    c.alpha_composite(l, ((size - l.width) // 2, (size - l.height) // 2))
    return c
icon(192).save(f"{PUB}/icons/icon-192.png")
icon(512).save(f"{PUB}/icons/icon-512.png")
icon(512, 0.8, NAVY).convert("RGB").save(f"{PUB}/icons/icon-maskable-512.png")
icon(180, 0.92, NAVY).convert("RGB").save(f"{PUB}/icons/apple-touch-icon.png")
buf = io.BytesIO()
icon(96).save(buf, "PNG", optimize=True)
data = base64.b64encode(buf.getvalue()).decode()
open(f"{PUB}/icons/favicon.svg", "w").write(
    f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 96 96"><image width="96" height="96" xlink:href="data:image/png;base64,{data}"/></svg>\n')
print("brand ok", len(manifest), "stiker")
