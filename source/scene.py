import numpy as np
import numpy.linalg as linalg
import pygame
import copy
import ctypes
import numba
import functools

from typing import Tuple, List, Union
from config import *
# ======= CONSTANTS ===========
PLAYER_MAX_VELOCITY = 1
EPSILON = 0.000001
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 400
ENEMY_ON_SPAWN_MIN_DIST = 1.5
VIEWPORT = np.array([WINDOW_WIDTH, WINDOW_HEIGHT])

# ===========


# ========== HELPER FUNCTIONS =======================
def get_translation_matrix_2d(tx: float, ty: float) -> np.array:
    '''
    returns 3x3 matrix for 2d translation
    '''
    return np.array([
        [1, 0, tx],
        [0, 1, ty],
        [0, 0, 1]
    ])


def get_scaling_matrix(sx: float, sy: float, sz: float) -> np.array:
    return np.array([
        [sx, 0, 0],
        [0, sy, 0],
        [0, 0, sz]
    ])


def get_rotation_matrix_2d(theta: float):
    ...


@numba.jit(nogil=True)
def map_opengl_to_pg_coordinates_2d(gl_pos: np.array, viewport) -> np.array:
    '''
    gl_pos: np.array - coordinates like it would be in opengl
    viewport: np.array - screensize
    (0, 0)
    (800, 400)
    (0, 0) -> (400, 200)
    '''
    if len(gl_pos) != 2 or len(viewport) != 2:
        raise ValueError(f"Wrong dimension of input vectors, gl_pos: {gl_pos.shape}, viewport: {viewport.shape}")
    
    # print(gl_pos.shape)
    # cp_gl_pos = np.append(gl_pos.copy(), 1).reshape(-1, 1)
    xpos, ypos = gl_pos
    w, h = viewport
    x_mapped = (xpos + 1) * 0.5 * w
    y_mapped = (-ypos + 1) * 0.5 * h

    # print(cp_gl_pos.shape)
    # v => translate => scale
    # new_x, new_y, _ = np.dot(get_scaling_matrix(0.5 * w, -0.5 * h, 0), np.dot(get_translation_matrix_2d(1, 1), cp_gl_pos))

    return np.array([x_mapped, y_mapped])
    # return np.array([new_x[0], new_y[0]])


@numba.jit(nogil=True)
def map_pg_to_opengl_coordinates_2d(pg_pos, viewport):
    # xpos, ypos = pg_pos
    # cp_pg_pos = np.append(pg_pos.copy(), 1).reshape(-1, 1)
    xpos, ypos = pg_pos
    w, h = viewport
    gl_xpos = -1 + xpos * (2 / w)
    gl_ypos = -ypos * (2 / h) + 1

    # print(cp_pg_pos.shape)
    # v => scale => translate
    # new_gl_xpos, new_gl_ypos, _ = \
    #     np.dot(get_translation_matrix_2d(-1, 1), np.dot(get_scaling_matrix(2 / w, -2 / h, 0), cp_pg_pos))
    # print(new_gl_xpos, new_gl_ypos)
    return np.array([gl_xpos, gl_ypos])
    # return np.array([new_gl_xpos[0], new_gl_ypos[0]])


@numba.njit
def fast_dist(v1: np.array, v2: np.array):
    v = (v1 - v2).astype('float64')
    return np.sqrt(v[0] ** 2 + v[1] ** 2)


# ====================================
# TODO
class Wall: ...
class Animation: ...


# ============ ENEMY LOGIC ==============
class Enemy:
    
    def __init__(self, gl_pos: np.array) -> None:
        self.gl_pos = gl_pos
        self.current_velocity = np.array([0, 0])
        self.radius = 10  # in pg coordinates

        self.hitpoints = 5
        self.base_armor = 0.0
        self.base_speed = 0.5
        self.base_damage = 1.0
        self.damage_multiplier = 1.0
    
    def get_damage(self):
        return self.base_damage * self.damage_multiplier

    def update_velocity(self, player_gl_pos: np.array):
        new_velocity_vector = player_gl_pos - self.gl_pos
        norm = fast_dist(player_gl_pos, self.gl_pos)
        self.current_velocity = new_velocity_vector.copy()  # is copy necessary?
        if norm < EPSILON:
            return
        
        self.current_velocity /= norm
    
    def update_position(self, dt):
        self.gl_pos += self.current_velocity * self.base_speed * dt
    
    def update_state(self, dt: float, player_gl_pos: np.array):
        self.update_velocity(player_gl_pos)
        self.update_position(dt)



# ================== PLAYER LOGIC =================================
class Bullet:
    
    def __init__(self, gl_pos: np.array, dir_vec: np.array, pg_radius, speed) -> None:
        self.gl_pos = gl_pos
        self.dir_vec = dir_vec
        self.pg_radius = pg_radius  # radius in pg coordinates
        self.speed = speed
    
    def update(self, dt) -> None:
        self.gl_pos += self.dir_vec * self.speed * dt
    
    def check_collision(self, enemy_obj) -> bool:
        enemy_pg_pos = map_opengl_to_pg_coordinates_2d(enemy_obj.gl_pos.copy(), VIEWPORT)
        bullet_pg_pos = map_opengl_to_pg_coordinates_2d(self.gl_pos.copy(), VIEWPORT)
        bullet_enemy_dist = fast_dist(bullet_pg_pos, enemy_pg_pos)
        # print(bullet_enemy_dist)
        # print(self.pg_radius, enemy_obj.radius)
        return bullet_enemy_dist  <= (self.pg_radius + enemy_obj.radius)


class Player:

    def __init__(self) -> None:
        self.current_position = np.array([0, 0]).astype("float64")
        self.current_weapon_direction = np.array([1, 0]).astype("float64")
        self.current_velocity = np.array([0, 0]).astype("float64")
        self.current_dv = np.array([0, 0]).astype("float64")

        self.hitpoints = 100
        self.base_damage = 1
        self.base_armor = 0.0
        self.base_dash_frequency = 1.0
        self.base_radius = 15

        self.damage_multiplier = 1.0

        self.base_shoot_frequency = 0.1
        self.base_bullet_radius = 5
        self.base_bullet_speed = 5

        self.cooldown_shoot = 0.0
        self.cooldown_dash = 0.0
        
        self.invincibility_time_left = 0.0
        self.is_invincible = False
        
        self.knockback_vector = np.array([0, 0])
        self.knockback_time_left = 0.0
        self.is_knockbacked = False

        self.bullets_alive: list[Bullet] = []
        self.bullets_shot = 0
        self.bullets_hit = 0

    def shoot(self):
        # create bullets
        if self.cooldown_shoot >= EPSILON:
            return
        
        new_bullet = Bullet(
            self.current_position, self.current_weapon_direction, 
            self.base_bullet_radius, self.base_bullet_speed
        )
        self.bullets_alive += [new_bullet]
        self.cooldown_shoot = self.base_shoot_frequency
        self.bullets_shot += 1

    def check_enemy_collision(self, enemy_obj) -> bool:
        if self.is_invincible:
            return False
        
        enemy_pg_pos = map_opengl_to_pg_coordinates_2d(enemy_obj.gl_pos.copy(), VIEWPORT)
        player_pg_pos = map_opengl_to_pg_coordinates_2d(self.current_position.copy(), VIEWPORT)
        return fast_dist(player_pg_pos, enemy_pg_pos) <= (self.base_radius + enemy_obj.radius)

    def get_current_damage(self):
        return self.base_damage * self.damage_multiplier

    def update_position(self, dt):
        speed = 1
        
        if self.is_knockbacked:
            speed = 2
            self.current_position = self.current_position + self.knockback_vector * dt * speed
            return
        # else
        self.current_position = self.current_position + self.current_velocity * dt * speed

    def update_current_weapon_direction(self, m_xpos, m_ypos):
        viewport = np.array([WINDOW_WIDTH, WINDOW_HEIGHT])
        mpos_vector = map_pg_to_opengl_coordinates_2d(np.array([m_xpos, m_ypos]), viewport)
        new_direction = mpos_vector - self.current_position
        self.current_weapon_direction = new_direction / linalg.norm(new_direction)
    
    def update_velocity_vector(self, keys_pressed):
        # ignore key presses when knockbacked
        if self.is_knockbacked:
            return
        keys_movement = (pygame.K_d, pygame.K_a, pygame.K_s, pygame.K_w)
        vs = (np.array([1, 0]), np.array([-1, 0]), np.array([0, -1]), np.array([0, 1]))
        keys_bitmask = tuple(map(lambda key: keys_pressed[key], keys_movement))
        current_move_vectors = [vec if is_pressed else np.array([0, 0]) for is_pressed, vec in zip(keys_bitmask, vs)]
        # print(current_move_vectors, keys_bitmask, keys_pressed)
        new_velocity_vector = sum(current_move_vectors)
        self.current_velocity = new_velocity_vector
        if linalg.norm(new_velocity_vector) < EPSILON:
            return
        
        self.current_velocity = self.current_velocity / linalg.norm(self.current_velocity)

    def update_bullets_state(self, dt):
        self.bullets_alive = list(filter(
            lambda bullet: linalg.norm(self.current_position - bullet.gl_pos) < 1.5,
            self.bullets_alive
        ))
        if len(self.bullets_alive) == 0:
            return

        for bullet in self.bullets_alive:
            bullet.update(dt)

    def update_cooldowns(self, dt):
        self.cooldown_shoot -= dt
        self.cooldown_dash -= dt
        # invincibility
        if self.is_invincible:
            self.invincibility_time_left -= dt
        if self.invincibility_time_left < 0:
            self.is_invincible = False
            self.invincibility_time_left = 0.0
        
        # knockback
        if self.is_knockbacked:
            self.knockback_time_left -= dt
        if self.knockback_time_left < 0:
            self.is_knockbacked = False
            self.knockback_time_left = 0.0

    def update_state(self, dt: float, m_xpos, m_ypos):
        self.update_position(dt)
        self.update_current_weapon_direction(m_xpos, m_ypos)
        self.update_bullets_state(dt)
        self.update_cooldowns(dt)


# ======================
class Camera:
    '''
    ideas:
    - velocity vector towards player
    - nearer to player -> slower camera's speed <=>
    <=> cam speed proportional (with minus) to dist(player, cam) and have stable point "at" player
    used for moving all objects of the scene towards camera when rendering
    '''
    def __init__(self) -> None:
        self.gl_pos = np.array([0, 0]).astype('float64')
        self.current_velocity = np.array([0, 0])
        self.speed = 0

    def apply(self, object_gl_pos) -> np.array:
        return object_gl_pos - self.gl_pos
    
    def update_velocity_vector(self, player_gl_pos):
        new_velocity_vector = player_gl_pos - self.gl_pos
        # norm  = linalg.norm(new_velocity_vector)  # is it rly necessary to comput norm if i multiply it afterwards?
        self.current_velocity = new_velocity_vector

    def update_position(self, dt: float):
        self.gl_pos += self.current_velocity * dt


class Scene():

    def __init__(self) -> None:
        self.player = Player()
        self.enemies_alive: list[Enemy] = []
        self.items = None
        self.max_enemies = 5
        self.camera = Camera()
        
    def add_random_enemy(self):
        player_gl_pos = self.player.current_position
        enemy_gl_pos = (np.random.random(size=2) - 0.5) * 2 + EPSILON
        enemy_direction = enemy_gl_pos - player_gl_pos
        enemy_direction /= linalg.norm(enemy_gl_pos)
        enemy_new_gl_pos = player_gl_pos + ENEMY_ON_SPAWN_MIN_DIST * enemy_direction
        new_enemy = Enemy(enemy_new_gl_pos)
        self.enemies_alive.append(new_enemy)

    def add_enemies(self):
        while len(self.enemies_alive) < self.max_enemies:
            self.add_random_enemy()
    
    def remove_dead_enemies(self) -> int:
        # keep enemies that are alive
        enemies_alive_length = self.enemies_alive.__len__()  # before enemies removal
        self.enemies_alive = list(filter(lambda ememy: ememy.hitpoints > 0, self.enemies_alive))
        return enemies_alive_length - self.enemies_alive.__len__()  # cound enemies dead

    def update_enemies(self, dt: float, player_gl_pos: np.array):
        # parallelizable
        for enemy in self.enemies_alive:
            enemy.update_state(dt, player_gl_pos)
        
    def process_collisions(self):
        # player with enemies
        for enemy in self.enemies_alive:
            if self.player.check_enemy_collision(enemy):
                
                if not self.player.is_invincible:
                    self.player.hitpoints -= enemy.get_damage()

                # process event "player got hit from enemy" collision here
                self.player.is_invincible = True
                self.player.invincibility_time_left = 0.5

                self.player.is_knockbacked = True
                self.player.knockback_time_left = 0.2
                self.player.knockback_vector = -(enemy.gl_pos - self.player.current_position) / fast_dist(enemy.gl_pos, self.player.current_position)

        # bullets with enemies (for each bullet for each enemy)
        for i, bullet in enumerate(self.player.bullets_alive.copy()):
            # for each bullet sort enemies by dist
            fast_dist_to_current_bullet_func = functools.partial(fast_dist, bullet.gl_pos)
            bullet_enemy_dist_array = np.array(list(map(
                lambda enemy: fast_dist_to_current_bullet_func(enemy.gl_pos), self.enemies_alive
            )))
            nearest_enemy_index = bullet_enemy_dist_array.argmin()
            bullet_hit_enemy = bullet.check_collision(self.enemies_alive[nearest_enemy_index])
            if bullet_hit_enemy:
                self.player.bullets_hit += 1
                # process event "bullet hit enemy"
                self.enemies_alive[nearest_enemy_index].hitpoints -= self.player.get_current_damage()
                # print(bullet_hit_enemy, bullet_enemy_dist_array[nearest_enemy_index], sep=', ')
                self.player.bullets_alive.pop(i)
                break

