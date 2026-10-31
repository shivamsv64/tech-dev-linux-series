# ElevenLabs voices (all Tech-dev series, credit-capped)

Shivam's ElevenLabs plan: **30,000 credits/month**, about **1 credit per character** on every model.
So voices go only where they matter, with a hard cap of **250 characters per series per day**
(3 series → ≤ 750/day → ≤ ~22.5k/month, leaving a buffer). Everything else stays captions + animal sounds.

What gets a human voice each day, per series:
| Line | Voice | Max chars |
|---|---|---|
| Long video: intro line (first caption, spoken at its time) | narrator | 90 |
| Short: hook | narrator | 80 |
| Short: one key beat (the beat with `'voice': True`, else the first beat) | that beat's character | 80 |
| Short: closing "Watch the full episode on Tech-dev, and subscribe!" | narrator | one-time clip `voice/assets/cta.mp3`, reused forever |

Cast (original voices, not modelled on any real actor or existing cartoon character): see `voices.json`.
Narrator = deep, confident Indian English with filmy-hero energy; each animal has its own cartoon-style voice.

## Rules
- `generations_count: 1`, model `eleven_flash_v2_5`. **Never** retry a generation call, never make test takes or previews (each call spends credits).
- Only voice lines that ship in a YouTube video. If anything fails, publish without voice rather than spending more.

## Daily procedure (inside the maker task, after the long video is rendered and the Short spec is written)
1. `python3 voice/vo.py plan <series> out/<id>/script.txt shorts/specs/<short-id>.py out/vo-<id>` → prints the plan (≤ 3 lines, ≤ 250 chars, voice ids, output paths).
2. For each line in `lines` (and the CTA only if `cta.exists` is false): ElevenLabs `creative_generate_speech` with `prompt` = the line's text exactly, `voice_id`, `model_id` = plan model, `generations_count` = 1. Poll `creative_get_flow_run_status` (wait `poll_after_seconds`) until done, then `curl -sS -o <path> "<generations[0].content_url>"`. A new CTA clip is saved to `voice/assets/cta.mp3` and committed.
3. `python3 voice/vo.py manifest out/vo-<id>` → writes `manifest.json` for the Short.
4. Long video: `python3 voice/vo.py mix-long out/<id>/video.mp4 out/vo-<id>/long_intro.mp3 <at from plan> out/<id>/video_vo.mp4`, check it with ffprobe, then use `video_vo.mp4` as the published `video.mp4`.
5. Short: render with `--vo out/vo-<id>/manifest.json` (the engine lengthens beats to fit the voice and mutes the animal gibberish on voiced beats).
6. Record `"voice_chars": <plan chars>` in the series.json row.
