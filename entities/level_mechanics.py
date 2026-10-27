"""钥匙、门、拉杆和栅栏门的通用关卡机制。"""

from __future__ import annotations

import math
from typing import ClassVar

import pygame

from config import COLORS
from utils.ui_art import draw_image, load_image


class KeyItem:
    def __init__(self, key_id, x, y, width=28, height=28, art_path=None):
        self.key_id = key_id
        self.rect = pygame.Rect(x, y, width, height)
        self.art_path = art_path
        self.collected = False
        self.visible = True

    def draw(self, screen, dirty_rects):
        if self.collected or not self.visible:
            return
        if self.art_path:
            draw_image(screen, self.art_path, self.rect, smooth=False)
            dirty_rects.append(self.rect)
            return
        pygame.draw.circle(screen, COLORS["GOLD"], self.rect.center, 9, 3)
        pygame.draw.line(
            screen,
            COLORS["GOLD"],
            (self.rect.centerx + 7, self.rect.centery),
            (self.rect.right, self.rect.centery),
            4,
        )
        dirty_rects.append(self.rect)


class Door:
    def __init__(
        self,
        door_id,
        key_id,
        x,
        y,
        width=36,
        height=80,
        visible=True,
        art_path=None,
        open_art_path=None,
    ):
        self.door_id = door_id
        self.key_id = key_id
        self.rect = pygame.Rect(x, y, width, height)
        self.unlocked = False
        self.visible = visible
        self.art_path = art_path
        self.open_art_path = open_art_path

    def draw(self, screen, dirty_rects):
        if not self.visible:
            return
        try:
            # 先绘制门芯（未激活黑色门或激活蓝色传送门），再让门框盖在最上层。
            door_rect = pygame.Rect(0, 0, 0, 0)
            door_rect.width = max(1, round(self.rect.width * 75 / 89))
            door_rect.height = max(1, round(self.rect.height * 93 / 99))
            door_rect.midbottom = self.rect.midbottom
            draw_image(
                screen,
                "images/gameplay/door_open.png"
                if self.unlocked
                else "images/gameplay/door_closed.png",
                door_rect,
                smooth=False,
            )
            draw_image(
                screen,
                "images/gameplay/door_frame.png",
                self.rect,
                smooth=False,
            )
            dirty_rects.append(self.rect.copy())
            return
        except (FileNotFoundError, pygame.error):
            pass
        if self.art_path:
            dirty_rects.append(draw_image(screen, self.art_path, self.rect, smooth=False))
            return
        color = COLORS["RED"]
        pygame.draw.rect(screen, color, self.rect, border_radius=4)
        pygame.draw.rect(screen, COLORS["WHITE"], self.rect, 2, border_radius=4)
        label = "门"
        text = pygame.font.Font(None, 18).render(label, True, COLORS["WHITE"])
        screen.blit(text, text.get_rect(center=self.rect.center))
        dirty_rects.append(self.rect)


class Lever:
    """由底座与杆身两件素材组装的拉杆。

    底座紧贴安装面且激活前后绝对静止；杆身绕底座半圆圆心旋转，未激活时
    垂直于安装面（0°），按 E 激活后向侧边倾斜 45°，杆底始终锁定在圆心。
    """

    BASE_ART = "images/gameplay/lever_base.png"
    POLE_ART = "images/gameplay/lever_pole.png"
    BASE_SIZE = (67.0, 36.0)
    POLE_SIZE = (8.0, 55.0)
    # 半圆圆心（底座本地坐标）与杆底锚点（杆身本地坐标）。
    BASE_PIVOT = (33.0, 33.0)
    POLE_PIVOT = (4.0, 53.0)
    # 圆心到平直底面的距离，杆身沿法向前移同样距离以贴合底面。
    PIVOT_DEPTH = 3.0
    MOUNT_ANGLES: ClassVar[dict[str, float]] = {
        "floor": 0.0,
        "ceiling": 180.0,
        "wall_left": -90.0,
        "wall_right": 90.0,
    }
    # 布局矩形安装边到平直底面的留白（源素材像素），用于抵消 PSD 图层的出入墙余量。
    MOUNT_MARGINS: ClassVar[dict[str, float]] = {
        "floor": 15.0,
        "ceiling": 15.0,
        "wall_left": 16.0,
        "wall_right": 16.0,
    }
    TILT_ANGLE = 45.0

    _scaled_cache: ClassVar[dict[tuple[str, int, int], pygame.Surface]] = {}

    def __init__(
        self,
        lever_id,
        gate_id,
        x,
        y,
        width=28,
        height=42,
        mount_direction="floor",
    ):
        self.lever_id = lever_id
        self.gate_id = gate_id
        self.rect = pygame.Rect(x, y, width, height)
        self.mount_direction = (
            mount_direction if mount_direction in self.MOUNT_ANGLES else "floor"
        )
        self.activated = False
        self.visible = True

    def _scale(self):
        """返回源素材到运行时布局的比例（底座的 67px 长边对齐布局长边）。"""

        long_side = (
            self.rect.height
            if self.mount_direction in ("wall_left", "wall_right")
            else self.rect.width
        )
        return max(0.05, long_side / self.BASE_SIZE[0])

    @classmethod
    def _scaled(cls, art_path, size):
        key = (art_path, size[0], size[1])
        surface = cls._scaled_cache.get(key)
        if surface is None:
            surface = pygame.transform.scale(load_image(art_path), size)
            cls._scaled_cache[key] = surface
        return surface

    def _surface_point(self, scale):
        """返回安装面上的底座贴合点及其指向杆身的法向。"""

        rect = self.rect
        margin = self.MOUNT_MARGINS[self.mount_direction] * scale
        if self.mount_direction == "floor":
            return (rect.centerx, rect.bottom - margin), (0.0, -1.0)
        if self.mount_direction == "ceiling":
            return (rect.centerx, rect.top + margin), (0.0, 1.0)
        if self.mount_direction == "wall_left":
            return (rect.left + margin, rect.centery), (1.0, 0.0)
        return (rect.right - margin, rect.centery), (-1.0, 0.0)

    @staticmethod
    def _blit_pivot(screen, image, angle, pivot_local, target):
        """绕本地轴点旋转图像，并把轴点对齐到目标世界坐标。"""

        rotated = pygame.transform.rotate(image, angle)
        width, height = image.get_size()
        vx = pivot_local[0] - width / 2.0
        vy = pivot_local[1] - height / 2.0
        radians = math.radians(angle)
        cos = math.cos(radians)
        sin = math.sin(radians)
        pivot_x = vx * cos + vy * sin
        pivot_y = -vx * sin + vy * cos
        rotated_width, rotated_height = rotated.get_size()
        pivot_x += rotated_width / 2.0
        pivot_y += rotated_height / 2.0
        position = (
            round(target[0] - pivot_x),
            round(target[1] - pivot_y),
        )
        screen.blit(rotated, position)
        return pygame.Rect(position, rotated.get_size())

    def draw(self, screen, dirty_rects):
        if not self.visible:
            return
        scale = self._scale()
        base = self._scaled(
            self.BASE_ART,
            (
                max(1, round(self.BASE_SIZE[0] * scale)),
                max(1, round(self.BASE_SIZE[1] * scale)),
            ),
        )
        pole = self._scaled(
            self.POLE_ART,
            (
                max(1, round(self.POLE_SIZE[0] * scale)),
                max(1, round(self.POLE_SIZE[1] * scale)),
            ),
        )

        angle = self.MOUNT_ANGLES[self.mount_direction]
        surface, normal = self._surface_point(scale)
        center = (
            surface[0] + normal[0] * self.PIVOT_DEPTH * scale,
            surface[1] + normal[1] * self.PIVOT_DEPTH * scale,
        )

        drawn = self._blit_pivot(
            screen,
            base,
            angle,
            (self.BASE_PIVOT[0] * scale, self.BASE_PIVOT[1] * scale),
            center,
        )
        pole_angle = angle - (self.TILT_ANGLE if self.activated else 0.0)
        drawn.union_ip(
            self._blit_pivot(
                screen,
                pole,
                pole_angle,
                (self.POLE_PIVOT[0] * scale, self.POLE_PIVOT[1] * scale),
                center,
            )
        )
        dirty_rects.append(drawn)


class FenceGate:
    def __init__(self, gate_id, x, y, width=40, height=100, art_path=None):
        self.gate_id = gate_id
        self.rect = pygame.Rect(x, y, width, height)
        self.open = False
        self.visible = True
        self.art_path = art_path

    def draw(self, screen, dirty_rects):
        if self.open:
            return
        if self.art_path:
            dirty_rects.append(
                draw_image(screen, self.art_path, self.rect, smooth=False)
            )
            return
        for x in range(self.rect.left + 5, self.rect.right, 10):
            pygame.draw.line(
                screen, COLORS["GRAY"], (x, self.rect.top), (x, self.rect.bottom), 3
            )
        pygame.draw.rect(screen, COLORS["RED"], self.rect, 2)
        dirty_rects.append(self.rect)


class LevelMechanics:
    LEVER_INTERACTION_MARGIN = 72

    def __init__(
        self, key_configs=None, door_configs=None, lever_configs=None, gate_configs=None
    ):
        self.keys = [
            KeyItem(
                item["id"],
                item["x"],
                item["y"],
                item.get("w", 28),
                item.get("h", 28),
                item.get("art_path"),
            )
            for item in (key_configs or [])
        ]
        for key, item in zip(self.keys, key_configs or []):
            key.visible = item.get("visible", True)
        self.doors = [
            Door(
                item["id"],
                item["key_id"],
                item["x"],
                item["y"],
                item.get("w", 36),
                item.get("h", 80),
                item.get("visible", True),
                item.get("art_path"),
                item.get("open_art_path"),
            )
            for item in (door_configs or [])
        ]
        self.levers = [
            Lever(
                item["id"],
                item["gate_id"],
                item["x"],
                item["y"],
                item.get("w", 28),
                item.get("h", 42),
                item.get("mount_direction", "floor"),
            )
            for item in (lever_configs or [])
        ]
        self.gates = [
            FenceGate(
                item["id"],
                item["x"],
                item["y"],
                item.get("w", 40),
                item.get("h", 100),
                item.get("art_path"),
            )
            for item in (gate_configs or [])
        ]

    def update(self, player_rect, interact=False):
        for key in self.keys:
            if not key.collected and player_rect.inflate(48, 48).colliderect(key.rect):
                key.collected = True

        collected_keys = {key.key_id for key in self.keys if key.collected}
        for door in self.doors:
            door.unlocked = door.key_id in collected_keys

        if interact:
            interaction_rect = player_rect.inflate(
                self.LEVER_INTERACTION_MARGIN,
                self.LEVER_INTERACTION_MARGIN,
            )
            nearby = [
                lever
                for lever in self.levers
                if not lever.activated and interaction_rect.colliderect(lever.rect)
            ]
            if nearby:
                min(
                    nearby,
                    key=lambda lever: (
                        (lever.rect.centerx - player_rect.centerx) ** 2
                        + (lever.rect.centery - player_rect.centery) ** 2
                    ),
                ).activated = True

        activated_gates = {lever.gate_id for lever in self.levers if lever.activated}
        for gate in self.gates:
            gate.open = gate.gate_id in activated_gates
        # 没有配置拉杆/栅栏的关卡（如霍里）出口应保持开放，只受钥匙门控制。
        if not self.levers and self.gates:
            for gate in self.gates:
                gate.open = True

    @property
    def goal_unlocked(self):
        # 拉杆和栅栏只负责沿途通行；拿到对应钥匙后，触碰终点门即可完成关卡。
        return all(door.unlocked for door in self.doors)

    def get_blockers(self):
        return [door.rect for door in self.doors if not door.unlocked] + [
            gate.rect for gate in self.gates if not gate.open
        ]

    def draw_gates(self, screen, dirty_rects):
        for gate in self.gates:
            gate.draw(screen, dirty_rects)

    def draw_foreground(self, screen, dirty_rects):
        for key in self.keys:
            key.draw(screen, dirty_rects)
        for door in self.doors:
            door.draw(screen, dirty_rects)
        for lever in self.levers:
            lever.draw(screen, dirty_rects)

    def draw(self, screen, dirty_rects):
        self.draw_foreground(screen, dirty_rects)
        self.draw_gates(screen, dirty_rects)
