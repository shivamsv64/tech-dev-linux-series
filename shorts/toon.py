"""Desk Life drawing kit: sketchy hand-drawn cartoon look for Tech-dev Shorts.

Everything is drawn in code with Pillow at 2x and downsampled. Lines "boil" (re-jitter) ~10 times a second,
like hand-drawn animation. Original characters only (no brand mascots, no copied characters).

World coordinates are the 1080x1920 frame; Ink scales them by SS internally.
"""
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
import os

W, H, SS = 1080, 1920, 2
HERE = os.path.dirname(os.path.abspath(__file__))

INK = (27, 26, 30)
PAPER = (216, 217, 200)        # warm grey-green paper (day)
PAPER_NIGHT = (96, 104, 126)   # blue-grey wall at night
WHITE = (250, 250, 244)
RED = (214, 64, 58)
SKY = (176, 208, 226)
NAVY = (36, 46, 74)
WOOD = (176, 146, 112)
WOOD_D = (140, 112, 84)
STICKY = (252, 226, 120)
SCREEN = (24, 28, 34)

# series accents: (muted fill for clothes/props, bright for text highlights)
ACCENT = {
    'linux': ((112, 172, 118), (88, 214, 120)),
    'git': ((226, 168, 74), (255, 190, 60)),
    'devops': ((92, 170, 206), (80, 200, 255)),
    'funny': ((232, 132, 92), (255, 150, 80)),
}

# original cast (human cartoons). top=None means the series accent colour.
CAST = {
    'rohan': {'name': 'Rohan', 'skin': (244, 208, 172), 'top': None, 'hair': 'messy', 'haircol': (40, 32, 30)},
    'meera': {'name': 'Meera', 'skin': (226, 182, 142), 'top': (104, 132, 160), 'hair': 'bob', 'haircol': (30, 26, 28),
              'glasses': True},
    'khanna': {'name': 'Khanna sir', 'skin': (214, 168, 128), 'top': (236, 236, 226), 'hair': 'bald',
               'haircol': (60, 52, 48), 'mustache': True, 'tie': RED},
    'tara': {'name': 'Tara', 'skin': (236, 196, 160), 'top': (196, 112, 146), 'hair': 'ponytail', 'haircol': (70, 40, 30)},
}


def font(name, size):
    p = {'luck': 'LuckiestGuy-Regular.ttf', 'kalam': 'Kalam-Bold.ttf', 'hand': 'PatrickHand-Regular.ttf'}.get(name)
    if p:
        return ImageFont.truetype(os.path.join(HERE, 'fonts', p), size)
    sys_fonts = {
        'mono': '/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf',
        'mono_r': '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',
        'pop': '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf',
    }
    try:
        return ImageFont.truetype(sys_fonts[name], size)
    except Exception:
        return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', size)


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


# ------------------------------------------------------------------ ink
class Ink:
    """Wobbly ink drawing on a 2x canvas. All coords in 1x frame units."""

    def __init__(self, img, rng, amp=1.6):
        self.img = img
        self.d = ImageDraw.Draw(img)
        self.r = rng
        self.amp = amp

    def _p(self, pts):
        return [(x * SS, y * SS) for x, y in pts]

    def dense(self, pts, closed=False, step=16, amp=None):
        amp = self.amp if amp is None else amp
        if closed:
            pts = list(pts) + [pts[0]]
        out = []
        for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
            n = max(1, int(math.hypot(x1 - x0, y1 - y0) / step))
            for i in range(n):
                t = i / n
                out.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t))
        out.append(pts[-1])
        o = np.zeros(2)
        res = []
        for x, y in out:
            o = o * 0.6 + self.r.uniform(-amp, amp, 2)
            res.append((x + o[0], y + o[1]))
        if closed:
            res[-1] = res[0]
        return res

    def line(self, pts, w=5, col=INK, amp=None, closed=False):
        p = self._p(self.dense(pts, closed, amp=amp))
        self.d.line(p, fill=col, width=int(w * SS), joint='curve')
        r = w * SS / 2
        for x, y in (p[0], p[-1]):
            self.d.ellipse([x - r, y - r, x + r, y + r], fill=col)

    def poly(self, pts, fill=None, w=5, col=INK, amp=None):
        p = self.dense(pts, True, amp=amp)
        if fill is not None:
            self.d.polygon(self._p(p), fill=fill)
        if w:
            pp = self._p(p)
            self.d.line(pp, fill=col, width=int(w * SS), joint='curve')

    def ell_pts(self, cx, cy, rx, ry, n=40, a0=0, a1=360, rot=0):
        pts = []
        for i in range(n + 1 if a1 - a0 < 360 else n):
            a = math.radians(a0 + (a1 - a0) * i / (n if a1 - a0 < 360 else n))
            x, y = rx * math.cos(a), ry * math.sin(a)
            if rot:
                c, s = math.cos(rot), math.sin(rot)
                x, y = x * c - y * s, x * s + y * c
            pts.append((cx + x, cy + y))
        return pts

    def ellipse(self, cx, cy, rx, ry, fill=None, w=5, col=INK, amp=None, rot=0):
        self.poly(self.ell_pts(cx, cy, rx, ry, rot=rot), fill, w, col, amp)

    def arc(self, cx, cy, rx, ry, a0, a1, w=5, col=INK, amp=None):
        self.line(self.ell_pts(cx, cy, rx, ry, 24, a0, a1), w, col, amp)

    def rect(self, x0, y0, x1, y1, fill=None, w=5, col=INK, amp=None):
        self.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], fill, w, col, amp)

    def rrect(self, x0, y0, x1, y1, r, fill=None, w=5, col=INK, amp=None):
        pts = []
        for cx, cy, a in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
            for i in range(7):
                ang = math.radians(a + 90 * i / 6)
                pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
        self.poly(pts, fill, w, col, amp)

    def flat(self, pts, fill):
        """filled shape without outline, no jitter (for glows, shadows)"""
        self.d.polygon(self._p(pts), fill=fill)

    def hatch(self, x0, y0, x1, y1, gap=26, col=None, w=2, ang=1.0):
        col = col or mix(INK, PAPER, 0.75)
        x = x0
        while x < x1:
            self.line([(x, y0), (x + (y1 - y0) * 0.0 + self.r.uniform(-4, 4), y1)], w, col, amp=0.8)
            x += gap + self.r.uniform(-6, 6)


def curve(pts, n=10):
    """Catmull-Rom through pts"""
    if len(pts) < 3:
        return pts
    P = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in range(2)))
    out.append(pts[-1])
    return out


# ------------------------------------------------------------------ faces
def eyes(ink, hx, hy, R, mood, look=(0, 0), boil=0, glasses=False):
    ex, ey, rx, ry = 0.34 * R, -0.08 * R, 0.30 * R, 0.37 * R
    lw = max(4, R * 0.035)
    lx, ly = look
    if mood == 'shock':
        rx, ry = rx * 1.12, ry * 1.12
    for side in (-1, 1):
        cx, cy = hx + side * ex, hy + ey
        if mood in ('happy', 'cheer', 'laugh'):
            ink.arc(cx, cy + ry * 0.25, rx * 0.8, ry * 0.55, 200, 340, lw * 1.3)
            continue
        if mood == 'sleep':
            ink.arc(cx, cy + ry * 0.1, rx * 0.8, ry * 0.4, 20, 160, lw * 1.2)
            continue
        ink.ellipse(cx, cy, rx, ry, fill=WHITE, w=lw)
        pr = {'shock': 0.07, 'panic': 0.09}.get(mood, 0.13) * R
        jit = (ink.r.uniform(-1, 1) * R * 0.03) if mood == 'panic' else 0
        px = cx + lx * rx * 0.45 + jit + (side * -0.05 * R if mood == 'smug' else 0)
        py = cy + ly * ry * 0.4 + (0.08 * R if mood in ('tired', 'sad') else 0)
        if mood == 'smug':
            px += 0.12 * R
        ink.ellipse(px, py, pr, pr * 1.08, fill=INK, w=0)
        if mood not in ('shock', 'panic'):
            ink.ellipse(px - pr * 0.35, py - pr * 0.35, pr * 0.28, pr * 0.28, fill=WHITE, w=0)
        if mood == 'tired':
            # bloodshot veins
            for k in range(5):
                a = math.radians(150 + k * 60 + side * 10)
                x0, y0 = cx + math.cos(a) * rx * 0.95, cy + math.sin(a) * ry * 0.95
                x1, y1 = cx + math.cos(a) * rx * 0.55, cy + math.sin(a) * ry * 0.55
                ink.line([(x0, y0), ((x0 + x1) / 2 + ink.r.uniform(-4, 4), (y0 + y1) / 2), (x1, y1)], lw * 0.35, RED, amp=1)
        # lids
        lid = {'tired': 0.48, 'smug': 0.42, 'sad': 0.22, 'angry': 0.28}.get(mood, 0)
        if lid:
            top = cy - ry
            yl = top + 2 * ry * lid
            pts = ink.ell_pts(cx, cy, rx, ry, 30, 180, 360)
            pts = [(x, min(y, yl)) for x, y in pts]
            ink.flat(pts + [(cx + rx, yl), (cx - rx, yl)], fill=SKIN_CUR[0])
            ink.line([(cx - rx * 0.98, yl), (cx + rx * 0.98, yl)], lw)
            ink.ellipse(cx, cy, rx, ry, None, w=lw)
        if mood == 'tired':
            ink.arc(cx, cy + ry * 1.05, rx * 0.75, ry * 0.3, 20, 160, lw * 0.6, col=mix(INK, SKIN_CUR[0], 0.45))
        if glasses:
            ink.ellipse(cx, cy, rx * 1.18, ry * 1.08, None, w=lw * 0.9)
    if glasses and mood not in ('happy', 'cheer', 'laugh', 'sleep'):
        ink.line([(hx - ex + rx * 1.15, hy + ey), (hx + ex - rx * 1.15, hy + ey)], lw * 0.8)
    # brows
    bl = {'angry': (25, -1), 'sad': (-22, 1), 'panic': (-25, 1), 'shock': (0, 0), 'worried': (-20, 1),
          'smug': (12, -1), 'determined': (18, -1), 'tired': (-8, 1)}.get(mood, (0, 0))
    by = hy + ey - ry - 0.13 * R - (0.08 * R if mood == 'shock' else 0)
    for side in (-1, 1):
        cx = hx + side * ex
        a = -math.radians(bl[0]) * side
        dx, dy = math.cos(a) * rx * 0.75, math.sin(a) * rx * 0.75
        ink.line([(cx - dx, by - dy), (cx + dx, by + dy)], lw * 1.25)


def mouth(ink, hx, hy, R, mood, boil=0):
    lw = max(4, R * 0.035)
    mx, my = hx, hy + 0.5 * R
    if mood in ('happy', 'cheer', 'laugh'):
        pts = ink.ell_pts(mx, my - 0.04 * R, 0.24 * R, 0.2 * R, 20, 0, 180)
        ink.poly(pts, fill=(120, 40, 46), w=lw)
        ink.ellipse(mx, my + 0.08 * R, 0.1 * R, 0.05 * R, fill=(222, 110, 110), w=0)
    elif mood == 'shock':
        ink.ellipse(mx, my + 0.04 * R, 0.1 * R, 0.15 * R, fill=(90, 30, 36), w=lw)
    elif mood == 'panic':
        ink.rrect(mx - 0.24 * R, my - 0.07 * R, mx + 0.24 * R, my + 0.12 * R, 0.05 * R, fill=WHITE, w=lw)
        ink.line([(mx - 0.22 * R, my + 0.025 * R), (mx + 0.22 * R, my + 0.025 * R)], lw * 0.6)
        for k in (-1, 0, 1):
            ink.line([(mx + k * 0.1 * R, my - 0.06 * R), (mx + k * 0.1 * R, my + 0.11 * R)], lw * 0.5)
    elif mood == 'angry':
        ink.rrect(mx - 0.2 * R, my - 0.04 * R, mx + 0.2 * R, my + 0.08 * R, 0.03 * R, fill=WHITE, w=lw)
        ink.line([(mx - 0.18 * R, my + 0.02 * R), (mx + 0.18 * R, my + 0.02 * R)], lw * 0.6)
    elif mood in ('sad', 'worried'):
        ink.arc(mx, my + 0.12 * R, 0.16 * R, 0.1 * R, 200, 340, lw)
    elif mood == 'tired':
        ink.line([(mx - 0.16 * R, my + 0.02 * R), (mx - 0.05 * R, my - 0.01 * R), (mx + 0.05 * R, my + 0.03 * R),
                  (mx + 0.16 * R, my)], lw)
    elif mood == 'smug':
        ink.line(curve([(mx - 0.14 * R, my + 0.02 * R), (mx + 0.05 * R, my + 0.03 * R), (mx + 0.2 * R, my - 0.08 * R)]), lw)
    elif mood == 'sleep':
        ink.ellipse(mx, my, 0.06 * R, 0.05 * R, fill=(90, 30, 36), w=lw * 0.7)
    elif mood == 'talk':
        o = 0.06 + 0.06 * (boil % 2)
        ink.ellipse(mx, my, 0.12 * R, o * R, fill=(110, 36, 42), w=lw)
    elif mood == 'determined':
        ink.line([(mx - 0.15 * R, my), (mx + 0.15 * R, my - 0.02 * R)], lw)
    else:  # calm
        ink.arc(mx, my - 0.06 * R, 0.15 * R, 0.1 * R, 30, 150, lw)


SKIN_CUR = [(244, 208, 172)]


def hair_back(ink, c, hx, hy, R):
    if c['hair'] == 'bob':
        pts = [(hx - 1.12 * R, hy - 0.2 * R), (hx - 1.05 * R, hy + 0.9 * R), (hx - 0.6 * R, hy + 1.0 * R),
               (hx + 0.6 * R, hy + 1.0 * R), (hx + 1.05 * R, hy + 0.9 * R), (hx + 1.12 * R, hy - 0.2 * R)]
        top = ink.ell_pts(hx, hy - 0.15 * R, 1.12 * R, 1.0 * R, 20, 180, 360)
        ink.poly(top + pts[::-1][:1] + pts[::-1], fill=c['haircol'], w=5)
    if c['hair'] == 'ponytail':
        ink.poly(curve([(hx + 0.7 * R, hy - 0.6 * R), (hx + 1.35 * R, hy - 0.3 * R), (hx + 1.45 * R, hy + 0.5 * R),
                        (hx + 1.1 * R, hy + 0.9 * R), (hx + 0.95 * R, hy + 0.2 * R)]), fill=c['haircol'], w=5)


def hair_front(ink, c, hx, hy, R):
    col = c['haircol']
    if c['hair'] == 'messy':
        pts = []
        n = 11
        for i in range(n + 1):
            a = math.radians(195 + (150) * i / n)
            rr = R * (1.02 if i % 2 == 0 else 1.32)
            if i in (0, n):
                rr = R * 0.98
            pts.append((hx + rr * math.cos(a), hy - 0.05 * R + rr * math.sin(a) * 1.02))
        inner = ink.ell_pts(hx, hy - 0.05 * R, 0.98 * R, 0.62 * R, 16, 345, 195)
        inner = [(x, y) for x, y in reversed(ink.ell_pts(hx, hy - 0.42 * R, 0.86 * R, 0.3 * R, 16, 180, 360))]
        ink.poly(pts + inner, fill=col, w=5)
    elif c['hair'] == 'bob':
        bang = ink.ell_pts(hx, hy - 0.2 * R, 1.02 * R, 0.85 * R, 18, 190, 350)
        low = [(hx + 0.95 * R, hy - 0.35 * R), (hx + 0.4 * R, hy - 0.45 * R), (hx, hy - 0.38 * R),
               (hx - 0.45 * R, hy - 0.48 * R), (hx - 0.98 * R, hy - 0.3 * R)]
        ink.poly(bang + low, fill=col, w=5)
        ink.ellipse(hx + 0.1 * R, hy - 1.12 * R, 0.32 * R, 0.26 * R, fill=col, w=5)
    elif c['hair'] == 'ponytail':
        bang = ink.ell_pts(hx, hy - 0.15 * R, 1.0 * R, 0.85 * R, 18, 190, 350)
        low = [(hx + 0.9 * R, hy - 0.45 * R), (hx - 0.2 * R, hy - 0.62 * R), (hx - 0.95 * R, hy - 0.35 * R)]
        ink.poly(bang + low, fill=col, w=5)
    elif c['hair'] == 'bald':
        for side in (-1, 1):
            ink.poly([(hx + side * 0.92 * R, hy - 0.35 * R), (hx + side * 1.08 * R, hy - 0.15 * R),
                      (hx + side * 1.04 * R, hy + 0.2 * R), (hx + side * 0.9 * R, hy + 0.05 * R)], fill=col, w=4)
        ink.arc(hx - 0.25 * R, hy - 0.62 * R, 0.3 * R, 0.16 * R, 200, 290, 4, col=WHITE)


def head(ink, who, hx, hy, R, mood='calm', look=(0, 0), boil=0, accent=None):
    c = CAST[who]
    SKIN_CUR[0] = c['skin']
    lw = max(4, R * 0.035)
    hair_back(ink, c, hx, hy, R)
    for side in (-1, 1):  # ears
        ink.ellipse(hx + side * 0.98 * R, hy + 0.08 * R, 0.14 * R, 0.2 * R, fill=c['skin'], w=lw)
    pts = ink.ell_pts(hx, hy, R, R * 1.02)
    pts = [(x, y + (0.07 * R if y > hy + 0.5 * R else 0)) for x, y in pts]
    ink.poly(pts, fill=c['skin'], w=lw * 1.1)
    hair_front(ink, c, hx, hy, R)
    if mood in ('happy', 'cheer', 'laugh', 'shock', 'panic'):  # cheeks
        for side in (-1, 1):
            ink.ellipse(hx + side * 0.6 * R, hy + 0.35 * R, 0.13 * R, 0.07 * R, fill=mix(c['skin'], (230, 110, 110), 0.45), w=0)
    eyes(ink, hx, hy, R, mood, look, boil, c.get('glasses'))
    ink.line([(hx + 0.02 * R, hy + 0.18 * R), (hx + 0.08 * R, hy + 0.3 * R), (hx - 0.02 * R, hy + 0.32 * R)], lw * 0.7)
    if c.get('mustache'):
        ink.poly(curve([(hx - 0.3 * R, hy + 0.44 * R), (hx - 0.15 * R, hy + 0.34 * R), (hx, hy + 0.38 * R),
                        (hx + 0.15 * R, hy + 0.34 * R), (hx + 0.3 * R, hy + 0.44 * R), (hx, hy + 0.46 * R)], 4),
                 fill=c['haircol'], w=lw * 0.6)
    mouth(ink, hx, hy + (0.06 * R if c.get('mustache') else 0), R, mood, boil)


# ------------------------------------------------------------------ bodies
POSES = {  # (elbow, hand) per side in R units from head centre; side -1 = left of screen
    'rest': {-1: ((-0.85, 1.95), (-0.6, 2.45)), 1: ((0.85, 1.95), (0.6, 2.45))},
    'type': {-1: ((-0.95, 1.95), (-0.42, 2.2)), 1: ((0.95, 1.95), (0.42, 2.2))},
    'point': {-1: ((-0.85, 1.95), (-0.6, 2.45)), 1: ((1.1, 1.05), (1.55, 0.35))},
    'facepalm': {-1: ((-0.85, 1.95), (-0.6, 2.45)), 1: ((0.75, 1.55), (0.15, 0.15))},
    'cheer': {-1: ((-1.05, 0.55), (-1.15, -0.55)), 1: ((1.05, 0.55), (1.15, -0.55))},
    'shrug': {-1: ((-1.05, 1.75), (-1.3, 1.2)), 1: ((1.05, 1.75), (1.3, 1.2))},
    'phone': {-1: ((-0.85, 1.95), (-0.6, 2.45)), 1: ((0.85, 2.0), (0.32, 1.35))},
    'mug': {-1: ((-0.95, 1.9), (-0.55, 1.6)), 1: ((0.85, 1.95), (0.6, 2.45))},
    'wave': {-1: ((-0.85, 1.95), (-0.6, 2.45)), 1: ((1.1, 0.95), (1.3, -0.15))},
    'headhold': {-1: ((-1.15, 1.2), (-0.95, 0.15)), 1: ((1.15, 1.2), (0.95, 0.15))},
    'think': {-1: ((-0.85, 1.95), (-0.6, 2.45)), 1: ((0.7, 1.75), (0.3, 0.9))},
}
FRONT_HANDS = ('facepalm', 'think')  # hands drawn over the face


def person(ink, who, hx, hy, R, mood='calm', pose='rest', boil=0, accent=(112, 172, 118), stand=False, look=(0, 0),
           seat_h=None):
    c = CAST[who]
    top = c['top'] or accent
    lw = max(4, R * 0.04)
    sh_y = hy + 1.05 * R
    if stand:
        # legs
        for side in (-1, 1):
            x = hx + side * 0.28 * R
            ink.line([(x, hy + 2.5 * R), (x + side * 0.05 * R, hy + 3.9 * R)], lw * 2.2, (60, 64, 80))
            ink.ellipse(x + side * 0.12 * R, hy + 3.98 * R, 0.24 * R, 0.1 * R, fill=INK, w=0)
    # torso
    tw_top, tw_bot = 0.62 * R, 0.78 * R
    bot = hy + (2.65 * R if stand else 2.8 * R)
    if c.get('tie'):
        pass
    ink.poly(curve([(hx - tw_top, sh_y), (hx - tw_bot, bot), (hx + tw_bot, bot), (hx + tw_top, sh_y),
                    (hx, sh_y - 0.08 * R)], 4), fill=top, w=lw)
    ink.line([(hx - 0.2 * R, sh_y + 0.02 * R), (hx, sh_y + 0.25 * R), (hx + 0.2 * R, sh_y + 0.02 * R)], lw * 0.8)
    if c.get('tie'):
        ink.poly([(hx, sh_y + 0.22 * R), (hx - 0.1 * R, sh_y + 0.9 * R), (hx, sh_y + 1.05 * R), (hx + 0.1 * R, sh_y + 0.9 * R)],
                 fill=c['tie'], w=lw * 0.7)
    elif who == 'rohan':  # hoodie strings + pocket
        for side in (-1, 1):
            ink.line([(hx + side * 0.12 * R, sh_y + 0.2 * R), (hx + side * 0.14 * R, sh_y + 0.6 * R)], lw * 0.5)
    arms = POSES.get(pose, POSES['rest'])
    hand_pts = {}
    for side in (-1, 1):
        (ex, ey), (hxx, hyy) = arms[side]
        if pose == 'type':
            hyy += 0.06 * ((boil + (side > 0)) % 2)
        if pose == 'wave' and side == 1:
            hxx += 0.15 * (1 if boil % 2 else -1)
        sx, sy = hx + side * 0.62 * R, sh_y + 0.18 * R
        e = (hx + ex * R, hy + ey * R)
        h = (hx + hxx * R, hy + hyy * R)
        hand_pts[side] = h
        if pose in FRONT_HANDS and side == 1:
            continue
        ink.line(curve([(sx, sy), e, h], 6), lw * 2.6, INK)
        ink.line(curve([(sx, sy), e, h], 6), lw * 1.5, top, amp=0.6)
        ink.ellipse(h[0], h[1], 0.13 * R, 0.13 * R, fill=c['skin'], w=lw * 0.8)
        if pose == 'point' and side == 1:
            ink.line([h, (h[0] + 0.22 * R, h[1] - 0.2 * R)], lw * 1.1)
    head(ink, who, hx, hy, R, mood, look, boil)
    if pose in FRONT_HANDS:
        (ex, ey), (hxx, hyy) = arms[1]
        sx, sy = hx + 0.62 * R, sh_y + 0.18 * R
        e = (hx + ex * R, hy + ey * R); h = (hx + hxx * R, hy + hyy * R)
        ink.line(curve([(sx, sy), e, h], 6), lw * 2.6, INK)
        ink.line(curve([(sx, sy), e, h], 6), lw * 1.5, top, amp=0.6)
        ink.ellipse(h[0], h[1], 0.3 * R, 0.24 * R, fill=c['skin'], w=lw)
        for k in range(3):
            ink.line([(h[0] - 0.2 * R + k * 0.16 * R, h[1] - 0.15 * R), (h[0] - 0.22 * R + k * 0.16 * R, h[1] + 0.08 * R)],
                     lw * 0.5)
    if pose == 'phone':
        px, py = hand_pts[1]
        ink.rrect(px - 0.2 * R, py - 0.55 * R, px + 0.2 * R, py + 0.05 * R, 0.05 * R, fill=(40, 44, 52), w=lw * 0.8)
        ink.rect(px - 0.15 * R, py - 0.5 * R, px + 0.15 * R, py - 0.02 * R, fill=(150, 220, 255), w=0)
        ink.ellipse(px, py, 0.13 * R, 0.13 * R, fill=c['skin'], w=lw * 0.8)
    if pose == 'mug':
        px, py = hand_pts[-1]
        mug(ink, px + 0.05 * R, py - 0.1 * R, 0.28 * R)
    return hand_pts


def mug(ink, x, y, s, steam=True):
    ink.rrect(x - s * 0.5, y - s * 0.6, x + s * 0.5, y + s * 0.6, s * 0.12, fill=WHITE, w=5)
    ink.arc(x + s * 0.55, y, s * 0.25, s * 0.28, -80, 80, 5)
    ink.rect(x - s * 0.5, y - s * 0.1, x + s * 0.5, y + s * 0.15, fill=(214, 64, 58), w=0)
    if steam:
        for k in (-1, 1):
            xx = x + k * s * 0.18
            ink.line(curve([(xx, y - s * 0.75), (xx + s * 0.15, y - s * 1.0), (xx - s * 0.1, y - s * 1.25),
                            (xx + s * 0.1, y - s * 1.5)]), 3, mix(INK, PAPER, 0.5))


# ------------------------------------------------------------------ effects
def fx(ink, kinds, hx, hy, R, boil, accent):
    for k in kinds or []:
        if k == 'sweat':
            for i, (dx, dy) in enumerate(((1.05, -0.55), (-1.1, -0.35), (0.9, 0.1))):
                yy = hy + dy * R + ((boil + i) % 3) * 0.08 * R
                x = hx + dx * R
                ink.poly(curve([(x, yy - 0.16 * R), (x + 0.08 * R, yy), (x, yy + 0.07 * R), (x - 0.08 * R, yy),
                                (x, yy - 0.16 * R)], 4), fill=(170, 214, 240), w=4)
        elif k == '!':
            x, y = hx + 1.25 * R, hy - 1.15 * R
            ink.poly([(x - 0.1 * R, y - 0.5 * R), (x + 0.12 * R, y - 0.5 * R), (x + 0.04 * R, y + 0.12 * R),
                      (x - 0.03 * R, y + 0.12 * R)], fill=RED, w=5)
            ink.ellipse(x, y + 0.3 * R, 0.08 * R, 0.08 * R, fill=RED, w=5)
        elif k == '?':
            f = font('luck', int(R * 0.9))
            ink.d.text(((hx + 1.1 * R) * SS, (hy - 1.6 * R) * SS), '?', font=font('luck', int(R * 0.9 * SS)), fill=INK)
        elif k == 'zzz':
            for i in range(3):
                s = int(R * (0.35 + 0.15 * i) * SS)
                ink.d.text(((hx + (0.9 + 0.3 * i) * R) * SS, (hy - (0.9 + 0.45 * i) * R - (boil % 3) * 6) * SS), 'z',
                           font=font('luck', s), fill=INK)
        elif k == 'lines':  # radial speed lines behind (call before person)
            for i in range(26):
                a = i / 26 * 2 * math.pi + ink.r.uniform(-0.05, 0.05)
                r0 = 1.9 * R + ink.r.uniform(0, 0.4 * R)
                r1 = 4.5 * R
                ink.line([(hx + math.cos(a) * r0, hy + math.sin(a) * r0), (hx + math.cos(a) * r1, hy + math.sin(a) * r1)],
                         ink.r.uniform(3, 7), mix(INK, PAPER, 0.35))
        elif k == 'sparkle':
            for i, (dx, dy) in enumerate(((-1.2, -0.9), (1.25, -0.7), (1.0, 0.6))):
                x, y = hx + dx * R, hy + dy * R
                s = 0.16 * R * (1 + 0.3 * ((boil + i) % 2))
                ink.poly([(x, y - s), (x + s * 0.25, y - s * 0.25), (x + s, y), (x + s * 0.25, y + s * 0.25), (x, y + s),
                          (x - s * 0.25, y + s * 0.25), (x - s, y), (x - s * 0.25, y - s * 0.25)], fill=accent, w=4)
        elif k == 'steam':  # angry steam
            for side in (-1, 1):
                x = hx + side * 1.05 * R
                ink.line(curve([(x, hy - 0.8 * R), (x + side * 0.2 * R, hy - 1.1 * R), (x, hy - 1.35 * R),
                                (x + side * 0.15 * R, hy - 1.6 * R)]), 6, WHITE)
        elif k == 'tear':
            for side in (-1, 1):
                x = hx + side * 0.34 * R
                y0 = hy + 0.25 * R
                ink.poly([(x - 0.07 * R, y0), (x + 0.07 * R, y0), (x + 0.09 * R, y0 + 0.7 * R), (x - 0.09 * R, y0 + 0.7 * R)],
                         fill=(150, 205, 240), w=3)


# ------------------------------------------------------------------ sets
def glow(img, cx, cy, rx, ry, col, strength=0.5):
    """additive soft glow on the 2x canvas"""
    g = Image.new('L', (int(rx * 2 * SS / 4), int(ry * 2 * SS / 4)), 0)
    gd = ImageDraw.Draw(g)
    w, h = g.size
    for i in range(12):
        f = 1 - i / 12
        gd.ellipse([w / 2 * (1 - f), h / 2 * (1 - f), w / 2 * (1 + f), h / 2 * (1 + f)], fill=int(255 * strength * (i + 1) / 12))
    g = g.filter(ImageFilter.GaussianBlur(w / 10)).resize((int(rx * 2 * SS), int(ry * 2 * SS)))
    layer = Image.new('RGB', g.size, col)
    box = (int((cx - rx) * SS), int((cy - ry) * SS))
    base = img.crop((box[0], box[1], box[0] + g.size[0], box[1] + g.size[1]))
    from PIL import ImageChops
    lit = ImageChops.screen(base, layer)
    base.paste(lit, (0, 0), g)
    img.paste(base, box)


def wall(ink, night, y_floor=1240):
    col = PAPER_NIGHT if night else PAPER
    ink.d.rectangle([0, 0, W * SS, H * SS], fill=col)
    floor = mix(col, (120, 108, 96) if not night else (50, 54, 70), 0.45)
    ink.d.rectangle([0, y_floor * SS, W * SS, H * SS], fill=floor)
    ink.line([(-10, y_floor), (W + 10, y_floor)], 5)
    ink.hatch(40, y_floor + 30, W, H, gap=60, col=mix(floor, INK, 0.25))


def window(ink, x0, y0, x1, y1, night, boil=0):
    if night:
        ink.rect(x0, y0, x1, y1, fill=NAVY, w=7)
        ink.ellipse(x0 + (x1 - x0) * 0.7, y0 + 90, 46, 46, fill=(240, 232, 196), w=4)
        for i, (sx, sy) in enumerate(((0.2, 0.15), (0.45, 0.3), (0.3, 0.45), (0.85, 0.4))):
            s = 7 + (boil + i) % 2 * 3
            ink.d.ellipse([(x0 + (x1 - x0) * sx - s) * SS, (y0 + (y1 - y0) * sy - s) * SS,
                           (x0 + (x1 - x0) * sx + s) * SS, (y0 + (y1 - y0) * sy + s) * SS], fill=(240, 236, 210))
        # city silhouette
        x = x0 + 6
        k = 0
        while x < x1 - 6:
            bw = 50 + (k * 37) % 40
            bh = 120 + (k * 73) % 170
            ink.rect(x, y1 - bh, min(x + bw, x1 - 6), y1 - 4, fill=(24, 30, 50), w=3)
            for wy in range(int(y1 - bh + 20), int(y1 - 20), 36):
                if (k + wy // 36) % 3 == 0:
                    ink.d.rectangle([(x + 14) * SS, wy * SS, (x + 26) * SS, (wy + 14) * SS], fill=(250, 214, 120))
            x += bw + 6; k += 1
    else:
        ink.rect(x0, y0, x1, y1, fill=SKY, w=7)
        for cx, cy, s in ((x0 + 120, y0 + 110, 1.0), (x1 - 110, y0 + 190, 0.8)):
            for dx, dy, r in ((0, 0, 40), (45, -15, 50), (95, 0, 38)):
                ink.ellipse(cx + dx * s, cy + dy * s, r * s, r * s * 0.8, fill=WHITE, w=0)
    ink.line([((x0 + x1) / 2, y0), ((x0 + x1) / 2, y1)], 7)
    ink.line([(x0, (y0 + y1) / 2), (x1, (y0 + y1) / 2)], 7)
    ink.rect(x0 - 20, y1, x1 + 20, y1 + 26, fill=mix(WOOD, WHITE, 0.3), w=5)


def frame_art(ink, x0, y0, x1, y1):
    ink.rect(x0, y0, x1, y1, fill=mix(WOOD, PAPER, 0.3), w=6)
    ink.rect(x0 + 22, y0 + 22, x1 - 22, y1 - 22, fill=(236, 226, 190), w=4)
    ink.poly([(x0 + 30, y1 - 30), (x0 + (x1 - x0) * 0.45, y0 + (y1 - y0) * 0.4), (x1 - 30, y1 - 30)],
             fill=(140, 170, 130), w=4)
    ink.ellipse(x1 - 60, y0 + 60, 18, 18, fill=(240, 180, 90), w=3)


def plant(ink, x, y, s=1.0):
    for a in (-60, -25, 5, 35, 65):
        r = math.radians(a - 90)
        ink.poly(curve([(x, y - 60 * s), (x + math.cos(r) * 70 * s - 20 * s, y - 60 * s + math.sin(r) * 120 * s),
                        (x + math.cos(r) * 140 * s, y - 60 * s + math.sin(r) * 190 * s),
                        (x + math.cos(r) * 70 * s + 20 * s, y - 60 * s + math.sin(r) * 120 * s)], 4),
                 fill=(108, 156, 100), w=4)
    ink.poly([(x - 60 * s, y - 70 * s), (x + 60 * s, y - 70 * s), (x + 45 * s, y + 40 * s), (x - 45 * s, y + 40 * s)],
             fill=(196, 112, 80), w=5)


def draw_lamp(ink, x, y, on=True):
    ink.line([(x, y), (x, y - 230)], 6)
    ink.ellipse(x, y + 4, 60, 14, fill=INK, w=0)
    ink.poly([(x - 70, y - 230), (x + 70, y - 230), (x + 40, y - 330), (x - 40, y - 330)],
             fill=(250, 232, 170) if on else (200, 196, 180), w=6)


def desk(ink, y_top, night, accent, boil=0, laptop=True, mug_at=True, laptop_x=700):
    ink.poly([(-20, y_top), (W + 20, y_top), (W + 20, y_top + 34), (-20, y_top + 34)], fill=mix(WOOD, (40, 40, 60), 0.35 if night else 0), w=6)
    ink.rect(-20, y_top + 34, W + 20, y_top + 300, fill=mix(WOOD_D, (40, 40, 60), 0.35 if night else 0), w=6)
    ink.hatch(0, y_top + 60, W, y_top + 290, gap=55, col=mix(WOOD_D, INK, 0.3))
    if laptop:
        lx = laptop_x
        ink.poly([(lx - 170, y_top - 230), (lx + 170, y_top - 230), (lx + 185, y_top + 4), (lx - 185, y_top + 4)],
                 fill=(196, 198, 204), w=6)
        ink.ellipse(lx, y_top - 118, 36, 36, fill=accent, w=4)
        ink.d.text(((lx - 23) * SS, (y_top - 138) * SS), 'TD', font=font('luck', 34 * SS), fill=INK)
    if mug_at:
        mug(ink, 200, y_top - 50, 70)


def set_bg(ink, img, name, accent, boil=0, lamp=True):
    night = name.endswith('night')
    if name in ('desk_night', 'desk_day'):
        wall(ink, night)
        window(ink, 90, 330, 470, 800, night, boil)
        frame_art(ink, 760, 360, 980, 560)
        if lamp:
            draw_lamp(ink, 930, 1170, on=True)
    elif name == 'bed_night':
        wall(ink, True, 1500)
        window(ink, 640, 330, 980, 760, True, boil)
        frame_art(ink, 90, 380, 300, 560)
    elif name in ('office', 'office_night'):
        wall(ink, night, 1300)
        # whiteboard
        ink.rect(120, 360, 960, 820, fill=WHITE if not night else (200, 204, 214), w=7)
        for k, yy in enumerate((440, 520, 600)):
            ink.line([(170, yy), (420 + 90 * k, yy + 6), (560 + 40 * k, yy - 4)], 4, (90, 110, 170))
        ink.rect(600, 430, 900, 740, None, w=4, col=(200, 80, 80))
        ink.line([(620, 700), (700, 600), (780, 650), (880, 470)], 5, (200, 80, 80))
        plant(ink, 980, 1280, 1.1)
    elif name == 'meeting':
        wall(ink, False, 1300)
        ink.rect(160, 380, 920, 820, fill=(40, 46, 60), w=8)
        ink.line([(240, 720), (400, 600), (560, 660), (760, 470), (860, 520)], 8, (110, 200, 140))
    else:  # plain paper
        ink.d.rectangle([0, 0, W * SS, H * SS], fill=PAPER_NIGHT if night else PAPER)


def screen_glow(img, hx, hy, R):
    glow(img, hx, hy + 0.2 * R, R * 1.8, R * 1.6, (110, 190, 255), 0.35)


# ------------------------------------------------------------------ inserts
def monitor(ink, night=True):
    ink.d.rectangle([0, 0, W * SS, H * SS], fill=PAPER_NIGHT if night else PAPER)
    ink.hatch(0, 0, W, H, gap=70, col=mix(PAPER_NIGHT if night else PAPER, INK, 0.12))
    ink.rrect(50, 360, 1030, 1230, 30, fill=(46, 48, 54), w=8)
    ink.rect(88, 400, 992, 1160, fill=SCREEN, w=5)
    ink.poly([(470, 1230), (610, 1230), (650, 1330), (430, 1330)], fill=(70, 72, 80), w=6)
    ink.rrect(330, 1320, 750, 1360, 12, fill=(70, 72, 80), w=6)
    for i, c in enumerate(((236, 96, 90), (240, 190, 80), (110, 200, 120))):
        ink.d.ellipse([(118 + i * 40) * SS, 420 * SS, (140 + i * 40) * SS, 442 * SS], fill=c)
    return (110, 470, 980, 1150)   # text area


def phone_insert(ink, skin, sleeve=(112, 172, 118)):
    ink.d.rectangle([0, 0, W * SS, H * SS], fill=PAPER_NIGHT)
    glow(ink.img, 540, 800, 520, 600, (140, 200, 255), 0.4)
    ink.rrect(270, 340, 810, 1340, 60, fill=(30, 32, 38), w=8)
    ink.rrect(300, 380, 780, 1300, 40, fill=(22, 26, 40), w=0)
    # fingers
    for k in range(3):
        ink.ellipse(255, 820 + k * 120, 48, 56, fill=skin, w=6)
    ink.ellipse(830, 880, 50, 64, fill=skin, w=6)
    ink.poly([(410, 1330), (680, 1330), (700, 1680), (390, 1680)], fill=skin, w=6)
    ink.poly([(370, 1640), (720, 1640), (760, 1940), (330, 1940)], fill=sleeve, w=6)
    ink.line([(385, 1700), (705, 1700)], 4)
    return (320, 420, 760, 1280)


def sticky(img, big, sub, accent, boil, rng):
    """sticky note card with rotated text, drawn on its own layer then pasted"""
    w, h = 760, 640
    layer = Image.new('RGBA', (w * SS, h * SS), (0, 0, 0, 0))
    ink = Ink(layer, rng)
    ink.poly([(20, 30), (w - 20, 20), (w - 30, h - 20), (30, h - 30)], fill=STICKY, w=6)
    ink.poly([(w / 2 - 110, 0), (w / 2 + 110, 6), (w / 2 + 104, 60), (w / 2 - 116, 54)], fill=(236, 236, 226, 255), w=3)
    d = ImageDraw.Draw(layer)
    size = 150
    f = font('luck', size * SS)
    while d.textlength(big, font=f) > (w - 110) * SS and size > 60:
        size -= 6; f = font('luck', size * SS)
    tw = d.textlength(big, font=f)
    d.text(((w * SS - tw) / 2, 150 * SS), big, font=f, fill=INK)
    if sub:
        fs = font('kalam', 58 * SS)
        lines = wrap(d, sub, fs, (w - 120) * SS)
        for i, ln in enumerate(lines[:3]):
            lw = d.textlength(ln, font=fs)
            d.text(((w * SS - lw) / 2, (150 + size + 40 + i * 74) * SS), ln, font=fs, fill=(60, 56, 70))
    ink.line([(120, 150 + size + 22), (w - 120, 150 + size + 16)], 6, accent)
    layer = layer.rotate(-2.5 + (boil % 2) * 0.4, resample=Image.BICUBIC, expand=False)
    img.paste(layer, (int((W - w) / 2 * SS), int(560 * SS)), layer)


def wrap(d, text, f, maxw):
    words = text.split()
    lines, cur = [], ''
    for wd in words:
        t = (cur + ' ' + wd).strip()
        if d.textlength(t, font=f) <= maxw:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


def giant_eye(ink, who, mood, boil, accent):
    c = CAST[who]
    SKIN_CUR[0] = c['skin']
    ink.d.rectangle([0, 0, W * SS, H * SS], fill=c['skin'])
    cx, cy, rx, ry = 560, 930, 430, 330
    lw = 16
    # head outline arcs at the edges (we're very close to the face)
    ink.arc(540, 980, 900, 1150, 200, 250, 12)
    if c['hair'] == 'messy':
        ink.poly([(-40, -40), (1120, -40), (1120, 260), (900, 330), (760, 230), (560, 320), (380, 210), (180, 300), (-40, 220)],
                 fill=c['haircol'], w=10)
    elif c['hair'] in ('bob', 'ponytail'):
        ink.poly(curve([(-40, -40), (1120, -40), (1120, 300), (820, 250), (520, 300), (220, 240), (-40, 330)], 6),
                 fill=c['haircol'], w=10)
    if c.get('glasses') and mood not in ('happy', 'cheer', 'laugh'):
        ink.ellipse(cx, cy, rx * 1.12, ry * 1.12, None, w=18)
    if mood in ('happy', 'cheer', 'laugh'):
        ink.arc(cx, cy + 80, rx * 0.85, ry * 0.6, 200, 340, 22)
        for i in range(3):
            fx(ink, ['sparkle'], cx, cy, 300, boil, accent)
        return
    ink.ellipse(cx, cy, rx, ry, fill=WHITE, w=lw)
    if mood == 'tired':
        for k in range(9):
            a = math.radians(120 + k * 33 + ink.r.uniform(-8, 8))
            pts = [(cx + math.cos(a) * rx * 0.97, cy + math.sin(a) * ry * 0.97)]
            for j in range(3):
                x, y = pts[-1]
                pts.append((x - math.cos(a) * rx * 0.13 + ink.r.uniform(-14, 14), y - math.sin(a) * ry * 0.13 + ink.r.uniform(-14, 14)))
            ink.line(pts, 4, RED, amp=1.5)
            x, y = pts[1]
            ink.line([(x, y), (x + ink.r.uniform(-40, 40), y + ink.r.uniform(-40, 40))], 3, RED, amp=1)
    pr = {'shock': 40, 'panic': 52}.get(mood, 110)
    jit = ink.r.uniform(-14, 14) if mood == 'panic' else 0
    py = cy + (60 if mood == 'tired' else 0)
    ink.ellipse(cx + jit, py, pr * 1.25, pr * 1.25, fill=(120, 84, 60) if mood not in ('shock', 'panic') else INK, w=6)
    ink.ellipse(cx + jit, py, pr * 0.7, pr * 0.7, fill=INK, w=0)
    if mood not in ('shock', 'panic'):
        ink.ellipse(cx - pr * 0.45, py - pr * 0.5, pr * 0.3, pr * 0.3, fill=WHITE, w=0)
    if mood in ('tired', 'sad', 'smug', 'angry'):
        lid = {'tired': 0.5, 'sad': 0.25, 'smug': 0.45, 'angry': 0.3}[mood]
        yl = cy - ry + 2 * ry * lid
        pts = ink.ell_pts(cx, cy, rx, ry, 40, 180, 360)
        pts = [(x, min(y, yl)) for x, y in pts]
        ink.flat(pts + [(cx + rx, yl), (cx - rx, yl)], fill=c['skin'])
        ink.line([(cx - rx * 0.99, yl), (cx + rx * 0.99, yl)], lw)
        ink.ellipse(cx, cy, rx, ry, None, w=lw)
        # lashes
        for k in range(5):
            x = cx - rx * 0.7 + k * rx * 0.35
            ink.line([(x, yl), (x - 10, yl - 40)], 8)
    if mood == 'tired':
        ink.arc(cx, cy + ry * 1.1, rx * 0.85, ry * 0.32, 15, 165, 10, col=mix(INK, c['skin'], 0.4))
        ink.arc(cx, cy + ry * 1.3, rx * 0.7, ry * 0.3, 25, 155, 8, col=mix(INK, c['skin'], 0.55))
    # brow
    ang = {'angry': 0.18, 'sad': -0.15, 'shock': 0, 'panic': -0.12, 'tired': -0.05}.get(mood, 0)
    by = cy - ry - 120 - (60 if mood == 'shock' else 0)
    ink.line([(cx - rx * 0.8, by - ang * 300), (cx + rx * 0.8, by + ang * 300)], 30)


def paper_grain(seed=3):
    rng = np.random.default_rng(seed)
    n = rng.normal(0, 1, (H // 4, W // 4)).astype(np.float32)
    g = Image.fromarray(np.clip(128 + n * 40, 0, 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)
    g = np.asarray(g, np.float32) / 255.0
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    v = 1 - 0.22 * (((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H / 2) / (H * 0.7)) ** 2)
    m = (0.94 + 0.06 * g) * v
    return np.clip(m, 0, 1)[..., None]
