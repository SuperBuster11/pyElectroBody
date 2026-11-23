"""
Video output module.

The game is always drawn on a 640x480 canvas (gl.window). This module
scales the canvas to the real window or screen, keeping the 4:3 aspect
ratio, and remembers the user's choice in a settings file.
The window is always placed in the center of the screen.

Keys (work everywhere):
    F11 or Alt+Enter - fullscreen on/off
    F10              - next window size (windowed mode only)

Fullscreen always uses the desktop resolution.
"""

import os
import sys
import json
import logging
import pygame
import emglobals as gl

CANVAS = (640, 480)
CAPTION = "Electro Man - Python Version"
SCALES = [1, 1.5, 2, 2.5, 3, 3.5, 4]  # window sizes as canvas multiples

settings = {"fullscreen": False, "scale": 1.5}
screen = None  # the real display surface
_notify = None  # function showing a short message

# ask SDL to open windows in the middle of the screen
os.environ["SDL_VIDEO_CENTERED"] = "1"


def settings_path():
    """Settings live in the user's folder - the game folder may be read only."""
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or \
            os.path.join(os.path.expanduser("~"), ".config")
    return os.path.join(base, "pyelectroman", "settings.json")


def load_settings():
    try:
        with open(settings_path(), "rt") as f:
            data = json.load(f)
        if data.get("scale") in SCALES:
            settings["scale"] = data["scale"]
        settings["fullscreen"] = bool(data.get("fullscreen", False))
    except (OSError, ValueError, TypeError):
        pass


def save_settings():
    try:
        path = settings_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wt") as f:
            json.dump(settings, f)
    except OSError as ex:
        logging.warning("Cannot save settings: %s", ex)


def desktop_size():
    try:
        return tuple(pygame.display.get_desktop_sizes()[0])
    except (AttributeError, IndexError, pygame.error):
        info = pygame.display.Info()
        return info.current_w, info.current_h


def available_scales():
    """Window sizes that fit on the desktop (always at least 1x)."""
    dw, dh = desktop_size()
    fitting = [s for s in SCALES
               if CANVAS[0] * s <= dw - 40 and CANVAS[1] * s <= dh - 80]
    return fitting or [1]


def center_window():
    """Move the window to the middle of the screen (pygame-ce)."""
    try:
        window = pygame.Window.from_display_module()
        window.position = pygame.WINDOWPOS_CENTERED
    except Exception:  # pylint: disable-msg=W0703
        pass  # older pygame - SDL_VIDEO_CENTERED does the job


def apply():
    """(Re)create the real display according to the settings."""
    global screen
    if settings["fullscreen"]:
        # (0, 0) = desktop resolution - no monitor mode change
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    else:
        scales = available_scales()
        if settings["scale"] not in scales:
            settings["scale"] = max(scales)
        size = (int(CANVAS[0] * settings["scale"]),
                int(CANVAS[1] * settings["scale"]))
        screen = pygame.display.set_mode(size)
        center_window()
    logging.info("Video mode: %s", describe())


def set_icon():
    """Window icon (title bar and taskbar). Must be set before set_mode()."""
    try:
        pygame.display.set_icon(pygame.image.load(
            os.path.join(gl.data_folder, "icon.png")))
    except (pygame.error, OSError, FileNotFoundError) as ex:
        logging.warning("Cannot load icon: %s", ex)


def windows_taskbar_id():
    """
    When the game runs as 'python em.py', Windows groups the window with
    python.exe and shows Python's icon on the taskbar. Giving the process
    its own application id makes Windows use the game's window icon.
    """
    if sys.platform.startswith("win"):
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "pyelectroman.electroman")
        except Exception:  # pylint: disable-msg=W0703
            pass


def init(notify=None):
    """Create the canvas and the real display."""
    global _notify
    _notify = notify
    pygame.display.set_caption(CAPTION)
    set_icon()
    load_settings()
    apply()
    gl.window = pygame.Surface(CANVAS)


def target_rect():
    """Where the canvas lands on the real display (4:3, centered)."""
    sw, sh = screen.get_size()
    k = min(sw / CANVAS[0], sh / CANVAS[1])
    w, h = max(1, int(CANVAS[0] * k)), max(1, int(CANVAS[1] * k))
    return pygame.Rect((sw - w) // 2, (sh - h) // 2, w, h)


def present():
    """Scale the canvas to the display and show it."""
    rect = target_rect()
    if rect.size == CANVAS:
        image = gl.window
    else:
        image = pygame.transform.scale(gl.window, rect.size)
    if rect.size != screen.get_size():
        screen.fill((0, 0, 0))
    screen.blit(image, rect.topleft)
    pygame.display.flip()


def describe():
    where = "pełny ekran" if settings["fullscreen"] else "okno"
    return "%s %dx%d" % ((where,) + tuple(screen.get_size()))


def changed():
    save_settings()
    if _notify:
        _notify(describe())


def toggle_fullscreen():
    settings["fullscreen"] = not settings["fullscreen"]
    apply()
    save_settings()


def next_window_size():
    """Next window size. Does nothing in fullscreen."""
    if settings["fullscreen"]:
        return
    scales = available_scales()
    i = scales.index(settings["scale"]) if settings["scale"] in scales else -1
    settings["scale"] = scales[(i + 1) % len(scales)]
    apply()
    changed()


def handle_event(event):
    """Handle video related keys. Return True if the event was used."""
    if event.type == pygame.KEYDOWN:
        alt_enter = (event.key == pygame.K_RETURN and
                     (getattr(event, "mod", 0) & pygame.KMOD_ALT))
        if event.key == pygame.K_F11 or alt_enter:
            toggle_fullscreen()
            return True
        if event.key == pygame.K_F10:
            next_window_size()
            return True
    return False
