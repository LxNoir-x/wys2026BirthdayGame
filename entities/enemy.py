import math

import pygame

from config import COLORS
from entities.base_entity import Entity


class Enemy(Entity):
    def __init__(self, x, y, platform):
        super().__init__(x, y, platform)
        self.alive = True
        self.pulse_phase = 0
        self.glow_phase = 0

    def update(self, dt, platform=None):
        if not self.alive:
            return
        self.pulse_phase += dt * 4
        self.glow_phase += dt * 2
        if platform:
            self.rect.x = platform.rect.x + self.offset_x
            self.rect.y = platform.rect.y + self.offset_y

    def draw(self, screen, dirty_rects):
        if not self.alive or not self.visible:
            return

        center_x, center_y = self.rect.center
        pulse_size = 1 + 0.1 * math.sin(self.pulse_phase)

        glow_surface = pygame.Surface((60, 60), pygame.SRCALPHA)
        for i in range(25, 0, -5):
            alpha = int(100 * (1 - i / 25) * (0.7 + 0.3 * math.sin(self.glow_phase)))
            glow_color = (255, 100, 100, alpha)
            pygame.draw.circle(glow_surface, glow_color, (30, 30), 15 + i)
        screen.blit(glow_surface, (center_x - 30, center_y - 30))

        size = int(12 * pulse_size)
        points = [
            (center_x, center_y - size),
            (center_x - size, center_y + size),
            (center_x + size, center_y + size)
        ]
        enemy_triangle = pygame.draw.polygon(screen, COLORS["RED"], points)
        pygame.draw.polygon(screen, (255, 200, 200), points, 2)

        dirty_rects.append(enemy_triangle.inflate(40, 40))

    def kill(self):
        self.alive = False