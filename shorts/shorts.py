#!/usr/bin/env python3
"""Tech-dev YouTube Shorts engine (vertical 1080x1920, 30-50 s, animal & bird cast).

One Short per long episode: a hook, 3-6 quick beats (each spoken by an animal or bird in
its own voice, optionally with a real terminal command), then a call to watch the full episode.

usage:
  python3 shorts/shorts.py shorts/specs/linux-ep01.py out/short-linux-ep01            # render
  python3 shorts/shorts.py shorts/specs/linux-ep01.py out/short-linux-ep01 --stills 2,9,20
Outputs: short.mp4, cover.jpg, upload.json, upload.txt
See shorts/README.md for the spec format.
"""
import sys, os, math, json, random, subprocess, importlib.util, wave
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cast

W, H, FPS, SR = 1080, 1920, 30, 44100
BG = (10, 15, 31)
CYAN = (56, 189, 248); AMBER = (251, 191, 36); VIOLET = (167, 139, 250)
GREEN = (52, 211, 153); RED = (239, 68, 68); WHITE = (241, 245, 249)
MUTED = (148, 163, 184); SOFT = (203, 213, 225); PANEL = (17, 24, 45); TERM = (8, 12, 26)

SERIES = {  # accent, label
    'linux': (GREEN, 'LINUX ZERO TO HERO'),
    'git': (AMBER, 'GIT & GITHUB'),
    'devops': (CYAN, 'DEVOPS & SRE'),
}

GF = '/usr/share/fonts/truetype/google-fonts/'
IF = '/usr/share/fonts/opentype/inter/'
DF = '/usr/share/fonts/truetype/dejavu/'


@lru_cache(None)
def font(name, size):
    path = {'head': GF + 'Poppins-Bold.ttf', 'headm': GF + 'Poppins-Medium.ttf',
            'body': IF + 'Inter-SemiBold.otf', 'bodyb': IF + 'Inter-Bold.otf',
            'mono': DF + 'DejaVuSansMono.ttf', 'monob': DF + 'DejaVuSansMono-Bold.ttf'}[name]
    return ImageFont.truetype(path, size)


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def back(x):
    x = clamp(x); c = 1.7
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def tw(text, f):
    return f.getlength(text)


def words_of(text):
    """'plain *hl words*, plain' -> [(word, highlighted)]; punctuation after a closing * stays plain-coloured."""
    import re
    out, hl = [], False
    for tok in text.split(' '):
        if not tok:
            continue
        m = re.match(r'^(\*?)(.*?)(\*?)([.,!?:;)]*)$', tok)
        opn, body, cls, tail = m.groups()
        if opn:
            hl = True
        out.append((body + tail, hl))
        if cls:
            hl = False
    return out


def wrap_words(ws, f, maxw):
    lines, cur, curw = [], [], 0
    sp = tw(' ', f)
    for w, h in ws:
        ww = tw(w, f)
        if cur and curw + sp + ww > maxw:
            lines.append(cur); cur, curw = [], 0
        cur.append((w, h)); curw += (sp if len(cur) > 1 else 0) + ww
    if cur:
        lines.append(cur)
    return lines


def draw_rich(d, lines, f, x0, y0, lh, base, hi, center_w=None, nshow=None):
    """Draws wrapped rich lines; nshow = number of words revealed (karaoke pop-in)."""
    k = 0
    sp = tw(' ', f)
    for li, line in enumerate(lines):
        lw = sum(tw(w, f) for w, _ in line) + sp * (len(line) - 1)
        x = x0 + (center_w - lw) / 2 if center_w else x0
        for w, h in line:
            if nshow is not None and k >= nshow:
                return
            d.text((x, y0 + li * lh), w, font=f, fill=hi if h else base)
            x += tw(w, f) + sp
            k += 1


def read_time(text):
    return 0.9 + len(text.replace('*', '').split()) * 0.30


# ------------------------------------------------------------------ backgrounds
@lru_cache(None)
def static_bg(accent):
    img = Image.new('RGB', (W, H), BG)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    arr = np.asarray(img).astype(np.float32)
    for (cx, cy, r, col, a) in ((180, 380, 700, accent, 0.20), (980, 1200, 760, VIOLET, 0.16),
                                (540, 1900, 650, CYAN, 0.10)):
        g = np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * (r / 2) ** 2))[..., None] * a
        arr = arr * (1 - g) + np.array(col, np.float32) * g
    img = Image.fromarray(arr.clip(0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    for x in range(0, W, 60):
        d.line([(x, 0), (x, H)], fill=mix(BG, SOFT, 0.05))
    for y in range(0, H, 60):
        d.line([(0, y), (W, y)], fill=mix(BG, SOFT, 0.05))
    # dim the area under YouTube's title overlay
    shade = Image.new('L', (W, H), 0)
    sd = ImageDraw.Draw(shade)
    for i in range(300):
        sd.line([(0, H - 300 + i), (W, H - 300 + i)], fill=int(110 * i / 300))
    img.paste(Image.new('RGB', (W, H), (4, 6, 14)), (0, 0), shade)
    return img


def stars(d, t, accent):
    rng = random.Random(7)
    for i in range(46):
        x, y = rng.uniform(20, W - 20), rng.uniform(220, 1700)
        sp = rng.uniform(0.3, 1.0)
        a = 0.5 + 0.5 * math.sin(t * 2.2 * sp + i)
        yy = y - (t * 18 * sp) % 1500
        if yy < 220:
            yy += 1480
        c = mix(BG, accent if i % 3 == 0 else SOFT, 0.25 + 0.5 * a)
        r = 2 + (i % 3)
        d.ellipse([x - r, yy - r, x + r, yy + r], fill=c)


def rr(d, box, fill, r=34, outline=None, width=3):
    d.rounded_rectangle(box, r, fill=fill, outline=outline, width=width)


# ------------------------------------------------------------------ chrome
def chrome(img, d, spec, gt, total):
    accent, label = SERIES[spec['series']]
    # progress bar
    d.rectangle([0, 0, W, 12], fill=mix(BG, SOFT, 0.12))
    d.rectangle([0, 0, int(W * clamp(gt / total)), 12], fill=accent)
    # tri-colour signature bar
    for i, c in enumerate((CYAN, AMBER, VIOLET)):
        d.rectangle([60 + i * 60, 66, 60 + i * 60 + 52, 72], fill=c)
    f = font('bodyb', 34)
    chip = f"{label}  ·  {spec['tag']}"
    cw = tw(chip, f)
    rr(d, [60, 92, 60 + cw + 52, 156], mix(BG, accent, 0.22), r=32, outline=accent, width=2)
    d.text((86, 101), chip, font=f, fill=WHITE)
    fm = font('monob', 34)
    d.text((W - 60 - tw('>_ Tech-dev', fm), 104), '>_ Tech-dev', font=fm, fill=SOFT)


# ------------------------------------------------------------------ terminal
def terminal(img, d, beat, accent, age, slide):
    x0, y0, x1 = 60, 240, 1020
    out = beat.get('out', [])
    y1 = y0 + 200 + 70 + 66 * max(1, len(out))
    y1 = max(y1, 640)
    dy = int((1 - ease(slide)) * -60)
    box = [x0, y0 + dy, x1, y1 + dy]
    sh = Image.new('L', (W, H), 0)
    ImageDraw.Draw(sh).rounded_rectangle([box[0] + 10, box[1] + 18, box[2] + 10, box[3] + 18], 34, fill=150)
    img.paste((2, 4, 10), (0, 0), sh.filter(ImageFilter.GaussianBlur(14)))
    rr(d, box, TERM, outline=mix(TERM, accent, 0.6), width=3)
    d.rounded_rectangle([x0, y0 + dy, x1, y0 + dy + 70], 34, fill=(22, 30, 54))
    d.rectangle([x0, y0 + dy + 40, x1, y0 + dy + 70], fill=(22, 30, 54))
    for i, c in enumerate((RED, AMBER, GREEN)):
        d.ellipse([x0 + 34 + i * 44, y0 + dy + 22, x0 + 60 + i * 44, y0 + dy + 48], fill=c)
    user = beat.get('user', 'shivam'); host = beat.get('host', 'tech-dev')
    fh = font('mono', 28)
    t = f"{user}@{host}: ~"
    d.text(((x0 + x1) / 2 - tw(t, fh) / 2, y0 + dy + 20), t, font=fh, fill=MUTED)
    # command typing
    cmd = beat['cmd']
    fc = font('monob', 66 if len(cmd) <= 20 else 50 if len(cmd) <= 26 else 40 if len(cmd) <= 34 else 32)
    tstart = 0.35
    n = int(clamp((age - tstart) * 15 / max(1, len(cmd))) * len(cmd)) if age > tstart else 0
    yc = y0 + dy + 120
    d.text((x0 + 40, yc), '$', font=fc, fill=accent)
    d.text((x0 + 40 + tw('$ ', fc), yc), cmd[:n], font=fc, fill=WHITE)
    typed_done = tstart + len(cmd) / 15
    if age < typed_done + 0.25 or int(age * 2.4) % 2 == 0:
        cx = x0 + 40 + tw('$ ' + cmd[:n], fc) + 4
        d.rectangle([cx, yc + 6, cx + 26, yc + fc.size + 4], fill=accent)
    # output
    if age > typed_done + 0.25:
        ml = max([len(o) for o in out] + [0])
        fo = font('mono', 54 if ml <= 22 else 40 if ml <= 34 else 32 if ml <= 44 else 26)
        hl = beat.get('hl', [])
        hl = [hl] if isinstance(hl, str) else hl
        err = beat.get('error', False)
        for i, line in enumerate(out):
            if age < typed_done + 0.25 + i * 0.12:
                break
            col = RED if err else (accent if any(h and h in line for h in hl) else SOFT)
            d.text((x0 + 40, yc + fc.size + 50 + i * 66), line, font=fo, fill=col)
    return box[3]


def big_card(img, d, beat, accent, age, slide):
    """No command: a big keyword card (e.g. 'case-sensitive')."""
    x0, y0, x1, y1 = 60, 240, 1020, 700
    dy = int((1 - ease(slide)) * -60)
    rr(d, [x0, y0 + dy, x1, y1 + dy], PANEL, outline=accent, width=3)
    s = back(clamp(age / 0.45))
    word = beat['big']
    size = 120
    while tw(word, font('head', size)) > (x1 - x0 - 80) and size > 54:
        size -= 6
    f = font('head', int(size * (0.6 + 0.4 * s)))
    d.text(((x0 + x1) / 2 - tw(word, f) / 2, (y0 + y1) / 2 + dy - f.size * 0.62 - (24 if beat.get('sub') else 0)),
           word, font=f, fill=accent)
    if beat.get('sub'):
        fs = font('body', 40)
        d.text(((x0 + x1) / 2 - tw(beat['sub'], fs) / 2, y1 + dy - 120), beat['sub'], font=fs, fill=SOFT)
    return y1 + dy


# ------------------------------------------------------------------ caption bubble
def bubble(img, d, text, accent, age, top, who):
    f = font('head', 58)
    ws = words_of(text)
    lines = wrap_words(ws, f, 860)
    lh = 76
    bh = 70 + lh * len(lines)
    y0 = top + 56
    x0, x1 = 60, 1020
    a = ease(age / 0.3)
    dy = int((1 - a) * 30)
    col = cast.CAST.get(who, {}).get('col', accent)
    rr(d, [x0, y0 + dy, x1, y0 + bh + dy], (250, 250, 252), r=40)
    # tail down-left toward the animal
    d.polygon([(240, y0 + bh + dy - 4), (330, y0 + bh + dy - 4), (250, y0 + bh + dy + 58)], fill=(250, 250, 252))
    nshow = int(clamp((age - 0.1) / max(0.4, 0.09 * len(ws))) * len(ws) + 0.999)
    draw_rich(d, lines, f, x0 + 48, y0 + dy + 30, lh, (15, 23, 42), mix(col, (15, 23, 42), 0.35), nshow=nshow)
    return y0 + bh


def name_tag(d, who, accent, age):
    c = cast.CAST[who]
    t = f"{c['name']} the {c['animal']}" if c['name'] != c['animal'] else c['name']
    f = font('bodyb', 38)
    a = ease(age / 0.35)
    x = 560 + int((1 - a) * 80)
    y = 1330
    w = tw(t, f)
    rr(d, [x, y, x + w + 48, y + 66], mix(BG, c['col'], 0.3), r=33, outline=c['col'], width=2)
    d.text((x + 24, y + 10), t, font=f, fill=WHITE)


# ------------------------------------------------------------------ timeline
def beat_duration(b):
    if b['kind'] == 'hook':
        return b.get('dur', 3.4)
    if b['kind'] == 'cta':
        return b.get('dur', 4.6)
    d = read_time(b['say']) + 0.6
    nsyl = cast.syllables_for(b['say'])
    d = max(d, cast.voice_len(b['who'], nsyl) + 0.9)
    if b.get('cmd'):
        d = max(d, 0.35 + len(b['cmd']) / 15 + 0.25 + 0.12 * len(b.get('out', [])) + 1.8)
    return round(clamp(d + b.get('extra', 0), 3.4, 8.0), 2)


VO_OFFSET = {'hook': 1.0, 'beat': 0.2, 'cta': 0.5}


def load_clip(path):
    """Decode an mp3/wav voice clip to mono float32 at SR."""
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-af', 'loudnorm=I=-15:TP=-1.5:LRA=11', '-f', 's16le', '-ac', '1', '-ar', str(SR), '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768.0


def build(spec, vo=None):
    """vo: {'hook': clip, 'beat3': clip, 'cta': clip} (ElevenLabs lines, see voice/vo.py)."""
    vo = vo or {}
    beats = [dict(kind='hook', **spec['hook'])] + [dict(kind='beat', **b) for b in spec['beats']] + \
            [dict(kind='cta', **spec['cta'])]
    nb = len(spec['beats'])
    t = 0.0
    for i, b in enumerate(beats):
        b['t0'] = t
        b['dur'] = beat_duration(b)
        b.pop('vo', None)
        key = 'hook' if i == 0 else ('cta' if i == nb + 1 else f'beat{i - 1}')
        if key in vo:
            b['vo'] = vo[key]
            b['vo_len'] = len(vo[key]) / SR
            b['dur'] = round(max(b['dur'], VO_OFFSET[b['kind']] + b['vo_len'] + 0.5), 2)
        t += b['dur']
    return beats, t


def frame(spec, beats, total, gt):
    accent = SERIES[spec['series']][0]
    img = static_bg(accent).copy()
    d = ImageDraw.Draw(img)
    stars(d, gt, accent)
    bi = max(i for i, b in enumerate(beats) if b['t0'] <= gt + 1e-6)
    b = beats[bi]
    age = gt - b['t0']
    prev = beats[bi - 1] if bi > 0 else None

    if b['kind'] == 'hook':
        f = font('head', 104)
        ws = words_of(b['text'])
        lines = wrap_words(ws, f, 940)
        lh = 124
        y = 520 - lh * len(lines) / 2
        s = back(clamp(age / 0.5))
        nshow = int(clamp(age / 0.9) * len(ws) + 0.999)
        draw_rich(d, lines, f, 70, y, lh, WHITE, accent, center_w=940, nshow=nshow)
        if b.get('sub') and age > 0.8:
            fs = font('body', 44)
            d.text((W / 2 - tw(b['sub'], fs) / 2, y + lh * len(lines) + 34), b['sub'], font=fs,
                   fill=mix(BG, SOFT, ease((age - 0.8) / 0.4)))
        who = b['who']
        for i, w in enumerate(who[:2]):
            delay = 0.25 + i * 0.35
            p = back(clamp((age - delay) / 0.5))
            if p <= 0:
                continue
            cx = 300 + i * 440
            cast.draw_animal(img, w, cx, int(1600 + (1 - p) * 500), 480, mood='happy',
                             arms='wave' if (i == 0 and w != 'ollie') else 'up', t=gt, talking=age > delay + 0.3 and age < delay + 1.4,
                             flip=(i == 1))
        chrome(img, d, spec, gt, total)
        return img

    if b['kind'] == 'cta':
        fs = font('head', 92)
        t1 = 'Full episode'
        t2 = 'on the channel'
        a = back(clamp(age / 0.5))
        d.text((W / 2 - tw(t1, fs) / 2, 330 - (1 - a) * 40), t1, font=fs, fill=WHITE)
        d.text((W / 2 - tw(t2, fs) / 2, 440 - (1 - a) * 40), t2, font=fs, fill=accent)
        fn = font('body', 42)
        for i, line in enumerate(b.get('lines', [])):
            if age > 0.5 + i * 0.25:
                d.text((W / 2 - tw(line, fn) / 2, 600 + i * 62), line, font=fn, fill=SOFT)
        # pulsing subscribe pill
        pulse = 1 + 0.05 * math.sin(age * 7)
        pw, ph = int(520 * pulse), int(120 * pulse)
        cx, cy = W / 2, 900
        if age > 0.9:
            rr(d, [cx - pw / 2, cy - ph / 2, cx + pw / 2, cy + ph / 2], RED, r=ph // 2)
            fb = font('head', int(56 * pulse))
            d.text((cx - tw('SUBSCRIBE', fb) / 2, cy - fb.size * 0.66), 'SUBSCRIBE', font=fb, fill=WHITE)
        cast_list = b['who']
        n = len(cast_list)
        for i, w in enumerate(cast_list):
            p = back(clamp((age - 0.2 - i * 0.15) / 0.5))
            if p <= 0:
                continue
            cx = W / 2 + (i - (n - 1) / 2) * (min(330, 800 / (n - 1)) if n > 1 else 0)
            cast.draw_animal(img, w, cx, int(1520 + (1 - p) * 500), 420 if n <= 3 else 340, mood='celebrate',
                             arms='up', t=gt + i, talking=False, flip=cx > W / 2)
        chrome(img, d, spec, gt, total)
        return img

    # regular beat
    accent_c = accent
    first_card = prev is None or prev['kind'] != 'beat' or (bool(prev.get('cmd')) != bool(b.get('cmd')))
    slide = age / 0.35 if first_card else 1.0
    if b.get('cmd'):
        bottom = terminal(img, d, b, accent_c, age, slide)
    elif b.get('big'):
        bottom = big_card(img, d, b, accent_c, age, slide)
    else:
        bottom = 240
    bubble(img, d, b['say'], accent_c, age, bottom, b['who'])
    who = b['who']
    same = prev is not None and prev['kind'] == 'beat' and prev['who'] == who
    p = 1.0 if same else back(clamp(age / 0.45))
    if b.get('vo') is not None:
        talking = VO_OFFSET['beat'] < age < VO_OFFSET['beat'] + b['vo_len']
    else:
        talking = age < cast.voice_len(who, cast.syllables_for(b['say'])) + 0.2
    cast.draw_animal(img, who, 300, int(1600 + (1 - p) * 560), 520, mood=b.get('mood', 'normal'),
                     arms=b.get('arms', 'point' if b.get('cmd') else 'rest'), t=gt, talking=talking)
    name_tag(d, who, accent_c, 1.0 if same else age)
    if b.get('badge') and age > 0.6:
        fb = font('head', 54)
        txt = b['badge']
        s = back(clamp((age - 0.6) / 0.35))
        bw = tw(txt, fb) + 60
        x = min(560, 960 - bw); y = 1430
        rr(d, [x, y, x + bw * s, y + 92], accent_c, r=46)
        if s > 0.7:
            d.text((x + 30, y + 10), txt, font=fb, fill=(10, 15, 31))
    chrome(img, d, spec, gt, total)
    return img


# ------------------------------------------------------------------ audio
def _env(n, a=0.005, dcy=0.2):
    t = np.arange(n) / SR
    return np.clip(t / a, 0, 1) * np.exp(-t / dcy)


def music(total, seed=5):
    n = int(total * SR); t = np.arange(n) / SR
    out = np.zeros(n)
    chords = [(220.0, 261.63, 329.63, 392.0), (174.61, 220.0, 261.63, 329.63),
              (130.81, 164.81, 196.0, 246.94), (196.0, 246.94, 293.66, 329.63)]
    bar = 60 / 86 * 4
    for k in range(int(total / bar) + 1):
        s = int(k * bar * SR); e = min(n, int((k + 1) * bar * SR) + int(0.3 * SR))
        if s >= n:
            break
        tt = t[s:e] - t[s]
        env = np.clip(tt / 0.4, 0, 1) * np.clip((bar + 0.3 - tt) / 0.5, 0, 1)
        for f in chords[k % 4]:
            out[s:e] += (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * f * 2.003 * tt)) * env * 0.05
    from scipy.signal import butter, lfilter
    b, a = butter(2, 1800 / (SR / 2)); out = lfilter(b, a, out)
    beat = 60 / 86
    rng = np.random.default_rng(seed)
    for k in range(int(total / beat * 2)):
        s = int(k * beat / 2 * SR)
        if s >= n:
            break
        if k % 2 == 0:  # kick on beats
            m = min(n - s, int(0.25 * SR)); tt = np.arange(m) / SR
            out[s:s + m] += np.sin(2 * np.pi * (50 + 70 * np.exp(-tt / 0.03)) * tt) * np.exp(-tt / 0.12) * 0.32
        m = min(n - s, int(0.05 * SR))  # hat
        hat = rng.standard_normal(m) * np.exp(-np.arange(m) / SR / 0.012) * 0.05
        out[s:s + m] += np.diff(np.concatenate([[0], hat]))
    return out


def sfx(kind, rng):
    if kind == 'whoosh':
        n = int(0.4 * SR); t = np.arange(n) / SR
        from scipy.signal import butter, lfilter
        noise = rng.standard_normal(n)
        b, a = butter(2, [600 / (SR / 2), 4000 / (SR / 2)], 'band')
        return lfilter(b, a, noise) * np.sin(np.pi * t / 0.4) ** 2 * 0.22
    if kind == 'key':
        n = int(0.03 * SR)
        return rng.standard_normal(n) * _env(n, 0.001, 0.006) * 0.12
    if kind == 'pop':
        n = int(0.18 * SR); t = np.arange(n) / SR
        return np.sin(2 * np.pi * (500 + 900 * t / 0.18) * t) * _env(n, 0.002, 0.05) * 0.25
    if kind == 'ding':
        n = int(0.9 * SR); t = np.arange(n) / SR
        return (np.sin(2 * np.pi * 1318 * t) + 0.5 * np.sin(2 * np.pi * 1976 * t)) * _env(n, 0.002, 0.3) * 0.16
    if kind == 'buzz':
        n = int(0.35 * SR); t = np.arange(n) / SR
        return np.sign(np.sin(2 * np.pi * 140 * t)) * _env(n, 0.005, 0.2) * 0.12
    return np.zeros(1)


def make_audio(beats, total, path, seed=11):
    rng = np.random.default_rng(seed)
    n = int(total * SR) + SR
    mixb = np.zeros(n)
    voc = np.zeros(n)

    def add(buf, sig, t, g=1.0):
        s = int(t * SR)
        if s >= n:
            return
        e = min(n, s + len(sig))
        buf[s:e] += sig[:e - s] * g

    seen = set()
    for b in beats:
        t0 = b['t0']
        add(mixb, sfx('whoosh', rng), max(0, t0 - 0.12))
        hv = b.get('vo') is not None
        if hv:  # human (ElevenLabs) voice line
            add(voc, b['vo'], t0 + VO_OFFSET[b['kind']], 1.0)
        if b['kind'] == 'hook':
            for i, w in enumerate(b['who'][:2]):
                add(voc, cast.call(w, rng), t0 + 0.3 + i * 0.45, 0.45 if hv else 0.9)
                seen.add(w)
        elif b['kind'] == 'cta':
            add(mixb, sfx('ding', rng), t0 + 0.9)
            for i, w in enumerate(b['who']):
                add(voc, cast.call(w, rng) * (0.25 if hv else 0.6), t0 + 0.3 + i * 0.35)
        else:
            w = b['who']
            if hv:
                seen.add(w)
            elif w not in seen:
                add(voc, cast.call(w, rng), t0 + 0.05, 0.85); seen.add(w)
                vstart = t0 + 0.05 + len(cast.call(w, np.random.default_rng(1))) / SR * 0.6
            else:
                vstart = t0 + 0.15
            if not hv:
                add(voc, cast.voice(w, cast.syllables_for(b['say']), rng), vstart, 0.95)
            if b.get('cmd'):
                for i in range(len(b['cmd'])):
                    add(mixb, sfx('key', rng), t0 + 0.35 + i / 15 + rng.uniform(0, 0.02))
                add(mixb, sfx('buzz' if b.get('error') else 'pop', rng), t0 + 0.35 + len(b['cmd']) / 15 + 0.25)
            if b.get('badge'):
                add(mixb, sfx('pop', rng), t0 + 0.6)
    # duck music under voices
    from scipy.signal import butter, lfilter
    envv = np.abs(voc)
    bb, aa = butter(1, 6 / (SR / 2)); envv = lfilter(bb, aa, envv)
    duck = 1 - 0.55 * np.clip(envv / (envv.max() + 1e-9) * 4, 0, 1)
    mus = np.zeros(n); m = music(total); mus[:len(m)] = m
    out = mus * duck * 0.9 + mixb + voc * 1.1
    fade = int(1.2 * SR); end = int(total * SR)
    out[end - fade:end] *= np.linspace(1, 0.2, fade)
    out[end:] = 0
    out = out[:end]
    out = out / (np.abs(out).max() + 1e-9) * 0.89
    pcm = (out * 32767).astype(np.int16)
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR)
        wf.writeframes(pcm.tobytes())


# ------------------------------------------------------------------ main
def load(path):
    spec_ = importlib.util.spec_from_file_location('spec', path)
    m = importlib.util.module_from_spec(spec_); spec_.loader.exec_module(m)
    return m.SHORT


def upload_text(spec, total, outdir):
    u = dict(spec['upload'])
    u['duration'] = round(total, 1)
    json.dump(u, open(os.path.join(outdir, 'upload.json'), 'w'), indent=2, ensure_ascii=False)
    with open(os.path.join(outdir, 'upload.txt'), 'w') as f:
        f.write(f"TITLE\n{u['title']}\n\nDESCRIPTION\n{u['description']}\n\nTAGS\n{', '.join(u['tags'])}\n")


def main():
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    spec = load(sys.argv[1]); outdir = sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    vo = {}
    if '--vo' in sys.argv:  # manifest.json from voice/vo.py: {"hook": path, "beat3": path, "cta": path}
        man = json.load(open(sys.argv[sys.argv.index('--vo') + 1]))
        vo = {k: load_clip(v) for k, v in man.items() if v and os.path.exists(v)}
        print('voice lines:', ', '.join(f"{k} {len(c) / SR:.1f}s" for k, c in vo.items()) or 'none')
    beats, total = build(spec, vo)
    print(f"Short length: {total:.1f}s")
    for b in beats:
        print(f"  {b['t0']:5.1f}s  {b['dur']:.1f}s  {b['kind']:5s} {b.get('who', '')} {b.get('cmd', b.get('big', b.get('text', '')))}")
    if not 25 <= total <= 58:
        print('WARNING: aim for 30-50 s (hard limit 60 s)')
    if '--stills' in sys.argv:
        ts = [float(x) for x in sys.argv[sys.argv.index('--stills') + 1].split(',')]
        for t in ts:
            frame(spec, beats, total, t).save(os.path.join(outdir, f'still_{t:05.1f}.jpg'), quality=88)
        print('stills written'); return
    wav = os.path.join(outdir, 'audio.wav')
    make_audio(beats, total, wav)
    nfr = int(total * FPS)
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
           '-i', '-', '-i', wav, '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p',
           '-c:a', 'aac', '-b:a', '160k', '-shortest', '-movflags', '+faststart', os.path.join(outdir, 'short.mp4')]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(nfr):
        p.stdin.write(frame(spec, beats, total, i / FPS).tobytes())
    p.stdin.close(); p.wait()
    cover_t = spec.get('cover_at', 1.6)
    frame(spec, beats, total, cover_t).convert('RGB').save(os.path.join(outdir, 'cover.jpg'), quality=90)
    upload_text(spec, total, outdir)
    os.remove(wav)
    print('done:', os.path.join(outdir, 'short.mp4'))


if __name__ == '__main__':
    main()
