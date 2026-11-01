#!/usr/bin/env python3
"""Tech-dev "Linux Zero to Hero" video engine.

usage:
  python3 engine.py episodes/ep01.py out/ep01                # full render
  python3 engine.py episodes/ep01.py out/ep01 --stills 5,40  # preview JPGs only
Outputs: video.mp4, thumbnail.jpg, upload.json, upload.txt, script.txt
"""
import sys, os, math, json, random, subprocess, importlib.util, wave
from functools import lru_cache
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

W, H, FPS = 1920, 1080, 30
SR = 44100
BG = (10, 15, 31)
CYAN = (56, 189, 248); AMBER = (251, 191, 36); VIOLET = (167, 139, 250)
GREEN = (52, 211, 153); RED = (239, 68, 68); WHITE = (241, 245, 249)
MUTED = (148, 163, 184); SOFT = (203, 213, 225); PANEL = (17, 24, 45)
TERM = (12, 16, 32); INK = (15, 23, 42)

GF = '/usr/share/fonts/truetype/google-fonts/'
IF = '/usr/share/fonts/opentype/inter/'
DF = '/usr/share/fonts/truetype/dejavu/'
F_HEAD = GF + 'Poppins-Bold.ttf'
F_HEADM = GF + 'Poppins-Medium.ttf'
F_BODY = IF + 'Inter-Regular.otf'
F_BODYS = IF + 'Inter-SemiBold.otf'
F_BODYB = IF + 'Inter-Bold.otf'
F_MONO = DF + 'DejaVuSansMono.ttf'
F_MONOB = DF + 'DejaVuSansMono-Bold.ttf'


@lru_cache(None)
def font(path, size):
    return ImageFont.truetype(path, size)


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def back(x):  # ease-out-back (overshoot pop)
    x = clamp(x)
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def mix(c1, c2, a):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * a) for i in range(3))


def tw(d, text, f):
    b = d.textbbox((0, 0), text, font=f)
    return b[2] - b[0]


def wrap(d, text, f, maxw):
    words, lines, cur = text.split(), [], ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if tw(d, t.replace('*', ''), f) <= maxw:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def rich(d, xy, text, f, base, hi=AMBER):
    """Draw text where *words* are highlighted."""
    x, y = xy
    parts = text.split('*')
    for i, p in enumerate(parts):
        if not p:
            continue
        d.text((x, y), p, font=f, fill=hi if i % 2 else base)
        x += tw(d, p, f)
    return x


def cap_words(text):
    return len(text.replace('*', '').split())


def read_time(text):
    return max(3.4, 0.47 * cap_words(text) + 2.1)


# ---------------------------------------------------------------- background
_STATIC = None


def static_bg():
    global _STATIC
    if _STATIC is None:
        img = Image.new('RGB', (W, H), BG)
        d = ImageDraw.Draw(img)
        for x in range(0, W, 64):
            d.line([(x, 0), (x, H)], fill=(18, 25, 46))
        for y in range(0, H, 64):
            d.line([(0, y), (W, y)], fill=(18, 25, 46))
        # vignette darkening via a radial mask
        yy, xx = np.mgrid[0:H // 4, 0:W // 4]
        r = np.sqrt(((xx - W / 8) / (W / 8)) ** 2 + ((yy - H / 8) / (H / 8)) ** 2)
        v = np.clip(1.05 - 0.35 * r ** 2, 0.55, 1.0)
        vm = Image.fromarray((v * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)
        img = Image.composite(img, Image.new('RGB', (W, H), (4, 6, 14)), vm)
        _STATIC = img
    return _STATIC


_GY, _GX = np.mgrid[0:108, 0:192] / np.array([108.0, 192.0])[:, None, None]


def glow(t):
    blobs = [
        (CYAN, 0.18 + 0.06 * math.sin(t * 0.21), 0.25 + 0.08 * math.cos(t * 0.17), 0.30, 0.20),
        (VIOLET, 0.82 + 0.05 * math.cos(t * 0.19), 0.72 + 0.07 * math.sin(t * 0.23), 0.34, 0.22),
        (AMBER, 0.55 + 0.10 * math.sin(t * 0.11), 0.95, 0.22, 0.07),
    ]
    acc = np.zeros((108, 192, 3))
    for col, cx, cy, r, s in blobs:
        g = np.exp(-(((_GX - cx) * 1.78) ** 2 + (_GY - cy) ** 2) / (2 * r * r)) * s
        acc += g[..., None] * np.array(col)
    return Image.fromarray(np.clip(acc, 0, 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)


def background(t):
    return ImageChops.add(static_bg(), glow(t))


# ---------------------------------------------------------------- mascot "Bashi"
BODY = (226, 232, 240); EDGE = (100, 116, 139); DARK = (30, 41, 59)


def _limb(d, a, b, wdt, col):
    d.line([a, b], fill=col, width=wdt)
    r = wdt // 2
    for p in (a, b):
        d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=col)


def _arm(d, sh, ang, length=150, hand=30):
    ex = sh[0] + length * math.cos(math.radians(ang))
    ey = sh[1] - length * math.sin(math.radians(ang))
    _limb(d, sh, (ex, ey), 30, EDGE)
    _limb(d, sh, (ex, ey), 20, BODY)
    d.ellipse([ex - hand, ey - hand, ex + hand, ey + hand], fill=BODY, outline=EDGE, width=6)


def _face(d, mood, blink):
    g = GREEN
    lx, rx, ey = 235, 365, 270
    if blink and mood not in ('happy', 'celebrate'):
        d.rounded_rectangle([lx - 28, ey - 4, lx + 28, ey + 6], 5, fill=g)
        d.rounded_rectangle([rx - 28, ey - 4, rx + 28, ey + 6], 5, fill=g)
    elif mood in ('happy', 'celebrate'):
        for x in (lx, rx):
            d.arc([x - 32, ey - 24, x + 32, ey + 30], 200, 340, fill=g, width=12)
    elif mood == 'panic':
        for x in (lx, rx):
            d.ellipse([x - 34, ey - 34, x + 34, ey + 34], outline=g, width=10)
            d.ellipse([x - 9, ey - 9, x + 9, ey + 9], fill=g)
    elif mood == 'curious':
        d.rounded_rectangle([lx - 18, ey - 34, lx + 18, ey + 30], 16, fill=g)
        d.rounded_rectangle([rx - 16, ey - 14, rx + 16, ey + 20], 14, fill=g)
        d.line([(rx - 30, ey - 46), (rx + 26, ey - 58)], fill=g, width=9)
    elif mood == 'think':
        d.rounded_rectangle([lx - 6, ey - 34, lx + 30, ey + 20], 16, fill=g)
        d.rounded_rectangle([rx - 6, ey - 34, rx + 30, ey + 20], 16, fill=g)
    else:
        d.rounded_rectangle([lx - 18, ey - 30, lx + 18, ey + 30], 16, fill=g)
        d.rounded_rectangle([rx - 18, ey - 30, rx + 18, ey + 30], 16, fill=g)
    my = 345
    if mood in ('happy', 'normal'):
        d.arc([255, my - 40, 345, my + 14], 20, 160, fill=g, width=10)
    elif mood == 'celebrate':
        d.chord([250, my - 36, 350, my + 30], 0, 180, fill=g)
    elif mood == 'panic':
        pts = [(250 + i * 20, my + (8 if i % 2 else -8)) for i in range(6)]
        d.line(pts, fill=g, width=8)
    elif mood == 'curious':
        d.ellipse([285, my - 16, 315, my + 14], outline=g, width=8)
    elif mood == 'think':
        d.line([(265, my), (335, my - 6)], fill=g, width=9)


@lru_cache(maxsize=256)
def bashi_sprite(mood, arms, phase, blink, height):
    S = 600, 800
    im = Image.new('RGBA', S, (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([150, 745, 450, 790], fill=(0, 0, 0, 90))  # shadow
    # legs
    for x in (225, 335):
        d.rounded_rectangle([x, 640, x + 45, 735], 20, fill=EDGE)
        d.ellipse([x - 22, 712, x + 68, 760], fill=DARK)
    # arms behind/in front
    wave = math.sin(phase / 8 * 2 * math.pi)
    L, R = (178, 500), (422, 500)
    if arms == 'wave':
        la, ra = 245, 60 + 28 * wave
    elif arms == 'point':
        la, ra = 245, 8
    elif arms == 'up':
        la, ra = 120 - 8 * wave, 60 + 8 * wave
    elif arms == 'head':
        la, ra = 150, 30
    elif arms == 'think':
        la, ra = 245, 115
    else:
        la, ra = 250, 290
    # body
    d.rounded_rectangle([170, 450, 430, 655], 55, fill=BODY, outline=EDGE, width=8)
    d.rounded_rectangle([215, 492, 385, 600], 26, fill=TERM)
    d.text((300, 546), '>_', font=font(F_MONOB, 64), fill=GREEN, anchor='mm')
    for i, c in enumerate((CYAN, AMBER, VIOLET)):
        d.rounded_rectangle([228 + i * 50, 612, 270 + i * 50, 624], 6, fill=c)
    if arms == 'head':
        _arm(d, L, la, 175); _arm(d, R, ra, 175)
    else:
        _arm(d, L, la); _arm(d, R, ra)
    # neck + head
    d.rectangle([272, 425, 328, 460], fill=EDGE)
    d.line([(300, 150), (300, 80)], fill=EDGE, width=10)
    d.ellipse([276, 44, 324, 92], fill=AMBER, outline=(180, 120, 10), width=4)
    d.rounded_rectangle([88, 230, 120, 330], 14, fill=CYAN)
    d.rounded_rectangle([480, 230, 512, 330], 14, fill=CYAN)
    d.rounded_rectangle([110, 145, 490, 435], 78, fill=BODY, outline=EDGE, width=8)
    d.rounded_rectangle([148, 185, 452, 400], 46, fill=TERM)
    d.rounded_rectangle([162, 197, 260, 214], 8, fill=(40, 52, 80))
    _face(d, mood, blink)
    if mood == 'panic':
        d.polygon([(520, 150), (540, 200), (500, 200)], fill=CYAN)
        d.ellipse([500, 182, 540, 222], fill=CYAN)
    if mood == 'think':
        for i, r in enumerate((10, 15, 21)):
            cx, cy = 500 + i * 34, 120 - i * 30
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=SOFT)
    if mood == 'curious':
        d.text((520, 120), '?', font=font(F_HEAD, 110), fill=AMBER, anchor='mm')
    w = int(S[0] * height / S[1])
    return im.resize((w, height), Image.LANCZOS)


def draw_bashi(img, cx, base_y, height, mood='normal', arms='rest', t=0.0):
    phase = int((t * 8 * 1.6) % 8)
    blink = (t % 3.7) < 0.13
    spr = bashi_sprite(mood, arms, phase if arms in ('wave', 'up') else 0, blink, height)
    bob = int(8 * math.sin(t * 2 * math.pi * 0.8)) if mood != 'panic' else int(5 * math.sin(t * 40))
    img.paste(spr, (int(cx - spr.width / 2), int(base_y - spr.height + bob)), spr)


# ---------------------------------------------------------------- props
def prop_server(d, x, y, t, fire=False, s=1.0):
    w, h = int(230 * s), int(330 * s)
    d.rounded_rectangle([x, y, x + w, y + h], int(18 * s), fill=(30, 41, 59), outline=(71, 85, 105), width=4)
    for i in range(4):
        uy = y + int(22 * s) + i * int(76 * s)
        d.rounded_rectangle([x + 16, uy, x + w - 16, uy + int(58 * s)], 8, fill=(15, 23, 42))
        for j in range(3):
            on = (int(t * 6 + i * 3 + j * 5) % 4) != 0
            c = (RED if fire and j == 0 else GREEN) if on else (40, 52, 70)
            d.ellipse([x + 32 + j * 26, uy + 20, x + 48 + j * 26, uy + 36], fill=c)
        d.rectangle([x + w - 100, uy + 24, x + w - 32, uy + 32], fill=(51, 65, 85))
    if fire:
        for k in range(5):
            fx = x + 25 + k * (w - 50) / 4
            fh = 70 + 30 * math.sin(t * 9 + k * 1.7)
            pts = [(fx - 28, y + 6), (fx, y - fh), (fx + 28, y + 6)]
            d.polygon(pts, fill=(249, 115, 22))
            pts2 = [(fx - 14, y + 6), (fx, y - fh * 0.55), (fx + 14, y + 6)]
            d.polygon(pts2, fill=AMBER)


def prop_clock(d, cx, cy, r, t, label='2:00 AM'):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(30, 41, 59), outline=AMBER, width=8)
    for k in range(12):
        a = k / 12 * 2 * math.pi
        d.line([(cx + (r - 18) * math.sin(a), cy - (r - 18) * math.cos(a)),
                (cx + (r - 8) * math.sin(a), cy - (r - 8) * math.cos(a))], fill=SOFT, width=4)
    d.line([(cx, cy), (cx + r * 0.45 * math.sin(math.pi / 3), cy - r * 0.45 * math.cos(math.pi / 3))], fill=WHITE, width=10)
    a = t * 2
    d.line([(cx, cy), (cx + r * 0.75 * math.sin(a), cy - r * 0.75 * math.cos(a))], fill=AMBER, width=5)
    d.text((cx, cy + r + 40), label, font=font(F_HEAD, 40), fill=AMBER, anchor='mm')


def prop_laptop(d, cx, cy, t):
    d.rounded_rectangle([cx - 190, cy - 150, cx + 190, cy + 90], 16, fill=(30, 41, 59), outline=(71, 85, 105), width=5)
    d.rounded_rectangle([cx - 170, cy - 132, cx + 170, cy + 72], 8, fill=TERM)
    d.text((cx - 150, cy - 110), '$', font=font(F_MONOB, 40), fill=GREEN)
    if int(t * 2) % 2 == 0:
        d.rectangle([cx - 120, cy - 106, cx - 98, cy - 66], fill=WHITE)
    d.polygon([(cx - 240, cy + 90), (cx + 240, cy + 90), (cx + 270, cy + 125), (cx - 270, cy + 125)], fill=(71, 85, 105))


def prop_cloud(d, cx, cy, label):
    for ox, oy, r in ((-90, 20, 70), (0, -20, 95), (95, 15, 75), (-40, 45, 70), (50, 50, 70)):
        d.ellipse([cx + ox - r, cy + oy - r, cx + ox + r, cy + oy + r], fill=(30, 41, 59), outline=CYAN, width=4)
    for ox, oy, r in ((-90, 20, 66), (0, -20, 91), (95, 15, 71), (-40, 45, 66), (50, 50, 66)):
        d.ellipse([cx + ox - r, cy + oy - r, cx + ox + r, cy + oy + r], fill=(30, 41, 59))
    d.text((cx, cy + 20), label, font=font(F_HEAD, 40), fill=CYAN, anchor='mm')


def prop_alert(d, cx, cy, t):
    s = 1 + 0.08 * math.sin(t * 8)
    r = 90 * s
    d.polygon([(cx, cy - r), (cx + r * 1.1, cy + r * 0.8), (cx - r * 1.1, cy + r * 0.8)], fill=RED)
    d.text((cx, cy + 10), '!', font=font(F_HEAD, int(110 * s)), fill=WHITE, anchor='mm')


def prop_sparkles(d, t, box, n=18, seed=3):
    rnd = random.Random(seed)
    x0, y0, x1, y1 = box
    for i in range(n):
        x = rnd.uniform(x0, x1); y = rnd.uniform(y0, y1)
        ph = rnd.uniform(0, 6.28); c = rnd.choice([CYAN, AMBER, VIOLET, GREEN])
        s = 6 + 12 * (0.5 + 0.5 * math.sin(t * 4 + ph))
        d.polygon([(x, y - s), (x + s * 0.3, y - s * 0.3), (x + s, y), (x + s * 0.3, y + s * 0.3),
                   (x, y + s), (x - s * 0.3, y + s * 0.3), (x - s, y), (x - s * 0.3, y - s * 0.3)], fill=c)


def draw_props(img, d, props, t):
    for p in props:
        k = p[0]
        if k == 'server':
            prop_server(d, p[1], p[2], t, fire=False)
        elif k == 'server_fire':
            prop_server(d, p[1], p[2], t, fire=True)
        elif k == 'clock':
            prop_clock(d, p[1], p[2], 90, t, p[3] if len(p) > 3 else '2:00 AM')
        elif k == 'laptop':
            prop_laptop(d, p[1], p[2], t)
        elif k == 'cloud':
            prop_cloud(d, p[1], p[2], p[3])
        elif k == 'alert':
            prop_alert(d, p[1], p[2], t)
        elif k == 'sparkles':
            prop_sparkles(d, t, p[1])


# ---------------------------------------------------------------- shared UI
@lru_cache(maxsize=512)
def caption_img(text):
    f = font(F_BODYS, 44)
    tmp = ImageDraw.Draw(Image.new('RGB', (10, 10)))
    lines = wrap(tmp, text, f, 1480)
    lh = 60
    h = 36 + lh * len(lines)
    w = max(tw(tmp, l.replace('*', ''), f) for l in lines) + 80
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], 22, fill=(8, 12, 26, 225), outline=(56, 72, 110, 255), width=2)
    for i, l in enumerate(lines):
        lw = tw(d, l.replace('*', ''), f)
        rich(d, ((w - lw) // 2, 14 + i * lh), l, f, WHITE)
    return im


def draw_caption(img, text, age):
    if not text:
        return
    im = caption_img(text)
    a = ease(age / 0.25)
    y = H - 34 - im.height + int((1 - a) * 18)
    if a < 1:
        im = im.copy()
        im.putalpha(im.getchannel('A').point(lambda v: int(v * a)))
    img.paste(im, ((W - im.width) // 2, y), im)


_HEADER = {}


def header_img(ep):
    key = ep['number']
    if key not in _HEADER:
        im = Image.new('RGBA', (W, 90), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle([40, 26, 96, 70], 10, fill=TERM, outline=GREEN, width=2)
        d.text((68, 48), '>_', font=font(F_MONOB, 24), fill=GREEN, anchor='mm')
        d.text((112, 30), 'Tech-dev', font=font(F_HEAD, 30), fill=WHITE)
        x = 112 + tw(d, 'Tech-dev', font(F_HEAD, 30)) + 20
        d.text((x, 36), 'Linux Zero to Hero', font=font(F_BODYS, 24), fill=MUTED)
        label = f"EP {ep['number']}"
        f = font(F_HEAD, 24)
        lw = tw(d, label, f)
        d.rounded_rectangle([W - 70 - lw, 28, W - 40, 68], 20, fill=AMBER)
        d.text((W - 55 - lw, 32), label, font=f, fill=INK)
        _HEADER[key] = im
    return _HEADER[key]


def draw_chrome(img, ep, gt, total):
    h = header_img(ep)
    img.paste(h, (0, 0), h)
    d = ImageDraw.Draw(img)
    pw = int(W * clamp(gt / total))
    d.rectangle([0, H - 8, W, H], fill=(20, 28, 50))
    seg = [CYAN, AMBER, VIOLET]
    for i, c in enumerate(seg):
        x0, x1 = i * W // 3, (i + 1) * W // 3
        if pw > x0:
            d.rectangle([x0, H - 8, min(pw, x1), H], fill=c)


def panel(d, box, fill=PANEL, outline=(44, 58, 92), r=26, width=2):
    d.rounded_rectangle(box, r, fill=fill, outline=outline, width=width)


def bubble(img, text, anchor_xy, tail_to, t_age, maxw=760):
    if not text:
        return
    f = font(F_HEAD, 46)
    tmp = ImageDraw.Draw(img)
    lines = wrap(tmp, text, f, maxw)
    lh = 64
    w = max(tw(tmp, l.replace('*', ''), f) for l in lines) + 90
    h = lh * len(lines) + 60
    s = back(t_age / 0.35)
    if s <= 0.02:
        return
    bx, by = anchor_xy
    layer = Image.new('RGBA', (w + 120, h + 120), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle([10, 10, w + 10, h + 10], 40, fill=(255, 255, 255, 255), outline=(203, 213, 225, 255), width=4)
    for i, l in enumerate(lines):
        rich(d, (55, 36 + i * lh), l, f, INK, hi=(217, 119, 6))
    sw, sh = max(1, int(layer.width * s)), max(1, int(layer.height * s))
    layer = layer.resize((sw, sh), Image.BILINEAR)
    img.paste(layer, (int(bx - 10 * s), int(by - 10 * s)), layer)
    if s > 0.9:
        dd = ImageDraw.Draw(img)
        tx, ty = tail_to
        ax = bx + 70 if tx < bx + w / 2 else bx + w - 70
        ay = by + h - 2
        dd.polygon([(ax - 26, ay), (ax + 26, ay), (tx, ty)], fill=(255, 255, 255))


# ---------------------------------------------------------------- scenes
class Scene:
    def __init__(self, spec, ep):
        self.spec, self.ep = spec, ep
        self.kind = spec['type']
        self.steps = []   # list of dict with start, dur, cap, + fields
        self.events = []  # (t_local, sound)
        self.build()
        self.dur = sum(s['dur'] for s in self.steps) + spec.get('pad', 0.6)

    def add(self, dur, **kw):
        start = self.steps[-1]['start'] + self.steps[-1]['dur'] if self.steps else 0.4
        kw.update(start=start, dur=dur)
        self.steps.append(kw)
        return kw

    def step_at(self, t):
        cur = self.steps[0]
        for s in self.steps:
            if t >= s['start']:
                cur = s
        return cur

    # ---- timing
    def build(self):
        sp = self.spec
        self.events.append((0.0, 'whoosh'))
        if self.kind == 'terminal':
            cwd = sp.get('cwd', '~')
            for st in sp['steps']:
                st = dict(st)
                st['cwd'] = st.get('cwd', cwd)          # directory shown in the prompt when typed
                cwd = st['cwd_after'] = st.get('to', st['cwd'])  # after a cd, the next prompt changes
                cmd = st.get('cmd')
                out = st.get('out', [])
                typing = (0.5 + len(cmd) / 15.0 + 0.4 + 0.07 * len(out)) if cmd else 0.4
                dur = max(read_time(st['cap']), typing + 3.0)
                s = self.add(dur, **st)
                if cmd:
                    for i in range(len(cmd)):
                        self.events.append((s['start'] + 0.5 + i / 15.0, 'click'))
                    t_out = s['start'] + 0.5 + len(cmd) / 15.0 + 0.4
                    self.events.append((t_out - 0.4, 'enter'))
                    if st.get('error'):
                        self.events.append((t_out, 'buzz'))
                    s['t_out'] = t_out - s['start']
                else:
                    s['t_out'] = 0
                    self.events.append((s['start'], 'pop'))
        elif self.kind == 'quiz':
            q = self.add(max(read_time(sp['caps'][0]), 7.5), cap=sp['caps'][0], reveal=False)
            for k in range(5):
                self.events.append((q['start'] + 1.5 + k, 'tick'))
            r = self.add(max(read_time(sp['caps'][1]), 5.0), cap=sp['caps'][1], reveal=True)
            self.events.append((r['start'], 'ding'))
        elif self.kind == 'outro':
            caps = sp['caps']
            total = sum(read_time(c) for c in caps)
            extra = max(0, 20 - total) / len(caps)
            for c in caps:
                self.add(read_time(c) + extra, cap=c)
            self.events.append((1.2, 'sparkle'))
        else:
            for i, st in enumerate(sp['steps']):
                st = dict(st) if isinstance(st, dict) else {'cap': st}
                s = self.add(read_time(st['cap']) + st.get('extra', 0), **st)
                if i > 0 or self.kind in ('cartoon',):
                    self.events.append((s['start'] + 0.05, 'pop' if self.kind != 'recap' else 'chime'))

    # ---- drawing
    def draw(self, img, t):
        d = ImageDraw.Draw(img)
        getattr(self, 'draw_' + self.kind)(img, d, t)
        st = self.step_at(t)
        draw_caption(img, st.get('cap'), t - st['start'])

    def draw_title(self, img, d, t):
        sp = self.spec
        a = ease((t - 0.2) / 0.8)
        x = 150 - int((1 - a) * 80)
        d.text((x, 250), 'LINUX ZERO TO HERO', font=font(F_HEAD, 40), fill=GREEN)
        f = font(F_HEAD, 104)
        lines = wrap(d, sp['title'], f, 1050)
        for i, l in enumerate(lines):
            aa = ease((t - 0.4 - i * 0.15) / 0.7)
            if aa > 0:
                rich(d, (150 - int((1 - aa) * 60), 310 + i * 124), l, f, WHITE, hi=CYAN)
        y = 330 + len(lines) * 124
        b = ease((t - 1.0) / 0.6)
        if b > 0:
            pill = f"Episode {self.ep['number']}  ·  {sp.get('sub', '')}"
            fp = font(F_BODYS, 36)
            pw = tw(d, pill, fp)
            d.rounded_rectangle([150, y, 150 + pw + 60, y + 70], 35, fill=(30, 41, 70), outline=AMBER, width=3)
            d.text((180, y + 14), pill, font=fp, fill=AMBER)
        for i, c in enumerate((CYAN, AMBER, VIOLET)):
            ww = int(160 * ease((t - 0.6 - i * 0.1) / 0.5))
            d.rounded_rectangle([150 + i * 176, 220, 150 + i * 176 + max(ww, 1), 230], 5, fill=c)
        bx = 1500
        s_in = ease(t / 0.9)
        draw_props(img, d, [('sparkles', (1150, 120, 1860, 300))], t)
        draw_bashi(img, bx + int((1 - s_in) * 500), 860, 600, 'happy', 'wave', t)

    def draw_cartoon(self, img, d, t):
        st = self.step_at(t)
        props = st.get('props', self.spec.get('props', []))
        draw_props(img, d, props, t)
        side = self.spec.get('side', 'left')
        bx = 520 if side == 'left' else 1400
        a = ease(t / 0.7)
        draw_bashi(img, bx + int((1 - a) * (-600 if side == 'left' else 600)), 880, 560,
                   st.get('mood', 'normal'), st.get('arms', 'rest'), t)
        if st.get('say'):
            bxy = (bx + 210, 170) if side == 'left' else (bx - 1050, 170)
            tail = (bx + 120, 420) if side == 'left' else (bx - 120, 420)
            bubble(img, st['say'], bxy, tail, t - st['start'])

    def draw_stack(self, img, d, t):
        sp = self.spec
        items = sp['items']  # reveal order, drawn bottom-up
        st = self.step_at(t)
        n_show = st.get('show', self.steps.index(st) + 1)
        d.text((150, 150), sp.get('heading', ''), font=font(F_HEAD, 56), fill=WHITE)
        x0, x1, bh, gap = 150, 1120, 128, 18
        base = 830
        cols = [VIOLET, CYAN, GREEN, AMBER, (244, 114, 182)]
        for i, it in enumerate(items[:n_show]):
            si = [s for s in self.steps if s.get('show', self.steps.index(s) + 1) > i][0]
            age = t - si['start']
            a = back(age / 0.45)
            y1 = base - i * (bh + gap)
            y0 = y1 - bh
            off = int((1 - clamp(a)) * 90)
            c = cols[i % len(cols)]
            panel(d, [x0 + off, y0, x1 + off, y1], fill=mix(PANEL, c, 0.10), outline=c, width=3)
            d.text((x0 + 40 + off, y0 + 26), it[0], font=font(F_HEAD, 44), fill=c)
            d.text((x0 + 40 + off, y0 + 82), it[1], font=font(F_BODY, 30), fill=SOFT)
            if len(it) > 2:
                d.text((x1 - 40 + off, y0 + bh // 2), it[2], font=font(F_MONOB, 34), fill=WHITE, anchor='rm')
        draw_bashi(img, 1520, 850, 500, st.get('mood', 'think' if n_show < len(items) else 'happy'),
                   st.get('arms', 'think' if n_show < len(items) else 'point'), t)

    def draw_cards(self, img, d, t):
        sp = self.spec
        st = self.step_at(t)
        d.text((150, 150), sp.get('heading', ''), font=font(F_HEAD, 56), fill=WHITE)
        cards = sp['cards']
        n = len(cards)
        cw, gap = (1620 - (n - 1) * 30) // n, 30
        cols = [CYAN, AMBER, VIOLET, GREEN, (244, 114, 182)]
        for i, c in enumerate(cards):
            a = back((t - 0.3 - i * 0.18) / 0.5)
            if a <= 0:
                continue
            x = 150 + i * (cw + gap)
            y = 300 + int((1 - clamp(a)) * 80)
            col = cols[i % len(cols)]
            panel(d, [x, y, x + cw, y + 380], outline=col, width=3)
            d.rounded_rectangle([x + 30, y + 30, x + 120, y + 120], 22, fill=mix(PANEL, col, 0.25))
            d.text((x + 75, y + 75), c.get('icon', '>_'), font=font(F_MONOB, 40), fill=col, anchor='mm')
            d.text((x + 30, y + 150), c['title'], font=font(F_HEAD, 42), fill=WHITE)
            fl = font(F_BODY, 30)
            for j, l in enumerate(wrap(d, c.get('text', ''), fl, cw - 60)):
                d.text((x + 30, y + 220 + j * 42), l, font=fl, fill=SOFT)
        hl = st.get('banner')
        if hl:
            a = ease((t - st['start']) / 0.4)
            f = font(F_HEAD, 46)
            bw = tw(d, hl.replace('*', ''), f) + 80
            x = (W - bw) // 2
            d.rounded_rectangle([x, 735 + int((1 - a) * 30), x + bw, 815 + int((1 - a) * 30)], 40, fill=(30, 41, 70), outline=GREEN, width=3)
            rich(d, (x + 40, 747 + int((1 - a) * 30)), hl, f, WHITE, hi=GREEN)

    def draw_chain(self, img, d, t):
        sp = self.spec
        st = self.step_at(t)
        d.text((150, 150), sp.get('heading', ''), font=font(F_HEAD, 56), fill=WHITE)
        nodes = sp['nodes']
        hi = sp.get('highlight', 0)
        per = 5
        nw, nh, gx, gy = 280, 120, 55, 120
        for i, n in enumerate(nodes):
            r, c = divmod(i, per)
            if r % 2 == 1:
                c = per - 1 - c
            x = 150 + c * (nw + gx)
            y = 290 + r * (nh + gy)
            a = back((t - 0.3 - i * 0.12) / 0.4)
            if a <= 0:
                continue
            on = i == hi
            col = AMBER if on else CYAN
            pulse = (6 * (0.5 + 0.5 * math.sin(t * 5))) if on else 0
            panel(d, [x - pulse, y - pulse, x + nw + pulse, y + nh + pulse],
                  fill=mix(PANEL, col, 0.22 if on else 0.06), outline=col, width=4 if on else 2)
            d.text((x + 22, y + 18), f'{i + 1}', font=font(F_HEAD, 30), fill=col)
            fl = font(F_BODYS, 30)
            ls = wrap(d, n, fl, nw - 70)
            for j, l in enumerate(ls[:2]):
                d.text((x + 62, y + 22 + j * 38), l, font=fl, fill=WHITE)
            if i < len(nodes) - 1:
                nr, nc = divmod(i + 1, per)
                if nr == r:
                    if r % 2 == 0:
                        ax0, ax1 = x + nw + 8, x + nw + gx - 8
                    else:
                        ax0, ax1 = x - 8, x - gx + 8
                    ay = y + nh // 2
                    d.line([(ax0, ay), (ax1, ay)], fill=MUTED, width=4)
                    dirn = 1 if ax1 > ax0 else -1
                    d.polygon([(ax1, ay), (ax1 - 14 * dirn, ay - 10), (ax1 - 14 * dirn, ay + 10)], fill=MUTED)
                else:
                    ax = x + nw // 2
                    d.line([(ax, y + nh + 8), (ax, y + nh + gy - 10)], fill=MUTED, width=4)
                    d.polygon([(ax, y + nh + gy - 8), (ax - 10, y + nh + gy - 22), (ax + 10, y + nh + gy - 22)], fill=MUTED)
        if sp.get('you_are_here', True):
            r, c = divmod(hi, per)
            x = 150 + c * (nw + gx) + nw // 2
            y = 290 + r * (nh + gy)
            yy = y - 50 + int(8 * math.sin(t * 4))
            d.text((x, yy), 'YOU ARE HERE', font=font(F_HEAD, 28), fill=AMBER, anchor='mm')
            d.polygon([(x - 12, yy + 22), (x + 12, yy + 22), (x, yy + 40)], fill=AMBER)

    def _term_lines(self, upto_t, prompt):
        """Return list of (segments) lines for terminal at time t."""
        lines = []
        cur_cursor = None
        for s in self.steps:
            if s['start'] > upto_t:
                break
            lt = upto_t - s['start']
            cmd = s.get('cmd')
            if cmd:
                n = int(clamp((lt - 0.5) * 15.0, 0, len(cmd)))
                lines.append({'prompt': True, 'text': cmd[:n], 'step': s, 'cwd': s.get('cwd', '~')})
                if n < len(cmd) or lt < s['t_out']:
                    cur_cursor = len(lines) - 1
                if lt >= s['t_out']:
                    k = int((lt - s['t_out']) / 0.07) + 1
                    for o in s.get('out', [])[:k]:
                        lines.append({'prompt': False, 'text': o, 'step': s, 'err': s.get('error')})
                    if s is self.steps[-1] or (s is self.step_at(upto_t) and k >= len(s.get('out', []))):
                        pass
        return lines, cur_cursor

    def draw_terminal(self, img, d, t):
        sp = self.spec
        st = self.step_at(t)
        user, host = sp.get('user', 'shivam'), sp.get('host', 'tech-dev')
        side = sp.get('side', 'card')
        tx0, ty0 = 110, 140
        tx1 = 1230 if side else 1810
        ty1 = 830
        # shake on error
        shake = 0
        if st.get('error'):
            lt = t - st['start'] - st['t_out']
            if 0 <= lt < 0.5:
                shake = int(14 * math.sin(lt * 60) * (1 - lt / 0.5))
        tx0 += shake; tx1 += shake
        a = ease(t / 0.5)
        oy = int((1 - a) * 60)
        ty0 += oy; ty1 += oy
        border = (44, 58, 92)
        if st.get('error') and t - st['start'] >= st['t_out']:
            border = RED
        d.rounded_rectangle([tx0 + 10, ty0 + 14, tx1 + 10, ty1 + 14], 22, fill=(4, 6, 14))
        d.rounded_rectangle([tx0, ty0, tx1, ty1], 22, fill=TERM, outline=border, width=3)
        d.rounded_rectangle([tx0, ty0, tx1, ty0 + 58], 22, fill=(30, 38, 62))
        d.rectangle([tx0, ty0 + 36, tx1, ty0 + 58], fill=(30, 38, 62))
        for i, c in enumerate(((239, 68, 68), (245, 158, 11), (34, 197, 94))):
            d.ellipse([tx0 + 24 + i * 34, ty0 + 18, tx0 + 46 + i * 34, ty0 + 40], fill=c)
        _cw = st.get('cwd_after', '~') if t - st['start'] >= st.get('t_out', 0) else st.get('cwd', '~')
        d.text(((tx0 + tx1) // 2, ty0 + 29), f'{user}@{host}: {_cw}', font=font(F_BODYS, 24), fill=MUTED, anchor='mm')
        fm, fmb = font(F_MONO, 32), font(F_MONOB, 32)
        cw = tw(d, 'M' * 10, fm) / 10
        maxc = int((tx1 - tx0 - 60) / cw)
        lh = 46
        cap_lines = int((ty1 - ty0 - 90) / lh)
        raw, cursor = self._term_lines(t, None)
        # expand prompt + wrap
        rows = []
        cur_cwd = st.get('cwd_after', '~') if t - st['start'] >= st.get('t_out', 0) else st.get('cwd', '~')
        p = f'{user}@{host}:{cur_cwd}$ '
        for li, L in enumerate(raw):
            if L['prompt']:
                full = f"{user}@{host}:{L.get('cwd', '~')}$ " + L['text']
                chunks = [full[i:i + maxc] for i in range(0, max(1, len(full)), maxc)] or ['']
                for ci, ch in enumerate(chunks):
                    rows.append({'kind': 'prompt' if ci == 0 else 'cont', 'text': ch, 'L': L,
                             'cursor': li == cursor and ci == len(chunks) - 1,
                             'pp': f"{user}@{host}:{L.get('cwd', '~')}$ "})
            else:
                txt = L['text']
                chunks = [txt[i:i + maxc] for i in range(0, max(1, len(txt)), maxc)] or ['']
                for ch in chunks:
                    rows.append({'kind': 'out', 'text': ch, 'L': L})
        idle_prompt = cursor is None
        if idle_prompt:
            rows.append({'kind': 'prompt', 'text': p, 'L': None, 'cursor': True, 'pp': p})
        rows = rows[-cap_lines:]
        y = ty0 + 80
        hl = st.get('hl', [])
        if isinstance(hl, str):
            hl = [hl]
        for r in rows:
            x = tx0 + 30
            if r['kind'] == 'prompt':
                txt = r['text']
                pp = r.get('pp', p)
                if txt.startswith(pp) or r['L'] is None:
                    segs = [(f'{user}@{host}', GREEN, fmb), (':', WHITE, fm), (pp[len(user) + len(host) + 2:-2], CYAN, fmb),
                            ('$ ', WHITE, fm), (txt[len(pp):], WHITE, fmb)]
                else:
                    segs = [(txt, WHITE, fmb)]
                for s_, c_, f_ in segs:
                    d.text((x, y), s_, font=f_, fill=c_)
                    x += len(s_) * cw
                if r.get('cursor') and int(t * 2.2) % 2 == 0:
                    d.rectangle([x + 2, y + 4, x + cw, y + 40], fill=WHITE)
            else:
                col = (252, 165, 165) if r['kind'] == 'out' and r['L'] and r['L'].get('err') else SOFT
                if r['kind'] == 'cont':
                    col = WHITE
                txt = r['text']
                hit = None
                for h_ in hl:
                    if h_ and h_ in txt and r['L'] is not None and r['L']['step'] is not None:
                        hit = h_
                if hit:
                    i0 = txt.index(hit)
                    hx0 = x + i0 * cw - 6
                    hx1 = x + (i0 + len(hit)) * cw + 6
                    pa = ease((t - st['start'] - 0.3) / 0.4)
                    d.rounded_rectangle([hx0, y - 2, hx0 + (hx1 - hx0) * pa, y + 42], 8, fill=(120, 80, 10))
                    d.text((x, y), txt, font=fm, fill=col)
                    d.text((x + i0 * cw, y), hit, font=fmb, fill=AMBER)
                else:
                    d.text((x, y), txt, font=fm, fill=col)
            y += lh
        # side
        sx0, sx1 = 1290, 1820
        if side == 'card':
            card = None
            for s in self.steps:
                if s['start'] <= t and s.get('card'):
                    card = s
            if card:
                age = t - card['start']
                a = back(age / 0.45)
                off = int((1 - clamp(a)) * 70)
                title, lines = card['card']
                panel(d, [sx0 + off, 140, sx1 + off, 830], outline=CYAN, width=3)
                d.text((sx0 + 40 + off, 196), 'COMMAND', font=font(F_BODYB, 24), fill=CYAN)
                ft = font(F_MONOB, 52 if len(title) <= 14 else 40)
                d.text((sx0 + 40 + off, 236), title, font=ft, fill=WHITE)
                d.line([(sx0 + 40 + off, 320), (sx1 - 40 + off, 320)], fill=(44, 58, 92), width=2)
                fl = font(F_BODY, 32)
                yy = 350
                for j, l in enumerate(lines):
                    la = ease((age - 0.3 - j * 0.25) / 0.4)
                    if la <= 0:
                        continue
                    ws = wrap(d, l, fl, sx1 - sx0 - 130)
                    d.ellipse([sx0 + 44 + off, yy + 12, sx0 + 60 + off, yy + 28], fill=AMBER)
                    for k, w_ in enumerate(ws):
                        rich(d, (sx0 + 80 + off, yy + k * 42), w_, fl, SOFT, hi=WHITE)
                    yy += 42 * len(ws) + 26
        elif side == 'bashi':
            draw_bashi(img, 1560, 840, 540, st.get('mood', 'normal'), st.get('arms', 'rest'), t)
            if st.get('say'):
                bubble(img, st['say'], (1300, 150), (1500, 380), t - st['start'], maxw=420)

    def draw_quiz(self, img, d, t):
        sp = self.spec
        st = self.step_at(t)
        d.text((150, 140), 'QUICK QUIZ', font=font(F_HEAD, 40), fill=AMBER)
        f = font(F_HEAD, 58)
        for i, l in enumerate(wrap(d, sp['q'], f, 1200)):
            rich(d, (150, 200 + i * 76), l, f, WHITE, hi=CYAN)
        opts = sp['options']
        reveal = st.get('reveal')
        ra = ease((t - st['start']) / 0.4) if reveal else 0
        for i, o in enumerate(opts):
            r, c = divmod(i, 2)
            x = 150 + c * 680
            y = 400 + r * 170
            a = back((t - 0.5 - i * 0.15) / 0.4)
            if a <= 0:
                continue
            ok = i == sp['answer']
            col = CYAN
            fill = PANEL
            if reveal:
                col = mix(CYAN, GREEN if ok else (71, 85, 105), ra)
                fill = mix(PANEL, (20, 70, 55) if ok else PANEL, ra)
            sc = int((1 - clamp(a)) * 40)
            panel(d, [x + sc, y + sc, x + 640 - sc, y + 140 - sc], fill=fill, outline=col, width=4 if (reveal and ok) else 2)
            d.text((x + 36, y + 42), 'ABCD'[i], font=font(F_HEAD, 46), fill=col)
            d.text((x + 100, y + 46), o, font=font(F_MONOB, 40), fill=WHITE if not reveal or ok else MUTED)
            if reveal and ok and ra > 0.5:
                d.text((x + 590, y + 70), '✓', font=font(F_BODYB, 56), fill=GREEN, anchor='mm')
        if not reveal:
            left = 5 - (t - st['start'] - 1.5)
            cx, cy, rr = 1660, 330, 90
            d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=(44, 58, 92), width=12)
            frac = clamp(left / 5)
            if t - st['start'] > 1.5:
                d.arc([cx - rr, cy - rr, cx + rr, cy + rr], -90, -90 + 360 * frac, fill=AMBER, width=12)
            n = int(math.ceil(clamp(left, 0, 5))) if t - st['start'] > 1.5 else 5
            d.text((cx, cy), str(n), font=font(F_HEAD, 80), fill=WHITE, anchor='mm')
            draw_bashi(img, 1660, 840, 360, 'think', 'think', t)
        else:
            draw_props(img, d, [('sparkles', (1420, 160, 1880, 380))], t)
            draw_bashi(img, 1660, 840, 420, 'celebrate', 'up', t)

    def draw_recap(self, img, d, t):
        sp = self.spec
        st = self.step_at(t)
        d.text((150, 140), sp.get('heading', 'Recap'), font=font(F_HEAD, 56), fill=WHITE)
        items = sp['items']
        panel(d, [150, 240, 1250, 260 + 92 * len(items) + 30], outline=GREEN, width=3)
        for i, (c, m) in enumerate(items):
            a = ease((t - 0.4 - i * 0.35) / 0.4)
            if a <= 0:
                continue
            y = 275 + i * 92
            off = int((1 - a) * 50)
            d.text((200 + off, y), '$ ' + c, font=font(F_MONOB, 40), fill=GREEN)
            d.text((760 + off, y + 6), m, font=font(F_BODY, 34), fill=SOFT)
            if i < len(items) - 1:
                d.line([(190, y + 76), (1210, y + 76)], fill=(30, 41, 70), width=2)
        draw_bashi(img, 1580, 850, 540, st.get('mood', 'celebrate'), st.get('arms', 'up'), t)
        hw = st.get('homework')
        if hw:
            a = back((t - st['start']) / 0.5)
            if a > 0:
                f = font(F_HEAD, 40)
                y = 280 + 92 * len(items) + 50
                bw = tw(d, hw.replace('*', ''), f) + 70
                d.rounded_rectangle([150, y, 150 + bw, y + 74], 37, fill=(60, 45, 10), outline=AMBER, width=3)
                rich(d, (185, y + 12), hw, f, WHITE, hi=AMBER)

    def draw_outro(self, img, d, t):
        sp = self.spec
        d.text((150, 170), 'NEXT EPISODE · TOMORROW 5 PM IST', font=font(F_HEAD, 36), fill=AMBER)
        f = font(F_HEAD, 76)
        for i, l in enumerate(wrap(d, sp['next'], f, 900)):
            rich(d, (150, 230 + i * 96), l, f, WHITE, hi=CYAN)
        # subscribe button
        pulse = 1 + 0.05 * math.sin(t * 5)
        bw, bh = int(420 * pulse), int(100 * pulse)
        x, y = 150, 640
        d.rounded_rectangle([x, y, x + bw, y + bh], 50, fill=RED)
        d.text((x + bw // 2, y + bh // 2), 'SUBSCRIBE', font=font(F_HEAD, int(44 * pulse)), fill=WHITE, anchor='mm')
        d.text((x + 10, y + 120), '+ turn on the bell', font=font(F_BODYS, 34), fill=SOFT)
        draw_bashi(img, 860, 860, 380, 'happy', 'wave', t)
        # right half left empty for YouTube end-screen elements (soft frames as guides)
        for k, (yy, hh) in enumerate(((180, 380), (600, 300))):
            d.rounded_rectangle([1190, yy, 1810, yy + hh], 26, outline=(30, 41, 70), width=2)


# ---------------------------------------------------------------- episode / timeline
def load_ep(path):
    spec = importlib.util.spec_from_file_location('ep', path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.EPISODE


def build(ep):
    scenes = [Scene(s, ep) for s in ep['scenes']]
    t = 0.0
    for s in scenes:
        s.t0 = t
        t += s.dur
    return scenes, t


FADE = 0.35


def frame_at(scenes, ep, total, i, t_local):
    s = scenes[i]
    gt = s.t0 + t_local
    bg = background(gt)
    img = bg.copy()
    s.draw(img, t_local)
    a = min(1.0, t_local / FADE, (s.dur - t_local) / FADE)
    if a < 1.0:
        img = Image.blend(bg, img, clamp(a))
    draw_chrome(img, ep, gt, total)
    return img


def render_scene(args):
    ep_path, i, outdir = args
    ep = load_ep(ep_path)
    scenes, total = build(ep)
    s = scenes[i]
    n = int(round(s.dur * FPS))
    tmp = os.path.join(outdir, f'scene_{i:02d}.tmp.mp4')
    fin = os.path.join(outdir, f'scene_{i:02d}.mp4')
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
           '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '19',
           '-pix_fmt', 'yuv420p', '-g', '60', tmp]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(n):
        img = frame_at(scenes, ep, total, i, f / FPS)
        p.stdin.write(img.tobytes())
    p.stdin.close()
    if p.wait() != 0:
        raise RuntimeError(f'ffmpeg failed on scene {i}')
    os.replace(tmp, fin)
    return i, n


# ---------------------------------------------------------------- audio
def _env(n, a=0.005, dcy=0.2):
    t = np.arange(n) / SR
    return np.minimum(1, t / a) * np.exp(-t / dcy)


def _lp(x, cut):
    from scipy.signal import butter, lfilter
    b, a = butter(2, cut / (SR / 2))
    return lfilter(b, a, x)


def _hp(x, cut):
    from scipy.signal import butter, lfilter
    b, a = butter(2, cut / (SR / 2), 'high')
    return lfilter(b, a, x)


def nf(n):
    return 440 * 2 ** ((n - 69) / 12)


def music(total):
    rng = np.random.default_rng(7)
    bpm = 84
    beat = 60 / bpm
    bar = 4 * beat
    chords = [[57, 60, 64, 67], [53, 57, 60, 64], [48, 52, 55, 59], [55, 59, 62, 64]]  # Am7 Fmaj7 Cmaj7 G6
    bass = [45, 41, 36, 43]
    nbars = 8
    L = int(nbars * bar * SR)
    keys = np.zeros(L); bs = np.zeros(L); dr = np.zeros(L)

    def put(buf, at, sig):
        i = int(at * SR)
        j = min(len(buf), i + len(sig))
        if i < len(buf):
            buf[i:j] += sig[:j - i]

    for b in range(nbars):
        ch = chords[b % 4]
        t0 = b * bar
        for hit, vel in ((0, 1.0), (2.5 * beat, 0.6)):
            n = int(2.6 * SR)
            tt = np.arange(n) / SR
            sig = np.zeros(n)
            for k, m in enumerate(ch):
                f = nf(m + 12)
                trem = 1 + 0.25 * np.sin(2 * np.pi * 4.2 * tt)
                sig += (np.sin(2 * np.pi * f * tt) + 0.35 * np.sin(4 * np.pi * f * tt) + 0.12 * np.sin(6 * np.pi * f * tt)) * trem
            sig *= _env(n, 0.01, 0.9) * vel * 0.06
            put(keys, t0 + hit + 0.012 * rng.standard_normal(), sig)
        for hit in (0, 2 * beat, 3.5 * beat):
            n = int(0.6 * SR); tt = np.arange(n) / SR
            f = nf(bass[b % 4])
            put(bs, t0 + hit, np.sin(2 * np.pi * f * tt) * _env(n, 0.01, 0.35) * 0.22)
        for q in range(4):
            tq = t0 + q * beat
            if q in (0, 2):
                n = int(0.3 * SR); tt = np.arange(n) / SR
                fr = 45 + 75 * np.exp(-tt / 0.04)
                put(dr, tq, np.sin(2 * np.pi * np.cumsum(fr) / SR) * _env(n, 0.002, 0.12) * 0.45)
            else:
                n = int(0.25 * SR)
                sn = rng.standard_normal(n) * _env(n, 0.002, 0.07) * 0.10
                put(dr, tq, sn)
            for e in (0, 0.5):
                n = int(0.06 * SR)
                sw = 0.06 if e else 0
                put(dr, tq + e * beat + sw * beat * 0, _hp(rng.standard_normal(n), 7000) * _env(n, 0.001, 0.02) * (0.05 if e else 0.035))
    mixl = _lp(keys, 3200) + _lp(bs, 400) + _lp(dr, 9000)
    # vinyl crackle
    crack = np.zeros(L)
    idx = rng.integers(0, L, int(L / SR * 12))
    crack[idx] = rng.uniform(-0.25, 0.25, len(idx))
    mixl += _lp(crack, 5000) * 0.25 + _lp(rng.standard_normal(L), 1200) * 0.006
    reps = int(math.ceil(total * SR / L)) + 1
    out = np.tile(mixl, reps)[:int(total * SR)]
    n = len(out)
    fade = np.ones(n)
    fi = int(2.0 * SR); fo = int(3.0 * SR)
    fade[:fi] = np.linspace(0, 1, fi)
    fade[-fo:] = np.linspace(1, 0, fo)
    return out * fade


def sfx(kind, rng):
    if kind == 'click':
        n = int(0.025 * SR)
        s = _hp(rng.standard_normal(n), 2500) * _env(n, 0.0005, 0.006) * rng.uniform(0.10, 0.18)
        return s
    if kind == 'enter':
        n = int(0.06 * SR)
        return _lp(rng.standard_normal(n), 3000) * _env(n, 0.001, 0.015) * 0.35
    if kind == 'whoosh':
        n = int(0.7 * SR)
        x = rng.standard_normal(n)
        lo, hi = _lp(x, 600), _lp(x, 4000)
        k = np.linspace(0, 1, n)
        s = lo * (1 - k) + hi * k
        e = np.sin(np.pi * np.clip(np.arange(n) / n, 0, 1)) ** 2
        return s * e * 0.10
    if kind == 'pop':
        n = int(0.12 * SR); tt = np.arange(n) / SR
        f = 520 + 600 * tt / 0.12
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(n, 0.002, 0.04) * 0.18
    if kind == 'buzz':
        n = int(0.5 * SR); tt = np.arange(n) / SR
        s = np.sign(np.sin(2 * np.pi * 110 * tt)) + np.sign(np.sin(2 * np.pi * 116.5 * tt))
        return _lp(s, 1400) * _env(n, 0.005, 0.25) * 0.10
    if kind == 'ding':
        n = int(1.4 * SR); tt = np.arange(n) / SR
        s = np.sin(2 * np.pi * 1318.5 * tt) + 0.6 * np.sin(2 * np.pi * 1975.5 * tt)
        return s * _env(n, 0.002, 0.45) * 0.16
    if kind == 'tick':
        n = int(0.04 * SR); tt = np.arange(n) / SR
        return np.sin(2 * np.pi * 1500 * tt) * _env(n, 0.001, 0.01) * 0.16
    if kind == 'chime':
        out = np.zeros(int(0.9 * SR))
        for k, m in enumerate((84, 88, 91)):
            n = int(0.7 * SR); tt = np.arange(n) / SR
            s = np.sin(2 * np.pi * nf(m) * tt) * _env(n, 0.002, 0.25) * 0.08
            i = int(k * 0.07 * SR)
            out[i:i + n] += s[:len(out) - i]
        return out
    if kind == 'sparkle':
        out = np.zeros(int(1.5 * SR))
        for k in range(10):
            n = int(0.3 * SR); tt = np.arange(n) / SR
            s = np.sin(2 * np.pi * rng.uniform(2000, 4200) * tt) * _env(n, 0.001, 0.08) * 0.05
            i = int(k * 0.11 * SR)
            out[i:i + n] += s[:len(out) - i]
        return out
    return np.zeros(1)


def make_audio(scenes, total, path):
    rng = np.random.default_rng(11)
    m = music(total) * 0.85
    fx = np.zeros_like(m)
    for s in scenes:
        for (tl, kind) in s.events:
            sig = sfx(kind, rng)
            i = int((s.t0 + tl) * SR)
            if i >= len(fx):
                continue
            j = min(len(fx), i + len(sig))
            fx[i:j] += sig[:j - i]
    mix_ = m + fx
    peak = np.max(np.abs(mix_)) or 1
    mix_ = mix_ / peak * 0.89
    st = np.stack([mix_, mix_ * 0.98], 1)
    pcm = (st * 32767).astype(np.int16)
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())


# ---------------------------------------------------------------- thumbnail + upload text
def thumbnail(ep, path):
    th = ep['thumb']
    img = background(3.0).resize((1280, 720), Image.LANCZOS)
    d = ImageDraw.Draw(img)
    f1 = font(F_HEAD, 190)
    d.text((60, 70), th['big'], font=f1, fill=GREEN, stroke_width=8, stroke_fill=(2, 6, 18))
    f2 = font(F_HEAD, 92)
    for i, l in enumerate(th['lines']):
        d.text((66, 300 + i * 110), l, font=f2, fill=WHITE if i == 0 else AMBER, stroke_width=6, stroke_fill=(2, 6, 18))
    if th.get('cmd'):
        fc = font(F_MONOB, 48)
        cw_ = tw(d, th['cmd'], fc) + 60
        d.rounded_rectangle([66, 560, 66 + cw_, 650], 18, fill=TERM, outline=GREEN, width=4)
        d.text((96, 578), th['cmd'], font=fc, fill=GREEN)
    spr = bashi_sprite(th.get('mood', 'happy'), th.get('arms', 'wave'), 2, False, 560)
    img.paste(spr, (1280 - spr.width - 10, 720 - spr.height + 20), spr)
    fb = font(F_HEAD, 46)
    d.ellipse([1110, 30, 1250, 170], fill=AMBER, outline=(2, 6, 18), width=5)
    d.text((1180, 82), 'EP', font=font(F_HEAD, 30), fill=INK, anchor='mm')
    d.text((1180, 122), str(ep['number']), font=fb, fill=INK, anchor='mm')
    d.rounded_rectangle([830, 40, 1090, 100], 14, fill=TERM, outline=CYAN, width=3)
    d.text((960, 70), '>_ Tech-dev', font=font(F_HEAD, 32), fill=WHITE, anchor='mm')
    img.save(path, quality=92)


def fmt(t):
    t = int(t)
    return f'{t // 60}:{t % 60:02d}'


def upload_text(ep, scenes, total, outdir):
    up = ep['upload']
    chapters, seen = [], set()
    for s in scenes:
        c = s.spec.get('chapter')
        if c and c not in seen:
            seen.add(c)
            chapters.append((s.t0, c))
    chapters[0] = (0, chapters[0][1])
    # keep chapters >= 10 s apart
    clean = []
    for t, c in chapters:
        if not clean or t - clean[-1][0] >= 10:
            clean.append((t, c))
    ch_txt = '\n'.join(f'{fmt(t)} {c}' for t, c in clean)
    cmds = '\n'.join(up['commands'])
    desc = (f"{up['hook']}\n\n"
            "I'm Shivam Singh Verma, a DevOps & SRE engineer with 5 years of experience building CI/CD pipelines, "
            "running cloud infrastructure on AWS & GCP, and managing projects.\n\n"
            f"📺 Linux Zero to Hero: a new episode every day at 5 PM IST.\n\n"
            f"⏱️ Chapters\n{ch_txt}\n\n"
            f"🔑 What you'll learn\n" + '\n'.join('• ' + b for b in up['learn']) + "\n\n"
            f"🧾 Cheat sheet (copy & practice)\n{cmds}\n\n"
            f"📝 Homework: {up['homework']}\n\n"
            f"➡️ Next: {up['next']}\n\n"
            "🔔 Subscribe to Tech-dev for practical DevOps, SRE & Cloud videos.\n\n"
            f"💬 {up['question']}\n\n"
            + ' '.join(up['hashtags']))
    data = {'title': up['title'], 'description': desc, 'tags': up['tags'], 'duration': round(total, 1),
            'chapters': clean}
    json.dump(data, open(os.path.join(outdir, 'upload.json'), 'w'), indent=2, ensure_ascii=False)
    with open(os.path.join(outdir, 'upload.txt'), 'w') as f:
        f.write(f"TITLE\n{up['title']}\n\nDESCRIPTION\n{desc}\n\nTAGS\n{', '.join(up['tags'])}\n")
    with open(os.path.join(outdir, 'script.txt'), 'w') as f:
        for s in scenes:
            for st in s.steps:
                if st.get('cap'):
                    f.write(f"[{fmt(s.t0 + st['start'])}] {st['cap'].replace('*', '')}\n")
    return data


# ---------------------------------------------------------------- main
def main():
    ep_path, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    ep = load_ep(ep_path)
    scenes, total = build(ep)
    print(f'{len(scenes)} scenes, total {total:.1f}s ({fmt(total)})')
    if '--stills' in sys.argv:
        ts = [float(x) for x in sys.argv[sys.argv.index('--stills') + 1].split(',')]
        for gt in ts:
            for i, s in enumerate(scenes):
                if s.t0 <= gt < s.t0 + s.dur:
                    frame_at(scenes, ep, total, i, gt - s.t0).save(os.path.join(outdir, f'still_{gt:06.1f}.jpg'), quality=90)
        thumbnail(ep, os.path.join(outdir, 'thumbnail.jpg'))
        upload_text(ep, scenes, total, outdir)
        for s in scenes:
            print(f'  {fmt(s.t0)} {s.kind:9s} {s.dur:5.1f}s  {s.spec.get("chapter", "")}')
        return
    thumbnail(ep, os.path.join(outdir, 'thumbnail.jpg'))
    upload_text(ep, scenes, total, outdir)
    make_audio(scenes, total, os.path.join(outdir, 'audio.wav'))
    order = sorted(range(len(scenes)), key=lambda i: -scenes[i].dur)
    with Pool(int(os.environ.get('JOBS', '2'))) as pool:
        for i, n in pool.imap_unordered(render_scene, [(ep_path, i, outdir) for i in order]):
            print(f'  scene {i} done ({n} frames)', flush=True)
    with open(os.path.join(outdir, 'concat.txt'), 'w') as f:
        for i in range(len(scenes)):
            f.write(f"file 'scene_{i:02d}.mp4'\n")
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i',
                    os.path.join(outdir, 'concat.txt'), '-c', 'copy', os.path.join(outdir, 'silent.mp4')], check=True)
    tmp = os.path.join(outdir, 'video.tmp.mp4')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', os.path.join(outdir, 'silent.mp4'), '-i',
                    os.path.join(outdir, 'audio.wav'), '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac',
                    '-b:a', '192k', '-shortest', '-movflags', '+faststart', tmp], check=True)
    os.replace(tmp, os.path.join(outdir, 'video.mp4'))
    print('done', os.path.join(outdir, 'video.mp4'))


if __name__ == '__main__':
    main()
