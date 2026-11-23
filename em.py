"""Main game module"""

import emglobals as gl
from emglobals import XY
import emdata as da
import emgame as ga
import emdisplay as di
import emhero as pl
import emother as ot
import emsound as sound
import emintro as intro
import pygame
import logging
import time


class Gameplay:
    """
    Main gameplay functionality class.
    Singleton by design.
    """
    def __init__(self):
        gl.level = da.Level()
        self.controller = ga.Controller()
        # initialize a few global objects
        # thus loading associated sprite sets
        gl.screen_manager = ga.ScreenManager()
        gl.player = pl.PlayerEntity(self.controller)
        gl.enemies = ot.Enemies()
        gl.weapons = ot.Weapons()
        gl.info = ot.Info()
        di.indicators = di.Indicators()
        gl.checkpoint = ga.ActiveCheckpoint()
        # initialize rest
        self.screens_map = None
        self.deferred = []
        # keys reacting once per key press
        self.key_handlers = {pygame.K_ESCAPE: self.on_k_escape,
                             pygame.K_TAB: self.on_k_tab,
                             pygame.K_F1: self.on_k_f1,
                             pygame.K_LEFT: self.on_k_left,
                             pygame.K_RIGHT: self.on_k_right,
                             pygame.K_UP: self.on_k_up,
                             pygame.K_DOWN: self.on_k_down}
        for number, key in enumerate([pygame.K_0, pygame.K_1, pygame.K_2,
                                      pygame.K_3, pygame.K_4, pygame.K_5,
                                      pygame.K_6, pygame.K_7, pygame.K_8]):
            self.key_handlers[key] = lambda n=number: self.on_k_number(n)

    def init_map(self):
        """Initialize level map"""
        # pylint: disable-msg=E1121
        screens_map = pygame.Surface((32, 32))
        pixels = pygame.PixelArray(screens_map)
        # pylint: enable-msg=E1121
        FULL = 0x33AA33
        EMPTY = 0x333333
        screens = gl.screen_manager.get_screens()
        for scr in range(256):
            color = FULL if screens[scr] else EMPTY
            for dx in range(2):
                for dy in range(2):
                    pixels[(scr % 16) * 2 + dx][(scr // 16) * 2 + dy] = color
        del pixels
        return screens_map

    def show_map(self, pos):
        """Display level map (for debug only)"""
        scr = gl.screen_manager.get_screen_number()
        CURRENT = 0xFFFFFF
        # pylint: disable-msg=E1121
        screens_map_copy = pygame.Surface((32, 32))
        screens_map_copy.blit(self.screens_map, (0, 0))
        pixels = pygame.PixelArray(screens_map_copy)
        # pylint: enable-msg=E1121
        for dx in range(2):
            for dy in range(2):
                pixels[(scr % 16) * 2 + dx][(scr // 16) * 2 + dy] = CURRENT
        del pixels
        gl.window.blit(screens_map_copy, pos)

    def show_info(self):
        """Display status line"""
        di.status_line.show()

    def display_screen(self, screen):
        """Display all objects (active and background) on the screen"""
        gl.screen_manager.update_active()  # make sure new objects get displayed
        self.deferred = []
        if screen:
            for entity in screen.background:
                entity.display()
            for entity in screen.collisions:
                entity.display()
                if gl.show_collisions:
                    entity.display_collisions()
            for entity in screen.active:
                deferred = entity.display()
                if deferred:
                    self.deferred.append(deferred)

    def display_deferred(self):
        for deferred in self.deferred:
            deferred()

    def display_hero(self):
        """Display player's character"""
        gl.player.display()

    def display_indicators(self):
        """Display weapon indicators (and other icons)"""
        di.indicators.display()

    def move_player(self, offset):
        position = gl.player.get_position() + offset
        gl.player.set_position(position)

    def change_screen(self, delta):
        cs = (gl.screen_manager.get_screen_number() + delta) % 256
        gl.screen_manager.change_screen(cs)

    # developer keys: Ctrl+arrows change screens, Shift+arrows move the hero
    def on_k_left(self):
        if pygame.key.get_mods() & pygame.KMOD_CTRL:
            self.change_screen(-1)
        elif pygame.key.get_mods() & pygame.KMOD_SHIFT:
            self.move_player((-gl.SPRITE_X, 0))

    def on_k_right(self):
        if pygame.key.get_mods() & pygame.KMOD_CTRL:
            self.change_screen(1)
        elif pygame.key.get_mods() & pygame.KMOD_SHIFT:
            self.move_player((gl.SPRITE_X, 0))

    def on_k_up(self):
        if pygame.key.get_mods() & pygame.KMOD_CTRL:
            self.change_screen(-16)
        elif pygame.key.get_mods() & pygame.KMOD_SHIFT:
            self.move_player((0, -gl.SPRITE_Y))

    def on_k_down(self):
        if pygame.key.get_mods() & pygame.KMOD_CTRL:
            self.change_screen(16)
        elif pygame.key.get_mods() & pygame.KMOD_SHIFT:
            self.move_player((0, gl.SPRITE_Y))

    def on_k_tab(self):
        gl.show_collisions = not gl.show_collisions

    def on_k_f1(self):
        gl.debug = not gl.debug

    def on_k_number(self, number):
        if pygame.key.get_mods() & pygame.KMOD_SHIFT:
            if number <= 5:
                gl.player.select_weapon(number)
        elif 1 <= number <= len(gl.level_names):
            gl.current_level = number - 1
            self.load_level()

    def on_k_escape(self):
        gl.loop_main_loop = False

    def load_level(self):
        gl.level.load(gl.level_names[gl.current_level])
        gl.screen_manager.add_screens(gl.level.get_screens())
        self.screens_map = self.init_map()
        gl.disks = 0  # no disks collected after level load
        gl.level_completed = False
        gl.player.respawn()
        di.info_lines.add("poziom %d" % (gl.current_level + 1))
        sound.play("area")

    def next_level(self):
        gl.current_level = (gl.current_level + 1) % len(gl.level_names)
        self.load_level()

    def loop_begin(self):
        di.clear_screen()

    def loop_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                gl.loop_main_loop = False
                gl.quit_requested = True
            elif event.type == pygame.KEYDOWN:
                handler = self.key_handlers.get(event.key)
                if handler:
                    handler()
        self.controller.update()

    def loop_run(self):
        gl.screen = gl.screen_manager.get_screen()
        if gl.screen:
            # iterate over a copy - objects may vanish during update
            for active in list(gl.screen.active):
                active.update()
        gl.player.update()
        if gl.level_completed:
            self.next_level()

    def loop_end(self):
        self.display_screen(gl.screen)
        self.display_hero()
        self.display_deferred()
        self.display_indicators()
        if gl.debug:
            self.show_map((640 - 32 - 8, 8))
            self.show_info()

    def show(self):
        """Display the screen."""
        if gl.debug:
            di.message(XY(500, 8), "logic: {0:>4.1f}\nrender: {1:>4.1f}".format(
                round(gl.logic_time * 1000, 1), round(gl.render_time * 1000, 1)))
        di.show()

    def start(self, level=0):
        """Start a new game."""
        gl.player = pl.PlayerEntity(self.controller)
        gl.checkpoint = ga.ActiveCheckpoint()
        gl.current_level = level
        self.load_level()

    def run(self):
        gl.loop_main_loop = True
        clock = pygame.time.Clock()
        while gl.loop_main_loop:
            # logic processing starts here
            logic_start = time.perf_counter()
            self.loop_begin()
            self.loop_events()
            self.loop_run()
            gl.logic_time = time.perf_counter() - logic_start
            # logic processing ended
            # rendering starts here
            render_start = time.perf_counter()
            self.loop_end()
            gl.render_time = time.perf_counter() - render_start
            # rendering ended
            self.show()  # show the screen
            gl.counter += 1
            clock.tick(20)  # keep constant frame rate (20fps)

    def stop(self):
        sound.stop_all()


class Game:
    """
    Main game class.
    Singleton by design.
    """
    def __init__(self):
        if not gl.log_filename:
            logging.basicConfig(level=logging.DEBUG)
        else:
            try:
                logging.basicConfig(filename=gl.log_filename, filemode="w",
                                    format='%(levelname)s: %(funcName)s(): %(message)s',
                                    level=logging.DEBUG)
            except OSError:
                logging.basicConfig(level=logging.WARNING)

    def init(self):
        sound.pre_init()
        di.init_display()
        sound.init()
        
    def quit(self):
        di.quit_display()


def fast_main():
    game = Game()
    game.init()
    gameplay = Gameplay()
    title = intro.Intro()
    while not gl.quit_requested:
        if not title.run():
            break
        gameplay.start()
        gameplay.run()
        gameplay.stop()
    game.quit()


def profile_main():
    # This is the main function for profiling
    import cProfile, pstats, io
    prof = cProfile.Profile()
    prof = prof.runctx("fast_main()", globals(), locals())
    stream = io.StringIO()
    stats = pstats.Stats(prof, stream=stream)
    stats.sort_stats("calls")
    stats.print_stats(80)  # how many to print
    logging.info("Profile data:\n%s", stream.getvalue())


main = fast_main

if __name__ == "__main__":
    main()
