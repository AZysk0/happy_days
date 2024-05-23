import pygame
import pygame.locals as locals
import sys
import time
import numpy as np
# custom src code
from button import Button
from scene import Scene, Bullet, map_opengl_to_pg_coordinates_2d, map_pg_to_opengl_coordinates_2d
import copy

###############
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 400
WINDOW_CAPTION = "Happy Days"
###############



# ======= HELPER FUNCTIONS =============
def get_font(size):
    return pygame.font.Font("assets/font.ttf", size)



# ======= RENDER FUNCTIONS =============
def render_cursor(screen_ptr: pygame.Surface, pg_cursor_pos: np.array, size: int) -> None:
    cursor_texture = get_font(size).render('+', True, 'red')
    screen_ptr.blit(cursor_texture, pg_cursor_pos)


def render_player(screen_ptr: pygame.Surface, player_pos) -> None:
    ...


def render_bullet(screen_ptr: pygame.Surface, bullet: Bullet) -> None:
    gl_pos = bullet.gl_pos.copy()
    viewport = np.array([WINDOW_WIDTH, WINDOW_HEIGHT])
    pg_pos = map_opengl_to_pg_coordinates_2d(gl_pos, viewport)
    pygame.draw.circle(screen_ptr, "red", pg_pos, bullet.pg_radius)

# ======= GAME WINDOW ======================
class Window:

    def __init__(self) -> None:
        pygame.init()
        pygame.mixer.init()

        self.clock = pygame.time.Clock()
        
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption(WINDOW_CAPTION)

        self.main_menu_bg = pygame.image.load("assets/Main_menu_bg.png").convert()
        self.main_menu_font = pygame.font.Font("assets/font.ttf", 32)
        # 
        self.gray = "#d7fcd"
        self.main_menu_buttons = (
            Button(image=pygame.image.load("assets/Play Rect.png"), pos=(400, 50), 
                        text_input="PLAY", font=get_font(75), base_color="Black", hovering_color="Red"),
            Button(image=pygame.image.load("assets/Options Rect.png"), pos=(400, 200), 
                        text_input="OPTIONS", font=get_font(75), base_color="Black", hovering_color="Red"),
            Button(image=pygame.image.load("assets/Quit Rect.png"), pos=(400, 350), 
                        text_input="QUIT", font=get_font(75), base_color="Black", hovering_color="Red")
        )

        # PLAY_BUTTON = Button(image=pygame.image.load("assets/Play Rect.png"), pos=(640, 250), 
        #                     text_input="PLAY", font=self.main_menu_font(75), base_color="#d7fcd4", hovering_color="White")
        # OPTIONS_BUTTON = Button(image=pygame.image.load("assets/Options Rect.png"), pos=(640, 400), 
        #                     text_input="OPTIONS", font=self.main_menu_font(75), base_color="#d7fcd4", hovering_color="White")
        # QUIT_BUTTON = Button(image=pygame.image.load("assets/Quit Rect.png"), pos=(640, 550), 
        #                     text_input="QUIT", font=self.main_menu_font(75), base_color="#d7fcd4", hovering_color="White")

        self.game_scene = Scene()
        self.current_game_state = 'main'
    
    def handle_keyboard_events_main_menu(self):
        menu_mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            # mouse clicked events
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.main_menu_buttons[0].checkForInput(menu_mouse_pos):
                    self.play()
                    self.current_game_state = 'play'
                if self.main_menu_buttons[1].checkForInput(menu_mouse_pos):
                    self.options()
                    self.current_game_state = 'options'
                if self.main_menu_buttons[2].checkForInput(menu_mouse_pos):
                    pygame.quit()
                    sys.exit()

            # press key events
            if event.type == pygame.KEYDOWN:
                ...

            # release key events
            if event.type == pygame.KEYUP:
                ...
            
        return
    
    def main_menu(self):
        pygame.mixer.music.load("assets/ambientmain_0.ogg")
        pygame.mixer.music.set_volume(0.1)
        pygame.mixer.music.play(-1)
        menu_is_active = True
        while menu_is_active:
            self.clock.tick(60)
            mouse_pos = pygame.mouse.get_pos()

            # if in main menu draw main menu buttons
            #
            # self.screen.fill("black")
            self.screen.blit(self.main_menu_bg, (0, 0), area=None, special_flags=0)

            for button in self.main_menu_buttons:
                button.changeColor(mouse_pos)
                button.update(self.screen)

            # handle main menu buttons events
            # self.handle_keyboard_events_main_menu()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                # mouse clicked events
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.main_menu_buttons[0].checkForInput(mouse_pos):
                        # self.current_game_state = 'play'
                        # menu_is_active = not menu_is_active
                        self.play()
                    if self.main_menu_buttons[1].checkForInput(mouse_pos):
                        # self.current_game_state = 'options'
                        # menu_is_active = not menu_is_active
                        self.options()
                    if self.main_menu_buttons[2].checkForInput(mouse_pos):
                        pygame.quit()
                        sys.exit()

            pygame.display.update()
        
        # activate game state chosen by player
        # print(f'main menu loop terminated, new game state is:{self.current_game_state}')
        # if self.current_game_state == 'play':
        #     self.play()
        # elif self.current_game_state == 'options':
        #     self.options()

    def options(self):
        return

    def handle_keyboard_events_play(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.KEYDOWN or event.type == pygame.KEYUP:
                keys_pressed = pygame.key.get_pressed()
                # keys_movement = (pygame.K_d, pygame.K_a, pygame.K_s, pygame.K_w)
                # vs = (np.array([1, 0]), np.array([-1, 0]), np.array([0, -1]), np.array([0, 1]))
                # keys_bitmask = tuple(map(lambda key: keys_pressed[key], keys_movement))
                # current_move_vectors = [vec if is_pressed else np.array([0, 0]) for is_pressed, vec in zip(keys_bitmask, vs)]
                # # print(current_move_vectors, keys_bitmask, keys_pressed)
                # new_velocity_vector = sum(current_move_vectors)
                # self.current_velocity = new_velocity_vector
                self.game_scene.player.update_velocity_vector(keys_pressed)
                # self.game_scene.player.normalize_velocity_vector()

    def play(self):
        debug_mode = True
        pygame.mixer.music.stop()
        pygame.mouse.set_cursor((8,8),(0,0),(0,0,0,0,0,0,0,0),(0,0,0,0,0,0,0,0)) # invisible cursor

        viewport = np.array([WINDOW_WIDTH, WINDOW_HEIGHT])
        fps = 120
        game_over = False
        while not game_over:       
            self.clock.tick(fps)  
            self.screen.fill("black")
            # update states
            m_xpos, m_ypos = pygame.mouse.get_pos()
            self.handle_keyboard_events_play()
            self.game_scene.player.update_state(1/fps, m_xpos, m_ypos)

            if pygame.mouse.get_pressed()[0]: # Left click
                self.game_scene.player.shoot()

            pg_player_pos = map_opengl_to_pg_coordinates_2d(
                self.game_scene.player.current_position,
                viewport
            )
            pg_player_dir_vector_endpoint = map_opengl_to_pg_coordinates_2d(
                self.game_scene.player.current_position + self.game_scene.player.current_weapon_direction,
                viewport
            )
            gl_weapon_dir_endpoint = self.game_scene.player.current_weapon_direction * 0.5 + \
                self.game_scene.player.current_position

            # Draw a circle
            pygame.draw.circle(self.screen, "white", pg_player_pos, 11)
            pygame.draw.line(self.screen, "red", pg_player_pos, pg_player_dir_vector_endpoint)
            render_cursor(self.screen, np.array([m_xpos, m_ypos]), size=16)

            for bullet in self.game_scene.player.bullets_alive:
                render_bullet(self.screen, bullet)

            if debug_mode:
                pg_direction_text = get_font(size=8).render(f'pg_weapon_direction: {pg_player_dir_vector_endpoint}', True, "white")
                gl_direction_text = get_font(size=8).render(f'gl_weapon_dir_endpoint: {gl_weapon_dir_endpoint}', True, "white")
                velocity_text = get_font(size=8).render(f'player_velocity: {self.game_scene.player.current_velocity}', True, "white")
                player_pos_text = get_font(size=8).render(f'player_pos:{pg_player_pos}', True, "white")
                self.screen.blit(pg_direction_text, (10, 10))
                self.screen.blit(gl_direction_text, (10, 20))
                self.screen.blit(velocity_text, (10, 30))
                self.screen.blit(player_pos_text, (10, 40))

            # render scene

            pygame.display.update()
    
    def pause_menu(self):
        ...

    def window_game_main_loop(self):
        
        self.main_menu()


