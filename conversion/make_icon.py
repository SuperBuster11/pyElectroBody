"""
Build data/icon.png (window icon) and icon.ico (exe icon) from the
original logo tiles elek2_02 + elek2_03. Requires Pillow.

Usage: python make_icon.py [game_folder]
"""
import sys, os
from PIL import Image
game = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
d = os.path.join(game, "data", "elek2")
a = Image.open(os.path.join(d, "elek2_02.png")).convert("RGBA")
b = Image.open(os.path.join(d, "elek2_03.png")).convert("RGBA")
logo = Image.new("RGBA", (a.width + b.width, a.height), (0, 0, 0, 0))
logo.paste(a, (0, 0)); logo.paste(b, (a.width, 0))
bbox = logo.getbbox()  # trim empty edges
logo = logo.crop(bbox)
print("logo", logo.size)

def icon(size):
    """Logo centered on a transparent square, sharp pixels where possible."""
    k = size / logo.width
    ik = int(k)
    if ik >= 1:
        img = logo.resize((logo.width * ik, logo.height * ik), Image.NEAREST)
    else:
        img = logo.resize((size, max(1, round(logo.height * k))), Image.LANCZOS)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    canvas.paste(img, ((size - img.width) // 2, (size - img.height) // 2), img)
    return canvas

big = icon(256)
big.save(os.path.join(game, "data", "icon.png"))
sizes = [16, 24, 32, 48, 64, 128, 256]
imgs = [icon(s) for s in sizes]
imgs[-1].save(os.path.join(game, "icon.ico"), format="ICO",
              sizes=[(s, s) for s in sizes], append_images=imgs[:-1])
print("Written: data/icon.png, icon.ico")
