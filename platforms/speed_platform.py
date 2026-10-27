import pygame
from platforms.base_platform import BasePlatform
from config import COLORS

class SpeedPlatform(BasePlatform):
    def __init__(self, x, y, w, h, speed_boost, direction=1):
        super().__init__(pygame.Rect(x, y, w, h))
        self.speed_boost = speed_boost  # 速度加成
        self.direction = direction  # 方向，1为向右，-1为向左
        self.active = True  # 是否激活

    def update(self, dt, player_rect=None):
        for enemy in self.enemies:
            enemy.update(dt, platform=self)
        for block in self.story_blocks:
            block.update(dt, platform=self, player_rect=player_rect)

    def draw(self, screen, dirty_rects):
        # 绘制加速平台
        rect = pygame.draw.rect(screen, COLORS["ORANGE"], self.rect, border_radius=8)
        # 绘制方向箭头
        arrow_size = 15
        if self.direction == 1:
            # 向右箭头
            pygame.draw.polygon(screen, COLORS["WHITE"], [
                (self.rect.centerx + 20, self.rect.centery),
                (self.rect.centerx + 20 - arrow_size, self.rect.centery - arrow_size // 2),
                (self.rect.centerx + 20 - arrow_size, self.rect.centery + arrow_size // 2)
            ])
        else:
            # 向左箭头
            pygame.draw.polygon(screen, COLORS["WHITE"], [
                (self.rect.centerx - 20, self.rect.centery),
                (self.rect.centerx - 20 + arrow_size, self.rect.centery - arrow_size // 2),
                (self.rect.centerx - 20 + arrow_size, self.rect.centery + arrow_size // 2)
            ])
        dirty_rects.append(rect)
        # 绘制平台上的实体
        for enemy in self.enemies:
            enemy.draw(screen, dirty_rects)
        for block in self.story_blocks:
            block.draw(screen, dirty_rects)
