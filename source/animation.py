import numpy as np
import numpy.linalg as linalg
import numba
import pygame
import copy
import ctypes


class Animation: 

    def __init__(self) -> None:
        self.bg_max_particles = 0

    def create_enemy_death_effect(self):
        # expolosion with particles
        ...
    
    def remove_enemy_death_effect(self):
        ...
    
    def background(self):
        # lonely chaotic particles appear and disappear
        ...


    def update_state(self, dt: float):
        ...
