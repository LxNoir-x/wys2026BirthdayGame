"""
关卡工厂模块
负责根据关卡数据创建关卡内容，包括平台、敌人、收集品和剧情方块
"""

import pygame

from entities.collect_item import CollectItem
from entities.enemy import Enemy
from entities.goal_point import GoalPoint
from entities.hazard import SpikeHazard
from entities.level_mechanics import LevelMechanics
from levels.level_data import LEVEL_COLLECTIBLE_IDS, LEVELS
from platforms.bouncing_platform import BouncingPlatform
from platforms.fragile_platform import FragilePlatform
from platforms.mixed_platform import MixedPlatform
from platforms.moving_platform import MovingPlatform
from platforms.rotating_platform import RotatingPlatform
from platforms.speed_platform import SpeedPlatform
from platforms.static_platform import StaticPlatform
from platforms.surface_platform import IcePlatform, SwampPlatform
from platforms.vanishing_platform import VanishingPlatform
from utils.ui_art import (
    level_map_hazards,
    level_map_layout,
    level_map_layout_rect,
    level_map_solid_rects,
)

# 平台类型到类的映射
platform_classes = {
    "static": StaticPlatform,
    "moving": MovingPlatform,
    "vanishing": VanishingPlatform,
    "mixed": MixedPlatform,
    "bouncing": BouncingPlatform,
    "rotating": RotatingPlatform,
    "fragile": FragilePlatform,
    "speed": SpeedPlatform,
    "ice": IcePlatform,
    "swamp": SwampPlatform,
}


def create_level(level_num, font_cache):
    """
    创建关卡内容

    根据关卡编号从 LEVELS 数据中读取配置，创建平台、敌人、收集品、剧情方块和终点

    Args:
        level_num: 关卡编号（0 为新手教程，1-20 为主线）
        font_cache: 字体缓存字典

    Returns:
        platforms: 平台列表
        collect: 收集品（可能为 None）
        goal: 终点目标点
        hazards: 伤害源列表
        mechanics: 钥匙、门、拉杆和栅栏门机制
    """
    # 获取关卡数据
    data = LEVELS[level_num]
    platforms = []

    # 创建平台。PSD 关卡只在这里把行为配置绑定到导出的场景布局。
    for p_data in _resolve_platform_configs(data, data["platforms"]):
        p_type = p_data["type"]
        cls = platform_classes[p_type]

        # 根据平台类型创建实例
        if p_type == "static":
            rect = pygame.Rect(*p_data["rect"])
            platform = cls(rect, p_data.get("art_path"), p_data.get("visible", True))
        elif p_type == "moving":
            platform = cls(
                p_data["x"],
                p_data["y"],
                p_data["w"],
                p_data["h"],
                p_data["speed"],
                p_data.get("range", 0),
                p_data.get("axis", "x"),
                p_data.get("art_path"),
                p_data.get("art_offset", (0, 0)),
                p_data.get("art_size"),
                p_data.get("motion_min"),
                p_data.get("motion_max"),
                p_data.get("initial_direction", 1),
            )
        elif p_type == "vanishing":
            platform = cls(
                p_data["x"],
                p_data["y"],
                p_data["w"],
                p_data["h"],
                p_data["vt"],
                p_data["ht"],
            )
        elif p_type == "mixed":
            platform = cls(
                p_data["x"],
                p_data["y"],
                p_data["w"],
                p_data["h"],
                p_data["speed"],
                p_data["range"],
                p_data["vt"],
                p_data["ht"],
            )
        elif p_type == "bouncing":
            platform = cls(
                p_data["x"],
                p_data["y"],
                p_data["w"],
                p_data["h"],
                p_data.get("speed", 0),
                p_data.get("range", 0),
            )
        elif p_type == "rotating":
            platform = cls(
                p_data["center_x"],
                p_data["center_y"],
                p_data["radius"],
                p_data["angle_speed"],
                p_data.get("width", 150),
                p_data.get("height", 20),
            )
        elif p_type == "fragile":
            platform = cls(
                p_data["x"],
                p_data["y"],
                p_data["w"],
                p_data["h"],
                p_data.get("art_path"),
                p_data.get("art_offset", (0, 0)),
                p_data.get("art_size"),
            )
        elif p_type == "speed":
            platform = cls(
                p_data["x"],
                p_data["y"],
                p_data["w"],
                p_data["h"],
                p_data["speed_boost"],
                p_data.get("direction", 1),
            )
        elif p_type in {"ice", "swamp"}:
            platform = cls(
                p_data["x"],
                p_data["y"],
                p_data["w"],
                p_data["h"],
                p_data.get("art_path"),
                p_data.get("art_offset", (0, 0)),
                p_data.get("art_size"),
            )

        platforms.append(platform)

    # 地图中的基础地形由导出时的元素语义生成完整实心碰撞体。
    # 它们放在声明的平台之后，以免改变动态平台的配置索引。
    map_solid_rects = (
        level_map_solid_rects(data["map"], data.get("element_offsets"))
        if data.get("map")
        else []
    )
    for exclusion in data.get("solid_exclusions", []):
        exclusion_rect = pygame.Rect(exclusion)
        map_solid_rects = [
            rect
            for rect in map_solid_rects
            if not exclusion_rect.collidepoint(rect.center)
        ]
    for rect in map_solid_rects:
        platforms.append(StaticPlatform(rect, visible=False))
    for platform in platforms:
        if isinstance(platform, MovingPlatform):
            platform.set_motion_blockers(map_solid_rects)

    # 终点位置优先使用 PSD 导出的布局；旧关卡仍可保留坐标配置。
    if goal_layout_id := data.get("goal_layout_id"):
        if not data.get("map"):
            raise ValueError(f"Level {level_num} defines goal_layout_id without a map")
        goal_rect = level_map_layout_rect(data["map"], goal_layout_id)
        goal = GoalPoint(goal_rect.x, goal_rect.y, font_cache, goal_rect.w, goal_rect.h)
    else:
        goal = GoalPoint(*data["goal"], font_cache)
    goal.visible = data.get("goal_visible", not data.get("goal_art_baked", False))

    # 生成固定归属的藏品。位置在正式布局提供前使用稳定的占位规则。
    collectible_id = data.get("collectible_id", LEVEL_COLLECTIBLE_IDS.get(level_num))
    collect = _create_collectible(
        platforms,
        goal,
        collectible_id,
        _resolve_collectible_placement(data, collectible_id),
    )

    # 正式需求暂不把敌人作为伤害源；保留显式配置入口供后续素材接入。
    if data.get("enemies"):
        _create_enemies(platforms, goal, collect, data["enemies"])

    hazards = _create_hazards(_resolve_hazard_configs(data, data.get("hazards", [])))
    if data.get("map"):
        # 地刺视觉和行为都由实体负责，地图绘制时会跳过原始静态刺图层。
        hazards.extend(
            SpikeHazard(
                spec["rect"].x,
                spec["rect"].y,
                spec["rect"].w,
                spec["rect"].h,
                art_path=spec["asset"],
                direction=spec["direction"],
                behavior=spec.get("behavior", "moving"),
                flip_x=spec.get("flip_x", False),
                flip_y=spec.get("flip_y", False),
            )
            for spec in _apply_map_hazard_overrides(
                level_map_hazards(data["map"]),
                data.get("hazard_overrides", []),
            )
        )
    mechanics = LevelMechanics(
        _resolve_layout_configs(data, data.get("keys")),
        _resolve_layout_configs(data, data.get("doors")),
        _resolve_layout_configs(data, data.get("levers")),
        _resolve_layout_configs(data, data.get("gates")),
    )
    hazard_blockers = [platform.rect for platform in platforms]
    hazard_blockers.extend(door.rect for door in mechanics.doors)
    hazard_blockers.extend(gate.rect for gate in mechanics.gates)
    for hazard in hazards:
        hazard.configure_trigger(hazard_blockers)

    return platforms, collect, goal, hazards, mechanics


def _resolve_layout_configs(level_data, configs):
    """Bind behavior-only configs to PSD-derived layout records when requested."""

    resolved = []
    for config in configs or []:
        layout_id = config.get("layout_id")
        if not layout_id:
            resolved.append(config)
            continue
        map_path = level_data.get("map")
        if not map_path:
            raise ValueError(f"Layout-backed entity {layout_id!r} requires a map")
        if any(key in config for key in ("x", "y", "w", "h", "art_path")):
            raise ValueError(
                f"Layout-backed entity {layout_id!r} must not duplicate position or asset fields"
            )
        layout = level_map_layout(map_path, layout_id)
        rect = layout["rect"]
        bound = {
            **config,
            "x": rect["x"] + config.get("position_offset", (0, 0))[0],
            "y": rect["y"] + config.get("position_offset", (0, 0))[1],
            "w": rect["width"],
            "h": rect["height"],
        }
        bound.pop("position_offset", None)
        if asset := layout.get("asset"):
            bound["art_path"] = asset
        bound.setdefault("open_art_path", "images/gameplay/door_open.png")
        resolved.append(bound)
    return resolved


def _resolve_platform_configs(level_data, configs):
    """Bind PSD-backed platform visuals to behavior-only platform settings."""

    resolved = []
    for config in configs or []:
        layout_id = config.get("layout_id")
        if not layout_id:
            resolved.append(config)
            continue
        map_path = level_data.get("map")
        if not map_path:
            raise ValueError(f"Layout-backed platform {layout_id!r} requires a map")
        if any(key in config for key in ("rect", "x", "y", "w", "h", "art_path")):
            raise ValueError(
                f"Layout-backed platform {layout_id!r} must not duplicate position or asset fields"
            )

        layout = level_map_layout(map_path, layout_id)
        rect = level_map_layout_rect(map_path, layout_id)
        asset = layout.get("asset")
        if not asset:
            raise ValueError(
                f"Layout-backed platform {layout_id!r} requires an exported asset"
            )
        bound = {key: value for key, value in config.items() if key != "layout_id"}

        position_offset = pygame.Vector2(config.get("position_offset", (0, 0)))
        visual_rect = rect.move(round(position_offset.x), round(position_offset.y))
        collision_offset = pygame.Vector2(config.get("collision_offset", (0, 0)))
        default_collision_size = visual_rect.size
        if config["type"] in {"fragile", "ice", "swamp"}:
            default_collision_size = (visual_rect.width, min(14, visual_rect.height))
        collision_size = config.get("collision_size", default_collision_size)
        if len(collision_size) != 2:
            raise ValueError(f"Platform {layout_id!r} has an invalid collision_size")
        width, height = (int(value) for value in collision_size)
        if width <= 0 or height <= 0:
            raise ValueError(
                f"Platform {layout_id!r} requires a positive collision_size"
            )

        if config["type"] != "moving":
            bound.update(
                {
                    "x": round(visual_rect.x + collision_offset.x),
                    "y": round(visual_rect.y + collision_offset.y),
                    "w": width,
                    "h": height,
                    "art_path": asset,
                    "art_offset": (
                        -round(collision_offset.x),
                        -round(collision_offset.y),
                    ),
                    "art_size": visual_rect.size,
                }
            )
            resolved.append(bound)
            continue

        bound.update(
            {
                "x": round(visual_rect.x + collision_offset.x),
                "y": round(visual_rect.y + collision_offset.y),
                "w": width,
                "h": height,
                "art_path": asset,
                "art_offset": (-round(collision_offset.x), -round(collision_offset.y)),
                "art_size": visual_rect.size,
            }
        )
        rail_layout_id = config.get("rail_layout_id")
        if rail_layout_id:
            rail = level_map_layout_rect(map_path, rail_layout_id)
            axis = config.get("axis", "x")
            if axis == "x":
                minimum = (rail.left, bound["y"])
                maximum = (rail.right - width, bound["y"])
            elif axis == "y":
                minimum = (bound["x"], rail.top)
                maximum = (bound["x"], rail.bottom - height)
            else:
                raise ValueError(f"Moving platform {layout_id!r} has an invalid axis")
            if minimum[0] > maximum[0] or minimum[1] > maximum[1]:
                raise ValueError(
                    f"Rail {rail_layout_id!r} is smaller than moving platform {layout_id!r}"
                )
            if (
                not pygame.Rect(*minimum, width, height)
                .union(pygame.Rect(*maximum, width, height))
                .collidepoint(bound["x"], bound["y"])
            ):
                raise ValueError(
                    f"Moving platform {layout_id!r} starts outside rail {rail_layout_id!r}"
                )
            bound["motion_min"] = minimum
            bound["motion_max"] = maximum
        resolved.append(bound)
    return resolved


def _resolve_hazard_configs(level_data, configs):
    """Bind dynamic hazards to their PSD layouts while retaining code-owned behavior."""

    resolved = []
    for config in configs or []:
        layout_id = config.get("layout_id")
        if not layout_id:
            resolved.append(config)
            continue
        map_path = level_data.get("map")
        if not map_path:
            raise ValueError(f"Layout-backed hazard {layout_id!r} requires a map")
        if any(
            key in config for key in ("x", "y", "w", "h", "art_path", "trigger_rect")
        ):
            raise ValueError(
                f"Layout-backed hazard {layout_id!r} must not duplicate position or asset fields"
            )
        layout = level_map_layout(map_path, layout_id)
        rect = level_map_layout_rect(map_path, layout_id)
        asset = layout.get("asset")
        if not asset:
            raise ValueError(
                f"Layout-backed hazard {layout_id!r} requires an exported asset"
            )
        bound = {key: value for key, value in config.items() if key != "layout_id"}
        bound.update(
            {"x": rect.x, "y": rect.y, "w": rect.w, "h": rect.h, "art_path": asset}
        )
        bound["origin_rect"] = tuple(bound[k] for k in ("x", "y", "w", "h"))
        if trigger_layout_id := config.get("trigger_layout_id"):
            bound["trigger_rect"] = tuple(
                level_map_layout_rect(map_path, trigger_layout_id)
            )
        resolved.append(bound)
    return resolved


def _apply_map_hazard_overrides(hazards, overrides):
    """按导出矩形为单张地图覆写地刺行为，不改动原始美术。"""

    by_rect = {tuple(override["match"]): override for override in overrides}
    matched = set()
    resolved = []
    for hazard in hazards:
        spec = dict(hazard)
        key = tuple(spec["rect"])
        override = by_rect.get(key)
        if override is None:
            resolved.append(spec)
            continue
        matched.add(key)
        if override.get("remove"):
            continue
        if "rect" in override:
            spec["rect"] = pygame.Rect(override["rect"])
        for field in ("behavior", "direction", "flip_x", "flip_y"):
            if field in override:
                spec[field] = override[field]
        resolved.append(spec)

    missing = set(by_rect) - matched
    if missing:
        raise ValueError(
            f"Hazard overrides do not match exported spikes: {sorted(missing)}"
        )
    return resolved


def _resolve_collectible_placement(level_data, collectible_id):
    """Bind the collectible to its PSD marker layout while keeping optional overrides."""

    layout_id = level_data.get("collectible_layout_id")
    if not layout_id:
        return level_data.get("collectible")
    if not collectible_id:
        raise ValueError(f"Collectible layout {layout_id!r} requires a collectible id")
    if not level_data.get("map"):
        raise ValueError(f"Collectible layout {layout_id!r} requires a map")
    placement = dict(level_data.get("collectible") or {})
    if any(key in placement for key in ("x", "y")):
        raise ValueError(
            f"Collectible layout {layout_id!r} must not duplicate position fields"
        )
    rect = level_map_layout_rect(level_data["map"], layout_id)
    # CollectItem 使用 40x40 的判定框，x/y 为左上角。
    placement["x"] = rect.centerx - 20
    placement["y"] = rect.centery - 20
    return placement


def _create_collectible(platforms, goal, item_id, placement=None):
    """
    创建收集品（内部方法）

    在关卡数据指定的平台上生成收集品；没有正式坐标时使用稳定的占位位置。

    Args:
        platforms: 平台列表
        goal: 终点目标点

    Returns:
        collect: 收集品对象（可能为 None）
    """
    # 计算各平台到终点的距离
    distances = [
        (
            p,
            abs(p.rect.centerx - goal.rect.centerx)
            + abs(p.rect.centery - goal.rect.centery),
        )
        for p in platforms
    ]
    distances.sort(key=lambda x: x[1])

    # 禁止在最靠近终点的平台上放置收集品
    forbidden_platform = distances[0][0] if distances else None

    # 选择可放置收集品的平台
    collect_candidates = [p for p in platforms if p != forbidden_platform]

    if collect_candidates and item_id:
        placement = placement or {}
        if "x" in placement and "y" in placement:
            cx = int(placement["x"])
            cy = int(placement["y"])
        else:
            platform_index = int(
                placement.get("platform", len(collect_candidates) // 2)
            )
            platform_index = max(0, min(platform_index, len(platforms) - 1))
            plat = platforms[platform_index]
            if plat == forbidden_platform or plat not in collect_candidates:
                plat = collect_candidates[len(collect_candidates) // 2]
            min_x = plat.rect.x + 15
            max_x = max(min_x, plat.rect.x + plat.rect.w - 60)
            cx = max(min_x, min(int(placement.get("x", (min_x + max_x) // 2)), max_x))
            cy = int(placement.get("y", plat.rect.y - 40))

        art_path = "images/collectibles/gameplay/box.gif"
        collect = CollectItem(
            cx,
            cy,
            item_id=item_id,
            art_path=art_path,
            visible=placement.get("visible", True),
        )
        return collect

    return None


def _create_enemies(platforms, goal, collect, enemy_configs):
    """
    创建敌人（内部方法）

    在除终点、收集品和剧情方块所在平台外的平台上随机生成敌人

    Args:
        platforms: 平台列表
        goal: 终点目标点
        collect: 收集品对象（可能为 None）
    """
    # 计算各平台到终点的距离
    distances = [
        (
            p,
            abs(p.rect.centerx - goal.rect.centerx)
            + abs(p.rect.centery - goal.rect.centery),
        )
        for p in platforms
    ]
    distances.sort(key=lambda x: x[1])

    # 禁止放置的平台
    forbidden_platform = distances[0][0] if distances else None

    for enemy_config in enemy_configs:
        platform_index = enemy_config.get("platform", 0)
        if not 0 <= platform_index < len(platforms):
            continue
        p = platforms[platform_index]
        # 跳过禁止放置的平台
        if p == forbidden_platform:
            continue
        if p.has_collectible:
            continue
        if p.story_blocks:
            continue

        enemy_x = p.rect.x + enemy_config.get("offset_x", 20)
        enemy_y = p.rect.y - 35
        enemy = Enemy(enemy_x, enemy_y, p)
        p.enemies.append(enemy)


def _create_hazards(hazard_configs):
    hazards = []
    for hazard_config in hazard_configs:
        if hazard_config.get("type") != "spike":
            continue
        hazards.append(
            SpikeHazard(
                hazard_config["x"],
                hazard_config["y"],
                hazard_config.get("w", 60),
                hazard_config.get("h", 24),
                hazard_config.get("visible", True),
                art_path=hazard_config.get("art_path"),
                trigger_rect=hazard_config.get("trigger_rect"),
                speed=hazard_config.get("speed", 0.0),
                direction=hazard_config.get("direction", 1),
                origin_rect=hazard_config.get("origin_rect"),
                behavior=hazard_config.get("behavior", "moving"),
                flip_x=hazard_config.get("flip_x", False),
                flip_y=hazard_config.get("flip_y", False),
            )
        )
    return hazards
