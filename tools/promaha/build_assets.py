#!/usr/bin/env python3
"""Siapkan aset dasar Promahadesa: potong maskot dari latar putih, bersihkan logo, buat varian."""
import os
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage as ni

PC = "/home/bian/Pictures/PhotoCraft"
V = "/home/bian/Documents/Promahadesa/Video/Motion-Graphic-Maskot"
OUT = f"{PC}/photobooth_promaha/assets"
os.makedirs(OUT, exist_ok=True)


def cutout(path, holes_below=None):
    """Latar putih yang tersambung ke tepi jadi transparan, tepinya dibersihkan dari sisa putih.

    holes_below: fraksi tinggi; bidang putih terkurung di bawah garis ini ikut dibuang (celah roda).
    """
    rgb = np.asarray(Image.open(path).convert("RGB")).astype(np.float32)
    lum = rgb.min(axis=2)
    white = lum > 226
    lab, _ = ni.label(white)
    edge_ids = set(np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]])) - {0}
    bg = np.isin(lab, list(edge_ids))
    if holes_below is not None:
        h = rgb.shape[0]
        for i, sl in enumerate(ni.find_objects(lab), 1):
            if sl and sl[0].start / h > holes_below and (lab[sl] == i).sum() > 12:
                bg |= lab == i
    # Bercak samar pada latar: buang komponen kecil yang bukan bagian figur
    fg = ~bg
    lab2, n2 = ni.label(fg)
    if n2 > 1:
        sizes = ni.sum(fg, lab2, range(1, n2 + 1))
        keep = np.isin(lab2, [i + 1 for i, s in enumerate(sizes) if s > 400])
        fg = keep
    # Celah putih kecil yang terkurung di antara lengan/kaki dan badan
    alpha = fg.astype(np.float32)
    band = ni.binary_dilation(~fg, iterations=2) & fg
    alpha[band] = np.clip((248 - lum[band]) / 60, 0, 1)
    alpha = np.clip(ni.gaussian_filter(alpha, 0.55), 0, 1)
    a3 = np.maximum(alpha, 0.2)[..., None]
    un = np.where(alpha[..., None] < 0.98, np.clip((rgb - 255 * (1 - a3)) / a3, 0, 255), rgb)
    im = Image.fromarray(np.dstack([un, alpha * 255]).astype(np.uint8), "RGBA")
    return im.crop(im.getbbox())


def diecut(im, width=12):
    """Bingkai putih ala stiker potong."""
    pad = width + 4
    base = Image.new("RGBA", (im.width + pad * 2, im.height + pad * 2), (0, 0, 0, 0))
    base.paste(im, (pad, pad), im)
    a = np.asarray(base.split()[3]) > 40
    d = ni.distance_transform_edt(~a)
    ring = np.clip(width + 0.5 - d, 0, 1)
    white = Image.fromarray(np.dstack([np.full(a.shape + (3,), 255, np.uint8), (ring * 255).astype(np.uint8)]), "RGBA")
    white.alpha_composite(base)
    return white


def fit(im, side):
    r = min(1, side / max(im.size))
    return im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)


stand = cutout(f"{PC}/maskot_src/stand.jpg")
head = cutout(f"{PC}/maskot_src/head.jpg")
bike = cutout(f"{V}/1793490630326.png", holes_below=0.5)
stand.save(f"{OUT}/maskot_stand.png")
head.save(f"{OUT}/maskot_head.png")
bike.save(f"{OUT}/maskot_bike.png")
bike.transpose(Image.FLIP_LEFT_RIGHT).save(f"{OUT}/maskot_bike_flip.png")

logo = Image.open(f"{PC}/maskot_photos/logo.png").convert("RGBA")
logo = logo.crop(logo.getbbox())
logo.save(f"{OUT}/logo.png")
fit(logo, 192).save(f"{OUT}/logo_192.png")

# Salin elemen pendukung ke satu folder agar .pcraft tidak bergantung pada banyak lokasi
ART = {"cloud_a": "maskot_art", "cloud_b": "maskot_art", "fg_aloe": "maskot_art", "fg_vine": "maskot_art",
       "petal": "maskot_art", "pot_jahe": "maskot_art", "pot_kunyit": "maskot_art", "pot_serai": "maskot_art",
       "pot_telang": "maskot_art", "bird": "maskot_art", "tape": "maskot_art", "sign_w": "maskot_art",
       "sign_s": "maskot_art", "leafbit": "maskot_art", "bg_c_far": "maskot_art", "bg_c_mid": "maskot_art",
       "bg_c_near": "maskot_art", "bg_c_road": "maskot_art", "bg_c_sky": "maskot_art", "bg_e": "maskot_art",
       "dusun0": "maskot_art", "ic_bottle": "maskot_parts", "ic_phone": "maskot_parts", "ic_foot": "maskot_parts",
       "ic_plant": "maskot_parts", "ic_kader": "maskot_parts", "ic_tea": "maskot_parts", "ic_house": "maskot_parts",
       "leaf_L1": "maskot_parts", "leaf_R1": "maskot_parts"}
for name, folder in ART.items():
    Image.open(f"{PC}/{folder}/{name}.png").convert("RGBA").save(f"{OUT}/{name}.png")
Image.open(f"{OUT}/fg_vine.png").transpose(Image.FLIP_LEFT_RIGHT).save(f"{OUT}/fg_vine_flip.png")
Image.open(f"{OUT}/fg_aloe.png").transpose(Image.FLIP_LEFT_RIGHT).save(f"{OUT}/fg_aloe_flip.png")

Image.open(f"{PC}/xbanner/logos.png").convert("RGBA").save(f"{OUT}/logos_mitra.png")
# Lapisan tanah di banner expo (daun bawah) dan pemandangan desa, tanpa tulisan
bn = Image.open(f"{PC}/banner_expo/bg.jpg").convert("RGB")
s = bn.width / 700
bn.crop((0, int(142 * s), bn.width, int(222 * s))).resize((1600, round(80 / 700 * 1600)), Image.LANCZOS).save(f"{OUT}/expo_scene.jpg", quality=92)
bn.crop((0, int(1345 * s), bn.width, int(1390 * s))).resize((1600, round(45 / 700 * 1600)), Image.LANCZOS).save(f"{OUT}/expo_leaves.jpg", quality=92)
print("assets ok", stand.size, head.size, bike.size)

# Maskot memegang kamera, digambar di PhotoCraft agar bentuk kameranya bisa diedit
import json, subprocess
sw, sh = stand.size
cx, cy = 432, 596   # letak kepalan tangan pada gambar berdiri
n = "#0E1F4D"
cmds = [
    ("file.placeEmbedded", dict(path=f"{OUT}/maskot_stand.png", scale=100, center=[sw / 2 + 40, sh / 2 + 10], fit=False)),
    ("shape.create", dict(kind="roundedRect", rect=[cx - 46, cy - 92, 62, 36], radii=8, fill="#3A4A78", stroke=dict(width=6, color=n, align="inside"), name="tombol kamera")),
    ("shape.create", dict(kind="roundedRect", rect=[cx - 118, cy - 66, 236, 146], radii=22, fill=dict(gradient=dict(stops=[[0, "#FDF6E3"], [1, "#E7D9B5"]], angle=90)), stroke=dict(width=8, color=n, align="inside"), name="badan kamera")),
    ("shape.create", dict(kind="rect", rect=[cx - 110, cy - 22, 220, 60], fill="#2747C7", name="pita kamera")),
    ("shape.create", dict(kind="ellipse", rect=[cx - 54, cy - 45, 108, 108], fill=n, name="lensa luar")),
    ("shape.create", dict(kind="ellipse", rect=[cx - 37, cy - 28, 74, 74], fill=dict(gradient=dict(stops=[[0, "#6C8CF0"], [1, "#16256C"]], angle=120)), stroke=dict(width=5, color="#D9B24C", align="center"), name="lensa")),
    ("shape.create", dict(kind="ellipse", rect=[cx - 22, cy - 20, 20, 20], fill="#FFFFFF", name="kilau")),
    ("shape.create", dict(kind="ellipse", rect=[cx + 74, cy - 54, 24, 24], fill="#A8CF45", stroke=dict(width=4, color=n, align="center"), name="lampu")),
]
args = ["/home/bian/.local/bin/photocraft-cli", "run", "--new", json.dumps(dict(width=sw + 120, height=sh + 40, background="transparent", name="maskot_kamera"))]
for c, p in cmds:
    args += ["--cmd", c, "--params", json.dumps(p)]
subprocess.run(args + ["--out", f"{OUT}/maskot_kamera_raw.png"], check=True, capture_output=True)
subprocess.run(args + ["--out", f"{PC}/photobooth_promaha/maskot_kamera.pcraft"], check=True, capture_output=True)
k = Image.open(f"{OUT}/maskot_kamera_raw.png")
k.crop(k.getbbox()).save(f"{OUT}/maskot_kamera.png")
print("kamera ok")

# Varian ber-tepi putih: tetap terbaca di frame gelap
for name, w in [("maskot_stand", 7), ("maskot_kamera", 7), ("maskot_head", 7), ("ic_bottle", 12), ("ic_tea", 12)]:
    diecut(Image.open(f"{OUT}/{name}.png").convert("RGBA"), w).save(f"{OUT}/{name}_dc.png")
