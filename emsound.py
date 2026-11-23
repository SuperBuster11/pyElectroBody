"""Sound effects and music module"""

import os
import logging
import pygame
import emglobals as gl

# sound effects used by the game (files data/<name>.wav)
EFFECTS = ["footstep", "jump", "jumpend", "shoot", "laser", "eshoot",
           "xplosion", "battery", "disk", "checkp", "teleport", "warning",
           "warning2", "area", "ask",
           "wpn_1", "wpn_2", "wpn_3", "wpn_4", "wpn_5"]
# intro music is made of short sampled phrases played one after another
INTRO_MUSIC = ["ta", "tb", "tc", "td", "te", "tf", "tg", "th", "tj"]

VOLUME = 0.3  # 30%

enabled = False
sounds = {}
_music = []
_music_pos = 0
_music_channel = None
_step_channel = None


def pre_init():
    """Must be called before pygame.init() for low latency sound."""
    try:
        pygame.mixer.pre_init(22050, -16, 1, 512)
    except Exception:  # pylint: disable-msg=W0703
        pass


def init():
    """Initialize mixer and load all sounds. Game works without sound."""
    global enabled, _music_channel, _step_channel
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init(22050, -16, 1, 512)
        pygame.mixer.set_num_channels(16)
        _music_channel = pygame.mixer.Channel(0)
        _step_channel = pygame.mixer.Channel(1)
        for name in EFFECTS + INTRO_MUSIC:
            path = os.path.join(gl.data_folder, name + ".wav")
            if os.path.exists(path):
                sounds[name] = pygame.mixer.Sound(path)
                sounds[name].set_volume(VOLUME)
        enabled = True
        logging.info("Sound initialized: %d sounds loaded", len(sounds))
    except Exception as ex:  # pylint: disable-msg=W0703
        enabled = False
        logging.warning("Sound disabled: %s", ex)


def play(name):
    """Play a sound effect."""
    if enabled and name in sounds:
        sounds[name].play()


def footstep():
    """Footsteps use their own channel so they don't pile up."""
    if enabled and "footstep" in sounds:
        if not _step_channel.get_busy():
            _step_channel.play(sounds["footstep"])


def start_music(phrases=None):
    """Start looping music built from sampled phrases."""
    global _music, _music_pos
    if not enabled:
        return
    _music = [sounds[p] for p in (phrases or INTRO_MUSIC) if p in sounds]
    _music_pos = 0
    if _music:
        _music_channel.play(_music[0])
        _music_pos = 1 % len(_music)
        _music_channel.queue(_music[_music_pos])


def update_music():
    """Keep the music queue filled. Call once per frame."""
    global _music_pos
    if enabled and _music and _music_channel.get_queue() is None:
        _music_pos = (_music_pos + 1) % len(_music)
        _music_channel.queue(_music[_music_pos])


def stop_music():
    global _music
    _music = []
    if enabled:
        _music_channel.stop()


def stop_all():
    stop_music()
    if enabled:
        pygame.mixer.stop()
