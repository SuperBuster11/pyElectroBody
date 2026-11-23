"""Gameplay module"""

import emglobals as gl
import emdata as da
import emsound as sound
from emglobals import XY
import pygame
import copy


class Controller:
    """
    Class representing player's input.
    Currently only keyboard is reported.
    Joystick and gamepad controllers planned for the future.
    Singleton by design.
    """
    def __init__(self):
        # pylint complains when those are defined via calling clear()
        self.left = False
        self.right = False
        self.up = False
        self.down = False
        self.fire = False
        self.debug = False

    def clear(self):
        self.left = False
        self.right = False
        self.up = False
        self.down = False
        self.fire = False
        self.debug = False

    def update(self):
        """Update controller settings"""
        self.clear()
        keys = pygame.key.get_pressed()
        mods = pygame.key.get_mods()
        if not (mods & (pygame.KMOD_CTRL |
                        pygame.KMOD_SHIFT |
                        pygame.KMOD_ALT)):
            if keys[pygame.K_LEFT]:
                self.left = True
            if keys[pygame.K_RIGHT]:
                self.right = True
            if keys[pygame.K_UP]:
                self.up = True
            if keys[pygame.K_DOWN]:
                self.down = True
            if keys[pygame.K_SPACE]:
                self.fire = True
        else:
            self.debug = True


class FSM:
    """Very simple Finite State Machine for entities."""
    def __init__(self):
        self.next_state = None
        self.state = lambda: None

    def switch_state(self, state):
        """Enter a new state immediately."""
        self.state = state
        self.state(True)

    def new_state(self, state):
        """Change to a new state in next frame."""
        self.next_state = state

    def run_fsm(self):
        """Cheange to a new state or run current."""
        if self.next_state:
            state = self.next_state
            self.next_state = None
            self.switch_state(state)
        else:
            self.state()


class Entity:
    def __init__(self, sprites, position):
        assert isinstance(sprites, list)
        self.sprites = sprites
        if not isinstance(position, XY):
            raise ValueError("Entity position must by XY() instance.")
        self.position = position
        self.frame = 0
        self.delay = 0
        self.deferred = None
        self.origin = None

    def set_origin(self, screen):
        self.origin = screen

    def set_position(self, position):
        """Set entity position"""
        if not isinstance(position, XY):
            raise ValueError("Entity position must by XY() instance.")
        # create a copy not just reference
        self.position = XY.from_self(position)

    def get_position(self):
        """
        Return entity's position as XY(x, y).
        May be changed by the referring code!
        """
        return self.position

    def copy_position(self):
        """
        Return a copy of entity's position as XY(x, y).
        """
        return self.position.copy()

    def get_x(self):
        return self.position.x

    def get_y(self):
        return self.position.y

    def get_bbox(self):
        """Return bounding box for current sprite frame as pygame.Rect."""
        return self.sprites[self.frame].bbox

    def get_sides(self):
        """Return boolean table with colliding sides for the current sprite."""
        return self.sprites[self.frame].collide

    def get_top(self):
        return self.sprites[self.frame].bbox.top + self.get_y()

    def is_touchable(self):
        return self.sprites[self.frame].flag("touchable")

    def get_touch(self):
        return self.sprites[self.frame].touch

    def vanish(self):
        """Remove itself from the current screen and the level definition"""
        screen = gl.screen_manager.get_screen()
        if screen and self in screen.active:
            screen.active.remove(self)
        if self.origin and self in self.origin.active:
            self.origin.active.remove(self)

    def get_abs_bbox(self):
        """Return bounding box in screen coordinates."""
        rect = self.get_bbox().copy()
        rect.move_ip(self.get_position())
        return rect

    def update(self):
        """Standard empty update method."""
        pass

    def name(self):
        """Return my class name."""
        return self.__class__.__name__

    def display(self):
        """
        Standard display method.
        Use sprite indicate by self.frame
        """
        sprite = self.sprites[self.frame]
        if not sprite.flag("in_front"):
            gl.display.blit(sprite.image, self.get_position())
            if gl.show_collisions and sprite.flag("active"):
                # show collision box or lines
                self.display_collisions(pygame.Color(255, 255, 0))
            return None
        else:
            return self.display_deferred

    def display_deferred(self):
        """Deferred display method usef for in_front sprites."""
        gl.display.blit(self.sprites[self.frame].image, self.get_position())
        if gl.show_collisions:
            # show collision box or lines
            self.display_collisions(pygame.Color(255, 255, 0))

    def display_collisions(self, color=pygame.Color(255, 0, 255)):
        """Display collision lines depending on collision sides."""
        x, y, w, h = self.sprites[self.frame].bbox
        collide = self.sprites[self.frame].collide
        position = self.get_position()
        if collide["T"]:
            sp = position + (x, y)
            ep = position + (x + w - 1, y)
            pygame.draw.line(gl.display, color, sp, ep)
        if collide["L"]:
            sp = position + (x, y)
            ep = position + (x, y + h - 1)
            pygame.draw.line(gl.display, color, sp, ep)
        if collide["R"]:
            sp = position + (x + w - 1, y)
            ep = position + (x + w - 1, y + h - 1)
            pygame.draw.line(gl.display, color, sp, ep)
        if collide["B"]:
            sp = position + (x, y + h - 1)
            ep = position + (x + w - 1, y + h - 1)
            pygame.draw.line(gl.display, color, sp, ep)

    def check_ground(self, screen):
        """
        Return distance from the bottom of entity's bounding box to the ground.
        Negative value means the entity BB is already in the ground (collides
        at the start).
        Offset moves starting point before check is made.
        """
        result = (gl.SCREEN_Y * (gl.SPRITE_Y + 1))
        if screen:
            bbox = self.get_bbox()
            x = bbox.left + self.get_x()
            y = bbox.top + bbox.height + self.get_y()
            w = bbox.width
            h = (gl.SCREEN_Y * gl.SPRITE_Y) - y
            me = pygame.Rect(x, y, w, h)
            #pygame.draw.rect(gl.display, pygame.Color(255, 255, 255), me, 1)
            collided = []
            for obj in screen.collisions:
                you = obj.get_bbox().copy()
                you.move_ip(obj.get_position())
                if me.colliderect(you):
                    collided.append(obj)
            if collided:
                # sorted by y position - probably not necessary anyway
                collided.sort(key=lambda o: o.get_top())
                for coll in collided:
                    # needs to collide from top
                    if coll.get_sides()["T"]:
                        ctop = coll.get_top()
                        result = ctop - y
                        break
        return result

    def check_collision(self, offset, screen, ignore_ground=False):
        """Check collision at offset."""
        collided = False
        if screen:
            me = self.get_bbox().copy()
            me.move_ip(self.get_position() + offset)
            for obj in screen.collisions:
                you = obj.get_bbox().copy()
                you.move_ip(obj.get_position())
                if me.colliderect(you):
                    sides = obj.get_sides()
                    if (offset[0] > 0) and sides["L"]:
                        # move right and left side
                        collided = collided if collided else True
                    elif (offset[0] < 0) and sides["R"]:
                        # move left and right side
                        collided = collided if collided else True
                    elif (offset[1] > 0) and sides["T"] and not ignore_ground:
                        # move down and top side
                        collided = collided if collided else True
                    elif (offset[1] < 0) and sides["B"]:
                        # move up and bottom side
                        collided = collided if collided else True
        return collided

    def get_touching(self, offset, screen):
        """Return objects touching at offset."""
        touched = []
        if screen:
            me = self.get_bbox().copy()
            me.move_ip(self.get_position() + offset)
            for obj in screen.active:
                you = obj.get_bbox().copy()
                you.move_ip(obj.get_position())
                if me.colliderect(you) and obj.is_touchable():
                    touched.append(obj)
        return touched

    def check_move(self, offset, screen, ignore_ground=False):
        """Check move possibility (offset - move vector)."""
        ox, oy = offset
        touched = []
        assert (ox & oy & 0x01) == 0
        if (ox == 0) and (oy == 0):
            touched.extend(self.get_touching((0, 0), screen))
            return XY(0, 0), touched
        nx, ny = 0, 0
        last_not_colliding = 0, 0
        swap_xy = False
        if abs(ox) < abs(oy):
            swap_xy = True
            oy, ox = ox, oy
        sy = (float(oy) / abs(ox)) * 2
        fy = 0.01
        # pylint: disable-msg=W0612
        # mutilsampling check with step 2 pixels
        for step in range(abs(ox) // 2):
            nx += 2 * ((ox > 0) - (ox < 0))
            fy += sy
            ny = int(fy) & ~0x1
            if swap_xy:
                current_offset = ny, nx
            else:
                current_offset = nx, ny
            touched.extend(self.get_touching(current_offset, screen))
            if self.check_collision(current_offset, screen, ignore_ground):
                break
            last_not_colliding = current_offset
        # pylint: enable-msg=W0612
        return XY.from_tuple(last_not_colliding), touched

    def set_initial_delay(self, mode, param):
        """Set initial delay depending on mode or object's position."""
        pos = self.get_position()
        if mode == 0:
            self.delay = ((pos.x // gl.SPRITE_X)
                          + (pos.y // gl.SPRITE_Y)) % (param + 1)
        elif mode == 1:
            self.delay = (pos.x // gl.SPRITE_X) % (param + 1)
        elif mode == 2:
            self.delay = (pos.y // gl.SPRITE_Y) % (param + 1)
        elif mode == 3:
            self.delay = 0
        elif mode == 4:
            self.delay = gl.random(param + 1)
        elif mode == 5:
            self.delay = gl.screen_randoms[pos.x // gl.SPRITE_X] % (param + 1)
        elif mode == 6:
            self.delay = gl.screen_randoms[pos.y // gl.SPRITE_Y] % (param + 1)
        elif mode == 7:
            self.frame = gl.random(len(self.sprites))
            self.delay = 0

class ScreenManager:
    """
    Screen manager class.
    Manages rooms (screens) from loaded level.
    Singleton by design.
    """
    def __init__(self):
        self.current_screen = 0  # current screen
        self.screens = None  # all screens
        self.screen = None  # current screen definition
        self.new_objects = [] # new objects created for current frame

    def add_screens(self, screens):
        self.screens = screens

    def get_screen(self):
        """
        Return active screen definition.
        """
        return self.screen

    def get_screens(self):
        """
        Return all screen definitions.
        """
        return self.screens

    def get_screen_number(self):
        return self.current_screen

    def inspect_screen(self, screen_number):
        """
        Return screen definition for inspection.
        Don't initialize it (the current screen won't change.
        """
        if (screen_number < 0) or (screen_number > 255):
            raise ValueError("Screen number out of range (0, 255).")
        if self.screens:
            return self.screens[screen_number]

    def change_screen(self, screen_number):
        if (screen_number < 0) or (screen_number > 255):
            raise ValueError("Screen number out of range (0, 255).")
        if self.screens:
            gl.init_screen_randoms(screen_number)
            self.current_screen = screen_number
            # changing screen reinitializes its content
            self.screen = da.Screen()
            cs = self.screens[self.current_screen]
            if cs:
                self.screen.background = copy.copy(cs.background)
                self.screen.collisions = copy.copy(cs.collisions)
                self.screen.active = copy.copy(cs.active)
            else:
                self.screen = None

    def add_active(self, object):
        """
        Add new objects to waiting queue.
        They will be displayed but not updated in this frame.
        """
        self.new_objects.append(object)

    def update_active(self):
        """
        Update list of active objects with objects from new objects queue.
        """
        if self.new_objects:
            if self.screen:
                self.screen.active.extend(self.new_objects)
            self.new_objects = []

class ActiveCheckpoint:
    """
    Active checkpoint class.
    References currently active checkpoint.
    Singleton by design.
    """
    def __init__(self):
        self.level = None
        self.screen = None
        self.position = None

    def update(self, level, screen, position):
        self.level = level
        self.screen = screen
        self.position = position

    def get_level(self):
        return self.level

    def get_screen(self):
        return self.screen

    def get_position(self):
        return self.position


class Cycle(Entity):
    def __init__(self, sprites, position):
        Entity.__init__(self, sprites, position)

    def update(self):
        if self.delay > 0:
            self.delay -= 1
        else:
            self.frame = (self.frame + 1) % len(self.sprites)
            self.delay = self.sprites[self.frame].param


class CyclePlus(Entity):
    def __init__(self, sprites, position):
        Entity.__init__(self, sprites, position)
        self.show = False
        self.empty_delay = 0

    def update(self):
        if self.delay > 0:
            self.delay -= 1
        else:
            if not self.show:
                self.show = True
            self.frame = (self.frame + 1) % len(self.sprites)
            if self.frame == 0:
                self.show = False
            if self.show:
                self.delay = self.sprites[self.frame].param
            else:
                self.delay = self.empty_delay

    def display(self):
        if self.show:
            Entity.display(self)

    def is_touchable(self):
        if self.show:
            return Entity.is_touchable(self)

    def get_touch(self):
        if self.show:
            return Entity.get_touch(self)
        else:
            return 0

class Pulse(Entity):
    def __init__(self, sprites, position):
        Entity.__init__(self, sprites, position)
        self.direction = 1  # 1 up -1 down

    def update(self):
        if self.delay > 0:
            self.delay -= 1
        else:
            self.frame += self.direction
            if self.frame < 0:
                self.frame = 0
                self.direction *= -1
            elif self.frame == len(self.sprites):
                self.frame -= 1
                self.direction *= -1
            self.delay = self.sprites[self.frame].param


class PulsePlus(Entity):
    def __init__(self, sprites, position):
        Entity.__init__(self, sprites, position)
        self.direction = 1  # 1 up -1 down
        self.show = False
        self.empty_delay = 0

    def update(self):
        if self.delay > 0:
            self.delay -= 1
        else:
            if not self.show:
                self.show = True
            self.frame += self.direction
            if self.frame < 0:
                self.show = False
                self.frame = 0
                self.direction *= -1
            elif self.frame == len(self.sprites):
                self.frame -= 1
                self.direction *= -1
            if self.show:
                self.delay = self.sprites[self.frame].param
            else:
                self.delay = self.empty_delay

    def display(self):
        if self.show:
            Entity.display(self)

    def is_touchable(self):
        if self.show:
            return Entity.is_touchable(self)

    def get_touch(self):
        if self.show:
            return Entity.get_touch(self)
        else:
            return 0

class Flash(Entity):
    def __init__(self, sprites, position):
        Entity.__init__(self, sprites, position)
        self.show = False

    def display(self):
        if self.show:
            Entity.display(self)

    def update(self):
        if self.delay > 0:
            self.delay -= 1
        else:
            self.show = not self.show
            self.delay = self.sprites[self.frame].param


class FlashPlus(Entity):
    def __init__(self, sprites, position):
        Entity.__init__(self, sprites, position)
        self.show = False

    def display(self):
        if self.show:
            Entity.display(self)

    def update(self):
        if self.delay > 0:
            self.delay -= 1
        else:
            self.show = not self.show
            self.delay = self.sprites[self.frame].param

    def get_touch(self):
        if self.show:
            return Entity.get_touch(self)
        else:
            return 0


class FlashSpecial(Entity):
    def __init__(self, sprites, position):
        Entity.__init__(self, sprites, position)
        self.show = False

    def display(self):
        if self.show:
            Entity.display(self)

    def update(self):
        if self.delay > 0:
            self.delay -= 1
        else:
            self.show = not self.show
            self.delay = 2


class Rocket(Entity):
    """
    Waits until the player passes under (or over) it, then launches.
    Explodes on walls, reloads at the starting position after a while.
    """
    DIRECTION = 1  # 1 down, -1 up
    RELOAD = 40  # frames before the rocket appears again

    def __init__(self, sprites, position):
        Entity.__init__(self, sprites, position)
        self.start = XY.from_self(position)
        self.flying = False
        self.speed = 0
        self.reload = 0
        self.ignored = []

    def is_touchable(self):
        return self.reload == 0 and Entity.is_touchable(self)

    def get_touch(self):
        return Entity.get_touch(self) if self.reload == 0 else 0

    def display(self):
        if self.reload == 0:
            return Entity.display(self)
        return None

    def player_in_range(self):
        player = gl.player
        if player is None or not player.is_alive():
            return False
        me = self.get_abs_bbox()
        target = player.get_abs_bbox()
        if target.right < me.left - 16 or target.left > me.right + 16:
            return False
        if self.DIRECTION > 0:
            return target.top > me.top
        return target.bottom < me.bottom

    def explode(self):
        sound.play("xplosion")
        add_explosion(self.get_position())
        self.flying = False
        self.reload = self.RELOAD
        self.set_position(self.start)

    def update(self):
        if self.reload:
            self.reload -= 1
            return
        if not self.flying:
            if self.player_in_range():
                self.flying = True
                self.speed = 4
                # ignore walls the rocket is mounted in
                start = self.get_abs_bbox()
                start.h += gl.SPRITE_Y // 2
                if self.DIRECTION < 0:
                    start.y -= gl.SPRITE_Y // 2
                screen = gl.screen_manager.get_screen()
                self.ignored = [obj for obj in (screen.collisions if screen else [])
                                if start.colliderect(obj.get_abs_bbox())]
                sound.play("laser")
            return
        max_speed = min(max(self.sprites[0].param * 2, 8), 16)
        self.speed = min(self.speed + 2, max_speed)
        self.set_position(self.get_position() + XY(0, self.speed * self.DIRECTION))
        rect = self.get_abs_bbox()
        if rect.bottom < 0 or rect.top > gl.MAX_Y:
            self.flying = False
            self.reload = self.RELOAD
            self.set_position(self.start)
            return
        screen = gl.screen_manager.get_screen()
        if screen:
            for obj in screen.collisions:
                if obj not in self.ignored and rect.colliderect(obj.get_abs_bbox()):
                    self.explode()
                    return


class RocketUp(Rocket):
    DIRECTION = -1


class RocketDown(Rocket):
    DIRECTION = 1


class KillingFloor(Entity):
    """
    Level editor marker: falling out of the bottom of this screen kills.
    Invisible in game.
    """
    def __init__(self, sprites, position):
        Entity.__init__(self, sprites, position)

    def display(self):
        if gl.show_collisions:
            gl.display.blit(self.sprites[0].image, self.get_position())
        return None

    def is_touchable(self):
        return False


class Monitor(Entity):
    def __init__(self, sprites, position):
        Entity.__init__(self, sprites, position)


class Display(Entity):
    def __init__(self, sprites, position):
        Entity.__init__(self, sprites, position)


class Checkpoint(Entity):
    def __init__(self, sprites, position):
        Entity.__init__(self, sprites, position)


class Teleport(Entity):
    def __init__(self, sprites, position):
        Entity.__init__(self, sprites, position)


class TeleportBase(Entity):
    def __init__(self, sprites, position):
        Entity.__init__(self, sprites, position)


class Exit(Entity):
    def __init__(self, sprites, position):
        Entity.__init__(self, sprites, position)


class Cannon(Entity):
    """Fires projectiles in one direction at regular intervals."""
    STEP = XY(0, 0)
    SPEED = 8

    def __init__(self, sprites, position):
        Entity.__init__(self, sprites, position)
        self.projectile = None  # projectile sprite (set by level loader)
        self.interval = 30  # frames between shots

    def setup(self, projectile, interval, mode):
        self.projectile = projectile
        self.interval = max(interval, 10)
        self.set_initial_delay(mode, self.interval)

    def update(self):
        if self.projectile is None:
            return
        if self.delay > 0:
            self.delay -= 1
            return
        self.delay = self.interval
        step = XY(self.STEP.x * self.SPEED, self.STEP.y * self.SPEED)
        position = self.get_position() + XY(self.STEP.x * gl.SPRITE_X // 2,
                                            self.STEP.y * gl.SPRITE_Y // 2)
        gl.screen_manager.add_active(EnemyShot(self.projectile, position, step))
        sound.play("shoot")


class CannonLeft(Cannon):
    STEP = XY(-1, 0)


class CannonRight(Cannon):
    STEP = XY(1, 0)


class CannonUp(Cannon):
    STEP = XY(0, -1)


class CannonDown(Cannon):
    STEP = XY(0, 1)


class Explosion(Entity):
    """Short explosion animation, removes itself when finished."""
    def __init__(self, position):
        Entity.__init__(self, gl.weapons.weapon["EXPLOSION"].anims, position)

    def update(self):
        self.frame += 1
        if self.frame >= len(self.sprites):
            self.frame = len(self.sprites) - 1
            self.vanish()

    def display(self):
        gl.display.blit(self.sprites[self.frame].image, self.get_position())


def add_explosion(position):
    gl.screen_manager.add_active(Explosion(XY.from_self(position)))


def rects_overlap(entity, other):
    return entity.get_abs_bbox().colliderect(other.get_abs_bbox())


class EnemyShot(Entity):
    """Enemy projectile. Kills the player on contact."""
    deadly = True

    def __init__(self, sprite, position, step):
        Entity.__init__(self, [sprite], position)
        self.step = step  # XY move vector per frame

    def update(self):
        self.set_position(self.get_position() + self.step)
        rect = self.get_abs_bbox()
        if (rect.right < 0 or rect.left > gl.MAX_X or
                rect.bottom < 0 or rect.top > gl.MAX_Y):
            self.vanish()
            return
        player = gl.player
        if player and player.is_alive() and not player.invulnerable and \
                rect.colliderect(player.get_abs_bbox()):
            player.die()
            self.vanish()
            return
        screen = gl.screen_manager.get_screen()
        if screen:
            for obj in screen.collisions:
                if rect.colliderect(obj.get_abs_bbox()):
                    self.vanish()
                    return

    def display(self):
        gl.display.blit(self.sprites[0].image, self.get_position())


class Enemy(Entity):
    """
    Base class for enemies.
    Walks (or flies) left and right, turns around at walls,
    platform edges and screen borders, shoots at the player.
    """
    deadly = True
    flying = False
    SPEED = 4

    def __init__(self, sprites, position):
        Entity.__init__(self, sprites, position)
        self.shoots = False
        self.anims = None
        self.frames = 0
        self.frame = 0  # index to self.sprites - always 0
        self.anim_frame = 0
        self.kind = 0
        self.direction = -1  # -1 left, 1 right
        self.cooldown = 0
        self.anim = "MLEFT"

    def setup(self):
        """Called after anims are assigned."""
        self.direction = -1 if gl.random(2) == 0 else 1
        self.anim = "MLEFT" if self.direction < 0 else "MRIGHT"
        self.anim_frame = gl.random(len(self.anims[self.anim]))
        self.cooldown = 10 + gl.random(30)

    def get_bbox(self):
        """Single bounding box for all frames - avoids jitter."""
        return self.anims["MLEFT"][0].bbox

    def get_sides(self):
        return {"L": True, "R": True, "T": True, "B": True}

    def is_touchable(self):
        return False

    def get_touch(self):
        return 0

    def display(self):
        anim = self.anims[self.anim]
        gl.display.blit(anim[self.anim_frame % len(anim)].image,
                        self.get_position())
        if gl.show_collisions:
            pygame.draw.rect(gl.display, pygame.Color(255, 0, 0),
                             self.get_abs_bbox(), 1)

    def wall_ahead(self, rect, screen):
        if rect.left < 0 or rect.right > gl.MAX_X:
            return True
        side = "L" if self.direction > 0 else "R"
        for obj in screen.collisions:
            if rect.colliderect(obj.get_abs_bbox()) and obj.get_sides()[side]:
                return True
        return False

    def ground_below(self, x, rect, screen):
        probe = pygame.Rect(x, rect.bottom, 2, 8)
        for obj in screen.collisions:
            if probe.colliderect(obj.get_abs_bbox()) and obj.get_sides()["T"]:
                return True
        return False

    def can_move(self, step, screen):
        rect = self.get_abs_bbox()
        rect.move_ip((step, 0))
        if self.wall_ahead(rect, screen):
            return False
        for obj in screen.active:
            if obj is not self and isinstance(obj, Enemy):
                other = obj.get_abs_bbox()
                if rect.colliderect(other) and \
                        (other.centerx - rect.centerx) * self.direction > 0:
                    return False  # bumped into another enemy
        if not self.flying:
            front = rect.right - 2 if self.direction > 0 else rect.left
            if not self.ground_below(front, rect, screen):
                return False
        return True

    def walk(self, screen):
        step = self.SPEED * self.direction
        if self.can_move(step, screen):
            self.set_position(self.get_position() + XY(step, 0))
        else:
            self.direction = -self.direction
            if not self.can_move(self.SPEED * self.direction, screen):
                self.direction = -self.direction  # stuck - keep facing
        self.anim = "MLEFT" if self.direction < 0 else "MRIGHT"

    def player_target(self):
        """Return player's bbox if the player can be shot at."""
        player = gl.player
        if player is None or not player.is_alive():
            return None
        return player.get_abs_bbox()

    def shoot(self):
        target = self.player_target()
        if target is None:
            return
        me = self.get_abs_bbox()
        if target.bottom < me.top or target.top > me.bottom:
            return  # not on the same height
        if (target.centerx - me.centerx) * self.direction <= 0:
            return  # player is behind
        name = "SLEFT" if self.direction < 0 else "SRIGHT"
        sprite = self.anims[name][0]
        speed = max(sprite.param, 6) + 4
        if self.direction < 0:
            x = me.left - (sprite.bbox.x + sprite.bbox.w)
        else:
            x = me.right - sprite.bbox.x
        y = me.centery - sprite.bbox.centery
        shot = EnemyShot(sprite, XY(x, y), XY(speed * self.direction, 0))
        gl.screen_manager.add_active(shot)
        sound.play("eshoot")
        self.cooldown = 20 + gl.random(30)

    def update(self):
        screen = gl.screen_manager.get_screen()
        if not screen:
            return
        self.anim_frame = (self.anim_frame + 1) % len(self.anims[self.anim])
        self.walk(screen)
        if self.cooldown > 0:
            self.cooldown -= 1
        elif self.shoots:
            self.shoot()

    def hit(self):
        """Hit by player's projectile."""
        sound.play("xplosion")
        add_explosion(self.get_position())
        self.vanish()


class EnemyPlatform(Enemy):
    SPEED = 4


class EnemyFlying(Enemy):
    """Flies left and right, drops bombs on the player below."""
    flying = True
    SPEED = 4

    def shoot(self):
        target = self.player_target()
        if target is None:
            return
        me = self.get_abs_bbox()
        if target.top < me.bottom or abs(target.centerx - me.centerx) > 24:
            return
        sprite = self.anims["SLEFT"][0] if "SLEFT" in self.anims else None
        if sprite is None:
            return
        speed = max(sprite.param, 6) + 4
        x = me.centerx - sprite.bbox.centerx
        y = me.bottom - sprite.bbox.y
        shot = EnemyShot(sprite, XY(x, y), XY(0, speed))
        gl.screen_manager.add_active(shot)
        sound.play("eshoot")
        self.cooldown = 15 + gl.random(20)


# -----------------------------------------------------------------------------
# test code below

def main():
    pass

if __name__ == "__main__":
    main()
