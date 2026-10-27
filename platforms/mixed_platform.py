import pygame
from platforms.base_platform import BasePlatform
from config import COLORS

class MixedPlatform(BasePlatform):
    def __init__(self, x, y, w, h, speed, ran, vt, ht):
        super().__init__(pygame.Rect(x, y, w, h))
        self.speed = speed
        self.ran = ran
        self.dir = 1
        self.ox = x
        self.v = True
        self.t = 0.0
        self.vt = vt
        self.ht = ht
        self.alpha = 255

    def update(self, dt, player_rect=None):
        self.rect.x += self.speed * self.dir
        if abs(self.rect.x - self.ox) > self.ran:
            self.dir *= -1

        self.t += dt
        if self.v and self.t >= self.vt:
            self.v = False
            self.t = 0.0
            self.set_entities_visibility(False)
        elif not self.v and self.t >= self.ht:
            self.v = True
            self.t = 0.0
            self.set_entities_visibility(True)

        if self.v:
            self.alpha = min(255, self.alpha + dt * 500)
        else:
            self.alpha = max(0, self.alpha - dt * 500)

        for enemy in self.enemies:
            enemy.update(dt, platform=self if self.v else None)
        for block in self.story_blocks:
            block.update(dt, platform=self if self.v else None, player_rect=player_rect)

    def get_rect(self):
        return self.rect if self.v else pygame.Rect(0, 0, 0, 0)

    def draw(self, screen, dirty_rects):
        if self.alpha > 0:
            s = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            color = (*COLORS["ORANGE"], self.alpha)
            pygame.draw.rect(s, color, (0, 0, self.rect.width, self.rect.height), border_radius=6)
            highlight_color = (*(255, 200, 150), self.alpha)
            pygame.draw.rect(s, highlight_color, (2, 2, self.rect.width - 4, 4), border_radius=2)
            screen.blit(s, self.rect)
            dirty_rects.append(self.rect)
            for enemy in self.enemies:
                if enemy.visible:
                    enemy.draw(screen, dirty_rects)
            for block in self.story_blocks:
                if block.visible:
                    block.draw(screen, dirty_rects)