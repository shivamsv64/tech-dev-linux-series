# Authoring a day (devops-series/episodes/dayNN.py)

`episodes/day01.py` is the style reference. Each file defines `EPISODE = {...}` with `number`, `scenes`, `thumb`, `upload`.

## Rules
- Target **7:00 to 10:00** (phase projects up to 15:00). The engine prints the timeline; add or trim steps to land in range.
- Simple English captions, at most ~22 words, with 1–2 `*highlights*`. Bubbles (`say`) are short: 2–6 words.
- Every command and output must be real and correct (Ubuntu 24.04, prompt `shivam@tech-dev`, or `ubuntu@ip-172-31-x-x` for EC2). Never invent flags or output; when unsure use a short output you are certain of, or show a file whose content you wrote.
- No brand mascots or logos (no whale, penguin, gopher, octocat). Tools are named in text only.
- 9-beat template:
  1. **Cold open** cartoon: Kaalu the Crow breaks something tied to today's topic, Kukdu (or the lead) reacts.
  2. **Title** scene (`cast` = 1–3 characters), 2–3 caption steps: Day N of 100, 8 PM IST, today's promise.
  3. **Recap** of yesterday + quiz answer (cartoon with Mitthu, or cards). Skip on Day 1 only.
  4. **Concept**: cards / stack / chain, with the lead's animal analogy in a cartoon.
  5. **Hands-on**: `terminal` scenes (side `card` for command cards, or `animal` with the lead character).
  6. **Real-world story** from DevOps/SRE work (Jenkins CI/CD, AWS EC2/GCP, incidents, compliance scans) as a cartoon.
  7. **Interview corner** (`qa`): one real interview question + a 2–3 line model answer.
  8. **Quiz** (Mitthu) → answer revealed in tomorrow's recap.
  9. **Recap** (`plain: True` for concept words) with homework, then **outro** naming tomorrow's PLAN.md episode.

## Cast (who key → character, owns)
| key | character | owns | voice |
|---|---|---|---|
| `ollie` | Ollie the Owl | concepts, recaps, the "why" | soft hoots |
| `mitthu` | Mitthu the Parrot | commands, quiz, "Mitthu says…" | squawky chirps |
| `bablu` | Bablu the Beaver | CI/CD, Terraform, Ansible, building | squeaky chatter, tail slap |
| `gajju` | Gajju the Elephant | Git history, logs, storage, state, interview corner | low brassy rumble, trumpet |
| `ashtu` | Ashtu the Octopus | containers, Kubernetes, Helm | bubbly blubs |
| `kukdu` | Kukdu the Rooster | monitoring, alerts, on-call, SLOs | nasal, cock-a-doodle-doo |
| `kaalu` | Kaalu the Crow (villain) | bugs, outages, attackers, misconfigs | harsh caws |
| `tortoise`, `cheetah` | guests | slow manual vs fast automated | |

Each character's signature call plays automatically the first time it appears in an episode; every `say` line plays
animal-gibberish speech in that character's voice with mouth movement. To add a guest animal (pigeon, honeybee,
squirrel, ant…), add a `draw_<key>` function + `VOICE`/`_syll`/`call` entries in `cast.py`, and check a character sheet.

## Scene types
| type | fields |
|---|---|
| `title` | `title` (`*word*` in cyan), `sub`, `cast` [keys], `steps` = strings or `{cap, say}` (first cast member speaks) |
| `cartoon` | `cast` [(key, x)], optional `h` (default 520; 330 for 7 characters), `props`, `moods` {key: mood}, `steps` = `{who, cap, say, mood, arms, moods?, props?}` |
| `stack` | `heading`, `host`, `items` [(name, line, badge)] bottom-first, `steps` `{cap, show, say?}` |
| `cards` | `heading`, `cards` [{icon, title, text}] (1–4), `steps` `{cap, banner?}` |
| `chain` | `heading`, `nodes` (≤10, ≤20 chars each), `highlight`, `you_are_here` (bool), `steps` = strings |
| `terminal` | `side` `card` or `animal` + `who`, `steps` `{cmd?, out[], cap, hl, card (title, [lines]), error?, say, mood, arms}` |
| `qa` | `host` (default gajju), `q`, `a` [2–3 lines], `steps` `{cap, reveal, say?}` |
| `quiz` | `host` (default mitthu), `q`, `options` (4, ≤18 chars), `answer`, `caps` [question, reveal] |
| `recap` | `heading`, `host`, `plain`, `items` [(word, meaning ≤22 chars)] ≤6, `steps` `{cap, homework?, say?}` |
| `outro` | `next` (tomorrow's title), `caps` (2) |

Every scene has a `chapter`. Moods: normal, happy, curious, panic, think, celebrate, angry, sly (Kaalu's default).
Arms/wings: rest, wave, point, up, think. Props: ('server', x, y), ('server_fire', x, y), ('clock', cx, cy, label),
('laptop', cx, cy), ('cloud', cx, cy, label), ('alert', cx, cy), ('sparkles', (x0, y0, x1, y1)). Keep props above y = 860
and away from where speech bubbles appear (top 110–340 px beside the speaker).

`thumb`: `big` (≤8 chars), `lines` (2 short), `who` (lead character), `mood`, `arms`.
`upload`: `title` ("<Topic hook> | DevOps & SRE Zero to Hero Day N"), `hook`, `learn` [], `commands` [], `interview`,
`quiz`, `homework`, `next`, `question`, `hashtags` (#DevOps #SRE #DevOpsZeroToHero #CloudComputing #TechDev + topic), `tags` (14–16).

## Commands
- Preview: `python3 engine.py episodes/dayNN.py out/dayNN --stills 10,60,...` then look at each still and `thumbnail.jpg`.
- Render: `python3 engine.py episodes/dayNN.py out/dayNN` (~10 min for 7 min on 2 cores). Audio is loudness-normalized to −16 LUFS.
- Outputs: video.mp4, thumbnail.jpg, upload.json / upload.txt, script.txt.
