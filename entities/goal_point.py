import math

import pygame

from config import COLORS


class GoalPoint:
    def __init__(self, x, y, font_cache, width=70, height=70):
        self.rect = pygame.Rect(x, y, width, height)
        self.visible = True
        self.pulse = 0
        self.font_cache = font_cache

    def update(self, dt):
        if not self.visible:
            return
        self.pulse += dt * 3

    def draw(self, screen, dirty_rects):
        if not self.visible:
            return
        center_x, center_y = self.rect.center
        pulse_size = 1 + 0.08 * math.sin(self.pulse)

        outer_radius = int(35 * pulse_size)
        inner_radius = outer_radius - 8

        for i in range(5):
            alpha = 200 - i * 40
            glow_color = (*COLORS["PURPLE"], alpha)
            pygame.draw.circle(screen, glow_color, (center_x, center_y), outer_radius + i)

        goal_rect = pygame.draw.circle(screen, COLORS["PURPLE"], (center_x, center_y), outer_radius)
        pygame.draw.circle(screen, COLORS["GREEN"], (center_x, center_y), outer_radius, 3)
        pygame.draw.circle(screen, COLORS["LIGHT_BLUE"], (center_x, center_y), inner_radius)

        text = self.font_cache["tiny"].render("终点", True, COLORS["WHITE"])
        text_rect = text.get_rect(center=(center_x, center_y))
        screen.blit(text, text_rect)

        dirty_rects.append(goal_rect.inflate(20, 20))
        dirty_rects.append(text_rect)
