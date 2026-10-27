import pygame
from platforms.base_platform import BasePlatform
from config import COLORS

class BouncingPlatform(BasePlatform):
    def __init__(self, x, y, w, h, speed=0, ran=0):
        super().__init__(pygame.Rect(x, y, w, h))
        self.speed = speed
        self.ran = ran
        self.dir = 1
        self.ox = x
        self.bounce_power = 25  # 弹跳力

    def update(self, dt, player_rect=None):
        if self.speed > 0:
            self.rect.x += self.speed * self.dir
            if abs(self.rect.x - self.ox) > self.ran:
                self.dir *= -1
        for enemy in self.enemies:
            enemy.update(dt, platform=self)
        for block in self.story_blocks:
            block.update(dt, platform=self, player_rect=player_rect)

    def draw(self, screen, dirty_rects):
        # 绘制平台主体
        rect = pygame.draw.rect(screen, COLORS["CYAN"], self.rect, border_radius=8)
        # 绘制弹跳标记
        pygame.draw.circle(screen, COLORS["WHITE"], 
                          (self.rect.centerx, self.rect.centery), 10, 2)
        pygame.draw.circle(screen, COLORS["WHITE"], 
                          (self.rect.centerx, self.rect.centery - 15), 8, 2)
        dirty_rects.append(rect)
        for enemy in self.enemies:
            enemy.draw(screen, dirty_rects)
        for block in self.story_blocks:
            block.draw(screen, dirty_rects)
