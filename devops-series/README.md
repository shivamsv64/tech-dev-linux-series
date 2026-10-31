# DevOps & SRE Zero to Hero (Tech-dev)

Free 100-day DevOps & SRE course by Shivam Singh Verma, live on the Tech-Dev YouTube channel every day at 8:00 PM IST
(Day 1 = 1 Nov 2026, Day 100 = 8 Feb 2027). Taught by an animal & bird cast with their own voices.

- `PLAN.md`: all 100 days (phase, topic, lead character)
- `AUTHORING.md`: how to write `episodes/dayNN.py`
- `engine.py` + `cast.py`: renderer (forest-at-night look, animal characters, animal voices, terminal scenes, music, thumbnail, upload text)
- `media/dayNN/`: published video, thumbnail and upload text
- `series.json`: status of each day

Render: `python3 engine.py episodes/day01.py out/day01` (needs ffmpeg, Pillow, numpy, scipy).
