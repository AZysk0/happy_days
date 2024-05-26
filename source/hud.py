import pygame
import ctypes
from typing import Tuple
from config import *


class HitpointsBar:

    def __init__(self, pos_tuple: Tuple, wh_tuple: Tuple, max_hp: float):
        if len(pos_tuple) != 2:
            raise ValueError("position tuple must be 2-element (upper-left rect corner pos)")
        
        if len(wh_tuple) != 2:
            raise ValueError("size tuple must be 2-element (width, height)")

        self.x, self.y = pos_tuple
        self.w, self.h = wh_tuple
        self.current_hp = max_hp
        self.max_hp = max_hp

    def update_hp_status(self, player_hp):
        self.current_hp = player_hp

    def draw(self, screen_ptr: pygame.Surface):
        #calculate health ratio
        ratio = self.current_hp / self.max_hp
        pygame.draw.rect(screen_ptr, "red", (self.x, self.y, self.w, self.h))
        pygame.draw.rect(screen_ptr, "green", (self.x, self.y, self.w * ratio, self.h))


class EnergyBar:

    def __init__(self) -> None:
        pass


class HeadupDisplay():

    def __init__(self, player_max_hp: float) -> None:

        self.hp_bar = HitpointsBar((HP_BAR_XPOS, HP_BAR_YPOS), (HP_BAR_WIDTH, HP_BAR_HEIGHT), player_max_hp)
        # self.energy_bar = EnergyBar()
    
    def update_hud(self, player_current_hp: float) -> None:
        self.hp_bar.update_hp_status(player_current_hp)

    def draw_hud_elements(self, screen_ptr: pygame.Surface) -> None:
        self.hp_bar.draw(screen_ptr)
