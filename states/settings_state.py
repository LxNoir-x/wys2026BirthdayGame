"""与关内暂停界面共用终端布局的全局设置状态。"""

from __future__ import annotations

import pygame

from states.game_state import GameState
from ui.pause_menu import draw_pause_menu


class SettingsState(GameState):
    """提供操作、按键说明和三轨音量三个页签。"""

    TAB_ORDER = ("actions", "controls", "audio")
    CONTENT_RECT = pygame.Rect(406, 205, 557, 365)

    def __init__(self, game, return_state=None, initial_tab=None):
        super().__init__(game)
        self.return_state = return_state
        aliases = {"operations": "actions", "music": "audio"}
        self.active_tab = aliases.get(initial_tab, initial_tab) or "actions"
        if self.active_tab not in self.TAB_ORDER:
            self.active_tab = "actions"
        self.selected_index = 0
        self.hovered_index = None
        self.confirm_clear = False
        self.tab_rects = {}
        self.action_rects = {}
        self.slider_rects = {}
        self.dragging_slider = None
        self.draw(self.game.screen)

    @property
    def tab(self):
        """兼容旧调用者使用的页签名称。"""

        return self.active_tab

    @property
    def _is_gameplay_menu(self):
        return self.return_state is not None and hasattr(self.return_state, "paused")

    def _action_items(self):
        if self._is_gameplay_menu:
            skip_label = (
                "直接跳关"
                if hasattr(self.return_state, "force_victory")
                else "返回主菜单"
            )
            return (
                ("continue", "继续游戏"),
                ("restart", "重新开始"),
                ("level_select", "关卡选择"),
                ("skip", skip_label),
                (
                    "streamer",
                    "主播模式：开启" if self.game.streamer_mode else "主播模式：关闭",
                ),
            )
        return (
            ("back", "返回主界面"),
            (
                "streamer",
                "主播模式：开启" if self.game.streamer_mode else "主播模式：关闭",
            ),
            (
                "clear",
                "再次点击确认清除" if self.confirm_clear else "清除存档",
            ),
        )

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self._back()
                    return
                if event.key in (pygame.K_1, pygame.K_KP1):
                    self.active_tab = "actions"
                elif event.key in (pygame.K_2, pygame.K_KP2):
                    self.active_tab = "controls"
                elif event.key in (pygame.K_3, pygame.K_KP3):
                    self.active_tab = "audio"
                elif self.active_tab == "actions":
                    item_count = len(self._action_items())
                    if event.key in (pygame.K_UP, pygame.K_w):
                        self.selected_index = (self.selected_index - 1) % item_count
                        self.hovered_index = self.selected_index
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        self.selected_index = (self.selected_index + 1) % item_count
                        self.hovered_index = self.selected_index
                    elif event.key in (
                        pygame.K_RETURN,
                        pygame.K_KP_ENTER,
                        pygame.K_SPACE,
                    ):
                        self._run_action(self._action_items()[self.selected_index][0])
                continue

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self._handle_tab_click(event.pos):
                    self.game.audio_system.play_sfx("click")
                    continue
                if self.active_tab == "actions":
                    action = self._action_at(event.pos)
                    if action:
                        self.game.audio_system.play_sfx("click")
                        self._run_action(action)
                elif self.active_tab == "audio":
                    slider = self._slider_at(event.pos)
                    if slider:
                        self.dragging_slider = slider
                        self._set_slider(slider, event.pos[0])
            elif event.type == pygame.MOUSEMOTION and self.dragging_slider:
                self._set_slider(self.dragging_slider, event.pos[0])
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.dragging_slider = None

    def _handle_tab_click(self, position):
        for tab, rect in self.tab_rects.items():
            if rect.collidepoint(position):
                self.active_tab = tab
                return True
        return False

    def _action_at(self, position):
        return next(
            (
                name
                for name, rect in self.action_rects.items()
                if rect.collidepoint(position)
            ),
            None,
        )

    def _slider_at(self, position):
        return next(
            (
                name
                for name, rect in self.slider_rects.items()
                if rect.collidepoint(position)
            ),
            None,
        )

    def _set_slider(self, name, mouse_x):
        rect = self.slider_rects.get(name)
        if not rect or rect.width <= 0:
            return
        ratio = max(0.0, min(1.0, (mouse_x - rect.left) / rect.width))
        audio = self.game.audio_system
        setters = {
            "master": audio.set_master_volume,
            "music": audio.set_music_volume,
            "sfx": audio.set_sfx_volume,
        }
        setters[name](ratio)

    def update(self, dt):
        return None

    def draw(self, screen):
        audio = self.game.audio_system
        action_items = self._action_items()
        self.selected_index %= len(action_items)
        result = draw_pause_menu(
            screen,
            self.game.font_cache,
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
            action_items=action_items,
        )
        if result["hovered"] is not None:
            self.hovered_index = result["hovered"]
        self.tab_rects = result["tabs"]
        self.action_rects = result["buttons"]
        self.slider_rects = result["sliders"]

    def _run_action(self, action):
        if action in {"continue", "back"}:
            self._back()
        elif action == "restart":
            self._restart()
        elif action == "level_select":
            from states.level_select_state import LevelSelectState

            # 与暂停菜单一致：从关卡内进入时，选关界面的「返回」回到本关。
            self.game.change_state(
                LevelSelectState(self.game, return_state=self.return_state)
            )
        elif action == "skip":
            if hasattr(self.return_state, "force_victory"):
                self.return_state.force_victory()
                self._back()
            else:
                from states.main_menu_state import MainMenuState

                self.game.change_state(MainMenuState(self.game))
        elif action == "streamer":
            self.game.audio_system.play_sfx("toggle")
            self.game.set_streamer_mode(not self.game.streamer_mode)
        elif action == "clear":
            if self.confirm_clear:
                self.game.clear_all_progress()
                self.confirm_clear = False
                self.game.ui_manager.show_toast("存档已清除", "已恢复默认设置。")
                # 清档后回到未解锁的默认主界面，而不是停在已解锁的旧主菜单上。
                from states.main_menu_state import MainMenuState

                self.game.change_state(MainMenuState(self.game))
            else:
                self.confirm_clear = True
                self.game.ui_manager.show_toast(
                    "确认清除存档",
                    "再次点击“清除存档”以确认。",
                )

    def _restart(self):
        state = self.return_state
        if hasattr(state, "restart_level"):
            self.game.change_state(state.restart_level())
            return
        state_name = type(state).__name__
        if state_name == "SLevelState":
            from states.s_level_state import SLevelState

            self.game.change_state(SLevelState(self.game))
        elif state_name == "ExMazeState":
            from states.ex_maze_state import ExMazeState

            self.game.change_state(ExMazeState(self.game))
        else:
            from states.endless_state import EndlessState

            self.game.change_state(EndlessState(self.game))

    def _back(self):
        if self.return_state is not None:
            if hasattr(self.return_state, "paused"):
                self.return_state.paused = False
            if hasattr(self.return_state, "escape_menu_open"):
                self.return_state.escape_menu_open = False
            self.game.change_state(self.return_state)
            return
        from states.main_menu_state import MainMenuState

        self.game.change_state(MainMenuState(self.game))
