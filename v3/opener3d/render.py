#!/usr/bin/env python3
"""Tech-dev 3D hook opener (three.js, clay look): the first ~20-30 s of a long video, in Shivam's own ElevenLabs voice.

    python3 v3/opener3d/render.py <episode_spec.py> <outdir> [--sheet | --frames 1.0,5.5,...]

EP['opener'] with 'engine': '3d' (see v3/OPENER.md): audio, text, roles [3 desks], big, photo, beats (word anchors).
Writes data/{lines,words,opener,cues}.json + data/narration.wav + script.json here, checks the film in headless Chrome,
mixes the sound (tools/mix.py) and renders <outdir>/opener.mp4 (1920x1080). engine v2 then puts it in front of the
episode automatically. Software rendering (no GPU): ~1-2 s per frame at 24 fps, so ~10-20 min for a 21 s opener.
--sheet writes <outdir>/opener_sheet.jpg (a frame every 0.5 s); --frames writes full-size JPEGs to <outdir>/opener_frames/.
"""
import sys, os, json, re, shutil, subprocess, importlib.util
import numpy as np, soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
LEAD, TAIL, SR = 0.35, 0.7, 48000
SHOW = {'devops': 'DevOps & SRE Zero to Hero', 'linux': 'Linux Zero to Hero', 'git': 'Git & GitHub: Beginner to Advanced'}


def load(path, name):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


def main():
    spec, out = sys.argv[1], os.path.abspath(sys.argv[2]); os.makedirs(out, exist_ok=True)
    EP = load(spec, 'ep').EP; op = EP['opener']
    R2 = load(os.path.join(REPO, 'v3', 'opener', 'render.py'), 'r2')       # shared helpers: Whisper words, anchors
    R2.VOICE_AT = LEAD
    audio = op['audio'] if os.path.isabs(op['audio']) else os.path.join(REPO, op['audio'])
    words = R2.word_times(audio, os.path.splitext(audio)[0] + '_words.json')
    voice = R2.decode(audio, SR); vdur = len(voice) / SR; dur = round(LEAD + vdur + TAIL, 2)

    # lines = sentences (for captions); words carry their line index
    lines, cur = [], []
    for w in words:
        cur.append(w)
        if re.search(r'[.?!]$', w['w']): lines.append(cur); cur = []
    if cur: lines.append(cur)
    L, Wj = [], []
    for i, ln in enumerate(lines):
        L.append(dict(i=i, text=' '.join(w['w'] for w in ln), start=round(ln[0]['s'] + LEAD, 3), end=round(ln[-1]['e'] + LEAD, 3)))
        Wj += [dict(w=w['w'], line=i, s=round(w['s'] + LEAD, 3), e=round(w['e'] + LEAD, 3)) for w in ln]
    D = os.path.join(HERE, 'data'); os.makedirs(D, exist_ok=True)
    json.dump(dict(duration=dur, lines=L), open(os.path.join(D, 'lines.json'), 'w'), indent=1)
    json.dump(Wj, open(os.path.join(D, 'words.json'), 'w'), indent=0)
    caps = op.get('caps') or []
    sl = [dict(text=l['text'], **({'caps': caps[i]} if i < len(caps) else {})) for i, l in enumerate(L)]
    json.dump(dict(title=EP['upload']['title'], music=op.get('music', 'bed'), lines=sl), open(os.path.join(HERE, 'script.json'), 'w'), indent=1)
    nar = np.concatenate([np.zeros(int(LEAD * SR), np.float32), voice]); sf.write(os.path.join(D, 'narration.wav'), np.stack([nar, nar], 1), SR)

    beats = R2.resolver(words)(op['beats'])
    for i, b in enumerate(beats):
        b['from'] = 0 if i == 0 else b['from']; b['to'] = beats[i + 1]['from'] if i + 1 < len(beats) else dur
    if op.get('photo'):
        os.makedirs(os.path.join(HERE, 'photo'), exist_ok=True)
        shutil.copy(os.path.join(REPO, 'hf', 'assets', op['photo']), os.path.join(HERE, 'photo', op['photo']))
    json.dump(dict(beats=beats, roles=op['roles'], big=op.get('big', ''), photo=op.get('photo'), show=SHOW[EP['series']], badge=EP['badge']),
              open(os.path.join(D, 'opener.json'), 'w'), indent=1)
    print(f'opener3d: {dur:.1f}s, {len(beats)} beats, {len(L)} lines')
    for b in beats: print(f"  {b['from']:6.2f}-{b['to']:6.2f}  {b['type']}")

    env = dict(os.environ, SOFTWARE_GL=os.environ.get('SOFTWARE_GL', '1'), QS=os.environ.get('QS', '&res=0.6&aa=0&shadow=1024'), FPS=os.environ.get('FPS', '24'))
    node = lambda *a: subprocess.run(['node', 'tools/capture.mjs', *a], cwd=HERE, env=env, check=True, capture_output=True, text=True).stdout
    chk = node('check'); print(chk.strip().splitlines()[-1])
    if 'CHECK OK' not in chk: print(chk); raise SystemExit('3D opener check failed')
    if '--sheet' in sys.argv:
        print(node('sheet', os.path.join(out, 'opener_sheet.jpg'), '0.5', '6').strip()); return
    if '--frames' in sys.argv:
        print(node('frames', os.path.join(out, 'opener_frames'), sys.argv[sys.argv.index('--frames') + 1]).strip()); return
    node('cues'); subprocess.run(['python3', 'tools/mix.py', '.'], cwd=HERE, check=True)
    tmp = os.path.join(out, 'opener.tmp.mp4'); print(node('video', tmp).strip().splitlines()[-1])
    os.replace(tmp, os.path.join(out, 'opener.mp4')); print('DONE', os.path.join(out, 'opener.mp4'))


if __name__ == '__main__':
    main()
