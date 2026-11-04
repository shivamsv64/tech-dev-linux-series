# Linux Zero to Hero: maker (v3), Tue/Thu/Sat
Read `v3/makers/COMMON.md` first; this file holds the Linux values. Repo: shivamsv64/tech-dev-linux-series (add_repo access "push"; shallow clone, generous timeout).
Runs Tue/Thu/Sat 2:23 PM IST. Episode goes live **today 5:00 PM IST**; its Short **tomorrow 12:30 PM IST**.

## Setup
1. `TZ=Asia/Kolkata date`. Today's episode N = the LOWEST-numbered row in `series.json` "episodes" whose status is not "scheduled" (PLAN.md order; PLAN dates are no longer air dates). All 45 scheduled: list scheduled tasks, disable
   "Tech-dev Linux episode + Short (engine v2, Tue/Thu/Sat, live 5 PM IST)", send "Linux series complete", stop. A row already scheduled TODAY with a "short": stop; without "short": skip to the Short.
2. `pip install --break-system-packages pillow numpy scipy soundfile kokoro-onnx faster-whisper`.
3. Read `v3/OPENER.md`, `v3/STYLES.md`, `v2/AUTHORING.md`, `v2/examples/git-sample.py` (terminal-heavy City style), `PLAN.md`, `series.json`, the latest `episodes-v2/epNN.py`, `devops-series/episodes-v2/day05.py` (v3 reference), `shorts/README.md`, `shorts/SKIT.md`.
4. Hygiene: `git rm` `media/epNN/video.mp4` (and opener.mp4) for earlier scheduled episodes whose live time passed, and `media/shorts/linux-epNN/short.mp4` for earlier Shorts whose live time passed.

## Make the episode
Paths: spec `episodes-v2/epNN.py`; out `out/epNN`; media `media/epNN/` (opener audio in `vo/`). Series values: `'series': 'linux'`, `'number': N`, `'badge': 'EP N'`, `'badge_long': 'EPISODE N'`. Look: Isometric City (city_* arts) + zine scenes + opener.
Shape (COMMON.md 3): opener -> title (intro True) -> short recap + quiz reveal -> terminal scenes for each command and key flag (each flag its own step, with a `note` card) -> "combine it" scene with earlier commands -> DevOps/SRE scenario from Shivam's world (Jenkins CI/CD, AWS EC2/GCP VMs, incidents) -> mistake (output lines starting with ! are red) + fix -> interview corner -> quiz (answer None) -> recap + homework -> outro naming the next PLAN row with cta 'New episodes Tue, Thu & Sat · 5 PM IST'.
Commands and outputs real for Ubuntu 24.04 (prompt shivam@tech-dev or ubuntu@ip-172-31-x-x for EC2; set each step's `prompt` after a cd); terminal lines <=60 chars with a note, <=95 without. No "where we are" roadmap scene. Opener: prefer the 2D styles or the 3D "desk" beats with a terminal screen role; a problem-first hook ("your disk is 100% full at 2 AM...").
`upload` title: `<Command or problem-first hook, <=60 chars> | Linux Zero to Hero Ep N`; thumb big = the main command (2 short lines), chip like "$ ls -la"; 14-16 tags.

## Publish
Copy `{video.mp4,thumbnail.jpg,upload.json,upload.txt,script.txt}` into `media/epNN/`; commit with the spec; push. Raw URLs `https://raw.githubusercontent.com/shivamsv64/tech-dev-linux-series/main/media/epNN/video.mp4` and `.../thumbnail.jpg` must return 200. Metricool: date `<today>T17:00:00+05:30`, type video.
HANDOFF key `TD-linux-epNN` -> `media/epNN/TD-linux-epNN.mp4`. Update the "episodes" row: status "scheduled", title, live, planner, metricool_id, engine "v2", `voice_chars`, `opener`. Commit + push.

## The Short
Spec `shorts/specs/linux-epNN.py`, `'series': 'linux'`, `'tag': 'EP N'`, hook in his voice (COMMON.md 4). Out `out/short-linux-epNN`; media `media/shorts/linux-epNN/` with `{short.mp4,cover.jpg,upload.json,upload.txt,hook_shivam.mp3}`.
Title `<situation hook, <=60 chars> #shorts #linux`; description schedule line 'New Linux episodes Tue, Thu & Sat at 5 PM IST'. Metricool: TOMORROW `12:30:00+05:30`, type short. HANDOFF key `TD-linux-epNN-short` -> `media/shorts/linux-epNN/TD-linux-epNN-short.mp4`.
Add the "short" object to the row (with `voice_chars`); commit + push. Then the report (COMMON.md 7).
