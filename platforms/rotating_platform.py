import pygame
import math
from platforms.base_platform import BasePlatform
from config import COLORS

class RotatingPlatform(BasePlatform):
    def __init__(self, center_x, center_y, radius, angle_speed, width=150, height=20):
        # 初始位置设置为中心点下方
        start_x = center_x - width // 2
        start_y = center_y + radius - height // 2
        super().__init__(pygame.Rect(start_x, start_y, width, height))
        self.center_x = center_x
        self.center_y = center_y
        self.radius = radius
        self.angle = 0  # 初始角度
        self.angle_speed = angle_speed  # 角速度（弧度/秒）
        self.width = width
        self.height = height

    def update(self, dt, player_rect=None):
        # 更新角度
        self.angle += self.angle_speed * dt
        if self.angle >= 2 * math.pi:
            self.angle -= 2 * math.pi

        # 计算新位置
        x = self.center_x - self.width // 2 + self.radius * math.cos(self.angle)
        y = self.center_y - self.height // 2 + self.radius * math.sin(self.angle)
        self.rect.x = x
        self.rect.y = y

        # 更新平台上的实体位置
        for enemy in self.enemies:
            enemy.update(dt, platform=self)
        for block in self.story_blocks:
            block.update(dt, platform=self, player_rect=player_rect)

    def draw(self, screen, dirty_rects):
        # 绘制旋转平台
        rect = pygame.draw.rect(screen, COLORS["PURPLE"], self.rect, border_radius=8)
        # 绘制旋转中心标记
        pygame.draw.circle(screen, COLORS["WHITE"], (self.center_x, self.center_y), 5)
        pygame.draw.line(screen, COLORS["WHITE"], (self.center_x, self.center_y), 
                         (self.rect.centerx, self.rect.centery), 2)
        dirty_rects.append(rect)
        # 绘制平台上的实体
        for enemy in self.enemies:
            enemy.draw(screen, dirty_rects)
        for block in self.story_blocks:
            block.draw(screen, dirty_rects)
