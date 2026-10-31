# Linux Zero to Hero (Tech-dev)

Daily 5–10 min Linux commands series by Shivam Singh Verma, live on the Tech-Dev YouTube channel every day at 5:00 PM IST.

- `PLAN.md`: all 45 episodes (commands, links between them, SRE scenario, common mistake)
- `AUTHORING.md`: how to write `episodes/epNN.py`
- `engine.py`: renders an episode (graphics, mascot Bashi, cartoons, terminal scenes, music + SFX, thumbnail, upload text)
- `media/epNN/`: published video, thumbnail and upload text
- `series.json`: status of each episode

Render: `python3 engine.py episodes/ep01.py out/ep01` (needs ffmpeg, Pillow, numpy, scipy).
