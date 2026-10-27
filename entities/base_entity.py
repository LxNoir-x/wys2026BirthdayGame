from abc import ABC, abstractmethod

import pygame


class Entity(ABC):
    def __init__(self, x, y, platform):
        self.rect = pygame.Rect(x, y, 30, 30)
        self.offset_x = x - platform.rect.x
        self.offset_y = y - platform.rect.y
        self.visible = True

    @abstractmethod
    def update(self, dt, platform=None):
        pass

    @abstractmethod
    def draw(self, screen, dirty_rects):
        pass