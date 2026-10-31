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

## Daily maker step (run after today's long episode is scheduled)
1. Write `shorts/specs/<id>.py` (id = `linux-epNN`, `git-epNN` or `devops-dayNN`) as a 30–50 s summary of **today's** episode:
   hook with 2 characters → 4–6 beats (the series' lead characters teach; real commands/outputs copied from the episode, output lines ≤ 30 chars) →
   the common mistake by Kaalu the Crow (`error: True` + `badge` with the fix) when the episode has one → cta.
   Lead cast: Linux = Mitthu (commands) + Ollie (why); Git = Gajju (history/commits) + Ollie, Bablu for CI/CD; DevOps = the day's PLAN.md lead + Ollie/Mitthu.
   `upload`: title "<hook, ≤60 chars> #shorts #<linux|git|devops>", description = 1–2 lines + 'Full episode: "<long title>" on the Tech-dev channel.' + schedule line + hashtags starting with #shorts; 10–14 tags.
2. Preview: `python3 shorts/shorts.py shorts/specs/<id>.py out/short-<id> --stills <5 times>`, look at every still (contact sheet is fine), fix overflow. Render without `--stills`. ffprobe: 1080x1920, 30–58 s, aac.
3. Copy `short.mp4, cover.jpg, upload.json, upload.txt` to the series' shorts media folder, commit + push, check the raw URL returns 200.
4. Metricool (only after the channel-safety check): same post shape as the long video, but `date` = **tomorrow** at the series' Short time (table above), `media` = [short URL], NO `videoThumbnailUrl`, `youtubeData.type` = "short", title/description/tags from the Short's upload.json.
5. Add `"short": {"status": "scheduled", "title", "live", "metricool_id", "planner"}` to today's series.json row; commit + push.
If the Short fails, the long episode still comes first: finish and report it, and say what failed with the Short.
