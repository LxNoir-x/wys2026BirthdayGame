"""关卡运行时的地图、实体与碰撞调试覆盖层。"""

from __future__ import annotations

from pathlib import Path

import pygame

from levels.level_data import LEVELS
from platforms.moving_platform import MovingPlatform
from utils.ui_art import load_level_map
from utils.ui_theme import get_font

COLORS = {
    "solid": (70, 220, 255),
    "hazard": (255, 76, 95),
    "layout": (213, 128, 255),
    "platform": (70, 235, 155),
    "motion": (255, 195, 72),
    "trigger": (255, 150, 55),
    "mechanic": (255, 225, 90),
    "goal": (116, 255, 240),
    "player": (255, 255, 255),
    "neutral": (160, 170, 185),
}


def draw_debug_overlay(screen: pygame.Surface, state) -> None:
    """绘制状态中所有可识别的地图边界与运行时实体。"""

    overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    font = get_font(state.game.font_cache, "micro")
    mouse = pygame.mouse.get_pos()
    inspected = []

    def screen_rect(rect):
        target = pygame.Rect(rect)
        target.y -= round(getattr(state, "camera_y", 0))
        return target

    def outline(rect, color, width=1):
        target = screen_rect(rect)
        pygame.draw.rect(overlay, (*color, 205), target, width)
        return target

    map_path = None
    if hasattr(state, "level"):
        map_path = LEVELS.get(state.level, {}).get("map")
    if map_path:
        map_data = load_level_map(map_path)
        for element in map_data.get("elements", []):
            raw = element["rect"]
            rect = pygame.Rect(raw["x"], raw["y"], raw["width"], raw["height"])
            collision = (element.get("collision") or {}).get("type")
            color = COLORS.get(collision, COLORS["neutral"])
            target = outline(rect, color)
            if target.collidepoint(mouse):
                inspected.append(
                    "MAP  "
                    f"{element.get('element_type', '?')}  "
                    f"collision={collision or 'none'}  "
                    f"asset={Path(element.get('asset', '-')).name}"
                )
        for layout in map_data.get("layouts", []):
            raw = layout["rect"]
            rect = pygame.Rect(raw["x"], raw["y"], raw["width"], raw["height"])
            target = outline(rect, COLORS["layout"], 2)
            if target.collidepoint(mouse):
                inspected.append(
                    f"LAYOUT  {layout.get('id', '?')}  type={layout.get('element_type', '?')}"
                )

    platforms = getattr(state, "platforms", [])
    for index, platform in enumerate(platforms):
        rect = platform.get_rect()
        target = outline(rect, COLORS["platform"], 2)
        if isinstance(platform, MovingPlatform):
            if platform.motion_min is not None and platform.motion_max is not None:
                start = pygame.Rect(platform.motion_min, rect.size)
                end = pygame.Rect(platform.motion_max, rect.size)
                outline(start.union(end), COLORS["motion"], 2)
            label = f"MOVING[{index}] {platform.axis} speed={platform.speed} dir={platform.dir}"
            _label(overlay, font, label, target.topleft, COLORS["motion"])
        elif getattr(platform, "visible", True):
            _label(
                overlay,
                font,
                f"{type(platform).__name__}[{index}]",
                target.topleft,
                COLORS["platform"],
            )
        if target.collidepoint(mouse):
            inspected.append(
                "ENTITY  "
                f"{type(platform).__name__}[{index}]  rect={tuple(rect)}  "
                f"surface={getattr(platform, 'movement_multiplier', 1.0)}"
            )

    for index, hazard in enumerate(getattr(state, "hazards", [])):
        if hazard.trigger_rect is not None:
            trigger = outline(hazard.trigger_rect, COLORS["trigger"])
            if trigger.collidepoint(mouse):
                inspected.append(
                    f"TRIGGER  spike[{index}] direction={hazard.direction_name} "
                    f"range={round(hazard.max_travel)}"
                )
        target = outline(hazard.rect, COLORS["hazard"], 2)
        start = screen_rect(hazard.origin).center
        end = target.center
        pygame.draw.line(overlay, (*COLORS["hazard"], 230), start, end, 2)
        _label(
            overlay,
            font,
            f"SPIKE[{index}] {hazard.direction_name} {('active' if hazard.active else 'idle')}",
            target.topleft,
            COLORS["hazard"],
        )
        if target.collidepoint(mouse):
            inspected.append(
                f"ENTITY  spike[{index}] active={hazard.active} finished={hazard.finished} "
                f"rect={tuple(hazard.rect)}"
            )

    mechanics = getattr(state, "mechanics", None)
    if mechanics is not None:
        groups = (
            ("KEY", mechanics.keys, "collected"),
            ("DOOR", mechanics.doors, "unlocked"),
            ("LEVER", mechanics.levers, "activated"),
            ("GATE", mechanics.gates, "open"),
        )
        for kind, entities, flag in groups:
            for index, entity in enumerate(entities):
                target = outline(entity.rect, COLORS["mechanic"], 2)
                value = getattr(entity, flag)
                _label(
                    overlay,
                    font,
                    f"{kind}[{index}] {flag}={value}",
                    target.topleft,
                    COLORS["mechanic"],
                )
                if target.collidepoint(mouse):
                    inspected.append(
                        f"ENTITY  {kind}[{index}] {flag}={value} rect={tuple(entity.rect)}"
                    )

    for name, entity, color in (
        ("COLLECTIBLE", getattr(state, "collect_item", None), COLORS["motion"]),
        ("GOAL", getattr(state, "goal_point", None), COLORS["goal"]),
        ("PLAYER", getattr(state, "player", None), COLORS["player"]),
    ):
        if entity is None:
            continue
        target = outline(entity.rect, color, 3)
        _label(overlay, font, f"{name} {tuple(entity.rect)}", target.topleft, color)
        if target.collidepoint(mouse):
            inspected.append(f"ENTITY  {name} rect={tuple(entity.rect)}")

    if hasattr(state, "spawn_point"):
        spawn = pygame.Rect(state.spawn_point, (30, 40))
        target = outline(spawn, COLORS["goal"], 2)
        _label(overlay, font, "SPAWN", target.topleft, COLORS["goal"])

    screen.blit(overlay, (0, 0))
    _draw_inspector(screen, font, state, mouse, inspected)


def _label(surface, font, text, position, color):
    label = font.render(str(text), True, color)
    rect = label.get_rect(topleft=(position[0] + 2, position[1] + 2))
    pygame.draw.rect(surface, (3, 8, 12, 205), rect.inflate(4, 2))
    surface.blit(label, rect)


def _draw_inspector(screen, font, state, mouse, inspected):
    player = getattr(state, "player", None)
    movement = (
        f"跑速={getattr(player, 'run_speed', 0.0):.1f}  "
        f"跳跃高度={round(getattr(player, 'jump_height', 0.0))}px  "
        f"实时速度=({getattr(player, 'vx', 0.0):.2f}, {getattr(player, 'vy', 0.0):.2f})"
    )
    lines = [
        f"DEBUG  F12关闭  Shift+F12工具  mouse={mouse}",
        f"state={type(state).__name__}  objects_under_cursor={len(inspected)}",
        movement,
        "青=地图实体  紫=命名布局  绿=运行碰撞  黄=机关/移动范围  橙=地刺触发",
        *inspected[:9],
    ]
    width = 610
    line_height = font.get_linesize() + 3
    panel = pygame.Surface((width, 16 + len(lines) * line_height), pygame.SRCALPHA)
    panel.fill((3, 8, 12, 225))
    pygame.draw.rect(panel, (*COLORS["solid"], 220), panel.get_rect(), 1)
    for index, line in enumerate(lines):
        color = COLORS["solid"] if index == 0 else (235, 240, 244)
        panel.blit(font.render(line, True, color), (10, 8 + index * line_height))
    screen.blit(panel, (screen.get_width() - width - 12, 12))
