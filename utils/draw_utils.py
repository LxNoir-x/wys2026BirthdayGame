import math

import pygame

from config import SCREEN_HEIGHT, SCREEN_WIDTH


def draw_gradient_background(screen, top_color, bottom_color):
    for y in range(SCREEN_HEIGHT):
        ratio = y / SCREEN_HEIGHT
        r = int(top_color[0] + (bottom_color[0] - top_color[0]) * ratio)
        g = int(top_color[1] + (bottom_color[1] - top_color[1]) * ratio)
        b = int(top_color[2] + (bottom_color[2] - top_color[2]) * ratio)
        pygame.draw.line(screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))

def draw_star(surface, x, y, size, color, outer_radius=1, inner_radius=0.4):
    points = []
    for i in range(10):
        angle = math.pi / 2 + i * math.pi / 5
        radius = size * (outer_radius if i % 2 == 0 else inner_radius)
        px = x + radius * math.cos(angle)
        py = y + radius * math.sin(angle)
        points.append((px, py))
    pygame.draw.polygon(surface, color, points)