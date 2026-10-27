import pygame
from abc import ABC, abstractmethod

class BasePlatform(ABC):
    def __init__(self, rect):
        self.rect = rect
        self.enemies = []
        self.story_blocks = []
        self.has_collectible = False

    def set_entities_visibility(self, visible):
        for enemy in self.enemies:
            enemy.visible = visible
        for block in self.story_blocks:
            block.visible = visible

    @abstractmethod
    def update(self, dt, player_rect=None):
        pass

    def get_rect(self):
        return self.rect

    @abstractmethod
    def draw(self, screen, dirty_rects):
        pass