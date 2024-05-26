import sys
import os
import pygame
import pygame.locals as locals
import time
import numpy as np
import copy
import numba
import random

# custom src code
from button import Button
from scene import ( 
    Scene, Bullet, Enemy, Camera, Player,
    map_opengl_to_pg_coordinates_2d, map_pg_to_opengl_coordinates_2d
)
from hud import HeadupDisplay


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


def render_player(screen_ptr: pygame.Surface, player: Player) -> None:
    gl_pos = player.current_position.copy()
    viewport = np.array([WINDOW_WIDTH, WINDOW_HEIGHT])
    pg_pos = map_opengl_to_pg_coordinates_2d(gl_pos, viewport)
    pygame.draw.circle(screen_ptr, "white", pg_pos, player.base_radius)


def render_bullet(screen_ptr: pygame.Surface, bullet: Bullet) -> None:
    gl_pos = bullet.gl_pos.copy()
    viewport = np.array([WINDOW_WIDTH, WINDOW_HEIGHT])
    pg_pos = map_opengl_to_pg_coordinates_2d(gl_pos, viewport)
    pygame.draw.circle(screen_ptr, "white", pg_pos, bullet.pg_radius)


def render_enemy(screen_ptr: pygame.Surface, enemy: Enemy) -> None:
    gl_pos = enemy.gl_pos.copy()
    viewport = np.array([WINDOW_WIDTH, WINDOW_HEIGHT])
    pg_pos = map_opengl_to_pg_coordinates_2d(gl_pos, viewport)
    pygame.draw.circle(screen_ptr, "red", pg_pos, enemy.radius)


def render_scene_camera_offset(screen_ptr: pygame.Surface, scene: Scene) -> None:
    
    # todo later (do not render shit too far away from player)

    # make copies of objects of the scene (to ensure original objects did not modified)
    player_copy = copy.deepcopy(scene.player)
    bullets_alive_copy = copy.deepcopy(player_copy.bullets_alive)
    enemies_alive_copy = copy.deepcopy(scene.enemies_alive)
    camera_copy = copy.deepcopy(scene.camera)
    
    # apply camera to all objects of the scene (player, bullets, enemies)
    player_copy.current_position = camera_copy.apply(player_copy.current_position)
    render_player(screen_ptr, player_copy)

    for bullet in bullets_alive_copy:
        bullet.gl_pos = camera_copy.apply(bullet.gl_pos)
        render_bullet(screen_ptr, bullet)

    for enemy in enemies_alive_copy:
        enemy.gl_pos = camera_copy.apply(enemy.gl_pos)
        render_enemy(screen_ptr, enemy)


def render_scene_no_camera_offset(screen_ptr: pygame.Surface, scene: Scene) -> None:
    
    # todo later (do not render shit too far away from player)

    # make copies of objects of the scene (to ensure original objects did not modified)
    player_copy = copy.deepcopy(scene.player)
    bullets_alive_copy = copy.deepcopy(player_copy.bullets_alive)
    enemies_alive_copy = copy.deepcopy(scene.enemies_alive)
    
    # apply camera to all objects of the scene (player, bullets, enemies)
    render_player(screen_ptr, player_copy)
    for bullet in bullets_alive_copy: render_bullet(screen_ptr, bullet)
    for enemy in enemies_alive_copy: render_enemy(screen_ptr, enemy)


# ======= GAME WINDOW ======================
class Window:

    def __init__(self) -> None:
        pygame.init()
        pygame.mixer.init()
        pygame.mixer.Channel(0).set_volume(0.02)

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
        self.current_track = ''
        self.prev_track = ''
        self.mixer_is_idle = True
        self.play_menu_track_queue = []
        self.track_list_folder = 'assets/music/'
        self.track_list = os.listdir(self.track_list_folder)
        # self.current_game_score = 0
        self.game_is_paused = False
    
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
                        pygame.mixer.music.stop()
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

    def handle_events_play(self):
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

    def play_music(self):
        if not pygame.mixer.Channel(0).get_busy():
            
            if self.prev_track == '':
                next_track_name = random.choice(self.track_list)
            else:
                tracklist_copy = self.track_list.copy()
                tracklist_copy.remove(self.prev_track)
                next_track_name = random.choice(self.track_list.copy())
            
            next_track = pygame.mixer.Sound(
                self.track_list_folder + next_track_name
            )
            self.prev_track = next_track_name
            pygame.mixer.Channel(0).play(next_track, fade_ms=3000)

    def play(self):
        debug_mode = True
        pygame.mouse.set_cursor((8,8),(0,0),(0,0,0,0,0,0,0,0),(0,0,0,0,0,0,0,0)) # invisible cursor
        current_session_hud = HeadupDisplay(player_max_hp=self.game_scene.player.hitpoints)
        viewport = np.array([WINDOW_WIDTH, WINDOW_HEIGHT])
        fps = 120
        game_over = False
        t1 = time.time()
        time.sleep(1 / fps)
        current_game_score = 0
        while not game_over:
            self.play_music()
            self.clock.tick(fps)  
            self.screen.fill("black")
            # update states
            t2 = time.time()
            dt = t2 - t1
            t1 = time.time()
            m_xpos, m_ypos = pygame.mouse.get_pos()
            self.handle_events_play()
            # player
            self.game_scene.player.update_state(dt, m_xpos, m_ypos)

            # enemies
            self.game_scene.add_enemies()
            self.game_scene.process_collisions()
            this_frame_enemies_dead = self.game_scene.remove_dead_enemies()
            current_game_score += this_frame_enemies_dead
            self.game_scene.update_enemies(dt, self.game_scene.player.current_position)

            # hud
            current_session_hud.update_hud(self.game_scene.player.hitpoints)

            # camera
            # self.game_scene.camera.update_velocity_vector(self.game_scene.player.current_position)
            # self.game_scene.camera.update_position(dt)


            if pygame.mouse.get_pressed()[0]: # Left click
                self.game_scene.player.shoot()

            # ========= rendering part
            render_cursor(self.screen, np.array([m_xpos, m_ypos]), size=16)

            # render_scene_no_camera_offset(self.screen, self.game_scene)
            render_scene_no_camera_offset(self.screen, self.game_scene)

            # hud is last to render (nearest to the user)
            current_session_hud.draw_hud_elements(self.screen)
            game_score_text = get_font(size=32).render(f'Score: {current_game_score}', True, 'white')
            player_accuracy = 0 if self.game_scene.player.bullets_shot == 0 else self.game_scene.player.bullets_hit / self.game_scene.player.bullets_shot
            player_accuracy_text = get_font(size=8).render(f'Accuracy% : {player_accuracy * 100}', True, 'white')

            self.screen.blit(game_score_text, (WINDOW_WIDTH // 2 - 100, 10))
            self.screen.blit(player_accuracy_text, (10, 20))

            if debug_mode:
                # pg_direction_text = get_font(size=8).render(f'pg_weapon_direction: {pg_player_dir_vector_endpoint}', True, "white")
                # gl_direction_text = get_font(size=8).render(f'gl_weapon_dir_endpoint: {gl_weapon_dir_endpoint}', True, "white")
                # velocity_text = get_font(size=8).render(f'player_velocity: {self.game_scene.player.current_velocity}', True, "white")
                # player_pos_text = get_font(size=8).render(f'player_pos:{pg_player_pos}', True, "white")
                fps_text = get_font(size=8).render(f'FPS: {int(1 / dt)}', True, 'white')
                # debug_labels = (
                #     pg_direction_text, gl_direction_text, velocity_text, 
                #     player_pos_text, fps_text
                # )
                # for i, label in enumerate(debug_labels):
                #     if label is None:
                #         i -= 1
                #         continue
                #     self.screen.blit(label, (10, 10 * (i + 1)))
                self.screen.blit(fps_text, (10, 10))

            # render scene

            pygame.display.update()
    
    def gameover_menu(self):
        # quit (to main menu button)
        # retry button
        ...

    def pause_menu(self):

        # render scene but no dt = 0 each frame

        # darken all game scene

        # draw pause buttons (resume, options, quit)

        ...

    def window_game_main_loop(self):   
        self.main_menu()


