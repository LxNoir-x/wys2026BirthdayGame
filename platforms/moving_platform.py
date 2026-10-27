import pygame

from config import COLORS
from platforms.base_platform import BasePlatform
from utils.ui_art import draw_image


class MovingPlatform(BasePlatform):
    def __init__(
        self, x, y, w, h, speed, ran, axis="x", art_path=None, art_offset=(0, 0), art_size=None,
        motion_min=None, motion_max=None, initial_direction=1,
    ):
        super().__init__(pygame.Rect(x, y, w, h))
        self.art_path = art_path
        self.art_offset = pygame.Vector2(art_offset)
        self.art_size = art_size
        self.speed = speed
        self.ran = ran
        self.dir = 1 if initial_direction >= 0 else -1
        self.ox = x
        self.oy = y
        self.axis = axis if axis in {"x", "y"} else "x"
        self.motion_min = pygame.Vector2(motion_min) if motion_min is not None else None
        self.motion_max = pygame.Vector2(motion_max) if motion_max is not None else None
        self.delta_x = 0
        self.delta_y = 0
        self.motion_blockers = []

    def set_motion_blockers(self, blockers) -> None:
        """设置移动过程中不可进入的实心地形。"""

        self.motion_blockers = [pygame.Rect(blocker) for blocker in blockers]

    def _blocked(self, rect: pygame.Rect) -> bool:
        return any(rect.colliderect(blocker) for blocker in self.motion_blockers)

    def update(self, dt, player_rect=None):
        self.delta_x = 0
        self.delta_y = 0
        step = self.speed * self.dir
        if self.axis == "y":
            next_y = self.rect.y + step
            lower_bound = self.motion_min.y if self.motion_min is not None else self.oy
            upper_bound = self.motion_max.y if self.motion_max is not None else self.oy + self.ran
            candidate = self.rect.copy()
            candidate.y = next_y
            if next_y < lower_bound or next_y > upper_bound or self._blocked(candidate):
                self.dir *= -1
                step = self.speed * self.dir
                next_y = self.rect.y + step
            self.rect.y = next_y
            self.delta_y = step
        else:
            next_x = self.rect.x + step
            lower_bound = self.motion_min.x if self.motion_min is not None else self.ox
            upper_bound = self.motion_max.x if self.motion_max is not None else self.ox + self.ran
            candidate = self.rect.copy()
            candidate.x = next_x
            if next_x < lower_bound or next_x > upper_bound or self._blocked(candidate):
                self.dir *= -1
                step = self.speed * self.dir
                next_x = self.rect.x + step
            self.rect.x = next_x
            self.delta_x = step
        for enemy in self.enemies:
            enemy.update(dt, platform=self)
        for block in self.story_blocks:
            block.update(dt, platform=self, player_rect=player_rect)

    def draw(self, screen, dirty_rects):
        if self.art_path:
            art_size = self.art_size or self.rect.size
            art_rect = pygame.Rect(
                self.rect.x + self.art_offset.x,
                self.rect.y + self.art_offset.y,
                *art_size,
            )
            rect = draw_image(screen, self.art_path, art_rect, smooth=False)
            dirty_rects.append(rect)
            for enemy in self.enemies:
                enemy.draw(screen, dirty_rects)
            for block in self.story_blocks:
                block.draw(screen, dirty_rects)
            return
        rect = pygame.draw.rect(screen, COLORS["BROWN"], self.rect, border_radius=8)
        pygame.draw.rect(screen, (200, 160, 120), (self.rect.x + 2, self.rect.y + 2, self.rect.width - 4, 5), border_radius=3)
        dirty_rects.append(rect)
        for enemy in self.enemies:
            enemy.draw(screen, dirty_rects)
        for block in self.story_blocks:
            block.draw(screen, dirty_rects)
