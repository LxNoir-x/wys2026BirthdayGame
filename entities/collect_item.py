import math

import pygame

from config import COLORS
from utils.draw_utils import draw_star
from utils.ui_art import draw_gif_frame, draw_image


class CollectItem:
    def __init__(self, x, y, item_id=None, art_path=None, visible=True):
        self.rect = pygame.Rect(x, y, 40, 40)
        self.item_id = item_id
        self.art_path = art_path
        self.visible = visible
        self.collected = False
        self.rotation = 0
        self.pulse = 0

    def update(self, dt):
        self.rotation += dt * 2
        self.pulse += dt * 4

    def draw(self, screen, dirty_rects):
        if self.collected or not self.visible:
            return

        center_x, center_y = self.rect.center
        pulse_size = 1 + 0.1 * math.sin(self.pulse)

        if self.art_path:
            if self.art_path.lower().endswith(".gif"):
                art_rect = pygame.Rect(0, 0, 60, 60)
                art_rect.center = self.rect.center
                draw_gif_frame(screen, self.art_path, art_rect, smooth=False)
                dirty_rects.append(art_rect)
            else:
                draw_image(screen, self.art_path, self.rect, smooth=True)
                dirty_rects.append(self.rect)
            return

        glow_surface = pygame.Surface((80, 80), pygame.SRCALPHA)
        for i in range(30, 0, -5):
            alpha = int(150 * (1 - i / 30))
            glow_color = (*COLORS["GOLD"], alpha)
            pygame.draw.circle(glow_surface, glow_color, (40, 40), i + 10)
        screen.blit(glow_surface, (center_x - 40, center_y - 40))

        draw_star(screen, center_x, center_y, 18 * pulse_size, COLORS["GOLD"])
        draw_star(screen, center_x, center_y, 12 * pulse_size, COLORS["WHITE"])

        dirty_rects.append(self.rect.inflate(60, 60))
