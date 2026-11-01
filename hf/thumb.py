"""Tech-dev photo thumbnail (1280x720): FLUX background + Shivam's cutout + brand text.

usage: python3 hf/thumb.py <spec.json> <out.jpg>
spec = {
  "series": "devops" | "linux" | "git", "number": 2,
  "bg": "path/to/flux_background.jpg",
  "photo": "clasped" | "clasped_close" | "serious" | "fullbody",   # cutouts in hf/assets/
  "top": "WHAT IS",            # optional small white line above the big word
  "big": "DEVOPS?",            # the big coloured word(s), <= 10 characters reads best
  "bottom": "for ONE fix?!",   # optional white line under the big word
  "chip": "$ man --help",      # optional terminal chip (monospace)
  "tag": "Explained simply",   # optional amber label
  "color": "cyan" | "amber" | "green" | "red" | "violet"
}
Photos of Shivam lying on a bed/sofa are never used (not professional); only the approved cutouts here.
"""
import json, math, os, sys
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1280, 720
NAVY, INK, WHITE = (10, 15, 31), (2, 6, 18), (255, 255, 255)
COLORS = {"cyan": (56, 189, 248), "amber": (251, 191, 36), "violet": (167, 139, 250),
          "green": (52, 211, 153), "red": (239, 68, 68)}
CYAN, AMBER, VIOLET = COLORS["cyan"], COLORS["amber"], COLORS["violet"]
POP = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
# how each approved photo sits in the frame: (height px, right edge x, crop bottom fraction, warm tint)
PHOTOS = {
    "clasped": ("shivam_clasped.png", 640, W + 30, 0.0, 0.06),
    "clasped_close": ("shivam_clasped.png", 650, W + 50, 0.40, 0.06),
    "serious": ("shivam_serious.png", 700, W + 40, 0.08, 0.0),
    "fullbody": ("shivam_fullbody.png", 690, W - 20, 0.56, 0.0),
}


def font(path, size):
    for p in (path, "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def background(path):
    im = Image.open(path).convert("RGB")
    s = max(W / im.width, H / im.height)
    im = im.resize((int(im.width * s + .5), int(im.height * s + .5)), Image.LANCZOS)
    x, y = (im.width - W) // 2, (im.height - H) // 2
    im = im.crop((x, y, x + W, y + H)).filter(ImageFilter.GaussianBlur(1.6))
    im = ImageEnhance.Brightness(im).enhance(0.9)
    shade = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(shade)
    for xx in range(W):                       # dark navy wash on the left so the words stay readable
        a = max(0.0, 1 - xx / (W * 0.62))
        d.line([(xx, 0), (xx, H)], fill=int(205 * a ** 1.2))
    im.paste(Image.new("RGB", (W, H), NAVY), (0, 0), shade)
    return im


def grade(p, warm):
    rgb, a = p.convert("RGB"), p.getchannel("A")
    if warm:
        r, g, b = rgb.split()
        r = r.point(lambda v: min(255, int(v * (1 + warm)))); b = b.point(lambda v: int(v * (1 - warm)))
        rgb = Image.merge("RGB", (r, g, b))
    rgb = ImageEnhance.Color(ImageEnhance.Contrast(rgb).enhance(1.12)).enhance(1.12)
    rgb = ImageEnhance.Brightness(rgb).enhance(1.04)
    out = rgb.convert("RGBA"); out.putalpha(a)
    return out


def place_person(img, photo, accent):
    fname, height, x_right, crop_bottom, warm = PHOTOS[photo]
    p = Image.open(os.path.join(HERE, "assets", fname))
    if crop_bottom:
        p = p.crop((0, 0, p.width, int(p.height * (1 - crop_bottom))))
    p = grade(p, warm)
    s = height / p.height
    p = p.resize((int(p.width * s), int(p.height * s)), Image.LANCZOS)
    x, y = x_right - p.width, H - p.height
    a = p.getchannel("A").point(lambda v: 255 if v > 110 else 0)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    big = Image.new("L", (W, H), 0); big.paste(a.filter(ImageFilter.MaxFilter(31)), (x, y))
    glow = Image.new("RGBA", (W, H), accent + (0,)); glow.putalpha(big.filter(ImageFilter.GaussianBlur(26)).point(lambda v: int(v * .95)))
    layer.alpha_composite(glow)
    ol = Image.new("L", (W, H), 0); ol.paste(a.filter(ImageFilter.MaxFilter(13)), (x, y))
    white = Image.new("RGBA", (W, H), WHITE + (0,)); white.putalpha(ol)
    layer.alpha_composite(white)
    layer.alpha_composite(p, (x, y))
    img.paste(layer, (0, 0), layer)


def stroked(d, xy, text, f, fill, stroke=9):
    d.text((xy[0] + 6, xy[1] + 8), text, font=f, fill=(0, 0, 0, 150), stroke_width=stroke, stroke_fill=(0, 0, 0, 150))
    d.text(xy, text, font=f, fill=fill, stroke_width=stroke, stroke_fill=INK)


def fit(d, text, path, max_w, start, floor=56):
    s = start
    while s > floor and d.textlength(text, font=font(path, s)) > max_w:
        s -= 4
    return font(path, s)


def chip(d, xy, text, fg, bg, outline, f, pad=(26, 14), radius=16):
    w = d.textlength(text, font=f); asc, desc = f.getmetrics()
    x, y = xy
    d.rounded_rectangle([x, y, x + w + pad[0] * 2, y + asc + desc + pad[1] * 2], radius, fill=bg, outline=outline, width=4)
    d.text((x + pad[0], y + pad[1]), text, font=f, fill=fg)
    return y + asc + desc + pad[1] * 2


def brand(d, accent, badge_top, badge_num):
    chip(d, (44, 34), ">_ Tech-dev", WHITE, (8, 14, 30), accent, font(POP, 30), pad=(20, 8), radius=14)
    cx, cy, r = 110, 600, 66
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=AMBER, outline=INK, width=6)
    d.text((cx, cy - 22), badge_top, font=font(POP, 28), fill=INK, anchor="mm")
    d.text((cx, cy + 20), badge_num, font=font(POP, 52 if len(badge_num) < 3 else 40), fill=INK, anchor="mm")
    seg = W // 3
    for i, c in enumerate((CYAN, AMBER, VIOLET)):
        d.rectangle([i * seg, H - 12, (i + 1) * seg + 2, H], fill=c)


def make(spec, out):
    accent = COLORS.get(spec.get("color", "cyan"), CYAN)
    img = background(spec["bg"])
    place_person(img, spec.get("photo", "clasped"), accent)
    d = ImageDraw.Draw(img, "RGBA")
    y, max_w = 112, 640
    if spec.get("top"):
        f = fit(d, spec["top"], POP, max_w, 104); stroked(d, (52, y), spec["top"], f, WHITE); y += int(f.size * 1.05)
    big_lines = [spec["big"]]
    words = spec["big"].split()
    if len(words) > 1 and fit(d, spec["big"], POP, max_w, 176).size < 130:   # too long for one line: wrap in two
        cut = min(range(1, len(words)), key=lambda i: abs(len(" ".join(words[:i])) - len(" ".join(words[i:]))))
        big_lines = [" ".join(words[:cut]), " ".join(words[cut:])]
    size = min(fit(d, line, POP, max_w, 176).size for line in big_lines)
    f = font(POP, size)
    for line in big_lines:
        stroked(d, (46, y), line, f, accent if line is big_lines[-1] else WHITE, stroke=11); y += int(size * 1.08)
    y += int(size * 0.04)
    if spec.get("bottom"):
        f = fit(d, spec["bottom"], POP, max_w, 84); stroked(d, (56, y), spec["bottom"], f, WHITE); y += int(f.size * 1.2)
    y = max(y + 6, 400)
    if spec.get("chip"):
        col = accent if spec.get("series") != "devops" else COLORS["green"]
        y = chip(d, (214, min(y, 470)), spec["chip"], col, (6, 10, 14), col, fit(d, spec["chip"], MONO, 560, 52, 30), pad=(26, 12)) + 16
    if spec.get("tag"):
        chip(d, (214, min(y, 500)), spec["tag"], INK, AMBER, INK, fit(d, spec["tag"], POP, 560, 34, 24))
    devops = spec.get("series") == "devops"
    brand(d, accent, "DAY" if devops else "EP", str(spec["number"]))
    img.save(out, quality=93)
    return out


if __name__ == "__main__":
    make(json.load(open(sys.argv[1])), sys.argv[2])
    print("wrote", sys.argv[2])
