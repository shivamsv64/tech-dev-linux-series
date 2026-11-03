# Tech-dev Shorts (all series)

One vertical YouTube Short (1080x1920, 30–50 s) per long episode.

**Since 3 Nov 2026 every Short uses the Desk Life cartoon-skit engine: `shorts/skit.py` — read `shorts/SKIT.md`.**
Relatable situation skits with an original human cast (Rohan, Meera, Khanna sir, Tara), a situation banner on top,
music-led, free local narrator (Kokoro) + Shivam's one-time subscribe clip. No animal characters or animal voices,
no ElevenLabs, no `voice/vo.py` step. The old animal engine (`shorts.py`, `cast.py`, old `SHORT = {...}` specs) is
kept only for reference.

## Schedule (Metricool brand 7777398, Tech-Dev channel only)
The daily maker task renders the Short together with its episode and schedules it for **the next day**:
| Series | Long video | Short |
|---|---|---|
| Git & GitHub | 4:00 PM IST | next day 11:30 AM IST |
| Linux Zero to Hero | 5:00 PM IST | next day 12:30 PM IST |
| DevOps & SRE Zero to Hero | 8:00 PM IST | next day 1:30 PM IST |
Metricool `youtubeData.type` = `"short"`, title ends with `#shorts`.

## Daily maker step (run after today's long episode is scheduled)
1. Write `shorts/specs/<id>.py` (id = `linux-epNN`, `git-epNN` or `devops-dayNN`) with a `SKIT = {...}` spec following
   `shorts/SKIT.md`: a relatable situation banner, scene 1 = the hook, the episode's key command(s) with real output on
   `screen` shots (copied from the episode), a reaction beat (`eye`/`face`/`phone`), the common mistake + fix when the
   episode has one (`!` error line + `badge`), and a sticky-note `card` takeaway. Style reference: `shorts/specs/linux-ep03-skit.py`.
   `upload`: title "<situation hook, ≤60 chars> #shorts #<linux|git|devops>", description = 1–2 lines +
   'Full episode: "<long title>" on the Tech-dev channel.' + schedule line + hashtags starting with #shorts; 10–14 tags.
2. Preview: `python3 shorts/skit.py shorts/specs/<id>.py out/short-<id> --sheet`, read `sheet.jpg` (and `--stills` for
   any frame you want full size), fix problems. Render without flags. ffprobe: 1080x1920, 30–58 s, aac.
3. Copy `short.mp4, cover.jpg, upload.json, upload.txt` to the series' shorts media folder, commit + push, check the raw URL returns 200.
4. Metricool (only after the channel-safety check): same post shape as the long video, but `date` = **tomorrow** at the series' Short time (table above), `media` = [short URL], NO `videoThumbnailUrl`, `youtubeData.type` = "short", `youtubeData.isAiGeneratedContent` = true, title/description/tags from the Short's upload.json.
5. Add `"short": {"status": "scheduled", "title", "live", "metricool_id", "planner", "engine": "skit"}` to today's series.json row; commit + push.
If the Short fails, the long episode still comes first: finish and report it, and say what failed with the Short.
