# Voices for Tech-dev videos — free by default

> **Policy (Shivam, 1 Nov 2026):** ElevenLabs credits are scarce (30,000/month) and must last the whole month.
> **No ElevenLabs generation in the daily tasks.** All narration is free and local (Kokoro, `v2/tts.py`).
> Shivam's own cloned voice (`bFB4JzmoiywTauhk6IsI`) appears only through two one-time clips that are reused forever:
> - `v2/assets/voice/intro_shivam.mp3` — "Hi, I'm Shivam Singh Verma, and welcome to Tech-dev." (long videos, title scene with `'intro': True`)
> - `voice/assets/cta.mp3` — "Watch the full episode on Tech-dev, and subscribe!" (end of every Short)
> Generating any new ElevenLabs audio needs Shivam's explicit OK in chat.

## Long videos (engine v2)
`v2/engine.py` narrates every scene's `say` with Kokoro (voice `am_michael`) and mixes the intro clip in. Nothing to do here.

## Shorts (daily maker step)
1. `python3 voice/vo.py plan <series> <long_out>/script.txt shorts/specs/<short-id>.py out/vo-<id>` → plan.json (hook + one key line).
2. `python3 voice/vo.py kokoro out/vo-<id>` → synthesizes those lines locally (free). Character lines get their own Kokoro voice.
3. `python3 voice/vo.py manifest out/vo-<id>` → manifest.json (includes `voice/assets/cta.mp3`).
4. Render the Short with `--vo out/vo-<id>/manifest.json`.
5. Record `"voice_chars": 0` (ElevenLabs) in the series.json row.

`vo.py mix-long` is no longer needed (engine v2 already narrates the long video).
