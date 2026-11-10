"""Helper bersama untuk merakit gambar lewat mesin PhotoCraft (photocraft-cli).

Setiap gambar adalah daftar perintah engine (shape.create, type.create, file.placeEmbedded, ...),
sehingga sumber .pcraft-nya tetap berlayer dan bisa diedit di PhotoCraft.
"""
import json, math, os, subprocess, sys
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
WORK = "/home/bian/Pictures/PhotoCraft/photobooth_filkom"
A = f"{WORK}/assets"
GEN = f"{WORK}/assets/gen"
SRC = f"{WORK}/sumber"
TMP = f"{WORK}/_tmp"
CLI = "/home/bian/.local/bin/photocraft-cli"
LAB = "/home/bian/Documents/Lab PC/Lab Pertanian Cerdas/img"
for d in (A, GEN, SRC, TMP):
    os.makedirs(d, exist_ok=True)

# Palet: hijau zaitun logo Lab + abu, merah-oranye dan emas dari logo Fasilkom
INK = "#232B16"       # garis tepi ilustrasi
OLIVE_D = "#3B4429"   # cincin gelap logo Lab
OLIVE = "#7A8C2E"     # isi logo Lab
LEAF = "#9DBA3A"
LIME = "#C6EB5A"
SOIL = "#151A0C"
GRAY = "#4A4B4D"      # wordmark Fasilkom
RED = "#E2401A"
GOLD = "#F2C230"
CREAM = "#F7F5EC"
WHITE = "#FFFFFF"
# Warna logo Dies Natalis ke-62 UNEJ
D_RED, D_YEL, D_GRN, D_GRN2 = "#EE3338", "#FFCD2A", "#0B9A55", "#1E7A4C"

DISPLAY = "Unbounded"   # judul lebar-tebal, senada wordmark FASILKOM
SERIF = "Fraunces"      # kalimat motivasi, dipakai italic

SIZE_CACHE = {}


def size_of(path):
    if path not in SIZE_CACHE:
        with Image.open(path) as im:
            SIZE_CACHE[path] = im.size
    return SIZE_CACHE[path]


def asset(name):
    return name if name.startswith("/") else f"{A}/{name}.png"


class Doc:
    """Daftar perintah PhotoCraft. Lapisan di bawah foto (under) dan di atas foto (over)."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.under, self.over = [], []
        self.cur = self.under
        self.figures = []   # kotak karakter/objek besar yang tidak boleh menimpa slot foto

    def top(self):
        self.cur = self.over

    def cmd(self, cid, **p):
        self.cur.append((cid, p))

    def _style(self, opacity, shadow):
        if opacity is not None:
            self.cmd("layer.setProps", opacity=opacity)
        if shadow:
            self.cmd("layer.layerStyle.dropShadow", color="#0B0F06", opacity=shadow, distance=6, size=14, angle=90)

    def rect(self, x, y, w, h, fill, r=0, stroke=None, sw=0, name="bidang", opacity=None, shadow=None, align="inside"):
        p = dict(kind="roundedRect" if r else "rect", rect=[x, y, w, h], fill=fill, name=name)
        if r:
            p["radii"] = r
        if stroke:
            p["stroke"] = dict(width=sw, color=stroke, align=align)
        self.cmd("shape.create", **p)
        self._style(opacity, shadow)

    def ellipse(self, cx, cy, rx, ry, fill, stroke=None, sw=0, opacity=None, name="lingkaran", shadow=None, align="inside"):
        p = dict(kind="ellipse", rect=[cx - rx, cy - ry, rx * 2, ry * 2], fill=fill, name=name)
        if stroke:
            p["stroke"] = dict(width=sw, color=stroke, align=align)
        self.cmd("shape.create", **p)
        self._style(opacity, shadow)

    def path(self, knots, fill=None, stroke=None, sw=0, closed=True, cap="round", name="path", opacity=None, shadow=None, subpaths=None):
        sp = subpaths or [dict(closed=closed, knots=knots)]
        p = dict(kind="path", path=dict(subpaths=sp), fill=fill, name=name)
        if stroke:
            p["stroke"] = dict(width=sw, color=stroke, align="center", cap=cap, join="round")
        self.cmd("shape.create", **p)
        self._style(opacity, shadow)

    def line(self, pts, color, sw, name="garis", opacity=None, cap="round"):
        self.path([list(map(float, p)) for p in pts], None, color, sw, closed=False, cap=cap, name=name, opacity=opacity)

    def text(self, x, y, s, size, color=WHITE, weight=700, align="left", track=0, font="Montserrat", name=None, opacity=None, italic=False):
        p = dict(x=x, y=y, text=s, font=font, weight=weight, size=size, color=color, align=align, tracking=track, name=name or s[:24])
        if italic:
            p["italic"] = True
        self.cmd("type.create", **p)
        self._style(opacity, None)

    def img(self, path, cx, cy, w=None, h=None, rot=0, shadow=None, opacity=None, name=None, figure=False):
        path = asset(path)
        iw, ih = size_of(path)
        scale = 100 * (w / iw if w else h / ih)
        if figure:
            bw, bh = iw * scale / 100, ih * scale / 100
            self.figures.append((cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2, name))
        self.cmd("file.placeEmbedded", path=path, scale=round(scale, 3), center=[cx, cy], fit=False)
        self.cmd("layer.setProps", name=name or os.path.basename(path).split(".")[0])
        if rot:
            self.cmd("edit.transform", rotate=rot)
        self._style(opacity, shadow)

    def bottom_img(self, path, cx, bottom, h=None, w=None, **k):
        iw, ih = size_of(asset(path))
        hh = h if h else w * ih / iw
        self.img(path, cx, bottom - hh / 2, w=w, h=h, **k)

    def cover(self, path, x=0, y=0, w=None, h=None, pos=0.5, name=None):
        """Gambar menutup bidang, dipotong dulu supaya pas."""
        w, h = round(w or self.w), round(h or self.h)
        src = asset(path)
        key = f"{GEN}/cov_{os.path.basename(src).split('.')[0]}_{w}x{h}_{int(pos * 100)}.png"
        if not os.path.exists(key):
            im = Image.open(src).convert("RGBA")
            r = max(w / im.width, h / im.height)
            nw, nh = round(im.width * r), round(im.height * r)
            im = im.resize((nw, nh), Image.LANCZOS)
            left, topy = (nw - w) // 2, round((nh - h) * pos)
            im.crop((left, topy, left + w, topy + h)).save(key)
        self.img(key, x + w / 2, y + h / 2, w=w, name=name)


def leaf_knots(base, tip, width, bend=0.0):
    """Daun dua sisi melengkung dari pangkal ke ujung."""
    (x0, y0), (x1, y1) = base, tip
    L = math.hypot(x1 - x0, y1 - y0)
    dx, dy = (x1 - x0) / L, (y1 - y0) / L
    nx, ny = -dy, dx
    a, b = width * (1 + bend), width * (1 - bend)
    return [
        dict(anchor=[x0, y0], out=[x0 + dx * L * 0.25 + nx * a, y0 + dy * L * 0.25 + ny * a],
             **{"in": [x0 + dx * L * 0.25 - nx * b, y0 + dy * L * 0.25 - ny * b]}),
        dict(anchor=[x1, y1], out=[x1 - dx * L * 0.35 - nx * b * 0.7, y1 - dy * L * 0.35 - ny * b * 0.7],
             **{"in": [x1 - dx * L * 0.35 + nx * a * 0.7, y1 - dy * L * 0.35 + ny * a * 0.7]}),
    ]


def arc_pts(cx, cy, r, a0, a1, n=48):
    """Titik busur; sudut derajat, 0 = kanan, 90 = bawah (sumbu y layar)."""
    return [[cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))] for i in range(n + 1)]


def run(steps, new, *outs):
    args = [CLI, "run", "--new", json.dumps(new)]
    for cid, p in steps:
        args += ["--cmd", cid, "--params", json.dumps(p)]
    for out in outs:
        r = subprocess.run(args + ["--out", out], capture_output=True, text=True)
        if r.returncode:
            raise RuntimeError(f"{out}: {r.stderr[-900:]}")
        bad = [l for l in r.stderr.splitlines() if "not installed" in l]
        if bad:
            print("PERINGATAN", os.path.basename(out), bad[0][:160], file=sys.stderr)


def render(d, name, crop=True):
    """Render Doc ke PNG di assets + sumber .pcraft. Kembalikan path PNG."""
    new = dict(width=d.w, height=d.h, background="transparent", name=name)
    out = f"{A}/{name}.png"
    run(d.under + d.over, new, f"{SRC}/{name}.pcraft", out)
    if crop:
        im = Image.open(out)
        im.crop(im.getbbox()).save(out)
    SIZE_CACHE.pop(out, None)
    return out


# --- Ukur teks dengan file font yang sama dengan engine, agar judul pas tanpa meluber ---
from PIL import ImageFont
_FD = os.path.expanduser("~/.local/share/fonts")
FONT_FILES = {
    ("Unbounded", 800): f"{_FD}/filkom/Unbounded-ExtraBold.ttf",
    ("Unbounded", 600): f"{_FD}/filkom/Unbounded-SemiBold.ttf",
    ("Fraunces", 600): f"{_FD}/filkom/Fraunces-SemiBoldItalic.ttf",
    ("Montserrat", 700): f"{_FD}/negeri-asap/Montserrat-Bold.ttf",
    ("Montserrat", 600): f"{_FD}/negeri-asap/Montserrat-SemiBold.ttf",
    ("IBM Plex Mono", 700): f"{_FD}/negeri-asap/IBMPlexMono-SemiBold.ttf",
    ("IBM Plex Mono", 600): f"{_FD}/negeri-asap/IBMPlexMono-SemiBold.ttf",
}


def text_w(s, font, weight, size, track=0):
    f = ImageFont.truetype(FONT_FILES[(font, weight)], 100)
    return f.getlength(s) * size / 100 + len(s) * track / 1000 * size


def fit(s, font, weight, size, maxw, track=0):
    """Ukuran terbesar <= size yang membuat teks muat di maxw."""
    w = text_w(s, font, weight, size, track)
    return size if w <= maxw else size * maxw / w
