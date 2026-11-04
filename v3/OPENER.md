# v3 look: own-voice hook opener + zine scenes (since 5 Nov 2026)

Shivam's decision (4 Nov 2026): more of his own voice at the start of every long video, narration that sounds human and
talks *to* the viewer, every video starts with a hook, and richer graphics inspired by his moodboard (newspaper front
pages, evidence boards with red string, dark halftone collage files, big condensed-type posters, his real photo).

## 1. The opener (first ~20–30 s, Shivam's own ElevenLabs voice)

Every long video starts with a Remotion-rendered cold open spoken in **Shivam's cloned voice**
(`bFB4JzmoiywTauhk6IsI`, "Shivam singh Verma"). Then the episode's `title` scene plays his fixed intro clip
("Hi, I'm Shivam Singh Verma, and welcome to Tech-dev.") and the free Kokoro narrator takes over.

### Voice budget (Shivam OK'd this on 4 Nov 2026)
- One opener per long video, **at most 350 characters**, **one take** (`generations_count: 1`), model `eleven_v4`.
  ≈ 56 long videos/month × ≤350 = ≤19.6k of the 30k monthly credits. Shorts keep using the free narrator + `voice/assets/cta.mp3`.
- Always run with `estimate_only: true` first; if the estimate is above 400 credits, shorten the text.
- Never generate test takes, never retry a generation. Record `"voice_chars": <credits>` in the series.json row.
- If ElevenLabs fails or credits are short: skip the opener (remove `'opener'` from the spec, put a `hook` scene back) and say so in the report.

### Writing the opener (hook rules)
1. **First 3 seconds = the hook**: a surprising fact, a contrast, a problem the viewer has, or a question. Never "In this video…".
2. Talk to one person ("you"), in full spoken sentences with connecting words (so, but, which means). Contractions.
3. Escalate once (why it matters / what goes wrong), then **promise the payoff** ("by the end of this video you'll know…").
4. 45–60 words, ≤350 characters. Numbers as spoken ("five years"). One mention of Shivam's real experience when it fits.
5. Only true claims. No clickbait the episode doesn't pay off.

### Generating the audio (maker step)
```
ElevenLabs connector → creative_generate_speech(prompt=<opener text>, model_id='eleven_v4', voice_id='bFB4JzmoiywTauhk6IsI',
                       generations_count=1, estimate_only=true)   # check credits, then the same call without estimate_only
creative_get_flow_run_status(...) until all_completed → download media[0].url with curl to <media dir>/vo/opener_shivam.mp3
```
(`elevenlabsusercontent.com` downloads work from the sandbox.) Word timings are made automatically with local Whisper
(`faster-whisper small.en`) and cached as `opener_shivam_words.json` next to the audio.

### The spec (`EP['opener']`)
```python
'opener': {
  'audio': 'devops-series/media/day05/vo/opener_shivam.mp3',   # repo-relative
  'text': '<exactly what he says>',
  'beats': [ {'type': 'frontpage', 'from': 0, ...}, {'type': 'dossier', 'from': '@same#2', ...}, ... ],
}
```
Times are **word anchors**: `'@word'` = when he starts saying that word, `'@word#2'` = its 2nd occurrence,
`'@word+0.4'` = 0.4 s later. Each beat lasts until the next beat's `from`. Change the picture every 2–5 s.

| beat | fields | look |
|---|---|---|
| `frontpage` | `masthead`, `date`, `left`, `headline` [{text, at}] ×1–3 (≤11 chars/line), `deck` + `deckAt`, `art`, `caption`, `stamp` {text, at} | newspaper front page, headline stamps in word by word |
| `dossier` | `kicker`, `wall` [art ×4–8], `cards` [{title, sub, color, art, at, fields [[k, v] ×≤3]}] ×1–3, `stamps` [{text, at, x, y, r}] | dark halftone collage wall with subject files; keep stamps at y≈870 (below cards, above captions) |
| `board` | `cards` [{title, at, art}] ×≤3, `labels` [{text, at, card}] (≤12 chars), `question` {text, at} | kraft evidence board, red string to handwritten notes |
| `photo` | `photo` (`photo/shivam_clasped.png` · `shivam_serious.png` · `shivam_fullbody.png`), `big` (≤8 chars), `bigAt`, `color`, `small` [3], `name`, `role` | Shivam's real photo in front of giant poster type: use it when he says "I" / his experience |
| `poster` | `lines` [{text, at, color}] ×2–3 (≤11 chars), `size`, `small` [3], `smallAt`, `art`, `bg` 'navy'/'paper' | big condensed type + brand tri-colour bars: the payoff promise |

Art paths are `art/<library or fresh FLUX art name>.jpg`. Never put brand logos, film/TV characters or real people
other than Shivam in a beat.

### Render
```
python3 v3/opener/render.py <spec.py> <outdir> --stills 1,4,8,12,16,20   # preview PNGs (look at every one)
python3 v3/opener/render.py <spec.py> <outdir>                           # -> <outdir>/opener.mp4 (~3-5 min on 2 cores)
```
Then run engine v2 as usual into the **same `<outdir>`**: it finds `opener.mp4`, puts it in front of the episode, shifts the
chapters and script.txt, and loudness-normalises both parts. Needs Node 22+, `google-chrome`, `npm install` (automatic).

### 3D opener (default since 4 Nov 2026: Shivam asked for 3D instead of the flat 2D look)
`'engine': '3d'` in `EP['opener']` → `python3 v3/opener3d/render.py <spec.py> <outdir> [--sheet | --frames t1,t2]`.
Real three.js 3D (clay-look sculpted people, soft shadows, depth of field, bloom), built from the faceless-shorts
Deep Dive 3D engine, adapted to 16:9. One world, five areas: the **ops room** (3 engineers at desks, each with a big wall
screen and a nameplate), a **server-rack aisle**, a **clay cloud** with orbiting containers, a **CI/CD conveyor** with
BUILD/TEST/DEPLOY gates, and a **photo stage** with Shivam's real cutout in front of extruded slab type.
- `roles` (3): `{label, color, screen: graph|pipeline|cost|terminal, screenLabel, skin, shirt}`; `big` (slab text, e.g. '5 YEARS'); `photo` (file in hf/assets).
- `beats` (word anchors, as above): `room` {drops [3 anchors]} · `racks` {pill} · `cloud` {pill} · `pipeline` {pill} ·
  `desk` {i, pill} · `question` {text, at} · `photo` {bigAt, name, role} · `finale` {lines [{text, at, color}] ×3, small [3], smallAt}.
  `pill` = {text, at, color}. Change the shot every 1.5–3 s.
- Software rendering (no GPU in the sandbox): ~10–15 min for a 21 s opener at 24 fps. Always check `--sheet` first.
- Keep `beats2d` (the Remotion 2D version) as a fallback: if the 3D render fails, set `'engine': '2d'` and run `v3/opener/render.py`.
- Full 9-minute episodes are NOT rendered in 3D (≈4–5 h per episode without a GPU); the body stays engine v2.

## 2. Zine scenes in engine v2 (body of the episode)

Full-frame scenes with their own paper/collage backgrounds (no `art` background needed); cuts into and out of them
are hard cuts with a short flash and whoosh. Use 3–6 per episode as pattern breaks, never two in a row.

| type | fields | use for |
|---|---|---|
| `headline` | `headline` [1–2 lines ≤14 chars], `deck`, `masthead`, `date`, `art`, `photo_caption`, `stamp`, `stamp_at`, `at` | incident stories, "what went wrong", news hooks |
| `board` | `cards` [{title, art}] ×2–3, `notes` [{text, card, at}], `question`, `question_at` | root cause, how things connect, career/learning maps |
| `dossier` | `kicker`, `wall` [arts], `cards` [{title, sub, color, art, at, fields [[k, v] ×≤4]}] ×1–3, `stamps` [{text, at, x, y, r}] | comparing roles/tools/services side by side |
| `poster` | `lines` [str or (str, color)] ×2–3, `small` [≤3], `art`, `bg`, `photo` | chapter openers ("ROLE 01 · DEVOPS") |

Field values in dossier cards: ≤12 characters (VT323 font). `at` values are fractions of the narration, like other scenes.

## 3. Narration rules (whole episode)
- Talk to the viewer: "you", questions, "pause and guess", "quick check", "comment D, S or C". One interaction every ~60–90 s.
- Open loops: promise something early ("at the end we'll check your guess") and pay it off.
- Full sentences with connecting words; contractions; no list-reading. Read it aloud in your head.
- Real experience: tell Shivam's real work stories (Jenkins CI/CD, AWS/GCP, Wiz/Qualys, on-call) in the third person
  ("in Shivam's team…") because the body narrator is not his voice.
