"""Intro (title screen) module"""

import math
import os
import pygame
import emglobals as gl
import emdata as da
import emsound as sound

# letters sprite set: a-z, Polish letters, digits and a few symbols
LETTERS = "abcdefghijklmnopqrstuvwxyząćęłńóśź0123456789:"
SYMBOLS = {"?": 47, "(": 48, ")": 49, "ż": 34}


class SpriteFont:
    """Text written with the original game's letter sprites."""
    def __init__(self, size):
        data = da.SpriteSet()
        data.load("letters")
        self.size = size
        self.glyphs = {}
        mapping = dict((ch, i + 1) for i, ch in enumerate(LETTERS))
        mapping.update(SYMBOLS)
        for ch, number in mapping.items():
            sprite = data.get_sprite(number)
            if sprite:
                self.glyphs[ch] = pygame.transform.scale(sprite.image,
                                                         (size, size))

    def width(self, text, spacing=0):
        return len(text) * (self.size + spacing) - spacing

    def draw(self, surface, text, position, spacing=0, wave=None):
        x, y = position
        for i, ch in enumerate(text.lower()):
            glyph = self.glyphs.get(ch)
            if glyph:
                dy = int(wave(i)) if wave else 0
                surface.blit(glyph, (x, y + dy))
            x += self.size + spacing

    def draw_centered(self, surface, text, y, spacing=0, wave=None):
        x = (surface.get_width() - self.width(text, spacing)) // 2
        self.draw(surface, text, (x, y), spacing, wave)


class Intro:
    """
    Title screen with the logo, walking hero and music.
    run() returns True to start the game, False to quit.
    """
    LOGO_SCALE = 5
    MENU = ["spacja   start",
            "esc   wyjście"]
    HELP = ["strzałki: ruch i skok",
            "w dół: teleport",
            "spacja: strzał",
            "f1: informacje"]

    def __init__(self):
        self.logo = self.load_logo()
        self.small = SpriteFont(20)
        self.hero = da.SpriteSet()
        self.hero.load("hero")
        self.info = da.SpriteSet()
        self.info.load("info")
        self.walk_right = [(15, n) for n in range(16, 26)]
        self.walk_left = [(4, n) for n in range(5, 15)]
        self.hero_x = -gl.SPRITE_X
        self.hero_dir = 1
        self.frame = 0
        self.counter = 0

    def load_logo(self):
        """Original logo is stored as two tiles in the first level's set."""
        try:
            parts = [pygame.image.load(os.path.join(gl.data_folder, "elek2",
                                                    "elek2_%02d.png" % n))
                     for n in (2, 3)]
        except Exception:  # pylint: disable-msg=W0703
            return None
        w, h = parts[0].get_width(), parts[0].get_height()
        logo = pygame.Surface((2 * w, h))
        logo.blit(parts[0], (0, 0))
        logo.blit(parts[1], (w, 0))
        return pygame.transform.scale(logo, (2 * w * self.LOGO_SCALE,
                                             h * self.LOGO_SCALE))

    def draw_logo(self, surface, t):
        if self.logo is None:
            return
        # zoom in during the first frames
        k = min(1.0, (t + 1) / 15.0)
        w = max(1, int(self.logo.get_width() * k))
        h = max(1, int(self.logo.get_height() * k))
        image = self.logo if k >= 1.0 else pygame.transform.scale(self.logo, (w, h))
        x = (surface.get_width() - w) // 2
        y = 25 + (self.logo.get_height() - h) // 2
        surface.blit(image, (x, y))

    def draw_floor(self, surface, y):
        bar = self.info.get_sprite(14)
        if bar:
            for x in range(0, surface.get_width(), gl.SPRITE_X):
                surface.blit(bar.image, (x, y))

    def draw_hero(self, surface, y):
        anim = self.walk_right if self.hero_dir > 0 else self.walk_left
        top, bottom = anim[self.frame % len(anim)]
        surface.blit(self.hero.get_sprite(top).image, (self.hero_x, y))
        surface.blit(self.hero.get_sprite(bottom).image,
                     (self.hero_x, y + gl.SPRITE_Y))
        self.frame += 1
        self.hero_x += 8 * self.hero_dir
        if self.hero_x > surface.get_width() or self.hero_x < -gl.SPRITE_X:
            self.hero_dir = -self.hero_dir

    def draw(self):
        surface = gl.window
        surface.fill(pygame.Color(0, 0, 0))
        t = self.counter
        self.draw_logo(surface, t)
        wave = lambda i: 3 * math.sin((t + i * 2) * 0.3)
        self.small.draw_centered(surface, "wersja python", 155, 0, wave)
        # floor and walking hero
        self.draw_floor(surface, 280)
        self.draw_hero(surface, 280 - 2 * gl.SPRITE_Y)
        # menu
        y = 336
        for i, line in enumerate(self.MENU):
            if i == 0 and (t // 5) % 2:
                y += 26
                continue  # blinking "start"
            self.small.draw_centered(surface, line, y)
            y += 26
        y += 4
        font = gl.font["normal"]
        for line in self.HELP:
            text = font.render(line, True, pygame.Color(160, 160, 160))
            surface.blit(text, ((surface.get_width() - text.get_width()) // 2, y))
            y += 18
        pygame.display.flip()

    def run(self):
        clock = pygame.time.Clock()
        self.counter = 0
        sound.start_music()
        pygame.event.get()  # forget keys pressed in the game
        result = None
        while result is None:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    gl.quit_requested = True
                    result = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        result = False
                    elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
                        result = True
            sound.update_music()
            self.draw()
            self.counter += 1
            clock.tick(20)
        sound.stop_music()
        return result
