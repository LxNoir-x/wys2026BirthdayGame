"""关卡伤害源的占位实体。"""

from __future__ import annotations

import pygame

from config import COLORS, SCREEN_HEIGHT, SCREEN_WIDTH
from utils.ui_art import draw_image, load_image


class SpikeHazard:
    """沿素材刺尖方向触发并飞向最近实体的一次性伤害源。"""

    def __init__(
        self,
        x: int,
        y: int,
        width: int = 60,
        height: int = 24,
        visible: bool = True,
        *,
        art_path: str | None = None,
        trigger_rect=None,
        speed: float = 420.0,
        direction="right",
        origin_rect=None,
        behavior="moving",
        flip_x=False,
        flip_y=False,
    ):
        self.rect = pygame.Rect(x, y, width, height)
        self.visible = visible
        self.art_path = art_path
        self.trigger_rect = pygame.Rect(trigger_rect) if trigger_rect else None
        self.speed = max(0.0, float(speed))
        if isinstance(direction, str):
            self.direction_name = direction
        else:
            self.direction_name = "right" if direction >= 0 else "left"
        self.direction = {
            "up": pygame.Vector2(0, -1),
            "down": pygame.Vector2(0, 1),
            "left": pygame.Vector2(-1, 0),
            "right": pygame.Vector2(1, 0),
        }[self.direction_name]
        if behavior not in {"moving", "static", "decorative"}:
            raise ValueError(f"Unsupported spike behavior: {behavior}")
        self.behavior = behavior
        self.flip_x = bool(flip_x)
        self.flip_y = bool(flip_y)
        self.active = False
        self.dangerous = behavior == "static"
        self.finished = False
        self.origin = pygame.Rect(origin_rect) if origin_rect else self.rect.copy()
        self.travelled = 0.0
        self.max_travel = 0.0

    def configure_trigger(self, blockers) -> None:
        """把刺尖到正前方最近实体之间的空间设为触发走廊。"""

        if self.behavior != "moving":
            self.trigger_rect = None
            return

        origin = self.origin
        candidates = []
        for blocker in (pygame.Rect(rect) for rect in blockers):
            if self.direction_name in {"up", "down"}:
                if min(origin.right, blocker.right) <= max(origin.left, blocker.left):
                    continue
                if self.direction_name == "down" and blocker.top >= origin.bottom - 1:
                    candidates.append(max(0, blocker.top - origin.bottom))
                elif self.direction_name == "up" and blocker.bottom <= origin.top + 1:
                    candidates.append(max(0, origin.top - blocker.bottom))
            else:
                if min(origin.bottom, blocker.bottom) <= max(origin.top, blocker.top):
                    continue
                if self.direction_name == "right" and blocker.left >= origin.right - 1:
                    candidates.append(max(0, blocker.left - origin.right))
                elif self.direction_name == "left" and blocker.right <= origin.left + 1:
                    candidates.append(max(0, origin.left - blocker.right))

        boundary_distance = {
            "up": origin.top,
            "down": SCREEN_HEIGHT - origin.bottom,
            "left": origin.left,
            "right": SCREEN_WIDTH - origin.right,
        }[self.direction_name]
        self.max_travel = float(min(candidates, default=max(0, boundary_distance)))
        if self.direction_name == "up":
            self.trigger_rect = pygame.Rect(
                origin.left,
                origin.top - self.max_travel,
                origin.width,
                origin.height + self.max_travel,
            )
        elif self.direction_name == "down":
            self.trigger_rect = pygame.Rect(
                origin.left,
                origin.top,
                origin.width,
                origin.height + self.max_travel,
            )
        elif self.direction_name == "left":
            self.trigger_rect = pygame.Rect(
                origin.left - self.max_travel,
                origin.top,
                origin.width + self.max_travel,
                origin.height,
            )
        else:
            self.trigger_rect = pygame.Rect(
                origin.left,
                origin.top,
                origin.width + self.max_travel,
                origin.height,
            )

    def update(self, dt: float, player_rect=None) -> None:
        if self.behavior != "moving":
            return
        if self.finished:
            return
        if not self.active:
            if not player_rect or not self._triggered_by(player_rect):
                return
            self.active = True
            self.dangerous = True
            self.visible = True
        elif self.max_travel > 0 and self.travelled >= self.max_travel:
            self.consume()
            return

        self.travelled = min(self.max_travel, self.travelled + self.speed * dt)
        self.rect.x = self.origin.x + round(self.direction.x * self.travelled)
        self.rect.y = self.origin.y + round(self.direction.y * self.travelled)

    def consume(self) -> None:
        if self.behavior != "moving":
            return
        self.finished = True
        self.active = False
        self.dangerous = self.behavior == "static"
        self.visible = False

    def reset(self) -> None:
        """回到原点，供关卡重开时清理飞行地刺。"""
        self.rect = self.origin.copy()
        self.active = False
        self.dangerous = False
        self.finished = False
        self.visible = True
        self.travelled = 0.0

    def _triggered_by(self, player_rect: pygame.Rect) -> bool:
        return self.trigger_rect is not None and player_rect.colliderect(self.trigger_rect)

    def draw(self, screen: pygame.Surface, dirty_rects: list[pygame.Rect]) -> None:
        if not self.visible:
            return

        if self.art_path:
            if self.flip_x or self.flip_y:
                image = load_image(self.art_path)
                if image.get_size() != self.rect.size:
                    image = pygame.transform.scale(image, self.rect.size)
                image = pygame.transform.flip(image, self.flip_x, self.flip_y)
                screen.blit(image, self.rect)
                dirty_rects.append(self.rect)
            else:
                dirty_rects.append(draw_image(screen, self.art_path, self.rect, smooth=False))
            return

        spike_count = max(1, self.rect.width // 15)
        step = self.rect.width / spike_count
        for index in range(spike_count):
            left = self.rect.x + index * step
            points = [
                (round(left), self.rect.bottom),
                (round(left + step / 2), self.rect.top),
                (round(left + step), self.rect.bottom),
            ]
            pygame.draw.polygon(screen, COLORS["RED"], points)
            pygame.draw.polygon(screen, COLORS["WHITE"], points, 1)
        dirty_rects.append(self.rect)
