import numpy as np
import numpy.linalg as linalg
import itertools
import pygame
import copy
import random

from typing import Tuple, List, Union

# ======= CONSTANTS ===========
PLAYER_MAX_VELOCITY = 1
EPSILON = 0.000001
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 400
ENEMY_ON_SPAWN_MIN_DIST = 1.5

# ===========


# ========== HELPER FUNCTIONS =======================
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
    xpos, ypos = gl_pos
    w, h = viewport
    x_mapped = (xpos + 1) * 0.5 * w
    y_mapped = (-ypos + 1) * 0.5 * h
    return np.array([x_mapped, y_mapped])


def map_pg_to_opengl_coordinates_2d(pg_pos, viewport):
    xpos, ypos = pg_pos
    w, h = viewport
    gl_xpos = -1 + xpos * (2 / w)
    gl_ypos = -(ypos * (2 / h) - 1)
    return np.array([gl_xpos, gl_ypos])


# ====================================


# TODO
class Wall: ...
class Animation: ...

# ================== PLAYER LOGIC =================================
class Bullet:
    
    def __init__(self, gl_pos: np.array, dir_vec: np.array, pg_radius, speed) -> None:
        self.gl_pos = gl_pos
        self.dir_vec = dir_vec
        self.pg_radius = pg_radius
        self.speed = speed
    
    def update(self, dt) -> None:
        self.gl_pos += self.dir_vec * self.speed * dt

    def check_collision(self, game_object) -> bool:
        ...


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

        self.base_shoot_frequency = 0.1
        self.base_bullet_radius = 5
        self.base_bullet_speed = 5

        self.cooldown_shoot = 0.0
        self.cooldown_dash = 0.0

        self.bullets_alive = []

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

    def check_collision(self, game_object):
        return False

    def update_position(self, dt):
        speed = 1
        self.current_position = self.current_position + self.current_velocity * dt * speed

    def update_current_weapon_direction(self, m_xpos, m_ypos):
        viewport = np.array([WINDOW_WIDTH, WINDOW_HEIGHT])
        mpos_vector = map_pg_to_opengl_coordinates_2d(np.array([m_xpos, m_ypos]), viewport)
        new_direction = mpos_vector - self.current_position
        self.current_weapon_direction = new_direction / linalg.norm(new_direction)
    
    def update_velocity_vector(self, keys_pressed):
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

    def update_state(self, dt: float, m_xpos, m_ypos):
        self.update_position(dt)
        self.update_current_weapon_direction(m_xpos, m_ypos)
        self.update_bullets_state(dt)
        self.update_cooldowns(dt)


class Enemy:
    
    def __init__(self, gl_pos: np.array) -> None:
        self.gl_pos = gl_pos
        self.current_velocity = np.array([0, 0])
        self.radius = 5

        self.base_hitpoints = 5
        self.base_armor = 0.0
        self.base_speed = 0.5

    def update_velocity(self, player_gl_pos: np.array):
        new_velocity_vector = player_gl_pos - self.gl_pos
        norm = linalg.norm(new_velocity_vector)
        self.current_velocity = new_velocity_vector.copy()  # is copy necessary?
        if norm < EPSILON:
            return
        
        self.current_velocity /= norm
    
    def update_position(self, dt):
        self.gl_pos += self.current_velocity * self.base_speed * dt
    
    def update_state(self, dt: float, player_gl_pos: np.array):
        self.update_velocity(player_gl_pos)
        self.update_position(dt)

# ======================
class Camera:

    def __init__(self) -> None:
        self.gl_pos = ...

    def apply(self, object_gl_pos):
        ...
    
    def shake(self):
        ...


class Scene():

    def __init__(self) -> None:
        self.player = Player()
        self.enemies_alive = []
        self.items = None
        self.max_enemies = 5
        
    def add_random_enemy(self):
        player_gl_pos = self.player.current_position
        enemy_gl_pos = (np.random.random(size=2) - 0.5) * 2 + EPSILON
        enemy_direction = enemy_gl_pos - player_gl_pos
        enemy_direction /= linalg.norm(enemy_gl_pos)
        enemy_new_gl_pos = player_gl_pos + ENEMY_ON_SPAWN_MIN_DIST * enemy_direction
        new_enemy = Enemy(enemy_new_gl_pos)
        self.enemies_alive.append(new_enemy)

    def add_enemies(self):
        while len(self.enemies_alive) < 5:
            self.add_random_enemy()
    
    def remove_enemies(self):
        ...

    def update_enemies(self, dt: float, player_gl_pos: np.array):
        for enemy in self.enemies_alive:
            enemy.update_state(dt, player_gl_pos)


