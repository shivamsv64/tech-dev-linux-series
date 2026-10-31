"""Animal & bird cast for "DevOps & SRE Zero to Hero" (Tech-dev).

Every character is drawn in code on a 600x800 canvas (feet at y~770) and scaled.
draw_animal(img, who, cx, base_y, height, mood, arms, t, talking, flip)
Voices: voice(who, n_syllables, rng) and call(who, rng) return mono float arrays at SR.
"""
import math, random
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageOps

SR = 44100
OUT = (15, 20, 36)          # outline ink
WHITEC = (255, 255, 255)
CYAN = (56, 189, 248); AMBER = (251, 191, 36); VIOLET = (167, 139, 250)
GREEN = (52, 211, 153); RED = (239, 68, 68)

CAST = {
    'ollie':  {'name': 'Ollie',  'animal': 'Owl',      'col': CYAN},
    'mitthu': {'name': 'Mitthu', 'animal': 'Parrot',   'col': GREEN},
    'bablu':  {'name': 'Bablu',  'animal': 'Beaver',   'col': AMBER},
    'gajju':  {'name': 'Gajju',  'animal': 'Elephant', 'col': VIOLET},
    'ashtu':  {'name': 'Ashtu',  'animal': 'Octopus',  'col': VIOLET},
    'kukdu':  {'name': 'Kukdu',  'animal': 'Rooster',  'col': AMBER},
    'kaalu':  {'name': 'Kaalu',  'animal': 'Crow',     'col': RED},
    'tortoise': {'name': 'Tortoise', 'animal': 'Tortoise', 'col': GREEN},
    'cheetah':  {'name': 'Cheetah',  'animal': 'Cheetah',  'col': AMBER},
}


# ------------------------------------------------------------------ helpers
def E(d, box, fill, w=7, outline=OUT):
    d.ellipse(box, fill=fill, outline=outline, width=w)


def poly(d, pts, fill, w=7, outline=OUT):
    d.polygon(pts, fill=fill)
    if w:
        d.line(pts + [pts[0]], fill=outline, width=w, joint='curve')


def blob(cx, cy, rx, ry, ang, n=28, pinch=0.0):
    """teardrop/ellipse points rotated by ang degrees (0 = pointing down)."""
    a = math.radians(ang)
    pts = []
    for i in range(n):
        th = 2 * math.pi * i / n
        x = rx * math.sin(th) * (1 - pinch * (0.5 - 0.5 * math.cos(th)))
        y = ry * (-math.cos(th))
        pts.append((cx + x * math.cos(a) - y * math.sin(a), cy + x * math.sin(a) + y * math.cos(a)))
    return pts


def wing(d, sh, length, width, ang, fill, tip=None):
    """wing hanging from shoulder sh; ang 0 = down, +ve = outward to the right."""
    a = math.radians(ang)
    cx = sh[0] + math.sin(a) * length * 0.5
    cy = sh[1] + math.cos(a) * length * 0.5
    pts = blob(cx, cy, width / 2, length / 2, -ang, pinch=0.5)
    poly(d, pts, fill, 6)
    if tip:
        tx = sh[0] + math.sin(a) * length * 0.82
        ty = sh[1] + math.cos(a) * length * 0.82
        poly(d, blob(tx, ty, width * 0.22, length * 0.2, -ang, pinch=0.4), tip, 4)


def wing_angles(arms, mood, phase):
    flap = math.sin(phase / 8 * 2 * math.pi)
    if arms == 'up' or mood in ('celebrate',):
        return 150 + 15 * flap, 150 + 15 * flap
    if mood == 'panic':
        return 120 + 30 * flap, 120 + 30 * flap
    if arms == 'wave':
        return 15, 120 + 25 * flap
    if arms == 'point':
        return 15, 95
    if arms == 'think':
        return 15, 60
    return 18, 18


def eyes(d, pts, r, mood, blink, iris=None, lid=None, look=(0.0, 0.0)):
    for k, (cx, cy) in enumerate(pts):
        if blink and mood not in ('happy', 'celebrate'):
            d.line([(cx - r, cy), (cx + r, cy)], fill=OUT, width=9)
            continue
        if mood in ('happy', 'celebrate'):
            d.arc([cx - r, cy - r * 0.7, cx + r, cy + r * 1.1], 200, 340, fill=OUT, width=11)
            continue
        E(d, [cx - r, cy - r, cx + r, cy + r], WHITEC, 6)
        lx, ly = look
        if mood == 'think':
            lx, ly = 0.35, -0.45
        elif mood == 'curious':
            lx, ly = 0.2, -0.1
        pr = r * (0.24 if mood == 'panic' else 0.42)
        px, py = cx + lx * r * 0.45, cy + ly * r * 0.45
        if iris and mood != 'panic':
            ir = r * 0.66
            d.ellipse([px - ir, py - ir, px + ir, py + ir], fill=iris)
        d.ellipse([px - pr, py - pr, px + pr, py + pr], fill=(8, 10, 20))
        hr = max(3, pr * 0.38)
        d.ellipse([px - pr * 0.55 - hr, py - pr * 0.55 - hr, px - pr * 0.55 + hr, py - pr * 0.55 + hr], fill=WHITEC)
        if mood in ('sly', 'angry') and lid:
            # heavy upper lid
            d.chord([cx - r - 2, cy - r - 2, cx + r + 2, cy + r + 2], 180, 360, fill=lid)
            d.line([(cx - r, cy), (cx + r, cy)], fill=OUT, width=6)
        # brows
        bw = r * 0.9
        if mood == 'curious' and k == 1:
            d.line([(cx - bw, cy - r - 22), (cx + bw, cy - r - 34)], fill=OUT, width=9)
        elif mood == 'panic':
            s = -1 if k == 0 else 1
            d.line([(cx - bw, cy - r - 18 - 10 * s), (cx + bw, cy - r - 18 + 10 * s)], fill=OUT, width=8)
        elif mood in ('angry', 'sly'):
            s = 1 if k == 0 else -1
            d.line([(cx - bw, cy - r - 14 - 14 * s), (cx + bw, cy - r - 14 + 14 * s)], fill=OUT, width=10)


def extras(d, mood, head_top=(300, 110)):
    x, y = head_top
    if mood == 'panic':
        poly(d, [(x + 200, y + 20), (x + 222, y + 75), (x + 178, y + 75)], CYAN, 0)
        d.ellipse([x + 176, y + 55, x + 224, y + 103], fill=CYAN)
    elif mood == 'think':
        for i, r in enumerate((12, 17, 24)):
            cx, cy = x + 190 + i * 34, y + 10 - i * 30
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(203, 213, 225))
    elif mood == 'curious':
        from PIL import ImageFont
        try:
            f = ImageFont.truetype('/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf', 110)
            d.text((x + 215, y + 10), '?', font=f, fill=AMBER, anchor='mm')
        except OSError:
            pass


def beak_v(d, cx, cy, w, h, talk, col, dark=(120, 40, 20)):
    """front-facing beak: upper triangle, lower triangle when open."""
    if talk:
        d.polygon([(cx - w * 0.55, cy + h * 0.25), (cx + w * 0.55, cy + h * 0.25), (cx, cy + h * 1.05)], fill=dark)
        poly(d, [(cx - w / 2, cy), (cx + w / 2, cy), (cx, cy + h * 0.6)], col, 5)
        poly(d, [(cx - w * 0.35, cy + h * 0.72), (cx + w * 0.35, cy + h * 0.72), (cx, cy + h * 1.1)], col, 5)
    else:
        poly(d, [(cx - w / 2, cy), (cx + w / 2, cy), (cx, cy + h)], col, 5)
        d.line([(cx - w * 0.3, cy + h * 0.35), (cx + w * 0.3, cy + h * 0.35)], fill=OUT, width=3)


def mouth(d, cx, cy, w, mood, talk, fill=(120, 30, 40)):
    if talk:
        E(d, [cx - w * 0.4, cy - w * 0.15, cx + w * 0.4, cy + w * 0.45], fill, 6)
        d.ellipse([cx - w * 0.22, cy + w * 0.12, cx + w * 0.22, cy + w * 0.4], fill=(240, 120, 130))
    elif mood == 'panic':
        pts = [(cx - w / 2 + i * w / 5, cy + (8 if i % 2 else -8)) for i in range(6)]
        d.line(pts, fill=OUT, width=7)
    elif mood == 'think':
        d.line([(cx - w * 0.35, cy + 6), (cx + w * 0.35, cy)], fill=OUT, width=7)
    elif mood in ('sly', 'angry'):
        d.arc([cx - w * 0.5, cy - w * 0.4, cx + w * 0.3, cy + w * 0.25], 20, 110, fill=OUT, width=7)
    elif mood == 'celebrate':
        d.chord([cx - w * 0.5, cy - w * 0.3, cx + w * 0.5, cy + w * 0.5], 0, 180, fill=fill, outline=OUT, width=6)
    else:
        d.arc([cx - w * 0.5, cy - w * 0.45, cx + w * 0.5, cy + w * 0.2], 25, 155, fill=OUT, width=7)


def feet3(d, x, y, col, s=1.0):
    for dx in (-26, 0, 26):
        d.line([(x, y - 30 * s), (x + dx * s, y)], fill=col, width=int(10 * s))
    d.line([(x, y - 30 * s), (x, y - 70 * s)], fill=col, width=int(11 * s))


# ------------------------------------------------------------------ characters
def draw_ollie(d, mood, arms, phase, blink, talk):
    BR, BRD, BEL, FACE = (139, 94, 60), (105, 70, 45), (226, 196, 156), (214, 178, 132)
    d.ellipse([170, 752, 430, 790], fill=(0, 0, 0, 80))
    feet3(d, 250, 772, (245, 158, 11)); feet3(d, 350, 772, (245, 158, 11))
    la, ra = wing_angles(arms, mood, phase)
    wing(d, (178, 450), 250, 110, -la, BRD, tip=BR)
    wing(d, (422, 450), 250, 110, ra, BRD, tip=BR)
    E(d, [160, 340, 440, 745], BR)
    E(d, [215, 450, 385, 725], BEL, 5)
    for r in range(4):  # belly feather scallops
        for c in range(3 - (r % 2)):
            x = 245 + c * 52 + (26 if r % 2 else 0)
            y = 500 + r * 50
            d.arc([x - 20, y - 14, x + 20, y + 16], 20, 160, fill=(176, 130, 90), width=5)
    # head + tufts
    poly(d, [(165, 175), (195, 60), (250, 135)], BRD)
    poly(d, [(435, 175), (405, 60), (350, 135)], BRD)
    E(d, [140, 100, 460, 420], BR)
    E(d, [168, 168, 300, 330], FACE, 5); E(d, [300, 168, 432, 330], FACE, 5)
    eyes(d, [(236, 248), (364, 248)], 56, mood, blink, iris=(245, 158, 11))
    beak_v(d, 300, 300, 46, 50, talk, (245, 158, 11))
    # cyan scarf
    d.rounded_rectangle([180, 400, 420, 446], 22, fill=CYAN, outline=OUT, width=6)
    poly(d, [(360, 430), (400, 430), (412, 520), (372, 512)], CYAN, 6)
    extras(d, mood, (300, 90))


def draw_mitthu(d, mood, arms, phase, blink, talk):
    G, GD, GL = (34, 197, 94), (21, 128, 61), (134, 239, 172)
    d.ellipse([190, 752, 410, 790], fill=(0, 0, 0, 80))
    # tail
    poly(d, [(300, 640), (360, 640), (420, 790), (370, 795)], (37, 99, 235), 6)
    poly(d, [(280, 640), (330, 640), (330, 798), (290, 798)], RED, 6)
    feet3(d, 260, 772, (148, 163, 184), 0.9); feet3(d, 340, 772, (148, 163, 184), 0.9)
    la, ra = wing_angles(arms, mood, phase)
    wing(d, (205, 430), 260, 105, -la, GD, tip=RED)
    wing(d, (395, 430), 260, 105, ra, GD, tip=RED)
    E(d, [190, 330, 410, 710], G)
    E(d, [235, 420, 365, 690], GL, 5)
    E(d, [170, 110, 430, 380], G)
    E(d, [190, 180, 290, 290], (254, 243, 199), 0)
    E(d, [310, 180, 410, 290], (254, 243, 199), 0)
    eyes(d, [(244, 228), (356, 228)], 40, mood, blink)
    # hooked beak
    if talk:
        poly(d, [(268, 300), (332, 300), (316, 360), (284, 360)], (60, 20, 10), 0)
        poly(d, [(276, 318), (324, 318), (300, 372)], (234, 88, 12), 5)
    poly(d, [(256, 262), (344, 262), (338, 300), (300, 340 if not talk else 318), (262, 300)], (249, 115, 22), 6)
    d.arc([262, 250, 338, 300], 200, 340, fill=(254, 215, 170), width=5)
    # head feather tuft
    poly(d, [(290, 118), (300, 60), (318, 116)], G, 6)
    poly(d, [(270, 125), (262, 78), (298, 118)], GD, 6)
    extras(d, mood, (300, 90))


def draw_bablu(d, mood, arms, phase, blink, talk):
    B, BD, BL = (166, 112, 70), (120, 78, 46), (222, 184, 140)
    d.ellipse([160, 752, 470, 790], fill=(0, 0, 0, 80))
    # flat tail behind
    tail = [(380, 640), (560, 600), (590, 680), (420, 740)]
    poly(d, blob(480, 670, 70, 130, -70), (92, 60, 40), 7)
    for k in range(4):
        d.line([(430 + k * 30, 618 + k * 6), (440 + k * 30, 720 + k * 4)], fill=(60, 38, 25), width=3)
    for x in (230, 330):
        E(d, [x - 20, 715, x + 70, 775], BD, 6)
    E(d, [160, 330, 440, 750], B)
    E(d, [215, 430, 385, 730], BL, 5)
    la, ra = wing_angles(arms, mood, phase)
    for sx, a in ((185, -la), (415, ra)):  # stubby arms
        rad = math.radians(a)
        ex, ey = sx + 120 * math.sin(rad), 470 + 120 * math.cos(rad)
        d.line([(sx, 470), (ex, ey)], fill=OUT, width=44)
        d.line([(sx, 470), (ex, ey)], fill=B, width=32)
        E(d, [ex - 26, ey - 26, ex + 26, ey + 26], BD, 6)
    E(d, [160, 150, 220, 210], BD); E(d, [380, 150, 440, 210], BD)
    E(d, [145, 120, 455, 410], B)
    E(d, [225, 255, 375, 360], BL, 5)
    eyes(d, [(242, 220), (358, 220)], 36, mood, blink)
    E(d, [276, 252, 324, 284], (40, 25, 20), 4)
    if talk:
        E(d, [262, 300, 338, 372], (110, 30, 40), 6)
        d.rectangle([280, 300, 320, 330], fill=WHITEC, outline=OUT, width=4)
        d.line([(300, 300), (300, 330)], fill=OUT, width=4)
    else:
        d.arc([255, 270, 345, 320], 30, 150, fill=OUT, width=6)
        d.rectangle([281, 316, 319, 348], fill=WHITEC, outline=OUT, width=4)
        d.line([(300, 316), (300, 348)], fill=OUT, width=4)
    # amber hard hat
    d.chord([175, 70, 425, 270], 180, 360, fill=AMBER, outline=OUT, width=7)
    d.rounded_rectangle([150, 160, 450, 186], 12, fill=AMBER, outline=OUT, width=6)
    d.rectangle([288, 80, 312, 164], fill=(245, 158, 11))
    extras(d, mood, (300, 80))


def draw_gajju(d, mood, arms, phase, blink, talk):
    G, GD, PINK = (156, 163, 186), (120, 128, 150), (244, 172, 196)
    d.ellipse([150, 752, 450, 790], fill=(0, 0, 0, 80))
    flap = math.sin(phase / 8 * 2 * math.pi) * (10 if mood in ('celebrate', 'panic') or arms == 'wave' else 3)
    for x in (195, 265, 335, 395):
        d.rounded_rectangle([x - 6, 640, x + 52, 770], 22, fill=GD, outline=OUT, width=6)
        for k in range(3):
            d.arc([x + 2 + k * 15, 752, x + 16 + k * 15, 768], 180, 360, fill=WHITEC, width=3)
    d.rounded_rectangle([170, 430, 450, 700], 110, fill=G, outline=OUT, width=7)
    # ears
    poly(d, blob(150 - flap, 270, 115, 150, 15), G, 7)
    poly(d, blob(158 - flap, 270, 78, 108, 15), PINK, 0)
    poly(d, blob(450 + flap, 270, 115, 150, -15), G, 7)
    poly(d, blob(442 + flap, 270, 78, 108, -15), PINK, 0)
    E(d, [170, 120, 430, 420], G)
    eyes(d, [(246, 236), (354, 236)], 34, mood, blink)
    # tusks
    poly(d, [(250, 360), (262, 360), (230, 420)], WHITEC, 5)
    poly(d, [(338, 360), (350, 360), (370, 420)], WHITEC, 5)
    # trunk: tapering chain, tip raised when talking / happy
    up = talk or mood == 'celebrate'
    sway = math.sin(phase / 8 * 2 * math.pi) * 12
    pts = []
    for i in range(16):
        u = i / 15
        if up:
            x = 300 + sway * u + 190 * u
            y = 300 + 110 * u - 300 * u ** 2.2
        else:
            x = 300 + sway * u + 25 * math.sin(u * 3)
            y = 290 + 210 * u
        pts.append((x, y, 36 - 20 * u))
    for x, y, r in pts:
        d.ellipse([x - r - 6, y - r - 6, x + r + 6, y + r + 6], fill=OUT)
    for x, y, r in pts:
        d.ellipse([x - r, y - r, x + r, y + r], fill=G)
    for x, y, r in pts[4:14:2]:
        d.arc([x - r * 0.8, y - 4, x + r * 0.8, y + 10], 20, 160, fill=GD, width=3)
    if talk:
        E(d, [256, 372, 296, 410], (120, 30, 40), 5)
    else:
        d.arc([246, 360, 296, 400], 30, 150, fill=OUT, width=5)
    # violet cap: Gajju remembers everything
    d.chord([215, 85, 385, 215], 180, 360, fill=VIOLET, outline=OUT, width=6)
    d.ellipse([288, 70, 312, 94], fill=WHITEC, outline=OUT, width=4)
    extras(d, mood, (300, 100))


def draw_ashtu(d, mood, arms, phase, blink, talk):
    V, VD, VL = (167, 139, 250), (124, 92, 220), (221, 214, 254)
    d.ellipse([110, 752, 490, 790], fill=(0, 0, 0, 80))
    ph = phase / 8 * 2 * math.pi
    wild = mood in ('celebrate', 'panic') or arms in ('up', 'wave')
    for k in range(8):
        base_x = 180 + k * 34
        dirn = (k - 3.5) / 3.5
        pts = []
        for i in range(14):
            u = i / 13
            amp = 22 + (30 if wild else 0)
            x = base_x + dirn * 180 * u + amp * math.sin(ph + k * 0.9 + u * 4) * u
            y = 470 + u * 290 - (u * u * 140 * abs(dirn) if wild else 0)
            pts.append((x, y, 30 - 18 * u))
        for x, y, r in pts:
            d.ellipse([x - r - 6, y - r - 6, x + r + 6, y + r + 6], fill=OUT)
        for x, y, r in pts:
            d.ellipse([x - r, y - r, x + r, y + r], fill=VD if k % 2 else V)
        for x, y, r in pts[3:12:3]:
            d.ellipse([x - r * 0.35, y - r * 0.35, x + r * 0.35, y + r * 0.35], fill=VL)
    E(d, [140, 110, 460, 540], V)
    for (x, y, r) in ((210, 190, 20), (380, 170, 14), (400, 250, 18), (190, 290, 12)):
        d.ellipse([x - r, y - r, x + r, y + r], fill=VD)
    eyes(d, [(240, 330), (360, 330)], 48, mood, blink)
    mouth(d, 300, 425, 70, mood, talk)
    # tiny captain hat (container ships)
    d.rounded_rectangle([230, 96, 370, 132], 14, fill=WHITEC, outline=OUT, width=6)
    d.rounded_rectangle([212, 124, 388, 144], 10, fill=(30, 41, 59), outline=OUT, width=5)
    d.ellipse([288, 102, 312, 126], fill=AMBER)
    extras(d, mood, (300, 110))


def draw_kukdu(d, mood, arms, phase, blink, talk):
    C, CD = (250, 245, 230), (226, 214, 190)
    d.ellipse([170, 752, 430, 790], fill=(0, 0, 0, 80))
    # tail fan
    for k, col in enumerate(((22, 101, 52), AMBER, (234, 88, 12), (22, 101, 52), AMBER)):
        a = -60 + k * 22
        poly(d, blob(420 + 40 * math.cos(math.radians(a)), 470 + 60 * math.sin(math.radians(a)), 40, 140, 200 + a), col, 6)
    feet3(d, 265, 772, (245, 158, 11)); feet3(d, 335, 772, (245, 158, 11))
    la, ra = wing_angles(arms, mood, phase)
    wing(d, (200, 440), 230, 100, -la, CD, tip=AMBER)
    wing(d, (400, 440), 230, 100, ra, CD, tip=AMBER)
    E(d, [180, 340, 420, 705], C)
    # comb
    for (x, y, r) in ((255, 128, 30), (295, 104, 34), (338, 122, 30)):
        E(d, [x - r, y - r, x + r, y + r], RED, 6)
    E(d, [200, 120, 400, 330], C)
    eyes(d, [(260, 210), (340, 210)], 30, mood, blink)
    # wattle
    poly(d, blob(300, 315, 22, 40, 0), RED, 5)
    beak_v(d, 300, 245, 50, 42, talk, (245, 158, 11))
    # amber whistle on a cord (the alert bird)
    d.line([(245, 330), (300, 395), (355, 330)], fill=OUT, width=4)
    d.rounded_rectangle([284, 390, 330, 414], 10, fill=AMBER, outline=OUT, width=4)
    extras(d, mood, (300, 90))


def draw_kaalu(d, mood, arms, phase, blink, talk):
    K, KD, KS = (44, 48, 66), (28, 31, 45), (71, 85, 140)
    if mood == 'normal':
        mood = 'sly'
    d.ellipse([180, 752, 420, 790], fill=(0, 0, 0, 80))
    poly(d, [(320, 620), (380, 620), (440, 760), (360, 740)], KD, 6)
    feet3(d, 265, 772, (71, 85, 105)); feet3(d, 335, 772, (71, 85, 105))
    la, ra = wing_angles(arms, mood, phase)
    wing(d, (200, 430), 260, 105, -la, KD, tip=KS)
    wing(d, (400, 430), 260, 105, ra, KD, tip=KS)
    E(d, [185, 330, 415, 715], K)
    d.arc([215, 380, 330, 520], 200, 280, fill=KS, width=8)
    E(d, [185, 110, 415, 350], K)
    poly(d, [(300, 115), (282, 60), (310, 70), (330, 50), (322, 118)], K, 6)
    # red bandit mask
    d.rounded_rectangle([178, 182, 422, 256], 34, fill=RED, outline=OUT, width=6)
    poly(d, [(410, 200), (470, 180), (460, 230)], RED, 6)
    eyes(d, [(252, 218), (348, 218)], 32, mood, blink, lid=RED)
    # long grey beak
    if talk:
        poly(d, [(262, 268), (338, 268), (300, 312)], (90, 98, 112), 6)
        d.polygon([(272, 300), (328, 300), (300, 330)], fill=(60, 20, 20))
        poly(d, [(276, 318), (324, 318), (300, 350)], (120, 128, 142), 6)
    else:
        poly(d, [(262, 268), (338, 268), (300, 345)], (110, 120, 135), 6)
        d.line([(280, 296), (320, 296)], fill=OUT, width=3)
    extras(d, mood, (300, 90))


def draw_tortoise(d, mood, arms, phase, blink, talk):
    S, SD, SK = (101, 163, 13), (63, 98, 18), (190, 210, 140)
    d.ellipse([90, 752, 520, 790], fill=(0, 0, 0, 80))
    for x in (160, 250, 360, 440):
        d.rounded_rectangle([x - 30, 640, x + 30, 770], 26, fill=SK, outline=OUT, width=6)
    E(d, [400, 470, 560, 620], SK)  # head on the right
    eyes(d, [(470, 525), (520, 525)], 22, mood, blink)
    mouth(d, 500, 580, 40, mood, talk)
    d.chord([90, 380, 470, 740], 180, 360, fill=S, outline=OUT, width=8)
    d.rectangle([96, 556, 464, 600], fill=SD, outline=OUT, width=6)
    for (x, y) in ((190, 490), (280, 445), (370, 490), (280, 520)):
        poly(d, blob(x, y, 40, 34, 0, n=6), SD, 5)


def draw_cheetah(d, mood, arms, phase, blink, talk):
    Y, YD = (251, 191, 36), (217, 119, 6)
    d.ellipse([120, 752, 520, 790], fill=(0, 0, 0, 80))
    run = math.sin(phase / 8 * 2 * math.pi)
    for i, x in enumerate((170, 240, 370, 440)):
        a = (run if i % 2 else -run) * 18
        d.line([(x, 600), (x + a, 765)], fill=OUT, width=34)
        d.line([(x, 600), (x + a, 765)], fill=Y, width=22)
    d.line([(130, 560), (40, 460 + run * 30)], fill=OUT, width=26)
    d.line([(130, 560), (40, 460 + run * 30)], fill=Y, width=16)
    E(d, [120, 470, 480, 660], Y)
    rnd = random.Random(5)
    for _ in range(14):
        x, y = rnd.uniform(160, 440), rnd.uniform(500, 630)
        d.ellipse([x - 9, y - 9, x + 9, y + 9], fill=(60, 40, 20))
    E(d, [380, 330, 560, 500], Y)
    E(d, [395, 320, 435, 360], YD); E(d, [505, 320, 545, 360], YD)
    eyes(d, [(440, 400), (500, 400)], 24, mood, blink)
    d.line([(430, 420), (436, 470)], fill=OUT, width=5); d.line([(510, 420), (504, 470)], fill=OUT, width=5)
    mouth(d, 470, 462, 44, mood, talk)


DRAW = {'ollie': draw_ollie, 'mitthu': draw_mitthu, 'bablu': draw_bablu, 'gajju': draw_gajju,
        'ashtu': draw_ashtu, 'kukdu': draw_kukdu, 'kaalu': draw_kaalu,
        'tortoise': draw_tortoise, 'cheetah': draw_cheetah}


@lru_cache(maxsize=1024)
def sprite(who, mood, arms, phase, blink, talk, height, flip=False):
    im = Image.new('RGBA', (600, 800), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    DRAW[who](d, mood, arms, phase, blink, talk)
    # light sticker rim so dark characters read on the night background
    from PIL import ImageFilter
    a = im.getchannel('A').point(lambda v: 255 if v > 120 else 0)
    rim = a.filter(ImageFilter.MaxFilter(13)).filter(ImageFilter.GaussianBlur(2))
    col = (148, 163, 184) if who == 'kaalu' else (203, 213, 225)
    strength = 0.75 if who == 'kaalu' else 0.35
    base = Image.new('RGBA', im.size, col + (0,))
    base.putalpha(rim.point(lambda v: int(v * strength)))
    im = Image.alpha_composite(base, im)
    w = int(600 * height / 800)
    im = im.resize((w, height), Image.LANCZOS)
    return ImageOps.mirror(im) if flip else im


def draw_animal(img, who, cx, base_y, height, mood='normal', arms='rest', t=0.0, talking=False, flip=False):
    phase = int((t * 10) % 8)
    animated = who in ('ashtu', 'cheetah') or arms in ('wave', 'up') or mood in ('celebrate', 'panic') or who == 'gajju'
    blink = ((t + sum(map(ord, who)) % 7 * 0.53) % 3.9) < 0.13
    talk = 1 if (talking and int(t * 9) % 2 == 0) else 0
    spr = sprite(who, mood, arms, phase if animated else 0, blink, talk, height, flip)
    bob = int(7 * math.sin(t * 2 * math.pi * 0.8 + sum(map(ord, who)) % 5)) if mood != 'panic' else int(5 * math.sin(t * 40))
    img.paste(spr, (int(cx - spr.width / 2), int(base_y - spr.height + bob)), spr)


# ------------------------------------------------------------------ voices
def _env(n, a=0.01, r=0.05):
    t = np.arange(n) / SR
    dur = n / SR
    return np.clip(t / a, 0, 1) * np.clip((dur - t) / r, 0, 1)


def _bp(x, lo, hi):
    from scipy.signal import butter, lfilter
    b, a = butter(2, [lo / (SR / 2), min(hi / (SR / 2), 0.99)], 'band')
    return lfilter(b, a, x)


def _lp(x, cut):
    from scipy.signal import butter, lfilter
    b, a = butter(2, cut / (SR / 2))
    return lfilter(b, a, x)


def _osc(freq, kind='sine'):
    ph = 2 * np.pi * np.cumsum(freq) / SR
    if kind == 'saw':
        return 2 * ((ph / (2 * np.pi)) % 1) - 1
    if kind == 'sq':
        return np.sign(np.sin(ph))
    return np.sin(ph)


def _syll(who, dur, f0, rng):
    n = int(dur * SR)
    t = np.arange(n) / SR
    u = t / dur
    if who == 'ollie':      # soft hoot
        f = f0 * (1.08 - 0.22 * u) * (1 + 0.012 * np.sin(2 * np.pi * 6 * t))
        s = _osc(f) + 0.25 * _osc(2 * f) + 0.04 * rng.standard_normal(n)
        return _lp(s, 2200) * _env(n, 0.03, 0.06) * 0.55
    if who == 'mitthu':     # squawky chirp
        f = f0 * (1 + 0.35 * np.sin(np.pi * u))
        mod = np.sin(2 * np.pi * np.cumsum(f * 0.18) / SR) * 3.0
        s = np.sin(2 * np.pi * np.cumsum(f) / SR + mod) + 0.35 * _bp(rng.standard_normal(n), 1500, 4000)
        return s * _env(n, 0.005, 0.03) * 0.33
    if who == 'bablu':      # chattery squeak
        f = f0 * (1.15 - 0.3 * u)
        s = _osc(f, 'sq') * 0.5 + _osc(f * 1.5)
        s = _bp(s, 500, 3500) * (0.6 + 0.4 * np.sign(np.sin(2 * np.pi * 28 * t)))
        return s * _env(n, 0.006, 0.03) * 0.42
    if who == 'gajju':      # brassy low rumble
        f = f0 * (0.95 + 0.15 * np.sin(np.pi * u))
        s = _osc(f, 'saw') + 0.5 * _osc(f * 1.01, 'saw')
        return _bp(s, 150, 1600) * _env(n, 0.02, 0.05) * 0.75
    if who == 'ashtu':      # bubbly blub
        f = f0 * (0.6 + 1.2 * u)
        s = _osc(f) + 0.2 * _osc(f * 2.02)
        return s * _env(n, 0.004, 0.04) * 0.5
    if who == 'kukdu':      # nasal bright
        f = f0 * (1 + 0.1 * np.sin(np.pi * u)) * (1 + 0.02 * np.sin(2 * np.pi * 22 * t))
        s = _osc(f, 'saw')
        return _bp(s, 700, 3800) * _env(n, 0.008, 0.04) * 0.5
    if who == 'kaalu':      # harsh caw
        f = f0 * (1.1 - 0.3 * u)
        s = _osc(f, 'saw') * (0.7 + 0.3 * np.sin(2 * np.pi * 34 * t)) + 0.6 * rng.standard_normal(n)
        return _bp(s, 700, 2400) * _env(n, 0.006, 0.05) * 0.5
    if who == 'tortoise':
        f = f0 * (1 - 0.1 * u)
        return _lp(_osc(f, 'saw'), 900) * _env(n, 0.04, 0.08) * 0.5
    if who == 'cheetah':
        s = _bp(rng.standard_normal(n), 300, 1400) * (0.5 + 0.5 * np.sin(2 * np.pi * 30 * t))
        return s * _env(n, 0.01, 0.05) * 0.6
    return np.zeros(n)


VOICE = {  # base pitch, syllable length
    'ollie': (340, 0.20), 'mitthu': (1500, 0.11), 'bablu': (900, 0.12), 'gajju': (150, 0.19),
    'ashtu': (380, 0.12), 'kukdu': (620, 0.13), 'kaalu': (520, 0.16), 'tortoise': (120, 0.26),
    'cheetah': (200, 0.12),
}


def syllables_for(text):
    words = len(text.replace('*', '').split())
    return int(max(3, min(14, round(words * 0.8))))


def voice_len(who, nsyl):
    f0, sl = VOICE.get(who, (400, 0.15))
    return nsyl * (sl * 1.05 + 0.05)


def voice(who, nsyl, rng):
    """Animal-gibberish speech: nsyl syllables in the animal's own timbre."""
    f0, sl = VOICE.get(who, (400, 0.15))
    parts = []
    for i in range(nsyl):
        dur = sl * rng.uniform(0.75, 1.3)
        fi = f0 * rng.uniform(0.85, 1.22) * (1.1 if i == nsyl - 1 and rng.random() < 0.5 else 1)
        parts.append(_syll(who, dur, fi, rng))
        parts.append(np.zeros(int(rng.uniform(0.03, 0.08) * SR)))
    return np.concatenate(parts)


def call(who, rng):
    """Signature animal call played when a character first appears."""
    def seq(notes):
        out = []
        for f, dur, gap in notes:
            out.append(_syll(who, dur, f, rng)); out.append(np.zeros(int(gap * SR)))
        return np.concatenate(out)
    if who == 'ollie':
        return seq([(380, 0.32, 0.12), (330, 0.5, 0.0)]) * 1.2
    if who == 'mitthu':
        return seq([(1700, 0.18, 0.05), (2100, 0.14, 0.04), (1500, 0.26, 0)]) * 1.2
    if who == 'bablu':  # tail slap + squeak
        n = int(0.35 * SR); t = np.arange(n) / SR
        thump = np.sin(2 * np.pi * (70 + 60 * np.exp(-t / 0.03)) * t) * np.exp(-t / 0.09)
        slap = _bp(rng.standard_normal(n), 800, 5000) * np.exp(-t / 0.02)
        return np.concatenate([(thump * 0.8 + slap * 0.6), seq([(1100, 0.12, 0.03), (1300, 0.1, 0)])])
    if who == 'gajju':  # trumpet
        n = int(1.1 * SR); t = np.arange(n) / SR; u = t / 1.1
        f = 280 + 360 * np.sin(np.pi * np.clip(u * 1.4, 0, 1)) ** 0.7
        f *= 1 + 0.02 * np.sin(2 * np.pi * 7 * t)
        s = _osc(f, 'saw') + 0.4 * _osc(f * 2, 'saw') + 0.15 * rng.standard_normal(n)
        return _bp(s, 300, 3200) * _env(n, 0.05, 0.25) * 0.55
    if who == 'ashtu':
        return seq([(f, 0.09, g) for f, g in zip(rng.uniform(250, 600, 9), rng.uniform(0.02, 0.1, 9))])
    if who == 'kukdu':  # cock-a-doodle-doo
        return seq([(650, 0.16, 0.03), (900, 0.12, 0.03), (1000, 0.2, 0.03), (820, 0.62, 0)]) * 1.15
    if who == 'kaalu':
        return seq([(560, 0.26, 0.12), (500, 0.3, 0)]) * 1.2
    if who == 'tortoise':
        return seq([(110, 0.5, 0)])
    if who == 'cheetah':
        return seq([(200, 0.15, 0.05), (220, 0.15, 0.05), (180, 0.4, 0)])
    return np.zeros(1)


def crickets(total, rng):
    n = int(total * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for f, rate, ph in ((4600, 0.9, 0.0), (5100, 0.7, 1.3)):
        chirp = (np.sin(2 * np.pi * 34 * t) > 0.2).astype(float)
        gate = (np.sin(2 * np.pi * rate * t + ph) > 0.55).astype(float)
        out += np.sin(2 * np.pi * f * t) * chirp * gate
    return _lp(out, 7000) * 0.006
