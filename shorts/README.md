# Tech-dev Shorts (all series)

One vertical YouTube Short (1080x1920, 30–50 s) per long episode, taught by the animal & bird cast in their own voices.

Render: `python3 shorts/shorts.py shorts/specs/<series>-<ep>.py out/short-<series>-<ep>` (needs ffmpeg, Pillow, numpy, scipy).
Preview first: add `--stills 2,8,15,...` and look at the JPGs.
Outputs: `short.mp4`, `cover.jpg`, `upload.json`, `upload.txt`. Publish to `media/shorts/<series>-<ep>/`.

## Schedule (Metricool brand 7777398, Tech-Dev channel only)
The daily maker task renders the Short together with its episode and schedules it for **the next day**:
| Series | Long video | Short |
|---|---|---|
| Git & GitHub | 4:00 PM IST | next day 11:30 AM IST |
| Linux Zero to Hero | 5:00 PM IST | next day 12:30 PM IST |
| DevOps & SRE Zero to Hero | 8:00 PM IST | next day 1:30 PM IST |
Metricool `youtubeData.type` = `"short"`, title ends with `#shorts`.

## Spec format (`shorts/specs/<series>-<ep>.py`)
```python
SHORT = {
  'series': 'linux' | 'git' | 'devops', 'tag': 'EP 2' or 'DAY 5',
  'hook': {'text': 'Big hook with *highlight*', 'sub': 'small line', 'who': ['mitthu', 'ollie']},  # 2 characters
  'beats': [  # 4-6 beats, one idea each, from the episode
    {'who': 'mitthu', 'say': '≤14 words, *1 highlight*', 'cmd': 'ls -lh', 'out': ['real output'], 'hl': 'text to colour'},
    {'who': 'ollie', 'say': '...', 'big': 'KEYWORD', 'sub': 'one line'},       # concept card, no command
    {'who': 'kaalu', 'say': '...', 'cmd': '...', 'out': [...], 'error': True, 'badge': 'The fix!'},  # the mistake
  ],
  'cta': {'who': ['mitthu', 'ollie', 'kaalu'], 'lines': ['<Series>, Ep N', 'New episode every day, 5 PM IST']},
  'upload': {'title': '<Hook, ≤70 chars> #shorts #linux', 'description': '...', 'tags': [...]},
}
```
Rules: every command and output must be real and correct; output lines ≤ 30 chars (split long lines); keep the total 30–50 s (the engine prints the timeline). Optional per beat: `mood`, `arms`, `extra` (seconds), `user`/`host`.

## Cast (cast.py, same as the DevOps series)
ollie (Owl, concepts), mitthu (Parrot, commands), bablu (Beaver, CI/CD and builds), gajju (Elephant, Git/logs/memory),
ashtu (Octopus, containers/Kubernetes), kukdu (Rooster, monitoring/alerts), kaalu (Crow, the villain: mistakes and outages),
tortoise, cheetah. Each has drawn poses and a synthesized animal voice + signature call. No brand mascots.
