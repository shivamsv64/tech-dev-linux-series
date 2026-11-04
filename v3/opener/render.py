#!/usr/bin/env python3
"""Tech-dev hook opener (Remotion): the first ~20-30 s of a long video, spoken in Shivam's own ElevenLabs voice.

    python3 v3/opener/render.py <episode_spec.py> <outdir> [--stills 1.0,5.5,...]

Reads EP['opener'] from the episode spec (see v3/OPENER.md), times every visual beat to the words Shivam says
(local Whisper word timestamps, cached next to the audio), stages fonts/art/photos/audio into public/ and renders
<outdir>/opener.mp4 (1920x1080, 30 fps, AAC). With --stills it only renders those frames as PNGs (fast preview).
engine v2 then puts opener.mp4 in front of the episode automatically (EP['opener'] present + <outdir>/opener.mp4).
"""
import sys, os, json, re, shutil, subprocess, importlib.util
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
V2 = os.path.join(REPO, 'v2')
GF = '/usr/share/fonts/truetype/google-fonts/'
SR = 48000
VOICE_AT = 0.35          # seconds of picture before Shivam starts speaking
SERIES = {'devops': ('DevOps & SRE Zero to Hero', 'mission', 'mission_theme.mp3', 'devops-series/media/day{n:02d}'),
          'linux': ('Linux Zero to Hero', 'city', 'city_theme.mp3', 'media/ep{n:02d}'),
          'git': ('Git & GitHub: Beginner to Advanced', 'city', 'city_theme.mp3', 'media/ep{n:02d}')}


def load_spec(path):
    s = importlib.util.spec_from_file_location('ep', path); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m.EP


def decode(path, sr):
    r = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', path, '-f', 'f32le', '-ac', '1', '-ar', str(sr), '-'], capture_output=True, check=True)
    return np.frombuffer(r.stdout, np.float32).copy()


def word_times(audio, cache):
    """[{w, s, e}] from local Whisper (faster-whisper small.en, MIT); cached as JSON next to the audio."""
    if os.path.exists(cache):
        return json.load(open(cache))
    from faster_whisper import WhisperModel
    m = WhisperModel('small.en', device='cpu', compute_type='int8')
    segs, _ = m.transcribe(decode(audio, 16000), word_timestamps=True, beam_size=5)
    words = [dict(w=w.word.strip(), s=round(w.start, 2), e=round(w.end, 2)) for s in segs for w in s.words]
    json.dump(words, open(cache, 'w'), indent=0)
    return words


def norm(w): return re.sub(r'[^a-z0-9]+', '', w.lower())


def resolver(words):
    """'@word' -> start time of the first spoken word matching it; '@word#2' -> second match; '@word+0.3' -> offset."""
    def res(v):
        if not (isinstance(v, str) and v.startswith('@')):
            return v
        m = re.match(r'@([^#+\-]+)(?:#(\d+))?([+\-][\d.]+)?$', v)
        if not m: raise SystemExit(f'bad anchor {v}')
        key, nth, off = norm(m.group(1)), int(m.group(2) or 1), float(m.group(3) or 0)
        hits = [w for w in words if norm(w['w']) == key]
        if len(hits) < nth: raise SystemExit(f'anchor {v}: "{m.group(1)}" is not spoken {nth} time(s) in the opener audio')
        return round(hits[nth - 1]['s'] + VOICE_AT + off, 3)
    def walk(x):
        if isinstance(x, dict): return {k: walk(v) for k, v in x.items()}
        if isinstance(x, list): return [walk(v) for v in x]
        return res(x)
    return walk


# ------------------------------------------------------------------ sound effects (numpy, no samples needed)
def _lp(x, k):
    y = np.zeros_like(x); a = 0.0
    for i in range(len(x)): a += k[i] * (x[i] - a); y[i] = a
    return y


def sfx_bank(dst):
    rng = np.random.default_rng(7); os.makedirs(dst, exist_ok=True)
    def save(name, a):
        a = a / max(1e-6, np.abs(a).max()) * 0.9
        import soundfile as sf; sf.write(os.path.join(dst, name), a.astype(np.float32), SR)
    n = int(.7 * SR); t = np.linspace(0, 1, n)
    save('whoosh.wav', _lp(rng.standard_normal(n), 0.02 + 0.3 * np.sin(np.pi * t) ** 2) * np.sin(np.pi * t) ** 2)
    n = int(.35 * SR); t = np.arange(n) / SR
    save('stamp.wav', np.sin(2 * np.pi * 70 * t) * np.exp(-t * 18) + 0.5 * rng.standard_normal(n) * np.exp(-t * 60))
    n = int(.12 * SR); t = np.arange(n) / SR
    save('pop.wav', np.sin(2 * np.pi * (520 + 900 * t / t[-1]) * t) * np.exp(-t * 35))
    n = int(.45 * SR); t = np.linspace(0, 1, n)
    save('zip.wav', _lp(rng.standard_normal(n), 0.05 + 0.4 * t) * np.sin(np.pi * t) ** 0.5 * 0.7)


def auto_sfx(beats):
    out = []
    for i, b in enumerate(beats):
        if i > 0: out.append(dict(file='sfx/whoosh.wav', at=max(0, b['from'] - 0.25), vol=0.35))
        for ln in b.get('headline', []) + b.get('lines', []): out.append(dict(file='sfx/stamp.wav', at=ln['at'], vol=0.30))
        for s in b.get('stamps', []) + ([b['stamp']] if b.get('stamp') else []): out.append(dict(file='sfx/stamp.wav', at=s['at'], vol=0.40))
        for c in b.get('cards', []): out.append(dict(file='sfx/pop.wav', at=c['at'], vol=0.25))
        for l in b.get('labels', []): out.append(dict(file='sfx/zip.wav', at=l['at'] - 0.5, vol=0.30))
    return out


# ------------------------------------------------------------------ main
def main():
    spec_path, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True)
    EP = load_spec(spec_path); op = EP['opener']; n = int(EP['number'])
    show, look, music, media_t = SERIES[EP['series']]; media = os.path.join(REPO, media_t.format(n=n))
    audio = os.path.join(REPO, op['audio']) if not os.path.isabs(op['audio']) else op['audio']
    if not os.path.exists(audio): raise SystemExit(f'opener audio missing: {audio} (generate it first, see v3/OPENER.md)')
    words = word_times(audio, os.path.splitext(audio)[0] + '_words.json')
    vdur = len(decode(audio, SR)) / SR
    duration = round(VOICE_AT + vdur + op.get('tail', 0.6), 2)
    R = resolver(words)
    beats = R(op['beats'])
    for i, b in enumerate(beats):
        b['from'] = 0 if i == 0 else b['from']
        b['to'] = beats[i + 1]['from'] if i + 1 < len(beats) else duration

    pub = os.path.join(HERE, 'public')
    shutil.rmtree(pub, ignore_errors=True); os.makedirs(os.path.join(pub, 'fonts')); os.makedirs(os.path.join(pub, 'art'))
    for f in os.listdir(os.path.join(V2, 'assets', 'fonts')): shutil.copy(os.path.join(V2, 'assets', 'fonts', f), os.path.join(pub, 'fonts', f))
    for f in ('Poppins-Bold.ttf', 'Poppins-Medium.ttf'): shutil.copy(GF + f, os.path.join(pub, 'fonts', f))
    for f in os.listdir(os.path.join(V2, 'assets', 'art')): shutil.copy(os.path.join(V2, 'assets', 'art', f), os.path.join(pub, 'art', f))
    if os.path.isdir(os.path.join(media, 'art')):   # fresh FLUX art of the day replaces library art of the same name
        for f in os.listdir(os.path.join(media, 'art')): shutil.copy(os.path.join(media, 'art', f), os.path.join(pub, 'art', f))
    shutil.copytree(os.path.join(REPO, 'hf', 'assets'), os.path.join(pub, 'photo'))
    shutil.copy(audio, os.path.join(pub, 'voice.mp3')); shutil.copy(os.path.join(V2, 'assets', 'music', music), os.path.join(pub, 'music.mp3'))
    sfx_bank(os.path.join(pub, 'sfx'))

    props = dict(duration=duration, words=[dict(w=w['w'], s=round(w['s'] + VOICE_AT, 3), e=round(w['e'] + VOICE_AT, 3)) for w in words],
                 beats=beats, show=show, badge=EP['badge'], look=look, voice='voice.mp3', voiceAt=VOICE_AT,
                 music='music.mp3' if op.get('music', True) else None, sfx=auto_sfx(beats))
    pp = os.path.join(out, 'opener_props.json'); json.dump(props, open(pp, 'w'), indent=1)
    print(f'opener: {duration:.1f}s, {len(beats)} beats, {len(words)} words')
    for b in beats: print(f"  {b['from']:6.2f}-{b['to']:6.2f}  {b['type']}")

    if not os.path.isdir(os.path.join(HERE, 'node_modules')):
        subprocess.run(['npm', 'install', '--no-audit', '--no-fund', '--loglevel=error'], cwd=HERE, check=True)
    chrome = shutil.which('google-chrome') or shutil.which('chromium') or ''
    common = ['--props', os.path.abspath(pp), '--public-dir', pub, '--log', 'error'] + (['--browser-executable', chrome] if chrome else [])
    if '--stills' in sys.argv:
        for ts in sys.argv[sys.argv.index('--stills') + 1].split(','):
            fr = int(float(ts) * 30)
            subprocess.run(['npx', 'remotion', 'still', 'src/index.ts', 'Opener', os.path.abspath(os.path.join(out, f'opener_{float(ts):05.1f}.png')),
                            '--frame', str(fr)] + common, cwd=HERE, check=True)
        print('stills done'); return
    tmp = os.path.abspath(os.path.join(out, 'opener.tmp.mp4'))
    subprocess.run(['npx', 'remotion', 'render', 'src/index.ts', 'Opener', tmp, '--codec', 'h264', '--crf', '18',
                    '--concurrency', os.environ.get('JOBS', '2'), '--audio-codec', 'aac'] + common, cwd=HERE, check=True)
    os.replace(tmp, os.path.join(out, 'opener.mp4'))
    print('DONE', os.path.join(out, 'opener.mp4'))


if __name__ == '__main__':
    main()
