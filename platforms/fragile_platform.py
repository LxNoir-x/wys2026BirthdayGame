import random

import pygame

from config import COLORS
from platforms.base_platform import BasePlatform
from utils.ui_art import draw_image


class FragilePlatform(BasePlatform):
    """连续站立 3 秒后消失，5 秒后缓缓恢复。"""

    def __init__(self, x, y, w, h, art_path=None, art_offset=(0, 0), art_size=None):
        super().__init__(pygame.Rect(x, y, w, h))
        self.art_path = art_path
        self.art_offset = pygame.Vector2(art_offset)
        self.art_size = art_size
        self.intact = True
        self.cracked = False
        self.broken = False
        self.standing_time = 0.0
        self.restore_timer = 0.0
        self.break_after = 3.0
        self.restore_after = 5.0
        self.alpha = 255

    def update(self, dt, player_rect=None):
        if self.intact:
            if player_rect and self._player_is_standing(player_rect):
                self.standing_time += dt
                self.cracked = self.standing_time >= 1.5
                if self.standing_time + 1e-6 >= self.break_after:
                    self.intact = False
                    self.broken = True
                    self.restore_timer = 0.0
                    self.set_entities_visibility(False)
            else:
                self.standing_time = 0.0
                self.cracked = False
        else:
            self.restore_timer += dt
            self.alpha = min(255, int(255 * self.restore_timer / self.restore_after))
            if self.restore_timer + 1e-6 >= self.restore_after:
                self.intact = True
                self.broken = False
                self.cracked = False
                self.standing_time = 0.0
                self.alpha = 255
                self.set_entities_visibility(True)

        for enemy in self.enemies:
            enemy.update(dt, platform=self if self.intact else None)
        for block in self.story_blocks:
            block.update(dt, platform=self if self.intact else None, player_rect=player_rect)

    def _player_is_standing(self, player_rect):
        vertical_match = abs(player_rect.bottom - self.rect.top) <= 8
        horizontal_overlap = player_rect.right > self.rect.left and player_rect.left < self.rect.right
        return vertical_match and horizontal_overlap

    def get_rect(self):
        return self.rect if self.intact else pygame.Rect(0, 0, 0, 0)

    def trigger_crack(self):
        if self.intact:
            self.cracked = True

    def draw(self, screen, dirty_rects):
        if self.art_path:
            art_rect = pygame.Rect(
                self.rect.x + self.art_offset.x,
                self.rect.y + self.art_offset.y,
                *(self.art_size or self.rect.size),
            )
            draw_image(screen, self.art_path, art_rect, opacity=self.alpha, smooth=False)
            dirty_rects.append(art_rect)
            return
        if self.intact:
            platform_color = COLORS["DARK_GRAY"] if self.cracked else COLORS["GRAY"]
            rect = pygame.draw.rect(screen, platform_color, self.rect, border_radius=8)
            if self.cracked:
                pygame.draw.line(
                    screen,
                    COLORS["BLACK"],
                    (self.rect.left, self.rect.centery),
                    (self.rect.right, self.rect.centery),
                    2,
                )
                pygame.draw.line(
                    screen,
                    COLORS["BLACK"],
                    (self.rect.centerx, self.rect.top),
                    (self.rect.centerx, self.rect.bottom),
                    2,
                )
            else:
                pygame.draw.circle(screen, COLORS["RED"], self.rect.center, 8, 2)
            dirty_rects.append(rect)
        elif self.alpha > 0:
            surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)
            surface.fill((*COLORS["GRAY"], self.alpha))
            screen.blit(surface, self.rect)
            dirty_rects.append(self.rect)


class EndlessFragilePlatform(FragilePlatform):
    """无尽模式：踩上 1 秒后碎裂，碎裂前抖动提示，且不再恢复。"""

    def __init__(self, x, y, w, h, art_path=None, art_offset=(0, 0), art_size=None):
        super().__init__(x, y, w, h, art_path, art_offset, art_size)
        self.break_after = 1.0
        self.restore_after = 1_000_000.0
        self.shake = 0

    def update(self, dt, player_rect=None):
        super().update(dt, player_rect)
        if self.intact and self.standing_time > 0:
            self.shake = random.choice((-2, -1, 1, 2))
        else:
            self.shake = 0

    def draw(self, screen, dirty_rects):
        original_x = self.rect.x
        self.rect.x += self.shake
        try:
            super().draw(screen, dirty_rects)
        finally:
            self.rect.x = original_x
