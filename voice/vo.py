#!/usr/bin/env python3
"""ElevenLabs voice helper for Tech-dev videos (credit-capped).

Budget: Shivam's ElevenLabs plan has 30,000 credits/month (~1 credit per character on every model).
Hard cap per series per day: 250 characters  ->  3 series = 750/day max (~22.5k/month).
Never generate test takes; generations_count = 1; never retry a generation call.

usage:
  python3 voice/vo.py plan <series> <long_script.txt> <short_spec.py> <workdir>
      -> writes <workdir>/plan.json (lines to voice, voice ids, output paths) and prints it.
         Then, for each line: ElevenLabs creative_generate_speech (model_id eleven_flash_v2_5,
         generations_count 1, voice_id, prompt=text) -> poll creative_get_flow_run_status ->
         curl -sS -o <path> "<content_url>".
  python3 voice/vo.py kokoro <workdir>
      -> FREE: synthesizes every planned Short line locally with Kokoro (v2/tts.py). No ElevenLabs credits.
         This is the default since 1 Nov 2026; ElevenLabs is no longer used per episode.
  python3 voice/vo.py manifest <workdir>
      -> checks the downloaded clips, writes <workdir>/manifest.json for shorts.py --vo
  python3 voice/vo.py mix-long <video.mp4> <clip.mp3> <at_seconds> <out.mp4>
      -> mixes one voice clip over a finished long video (music/SFX ducked under the voice).
"""
import sys, os, re, json, subprocess, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
VOICES = json.load(open(os.path.join(HERE, 'voices.json')))
CAP = VOICES['budget']['per_series_per_day_chars']


def clean(t):
    t = t.replace('*', '').replace('→', 'to').replace('—', ', ').strip()
    return re.sub(r'\s+', ' ', t)


def fit(t, limit):
    """First sentence(s) that fit in `limit` chars; else cut at a word boundary."""
    t = clean(t)
    if len(t) <= limit:
        return t
    parts = re.split(r'(?<=[.!?])\s+', t)
    out = ''
    for p in parts:
        if len((out + ' ' + p).strip()) <= limit:
            out = (out + ' ' + p).strip()
        else:
            break
    if out:
        return out
    words, out = t.split(), ''
    for w in words:
        if len((out + ' ' + w).strip()) > limit - 1:
            break
        out = (out + ' ' + w).strip()
    return out.rstrip(',;:') + '.'


def first_caption(script_path):
    for line in open(script_path, encoding='utf-8'):
        m = re.match(r'^\[(\d+):(\d+)\]\s+(.*\S)', line.strip())
        if m:
            return int(m.group(1)) * 60 + int(m.group(2)), m.group(3)
    raise SystemExit('no timed caption found in ' + script_path)


def load_short(path):
    s = importlib.util.spec_from_file_location('spec', path)
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m.SHORT


def voice_for(who):
    v = VOICES['cast'].get(who) or VOICES['cast']['narrator']
    return v['voice_id']


def cmd_plan(series, script, short_spec, workdir):
    os.makedirs(workdir, exist_ok=True)
    lim = VOICES['budget']['line_chars']
    sp = load_short(short_spec)
    lines = []
    at, cap = first_caption(script)
    lines.append({'id': 'long_intro', 'who': 'narrator', 'text': fit(cap, lim['long_intro']), 'at': at + 0.3})
    lines.append({'id': 'hook', 'who': 'narrator', 'text': fit(sp['hook']['text'], lim['short_hook'])})
    beats = sp['beats']
    k = next((i for i, b in enumerate(beats) if b.get('voice')), 0)
    lines.append({'id': f'beat{k}', 'who': beats[k]['who'], 'text': fit(beats[k]['say'], lim['short_line'])})
    total = sum(len(l['text']) for l in lines)
    while total > CAP:  # shrink the longest line until under the cap
        l = max(lines, key=lambda x: len(x['text']))
        l['text'] = fit(l['text'], len(l['text']) - 10)
        total = sum(len(l['text']) for l in lines)
    for l in lines:
        l['voice_id'] = voice_for(l['who'])
        l['path'] = os.path.join(workdir, l['id'] + '.mp3')
    cta = os.path.join(HERE, 'assets', 'cta.mp3')
    plan = {'series': series, 'model_id': VOICES['model_id'], 'generations_count': 1, 'chars': total, 'cap': CAP,
            'lines': lines,
            'cta': {'path': cta, 'exists': os.path.exists(cta), 'text': VOICES['cta']['text'],
                    'voice_id': voice_for('narrator'),
                    'note': 'one-time: generate only if exists is false, save to path and commit it; reused forever'}}
    json.dump(plan, open(os.path.join(workdir, 'plan.json'), 'w'), indent=2, ensure_ascii=False)
    print(json.dumps(plan, indent=2, ensure_ascii=False))


def dur(path):
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path],
                       capture_output=True, text=True)
    return float(r.stdout.strip() or 0)


def cmd_manifest(workdir):
    plan = json.load(open(os.path.join(workdir, 'plan.json')))
    man, missing = {}, []
    for l in plan['lines']:
        if os.path.exists(l['path']) and dur(l['path']) > 0.3:
            if l['id'] != 'long_intro':
                man[l['id']] = os.path.abspath(l['path'])
        else:
            missing.append(l['id'])
    if plan['cta']['exists'] or os.path.exists(plan['cta']['path']):
        man['cta'] = plan['cta']['path']
    json.dump(man, open(os.path.join(workdir, 'manifest.json'), 'w'), indent=2)
    print(json.dumps({'manifest': man, 'missing': missing}, indent=2))


KOKORO_VOICES = {'narrator': 'am_michael', 'mitthu': 'af_bella', 'ollie': 'bm_george', 'bablu': 'am_puck',
                 'gajju': 'am_onyx', 'ashtu': 'af_nicole', 'kukdu': 'am_eric', 'kaalu': 'am_fenrir'}


def cmd_kokoro(workdir):
    """free local voices for the Short lines in plan.json (skips long_intro: engine v2 narrates long videos)"""
    sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'v2'))
    import tts
    plan = json.load(open(os.path.join(workdir, 'plan.json')))
    for l in plan['lines']:
        if l['id'] == 'long_intro':
            continue
        v = KOKORO_VOICES.get(l['who'], 'am_michael')
        try:
            a = [tts.synth_sentence(s, v) for s in tts.sentences(l['text'])]
        except Exception as e:  # unknown voice name etc. -> narrator voice
            print('voice fallback', v, e); a = [tts.synth_sentence(s, 'am_michael') for s in tts.sentences(l['text'])]
        import numpy as np, soundfile as sf
        wav = l['path'][:-4] + '.wav'
        sf.write(wav, np.concatenate([np.concatenate([x, np.zeros(2400, np.float32)]) for x in a]), tts.SR)
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', wav, '-b:a', '160k', l['path']], check=True)
        os.remove(wav); print('voiced', l['id'], v, f"{dur(l['path']):.1f}s")


def cmd_mix_long(video, clip, at, out):
    at_ms = int(float(at) * 1000)
    fc = (f"[1:a]loudnorm=I=-15:TP=-1.5:LRA=11,aresample=44100,aformat=channel_layouts=stereo,adelay={at_ms}|{at_ms},apad,asplit[vo][sc];"
          f"[0:a]aresample=44100,aformat=channel_layouts=stereo[bed];"
          f"[bed][sc]sidechaincompress=threshold=0.015:ratio=10:attack=15:release=450:makeup=1[duck];"
          f"[duck][vo]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[a]")
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', video, '-i', clip, '-filter_complex', fc,
                    '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
                    '-movflags', '+faststart', out], check=True)
    print('mixed:', out, f'{dur(out):.1f}s')


if __name__ == '__main__':
    a = sys.argv[1:]
    if not a:
        print(__doc__); sys.exit(1)
    {'plan': lambda: cmd_plan(*a[1:5]), 'manifest': lambda: cmd_manifest(a[1]), 'kokoro': lambda: cmd_kokoro(a[1]),
     'mix-long': lambda: cmd_mix_long(*a[1:5])}[a[0]]()
