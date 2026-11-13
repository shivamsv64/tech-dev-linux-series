#!/usr/bin/env python3
"""Desk Life Shorts engine: relatable cartoon-skit Shorts for every Tech-dev series (and the funny Shorts channel).

    python3 shorts/skit.py shorts/specs/<id>.py out/short-<id>                 # render short.mp4 + cover + upload files
    python3 shorts/skit.py shorts/specs/<id>.py out/short-<id> --stills 1,5,9  # preview frames only
    python3 shorts/skit.py shorts/specs/<id>.py out/short-<id> --sheet         # contact sheet (1 frame per second)

Look: sketchy hand-drawn line art on muted paper, original human cast with big expressive eyes, a one-line
situation banner on top, music-led with a calm human narrator (free local Kokoro voice, am_michael) and
Shivam's own one-time "subscribe" clip at the end. Zero ElevenLabs credits. Spec format: shorts/SKIT.md.
"""
import importlib.util, json, math, os, re, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, 'v2'))
import toon as T  # noqa: E402

W, H, SS, FPS = T.W, T.H, T.SS, 30
SR = 24000
BOIL_FPS = 10
CTA_CLIP = os.path.join(ROOT, 'voice', 'assets', 'cta.mp3')
CTA_TEXT = 'Watch the full *episode* on Tech-dev, and subscribe!'
VOICE = 'am_michael'
SPEED = 1.05
CAP_Y = 1350          # caption centre (kept above YouTube's bottom title/buttons)
SAFE_X = (60, 960)    # keep text left of YouTube's right-side buttons


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def back(x):
    x = clamp(x)
    c = 1.9
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


# ------------------------------------------------------------------ narration
def tts_clip(text, cache):
    if not text:
        return None
    import tts
    text = re.sub(r'(^|\s)--(\w)', r'\1dash dash \2', text.replace('*', ''))
    text = re.sub(r'(^|\s)-(\w)\b', r'\1dash \2', text)
    parts = [tts.synth_sentence(s, VOICE, SPEED, cache) for s in tts.sentences(text)]
    gap = np.zeros(int(0.1 * tts.SR), np.float32)
    return np.concatenate([np.concatenate([p, gap]) for p in parts])[:-len(gap)]


def load_mp3(path):
    raw = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', path, '-f', 'f32le', '-ac', '1', '-ar', str(SR), '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def chunks(text, maxw=4, maxc=24):
    words = text.split()
    out, cur = [], []
    for w in words:
        if cur and (len(cur) >= maxw or len(' '.join(cur + [w]).replace('*', '')) > maxc):
            out.append(cur); cur = []
        cur.append(w)
        if w.rstrip('*').endswith(('.', '!', '?', ',')):
            out.append(cur); cur = []
    if cur:
        out.append(cur)
    return out


# ------------------------------------------------------------------ timeline
def build(spec, cache):
    scenes = [dict(s) for s in spec['scenes']]
    cta = dict(spec.get('cta', {}))
    cta.setdefault('shot', 'cta')
    cta.setdefault('banner', 'Full episode on Tech-dev')
    scenes.append(cta)
    t = 0.0
    banner = spec.get('banner', '')
    for i, s in enumerate(scenes):
        s['i'] = i
        if s.get('banner'):
            banner = s['banner']
        s['banner_now'] = banner
        if s['shot'] == 'cta':
            s['clip'] = load_mp3(CTA_CLIP) if os.path.exists(CTA_CLIP) else tts_clip(CTA_TEXT, cache)
            s['say'] = CTA_TEXT
        elif s.get('mp3') and os.path.exists(os.path.join(ROOT, s['mp3'])):
            s['clip'] = load_mp3(os.path.join(ROOT, s['mp3']))   # Shivam's own-voice hook (ElevenLabs), repo-relative path
        else:
            s['clip'] = tts_clip(s.get('say', ''), cache)
        speech = len(s['clip']) / SR if s['clip'] is not None else 0
        lead = 0.12 if i == 0 else 0.22
        need = speech + lead + 0.45
        if s['shot'] == 'screen':
            n_out = len(s.get('out', []))
            need = max(need, 0.5 + len(s.get('cmd', '')) / 16 + 0.35 + 0.22 * n_out + 1.1 + (0.8 if s.get('badge') else 0))
        if s['shot'] == 'cta':
            need = speech + 1.0
        s['dur'] = max(1.5, need + s.get('extra', 0))
        s['t0'] = t
        s['vo_t'] = t + lead
        s['speech'] = speech
        # caption chunks with times
        caps = []
        if s.get('say'):
            ch = chunks(s['say'])
            total_c = sum(len(' '.join(c)) for c in ch) or 1
            acc = 0
            for c in ch:
                caps.append((s['vo_t'] + speech * acc / total_c, c))
                acc += len(' '.join(c))
        s['caps'] = caps
        t += s['dur']
    return scenes, t


def scene_at(scenes, t):
    for s in scenes:
        if s['t0'] <= t < s['t0'] + s['dur']:
            return s
    return scenes[-1]


# ------------------------------------------------------------------ world (2x, boiled)
SEATED = {1: [(540, 0)], 2: [(380, 0), (780, 1)]}


def draw_world(spec, s, boil):
    acc, _ = T.ACCENT[spec.get('series', 'linux')]
    img = Image.new('RGB', (W * SS, H * SS), T.PAPER)
    rng = np.random.default_rng(1000 * s['i'] + boil)
    ink = T.Ink(img, rng)
    shot = s['shot']
    setn = s.get('set', 'desk_night')
    night = setn.endswith('night')
    focus = (540, 900)
    if shot in ('wide', 'cta'):
        if shot == 'cta':
            setn = s.get('set', 'office')
            night = setn.endswith('night')
        T.set_bg(ink, img, setn, acc, boil, lamp=len(s.get('cast') or [1]) == 1)
        cast = s.get('cast') or ([{'who': 'rohan', 'mood': 'happy', 'pose': 'cheer'},
                                  {'who': 'meera', 'mood': 'happy', 'pose': 'wave'}] if shot == 'cta' else
                                 [{'who': 'rohan'}])
        desk_set = setn.startswith('desk')
        bed = setn == 'bed_night'
        if bed:
            ink.rrect(170, 620, 910, 1300, 60, fill=T.mix(T.WOOD_D, T.NAVY, 0.4), w=7)
        n = len(cast)
        heads = []
        for k, c in enumerate(cast):
            stand = c.get('stand', not (desk_set or bed))
            if desk_set and not stand:
                R = 165 if n == 1 else 140
                hx = c.get('x', 540 if n == 1 else [360, 760][k % 2])
                hy = 770 if n == 1 else 800
            elif bed:
                R, hx, hy = 160, c.get('x', 540), 840
            else:
                R = 125 if n > 1 else 140
                floor = 1240 if desk_set else 1300
                hx = c.get('x', {1: [540], 2: [330, 760], 3: [230, 540, 850]}[min(n, 3)][k % 3])
                hy = floor - 4.02 * R
            if 'lines' in (c.get('fx') or []):
                T.fx(ink, ['lines'], hx, hy, R, boil, acc)
            T.person(ink, c['who'], hx, hy, R, c.get('mood', 'calm'), c.get('pose', 'type' if desk_set else 'rest'),
                     boil, acc, stand=stand, look=tuple(c.get('look', (0, 0))))
            heads.append((hx, hy, R, c))
        if desk_set:
            T.desk(ink, 1180, night, acc, boil, laptop=s.get('laptop', True), mug_at=s.get('mug', True),
                   laptop_x=s.get('laptop_x', heads[0][0] if n == 1 else 560))
        if bed:
            ink.poly(T.curve([(120, 1230), (380, 1180), (700, 1215), (960, 1180), (990, 1500), (90, 1500)], 6),
                     fill=(150, 120, 170), w=7)
            ink.hatch(130, 1260, 980, 1490, gap=80, col=(120, 96, 140))
        for hx, hy, R, c in heads:
            if night and (desk_set or c.get('pose') == 'phone'):
                T.screen_glow(img, hx, hy, R)
            T.fx(ink, [f for f in (c.get('fx') or []) if f != 'lines'], hx, hy, R, boil, acc)
        if heads:
            focus = (heads[0][0] if n == 1 else 540, heads[0][1] + 150)
    elif shot == 'face':
        T.set_bg(ink, img, 'plain_night' if night else 'plain', acc, boil)
        ink.hatch(0, 0, W, H, gap=90, col=T.mix(T.PAPER_NIGHT if night else T.PAPER, T.INK, 0.12))
        R, hx, hy = 290, 540, 830
        if 'lines' in (s.get('fx') or []):
            T.fx(ink, ['lines'], hx, hy, R, boil, acc)
        T.person(ink, s.get('who', 'rohan'), hx, hy, R, s.get('mood', 'shock'), s.get('pose', 'rest'), boil, acc,
                 look=tuple(s.get('look', (0, 0))))
        if night:
            T.screen_glow(img, hx, hy, R)
        T.fx(ink, [f for f in (s.get('fx') or []) if f != 'lines'], hx, hy, R, boil, acc)
        focus = (hx, hy + 60)
    elif shot == 'eye':
        T.giant_eye(ink, s.get('who', 'rohan'), s.get('mood', 'tired'), boil, acc)
        focus = (560, 930)
    elif shot == 'screen':
        T.monitor(ink, night)
    elif shot == 'phone':
        c = T.CAST[s.get('who', 'rohan')]
        T.phone_insert(ink, c['skin'], c['top'] or acc)
    elif shot == 'card':
        T.set_bg(ink, img, 'plain_night' if night else 'plain', acc, boil)
        ink.hatch(0, 0, W, H, gap=90, col=T.mix(T.PAPER_NIGHT if night else T.PAPER, T.INK, 0.12))
        T.sticky(img, s.get('big', ''), s.get('sub', ''), acc, boil, rng)
        focus = (540, 880)
    world = img.resize((W, H), Image.LANCZOS)
    return world, focus


# ------------------------------------------------------------------ overlays (1x, every frame)
def text_stroke(d, xy, txt, f, fill, stroke=7, sfill=T.INK):
    d.text(xy, txt, font=f, fill=fill, stroke_width=stroke, stroke_fill=sfill)


def draw_banner(img, d, text, age, series, tag):
    if not text:
        return
    acc_b = T.ACCENT[series][1]
    f = T.font('kalam', 62)
    lines = T.wrap(d, text, f, 860)
    if len(lines) > 2:
        f = T.font('kalam', 52); lines = T.wrap(d, text, f, 880)[:3]
    lh = int(f.size * 1.18)
    bw = max(d.textlength(l, font=f) for l in lines) + 70
    bh = lh * len(lines) + 40
    k = back(age / 0.35)
    x0 = (W - bw) / 2
    y0 = 150 - (1 - k) * 260
    d.rounded_rectangle([x0 + 8, y0 + 10, x0 + bw + 8, y0 + bh + 10], 26, fill=(0, 0, 0, 70))
    d.rounded_rectangle([x0, y0, x0 + bw, y0 + bh], 26, fill=(252, 252, 246), outline=T.INK, width=5)
    for i, l in enumerate(lines):
        lw = d.textlength(l, font=f)
        d.text(((W - lw) / 2, y0 + 16 + i * lh), l, font=f, fill=T.INK)
    if tag:
        ft = T.font('pop', 30)
        tw = d.textlength(tag, font=ft)
        d.rounded_rectangle([x0 + 18, y0 + bh - 8, x0 + 18 + tw + 34, y0 + bh + 40], 20, fill=acc_b, outline=T.INK, width=4)
        d.text((x0 + 35, y0 + bh - 4), tag, font=ft, fill=T.INK)


def draw_caption(img, d, s, t, series):
    caps = s['caps']
    cur = None
    for ct, c in caps:
        if t >= ct:
            cur = (ct, c)
    if not cur:
        return
    ct, words = cur
    age = t - ct
    acc_b = T.ACCENT[series][1]
    size = 76
    f = T.font('luck', size)
    full = ' '.join(w.replace('*', '') for w in words)
    while d.textlength(full, font=f) > SAFE_X[1] - SAFE_X[0] - 20 and size > 50:
        size -= 4; f = T.font('luck', size)
    k = back(age / 0.18)
    sc = 0.75 + 0.25 * k
    fs = T.font('luck', max(20, int(size * sc)))
    total = d.textlength(full, font=fs)
    x = (SAFE_X[0] + SAFE_X[1]) / 2 - total / 2
    y = CAP_Y - fs.size / 2
    for w in words:
        hi = w.startswith('*') or w.rstrip('.,!?').endswith('*')
        clean = w.replace('*', '')
        text_stroke(d, (x, y), clean, fs, acc_b if hi else (255, 255, 255), max(5, int(8 * sc)))
        x += d.textlength(clean + ' ', font=fs)


def draw_terminal(img, d, s, age, series):
    acc_b = T.ACCENT[series][1]
    x0, y0, x1, y1 = 110, 470, 980, 1150
    prompt = s.get('prompt', 'shivam@tech-dev:~$')
    cmd = s.get('cmd', '')
    out = s.get('out', [])
    lines_all = [prompt + ' ' + cmd] + [l.lstrip('!') for l in out]
    size = 54
    f = T.font('mono', size)
    while max(d.textlength(l, font=f) for l in lines_all) > x1 - x0 - 30 and size > 26:
        size -= 2; f = T.font('mono', size)
    fr = T.font('mono_r', size)
    lh = int(size * 1.45)
    block = lh * (len(out) + 1.3)
    two_line = d.textlength(prompt + ' ' + cmd, font=f) > x1 - x0 - 30
    y0 = int((470 + 1150) / 2 - block / 2 - 40)
    d.text((x0 + 14, y0), prompt, font=f, fill=(110, 220, 130))
    px = x0 + 14 + d.textlength(prompt + ' ', font=f)
    nch = int(clamp((age - 0.45) * 16, 0, len(cmd)))
    d.text((px, y0), cmd[:nch], font=f, fill=(240, 240, 240))
    typed_end = 0.45 + len(cmd) / 16
    if nch < len(cmd) or int(age * 2.5) % 2 == 0:
        cx = px + d.textlength(cmd[:nch], font=f)
        d.rectangle([cx + 2, y0 + 4, cx + size * 0.55, y0 + size + 4], fill=(240, 240, 240))
    hl = s.get('hl', '')
    x0 = x0 + 4
    for i, line in enumerate(out):
        ta = typed_end + 0.35 + i * 0.22
        if age < ta:
            break
        err = s.get('error') or line.startswith('!')
        txt = line[1:] if line.startswith('!') else line
        col = (255, 110, 100) if err else (214, 220, 226)
        yy = y0 + lh * (i + 1.3)
        if hl and hl in txt and not err:
            a, b = txt.split(hl, 1)
            d.text((x0 + 10, yy), a, font=fr, fill=col)
            xa = x0 + 10 + d.textlength(a, font=fr)
            wv = d.textlength(hl, font=f)
            d.rectangle([xa - 4, yy - 2, xa + wv + 4, yy + size + 8], fill=(60, 66, 40) if series == 'git' else (30, 70, 50))
            d.text((xa, yy), hl, font=f, fill=acc_b)
            d.text((xa + wv, yy), b, font=fr, fill=col)
        else:
            d.text((x0 + 10, yy), txt, font=f if err else fr, fill=col)
    if s.get('badge'):
        ba = typed_end + 0.35 + len(out) * 0.22 + 0.5
        if age > ba:
            k = back((age - ba) / 0.3)
            fb = T.font('luck', int(64 * (0.6 + 0.4 * k)))
            txt = s['badge']
            tw = d.textlength(txt, font=fb)
            bx, by = W - 70 - tw - 60, 1110
            lay = Image.new('RGBA', (int(tw + 80), int(fb.size + 60)), (0, 0, 0, 0))
            ld = ImageDraw.Draw(lay)
            ld.rounded_rectangle([4, 4, tw + 74, fb.size + 52], 24, fill=acc_b, outline=T.INK, width=6)
            ld.text((38, 22), txt, font=fb, fill=T.INK)
            lay = lay.rotate(4, expand=True, resample=Image.BICUBIC)
            img.paste(lay, (int(bx), int(by)), lay)


def draw_phone(img, d, s, age):
    x0, y0, x1, y1 = 320, 420, 760, 1280
    ft = T.font('pop', 120)
    tm = s.get('time', '3:07')
    tw = d.textlength(tm, font=ft)
    d.text(((x0 + x1) / 2 - tw / 2, y0 + 30), tm, font=ft, fill=(236, 240, 250))
    fdd = T.font('pop', 30)
    dt = s.get('date', 'Tuesday')
    d.text(((x0 + x1) / 2 - d.textlength(dt, font=fdd) / 2, y0 + 175), dt, font=fdd, fill=(170, 180, 200))
    al = s.get('alert', {})
    k = back((age - 0.35) / 0.3)
    if age > 0.35:
        cy = y0 + 280 + (1 - k) * 60
        lines = al.get('lines', [])
        ftt = T.font('pop', 34); fl = T.font('mono_r', 27)
        ch = 92 + 38 * len(lines)
        d.rounded_rectangle([x0 + 10, cy, x1 - 10, cy + ch], 26, fill=(246, 246, 250))
        d.ellipse([x0 + 30, cy + 26, x0 + 60, cy + 56], fill=(226, 60, 56))
        d.text((x0 + 75, cy + 18), al.get('title', 'ALERT'), font=ftt, fill=(30, 30, 36))
        for i, ln in enumerate(lines):
            d.text((x0 + 32, cy + 74 + i * 38), ln, font=fl, fill=(70, 70, 80))
        for j, extra in enumerate(al.get('more', [])):
            yy = cy + ch + 18 + j * 86
            if age > 0.9 + j * 0.25:
                d.rounded_rectangle([x0 + 10, yy, x1 - 10, yy + 72], 22, fill=(232, 232, 238))
                d.ellipse([x0 + 30, yy + 22, x0 + 56, yy + 48], fill=(226, 60, 56))
                d.text((x0 + 72, yy + 16), extra, font=T.font('pop', 30), fill=(40, 40, 46))



# ------------------------------------------------------------------ v3 zine shots (hook card + stat card), full-frame 9:16
ZINE = ('hookcard', 'statcard')
_FD = os.path.join(ROOT, 'v2', 'assets', 'fonts')
_PAL = {'accent': (56, 189, 248), 'warm': (251, 191, 36), 'purple': (167, 139, 250), 'ok': (52, 211, 153), 'red': (239, 68, 68), 'white': (255, 255, 255)}


def zfont(name, size):
    from PIL import ImageFont
    f = {'anton': 'Anton-Regular.ttf', 'bebas': 'BebasNeue-Regular.ttf', 'marker': 'PermanentMarker-Regular.ttf'}[name]
    return ImageFont.truetype(os.path.join(_FD, f), size)


def _pop(age, t0, d=0.32):
    x = (age - t0) / d
    if x <= 0:
        return 0.0
    if x >= 1.6:
        return 1.0
    return 1 - math.exp(-4.2 * x) * math.cos(5.5 * x)


def _count(val, k):
    m = re.match(r'^([^0-9]*)([0-9][0-9,]*\.?[0-9]*)(.*)$', val)
    if not m:
        return val
    pre, num, suf = m.groups(); dec = len(num.split('.')[1]) if '.' in num else 0
    x = float(num.replace(',', '')) * k
    return pre + (f'{x:,.{dec}f}' if ',' in num else f'{x:.{dec}f}') + suf


def draw_zine(spec, s, age):
    """hookcard: giant stacked condensed words on navy/paper (newsroom/poster look); statcard: big number on a blue-violet gradient.
    Spec fields: hookcard {lines:[str|(str,color)] x1-3 (<=9 chars), bg:'navy'|'paper', small:[<=3], stamp}; statcard {kicker, big, label, sub, color}."""
    from PIL import ImageFont
    if s['shot'] == 'hookcard':
        paper = s.get('bg', 'navy') == 'paper'
        bg = (236, 227, 207) if paper else (10, 15, 31)
        img = Image.new('RGB', (W, H), bg); d = ImageDraw.Draw(img, 'RGBA')
        rng = np.random.default_rng(3); n = rng.normal(0, 5, (H, W, 1)).astype(np.float32)
        img = Image.fromarray(np.clip(np.asarray(img, np.float32) + n, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(img, 'RGBA')
        for i, c in enumerate([_PAL['accent'], _PAL['warm'], _PAL['purple']]):
            hh = int(70 * ease((age - i * 0.07) / 0.4)); d.rectangle([80 + i * 140, 0, 80 + i * 140 + 110, hh], fill=c + (235,))
        lines = s['lines']; ink = (22, 19, 15) if paper else (255, 255, 255)
        size = 300 if len(lines) <= 2 else 250
        for i, ln in enumerate(lines):
            txt, c = (ln, None) if isinstance(ln, str) else (ln[0], ln[1])
            size_i = size
            f = zfont('anton', size_i)
            while d.textlength(txt, font=f) > 900 and size_i > 90:
                size_i -= 10; f = zfont('anton', size_i)
            p = _pop(age, 0.12 + i * 0.32)
            if p <= 0:
                continue
            y = 330 + i * (size * 0.95) + (1 - min(1, p)) * 60
            col_ = _PAL.get(c, ink) if c else ink
            d.text((90, y), txt, font=f, fill=col_ + (int(255 * min(1, p * 1.6)),))
        if s.get('small'):
            a = ease((age - 0.12 - len(lines) * 0.32) / 0.4); x = 90; fb = zfont('bebas', 62)
            for j, t_ in enumerate(s['small'][:3]):
                d.text((x, 1130), t_, font=fb, fill=[_PAL['accent'], _PAL['warm'], _PAL['purple']][j % 3] + (int(255 * a),)); x += d.textlength(t_, font=fb) + 40
        if s.get('stamp'):
            p = _pop(age, 0.12 + len(lines) * 0.32 + 0.2, 0.25)
            if p > 0:
                f = zfont('marker', 84); tw = d.textlength(s['stamp'], font=f)
                st = Image.new('RGBA', (int(tw + 60), 150), (0, 0, 0, 0)); sd = ImageDraw.Draw(st)
                sd.rounded_rectangle([0, 0, st.width - 1, 149], 12, outline=(215, 38, 61, 255), width=9); sd.text((30, 28), s['stamp'], font=f, fill=(215, 38, 61, 255))
                sz = 2.0 - min(1, p); st = st.resize((int(st.width * sz), int(st.height * sz))).rotate(-8, expand=True)
                img.paste(st, (int(780 - st.width / 2), int(1010 - st.height / 2)), st)
        return img
    # statcard
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]; xx = np.linspace(0, 1, W, dtype=np.float32)[None, :, None]
    a_ = np.array([7, 11, 36], np.float32); b_ = np.array([34, 52, 214], np.float32); c_ = np.array([88, 52, 220], np.float32)
    t_ = np.clip(yy * 0.75 + xx * 0.25, 0, 1); im = a_ * (1 - t_) ** 1.6 + b_ * t_ ** 1.2 * 0.9
    g = np.exp(-(((xx - 0.85) / 0.6) ** 2 + ((yy - 0.9) / 0.25) ** 2)); im = im + c_ * g * 0.5
    img = Image.fromarray(np.clip(im, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(img, 'RGBA')
    tint = _PAL.get(s.get('color', 'accent'), _PAL['accent'])
    cw, ch, x0, y0 = 900, 760, 90, 400
    p = _pop(age, 0.1, 0.45)
    card = Image.new('RGBA', (cw, ch), (0, 0, 0, 0)); cd = ImageDraw.Draw(card)
    cd.rounded_rectangle([0, 0, cw - 1, ch - 1], 40, fill=(246, 248, 255, 255)); cd.rounded_rectangle([50, 60, 150, 70], 5, fill=tint + (255,))
    if s.get('kicker'):
        cd.text((50, 100), '[' + s['kicker'] + ']', font=T.font('pop', 36), fill=(84, 96, 140))
    big = s['big']; size = 260
    while ImageFont.truetype('/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf', size).getlength(big) > cw - 100 and size > 80:
        size -= 8
    fb = ImageFont.truetype('/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf', size)
    cd.text((50, 190), _count(big, ease((age - 0.2) / 1.0)), font=fb, fill=(14, 20, 54))
    cd.text((50, ch - 270), s.get('label', ''), font=T.font('pop', 56), fill=(30, 50, 200))
    for j, ln in enumerate(s.get('sub', '').split('|')[:3]):
        cd.text((50, ch - 190 + j * 52), ln.strip(), font=T.font('pop', 40), fill=(84, 96, 140))
    k = 0.92 + 0.08 * min(1.0, p)
    if p > 0:
        card = card.resize((int(cw * k), int(ch * k)), Image.BILINEAR)
        img.paste(card, (int(x0 + (cw - card.width) / 2), int(y0 + (ch - card.height) / 2 + (1 - min(1, p)) * 50)), card)
    return img


# ------------------------------------------------------------------ frame
GRAIN = None
_CACHE = {}


def frame(spec, scenes, total, t):
    global GRAIN
    if GRAIN is None:
        GRAIN = T.paper_grain()
    s = scene_at(scenes, t)
    age = t - s['t0']
    boil = int(t * BOIL_FPS)
    key = (s['i'], boil)
    if s['shot'] in ZINE:
        _CACHE[key] = (draw_zine(spec, s, age), (540, 900))
    elif key not in _CACHE:
        if len(_CACHE) > 6:
            _CACHE.clear()
        _CACHE[key] = draw_world(spec, s, boil)
    world, focus = _CACHE[key]
    shot = s['shot']
    overlay_locked = shot in ('screen', 'phone') + ZINE
    img = world
    if not overlay_locked:
        cam = s.get('cam', 'push')
        z = 1.0
        if cam == 'push':
            z = 1.0 + 0.06 * ease(age / s['dur'])
        elif cam == 'pull':
            z = 1.08 - 0.07 * ease(age / s['dur'])
        if shot == 'eye':
            z = 1.0 + 0.12 * ease(age / s['dur'])
        z += 0.045 * (1 - ease(age / 0.2))  # punch on the cut
        sx = sy = 0.0
        if cam == 'shake' or s.get('mood') in ('shock', 'panic') or any(
                c.get('mood') in ('shock', 'panic') for c in s.get('cast', [])):
            amp = 16 * max(0.0, 1 - age / 0.6)
            sx, sy = amp * math.sin(age * 71), amp * math.cos(age * 53)
        cw, ch = W / z, H / z
        fx_, fy_ = focus
        cx = clamp(fx_, cw / 2, W - cw / 2) + sx
        cy = clamp(fy_, ch / 2, H - ch / 2) + sy
        img = world.transform((W, H), Image.EXTENT, (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2), Image.BILINEAR)
    else:
        img = world.copy()
        if shot == 'phone' and age < 0.9:
            j = int(10 * math.sin(age * 90) * (1 - age / 0.9))
            img = img.transform((W, H), Image.AFFINE, (1, 0, j, 0, 1, 0), Image.BILINEAR)
    d = ImageDraw.Draw(img, 'RGBA')
    if shot == 'screen':
        draw_terminal(img, d, s, age, spec['series'])
    elif shot == 'phone':
        draw_phone(img, d, s, age)
    # grain + vignette
    arr = (np.asarray(img, np.float32) * GRAIN).astype(np.uint8)
    img = Image.fromarray(arr)
    d = ImageDraw.Draw(img, 'RGBA')
    ban_age = t if s['i'] == 0 or s['banner_now'] != scenes[s['i'] - 1]['banner_now'] else 9
    if s['shot'] == 'cta':
        ban_age = age
    tag = spec.get('tag_label') or (f"{spec['series'].upper()} · {spec['tag']}" if spec.get('tag') else '')
    if s['shot'] not in ZINE:
        draw_banner(img, d, s['banner_now'], ban_age, spec['series'], tag)
    draw_caption(img, d, s, t, spec['series'])
    # fade out at the very end
    if t > total - 0.4:
        a = clamp((t - (total - 0.4)) / 0.4)
        img = Image.blend(img, Image.new('RGB', (W, H), T.PAPER), a * 0.6)
    return img


# ------------------------------------------------------------------ audio
def env(n, a=0.004, dcy=0.2):
    t = np.arange(n) / SR
    return np.clip(t / a, 0, 1) * np.exp(-t / dcy)


def pluck(f, dur, bright=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    out = np.zeros(n)
    for k in range(1, 7):
        out += np.sin(2 * np.pi * f * k * t) * np.exp(-t * (2.2 + 2.6 * k)) * (bright ** (k - 1)) / k
    return out * np.clip(t / 0.003, 0, 1)


NOTE = {'C3': 130.81, 'D3': 146.83, 'E3': 164.81, 'F3': 174.61, 'G3': 196.0, 'A3': 220.0, 'B3': 246.94,
        'C4': 261.63, 'D4': 293.66, 'E4': 329.63, 'F4': 349.23, 'G4': 392.0, 'A4': 440.0, 'B4': 493.88, 'C5': 523.25,
        'E5': 659.25, 'G5': 783.99, 'A2': 110.0, 'F2': 87.31, 'G2': 98.0, 'C2': 65.41, 'E2': 82.41, 'D2': 73.42}


def music_fun(total, seed=7):
    """cheerful plucked tune (only for the funny Shorts channel)"""
    from scipy.signal import butter, lfilter
    rng = np.random.default_rng(seed)
    n = int((total + 2) * SR)
    out = np.zeros(n)
    bpm = 100
    beat = 60 / bpm
    prog = [('C2', ['C4', 'E4', 'G4', 'C5']), ('A2', ['A3', 'C4', 'E4', 'A4']),
            ('F2', ['F3', 'A3', 'C4', 'F4']), ('G2', ['G3', 'B3', 'D4', 'G4'])]
    patt = [0, 2, 1, 3, 2, 1, 3, 2]

    def add(sig, t, g):
        s = int(t * SR)
        if s >= n:
            return
        e = min(n, s + len(sig)); out[s:e] += sig[:e - s] * g

    bar = 0
    t = 0.0
    while t < total + 1:
        root, ch = prog[bar % 4]
        for k in range(8):
            tt = t + k * beat / 2 + rng.uniform(0, 0.008)
            add(pluck(NOTE[ch[patt[k]]], 0.9, 0.55), tt, 0.16 if k % 2 == 0 else 0.11)
        for k in (0, 2):  # bass
            m = int(0.8 * SR); ts = np.arange(m) / SR
            f = NOTE[root]
            add((np.sin(2 * np.pi * f * ts) + 0.35 * np.sin(4 * np.pi * f * ts)) * np.exp(-ts / 0.35) *
                np.clip(ts / 0.01, 0, 1), t + k * beat, 0.32)
        for k in range(8):  # shaker
            m = int(0.06 * SR)
            sh = rng.standard_normal(m) * env(m, 0.004, 0.02)
            add(np.diff(np.concatenate([[0], sh])), t + k * beat / 2 + beat / 4, 0.05)
        for k in (1, 3):  # finger snap
            m = int(0.12 * SR)
            sn = rng.standard_normal(m) * env(m, 0.001, 0.03)
            b, a = butter(2, [1500 / (SR / 2), 5000 / (SR / 2)], 'band')
            add(lfilter(b, a, sn), t + k * beat, 0.35)
        if bar % 2 == 1:  # little bell answer
            add(pluck(NOTE['E5'] if bar % 4 == 1 else NOTE['G5'], 1.2, 0.3), t + 3.5 * beat, 0.06)
        t += 4 * beat; bar += 1
    b, a = butter(2, 5200 / (SR / 2)); out = lfilter(b, a, out)
    return out[:int(total * SR)]


def music_tech(total, seed=7):
    """calm 'coding focus' bed for tech Shorts: soft minor-7th pads, warm sub bass, quiet kick and hat ticks,
    a few soft UI blips. No melody, so it never fights the narrator."""
    from scipy.signal import butter, lfilter
    rng = np.random.default_rng(seed)
    n = int((total + 3) * SR)
    out = np.zeros(n)
    beat = 60 / 88
    bar = 4 * beat
    # Am9, Fmaj7, Cmaj7, Em7 (voiced low and close)
    prog = [(55.00, [220.00, 261.63, 329.63, 392.00, 493.88]),
            (43.65, [174.61, 220.00, 261.63, 329.63, 392.00]),
            (65.41, [196.00, 246.94, 261.63, 329.63, 392.00]),
            (41.20, [164.81, 196.00, 246.94, 293.66, 329.63])]

    def add(sig, t, g):
        st = int(t * SR)
        if st < 0:
            sig = sig[-st:]; st = 0
        if st >= n:
            return
        e = min(n, st + len(sig)); out[st:e] += sig[:e - st] * g

    k = 0
    t = 0.0
    while t < total + 1:
        root, chord = prog[k % 4]
        L = bar + 1.2
        m = int(L * SR); ts = np.arange(m) / SR
        envp = np.clip(ts / 0.9, 0, 1) * np.clip((L - ts) / 1.1, 0, 1)
        pad = np.zeros(m)
        for f in chord:
            for det in (-0.004, 0.0, 0.005):
                ff = f * (1 + det)
                ph = rng.uniform(0, 6.28)
                pad += (np.sin(2 * np.pi * ff * ts + ph) + 0.35 * np.sin(4 * np.pi * ff * ts + ph)
                        + 0.12 * np.sin(6 * np.pi * ff * ts + ph))
        pad *= envp * (0.85 + 0.15 * np.sin(2 * np.pi * 0.25 * ts)) / (len(chord) * 3)
        add(pad, t - 0.3, 0.55)
        sub = np.sin(2 * np.pi * root * 2 * ts) * np.clip(ts / 0.25, 0, 1) * np.clip((bar - ts) / 0.4, 0, 1)
        add(sub, t, 0.22)
        for b in range(4):  # quiet kick on 1 and 3, hat ticks on 8ths
            if b in (0, 2):
                mk = int(0.3 * SR); tk = np.arange(mk) / SR
                add(np.sin(2 * np.pi * (48 + 60 * np.exp(-tk / 0.025)) * tk) * np.exp(-tk / 0.13), t + b * beat, 0.28)
            for h in (0, 1):
                mh = int(0.04 * SR)
                hat = rng.standard_normal(mh) * env(mh, 0.001, 0.008)
                add(np.diff(np.concatenate([[0], hat])), t + b * beat + h * beat / 2, 0.035 if h else 0.02)
        if k % 2 == 1:  # soft UI blips
            for j, f in enumerate((1318.5, 1975.5)):
                mb = int(0.25 * SR); tb = np.arange(mb) / SR
                add(np.sin(2 * np.pi * f * tb) * env(mb, 0.003, 0.07), t + 3 * beat + j * beat / 4, 0.025)
        t += bar; k += 1
    b, a = butter(2, 3800 / (SR / 2)); out = lfilter(b, a, out)
    hb, ha = butter(1, 35 / (SR / 2), 'high'); out = lfilter(hb, ha, out)
    return out[:int(total * SR)]


def music(total, kind='tech'):
    if kind == 'none':
        return np.zeros(int(total * SR))
    return music_fun(total) if kind == 'fun' else music_tech(total)


def sfx(kind, rng):
    from scipy.signal import butter, lfilter
    if kind == 'whoosh':
        m = int(0.35 * SR); t = np.arange(m) / SR
        b, a = butter(2, [500 / (SR / 2), 3500 / (SR / 2)], 'band')
        return lfilter(b, a, rng.standard_normal(m)) * np.sin(np.pi * t / 0.35) ** 2 * 0.2
    if kind == 'pop':
        m = int(0.14 * SR); t = np.arange(m) / SR
        return np.sin(2 * np.pi * (420 + 1100 * t / 0.14) * t) * env(m, 0.002, 0.04) * 0.28
    if kind == 'key':
        m = int(0.03 * SR)
        return rng.standard_normal(m) * env(m, 0.001, 0.006) * 0.1
    if kind == 'boing':
        m = int(0.55 * SR); t = np.arange(m) / SR
        f = 220 + 260 * (1 - np.exp(-t / 0.08)) + 40 * np.sin(2 * np.pi * 14 * t) * np.exp(-t / 0.3)
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(m, 0.003, 0.22) * 0.26
    if kind == 'alarm':
        out = np.zeros(int(1.0 * SR))
        for i in range(3):
            m = int(0.14 * SR); t = np.arange(m) / SR
            tone = np.sin(2 * np.pi * (988 if i % 2 == 0 else 784) * t) * env(m, 0.004, 0.08) * 0.14
            s = int(i * 0.24 * SR); out[s:s + m] += tone
        return out
    if kind == 'buzz':
        m = int(0.3 * SR); t = np.arange(m) / SR
        b, a = butter(2, 1200 / (SR / 2))
        return lfilter(b, a, np.sign(np.sin(2 * np.pi * 110 * t))) * env(m, 0.005, 0.15) * 0.16
    if kind == 'ding':
        m = int(1.0 * SR); t = np.arange(m) / SR
        return (np.sin(2 * np.pi * 1318.5 * t) + 0.5 * np.sin(2 * np.pi * 1975.5 * t)) * env(m, 0.002, 0.35) * 0.13
    if kind == 'slide':  # slide whistle down (fail moment)
        m = int(0.6 * SR); t = np.arange(m) / SR
        f = 1400 - 1000 * t / 0.6
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(m, 0.02, 0.5) * 0.09
    return np.zeros(1)


def make_audio(scenes, total, path, seed=11, music_kind='tech'):
    rng = np.random.default_rng(seed)
    n = int((total + 1) * SR)
    fxb = np.zeros(n); voc = np.zeros(n)

    def add(buf, sig, t, g=1.0):
        if sig is None:
            return
        s = int(t * SR)
        if s >= n:
            return
        e = min(n, s + len(sig)); buf[s:e] += sig[:e - s] * g

    for s in scenes:
        t0 = s['t0']
        if s['i'] > 0:
            add(fxb, sfx('whoosh', rng), max(0, t0 - 0.1))
        else:
            add(fxb, sfx('pop', rng), 0.15)
        add(voc, s['clip'], s['vo_t'], 1.0)
        moods = [s.get('mood')] + [c.get('mood') for c in s.get('cast', [])]
        if any(m in ('shock', 'panic') for m in moods):
            add(fxb, sfx('boing', rng), t0 + 0.05, 0.9)
        if s['shot'] == 'phone':
            add(fxb, sfx('alarm', rng), t0 + 0.05)
        if s['shot'] == 'card':
            add(fxb, sfx('pop', rng), t0 + 0.1)
        if s['shot'] == 'screen':
            cmd = s.get('cmd', '')
            for i in range(len(cmd)):
                add(fxb, sfx('key', rng), t0 + 0.45 + i / 16 + rng.uniform(0, 0.015))
            te = t0 + 0.45 + len(cmd) / 16 + 0.35
            add(fxb, sfx('buzz' if s.get('error') or any(l.startswith('!') for l in s.get('out', [])) else 'pop', rng), te)
            if s.get('badge'):
                add(fxb, sfx('ding', rng), te + len(s.get('out', [])) * 0.22 + 0.5)
        if s['shot'] == 'cta':
            add(fxb, sfx('ding', rng), t0 + 0.2)
        for k in s.get('sfx', []):
            add(fxb, sfx(k, rng), t0 + 0.1)
    from scipy.signal import butter, lfilter
    e = np.abs(voc)
    bb, aa = butter(1, 5 / (SR / 2)); e = lfilter(bb, aa, e)
    duck = 1 - 0.6 * np.clip(e / (e.max() + 1e-9) * 5, 0, 1)
    mus = np.zeros(n); m = music(total, music_kind); mus[:len(m)] = m
    mus = mus / (np.abs(mus).max() + 1e-9) * 0.30
    out = mus * duck + fxb + voc * 1.15
    end = int(total * SR)
    fade = int(1.0 * SR)
    out[end - fade:end] *= np.linspace(1, 0.15, fade)
    out = out[:end]
    out = out / (np.abs(out).max() + 1e-9) * 0.9
    import soundfile as sf
    sf.write(path, out.astype(np.float32), SR)


# ------------------------------------------------------------------ main
def load(path):
    sp = importlib.util.spec_from_file_location('spec', path)
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
    return m.SKIT


def yt_safe(s):
    """YouTube rejects < and > in titles, descriptions and tags (Shivam's rule, 4 Nov 2026):
    '<file>' placeholders become 'file', any other < or > is dropped."""
    if isinstance(s, list): return [yt_safe(x) for x in s]
    if not isinstance(s, str): return s
    s = re.sub(r'<([^<>\n]{1,40})>', r'\1', s)
    return s.replace('<', '').replace('>', '')

def upload_text(spec, total, outdir):
    u = dict(spec['upload'])
    for k in ('title', 'description', 'tags'):
        if k in u: u[k] = yt_safe(u[k])
    u['duration'] = round(total, 1)
    json.dump(u, open(os.path.join(outdir, 'upload.json'), 'w'), indent=2, ensure_ascii=False)
    with open(os.path.join(outdir, 'upload.txt'), 'w') as f:
        f.write(f"TITLE\n{u['title']}\n\nDESCRIPTION\n{u['description']}\n\nTAGS\n{', '.join(u['tags'])}\n")


def main():
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    spec = load(sys.argv[1]); outdir = sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    cache = os.path.join(os.path.expanduser('~/.cache'), 'td-skit-tts')
    global VOICE, SPEED
    if spec.get('voice'):   # e.g. 'chatterbox-shivam': lines pre-filled into <outdir>/vo by voice/prefill_engine_vo.py
        VOICE = spec['voice']; SPEED = spec.get('speed', 1.0); cache = os.path.join(outdir, 'vo')
    scenes, total = build(spec, cache)
    print(f'Short length: {total:.1f}s')
    for s in scenes:
        what = s.get('cmd') or s.get('big') or ', '.join(c['who'] + ':' + c.get('mood', '') for c in s.get('cast', [])) or s.get('mood', '')
        print(f"  {s['t0']:5.1f}s {s['dur']:4.1f}s {s['shot']:6s} {what}  | {s.get('say', '')[:60]}")
    if not 25 <= total <= 58:
        print('WARNING: aim for 30-50 s (hard limit 60 s)')
    if '--stills' in sys.argv:
        ts = [float(x) for x in sys.argv[sys.argv.index('--stills') + 1].split(',')]
        for t in ts:
            frame(spec, scenes, total, t).save(os.path.join(outdir, f'still_{t:05.1f}.jpg'), quality=88)
        print('stills written'); return
    if '--sheet' in sys.argv:
        ts = [i + 0.6 for i in range(int(total))]
        th = [frame(spec, scenes, total, t).resize((270, 480)) for t in ts]
        cols = 8
        rows = math.ceil(len(th) / cols)
        sheet = Image.new('RGB', (cols * 270, rows * 500), (20, 20, 20))
        dd = ImageDraw.Draw(sheet)
        for i, im in enumerate(th):
            x, y = (i % cols) * 270, (i // cols) * 500
            sheet.paste(im, (x, y)); dd.text((x + 6, y + 482), f'{ts[i]:.1f}s', fill=(255, 255, 255))
        sheet.save(os.path.join(outdir, 'sheet.jpg'), quality=85)
        print('sheet written'); return
    wav = os.path.join(outdir, 'audio.wav')
    make_audio(scenes, total, wav, music_kind=spec.get('music', 'fun' if spec.get('series') == 'funny' else 'tech'))
    nfr = int(total * FPS)
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
           '-i', '-', '-i', wav, '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p',
           '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11', '-ar', '48000', '-c:a', 'aac', '-b:a', '160k', '-shortest', '-movflags', '+faststart', os.path.join(outdir, 'short.mp4')]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(nfr):
        p.stdin.write(frame(spec, scenes, total, i / FPS).tobytes())
        if i % 150 == 0:
            print(f'  frame {i}/{nfr}', flush=True)
    p.stdin.close(); p.wait()
    frame(spec, scenes, total, spec.get('cover_at', 1.0)).save(os.path.join(outdir, 'cover.jpg'), quality=90)
    upload_text(spec, total, outdir)
    os.remove(wav)
    print('done:', os.path.join(outdir, 'short.mp4'))


if __name__ == '__main__':
    main()
