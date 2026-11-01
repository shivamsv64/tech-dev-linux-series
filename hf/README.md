# Hugging Face prep (daily, before the episode makers)

Free, open-source Hugging Face models make each episode's visuals fresh. A scheduled task
("Tech-dev Hugging Face prep") runs every morning before the makers and commits, per episode due today:

| What | Where | Used by |
|---|---|---|
| 4 FLUX scene arts (1344×768) | `<media dir>/art/<art name>.jpg` | engine v2 automatically: any scene whose `art` has that name uses the fresh image instead of the library one (`art_path()` in `v2/engine.py`) |
| Photo thumbnail (1280×720) | `<media dir>/thumbnail_custom.jpg` | engine v2 automatically writes it as `thumbnail.jpg` |

Media dirs: DevOps `devops-series/media/dayNN/` (this repo), Linux `media/epNN/` (this repo), Git `media/epNN/` (shivamsv64/tech-dev-git-series).

## Models (all allowed on a monetized channel)
- **FLUX.1-schnell** (Apache-2.0) via the "Hugging Face Spaces" connector tool `gr1_flux1_schnell_infer` (Space `evalstate/flux1_schnell`), width 1344, height 768, 4 steps.
- **Qwen-Image-Fast** (Apache-2.0), tool `gr2_qwen_image_fast_generate_image`, when an image needs readable text. Never write "YouTube" in a prompt (it draws a fake logo).
- **BiRefNet** (MIT) made the cutouts in `hf/assets/` from Shivam's approved photos.
- Do NOT use FLUX.1-dev / Krea-dev / Kontext-dev, MusicGen, SDXL-Turbo, F5-TTS or XTTS: non-commercial licenses.
- Free ZeroGPU quota is small: about 5 images per episode is fine. If a tool reports the quota is used up, stop and keep what exists.

## Tools
```
python3 hf/fetch.py <Image URL from the tool result> <out.jpg> [1344x768]   # download + resize
python3 hf/thumb.py <spec.json> <out.jpg>                                   # photo thumbnail
```
Thumbnail spec: see the docstring in `hf/thumb.py` (series, number, bg, photo, top/big/bottom, chip, tag, color).
Photos: `clasped` (friendly, concepts), `clasped_close` (head & shoulders), `serious` (problems, outages, mistakes),
`fullbody` (confident, how-to). Never use photos of Shivam lying on a bed or sofa.

## Art prompts
Re-imagine the chosen library art for today's topic, in the series look:
- Mission Control (DevOps): "cinematic sci-fi space-operations control center ... deep navy with cyan and violet light"
- Isometric City (Linux, Git): "isometric 3D miniature tech city at night ... dark navy with green / amber neon, tilt-shift"
Always add: "left third darker and calm, no text, no letters, no logos, no people, highly detailed".
