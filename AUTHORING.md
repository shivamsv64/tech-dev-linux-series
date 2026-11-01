# Authoring an episode (episodes/epNN.py)

`episodes/ep01.py` is the style reference. Copy its shape. Each file defines `EPISODE = {...}` with `number`, `scenes`, `thumb` and `upload`.

## Rules
- Target 5:30 to 8:00 total. The engine prints the timeline; add or trim steps to land in range.
- Simple English captions, at most ~22 words each, with 1–2 `*highlights*`.
- Every command and every output line must be real and correct for Ubuntu 24.04 (prompt `shivam@tech-dev`). Never invent flags or output. When unsure, use a short output you are sure of.
- Use the 8-beat template from the plan: hook cartoon → command terminal scenes with cards → combine with earlier commands → DevOps/SRE scenario (Jenkins, AWS/GCP, incidents) → common mistake (terminal `side: 'bashi'`, `error: True`) → quiz → recap with homework → outro naming tomorrow's episode.
- No "where we are" / module roadmap scene (no `chain` scene showing Module N): Shivam asked to skip it. Mention the earlier episode in a caption instead.
- Bashi (the mascot) appears in every episode: in a cartoon hook, the mistake scene and the recap.

## Scene types
| type | fields |
|---|---|
| `title` | `title` (with `*word*` in cyan), `sub`, `steps` = list of caption strings |
| `cartoon` | `side` left/right, `props` list, `steps` = dicts `{cap, say, mood, arms, props?}` |
| `stack` | `heading`, `items` [(name, line, badge)] in reveal order (bottom first), `steps` `{cap, show}` |
| `cards` | `heading`, `cards` [{icon, title, text}], `steps` `{cap, banner?}` |
| `chain` | `heading`, `nodes` (≤10), `highlight` index, `steps` = caption strings |
| `terminal` | `side` 'card' or 'bashi', optional `user`/`host`, `steps` `{cmd?, out[], cap, hl (str or list), card (title, [lines]), error?, mood/arms/say for bashi}` |
| `quiz` | `q`, `options` (4), `answer` index, `caps` [question, reveal] |
| `recap` | `heading`, `items` [(cmd, meaning)] ≤6, `steps` `{cap, homework?, extra?}` |
| `outro` | `next` (tomorrow's title), `caps` (2) |

Every scene has a `chapter` (YouTube chapter name; repeated names merge).

Moods: normal, happy, curious, panic, think, celebrate. Arms: rest, wave, point, up, head, think.
Props: ('server', x, y), ('server_fire', x, y), ('clock', cx, cy, label), ('laptop', cx, cy), ('cloud', cx, cy, label), ('alert', cx, cy), ('sparkles', (x0, y0, x1, y1)). Keep props above y = 860 (the caption area).

## Commands
- Preview: `python3 engine.py episodes/epNN.py out/epNN --stills 10,60,120,...`, then look at each still and `thumbnail.jpg`.
- Render: `python3 engine.py episodes/epNN.py out/epNN` (~8 min for a 6 min episode on 2 cores).
- Outputs: video.mp4, thumbnail.jpg, upload.json/upload.txt (title, description with chapters, tags), script.txt.
