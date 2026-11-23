"""
Render whole levels (16x16 screens) into big PNG maps.

Usage: python display_levels.py [data_folder] [output_folder]
Defaults: ../data -> ../maps (next to this script). Requires Pillow.
"""

import os
import sys
import json
import glob
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
TILE = 24  # original sprite size in pixels
SCREEN_W, SCREEN_H = 13, 8  # screen size in tiles
TY = 16  # screen rows to render


def load_sprites(folder, set1, set2):
    print("Loading sprite sets: %s, %s" % (set1, set2))
    sprites = [None] * 128
    for sprite in range(1, 128):
        set_name, number = (set1, sprite) if sprite < 64 else (set2, sprite - 64)
        path = os.path.join(folder, set_name, "%s_%02d.png" % (set_name, number))
        if os.path.exists(path):
            sprites[sprite] = Image.open(path).convert("RGBA")
    return sprites


def render_screen(screen, sprites):
    image = Image.new("RGBA", (SCREEN_W * TILE, SCREEN_H * TILE), (0, 0, 0, 255))
    if screen:
        for layer in screen:
            if layer:
                for y in range(SCREEN_H):
                    for x in range(SCREEN_W):
                        sprite = sprites[layer[y * SCREEN_W + x]]
                        if sprite:
                            image.alpha_composite(sprite, (x * TILE, y * TILE))
    return image


def render_level(filename, folder, output):
    print("Loading level:", filename)
    with open(filename, "rt") as f:
        level = json.load(f)
    sprites = load_sprites(folder, *level["names"])
    width, height = SCREEN_W * TILE, SCREEN_H * TILE
    big = Image.new("RGB", (16 * width, TY * height))
    for s in range(TY * 16):
        screen = render_screen(level["screens"][s], sprites)
        big.paste(screen.convert("RGB"), ((s % 16) * width, (s // 16) * height))
    name = os.path.splitext(os.path.basename(filename))[0]
    big.save(os.path.join(output, name + ".png"))
    print("Written:", name + ".png")


def main():
    folder = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "data")
    output = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "maps")
    os.makedirs(output, exist_ok=True)
    for filename in sorted(glob.glob(os.path.join(folder, "*.ebl"))):
        render_level(filename, folder, output)
    print("Done.")


if __name__ == '__main__':
    main()
