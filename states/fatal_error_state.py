"""SAN 计数达到上限后的蓝屏退出状态。"""

from __future__ import annotations

import sys

import pygame

from config import SCREEN_HEIGHT
from states.game_state import GameState


class FatalErrorState(GameState):
    """先展示蓝屏，再退出程序；进入前已经完成恢复存档。"""

    EXIT_DELAY_SECONDS = 3.0

    def __init__(self, game):
        super().__init__(game)
        self.elapsed = 0.0

    def handle_events(self, events):
        return None

    def update(self, dt):
        self.elapsed += dt
        if self.elapsed >= self.EXIT_DELAY_SECONDS:
            pygame.quit()
            sys.exit(0)

    def draw(self, screen):
        screen.fill((0, 70, 155))
        title = self.game.font_cache["large"].render(":(", True, (255, 255, 255))
        screen.blit(title, (90, 100))

        lines = [
            "你的设备遇到问题，需要重新启动。",
            "检测到致命伤害，保护模式启动。",
            "正在保存当前游玩进度……",
        ]
        for index, line in enumerate(lines):
            text = self.game.font_cache["small"].render(line, True, (255, 255, 255))
            screen.blit(text, (100, 230 + index * 55))

        percent = min(100, int(self.elapsed / self.EXIT_DELAY_SECONDS * 100))
        progress = self.game.font_cache["small"].render(
            f"完成度 {percent}%", True, (255, 255, 255)
        )
        screen.blit(progress, (100, SCREEN_HEIGHT - 110))
