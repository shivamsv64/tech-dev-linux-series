#!/usr/bin/env python3
"""Tech-dev engine v2 — illustrated backgrounds, camera moves, animated overlays, free narration.

    python3 v2/engine.py <episode_spec.py> <outdir> [--stills t1,t2,...]

Outputs in <outdir>: video.mp4, thumbnail.jpg, upload.json, upload.txt, script.txt
Looks: 'mission' (DevOps & SRE) and 'city' (Linux, Git). Spec format: v2/AUTHORING.md.
Narration: Kokoro (v2/tts.py, free, local). ElevenLabs is NOT used per episode; the only cloned-voice
audio is the one-time clip v2/assets/voice/intro_shivam.mp3 (title scene with 'intro': True).
"""
import sys, os, re, json, math, subprocess, functools, importlib.util, multiprocessing as mp
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import tts

W, H, FPS = 1920, 1080, 30
ART_DIR = os.path.join(HERE, 'assets', 'art')
GF = '/usr/share/fonts/truetype/google-fonts/'
DF = '/usr/share/fonts/truetype/dejavu/'
WHITE, MUTED, DIM = (241, 245, 249), (148, 163, 184), (100, 116, 139)

# ------------------------------------------------------------------ looks & series
LOOKS = {
    'mission': dict(accent=(56, 189, 248), warm=(251, 191, 36), bad=(248, 113, 113), ok=(52, 211, 153),
                    purple=(167, 139, 250), panel=(6, 12, 30, 208), edge=(56, 189, 248, 150), radius=6, hud=True,
                    label_font='mono', music=['mission_theme.mp3'], default_art='mc_room'),
    'city': dict(accent=(45, 212, 191), warm=(251, 191, 36), bad=(251, 113, 133), ok=(74, 222, 128),
                 purple=(167, 139, 250), panel=(20, 16, 40, 218), edge=(167, 139, 250, 120), radius=22, hud=False,
                 label_font='med', music=['city_theme.mp3'], default_art='city_hero', vig_k=1.35),
}
SERIES = {
    'devops': dict(look='mission', show='DevOps & SRE Zero to Hero',
                   line='📺 Day {n} of 100 · DevOps & SRE Zero to Hero: a free course with a new episode every day at 8 PM IST.'),
    'linux': dict(look='city', show='Linux Zero to Hero',
                  line='📺 Linux Zero to Hero, Episode {n}: a free course with new episodes every Tue, Thu & Sat at 5 PM IST.'),
    'git': dict(look='city', show='Git & GitHub: Beginner to Advanced',
                line='📺 Git & GitHub: Beginner to Advanced, Episode {n}: new episodes every Mon, Wed & Fri at 4 PM IST.'),
}
INTRO_CLIP = os.path.join(HERE, 'assets', 'voice', 'intro_shivam.mp3')
INTRO_TEXT = "Hi, I'm Shivam Singh Verma, and welcome to Tech-dev."

EP = None; TH = None; SCENES = None; TOTAL = 0.0   # set in main (inherited by render workers)

@functools.lru_cache(None)
def font(name, size):
    return ImageFont.truetype({'bold': GF + 'Poppins-Bold.ttf', 'med': GF + 'Poppins-Medium.ttf',
                               'reg': GF + 'Poppins-Regular.ttf', 'mono': DF + 'DejaVuSansMono-Bold.ttf',
                               'monor': DF + 'DejaVuSansMono.ttf', 'sym': DF + 'DejaVuSans-Bold.ttf'}[name], size)

def col(c):
    if isinstance(c, tuple): return c
    return {'ok': TH['ok'], 'bad': TH['bad'], 'warm': TH['warm'], 'accent': TH['accent'], 'purple': TH['purple'],
            'muted': MUTED, 'white': WHITE, None: WHITE}.get(c, WHITE)

# ------------------------------------------------------------------ easing / sprites
def clamp(x, a=0., b=1.): return a if x < a else b if x > b else x
def ease(x): x = clamp(x); return 1 - (1 - x) ** 3
def ease_io(x): x = clamp(x); return 3 * x * x - 2 * x * x * x
def win(t, t0, d=0.45): return ease((t - t0) / d)

@functools.lru_cache(2048)
def text_sprite(txt, fname, size, color):
    f = font(fname, size)
    l, t, r, b = f.getbbox(txt or ' ')
    asc, desc = f.getmetrics()
    top = int(asc * 0.22)
    im = Image.new('RGBA', (max(1, r - l + 8), asc + desc - top + 8), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((4 - l, 4 - top), txt, font=f, fill=color)
    return im

@functools.lru_cache(512)
def panel_sprite(w, h, tint=None, alpha=None):
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    fill = TH['panel'] if alpha is None else TH['panel'][:3] + (alpha,)
    edge = TH['edge'] if tint is None else tint + (200,)
    d.rounded_rectangle([0, 0, w - 1, h - 1], TH['radius'], fill=fill, outline=edge, width=2)
    if TH['hud']:
        c = (TH['accent'] if tint is None else tint) + (255,); L = min(22, w // 4, h // 3)
        for (x, y, sx, sy) in [(0, 0, 1, 1), (w - 1, 0, -1, 1), (0, h - 1, 1, -1), (w - 1, h - 1, -1, -1)]:
            d.line([(x, y + sy * L), (x, y), (x + sx * L, y)], fill=c, width=4)
    return im

@functools.lru_cache(256)
def rect(w, h, c):
    return Image.new('RGBA', (max(1, int(w)), max(1, int(h))), c)

def put(layer, sprite, x, y, a=1.0):
    if a <= 0.01: return
    if a < 0.99:
        s = sprite.copy(); arr = np.asarray(s.getchannel('A'), dtype=np.float32) * a
        s.putalpha(Image.fromarray(arr.astype(np.uint8))); sprite = s
    layer.alpha_composite(sprite, (int(x), int(y)))

def text(layer, txt, x, y, size, color, fname='bold', a=1.0, anchor='l'):
    c = col(color); s = text_sprite(str(txt), fname, size, c + (255,))
    if anchor == 'c': x -= s.width / 2
    elif anchor == 'r': x -= s.width
    put(layer, s, x, y, a)
    return s.width

def wrap(txt, fname, size, maxw):
    f = font(fname, size); lines, cur = [], ''
    for w in str(txt).split():
        t = (cur + ' ' + w).strip()
        if f.getlength(t) > maxw and cur: lines.append(cur); cur = w
        else: cur = t
    if cur: lines.append(cur)
    return lines

def label(L, txt, x, y, a=1.0, size=26):
    return text(L, txt.upper() if TH['label_font'] == 'mono' else txt, x, y, size, 'accent', TH['label_font'], a)

def check(L, x, y, size, c, a=1.0):
    text(L, '✓', x, y, size, c, 'sym', a)

# ------------------------------------------------------------------ narration & timing
LEAD, GAP = 0.15, 0.45

def strip_marks(s): return s.replace('*', '')

def build():
    """narrate every scene (cached), lay out the timeline, captions and SFX events"""
    vo_dir = os.path.join(OUT, 'vo'); os.makedirs(vo_dir, exist_ok=True)
    voice = EP.get('voice', tts.DEFAULT_VOICE)
    scenes, t = [], 0.0
    for i, sp in enumerate(EP['scenes']):
        sc = dict(spec=sp, kind=sp['type'], idx=i)
        clips, caps, cur = [], [], 0.0
        if sp.get('intro'):
            a = load_mono(INTRO_CLIP, tts.SR)
            clips.append((cur, a)); caps.append((cur, cur + len(a) / tts.SR, INTRO_TEXT)); cur += len(a) / tts.SR + 0.25
        for s in tts.sentences(sp['say']):
            tts_text = strip_marks(s)
            a = tts.synth_sentence(tts_text, voice, EP.get('speed', 1.0), vo_dir)
            d = len(a) / tts.SR
            clips.append((cur, a)); caps.append((cur, cur + d, s)); cur += d + 0.12
        vo_dur = cur
        dur = LEAD + vo_dur + GAP + sp.get('hold', 0) + (1.8 if sp['type'] == 'outro' else 0)
        sc.update(t0=t, t1=t + dur, va=LEAD, vd=vo_dur, clips=clips,
                  caps=[(LEAD + a, LEAD + b, s) for a, b, s in split_caps(caps)])
        scenes.append(sc); t += dur
    # art + camera (continuous camera when consecutive scenes share an art)
    presets = ['push', 'right', 'pull', 'left', 'push', 'up']
    prev = None
    for i, sc in enumerate(scenes):
        sp = sc['spec']
        sc['art'] = sp.get('art') or (prev['art'] if prev else TH['default_art'])
        if not os.path.exists(art_path(sc['art'])):
            print('WARNING: unknown art', sc['art'], '-> using', TH['default_art']); sc['art'] = TH['default_art']
        same = prev is not None and prev['art'] == sc['art']
        if same: z, fx, fy = prev['cam_end']
        else:
            fx, fy = sp.get('focus', (0.55, 0.5)); z = 1.16
        mv = sp.get('cam', presets[i % len(presets)])
        dz = {'push': .10, 'pull': -.10}.get(mv, 0.03); dx = {'left': -.07, 'right': .07}.get(mv, 0)
        dy = {'up': -.05, 'down': .05}.get(mv, 0)
        if mv == 'still': dz = dx = dy = 0
        z2 = clamp(z + dz, 1.03, 1.42)
        if z2 == z and mv in ('push', 'pull'): z2 = clamp(z - dz, 1.03, 1.42)
        sc['cam_start'] = (z, fx, fy); sc['cam_end'] = (z2, clamp(fx + dx, .25, .75), clamp(fy + dy, .3, .7))
        sc['xfade'] = (i > 0 and not same)
        prev = sc
    return scenes, t

def split_caps(caps):
    """break sentence captions into chunks of <= ~62 chars, timed by character share"""
    out = []
    for a, b, s in caps:
        words, chunks, cur = s.split(), [], []
        for w in words:
            cur.append(w); n = len(' '.join(cur))
            if (w[-1] in ',:;' and n > 30) or n > 58: chunks.append(cur); cur = []
        if cur:
            if chunks and len(' '.join(cur)) < 12: chunks[-1] += cur
            else: chunks.append(cur)
        tot = sum(len(' '.join(c)) for c in chunks); t = a
        for c in chunks:
            d = (b - a) * len(' '.join(c)) / tot; out.append((t, t + d, ' '.join(c))); t += d
    return out

# ------------------------------------------------------------------ backgrounds
def episode_media_dir():
    """This episode's media folder in the repo (devops-series/media/dayNN or media/epNN), or None."""
    d = CUSTOM_THUMB_DIRS.get((EP or {}).get('series'))
    return os.path.join(os.path.dirname(HERE), d.format(n=int(EP['number']))) if d else None


def art_path(name):
    """Episode art first: <media dir>/art/<name>.jpg (fresh FLUX art made by the daily Hugging Face prep
    task, either replacing a library art of the same name or adding a new one), then the library."""
    m = episode_media_dir()
    if m:
        p = os.path.join(m, 'art', name + '.jpg')
        if os.path.exists(p):
            return p
    return os.path.join(ART_DIR, name + '.jpg')


_ART = {}
def art(name):
    if name not in _ART:
        im = Image.open(art_path(name)).convert('RGB')
        _ART[name] = im.resize((int(W * 1.4), int(W * 1.4 * im.height / im.width)), Image.LANCZOS)
    return _ART[name]

def bg_frame(sc, p):
    (z0, x0, y0), (z1, x1, y1) = sc['cam_start'], sc['cam_end']
    q = ease_io(p) if not sc.get('linear_cam') else p
    z = z0 + (z1 - z0) * q; fx = x0 + (x1 - x0) * q; fy = y0 + (y1 - y0) * q
    im = art(sc['art']); aw, ah = im.size
    vw = aw / z; vh = vw * H / W
    if vh > ah: vh = ah; vw = vh * W / H
    cx = clamp(fx * aw, vw / 2, aw - vw / 2); cy = clamp(fy * ah, vh / 2, ah - vh / 2)
    return im.transform((W, H), Image.EXTENT, (cx - vw / 2, cy - vh / 2, cx + vw / 2, cy + vh / 2), Image.BILINEAR)

VIG_DEFAULT = dict(hook='left', title='left', outro='left', statement='left', bullets='left', qa='left', quiz='dim',
                   swap='left', bars='left', chips='right', timeline='top', pipeline='top', compare='dim', terminal='dim')

@functools.lru_cache(16)
def vignette(kind, k=1.0):
    y = np.linspace(0, 1, H)[:, None]; x = np.linspace(0, 1, W)[None, :]
    a = np.zeros((H, W), np.float32)
    a += np.clip((y - 0.62) / 0.38, 0, 1) ** 1.5 * 170 + np.clip((0.16 - y) / 0.16, 0, 1) * 120
    if kind == 'left': a += np.clip((0.62 - x) / 0.62, 0, 1) ** 1.1 * 165 * k
    if kind == 'right': a += np.clip((x - 0.38) / 0.62, 0, 1) ** 1.1 * 165 * k
    if kind == 'top': a += np.clip((0.55 - y) / 0.55, 0, 1) ** 1.3 * 130 * k
    if kind == 'dim': a += 120 * k
    im = Image.new('RGBA', (W, H), (4, 6, 18, 0)); im.putalpha(Image.fromarray(np.clip(a, 0, 225 if k <= 1 else 235).astype(np.uint8)))
    return im

# ------------------------------------------------------------------ scene drawers
def reveal_times(n, va, vd, start=.08, end=.78):
    if n <= 1: return [va + vd * start]
    return [va + vd * (start + (end - start) * i / (n - 1)) for i in range(n)]

def d_hook(L, sc, lt):
    sp, va, vd = sc['spec'], sc['va'], sc['vd']
    if sp.get('label'): label(L, sp['label'], 120, 240, win(lt, .2), 30)
    if sp.get('line'): text(L, sp['line'], 120, 290, 46, WHITE, 'bold', win(lt, .5))
    stats = sp.get('stats', [])
    ts = [va + vd * f for f in sp.get('at', [])] or reveal_times(len(stats), va, vd, .25, .62)
    for i, st in enumerate(stats):
        big, small, c = (list(st) + ['accent'])[:3]
        a = win(lt, ts[i]); y = 390 + i * 180 + (1 - a) * 30
        put(L, panel_sprite(580, 156, col(c)), 120, y, a)
        text(L, big, 160, y + 16, 76, c, 'bold', a); text(L, small, 160, y + 108, 30, WHITE, 'med', a)
    if sp.get('punch'):
        a = win(lt, va + vd * .9, .3)
        text(L, sp['punch'], 770, 520 - (1 - a) * 20, 140 if len(sp['punch']) < 8 else 80, 'warm', 'bold', a)

def d_title(L, sc, lt):
    sp = sc['spec']; a = win(lt, .1)
    label(L, sp.get('kicker', SERIES[EP['series']]['show']), 120, 320, a, 30)
    badge = sp.get('badge', EP.get('badge_long', EP['badge']))
    f = font('bold', 34); bw = int(f.getlength(badge)) + 52
    put(L, panel_sprite(bw, 64, TH['warm']), 120, 372, win(lt, .3)); text(L, badge, 146, 383, 34, 'warm', 'bold', win(lt, .3))
    lines = sp['title'] if isinstance(sp['title'], list) else [sp['title']]
    size = 110 if max(len(x) for x in lines) <= 16 else 84
    for i, w in enumerate(lines):
        b = win(lt, .55 + i * .25)
        text(L, w, 120, 460 + i * (size + 10) + (1 - b) * 40, size, WHITE if i == 0 else 'accent', 'bold', b)
    yb = 460 + len(lines) * (size + 10) + 20
    if sp.get('sub'): text(L, sp['sub'], 124, yb, 40, (203, 213, 225), 'med', win(lt, 1.2))
    bw = int(520 * win(lt, 1.0, .8))
    for j, c in enumerate([TH['accent'], TH['warm'], TH['purple']]):
        if bw > 24: L.alpha_composite(rect(bw // 3 - 8, 8, c + (255,)), (124 + j * (bw // 3), yb + 70))

def d_timeline(L, sc, lt):
    sp, va, vd = sc['spec'], sc['va'], sc['vd']
    stations, step = sp['stations'], sp.get('step', 0)
    prev = SCENES[sc['idx'] - 1] if sc['idx'] > 0 else None
    cont_in = prev is not None and prev['kind'] == 'timeline' and prev['spec'].get('label') == sp.get('label')
    pa = 1.0 if cont_in else win(lt, 0)
    n = len(stations); px, py, pw, ph = 80, 110, 1760, 250
    has_ctr = bool(sp.get('counter'))
    put(L, panel_sprite(pw, ph), px, py, pa); label(L, sp.get('label', ''), px + 40, py + 22, pa)
    span = (pw - 130 - (430 if has_ctr else 130)) / max(1, n - 1) if n > 1 else 0
    xs = [px + 130 + i * span for i in range(n)]; ly = py + 125
    prog = step + win(lt, va + vd * .15, 1.2)
    for i in range(n - 1):
        x0, x1 = xs[i] + 30, xs[i + 1] - 30
        L.alpha_composite(rect(x1 - x0, 4, DIM + (int(160 * pa),)), (int(x0), ly - 2))
        if i < step or (i == step - 1):
            L.alpha_composite(rect((x1 - x0) * clamp(prog - i), 4, TH['warm'] + (255,)), (int(x0), ly - 2))
    sz = 30 if n <= 5 else 25
    for i, st in enumerate(stations):
        name, sub = (list(st) + [''])[:2]
        if i > step: c, a, r = DIM, .55 * pa, 22
        elif i < step: c, a, r = TH['ok'], pa, 22
        else: c, a, r = col(sp.get('color', 'warm')), 1.0, 22 + 6 * (0.5 + 0.5 * math.sin(lt * 5))
        ring = Image.new('RGBA', (80, 80), (0, 0, 0, 0)); d = ImageDraw.Draw(ring)
        d.ellipse([40 - r, 40 - r, 40 + r, 40 + r], fill=c + (255,) if i <= step else (30, 41, 59, 255), outline=c + (255,), width=4)
        put(L, ring, xs[i] - 40, ly - 40, a)
        if i < step: text(L, '✓', xs[i], ly - 21, 28, (8, 12, 24), 'sym', a, 'c')
        else: text(L, str(i + 1), xs[i], ly - 21, 28, (8, 12, 24) if i == step else c, 'mono', a, 'c')
        text(L, name, xs[i], ly + 40, sz, WHITE if i <= step else MUTED, 'bold', a, 'c')
        if sub: text(L, sub, xs[i], ly + 80, sz - 5, c if i == step else MUTED, 'med', a, 'c')
    if has_ctr:
        ct = sp['counter']; cx = px + pw - 170
        v = ct.get('from', 0) + (ct.get('to', 0) - ct.get('from', 0)) * ease_io((lt - va - vd * .2) / max(.5, vd * .7))
        label(L, ct.get('label', ''), cx - font(TH['label_font'], 26).getlength(ct.get('label', '')) / 2, py + 30, pa)
        text(L, f"{int(round(v))}{ct.get('suffix', '')}", cx, py + 62, 110, 'bad' if ct.get('alarm') and v >= ct.get('alarm') else 'warm', 'bold', pa, 'c')
        if ct.get('unit'): text(L, ct['unit'], cx, py + 192, 24, (203, 213, 225), 'med', pa, 'c')
    if sp.get('alert'):
        al = sp['alert']; a = win(lt, va + vd * .5)
        put(L, panel_sprite(600, 130, TH['bad']), 1220, 470, a)
        text(L, al.get('title', ''), 1255, 490, 30, 'bad', TH['label_font'], a)
        text(L, al.get('text', ''), 1255, 540, 34, WHITE, 'bold', a)

def d_bars(L, sc, lt):
    sp, va, vd = sc['spec'], sc['va'], sc['vd']; bars = sp['bars']
    step = 140 if len(bars) <= 3 else max(88, 440 // len(bars))   # 4-5 bars: tighter rows so panel + punch stay above the captions
    ph = 120 + step * len(bars)
    put(L, panel_sprite(900, ph), 100, 230, win(lt, 0)); label(L, sp.get('label', ''), 140, 260, win(lt, 0))
    ts = reveal_times(len(bars), va, vd, .12, .4)
    for i, b in enumerate(bars):
        name, frac, c, val = b; a = win(lt, ts[i]); y = 330 + i * step
        text(L, name, 140, y, 34, WHITE, 'bold', a)
        L.alpha_composite(rect(600, 26, (51, 65, 85, int(200 * a))), (140, y + 56))
        L.alpha_composite(rect(max(6, 600 * frac * ease((lt - ts[i]) / 1.2)), 26, col(c) + (int(255 * a),)), (140, y + 56))
        text(L, val, 760, y + 46, 34, c, 'bold', a)
    if sp.get('punch'):
        a = win(lt, va + vd * .72)
        for j, ln in enumerate(wrap(sp['punch'], 'bold', 60, 1000)):
            text(L, ln, 100, 230 + ph + 40 + j * 74 + (1 - a) * 20, 60, 'warm', 'bold', a)

def d_chips(L, sc, lt):
    sp, va, vd = sc['spec'], sc['va'], sc['vd']; chips = sp['chips'][:12]; bx, by = 1010, 210
    put(L, panel_sprite(800, 560), bx, by, win(lt, 0)); label(L, sp.get('label', ''), bx + 40, by + 28, win(lt, 0))
    bad = sp.get('bad')
    for i, ch in enumerate(chips):
        a = win(lt, va + vd * .05 + i * 0.16, .3)
        gx, gy = bx + 50 + (i % 4) * 182, by + 100 + (i // 4) * 110
        broke = bad == i and lt > va + vd * .6
        c = TH['bad'] if broke else MUTED
        put(L, panel_sprite(160, 80, c, 235), gx, gy - (1 - a) * 40, a)
        text(L, ch, gx + 80, gy + 22 - (1 - a) * 40, 30 if len(ch) <= 7 else 22, c if broke else WHITE, 'mono', a, 'c')
    if sp.get('punch'):
        text(L, sp['punch'], bx + 40, by + 440, 46, 'bad' if bad is not None else 'warm', 'bold', win(lt, va + vd * .64))

def d_pipeline(L, sc, lt):
    sp, va, vd = sc['spec'], sc['va'], sc['vd']; nodes = sp['nodes']; n = len(nodes)
    prev = SCENES[sc['idx'] - 1] if sc['idx'] > 0 else None
    cont = prev is not None and prev['kind'] == 'pipeline' and prev['spec'].get('label') == sp.get('label')
    px, py, pw, ph = 160, 120, 1600, 250; pa = 1.0 if cont else win(lt, 0)
    put(L, panel_sprite(pw, ph), px, py, pa); label(L, sp.get('label', ''), px + 40, py + 22, pa)
    span = (pw - 460) / max(1, n - 1); xs = [px + 230 + i * span for i in range(n)]; ly = py + 135
    mode, fail = sp.get('mode', 'build'), sp.get('fail')
    if mode == 'flow': prog = (lt * 1.6) % (n + .6)
    else: prog = clamp((lt - va - vd * .3) / (vd * .55)) * (n - 0.001)
    for i in range(n - 1):
        x0, x1 = xs[i] + 50 + (n <= 4) * 0, xs[i + 1] - 50
        L.alpha_composite(rect(x1 - x0, 6, (51, 65, 85, int(220 * pa))), (int(x0), ly - 3))
        f = clamp(prog - i)
        if fail is not None and i >= fail: f = 0
        if f > 0: L.alpha_composite(rect((x1 - x0) * f, 6, TH['ok'] + (255,)), (int(x0), ly - 3))
    bw = min(220, int(span) - 30) if n > 1 else 220
    for i, nd in enumerate(nodes):
        on = prog >= i and (fail is None or i <= fail)
        failed = fail is not None and i == fail and prog >= i
        c = TH['bad'] if failed else (TH['ok'] if on else DIM)
        put(L, panel_sprite(bw, 100, c, 240), xs[i] - bw / 2, ly - 50, pa)
        sz = 34 if len(nd) <= 8 else 26
        if on or failed:
            sym = '✗' if failed else '✓'; tw = font('bold', sz).getlength(nd); cw = font('sym', 30).getlength(sym + ' ')
            x0 = xs[i] - (tw + cw) / 2; text(L, sym, x0, ly - 18, 30, c, 'sym', pa); text(L, nd, x0 + cw, ly - 22, sz, c, 'bold', pa)
        else: text(L, nd, xs[i], ly - 22, sz, WHITE, 'bold', pa, 'c')
    if sp.get('note'):
        a = win(lt, va + vd * .7)
        put(L, panel_sprite(1000, 110), px, py + ph + 40, a)
        text(L, sp['note'], px + 40, py + ph + 72, 36, 'bad' if fail is not None else WHITE, 'bold', a)
    if sp.get('swap'): d_swap(L, sc, lt, sp['swap'], y=450)

def d_swap(L, sc, lt, sw=None, y=300):
    sp, va, vd = sc['spec'], sc['va'], sc['vd']; sw = sw or sp
    a = win(lt, va + vd * .05)
    put(L, panel_sprite(1000, 300), 160, y, a); label(L, sw.get('label', ''), 200, y + 28, a, 28)
    w = text(L, sw['old'], 200, y + 80, 96, MUTED, 'bold', a)
    s = win(lt, va + vd * .45, .35)
    if s > 0: L.alpha_composite(rect(w * s, 8, TH['bad'] + (255,)), (200, y + 150))
    b = win(lt, va + vd * .55)
    text(L, '→', 200 + w + 30, y + 98, 80, 'ok', 'sym', b); text(L, sw['new'], 200 + w + 140, y + 80, 96, 'ok', 'bold', b)
    if sw.get('sub'): text(L, sw['sub'], 204, y + 220, 34, WHITE, 'med', win(lt, va + vd * .25))

def d_bullets(L, sc, lt):
    sp, va, vd = sc['spec'], sc['va'], sc['vd']; items = sp['items'][:6]
    side = sp.get('side', 'left'); px = 100 if side == 'left' else 900; pw = 920
    top = 200; hdr = 70 + (80 if sp.get('title') else 0)
    rows = [wrap(it if isinstance(it, str) else it[1], 'med', 36, pw - (230 if not isinstance(it, str) else 150)) for it in items]
    ph = hdr + sum(26 + 48 * len(r) for r in rows) + 30
    put(L, panel_sprite(pw, ph), px, top, win(lt, 0)); label(L, sp.get('label', ''), px + 40, top + 26, win(lt, 0))
    if sp.get('title'): text(L, sp['title'], px + 40, top + 66, 50, WHITE, 'bold', win(lt, .2))
    ts = [va + vd * f for f in sp['at']] if sp.get('at') else reveal_times(len(items), va, vd)
    y = top + hdr
    for i, it in enumerate(items):
        a = win(lt, ts[i]); dx = (1 - a) * 30
        if isinstance(it, str):
            dot = Image.new('RGBA', (22, 22), (0, 0, 0, 0)); ImageDraw.Draw(dot).ellipse([2, 2, 20, 20], fill=TH['accent'] + (255,))
            put(L, dot, px + 44 + dx, y + 16, a); tx = px + 90
        else:
            tag, _, c = (list(it) + ['accent'])[:3]
            f = font('mono', 26); tw = int(f.getlength(tag)) + 28
            put(L, panel_sprite(tw, 46, col(c), 230), px + 40 + dx, y + 4, a); text(L, tag, px + 54 + dx, y + 10, 26, c, 'mono', a)
            tx = px + 60 + max(tw, 120)
        for j, ln in enumerate(rows[i]):
            text(L, ln, tx + dx, y + j * 48, 36, WHITE, 'med', a)
        y += 26 + 48 * len(rows[i])

def d_terminal(L, sc, lt):
    sp, va, vd = sc['spec'], sc['va'], sc['vd']
    note = sp.get('note'); full = not note
    tx, ty = 80, 130; tw = 1760 if full else 1120; th_ = 680
    a0 = win(lt, 0)
    win_im = Image.new('RGBA', (tw, th_), (0, 0, 0, 0)); d = ImageDraw.Draw(win_im)
    d.rounded_rectangle([0, 0, tw - 1, th_ - 1], 16, fill=(10, 14, 26, 238), outline=TH['edge'][:3] + (160,), width=2)
    d.rounded_rectangle([0, 0, tw - 1, 50], 16, fill=(24, 30, 48, 255)); d.rectangle([0, 30, tw - 1, 50], fill=(24, 30, 48, 255))
    for k, c in enumerate([(248, 113, 113), (251, 191, 36), (74, 222, 128)]):
        d.ellipse([20 + k * 30, 16, 38 + k * 30, 34], fill=c + (255,))
    put(L, win_im, tx, ty, a0)
    text(L, sp.get('title', 'shivam@tech-dev: ~'), tx + tw / 2, ty + 10, 22, MUTED, 'monor', a0, 'c')
    prompt = sp.get('prompt', 'shivam@tech-dev:~$')
    steps = sp['steps']; n = len(steps)
    ts = [va + vd * s['at'] for s in steps] if all('at' in s for s in steps) else reveal_times(n, va, vd, .04, .7)
    fsz, lh = 28, 40; cw = font('mono', fsz).getlength('M'); maxc = int((tw - 60) / cw)
    lines = []   # (kind, text, alpha-progress)
    for i, s in enumerate(steps):
        if lt < ts[i]: break
        cmd = s.get('cmd', ''); typed = clamp((lt - ts[i]) / max(.5, min(1.4, len(cmd) * .045)))
        p = s.get('prompt', prompt)
        lines.append(('cmd', (p, cmd[:int(len(cmd) * typed)], typed < 1)))
        if typed >= 1:
            for o in s.get('out', []):
                lines.append(('out', o))
    vis = int((th_ - 80) / lh); lines = lines[-vis:]
    y = ty + 70
    for kind, v in lines:
        if kind == 'cmd':
            p, c, cursor = v
            pw_ = text(L, p, tx + 30, y, fsz, 'ok', 'mono', a0)
            text(L, ' ' + c[:maxc - len(p) - 1] + ('▌' if cursor and int(lt * 3) % 2 == 0 else ''), tx + 30 + pw_ - 8, y, fsz, WHITE, 'mono', a0)
        else:
            o = v; c = (203, 213, 225)
            if o.startswith('!'): o, c = o[1:], TH['bad']
            elif o.startswith('#'): c = DIM
            elif o.startswith('+'): o, c = o[1:], TH['ok']
            text(L, o[:maxc], tx + 30, y, fsz, c, 'monor', a0)
        y += lh
    if note:
        a = win(lt, va + vd * note.get('at', .3)); nx = tx + tw + 40; nw = 1840 - nx
        body = wrap(note.get('text', ''), 'med', 32, nw - 70)
        nh = 110 + 46 * len(body) + (60 if note.get('cmd') else 0)
        put(L, panel_sprite(nw, nh), nx, ty, a); label(L, note.get('label', 'KEY IDEA'), nx + 34, ty + 24, a, 24)
        text(L, note.get('title', ''), nx + 34, ty + 58, 40, 'warm', 'bold', a)
        for j, ln in enumerate(body): text(L, ln, nx + 34, ty + 116 + j * 46, 32, WHITE, 'med', a)
        if note.get('cmd'): text(L, note['cmd'], nx + 34, ty + 124 + 46 * len(body), 28, 'accent', 'mono', a)

def d_compare(L, sc, lt):
    sp, va, vd = sc['spec'], sc['va'], sc['vd']; cols, rows = sp['cols'], sp['rows']
    nc = len(cols); px, py, pw = 160, 140, 1600; kw = 360; cwid = (pw - kw - 60) / nc
    ph = 150 + 92 * len(rows); a0 = win(lt, 0)
    put(L, panel_sprite(pw, ph), px, py, a0); label(L, sp.get('label', ''), px + 40, py + 24, a0)
    colors = [TH['accent'], TH['warm'], TH['purple']]
    for j, c in enumerate(cols): text(L, c, px + kw + 30 + cwid * j + cwid / 2, py + 64, 40, colors[j % 3], 'bold', a0, 'c')
    ts = reveal_times(len(rows), va, vd, .1, .8)
    for i, r in enumerate(rows):
        a = win(lt, ts[i]); y = py + 140 + i * 92
        L.alpha_composite(rect(pw - 60, 2, DIM + (int(120 * a),)), (px + 30, y - 12))
        text(L, r[0], px + 40, y + 6, 32, MUTED, 'bold', a)
        for j, v in enumerate(r[1:nc + 1]):
            ls = wrap(v, 'med', 30, cwid - 30)[:2]
            for k, ln in enumerate(ls): text(L, ln, px + kw + 30 + cwid * j + cwid / 2, y + k * 36 + (18 if len(ls) == 1 else 0), 30, WHITE, 'med', a, 'c')

def d_quiz(L, sc, lt):
    sp, va, vd = sc['spec'], sc['va'], sc['vd']; opts = sp['options']; ans = sp.get('answer')
    a0 = win(lt, 0); label(L, sp.get('label', 'QUICK QUIZ'), 160, 150, a0, 30)
    for j, ln in enumerate(wrap(sp['question'], 'bold', 56, 1600)[:2]): text(L, ln, 160, 196 + j * 70, 56, WHITE, 'bold', a0)
    rv = va + vd * sp.get('reveal', .82); revealed = ans is not None and lt >= rv
    ts = reveal_times(len(opts), va, vd, .25, .55)
    for i, o in enumerate(opts):
        a = win(lt, ts[i]); x = 160 + (i % 2) * 820; y = 380 + (i // 2) * 170
        c = None
        if revealed: c = TH['ok'] if i == ans else DIM
        put(L, panel_sprite(780, 140, c, 230), x, y + (1 - a) * 20, a * (0.6 if revealed and i != ans else 1))
        text(L, 'ABCD'[i], x + 40, y + 40, 46, c or TH['warm'], 'bold', a)
        for k, ln in enumerate(wrap(o, 'med', 34, 640)[:2]): text(L, ln, x + 110, y + 30 + k * 44 + (20 if len(wrap(o, 'med', 34, 640)) == 1 else 0), 34, WHITE, 'med', a)
    if ans is None:
        text(L, sp.get('footer', 'Answer in the comments · reveal in the next episode'), 160, 740, 32, 'accent', 'med', win(lt, va + vd * .7))

def d_qa(L, sc, lt):
    sp, va, vd = sc['spec'], sc['va'], sc['vd']; a0 = win(lt, 0)
    q = wrap(sp['question'], 'bold', 46, 1380)[:3]; pts = sp.get('points', [])
    ph = 140 + 58 * len(q) + 64 * len(pts) + 30
    put(L, panel_sprite(1600, ph), 160, 160, a0); label(L, sp.get('label', 'INTERVIEW CORNER'), 200, 186, a0)
    put(L, panel_sprite(70, 70, TH['warm']), 200, 236, a0); text(L, 'Q', 235, 244, 44, 'warm', 'bold', a0, 'c')
    for j, ln in enumerate(q): text(L, ln, 300, 240 + j * 58, 46, WHITE, 'bold', a0)
    ts = reveal_times(len(pts), va, vd, .3, .85); y = 260 + 58 * len(q) + 20
    for i, p in enumerate(pts):
        a = win(lt, ts[i]); check(L, 300, y + 6, 32, TH['ok'], a); text(L, p, 350, y, 36, WHITE, 'med', a); y += 64

def d_statement(L, sc, lt):
    sp, va, vd = sc['spec'], sc['va'], sc['vd']
    if sp.get('kicker'): label(L, sp['kicker'], 120, 300, win(lt, .1), 30)
    lines = wrap(sp['text'], 'bold', 80, 980)[:4]
    for i, ln in enumerate(lines):
        a = win(lt, .3 + i * .2); text(L, ln, 120, 350 + i * 96 + (1 - a) * 30, 80, WHITE if i < len(lines) - 1 or len(lines) == 1 else 'accent', 'bold', a)
    if sp.get('sub'): text(L, sp['sub'], 124, 370 + len(lines) * 96, 36, (203, 213, 225), 'med', win(lt, va + vd * .5))

def d_outro(L, sc, lt):
    sp, va, vd = sc['spec'], sc['va'], sc['vd']
    label(L, sp.get('kicker', 'NEXT EPISODE'), 120, 290, win(lt, .1), 32)
    nx = sp['next'] if isinstance(sp['next'], list) else wrap(sp['next'], 'bold', 76, 900)
    for i, ln in enumerate(nx[:3]): text(L, ln, 120, 340 + i * 95, 76, WHITE if i < len(nx) - 1 else 'accent', 'bold', win(lt, .3 + i * .2))
    y = 360 + len(nx[:3]) * 95 + 30; b = win(lt, va + vd * .45); pulse = 1 + 0.04 * math.sin(lt * 4) * b
    pill = Image.new('RGBA', (340, 90), (0, 0, 0, 0)); ImageDraw.Draw(pill).rounded_rectangle([0, 0, 339, 89], 45, fill=(239, 68, 68, 255))
    pill = pill.resize((int(340 * pulse), int(90 * pulse)), Image.BILINEAR); put(L, pill, 120, y, b)
    text(L, 'SUBSCRIBE', 120 + pill.width / 2, y + pill.height / 2 - 24, 38, (255, 255, 255), 'bold', b, 'c')
    if sp.get('cta'): text(L, sp['cta'], 124, y + 120, 36, (203, 213, 225), 'med', win(lt, va + vd * .6))

DRAW = dict(hook=d_hook, title=d_title, timeline=d_timeline, bars=d_bars, chips=d_chips, pipeline=d_pipeline,
            swap=lambda L, sc, lt: d_swap(L, sc, lt), bullets=d_bullets, terminal=d_terminal, compare=d_compare,
            quiz=d_quiz, qa=d_qa, statement=d_statement, outro=d_outro)
CONTINUES = {'timeline', 'pipeline'}

def header(L, t):
    text(L, '>_ Tech-dev', 60, 34, 30, WHITE, 'bold')
    text(L, SERIES[EP['series']]['show'], 262, 41, 24, MUTED, 'med')
    b = EP['badge']; bw = int(font('bold', 26).getlength(b)) + 40
    put(L, panel_sprite(bw, 52, TH['warm']), W - 60 - bw, 28); text(L, b, W - 60 - bw / 2, 38, 26, 'warm', 'bold', 1, 'c')
    L.alpha_composite(rect(W, 6, (30, 41, 59, 200)), (0, H - 6))
    L.alpha_composite(rect(W * t / TOTAL, 6, TH['accent'] + (255,)), (0, H - 6))

def caption(L, sc, lt):
    for (c0, c1, s) in sc['caps']:
        if c0 - 0.05 <= lt < c1 + 0.1:
            a = win(lt, c0 - 0.05, .15); f = font('bold', 44)
            words = s.split(); lines, cur = [], []
            for w in words:
                if f.getlength(strip_marks(' '.join(cur + [w]))) > 1500 and cur: lines.append(cur); cur = [w]
                else: cur.append(w)
            lines.append(cur); lh = 62; bh = 30 + lh * len(lines)
            maxw = max(f.getlength(strip_marks(' '.join(l))) for l in lines)
            bx, by = (W - maxw) / 2 - 36, H - 70 - bh
            box = Image.new('RGBA', (int(maxw + 72), bh), (0, 0, 0, 0))
            ImageDraw.Draw(box).rounded_rectangle([0, 0, box.width - 1, bh - 1], 18, fill=(4, 8, 20, 190)); put(L, box, bx, by, a)
            hl = set(w.lower().strip('.,!?:;') for w in sc['spec'].get('hl', []))
            for li, line in enumerate(lines):
                x = (W - f.getlength(strip_marks(' '.join(line)))) / 2; y = by + 12 + li * lh
                for w in line:
                    lit = w.startswith('*') or w.rstrip('.,!?:;').endswith('*') or w.lower().strip('.,!?:;*') in hl
                    ww = strip_marks(w); text(L, ww, x - 4, y, 44, 'warm' if lit else WHITE, 'bold', a); x += f.getlength(ww + ' ')
            return

def frame_at(t):
    i = next((j for j, s in enumerate(SCENES) if s['t0'] <= t < s['t1']), len(SCENES) - 1)
    sc = SCENES[i]; lt = t - sc['t0']; p = lt / (sc['t1'] - sc['t0'])
    img = bg_frame(sc, p).convert('RGBA')
    if sc['xfade'] and lt < 0.6:
        ps = SCENES[i - 1]; img = Image.blend(bg_frame(ps, 1.0).convert('RGBA'), img, ease_io(lt / 0.6))
    img.alpha_composite(vignette(sc['spec'].get('vig', VIG_DEFAULT.get(sc['kind'], 'left')), TH.get('vig_k', 1.0)))
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); DRAW[sc['kind']](L, sc, lt)
    nxt = SCENES[i + 1] if i + 1 < len(SCENES) else None
    keep = nxt is not None and sc['kind'] in CONTINUES and nxt['kind'] == sc['kind'] and nxt['spec'].get('label') == sc['spec'].get('label')
    fo = 1.0 if (keep or nxt is None) else 1 - win(t, sc['t1'] - 0.3, 0.3)
    if fo < 0.999:
        arr = np.asarray(L, dtype=np.float32); arr[..., 3] *= fo; L = Image.fromarray(arr.astype(np.uint8), 'RGBA')
    img.alpha_composite(L)
    H2 = Image.new('RGBA', (W, H), (0, 0, 0, 0)); header(H2, t); caption(H2, sc, lt); img.alpha_composite(H2)
    return img.convert('RGB')

def render_chunk(args):
    f0, f1, path = args
    tmp = path + '.tmp.mp4'
    p = subprocess.Popen(['ffmpeg', '-loglevel', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                          '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20',
                          '-pix_fmt', 'yuv420p', '-threads', '1', tmp], stdin=subprocess.PIPE)
    for f in range(f0, f1): p.stdin.write(frame_at(f / FPS).tobytes())
    p.stdin.close(); assert p.wait() == 0
    os.replace(tmp, path); return path

# ------------------------------------------------------------------ audio
SR = 48000
def load_mono(path, sr_out=SR):
    if path.endswith('.mp3'):
        r = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', path, '-f', 'f32le', '-ac', '1', '-ar', str(sr_out), '-'],
                           capture_output=True, check=True)
        return np.frombuffer(r.stdout, np.float32).copy()
    a, sr = sf.read(path, always_2d=True, dtype='float32'); a = a.mean(1)
    if sr != sr_out: a = np.interp(np.linspace(0, len(a) - 1, int(len(a) * sr_out / sr)), np.arange(len(a)), a).astype(np.float32)
    return a

def resample(a, sr_in):
    return np.interp(np.linspace(0, len(a) - 1, int(len(a) * SR / sr_in)), np.arange(len(a)), a).astype(np.float32)

def whoosh(d=0.7, seed=1):
    rng = np.random.default_rng(seed); n = int(SR * d); x = rng.standard_normal(n).astype(np.float32)
    t = np.linspace(0, 1, n); cut = 0.02 + 0.25 * np.sin(np.pi * t) ** 2; out = np.zeros(n, np.float32); y = 0.0
    for i in range(n): y += cut[i] * (x[i] - y); out[i] = y
    return out * np.sin(np.pi * t) ** 2 * 0.5

def blip(f=880, d=0.12):
    t = np.arange(int(SR * d)) / SR; return (np.sin(2 * np.pi * f * t) * np.exp(-t * 30) * 0.16).astype(np.float32)

def clicks(d, seed=3):
    rng = np.random.default_rng(seed); n = int(SR * d); out = np.zeros(n, np.float32); t = 0.0
    while t < d - .03:
        s = int(t * SR); k = rng.standard_normal(int(.012 * SR)).astype(np.float32) * np.exp(-np.arange(int(.012 * SR)) / 90)
        out[s:s + len(k)] += k * 0.05; t += rng.uniform(.06, .12)
    return out

def music_bed(n):
    tracks = [load_mono(os.path.join(HERE, 'assets', 'music', m)) for m in EP.get('music', TH['music'])]
    xf = int(2.5 * SR); bed = np.zeros(0, np.float32); k = 0
    while len(bed) < n:
        tr = tracks[k % len(tracks)]; k += 1
        if len(bed) == 0: bed = tr.copy(); continue
        ramp = np.linspace(0, 1, xf, dtype=np.float32)
        bed[-xf:] = bed[-xf:] * (1 - ramp) + tr[:xf] * ramp; bed = np.concatenate([bed, tr[xf:]])
    return bed[:n]

def make_audio(path):
    n = int(TOTAL * SR) + SR
    voice = np.zeros(n, np.float32); sfx = np.zeros(n, np.float32); mask = np.zeros(n, np.float32)
    def add(buf, at, a, g=1.0):
        s = int(at * SR); e = min(n, s + len(a)); buf[s:e] += a[:e - s] * g
    for i, sc in enumerate(SCENES):
        for at, a in sc['clips']:
            a48 = resample(a, tts.SR); add(voice, sc['t0'] + sc['va'] + at, a48)
            s = int((sc['t0'] + sc['va'] + at) * SR); mask[s:s + len(a48)] = 1
        if sc['xfade']: add(sfx, max(0, sc['t0'] - .25), whoosh(), .9)
        sp, va, vd = sc['spec'], sc['va'], sc['vd']; base = sc['t0']
        if sc['kind'] == 'timeline': add(sfx, base + va + .2, blip(660 + 90 * sp.get('step', 0)))
        if sc['kind'] == 'bullets':
            ts = [va + vd * f for f in sp['at']] if sp.get('at') else reveal_times(len(sp['items'][:6]), va, vd)
            for j, tt in enumerate(ts): add(sfx, base + tt, blip(740 + 40 * j, .1), .8)
        if sc['kind'] == 'pipeline' and sp.get('mode', 'build') == 'build':
            for j in range(len(sp['nodes'])): add(sfx, base + va + vd * (.3 + .55 * j / max(1, len(sp['nodes']) - .001)), blip(880 * 1.12 ** j))
        if sc['kind'] == 'terminal':
            steps = sp['steps']
            ts = [va + vd * s['at'] for s in steps] if all('at' in s for s in steps) else reveal_times(len(steps), va, vd, .04, .7)
            for s, tt in zip(steps, ts): add(sfx, base + tt, clicks(max(.5, min(1.4, len(s.get('cmd', '')) * .045))))
        if sc['kind'] == 'quiz' and sp.get('answer') is not None: add(sfx, base + va + vd * sp.get('reveal', .82), blip(1046, .25), 1.2)
    m = music_bed(n)
    k = int(0.25 * SR); env = np.convolve(mask, np.ones(k) / k, mode='same')
    gain = 0.40 - 0.25 * np.clip(env * 1.5, 0, 1)
    fade = np.ones(n, np.float32); fl = int(2 * SR); fe = int(TOTAL * SR)
    fade[fe - fl:fe] = np.linspace(1, 0, fl); fade[fe:] = 0; fade[:int(.3 * SR)] = np.linspace(0, 1, int(.3 * SR))
    mix = (voice + m * gain * fade + sfx)[:int(TOTAL * SR)]
    mix = mix / max(1e-6, np.abs(mix).max()) * 0.89
    sf.write(path, np.stack([mix, mix], 1), SR)

# ------------------------------------------------------------------ thumbnail & upload text
CUSTOM_THUMB_DIRS = {'devops': 'devops-series/media/day{n:02d}', 'linux': 'media/ep{n:02d}', 'git': 'media/ep{n:02d}'}


def custom_thumbnail():
    """Shivam's approved photo thumbnail for this episode, if one was committed
    (<media dir>/thumbnail_custom.jpg); it replaces the drawn thumbnail."""
    d = CUSTOM_THUMB_DIRS.get(EP['series'])
    if not d:
        return None
    p = os.path.join(os.path.dirname(HERE), d.format(n=int(EP['number'])), 'thumbnail_custom.jpg')
    return p if os.path.exists(p) else None


def thumbnail(path):
    custom = custom_thumbnail()
    if custom:
        Image.open(custom).convert('RGB').resize((1280, 720), Image.LANCZOS).save(path, quality=93)
        print(f'thumbnail: using {os.path.relpath(custom, os.path.dirname(HERE))}')
        return
    tb = EP['thumb']; tw_, th_ = 1280, 720
    im = Image.open(art_path(tb.get('art', SCENES[0]['art']))).convert('RGB')
    g_ = np.asarray(im.convert('L'), np.float32); half = g_.shape[1] // 2
    if tb.get('flip', g_[:, :half].std() > g_[:, half:].std() * 1.1):   # keep the busy side of the art on the right
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    sc = max(tw_ / im.width, th_ / im.height) * 1.12; im = im.resize((int(im.width * sc), int(im.height * sc)), Image.LANCZOS)
    fx = tb.get('focus', 1.0); x0 = int((im.width - tw_) * fx); y0 = (im.height - th_) // 2
    img = im.crop((x0, y0, x0 + tw_, y0 + th_)).convert('RGBA')
    x = np.linspace(0, 1, tw_)[None, :].repeat(th_, 0)
    a = (np.clip((0.66 - x) / 0.66, 0, 1) ** 1.1 * 225).astype(np.uint8)
    g = Image.new('RGBA', (tw_, th_), (4, 6, 18, 0)); g.putalpha(Image.fromarray(a)); img.alpha_composite(g)
    d = ImageDraw.Draw(img)
    big = tb['big']; fs = 170 if len(big) <= 7 else 130 if len(big) <= 10 else 104
    d.text((54, 150), big, font=font('bold', fs), fill=col(tb.get('color', 'accent')), stroke_width=8, stroke_fill=(5, 8, 20))
    y = 150 + fs + 24
    for j, ln in enumerate(tb.get('lines', [])[:2]):
        d.text((60, y + j * 84), ln, font=font('bold', 70), fill=WHITE if j == 0 else TH['warm'], stroke_width=6, stroke_fill=(5, 8, 20))
    if tb.get('chip'):
        f = font('mono', 40); cw = f.getlength(tb['chip']) + 50; cy = y + 84 * len(tb.get('lines', [])[:2]) + 20
        d.rounded_rectangle([60, cy, 60 + cw, cy + 70], 14, fill=(10, 14, 26, 235), outline=TH['ok'] + (255,), width=3)
        d.text((85, cy + 10), tb['chip'], font=f, fill=TH['ok'])
    f = font('bold', 36); bt = '>_ Tech-dev'; bw = f.getlength(bt) + 44
    d.rounded_rectangle([40, 40, 40 + bw, 104], 14, fill=(10, 14, 26, 235), outline=TH['accent'] + (255,), width=3)
    d.text((62, 47), bt, font=f, fill=WHITE)
    if tb.get('badge'):
        bl = tb['badge'].split(); r = 92; cx, cy = tw_ - 60 - r, 60 + r
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=TH['warm'], outline=(5, 8, 20), width=6)
        for k, part in enumerate(bl[:2]):
            ff = font('bold', 44 if k == 0 else 76); d.text((cx, cy - (34 if len(bl) > 1 else 0) + k * 58), part, font=ff, fill=(15, 15, 25), anchor='mm')
    img.convert('RGB').save(path, quality=92)

def fmt(t): t = int(t); return f'{t // 60}:{t % 60:02d}'

def yt_safe(s):
    """YouTube rejects < and > in titles, descriptions and tags (Shivam's rule, 4 Nov 2026):
    '<file>' placeholders become 'file', any other < or > is dropped."""
    if isinstance(s, list): return [yt_safe(x) for x in s]
    if not isinstance(s, str): return s
    s = re.sub(r'<([^<>\n]{1,40})>', r'\1', s)
    return s.replace('<', '').replace('>', '')

def upload_files(outdir):
    up = EP['upload']; ser = SERIES[EP['series']]
    chapters, seen = [], set()
    for s in SCENES:
        c = s['spec'].get('chapter')
        if c and c not in seen: seen.add(c); chapters.append((s['t0'], c))
    if chapters: chapters[0] = (0, chapters[0][1])
    clean = []
    for t, c in chapters:
        if not clean or t - clean[-1][0] >= 10: clean.append((t, c))
    ch_txt = '\n'.join(f'{fmt(t)} {c}' for t, c in clean)
    cmds = '\n'.join(up.get('commands', []))
    desc = (f"{up['hook']}\n\n"
            "I'm Shivam Singh Verma, a DevOps & SRE engineer with 5 years of experience building CI/CD pipelines, "
            "running cloud infrastructure on AWS & GCP, and managing projects.\n\n"
            + ser['line'].format(n=EP['number']) + "\n\n"
            + (f"⏱️ Chapters\n{ch_txt}\n\n" if ch_txt else "")
            + "🔑 What you'll learn\n" + '\n'.join('• ' + b for b in up['learn']) + "\n\n"
            + (f"🧾 Cheat sheet (copy & practice)\n{cmds}\n\n" if cmds else "")
            + (f"🎤 Interview question: {up['interview']}\n\n" if up.get('interview') else "")
            + (f"🧠 Quiz: {up['quiz']} (answer in the comments, reveal in the next episode)\n\n" if up.get('quiz') else "")
            + (f"📝 Homework: {up['homework']}\n\n" if up.get('homework') else "")
            + (f"➡️ Next: {up['next']}\n\n" if up.get('next') else "")
            + "🔔 Subscribe to Tech-dev for practical DevOps, SRE, Cloud, Linux & Git videos.\n\n"
            + (f"💬 {up['question']}\n\n" if up.get('question') else "")
            + ' '.join(up.get('hashtags', [])))
    up = dict(up, title=yt_safe(up['title']), tags=yt_safe(up['tags'])); desc = yt_safe(desc)
    data = {'title': up['title'], 'description': desc, 'tags': up['tags'], 'duration': round(TOTAL, 1), 'chapters': clean}
    json.dump(data, open(os.path.join(outdir, 'upload.json'), 'w'), indent=2, ensure_ascii=False)
    with open(os.path.join(outdir, 'upload.txt'), 'w') as f:
        f.write(f"TITLE\n{up['title']}\n\nDESCRIPTION\n{desc}\n\nTAGS\n{', '.join(up['tags'])}\n")
    with open(os.path.join(outdir, 'script.txt'), 'w') as f:
        for s in SCENES:
            for c0, c1, txt in s['caps']: f.write(f"[{fmt(s['t0'] + c0)}] {strip_marks(txt)}\n")
    return data

# ------------------------------------------------------------------ main
def load_spec(path):
    s = importlib.util.spec_from_file_location('ep', path); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m.EP

def validate():
    probs = []
    for i, sp in enumerate(EP['scenes']):
        if sp.get('type') not in DRAW: probs.append(f'scene {i}: unknown type {sp.get("type")}')
        if not sp.get('say'): probs.append(f'scene {i}: missing say')
        if sp.get('art') and not os.path.exists(art_path(sp['art'])): probs.append(f'scene {i}: unknown art {sp["art"]}')
    if probs: raise SystemExit('\n'.join(probs))

def main():
    global EP, TH, SCENES, TOTAL, OUT
    EP = load_spec(sys.argv[1]); OUT = sys.argv[2]; os.makedirs(OUT, exist_ok=True)
    TH = LOOKS[EP.get('look', SERIES[EP['series']]['look'])]
    validate()
    SCENES, TOTAL = build()
    print(f'{len(SCENES)} scenes, total {TOTAL:.1f}s ({fmt(TOTAL)})')
    for s in SCENES: print(f"  {fmt(s['t0'])} {s['kind']:9s} {s['t1'] - s['t0']:5.1f}s  {s['art']:14s} {s['spec'].get('chapter', '')}")
    thumbnail(os.path.join(OUT, 'thumbnail.jpg')); upload_files(OUT)
    if '--stills' in sys.argv:
        for t in [float(x) for x in sys.argv[sys.argv.index('--stills') + 1].split(',')]:
            frame_at(t).save(os.path.join(OUT, f'still_{t:06.1f}.jpg'), quality=90)
        return
    make_audio(os.path.join(OUT, 'audio.wav'))
    nf = int(TOTAL * FPS); step = 30 * FPS
    jobs = [(f, min(nf, f + step), os.path.join(OUT, f'chunk_{k:03d}.mp4')) for k, f in enumerate(range(0, nf, step))]
    with mp.get_context('fork').Pool(int(os.environ.get('JOBS', '2'))) as pool:
        for k, pth in enumerate(pool.imap(render_chunk, jobs)): print(f'  chunk {k + 1}/{len(jobs)}', flush=True)
    with open(os.path.join(OUT, 'concat.txt'), 'w') as f:
        for _, _, pth in jobs: f.write(f"file '{os.path.basename(pth)}'\n")
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', os.path.join(OUT, 'concat.txt'),
                    '-c', 'copy', os.path.join(OUT, 'silent.mp4')], check=True)
    tmp = os.path.join(OUT, 'video.tmp.mp4')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', os.path.join(OUT, 'silent.mp4'), '-i', os.path.join(OUT, 'audio.wav'),
                    '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11', '-ar', '48000',
                    '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', tmp], check=True)
    os.replace(tmp, os.path.join(OUT, 'video.mp4'))
    for _, _, pth in jobs: os.remove(pth)
    for x in ('silent.mp4', 'audio.wav', 'concat.txt'): os.remove(os.path.join(OUT, x))
    print('DONE', os.path.join(OUT, 'video.mp4'), fmt(TOTAL))

if __name__ == '__main__':
    main()
