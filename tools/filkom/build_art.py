#!/usr/bin/env python3
"""Ilustrasi vektor tema Fasilkom × Lab Pertanian Cerdas, digambar dengan mesin PhotoCraft.

Hasil: PNG transparan di assets/ + sumber .pcraft berlayer di sumber/.
Jalankan: python3 tools/filkom/build_art.py [nama ...]
"""
import random, sys
from concurrent.futures import ThreadPoolExecutor
from pc import *


def grad(a, b, angle=-90):
    return {"gradient": {"stops": [[0, a], [1, b]], "angle": angle}}


METAL = grad("#E4E7DD", "#8E9486", 0)


# ---------------------------------------------------------------------------
# Si Tunas: robot pot pintar, tunas di kepala, lengan sirkuit seperti node logo Lab
# ---------------------------------------------------------------------------
def tunas(pose="wave"):
    d = Doc(820, 1000)
    d.ellipse(400, 948, 230, 26, SOIL, opacity=0.18, name="bayangan")
    for x in (300, 500):
        d.rect(x - 14, 860, 28, 84, METAL, r=8, stroke=INK, sw=7, name="probe sensor")
    # Lengan sirkuit
    if pose == "wave":
        arms = [([[208, 700], [128, 700]], (98, 700)), ([[592, 680], [650, 680], [700, 600]], (712, 576))]
    else:  # cheer: dua lengan terangkat
        arms = [([[206, 680], [150, 680], [100, 600]], (88, 576)), ([[594, 680], [650, 680], [700, 600]], (712, 576))]
    for pts, (nx, ny) in arms:
        d.line(pts, INK, 15, name="lengan sirkuit")
        d.ellipse(nx, ny, 30, 30, LIME, stroke=INK, sw=11, name="node")
    # Badan pot
    d.path([[186, 500], [614, 500], [576, 880], [224, 880]], grad("#9AB13E", "#66792A"), INK, 15, name="badan pot")
    d.path([[234, 524], [296, 524], [262, 860], [246, 860]], WHITE, opacity=0.22, name="kilap")
    d.rect(158, 450, 484, 86, grad("#56643A", "#3B4429"), r=30, stroke=INK, sw=15, name="bibir pot")
    d.rect(186, 462, 428, 16, WHITE, r=8, opacity=0.14, name="kilap bibir")
    # Layar wajah
    d.rect(256, 572, 288, 192, grad("#2A341C", "#12170A"), r=48, stroke=INK, sw=10, name="layar")
    d.rect(276, 586, 120, 18, WHITE, r=9, opacity=0.08, name="pantulan layar")
    if pose == "wave":
        for cx in (336, 464):
            d.ellipse(cx, 658, 27, 31, LIME, name="mata")
            d.ellipse(cx - 9, 648, 8, 8, WHITE, name="kilau mata")
    else:
        for cx in (336, 464):
            d.path([dict(anchor=[cx - 26, 668], out=[cx - 22, 628]), dict(anchor=[cx + 26, 668], **{"in": [cx + 22, 628]})],
                   None, LIME, 12, closed=False, name="mata senang")
    d.path([dict(anchor=[364, 712], out=[380, 742]), dict(anchor=[436, 712], **{"in": [420, 742]})],
           None, LIME, 11, closed=False, name="senyum")
    for cx in (292, 508):
        d.ellipse(cx, 712, 18, 11, "#F06A45", opacity=0.9, name="pipi")
    for i, c in enumerate((RED, GOLD, LIME)):
        d.ellipse(364 + i * 36, 812, 12, 12, c, stroke=INK, sw=5, name="led")
    # Batang dan daun
    d.path([dict(anchor=[400, 458], out=[400, 400]), dict(anchor=[396, 282], **{"in": [392, 340]})],
           None, INK, 18, closed=False, name="batang")
    d.path(leaf_knots((392, 334), (196, 214), 70, 0.1), grad("#AECB46", "#6E8A25", 135), INK, 12, name="daun kiri")
    d.line([[386, 328], [250, 248]], INK, 8, name="tulang daun")
    d.path(leaf_knots((402, 292), (624, 132), 84, -0.1), grad("#C2E254", "#7A9A2A", 45), INK, 12, name="daun kanan")
    d.line([[408, 286], [566, 176]], INK, 8, name="tulang daun")
    # Sinyal
    for i, c in enumerate((RED, GOLD)):
        r = 46 + i * 40
        d.line(arc_pts(286, 166, r, 200, 250, 12), c, 11, name="sinyal")
    return d


# ---------------------------------------------------------------------------
# Daun lepas untuk taburan
# ---------------------------------------------------------------------------
def leaf(variant):
    d = Doc(420, 420)
    a, b = [("#B9DD4E", "#6E8A25"), ("#8FAE36", "#3F5A18"), ("#D5EE7A", "#94B23A")][variant]
    d.path(leaf_knots((60, 360), (370, 50), 95, 0.15 * (variant - 1)), grad(a, b, 45), INK, 9, name="daun")
    d.path([dict(anchor=[70, 350], out=[180, 260]), dict(anchor=[352, 70], **{"in": [260, 160]})], None, INK, 7, closed=False, name="tulang")
    return d


# ---------------------------------------------------------------------------
# Sensor kelembapan tanah: PCB garpu
# ---------------------------------------------------------------------------
def sensor():
    d = Doc(360, 900)
    pcb = grad("#5C7A22", "#3E5517", 0)
    d.path([[60, 120], [300, 120], [300, 420], [262, 420], [262, 820], [232, 860], [202, 820], [202, 420],
            [158, 420], [158, 820], [128, 860], [98, 820], [98, 420], [60, 420]], pcb, INK, 12, name="pcb garpu")
    for x in (128, 232):
        d.rect(x - 12, 430, 24, 360, grad("#F6D86A", "#C9961C", 0), r=12, name="jalur emas")
    for i in range(3):
        d.rect(100 + i * 60, 40, 40, 100, METAL, r=6, stroke=INK, sw=6, name="pin")
        d.rect(88 + i * 60, 110, 64, 30, "#1D1D1D", r=4, name="header")
    d.rect(120, 190, 120, 70, "#1C2410", r=10, stroke=INK, sw=6, name="ic")
    d.ellipse(110, 330, 16, 16, RED, stroke=INK, sw=5, name="led")
    d.ellipse(250, 330, 22, 22, GOLD, stroke=INK, sw=5, name="kapasitor")
    d.text(180, 312, "SOIL", 30, LIME, 700, "center", font="IBM Plex Mono", name="label")
    return d


# ---------------------------------------------------------------------------
# Chip mikrokontroler dengan logo daun
# ---------------------------------------------------------------------------
def chip():
    d = Doc(640, 640)
    for i in range(6):
        o = 170 + i * 60
        for (x, y, w, h) in ((o - 12, 60, 24, 70), (o - 12, 510, 24, 70), (60, o - 12, 70, 24), (510, o - 12, 70, 24)):
            d.rect(x, y, w, h, METAL, r=6, stroke=INK, sw=5, name="kaki chip")
    d.rect(110, 110, 420, 420, grad("#2E3A1C", "#141A0B", 120), r=44, stroke=INK, sw=14, name="badan chip")
    d.rect(140, 140, 360, 360, None, r=30, stroke=OLIVE, sw=4, name="garis dalam")
    d.ellipse(170, 170, 14, 14, GOLD, name="penanda")
    d.path(leaf_knots((300, 380), (230, 220), 46, 0), grad(LIME, "#7A9A2A", 45), None, name="daun kiri")
    d.path(leaf_knots((330, 380), (430, 210), 58, 0), grad(LIME, "#7A9A2A", 45), None, name="daun kanan")
    d.line([[320, 440], [320, 370]], LIME, 12, name="batang")
    d.text(320, 480, "AGRI-32", 34, GOLD, 700, "center", font="IBM Plex Mono", name="label")
    return d


# ---------------------------------------------------------------------------
# Drone pemantau lahan
# ---------------------------------------------------------------------------
def drone():
    d = Doc(1000, 520)
    for x in (130, 870):
        d.line([[x, 150], [x, 110]], INK, 14, name="poros")
        d.ellipse(x, 104, 120, 20, "#DCE6C4", stroke=INK, sw=6, opacity=0.85, name="baling")
    for side in (-1, 1):
        d.line([[500 + side * 120, 230], [500 + side * 370, 150]], INK, 34, name="lengan")
        d.line([[500 + side * 120, 230], [500 + side * 370, 150]], "#5E6A3C", 20, name="lengan isi")
        d.ellipse(500 + side * 370, 160, 44, 30, OLIVE_D, stroke=INK, sw=8, name="motor")
    d.rect(330, 170, 340, 150, grad("#E9EDE0", "#B9C0A8"), r=60, stroke=INK, sw=12, name="badan drone")
    d.rect(370, 190, 260, 30, WHITE, r=15, opacity=0.5, name="kilap")
    d.rect(380, 240, 240, 26, OLIVE, r=13, name="pita")
    d.ellipse(500, 352, 58, 52, "#1E2414", stroke=INK, sw=10, name="kamera")
    d.ellipse(500, 352, 30, 30, grad("#7FA0C8", "#1B2A44", 120), stroke=GOLD, sw=5, name="lensa")
    d.ellipse(490, 342, 8, 8, WHITE, name="kilau")
    d.ellipse(360, 252, 10, 10, RED, name="led")
    d.ellipse(640, 252, 10, 10, LIME, name="led")
    for x in (400, 600):
        d.line([[x, 316], [x - 20 * (1 if x < 500 else -1), 420]], INK, 12, name="kaki")
        d.line([[x - 60, 420], [x + 20, 420]] if x < 500 else [[x - 20, 420], [x + 60, 420]], INK, 12, name="kaki")
    # Sinar pindai
    d.path([[470, 420], [530, 420], [700, 520], [300, 520]], LIME, opacity=0.25, name="sinar pindai")
    return d


# ---------------------------------------------------------------------------
# Pipa hidroponik dengan selada
# ---------------------------------------------------------------------------
def hidro(n=4, w=1200):
    d = Doc(w, 560)
    gap = w / n
    rnd = random.Random(3)
    for i in range(n):
        cx = gap * (i + 0.5)
        # selada: daun bulat bertumpuk membentuk kubah
        blobs = [(-70, 250, 62, 70), (70, 250, 62, 70), (-40, 200, 66, 76), (40, 200, 66, 76), (0, 165, 64, 72), (0, 240, 70, 64)]
        for k, (ox, oy, rx, ry) in enumerate(blobs):
            cols = [("#C6EB5A", "#7A9A2A"), ("#AECB46", "#5E7A1E"), ("#D9F08A", "#8FAE36")][k % 3]
            d.ellipse(cx + ox + rnd.uniform(-6, 6), oy + rnd.uniform(-6, 6), rx, ry, grad(*cols), stroke=INK, sw=8, name="daun selada")
        for ox in (-40, 0, 40):
            d.line([[cx + ox * 0.4, 296], [cx + ox, 200]], "#EAF5B8", 6, name="urat selada", opacity=0.7)
        d.rect(cx - 62, 300, 124, 70, grad("#3B4429", "#232B16"), r=12, stroke=INK, sw=8, name="netpot")
        for j in range(3):
            d.line([[cx - 30 + j * 30, 370], [cx - 30 + j * 30 + rnd.uniform(-15, 15), 470]], "#E9E3C8", 6, name="akar")
    d.rect(10, 350, w - 20, 160, grad("#FFFFFF", "#C9CFBE"), r=80, stroke=INK, sw=12, name="pipa")
    d.rect(60, 372, w - 120, 22, WHITE, r=11, opacity=0.8, name="kilap pipa")
    d.rect(10, 470, w - 20, 18, OLIVE, r=9, opacity=0.35, name="air")
    for i in range(n):
        cx = gap * (i + 0.5)
        d.rect(cx - 72, 340, 144, 34, grad("#56643A", "#3B4429"), r=10, stroke=INK, sw=8, name="bibir lubang")
    return d


# ---------------------------------------------------------------------------
# Kartu gauge seperti dashboard IoT web Lab
# ---------------------------------------------------------------------------
def gauge(label="KELEMBAPAN TANAH", value=68, unit="%", color=LIME):
    d = Doc(560, 420)
    d.rect(10, 10, 540, 400, grad("#2A341C", "#151A0C"), r=36, stroke=INK, sw=10, name="kartu", shadow=0.35)
    d.text(46, 70, label, 24, "#C9D4A8", 700, track=80, font="Montserrat", name="label")
    d.ellipse(500, 60, 10, 10, LIME, name="status online")
    d.line(arc_pts(280, 300, 150, 180, 360), "#3E4A27", 30, name="busur latar", cap="round")
    d.line(arc_pts(280, 300, 150, 180, 180 + 180 * value / 100), color, 30, name="busur nilai", cap="round")
    d.text(280, 290, f"{value}{unit}", 84 if len(f"{value}{unit}") <= 3 else 62, WHITE, 700, "center", font="IBM Plex Mono", name="nilai")
    d.text(280, 350, "OPTIMAL", 22, color, 700, "center", track=200, name="status")
    return d


def droplet():
    d = Doc(300, 400)
    d.path([dict(anchor=[150, 30], out=[190, 120]), dict(anchor=[260, 260], **{"in": [250, 180]}, out=[260, 330]),
            dict(anchor=[150, 370], **{"in": [220, 370]}, out=[80, 370]), dict(anchor=[40, 260], **{"in": [40, 330]}, out=[50, 180])],
           grad("#9ED8F0", "#2F86C0", 90), INK, 12, name="tetes air")
    d.path(leaf_knots((95, 270), (120, 170), 14, 0), WHITE, opacity=0.7, name="kilau")
    return d


def sun():
    d = Doc(400, 400)
    import math
    for i in range(12):
        a = math.radians(i * 30)
        d.line([[200 + 120 * math.cos(a), 200 + 120 * math.sin(a)], [200 + 170 * math.cos(a), 200 + 170 * math.sin(a)]], GOLD, 18, name="sinar")
    d.ellipse(200, 200, 96, 96, grad("#FFE27A", "#F2B020"), stroke=INK, sw=10, name="matahari")
    return d


def wifi():
    d = Doc(360, 300)
    for i, c in enumerate((LIME, GOLD, RED)):
        d.line(arc_pts(180, 260, 60 + i * 60, 225, 315, 20), c, 26, name="gelombang")
    d.ellipse(180, 252, 22, 22, LIME, name="titik")
    return d


def code_mark():
    """Tanda </> ala chevron logo Fasilkom."""
    d = Doc(640, 340)
    d.path([[170, 30], [250, 30], [150, 170], [250, 310], [170, 310], [60, 170]], grad("#F05A28", "#C8300E", 135), name="chevron kiri")
    d.path([[450, 30], [370, 30], [470, 170], [370, 310], [450, 310], [560, 170]], grad("#F05A28", "#C8300E", 135), name="chevron kanan")
    d.path([[372, 30], [444, 30], [248, 310], [176, 310]], {"gradient": {"stops": [[0, "#C99A06"], [0.5, "#FFE65A"], [1, "#D9A90E"]], "angle": 120}}, name="garis emas")
    return d


def bubble(text, fill, color, w, tail="left", size=46):
    h = 150
    d = Doc(w, h + 40)
    tx = 70 if tail == "left" else w - 132
    d.path([[tx, h - 34], [tx + 62, h - 34], [tx + (0 if tail == "left" else 62), h + 34]], fill, INK, 8, name="ekor")
    d.rect(8, 8, w - 16, h - 28, fill, r=48, stroke=INK, sw=8, name="gelembung")
    d.rect(tx + 7, h - 32, 48, 12, fill, name="sambung ekor")
    d.text(w / 2, (h - 20) / 2 + size * 0.36, text, size, color, 700, "center", name="teks")
    return d



# ---------------------------------------------------------------------------
# Laptop yang ditumbuhi tunas: komputer x pertanian
# ---------------------------------------------------------------------------
def laptop():
    d = Doc(900, 760)
    # tunas tumbuh dari balik layar
    d.path([dict(anchor=[560, 250], out=[560, 180]), dict(anchor=[600, 60], **{"in": [570, 110]})], None, INK, 16, closed=False, name="batang")
    d.path(leaf_knots((590, 120), (440, 30), 56, 0.1), grad("#AECB46", "#6E8A25", 135), INK, 10, name="daun")
    d.path(leaf_knots((600, 70), (790, 20), 66, -0.1), grad("#C2E254", "#7A9A2A", 45), INK, 10, name="daun")
    d.rect(170, 150, 560, 380, grad("#4A4B4D", "#2E2F31"), r=34, stroke=INK, sw=14, name="bingkai layar")
    d.rect(204, 184, 492, 312, grad("#1B2410", "#0E1308"), r=14, name="layar")
    rnd = random.Random(4)
    cols = [LIME, GOLD, "#F06A45", "#9ED8F0", CREAM]
    y = 222
    for i in range(7):
        x = 236 + (i in (2, 3, 5)) * 34
        for k in range(rnd.randint(1, 3)):
            w = rnd.randint(40, 130)
            if x + w > 660:
                break
            d.rect(x, y, w, 16, cols[(i + k) % 5], r=8, opacity=0.9, name="kode")
            x += w + 16
        y += 38
    d.text(640, 474, "</>", 34, RED, 700, "right", font="IBM Plex Mono", name="tanda kode")
    d.path([[110, 540], [790, 540], [860, 650], [40, 650]], grad("#D9DCD2", "#9EA394"), INK, 14, name="badan bawah")
    d.rect(360, 560, 180, 26, "#7C8172", r=13, name="touchpad")
    d.rect(30, 646, 840, 40, grad("#B7BBAE", "#8E9486"), r=18, stroke=INK, sw=12, name="alas")
    return d


def sparkle(color=GOLD):
    d = Doc(300, 300)
    d.cmd("shape.create", kind="star", rect=[20, 20, 260, 260], sides=4, starRatio=0.32, fill=color,
          stroke=dict(width=10, color=INK, align="inside", join="round"), name="kilau")
    return d


def pennants(cols=(D_RED, D_YEL, D_GRN), count=9, w=1400):
    d = Doc(w, 240)
    tri = w / count
    sag = lambda t: 14 + 30 * (1 - (2 * t - 1) ** 2)
    pts = [[t, sag(t / w)] for t in range(0, w + 1, 20)]
    for i in range(count):
        x0, x1 = i * tri + 6, (i + 1) * tri - 6
        y0, y1 = sag(x0 / w), sag(x1 / w)
        d.path([[x0, y0], [x1, y1], [(x0 + x1) / 2, max(y0, y1) + tri * 0.95]], cols[i % len(cols)], INK, 5, name="bendera")
    d.line(pts, INK, 6, name="tali")
    return d


def sprout():
    d = Doc(420, 380)
    d.path([dict(anchor=[30, 340], out=[90, 250]), dict(anchor=[390, 340], **{"in": [330, 250]})], grad("#7A5A36", "#4E3820"), INK, 10, name="tanah")
    d.path([dict(anchor=[210, 290], out=[210, 230]), dict(anchor=[206, 150], **{"in": [204, 190]})], None, INK, 14, closed=False, name="batang")
    d.path(leaf_knots((204, 190), (60, 110), 52, 0.1), grad("#AECB46", "#6E8A25", 135), INK, 10, name="daun")
    d.path(leaf_knots((208, 160), (370, 40), 62, -0.1), grad("#C2E254", "#7A9A2A", 45), INK, 10, name="daun")
    return d


ART = {
    "tunas": lambda: tunas("wave"),
    "tunas_cheer": lambda: tunas("cheer"),
    "leaf_a": lambda: leaf(0), "leaf_b": lambda: leaf(1), "leaf_c": lambda: leaf(2),
    "sensor": sensor, "chip": chip, "drone": drone,
    "hidro": hidro, "hidro_wide": lambda: hidro(6, 1800),
    "gauge_lembap": gauge,
    "gauge_suhu": lambda: gauge("SUHU UDARA", 28, "°C", GOLD),
    "droplet": droplet, "sun": sun, "wifi": wifi, "code_mark": code_mark,
    "bub_halo": lambda: bubble("Halo, Fasilkom!", CREAM, INK, 560),
    "bub_tani": lambda: bubble("Tani Cerdas!", LIME, INK, 440, "right"),
    "bub_panen": lambda: bubble("Panen Data!", RED, WHITE, 430),
    "bub_innovate": lambda: bubble("Innovate to Elevate", GRAY, WHITE, 640, "right", 40),
    "bub_dies": lambda: bubble("Selamat Dies Natalis ke-62!", D_YEL, INK, 820, "left", 42),
    "bub_tumbuh": lambda: bubble("Terus Tumbuh!", D_GRN, WHITE, 470, "right"),
    "laptop": laptop,
    "sparkle": sparkle, "sparkle_lime": lambda: sparkle(LIME), "sparkle_red": lambda: sparkle(D_RED),
    "pennants_dies": pennants, "pennants_lab": lambda: pennants((LIME, GOLD, RED, OLIVE)),
    "sprout": sprout,
}


if __name__ == "__main__":
    names = sys.argv[1:] or list(ART)
    with ThreadPoolExecutor(max_workers=6) as ex:
        for n, p in zip(names, ex.map(lambda n: render(ART[n](), n), names)):
            print("ok", n, size_of(p))
