import pygame

from states.game_state import GameState
from ui.pause_menu import ACTION_BUTTONS, draw_pause_menu


class PauseMenuState(GameState):
    """关内暂停：操作、键位说明与音量三个页签。"""

    TAB_ORDER = ("actions", "controls", "audio")

    def __init__(self, game, play_state):
        super().__init__(game)
        self.play_state = play_state
        self.active_tab = "actions"
        self.selected_index = 0
        # 记录最近一次真正悬停到的按钮，鼠标滑入按钮缝隙时保持光标不回跳。
        self.hovered_index = None
        self.tab_rects = {}
        self.action_rects = {}
        self.slider_rects = {}
        self.dragging_slider = None
        self.menu_rect = None
        self.draw(self.game.screen)  # 立即绘制以创建可点击矩形

    @property
    def _has_force_victory(self):
        return hasattr(self.play_state, "force_victory")

    def _resume(self):
        self.play_state.paused = False
        self.game.change_state(self.play_state)

    def _activate(self, action):
        if action == "continue":
            self._resume()
        elif action == "restart":
            self._restart()
        elif action == "level_select":
            from states.level_select_state import LevelSelectState

            # 携带当前关卡：在选关界面点「返回」时回到本关，而不是主菜单。
            self.game.change_state(
                LevelSelectState(self.game, return_state=self.play_state)
            )
        elif action == "skip":
            if self._has_force_victory:
                self.play_state.paused = False
                self.play_state.force_victory()
                self.game.change_state(self.play_state)
            else:
                from states.main_menu_state import MainMenuState

                self.game.change_state(MainMenuState(self.game))
        elif action == "streamer":
            self.game.set_streamer_mode(not self.game.streamer_mode)

    def _restart(self):
        if hasattr(self.play_state, "level"):
            self.game.change_state(self.play_state.restart_level())
        elif type(self.play_state).__name__ == "EndlessState":
            from states.endless_state import EndlessState

            self.game.change_state(EndlessState(self.game))

    def _set_slider(self, name, mouse_x):
        rect = self.slider_rects.get(name)
        if not rect or rect.width <= 0:
            return
        ratio = max(0.0, min(1.0, (mouse_x - rect.left) / rect.width))
        audio = self.game.audio_system
        if name == "master":
            audio.set_master_volume(ratio)
        elif name == "music":
            audio.set_music_volume(ratio)
        else:
            audio.set_sfx_volume(ratio)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self._resume()
                elif event.key in (pygame.K_1, pygame.K_KP1):
                    self.active_tab = "actions"
                elif event.key in (pygame.K_2, pygame.K_KP2):
                    self.active_tab = "controls"
                elif event.key in (pygame.K_3, pygame.K_KP3):
                    self.active_tab = "audio"
                elif self.active_tab == "actions":
                    if event.key in (pygame.K_UP, pygame.K_w):
                        self.selected_index = (self.selected_index - 1) % len(
                            ACTION_BUTTONS
                        )
                        self.hovered_index = self.selected_index
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        self.selected_index = (self.selected_index + 1) % len(
                            ACTION_BUTTONS
                        )
                        self.hovered_index = self.selected_index
                    elif event.key in (
                        pygame.K_RETURN,
                        pygame.K_KP_ENTER,
                        pygame.K_SPACE,
                    ):
                        self._activate(ACTION_BUTTONS[self.selected_index][0])
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self._handle_tab_click(event.pos):
                    self.game.audio_system.play_sfx("click")
                    continue
                if self.active_tab == "actions":
                    button = self._button_at(event.pos)
                    if button:
                        self.selected_index = next(
                            index
                            for index, (name, *_rest) in enumerate(ACTION_BUTTONS)
                            if name == button
                        )
                        self.game.audio_system.play_sfx("click")
                        self._activate(button)
                elif self.active_tab == "audio":
                    slider = self._slider_at(event.pos)
                    if slider:
                        self.dragging_slider = slider
                        self._set_slider(slider, event.pos[0])
            elif event.type == pygame.MOUSEMOTION:
                if self.dragging_slider:
                    self._set_slider(self.dragging_slider, event.pos[0])
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.dragging_slider = None

    def _handle_tab_click(self, position):
        for tab, rect in self.tab_rects.items():
            if rect.collidepoint(position):
                self.active_tab = tab
                return True
        return False

    def _button_at(self, position):
        for name, rect in self.action_rects.items():
            if rect.collidepoint(position):
                return name
        return None

    def _slider_at(self, position):
        for name, rect in self.slider_rects.items():
            if rect.collidepoint(position):
                return name
        return None

    def update(self, dt):
        return None

    def draw(self, screen):
        self.play_state.draw(screen)  # 先绘制游戏背景
        skip_label = "直接跳关" if self._has_force_victory else "返回主菜单"
        audio = self.game.audio_system
        result = draw_pause_menu(
            screen,
            self.game.font_cache,
            skip_label=skip_label,
            active_tab=self.active_tab,
            selected_index=self.selected_index,
            volumes={
                "master": audio.get_master_volume(),
                "music": audio.get_music_volume(),
                "sfx": audio.get_sfx_volume(),
            },
            hovered_slider=self.dragging_slider,
            streamer_mode=self.game.streamer_mode,
            hovered_index=self.hovered_index,
        )
        if result["hovered"] is not None:
            self.hovered_index = result["hovered"]
        self.menu_rect = result["menu_rect"]
        self.tab_rects = result["tabs"]
        self.action_rects = result["buttons"]
        self.slider_rects = result["sliders"]
