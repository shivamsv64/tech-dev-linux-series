# Desk Life Shorts (all Tech-dev Shorts since 3 Nov 2026)

Shivam's chosen look for **every** Short (Git, Linux, DevOps, and his funny Shorts channel): relatable cartoon
skits like these references — https://www.youtube.com/shorts/6hfqxSjMSAA , https://www.youtube.com/shorts/C-butiuZz78 ,
https://www.youtube.com/shorts/5toLxPmN3-4 — sketchy hand-drawn line art on muted paper, human characters with big
expressive eyes, a one-line situation banner on top, music-led, with a calm human narrator. **Original characters and
scripts only** (never copy those creators' characters, jokes, shots or frames). **No animal characters, no animal voices.**

Engine: `shorts/skit.py` (drawing kit `shorts/toon.py`, fonts in `shorts/fonts/`). The old animal engine `shorts/shorts.py`
is retired for new Shorts.

```bash
python3 shorts/skit.py shorts/specs/<id>.py out/short-<id> --sheet          # contact sheet, 1 frame/s -> sheet.jpg
python3 shorts/skit.py shorts/specs/<id>.py out/short-<id> --stills 1,9,20  # full-size frames
python3 shorts/skit.py shorts/specs/<id>.py out/short-<id>                  # short.mp4, cover.jpg, upload.json, upload.txt
```
Needs ffmpeg, Pillow, numpy, scipy, soundfile, kokoro-onnx (narration is free/local Kokoro `am_michael`,
model cached in `$TD_KOKORO_DIR` or ~/.cache/kokoro). Shivam's own one-time clip `voice/assets/cta.mp3` closes every Short.
**Zero ElevenLabs.** No `--vo` / `voice/vo.py` step is needed. Render ≈ 2–3 min for 40 s.

## Cast (original, human)
| key | who | use for |
|---|---|---|
| `rohan` | junior engineer, messy hair, hoodie in the series colour | the hero who hits the problem |
| `meera` | calm senior SRE, glasses, bun | the one who knows the fix |
| `khanna` | manager, mustache, tie | pressure, "is prod down?!", deadlines |
| `tara` | teammate, ponytail | second dev, pair-programming, PR reviews |

Moods: `calm happy laugh shock panic tired worried sad angry smug determined sleep talk`.
Poses: `type rest point facepalm cheer shrug phone mug wave headhold think`.
Effects (`fx`): `sweat ! ? zzz lines sparkle steam tear` (`lines` = radial speed lines for shock beats).

## Spec (`shorts/specs/<id>.py`, id = `linux-epNN`, `git-epNN`, `devops-dayNN`)
```python
SKIT = {
  'series': 'linux' | 'git' | 'devops' | 'funny',  # colour: green / amber / cyan / orange
  'tag': 'EP 3' or 'DAY 5',                        # chip under the banner ("LINUX · EP 3")
  'banner': 'When you forget a Linux command at 2 AM',   # relatable situation, ≤ 48 chars, stays on top
  'scenes': [                                      # 8–11 scenes, ONE line of narration each
    {'shot': 'wide', 'set': 'desk_night', 'cast': [{'who': 'rohan', 'mood': 'tired', 'pose': 'type', 'fx': ['sweat']}],
     'say': 'Stop Googling Linux commands. Your *terminal* already knows.'},          # scene 1 = the HOOK
    {'shot': 'eye', 'who': 'rohan', 'mood': 'tired', 'say': '...'},               # giant-eye meme close-up
    {'shot': 'wide', 'set': 'desk_night', 'cast': [{'who': 'rohan', 'mood': 'worried', 'pose': 'headhold', 'x': 380},
              {'who': 'meera', 'mood': 'smug', 'pose': 'mug', 'stand': True, 'x': 790}], 'laptop_x': 380, 'mug': False,
     'say': '...'},
    {'shot': 'screen', 'cmd': 'man -k rotate', 'out': ['logrotate (8) - rotates, compresses,'], 'hl': 'logrotate (8)',
     'say': '...'},                                # monitor close-up, command types itself
    {'shot': 'screen', 'cmd': 'man cd', 'out': ['!No manual entry for cd'], 'badge': 'Use: help cd', 'say': '...'},
    {'shot': 'face', 'who': 'rohan', 'mood': 'shock', 'fx': ['lines', '!'], 'say': 'Wait. It was there the *whole* time?'},
    {'shot': 'phone', 'time': '3:07', 'alert': {'title': 'CRITICAL', 'lines': ['prod-api: 5xx > 20%'], 'more': ['disk 98% on web-01']},
     'say': '...'},                                # pager alert on a phone (buzzes)
    {'shot': 'card', 'big': 'man -k', 'sub': 'search every manual by keyword', 'say': 'Save this...'},   # sticky note takeaway
  ],
  'cta': {'set': 'office'},                        # optional; banner 'Full episode on Tech-dev', Shivam's subscribe clip
  'cover_at': 1.2,
  'upload': {'title': '<Situation hook> #shorts #linux', 'description': '...', 'tags': [...]},
}
```
Sets: `desk_night desk_day bed_night office office_night meeting`. Shots: `wide face eye screen phone card`
(+ automatic `cta`). Optional per scene: `banner` (changes the top banner from here on), `cam` (`push` default, `pull`,
`shake`, `still`), `extra` (seconds), `sfx` (`boing alarm buzz ding slide pop whoosh`), `look` [x, y] for eyes,
`prompt` (e.g. `ubuntu@ip-172-31-8-14:~$`). Output lines starting with `!` are red errors (buzz sound).

## Writing rules (what makes these work)
- **Banner = a relatable situation, not a lesson title**: "When the pipeline fails 5 min before the demo",
  "POV: your first day on call", "When you `git push --force` on main". It's the joke; the narration is the payoff.
- **Scene 1 narration is the hook** (≤ 70 chars), spoken in the first 2 s: a bold claim or a problem.
- Story shape: situation → it goes wrong (eye/face/phone beat, mistake on screen) → the fix (real command + output on the
  screen, from the episode) → reaction (shock/relief) → sticky-note takeaway → CTA. Narration in short, flowing
  storyteller sentences (1 sentence per scene, 6–14 words), one `*highlight*` word each.
- Every command and output must be real and copied from the episode (or verified in a scratch folder);
  output lines ≤ 34 chars (split long lines). Total 30–50 s (the engine prints the timeline).
- Mix shots: at least one `eye` or `face` reaction, 2–4 `screen` beats, one `card`. Vary moods; the eyes do the acting.
- Keep it kind and professional: jokes about situations, never about people or companies; no real brands/logos.

## QA (always, before publishing)
`--sheet` and read it: banner never covers a face, text fits the monitor, captions readable and above the bottom
quarter, moods match the line being said, nothing odd (hands through objects, characters cut in half by the frame).
Then `ffprobe short.mp4`: 1080x1920, 30–58 s, aac.
