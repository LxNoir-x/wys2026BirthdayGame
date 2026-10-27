"""主线结局展示状态。"""

from __future__ import annotations

import pygame

from states.game_state import GameState
from states.main_menu_state import MainMenuState
from utils.ui_art import scaled_image

ENDING_SLIDES = {
    "HE": ("he", 18),
    "HE_RECOVERY": ("he", 18),
    "BE": ("be", 20),
    "TE": ("te", 7),
}


class EndingState(GameState):
    """按三合一结局演示稿逐页播放当前分支。"""

    def __init__(self, game, ending_type: str):
        super().__init__(game)
        self.ending_type = ending_type if ending_type in ENDING_SLIDES else "HE"
        self.slide_index = 0
        self.slide_prefix, self.slide_count = ENDING_SLIDES[self.ending_type]
        self.previous_slide_index = None
        self.transition_elapsed = 0.0
        self.transition_duration = 0.45
        self.fading_to_menu = False
        self.menu_fade_elapsed = 0.0
        self.menu_fade_duration = 1.6
        self.return_menu = MainMenuState(game)
        if self.ending_type in {"HE", "HE_RECOVERY"}:
            self.music_scene = "ending_he"
        elif self.ending_type == "BE":
            self.music_scene = "be_theme"
        elif self.ending_type == "TE":
            # TE 结局演出不使用 BGM；te_theme 只用于 TE 主界面。
            self.game.audio_system.stop_bgm()

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self._finish()
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_RIGHT):
                    self._advance()
                elif event.key == pygame.K_LEFT and self.slide_count:
                    self.slide_index = max(0, self.slide_index - 1)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._advance()

    def update(self, dt):
        if self.fading_to_menu:
            self.menu_fade_elapsed = min(
                self.menu_fade_duration,
                self.menu_fade_elapsed + dt,
            )
            if self.menu_fade_elapsed >= self.menu_fade_duration:
                self.game.change_state(self.return_menu)
            return
        self.transition_elapsed = min(
            self.transition_duration,
            self.transition_elapsed + dt,
        )

    def draw(self, screen):
        if self.fading_to_menu:
            self.return_menu.draw(screen)
            progress = self.menu_fade_elapsed / self.menu_fade_duration
            self._draw_slide(screen, self.slide_index, round(255 * (1 - progress)))
            return

        if self.previous_slide_index is not None:
            self._draw_slide(screen, self.previous_slide_index)
        else:
            screen.fill((0, 0, 0))
        progress = min(1.0, self.transition_elapsed / self.transition_duration)
        self._draw_slide(screen, self.slide_index, round(255 * progress))

        pulse = 170 + round(55 * abs(pygame.time.get_ticks() % 1000 - 500) / 500)
        arrow = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.polygon(
            arrow,
            (235, 243, 240, pulse),
            ((10, 7), (32, 20), (10, 33)),
        )
        screen.blit(arrow, (1200, 652))

    def _draw_slide(self, screen, index, opacity=255):
        image = scaled_image(
            f"images/ending/{self.slide_prefix}_{index + 1:02d}.png",
            screen.get_size(),
        )
        if opacity >= 255:
            screen.blit(image, (0, 0))
            return
        faded = image.copy()
        faded.set_alpha(max(0, opacity))
        screen.blit(faded, (0, 0))

    def _advance(self):
        if self.fading_to_menu:
            return
        if self.slide_index < self.slide_count - 1:
            self.previous_slide_index = self.slide_index
            self.slide_index += 1
            self.transition_elapsed = 0.0
        else:
            self._finish()

    def _finish(self):
        if self.fading_to_menu:
            return
        self.fading_to_menu = True
        self.menu_fade_elapsed = 0.0
