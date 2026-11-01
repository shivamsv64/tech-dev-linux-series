# Engine v2 — how to write an episode

Engine v2 replaced the animal-cast engines on 2 Nov 2026 for all long videos (DevOps, Linux, Git).
Looks: **Mission Control** (DevOps & SRE) and **Isometric City** (Linux, Git). Every scene is narrated
(free Kokoro voice) with synced captions, illustrated backgrounds with slow camera moves, animated
overlays and a music bed. **No ElevenLabs credits are used per episode.**

```
pip install --break-system-packages pillow numpy scipy soundfile kokoro-onnx   # ffmpeg required
python3 v2/engine.py <spec.py> <outdir> --stills 10,60,120,...   # narrates (cached) + stills + thumbnail + upload files
python3 v2/engine.py <spec.py> <outdir>                           # full render -> video.mp4 (run with nohup, poll for DONE)
```
First run downloads the voice model (~350 MB, from GitHub) to `~/.cache/kokoro`. Narration is cached in
`<outdir>/vo/`, so re-running after a fix only re-renders frames. Render speed ≈ 1.3 min per minute of
video on 2 cores (JOBS=2), plus ~1 min of narration per minute of video on the first run.

Style references: `v2/examples/devops-sample.py` (Mission Control) and `v2/examples/git-sample.py` (City).

## Spec file
```python
EP = {
  'series': 'devops' | 'linux' | 'git',          # picks look, show name and description line
  'number': 2, 'badge': 'DAY 2/100', 'badge_long': 'DAY 2 OF 100',   # Linux/Git: 'EP 3' / 'EPISODE 3'
  'scenes': [ {...}, ... ],
  'thumb':  {...}, 'upload': {...},
}
```
Every scene needs `type` and `say`. Common optional keys:
- `say` — the narration, plain spoken English (it is also the caption). Wrap 1–2 key words per scene in `*stars*` to highlight them in amber.
  Write numbers and symbols the way they should be spoken ("set minus e", "dot git folder", "ten days").
- `art` — background name from the library below. Consecutive scenes with the same art share one continuous camera move (no crossfade); a new art crossfades with a whoosh.
- `cam` — `push` `pull` `left` `right` `up` `down` `still` (use `still` for terminal scenes). `focus` — (fx, fy) start point, default (0.55, 0.5).
- `chapter` — starts a YouTube chapter here (keep chapters ≥ 10 s apart; the first becomes 0:00).
- `hold` — extra seconds after the narration (e.g. 1.5 on a terminal scene with long output). `vig` — `left|right|top|dim|none` legibility shading.
- `intro: True` — on the **title** scene only: plays Shivam's own recorded "Hi, I'm Shivam Singh Verma, and welcome to Tech-dev." before the narration.

### Scene types
| type | fields | use for |
|---|---|---|
| `hook` | `label`, `line`, `stats` [(big, small, color) ×1–3], `punch` | cold open with a striking number or problem |
| `title` | `title` [line1, line2], `sub`, `kicker` (default show name), `badge` (default badge_long), `intro` | episode title, always 2nd scene |
| `timeline` | `label`, `stations` [(name, sub) ×3–6], `step` (index lit now), `counter` {label, from, to, unit, suffix, alarm}, `alert` {title, text}, `color` | processes, request paths, release flows. Repeat the scene with step+1 and the **same label** to walk through it — the panel stays put |
| `pipeline` | `label`, `nodes` [3–5 short words], `mode` build/flow, `fail` (index → red ✗), `note`, `swap` {label, old, new, sub} | CI/CD stages, data flows, "a failing test stops the release" |
| `terminal` | `steps` [{cmd, out [lines], prompt, at}], `title`, `prompt`, `note` {label, title, text, cmd, at} | hands-on commands. Output prefixes: `!` red error, `+` green success, `#` grey comment. Lines ≤ 60 chars with a note, ≤ 95 without |
| `bullets` | `label`, `title`, `items` [str or (tag, text, color)] ×2–6, `side` left/right, `at` | key points, incident timelines with time tags, cheat-sheets |
| `compare` | `label`, `cols` [2–3 headers], `rows` [(label, a, b[, c]) ×2–6] | X vs Y vs Z |
| `bars` | `label`, `bars` [(name, fraction 0–1, color, value)], `punch` | proportions: wait vs work, cost, latency |
| `chips` | `label`, `chips` [≤12 short strings], `bad` (index turns red), `punch` | many small things: commits, pods, servers, files |
| `swap` | `label`, `old`, `new`, `sub` | before → after numbers |
| `qa` | `question`, `points` [2–4], `label` | interview corner |
| `quiz` | `question`, `options` [2–4], `answer` (index, or None = "answer in the comments") | daily quiz |
| `statement` | `kicker`, `text`, `sub` | one big idea, recap, warning, homework |
| `outro` | `kicker`, `next` [1–2 lines], `cta` | last scene: next episode + subscribe (keeps the right half clear for end-screen elements) |

Colors: `accent`, `warm`, `ok`, `bad`, `purple`, `muted`.

### Art library (`v2/assets/art/`)
**Mission Control (DevOps & SRE):** `mc_room` control room (hook/title/outro) · `mc_pad` launch pad with checkpoints (processes, waiting, gates) ·
`mc_alert` red-alert console (incidents, midnight deploys, failures) · `mc_pipe` automated launch line (CI/CD, pipelines) · `mc_servers` data-center aisle (Linux, servers) ·
`mc_cloud` orbital station modules (cloud, AWS/GCP, scaling) · `mc_containers` cargo bay of containers (Docker, Kubernetes) · `mc_monitor` monitoring wall (SRE, SLOs, observability) ·
`mc_incident` war-room table (postmortems, on-call) · `mc_terminal` engineer workstation (terminal scenes) · `mc_security` vault airlock (security, Wiz/Qualys, IAM) ·
`mc_network` star-map network (networking, DNS, load balancing) · `mc_blueprint` hologram blueprint (architecture, IaC, Terraform) · `mc_sunrise` observation deck sunrise (recap, wins).

**Isometric City (Linux & Git):** `city_hero` tech city (hook/title/outro) · `city_jam` trucks stuck at toll booths (queues, waiting, bottlenecks) · `city_night` office at midnight (outages, mistakes) ·
`city_fast` express highway (automation, speed) · `city_terminal` developer workshop (terminal scenes) · `city_archive` archive library (filesystem, history, logs) ·
`city_rail` railway junction (branches, merges, rebase) · `city_servers` server district (servers, processes, services) · `city_post` post-office sorting (staging, commits, pipes, packages) ·
`city_build` construction site (scripts, building, install) · `city_vault` vault (permissions, users, secrets, .gitignore) · `city_tower` control tower (monitoring, systemd, cron) ·
`city_clock` clock tower (log, reset, revert, undo) · `city_class` rooftop classroom (quiz, interview, recap).

Use at least 6 different arts per episode and don't stay on one art for more than ~60 s.

### Thumbnail and upload
```python
'thumb': {'art': 'mc_alert', 'big': '10 DAYS', 'lines': ['to ship a', '10-minute fix?'], 'badge': 'DAY 2', 'color': 'bad', 'chip': '$ ls -la'},
'upload': {'title', 'hook', 'learn' [..], 'commands' [..], 'interview', 'quiz', 'homework', 'next', 'question', 'hashtags' [..], 'tags' [12–16]},
```
`big` ≤ 10 characters, 2 short `lines`, optional `chip` (a command, for Linux/Git). The busy side of the art is kept on the right automatically.

## Episode shape (7–10 min = roughly 45–70 scenes, each 5–15 s)
hook → title (`intro: True`) → recap of the last episode (reveal its quiz answer) → concept (timeline / pipeline / bullets / compare) →
hands-on terminal scenes for every command in the plan, each key flag its own step → real-world DevOps/SRE story from Shivam's work
(Jenkins CI/CD, AWS EC2/GCP, incidents, Wiz/Qualys scans, on-call) → common mistake and its fix → interview corner (`qa`) → `quiz` →
recap `statement` with homework → `outro` naming the next episode.

Rules: one idea per scene; `say` 1–3 sentences (~12–40 words); commands and outputs must be real and correct (Ubuntu 24.04,
`shivam@tech-dev` prompt; run them in a scratch folder when unsure); no animal characters, no brand mascots.

## Checking before the full render
Render 10–12 stills at the busiest moments and look at them: text overflow, panels covering captions (content must stay above y≈880),
terminal lines cut off, empty-looking scenes. Check the printed total length. Then render and verify with ffprobe (1920x1080, aac, duration).
