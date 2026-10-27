import pygame
from platforms.base_platform import BasePlatform
from config import COLORS
from utils.ui_art import draw_image

class StaticPlatform(BasePlatform):
    def __init__(self, rect, art_path=None, visible=True, art_size=None, art_offset=(0, 0)):
        super().__init__(rect)
        self.art_path = art_path
        self.visible = visible
        self.art_size = art_size
        self.art_offset = pygame.Vector2(art_offset)

    def update(self, dt=0, player_rect=None):
        for enemy in self.enemies:
            enemy.update(dt, platform=self)
        for block in self.story_blocks:
            block.update(dt, platform=self, player_rect=player_rect)

    def draw(self, screen, dirty_rects):
        if not self.visible:
            return
        if self.art_path:
            if self.art_size:
                art_rect = pygame.Rect(
                    self.rect.x + self.art_offset.x,
                    self.rect.y + self.art_offset.y,
                    *self.art_size,
                )
            else:
                art_rect = self.rect
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
