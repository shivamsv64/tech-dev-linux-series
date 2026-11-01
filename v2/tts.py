#!/usr/bin/env python3
"""Free local narration for Tech-dev videos (Kokoro, Apache-2.0). Zero ElevenLabs credits.

The model (~350 MB) is downloaded once per machine from GitHub releases into ~/.cache/kokoro
(or $TD_KOKORO_DIR).  Needs: pip install --break-system-packages kokoro-onnx soundfile

    python3 v2/tts.py "Some text" out.wav [voice]      # quick one-off
"""
import os, re, sys, subprocess, hashlib
import numpy as np
import soundfile as sf

MODEL_DIR = os.environ.get('TD_KOKORO_DIR', os.path.expanduser('~/.cache/kokoro'))
URLS = {
    'kokoro-v1.0.onnx': 'https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx',
    'voices-v1.0.bin': 'https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin',
}
DEFAULT_VOICE = 'am_michael'   # calm, clear male narrator (the voice Shivam approved in the pilots)
SR = 24000

# spoken forms for terms TTS tends to mangle (applied to the TTS text only, captions keep the original)
SPOKEN = [
    (r'CI/CD', 'C I C D'), (r'\bkubectl\b', 'kube control'), (r'\bK8s\b', 'Kubernetes'), (r'\bnginx\b', 'engine x'),
    (r'\bsudo\b', 'sue doo'), (r'\bSLOs\b', 'S L Os'), (r'\bSLO\b', 'S L O'), (r'\bSLIs\b', 'S L Is'), (r'\bSLI\b', 'S L I'),
    (r'\bSLA\b', 'S L A'), (r'\bSRE\b', 'S R E'), (r'\bAWS\b', 'A W S'), (r'\bGCP\b', 'G C P'), (r'\bEC2\b', 'E C 2'),
    (r'\bIaC\b', 'infrastructure as code'), (r'\bYAML\b', 'yammel'), (r'\bSSH\b', 'S S H'), (r'\bsystemd\b', 'system D'),
    (r'\bchmod\b', 'C H mod'), (r'\bchown\b', 'C H own'), (r'\bgrep\b', 'grep'), (r'\bVM\b', 'V M'), (r'\bVMs\b', 'V Ms'),
    (r'\bAPI\b', 'A P I'), (r'\bAPIs\b', 'A P Is'), (r'\bDNS\b', 'D N S'), (r'\bTCP\b', 'T C P'), (r'\bHTTP\b', 'H T T P'),
    (r'\bHTTPS\b', 'H T T P S'), (r'\bPR\b', 'P R'), (r'\bPRs\b', 'P Rs'), (r'\bIP\b', 'I P'), (r'\bCLI\b', 'C L I'),
    (r'\bQA\b', 'Q A'), (r'\bOS\b', 'O S'), (r'\.gitignore\b', 'dot git ignore'), (r'\bHEAD~1\b', 'head tilde one'),
    (r'→', ' to '), (r'—', ', '), (r'&', ' and '), (r'\*', ''),
]


def spoken(text):
    t = text
    for pat, rep in SPOKEN:
        t = re.sub(pat, rep, t)
    return re.sub(r'\s+', ' ', t).strip()


def ensure_model():
    os.makedirs(MODEL_DIR, exist_ok=True)
    for name, url in URLS.items():
        p = os.path.join(MODEL_DIR, name)
        if not os.path.exists(p) or os.path.getsize(p) < 1_000_000:
            print('downloading', name, flush=True)
            subprocess.run(['curl', '-sSL', '--retry', '3', '-o', p + '.part', url], check=True)
            os.replace(p + '.part', p)
    return os.path.join(MODEL_DIR, 'kokoro-v1.0.onnx'), os.path.join(MODEL_DIR, 'voices-v1.0.bin')


_K = None
def kokoro():
    global _K
    if _K is None:
        from kokoro_onnx import Kokoro
        m, v = ensure_model()
        _K = Kokoro(m, v)
    return _K


def sentences(text):
    parts = re.split(r'(?<=[.!?])\s+', text.strip())
    return [p for p in parts if p.strip()]


def synth_sentence(text, voice=DEFAULT_VOICE, speed=1.0, cache_dir=None):
    """returns float32 mono @24k, trimmed; cached by content hash"""
    key = hashlib.sha1(f'{voice}|{speed}|{text}'.encode()).hexdigest()[:16]
    if cache_dir:
        cp = os.path.join(cache_dir, key + '.wav')
        if os.path.exists(cp):
            a, _ = sf.read(cp, dtype='float32'); return a
    a, sr = kokoro().create(spoken(text), voice=voice, speed=speed, lang='en-us')
    a = np.asarray(a, np.float32)
    idx = np.where(np.abs(a) > 0.01)[0]
    if len(idx):
        a = a[max(0, idx[0] - 300): idx[-1] + 1800]
    if cache_dir:
        os.makedirs(cache_dir, exist_ok=True); sf.write(cp, a, SR)
    return a


if __name__ == '__main__':
    txt, out = sys.argv[1], sys.argv[2]
    v = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_VOICE
    parts = [synth_sentence(s, v) for s in sentences(txt)]
    gap = np.zeros(int(0.12 * SR), np.float32)
    a = np.concatenate([np.concatenate([p, gap]) for p in parts])
    if out.endswith('.mp3'):
        tmp = out + '.wav'; sf.write(tmp, a, SR)
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', tmp, '-b:a', '160k', out], check=True); os.remove(tmp)
    else:
        sf.write(out, a, SR)
    print(out, round(len(a) / SR, 2), 's')
