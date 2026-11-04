# v3 graphics styles: which look for which moment
Shivam's moodboard (4 Nov 2026) adds these looks to the earlier 3D ops room and 2D engine. Mix and match by situation; change the look at least every 60-90 s inside a long video. Take the STYLE only: no brands, logos, film/TV characters or real people (other than Shivam) in anything we render.

| situation | style | how to make it | status |
|---|---|---|---|
| incident, outage, "what went wrong", a shocking number | **Newsroom front page** (cream newsprint, huge condensed headline stamped word by word) | zine scene `headline`; opener beat `frontpage` | built |
| root cause, how pieces connect, mysteries, learning maps | **Evidence board / hand-drawn mind map** (kraft paper, tape, red string, scribbled notes, "?" and arrows) | zine scene `board`; opener beat `board` | built |
| comparing roles / tools / services side by side, threat files | **Dark halftone dossier** (black collage wall, subject-file cards, stamps) | zine scene `dossier`; opener beat `dossier` | built |
| chapter openers, big claims, "ROLE 01", the payoff promise | **Poster type** (giant condensed letters, brand tri-colour bars, photo of Shivam when he says "I") | zine scene `poster`; opener beats `poster`, `photo` | built |
| the team, the day in the life, pipelines, cloud, cost | **3D ops room** (clay-look people at desks, wall screens, racks, cloud, conveyor pipeline, photo stage) | `'engine': '3d'` opener (`v3/opener3d`) | built (opener only) |
| big numbers: SLO, DORA, cost, benchmarks | **Deck UI** (white/navy cards on a blue-violet gradient, huge numerals, small labels) | zine scene `deck` (kicker, title, tag, alt, cards [{big,label,sub,color,at}] x1-4, count-up numbers); Shorts shot `statcard` | built |
| "how it works inside" concept art, kernel, containers, security | **Engraved mechanical** (cream / teal / rust line illustrations of gears, circuits, skulls on near-black) | fresh FLUX art for the series arts, prompt: "vintage engraved flat illustration of <concept> built from gears and circuit traces, cream teal and rust on near-black, no text, no logos" | art direction |
| hardware, boot, network, storage, Linux internals | **Macro hardware** (dark circuit-board macro, shallow depth of field, teal and pink bokeh) | fresh FLUX art: "macro photo of <server board / disk / cable>, shallow depth of field, teal and pink bokeh, dark, no text" as `mc_*` / `city_*` backgrounds | art direction |
| calm explainers, on-call story, outros, "slow days" moments | **Cozy desk** (warm lamp light, plants, string lights, monitor with a soft wallpaper) and **moody dark desk** (laptop on a glossy white desk, one lamp) | planned: 3D desk world (extend `v3/opener3d/src/core/ops.js`); until then FLUX art "cozy home office desk, warm lamp, plants, string lights, no text, no people" | planned |
| Shorts hook / stat (vertical) | **Hook card** (giant stacked condensed words, navy or paper, tri-colour bars, red stamp) and **Stat card** (white card, count-up number, blue-violet gradient) | Shorts shots `hookcard`, `statcard` in `shorts/skit.py` | built |
| story / cover with photo | **Giant type over a real photo** + one small editorial caption (lowercase, serif) | opener beat `photo`; zine `poster` with `photo` | built |

## Rules of thumb
- Two zine scenes are never back to back; 4-6 per long video; each stays 6-14 s.
- Never more than 4 words per headline line (<=11 characters per line for stamps); content stays above y~880 (captions live below).
- Colour: series brand colours stay (DevOps cyan/violet, Linux green, Git amber); zine scenes bring newsprint cream, kraft, black and a single red.
- 3D openers for topics about people/teams/pipelines/cloud; 2D openers for incidents, comparisons, commands. Alternate day to day so the channel does not look the same.
- Photo of Shivam: only the committed files in `hf/assets` (`shivam_clasped.png`, `shivam_serious.png`, `shivam_fullbody.png`).
