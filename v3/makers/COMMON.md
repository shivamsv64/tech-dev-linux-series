# Tech-dev daily maker: shared rules (v3, since 5 Nov 2026)

Authoritative for the three daily maker tasks (DevOps, Linux, Git). Each task's own file (`devops.md`, `linux.md`, `git.md`
in this folder) holds the series-specific values (paths, times, keys). Work unattended, but keep Shivam informed with
SendUserMessage. Never claim something worked that you did not see.

## 0. Why v3 (Shivam, 4 Nov 2026) and what the research says
Shivam asked for: his own voice at the start of every long video, Short and Instagram Reel; human, interactive, hook-first
narration; richer graphics (3D and 2D mixed by situation); and content that still pulls views in 2026, because a plain
"full course" is not enough. The channel's own numbers (1-4 Nov 2026, vidIQ): Shorts 900 views vs long videos 166, average view
duration 42 s on long videos, 16 s on Shorts. Research (vidIQ outliers + 2026 articles) says what works for small
DevOps/Linux/Git channels:
- **Standalone, searchable question per video**, not "lesson N". Breakout titles: "Every Major DevOps Tool Explained in 11 Minutes",
  "How Docker, Kubernetes, Redis, Kafka & Prometheus Fit Together in One Application" (462x), "<X> (A True Story)" incident stories
  (pouria, 663K), "AWS DevOps Interview: Explain Your CI/CD Pipeline Like a Senior", "I Wish Someone Explained Docker Like This",
  "Reverse Proxy vs Load Balancer vs API Gateway: The Real Difference". Series numbering goes at the END of the title only.
- **Hook in 3 s, payoff promised in the first 30 s, intro under 10 s, pattern interrupt every 60-90 s.** Retention under ~40%
  gets a video deprioritised; target 50%+ for 6-10 min.
- **Length 8-11 minutes** (mid-roll ads need 8+; 6-15 min converts subscribers best).
- **Shorts: 25-45 s, hook in the first 1-2 s, result first, on-screen text, one clear idea, CTA in the last 5 s.** Shorts feed discovery;
  long videos carry watch hours. Shorts views do not count toward the 4,000 watch hours. (A vendor article says the YPP bar rises on
  1 Feb 2027 to 8,000 watch hours / 20M Shorts views for new applications; unverified, Shivam should check YouTube's own page.)
- **Instagram Reels** rank by watch time/completion, replays and DM shares; under 30 s educational quick hits do best. The
  cross-post task posts our Shorts as they are, so every Short must work with sound off and in 2 s.
- Own voice + real work stories + original visuals are what separates the channel from mass-produced AI content (YouTube's
  inauthentic-content policy). Keep the AI disclosure on.

## 1. Mandatory rules (unchanged)
- CHANNEL SAFETY: only Tech-Dev, channel id UCkMTPE1hLFUG1-4ccCDmP9w. Never Lonely Hours Lofi (UCZAlvuJrNlK6ORtuN5x06ZQ). Before any Metricool
  scheduling call getBrandSettings and confirm brand 7777398 has networksData.youtubeData == "UCkMTPE1hLFUG1-4ccCDmP9w"; else schedule nothing,
  send the files and say so.
- AI DISCLOSURE: every long video and Short is scheduled with youtubeData.isAiGeneratedContent = true. Never false.
- Commit as user.name "Shivam Singh Verma", user.email "shivamsinghverma64@gmail.com". Before every push: `git fetch origin main` and rebase. Add as the last
  lines of commit messages the attribution lines given in the session, if any.
- Never put brand logos, film/TV characters or real people other than Shivam in any scene or art. Take STYLE from references, never their content.

## 2. ELEVENLABS: Shivam's own voice (new rule, replaces "never call ElevenLabs")
Voice: cloned "Shivam singh Verma", voice_id `bFB4JzmoiywTauhk6IsI`, model `eleven_v4`. Tools: ElevenLabs connector (`creative_generate_speech`,
`creative_get_flow_run_status`; load with ToolSearch). Monthly plan: 30,000 credits (about 1 credit per character).
- **Long video opener** (first 20-25 s, his voice): at most 330 characters. **Short hook** (first sentence of the Short, his voice): at most 90 characters.
  Everything else stays on the free Kokoro narrator (plus his committed intro/CTA clips).
- ONE take only: `generations_count: 1`. ALWAYS call with `estimate_only: true` first. If the estimate is above 400 credits (opener) or 120 (Short), shorten the text and estimate again.
  Never generate test takes, never retry a generation (a retry bills twice). If a poll fails, poll again; do not generate again.
- Budget gate before each generation: add up `voice_chars` over all rows and `short` objects in the three trackers (devops-series/series.json, tech-dev-linux-series series.json,
  tech-dev-git-series series.json) whose date is in the current IST month. If the total is 22,000 or more, skip Short hooks (Kokoro only). If it is 27,000 or more, skip openers too
  (use a normal `hook` scene) and say so in the report. Record `voice_chars` (the credits the estimate said) on the row / short object.
- Flow: generate, poll `creative_get_flow_run_status` (wait poll_after_seconds) until all_completed, download `media[0].url` with curl to the target path (elevenlabsusercontent.com works from the sandbox),
  check with ffprobe (duration about 4-25 s, not silent). If ElevenLabs fails or credits are short: no opener (restore the `hook` scene) / Kokoro-only Short, and tell Shivam.
- Words timed locally by faster-whisper (`pip install --break-system-packages faster-whisper numpy soundfile`; model downloads on first use, retry once on an HF 429).

## 3. The long video (8-11 min)
Read first: `v3/OPENER.md`, `v3/STYLES.md`, `v2/AUTHORING.md`, the series sample episode, and the latest `episodes-v2/*.py` (continuity). Reference episode: `devops-series/episodes-v2/day05.py` (in the linux repo).
1. **Pick the angle** from the PLAN row, but frame it as ONE question a learner would search or fear ("Why does `rm -rf` ... ?", "Which of the three fits you?", "Fix a full disk in 5 minutes"). Use a breakout pattern above
   when it fits (explained-in-N-minutes, how-the-pieces-fit, a true story from Shivam's work in the third person, interview answer, X-vs-Y real difference). The video must stand alone: a new viewer needs no earlier episode.
2. **Title** = `<problem/outcome hook, at most 60 chars> | <series title> <Day N | Ep N>` exactly as the series file says (the watchdogs look for the suffix). No clickbait the video does not pay off.
3. **Opener** (his voice, `EP['opener']`, see `v3/OPENER.md`): 45-55 words, at most 330 chars: surprising fact / contrast / problem in the first sentence, escalate once, promise the payoff ("by the end of this video you'll...").
   Estimate, generate (section 2), save `<media dir>/vo/opener_shivam.mp3`, commit it with its `_words.json`. Choose `'engine'`: `'3d'` when the topic fits the ops-room world (roles/desks, racks, cloud, pipeline, photo finale), otherwise `'2d'` (Remotion front page / dossier / board / photo / poster);
   alternate styles across days for variety. Keep `beats2d` as the fallback when you use 3D.
   Render: `python3 v3/opener3d/render.py <spec> <outdir> --sheet` (look at the sheet, fix, then without flag) or `python3 v3/opener/render.py <spec> <outdir> --stills ...` then without flag. 3D is software-rendered (about 20-25 min): start it in the
   background, then write the body spec while it runs; do not run two heavy renders at once. If 3D is not DONE after 40 min, kill it and render 2D instead. Verify `<outdir>/opener.mp4` (ffprobe 1920x1080, aac, 18-26 s) and look at 3 frames.
   With an opener: no `hook` scene; the body starts at `title` (intro True). engine v2 puts `<outdir>/opener.mp4` in front automatically.
4. **Body** (engine v2): recap of the last episode at most 15 s (reveal its quiz answer), then the concept, hands-on terminal scenes (real, correct commands and outputs; run them in a scratch folder when unsure), one real work story (third person: "in Shivam's team..."), common mistake and fix, interview corner, quiz (answer None), recap with homework, outro naming the next episode.
   - **Interactive**: one direct question to the viewer every 60-90 s ("pause and guess", "type A, B or C", "quick check"); open a loop early and pay it off.
   - **Pattern breaks**: 4-6 zine scenes (`headline`, `board`, `dossier`, `poster`, `deck` when available), never two in a row, chosen by situation with `v3/STYLES.md`. Mix them with the normal scenes.
   - Narration is full spoken sentences with contractions, talks to "you", no list-reading.
   - Total 8-11 minutes (65-90 scenes); if shorter, add hands-on or story scenes, not filler.
5. Preview stills (12, look at every one), fix, one fix pass, render in the background, verify with ffprobe (1920x1080, aac, duration, opener + body) and frames. Loudness about -14 LUFS.

## 4. The Short (25-45 s, goes to YouTube Shorts AND Instagram Reels)
Follow `shorts/README.md` and `shorts/SKIT.md` (Desk Life skit), with these v3 changes:
- Scene 1 is the **hook in Shivam's own voice**: one sentence, at most 90 characters, result-first or a direct question to the viewer ("Your server is down. Do you know the first command?"). Estimate, generate (section 2), save `<short media dir>/hook_shivam.mp3`, commit it, and
  put `'mp3': '<repo-relative path>'` on scene 1 together with the same text in `say` (captions). Everything after it: free narrator.
- Length 25-45 s (ffprobe 1080x1920, aac). On-screen banner/keywords readable with sound off. Result first, one idea, a clear payoff, takeaway card, CTA in the last 5 s.
- Title: `<situation hook, at most 60 chars> #shorts #<series tag>` (as the series file says). Relatable situations, "what is X in 40 seconds", "POV" and 'one mistake' formats work best for this audience.
- Vertical 3D/zine Shorts are not built yet (planned): keep the skit look for now.

## 5. Metricool free limit and vidIQ handoff (unchanged, Shivam 3 Nov 2026)
Metricool's free plan publishes 20 posts per IST month. GATE immediately before EACH `createScheduledPost` (episode and Short): target month = month of that post's date in IST; `getScheduledPosts` brandId "7777398", timezone "Asia/Kolkata", whole month; count posts whose providers include
"youtube" and whose youtube status is PUBLISHED or PENDING. 19 or less: schedule with Metricool. 20 or more (or the call fails): HANDOFF:
H1. Commit the file under its key name instead of video.mp4 / short.mp4 (paths in the series file). Push; check the raw URL returns 200.
H2. In the series tracker set on the row / short object: status "scheduled", route "vidiq", yt_state "awaiting_upload", key, file (raw URL), title, live (the planned IST date and time), commit + push. Never create a Metricool post for a handoff item.
H3. In the report tell Shivam: Metricool's 20 free posts for <month> are used, so download <file URL> and upload it to YouTube Studio on Tech-Dev as Private WITHOUT renaming (the title must stay <key>), and turn on "Altered or synthetic content"; the "Tech-dev vidIQ scheduler" task then sets title, description, tags, thumbnail and the <live time> IST time.
Hygiene: for route "vidiq" items delete their TD-*.mp4 only when yt_state is "scheduled_on_youtube" or "missed" AND the live time has passed; never delete a file whose yt_state is "awaiting_upload".

## 6. Metricool post shape (when the gate allows)
`createScheduledPost` blogId "7777398", info JSON built with python json.dumps: {"autoPublish": true, "descendants": [], "draft": false, "firstCommentText": "", "hasNotReadNotes": false, "media": [video URL], "videoThumbnailUrl": thumbnail URL (episode only),
"mediaAltText": [], "providers": [{"network": "youtube"}], "publicationDate": {"dateTime": "<local time>", "timezone": "Asia/Kolkata"}, "shortener": false, "smartLinkData": {"ids": []}, "text": <description from upload.json>,
"youtubeData": {"title": <title>, "type": "video" or "short", "privacy": "public", "tags": <tags>, "category": "EDUCATION", "madeForKids": false, "isAiGeneratedContent": true}}. If the thumbnail field is rejected retry once without it and tell Shivam.
If the planned time already passed, schedule 15 minutes from now.

## 7. Report (SendUserFile the thumbnail, the video and the Short, then ONE SendUserMessage)
Episode title, length, live time; the Short title and live time; "ElevenLabs credits used: <opener + hook>" and the month-to-date total against 30,000; "marked as AI content"; opener style (3D/2D) and which zine scenes were used; Metricool planner links (only for posts really created) and
"Metricool posts used this month: N/20"; any handoff instructions; anything that needs attention. If a step fails and you cannot fix it, still send the rendered files and say exactly what failed.
