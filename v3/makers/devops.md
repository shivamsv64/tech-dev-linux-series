# DevOps & SRE Zero to Hero: daily maker (v3)
Read `v3/makers/COMMON.md` first; this file holds the DevOps values. Repo: shivamsv64/tech-dev-linux-series (add_repo access "push"; `git clone --depth 1 --filter=blob:limit=5m`, generous timeout).
Runs daily 3:41 PM IST. Episode goes live **today 8:00 PM IST**; its Short **tomorrow 1:30 PM IST**.

## Setup
1. `TZ=Asia/Kolkata date`. Day N = days since 2026-11-01 + 1 (Day 1 = 1 Nov 2026, Day 100 = 8 Feb 2027). Today's episode = the `devops-series/series.json` row whose date is today. No row (series finished): list scheduled tasks, disable the one named
   "Tech-dev DevOps Zero to Hero episode + Short (engine v2, daily, live 8 PM IST)" (update_trigger enabled=false), send "DevOps series complete", stop. If the row is already "scheduled" and has a "short": stop; scheduled without "short": skip to the Short.
2. `pip install --break-system-packages pillow numpy scipy soundfile kokoro-onnx faster-whisper` (ffmpeg, node 22 and google-chrome are present). First engine run downloads the free voice (~350 MB).
3. Read `v3/OPENER.md`, `v3/STYLES.md`, `v2/AUTHORING.md`, `v2/examples/devops-sample.py`, `devops-series/PLAN.md`, `devops-series/series.json`, the latest `devops-series/episodes-v2/dayNN.py`, `devops-series/episodes-v2/day05.py` (v3 reference), `shorts/README.md`, `shorts/SKIT.md`.
4. Hygiene: delete `devops-series/media/dayNN/video.mp4` (and `opener.mp4`) for earlier scheduled days whose live time passed; delete `devops-series/media/shorts/dayNN/short.mp4` for earlier Shorts whose live time passed.

## Make the episode
Paths: spec `devops-series/episodes-v2/dayNN.py`; scratch out `devops-series/out/dayNN`; media `devops-series/media/dayNN/` (opener audio in `vo/`). Series values: `'series': 'devops'`, `'number': N`, `'badge': 'DAY N/100'`, `'badge_long': 'DAY N OF 100'`.
Look: Mission Control (mc_* arts) + zine scenes + 3D/2D opener. Phase 2 (Linux) episodes point to the sister series "Linux Zero to Hero" for deeper command coverage.
**Day 5 is pre-made**: if `episodes-v2/day05.py` already exists with an `opener` and `vo/opener_shivam.mp3`, do NOT rewrite it: copy `devops-series/media/day05/opener.mp4` into `devops-series/out/day05/` (skip the opener render), then preview, fix, render the body, publish. Only if `opener.mp4` is missing, render it (3D).
For every other day, follow COMMON.md section 3 and the shape: opener (his voice) -> title (intro True) -> short recap + quiz reveal -> concept scenes -> hands-on terminal scenes -> real work story (Jenkins CI/CD, AWS EC2/GCP, incidents, Wiz/Qualys, on-call) -> mistake + fix -> interview corner -> quiz (answer None) -> recap + homework -> outro naming tomorrow's PLAN row.
Fill `thumb` and `upload`: title `<problem/outcome hook, <=60 chars> | DevOps & SRE Zero to Hero Day N`, hook, learn bullets, commands, interview, quiz, homework, next, question, hashtags, 14-16 tags. Use `devops-series/media/dayNN/thumbnail_custom.jpg` and art made by the Hugging Face prep task when present (the engine reads them).

## Publish
Copy `{video.mp4,thumbnail.jpg,upload.json,upload.txt,script.txt}` from the out dir into the media dir (re-encode with libx264 -crf 24 if video.mp4 > 95 MB, copy audio). Commit with the spec and push. Check raw URLs return 200:
`https://raw.githubusercontent.com/shivamsv64/tech-dev-linux-series/main/devops-series/media/dayNN/video.mp4` and `.../thumbnail.jpg`. Metricool (COMMON.md 5-6): date `<today>T20:00:00+05:30`, type video, category EDUCATION.
HANDOFF key `TD-devops-dayNN` -> file `devops-series/media/dayNN/TD-devops-dayNN.mp4` (instead of video.mp4). Then update the series.json row: status "scheduled", title, live, planner, metricool_id, engine "v2", `voice_chars` (opener credits), `opener` "3d"|"2d". Commit + push.

## The Short
Spec `shorts/specs/devops-dayNN.py` (`SKIT`, style reference `shorts/specs/linux-ep03-skit.py`), `'series': 'devops'`, `'tag': 'DAY N'`, hook in his voice (COMMON.md 4). Out `out/short-devops-dayNN`; media `devops-series/media/shorts/dayNN/` with `{short.mp4,cover.jpg,upload.json,upload.txt,hook_shivam.mp3}`.
Title `<situation hook, <=60 chars> #shorts #devops`. Metricool: date TOMORROW `13:30:00+05:30`, type short, no thumbnail. HANDOFF key `TD-devops-dayNN-short` -> `devops-series/media/shorts/dayNN/TD-devops-dayNN-short.mp4`.
Add `"short": {"status","title","live","metricool_id","planner","engine":"skit","voice_chars"}` to the row; commit + push. Then the report (COMMON.md 7).
