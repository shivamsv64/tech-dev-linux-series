# Git & GitHub: Beginner to Advanced: maker (v3), Mon/Wed/Fri
Read `v3/makers/COMMON.md` first; this file holds the Git values. Repo: shivamsv64/tech-dev-git-series (add_repo access "push"; shallow clone, generous timeout; it is self-contained: the v3 engine, fonts, photos and these files are copied into it).
For the voice-budget gate you also need the other two trackers: read them with curl from raw.githubusercontent.com (`shivamsv64/tech-dev-linux-series` `devops-series/series.json` and `series.json`) instead of cloning.
Runs Mon/Wed/Fri 1:37 PM IST. Episode goes live **today 4:00 PM IST**; its Short **tomorrow 11:30 AM IST**.

## Setup
1. `TZ=Asia/Kolkata date`. Today's episode N = the LOWEST-numbered row in `series.json` whose status is not "scheduled" (PLAN.md order). All 15 scheduled: list scheduled tasks, disable
   "Tech-dev Git episode + Short (engine v2, Mon/Wed/Fri, live 4 PM IST)", send "Git series complete", stop. A row already scheduled TODAY with a "short": stop; without "short": skip to the Short.
2. `pip install --break-system-packages pillow numpy scipy soundfile kokoro-onnx faster-whisper`.
3. Read `v3/OPENER.md`, `v3/STYLES.md`, `v2/AUTHORING.md`, `v2/examples/git-sample.py`, `PLAN.md`, `series.json`, the latest `episodes-v2/epNN.py`, `shorts/README.md`, `shorts/SKIT.md`. (The v3 reference episode `devops-series/episodes-v2/day05.py` lives in the Linux repo: fetch it with curl from raw.githubusercontent.com if you want to see a full spec.)
4. Hygiene: `git rm` `media/epNN/video.mp4` (and opener.mp4) for earlier scheduled episodes whose 4 PM time passed, and `media/shorts/git-epNN/short.mp4` for earlier Shorts whose live time passed.

## Make the episode
Paths: spec `episodes-v2/epNN.py`; out `out/epNN`; media `media/epNN/` (opener audio in `vo/`). Series values: `'series': 'git'`, `'number': N`, `'badge': 'EP N'`, `'badge_long': 'EPISODE N'`. Look: Isometric City (city_* arts: city_rail branches, city_post staging/commits, city_clock undo/history, city_archive repos/logs) + zine scenes + opener.
Shape (COMMON.md 3): opener -> title (intro True) -> short recap + quiz reveal -> concept with the PLAN real-life analogy -> hands-on terminal scenes for every command in the PLAN row (each key flag its own step, realistic output, a `note` card) -> "what Git does inside" scene -> common mistake (lines starting with ! are red) + fix -> DevOps example from Shivam's world (Jenkins CI/CD, AWS/GCP, production rollbacks) as a pipeline plus a terminal scene -> interview corner -> quiz (answer None) -> recap + homework -> outro naming the next episode with cta 'New episodes Mon, Wed & Fri · 4 PM IST' (Ep 15: 'Full playlist on the channel').
Double-check every Git command and output in a scratch repo; terminal lines <=60 chars with a note, <=95 without; no tab characters. Opener: 2D styles (newsroom incident, board for branches) or 3D when it fits; a problem-first hook ("you just committed to main by mistake...").
`upload` title: `<Topic or problem-first hook, <=60 chars> | Git & GitHub Ep N`; thumb big = main command or 2-3 big words; 12-15 tags.
GitHub Releases are NOT permitted for this session.

## Publish
Copy `{video.mp4,thumbnail.jpg,upload.json,upload.txt,script.txt}` into `media/epNN/`; commit with the spec; push. Raw URLs `https://raw.githubusercontent.com/shivamsv64/tech-dev-git-series/main/media/epNN/video.mp4` and `.../thumbnail.jpg` must return 200. Metricool: date `<today>T16:00:00+05:30`, type video.
HANDOFF key `TD-git-epNN` -> `media/epNN/TD-git-epNN.mp4`. Update Ep N's row: status "scheduled", date (today), video_url, planner, metricool_id, engine "v2", `voice_chars`, `opener`. Run `python3 build_hub.py`, commit + push, then republish the tracker page with the Artifact tool (action publish, url https://claude.ai/artifact/Tgx9qpy6sX3n8BDQTRbgbu, file_path hub/index.html; read the artifact first if required; omit capabilities).

## The Short
Spec `shorts/specs/git-epNN.py`, `'series': 'git'`, `'tag': 'EP N'`, hook in his voice (COMMON.md 4). Out `out/short-git-epNN`; media `media/shorts/git-epNN/` with `{short.mp4,cover.jpg,upload.json,upload.txt,hook_shivam.mp3}`.
Title `<situation hook, <=60 chars> #shorts #git`; description schedule line 'New episodes Mon, Wed & Fri, 4 PM IST' (Ep 15: 'Full playlist on the channel'). Metricool: TOMORROW `11:30:00+05:30`, type short. HANDOFF key `TD-git-epNN-short` -> `media/shorts/git-epNN/TD-git-epNN-short.mp4`.
Add the "short" object to Ep N's row (with `voice_chars`); commit + push. Then the report (COMMON.md 7).
