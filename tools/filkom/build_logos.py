#!/usr/bin/env python3
"""Siapkan logo: Lab Pertanian Cerdas, Fasilkom (asli dan putih), UNEJ, dan deret logo mitra."""
import numpy as np
from PIL import Image
from pc import A, LAB, ROOT


def trim(im):
    return im.crop(im.getbbox())


lab = trim(Image.open(f"{LAB}/Logo Pertanian Cerdas.png").convert("RGBA"))
lab.save(f"{A}/logo_lab.png")

unej = trim(Image.open("/home/bian/Documents/Laporan pengabdian/logo_unej.png").convert("RGBA"))
unej.save(f"{A}/logo_unej.png")

fas = Image.open(f"{LAB}/logo-fasilkom.png").convert("RGBA")
a = np.asarray(fas).astype(np.float32)
a[..., 3] = np.where(a[..., 3] < 8, 0, a[..., 3])
fas = trim(Image.fromarray(a.astype(np.uint8), "RGBA"))
fas.save(f"{A}/logo_fasilkom.png")

# Versi untuk latar gelap: abu wordmark jadi putih, chevron merah-emas tetap
px = np.asarray(fas).astype(np.float32)
rgb = px[..., :3]
sat = rgb.max(axis=2) - rgb.min(axis=2)
gray = sat < 40
rgb[gray] = 255
Image.fromarray(np.dstack([rgb, px[..., 3]]).astype(np.uint8), "RGBA").save(f"{A}/logo_fasilkom_putih.png")

# Deret mitra dari header resmi (Tut Wuri, UNEJ, BLU, Diktisaintek)
head = Image.open(f"{LAB}/header-logo-fik.webp").convert("RGBA")
mitra = trim(head.crop((600, 0, head.width, head.height)))
mitra.save(f"{A}/logo_mitra.png")
head_full = trim(head)
head_full.save(f"{A}/logo_header.png")
print("logo ok", lab.size, unej.size, fas.size, mitra.size)

# Logo Dies Natalis ke-62 UNEJ (file dari panitia, diletakkan di akar repo)
dies = trim(Image.open(f"{ROOT}/Desain-Logo-DIES-NATALIS-KE-62-Rev.png").convert("RGBA"))
dies.thumbnail((1400, 1400), Image.LANCZOS)
dies.save(f"{A}/logo_dies.png")
print("logo dies ok", dies.size)
