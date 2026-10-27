"""具有地表移动修正的功能平台（浮冰/沼泽）。"""

from __future__ import annotations

import pygame

from config import COLORS
from platforms.base_platform import BasePlatform
from utils.ui_art import draw_image


class SurfacePlatform(BasePlatform):
    def __init__(self, x, y, w, h, movement_multiplier, color, label, art_path=None,
                 art_offset=(0, 0), art_size=None, jump_multiplier=None):
        super().__init__(pygame.Rect(x, y, w, h))
        self.movement_multiplier = movement_multiplier
        self.jump_multiplier = 1.0 if jump_multiplier is None else jump_multiplier
        self.color = color
        self.label = label
        self.art_path = art_path
        self.art_offset = pygame.Vector2(art_offset)
        self.art_size = art_size

    def update(self, dt, player_rect=None):
        for enemy in self.enemies:
            enemy.update(dt, platform=self)
        for block in self.story_blocks:
            block.update(dt, platform=self, player_rect=player_rect)

    def draw(self, screen, dirty_rects):
        if self.art_path:
            art_rect = pygame.Rect(
                self.rect.x + self.art_offset.x,
                self.rect.y + self.art_offset.y,
                *(self.art_size or self.rect.size),
            )
            dirty_rects.append(draw_image(screen, self.art_path, art_rect, smooth=False))
        else:
            rect = pygame.draw.rect(screen, self.color, self.rect, border_radius=8)
            pygame.draw.rect(screen, COLORS["WHITE"], self.rect, 2, border_radius=8)
            label = pygame.font.Font(None, 18).render(self.label, True, COLORS["WHITE"])
            screen.blit(label, label.get_rect(center=self.rect.center))
            dirty_rects.append(rect)
        for enemy in self.enemies:
            enemy.draw(screen, dirty_rects)
        for block in self.story_blocks:
            block.draw(screen, dirty_rects)


class IcePlatform(SurfacePlatform):
    def __init__(self, x, y, w, h, art_path=None, art_offset=(0, 0), art_size=None,
                 movement_multiplier=1.5, jump_multiplier=None):
        super().__init__(x, y, w, h, movement_multiplier, COLORS["LIGHT_BLUE"], "浮冰 1.5x",
                         art_path, art_offset, art_size, jump_multiplier)


class SwampPlatform(SurfacePlatform):
    def __init__(self, x, y, w, h, art_path=None, art_offset=(0, 0), art_size=None,
                 movement_multiplier=0.75, jump_multiplier=None):
        super().__init__(x, y, w, h, movement_multiplier, COLORS["GREEN"], "沼泽 0.75x",
                         art_path, art_offset, art_size, jump_multiplier)
