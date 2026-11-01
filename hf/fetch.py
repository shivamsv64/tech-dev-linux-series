"""Download an image returned by a Hugging Face Space (the "Image URL" in the connector's result)
and save it as JPEG at the engine's art size.

usage: python3 hf/fetch.py <image_url> <out.jpg> [WIDTHxHEIGHT]   (default 1344x768, the art library size)
"""
import io, sys, urllib.request
from PIL import Image

url, out = sys.argv[1], sys.argv[2]
w, h = (int(v) for v in (sys.argv[3] if len(sys.argv) > 3 else "1344x768").split("x"))
req = urllib.request.Request(url, headers={"User-Agent": "tech-dev-hf-prep"})
data = urllib.request.urlopen(req, timeout=120).read()
im = Image.open(io.BytesIO(data)).convert("RGB")
s = max(w / im.width, h / im.height)
im = im.resize((int(im.width * s + .5), int(im.height * s + .5)), Image.LANCZOS)
x, y = (im.width - w) // 2, (im.height - h) // 2
im.crop((x, y, x + w, y + h)).save(out, quality=92)
print(f"saved {out} ({w}x{h}) from {len(data)} bytes")
