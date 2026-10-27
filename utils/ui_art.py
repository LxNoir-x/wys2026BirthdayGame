"""需求素材的加载与绘制工具。

需求中的 UI 是按 1920x1080 / 2646x1489 / 3840x2160 导出的合成图。
运行时统一缩放到游戏窗口，页面状态只处理交互与动态数据。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pygame

from config import SCREEN_HEIGHT, SCREEN_WIDTH

_IMAGE_CACHE: dict[str, pygame.Surface] = {}
_SCALED_CACHE: dict[tuple[str, int, int], pygame.Surface] = {}
_GIF_CACHE: dict[str, tuple[list[pygame.Surface], int]] = {}
_MAP_CACHE: dict[str, dict[str, object]] = {}
_SPIKE_DIRECTION_CACHE: dict[str, str] = {}
_SOLID_RECTS_CACHE: dict[tuple, tuple[pygame.Rect, ...]] = {}


def _asset_roots() -> list[Path]:
    roots = [Path(__file__).resolve().parent.parent / "assets"]
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        roots.insert(0, Path(meipass) / "assets")
    return roots


def asset_path(relative_path: str) -> Path:
    """返回打包环境或开发环境中的资源路径。"""

    relative = Path(relative_path)
    for root in _asset_roots():
        candidate = root / relative
        if candidate.is_file():
            return candidate
    return _asset_roots()[0] / relative


def load_image(relative_path: str) -> pygame.Surface:
    """加载并缓存一张带透明通道的图片。"""

    if relative_path not in _IMAGE_CACHE:
        path = asset_path(relative_path)
        image = pygame.image.load(str(path))
        try:
            image = image.convert_alpha()
        except pygame.error:
            image = image.convert()
        _IMAGE_CACHE[relative_path] = image
    return _IMAGE_CACHE[relative_path]


def scaled_image(
    relative_path: str, size=(SCREEN_WIDTH, SCREEN_HEIGHT)
) -> pygame.Surface:
    """按目标窗口尺寸缓存缩放后的图片。"""

    width, height = int(size[0]), int(size[1])
    key = (relative_path, width, height)
    if key not in _SCALED_CACHE:
        _SCALED_CACHE[key] = pygame.transform.smoothscale(
            load_image(relative_path), (width, height)
        )
    return _SCALED_CACHE[key]


def draw_background(screen: pygame.Surface, relative_path: str) -> pygame.Rect:
    """铺满窗口绘制一张 UI 合成底图。"""

    image = scaled_image(relative_path, screen.get_size())
    screen.blit(image, (0, 0))
    return image.get_rect(topleft=(0, 0))


def load_level_map(relative_path: str) -> dict[str, object]:
    """读取并缓存 PSD 导出的地图数据。"""

    if relative_path not in _MAP_CACHE:
        map_path = asset_path(relative_path)
        _MAP_CACHE[relative_path] = json.loads(map_path.read_text(encoding="utf-8"))
    return _MAP_CACHE[relative_path]


def level_map_layout(relative_path: str, layout_id: str) -> dict[str, object]:
    """Return one named PSD-derived layout record or raise a useful configuration error."""

    layouts = load_level_map(relative_path).get("layouts", [])
    matches = [layout for layout in layouts if layout.get("id") == layout_id]
    if len(matches) != 1:
        message = "missing" if not matches else "duplicated"
        raise ValueError(f"Layout id {layout_id!r} is {message} in {relative_path}")
    return matches[0]


def level_map_layout_rect(relative_path: str, layout_id: str) -> pygame.Rect:
    """Return the runtime rectangle for one named PSD-derived layout record."""

    rect = level_map_layout(relative_path, layout_id)["rect"]
    return pygame.Rect(rect["x"], rect["y"], rect["width"], rect["height"])


def _element_layer_path(element) -> str:
    return "/".join(element.get("layer_path", ()))


def _element_offset(element, element_offsets=None) -> pygame.Vector2:
    if not element_offsets:
        return pygame.Vector2()
    return pygame.Vector2(element_offsets.get(_element_layer_path(element), (0, 0)))


def level_map_solid_rects(
    relative_path: str,
    element_offsets=None,
) -> list[pygame.Rect]:
    """按素材透明度生成地形碰撞，避免外接矩形形成空气墙。"""

    offset_key = tuple(
        sorted(
            (str(path), int(offset[0]), int(offset[1]))
            for path, offset in (element_offsets or {}).items()
        )
    )
    cache_key = (relative_path, offset_key)
    if cache_key in _SOLID_RECTS_CACHE:
        return [rect.copy() for rect in _SOLID_RECTS_CACHE[cache_key]]

    solid_rects: list[pygame.Rect] = []
    for element in load_level_map(relative_path)["elements"]:
        collision = element.get("collision")
        if not collision or collision.get("type") != "solid":
            continue
        rect = element["rect"]
        offset = _element_offset(element, element_offsets)
        target = pygame.Rect(
            rect["x"] + round(offset.x),
            rect["y"] + round(offset.y),
            rect["width"],
            rect["height"],
        )
        top_only = element.get("element_type") == "terrain_platform"
        solid_rects.extend(
            _alpha_collision_rects(
                element["asset"],
                target,
                max_height=min(14, target.height) if top_only else None,
            )
        )

    _SOLID_RECTS_CACHE[cache_key] = tuple(rect.copy() for rect in solid_rects)
    return [rect.copy() for rect in solid_rects]


def level_map_surface_top(
    relative_path: str,
    x_left: int,
    x_right: int,
    min_y: int,
    max_y: int,
    element_offsets=None,
) -> int | None:
    """返回一段水平区间内实心地形完整砖面的顶边。

    地形的碰撞顶边由 alpha 瓦片量化得到，可能停在草叶尖端；这里在候选
    图元中寻找第一条近乎满宽的实心行，即真正的砖面基准。
    """

    offsets = element_offsets or {}
    surfaces: list[int] = []
    for element in load_level_map(relative_path)["elements"]:
        collision = element.get("collision")
        if not collision or collision.get("type") != "solid":
            continue
        rect = element["rect"]
        offset = _element_offset(element, offsets)
        target = pygame.Rect(
            rect["x"] + round(offset.x),
            rect["y"] + round(offset.y),
            rect["width"],
            rect["height"],
        )
        if target.right <= x_left or target.left >= x_right:
            continue
        if target.top < min_y or target.top > max_y:
            continue
        surface = _full_width_top(element["asset"], target)
        if surface is not None:
            surfaces.append(surface)
    return min(surfaces) if surfaces else None


def _full_width_top(
    relative_path: str,
    target: pygame.Rect,
    coverage=0.9,
) -> int | None:
    """返回素材中第一条实心像素覆盖率达到整宽的行的世界 y 坐标。"""

    image = load_image(relative_path)
    if image.get_size() != target.size:
        image = pygame.transform.scale(image, target.size)
    mask = pygame.mask.from_surface(image, 32)
    threshold = target.width * coverage
    for y in range(target.height):
        solid = 0
        for x in range(target.width):
            if mask.get_at((x, y)):
                solid += 1
                if solid >= threshold:
                    return target.y + y
    return None


def _alpha_collision_rects(
    relative_path: str,
    target: pygame.Rect,
    tile_size=5,
    max_height=None,
):
    """把不规则透明素材压缩成按行合并的碰撞瓦片。"""

    image = load_image(relative_path)
    if image.get_size() != target.size:
        image = pygame.transform.scale(image, target.size)
    mask = pygame.mask.from_surface(image, 32)
    result = []
    if max_height is None:
        scans = [(mask, pygame.Rect(0, 0, target.width, target.height))]
    else:
        # A single PSD layer can contain several platforms at different heights.
        # Treat each opaque island separately so every island gets a thin walkable top.
        scans = [
            (component, component.get_bounding_rects()[0])
            for component in mask.connected_components(max(1, tile_size))
            if component.get_bounding_rects()
        ]

    tile = pygame.mask.Mask((tile_size, tile_size), fill=True)
    for scan_mask, bounds in scans:
        scan_bottom = bounds.bottom
        if max_height is not None:
            scan_bottom = min(scan_bottom, bounds.top + max_height)
        rows = []
        for y in range(bounds.top, scan_bottom, tile_size):
            runs = []
            run_start = None
            for x in range(bounds.left, bounds.right, tile_size):
                occupied = scan_mask.overlap(tile, (x, y)) is not None
                if occupied and run_start is None:
                    run_start = x
                elif not occupied and run_start is not None:
                    runs.append((run_start, x - run_start))
                    run_start = None
            if run_start is not None:
                runs.append((run_start, bounds.right - run_start))
            rows.append((y, runs))

        active = {}
        for y, runs in rows:
            current = set(runs)
            for run, rect in list(active.items()):
                if run not in current:
                    result.append(rect)
                    del active[run]
            for run in runs:
                height = min(scan_bottom, y + tile_size) - y
                if run in active:
                    active[run].height += height
                else:
                    active[run] = pygame.Rect(run[0], y, run[1], height)
        result.extend(active.values())

    for rect in result:
        rect.move_ip(target.topleft)
    return result


def level_map_hazard_rects(relative_path: str) -> list[pygame.Rect]:
    """返回地图中由原始美术绘制的伤害区域。"""

    hazard_rects = []
    for element in load_level_map(relative_path)["elements"]:
        collision = element.get("collision")
        if not collision or collision.get("type") != "hazard":
            continue
        rect = element["rect"]
        hazard_rects.append(
            pygame.Rect(rect["x"], rect["y"], rect["width"], rect["height"])
        )
    return hazard_rects


def infer_spike_direction(asset: str) -> str:
    """根据刺素材中底座一侧的像素密度识别刺尖方向。"""

    if asset in _SPIKE_DIRECTION_CACHE:
        return _SPIKE_DIRECTION_CACHE[asset]

    mask = pygame.mask.from_surface(load_image(asset))
    bounds = mask.get_bounding_rects()
    if not bounds:
        direction = "down"
    else:
        bound = bounds[0].copy()
        for rect in bounds[1:]:
            bound.union_ip(rect)
        weighted_x = 0
        weighted_y = 0
        pixel_count = 0
        for y in range(bound.top, bound.bottom):
            for x in range(bound.left, bound.right):
                if not mask.get_at((x, y)):
                    continue
                weighted_x += x - bound.left
                weighted_y += y - bound.top
                pixel_count += 1
        if bound.width >= bound.height:
            mean_y = weighted_y / max(1, pixel_count)
            direction = "down" if mean_y < (bound.height - 1) / 2 else "up"
        else:
            mean_x = weighted_x / max(1, pixel_count)
            direction = "right" if mean_x < (bound.width - 1) / 2 else "left"

    _SPIKE_DIRECTION_CACHE[asset] = direction
    return direction


def level_map_hazards(relative_path: str) -> list[dict[str, object]]:
    """返回地图中地刺的运行时素材、判定框和朝向。"""

    hazards = []
    for element in load_level_map(relative_path)["elements"]:
        collision = element.get("collision")
        if (
            element.get("element_type") != "spike"
            or not collision
            or collision.get("type") != "hazard"
        ):
            continue
        rect = element["rect"]
        hazards.append(
            {
                "rect": pygame.Rect(
                    rect["x"],
                    rect["y"],
                    rect["width"],
                    rect["height"],
                ),
                "asset": element["asset"],
                "direction": infer_spike_direction(element["asset"]),
            }
        )
    return hazards


def draw_level_map(
    screen: pygame.Surface,
    relative_path: str,
    *,
    excluded_element_types=frozenset(),
    excluded_layer_paths=frozenset(),
    element_offsets=None,
) -> None:
    """Draw a PSD-derived scene map whose elements remain independent at runtime."""

    for element in load_level_map(relative_path)["elements"]:
        if element.get("element_type") in excluded_element_types:
            continue
        if _element_layer_path(element) in excluded_layer_paths:
            continue
        _draw_map_element(screen, element, element_offsets)


def draw_level_map_layers(
    screen: pygame.Surface,
    relative_path: str,
    layer_paths,
    *,
    element_offsets=None,
) -> None:
    """只绘制指定 layer_path 的地图元素，用于把前景元素补画在机关之上。"""

    wanted = set(layer_paths or ())
    if not wanted:
        return
    for element in load_level_map(relative_path)["elements"]:
        if _element_layer_path(element) in wanted:
            _draw_map_element(screen, element, element_offsets)


def _draw_map_element(screen, element, element_offsets=None) -> None:
    rect = element["rect"]
    offset = _element_offset(element, element_offsets)
    draw_image(
        screen,
        element["asset"],
        pygame.Rect(
            rect["x"] + round(offset.x),
            rect["y"] + round(offset.y),
            rect["width"],
            rect["height"],
        ),
        smooth=False,
    )


def draw_image(
    screen: pygame.Surface,
    relative_path: str,
    rect,
    *,
    opacity: int | None = None,
    smooth: bool = True,
) -> pygame.Rect:
    """在指定区域绘制资源，返回实际区域。"""

    target = pygame.Rect(rect)
    image = load_image(relative_path)
    if image.get_size() != target.size:
        transform = pygame.transform.smoothscale if smooth else pygame.transform.scale
        image = transform(image, target.size)
    if opacity is not None:
        image = image.copy()
        image.set_alpha(max(0, min(255, int(opacity))))
    screen.blit(image, target)
    return target


def _gif_frames(relative_path: str) -> tuple[list[pygame.Surface], int]:
    """载入并缓存 GIF，返回 (帧列表, 单帧时长 ms)。"""

    if relative_path not in _GIF_CACHE:
        from PIL import Image

        image = Image.open(asset_path(relative_path))
        frames = []
        duration = max(40, int(image.info.get("duration", 100)))
        for index in range(image.n_frames):
            image.seek(index)
            frame = image.convert("RGBA")
            frames.append(
                pygame.image.fromstring(
                    frame.tobytes("raw", "RGBA"), frame.size, "RGBA"
                )
            )
        _GIF_CACHE[relative_path] = (frames, duration)
    return _GIF_CACHE[relative_path]


def gif_total_seconds(relative_path: str) -> float:
    """返回 GIF 完整播放一遍的秒数（与 draw_gif_frame 的取帧口径一致）。"""

    frames, duration = _gif_frames(relative_path)
    return len(frames) * duration / 1000.0


def draw_gif_frame(
    screen: pygame.Surface,
    relative_path: str,
    rect,
    *,
    smooth: bool = True,
    contain: bool = False,
    align: str = "center",
    elapsed: float | None = None,
) -> pygame.Rect:
    """按 GIF 原始帧时长绘制当前帧，用于界面中的角色预览。

    `elapsed` 为播放进度（秒）：传入时按该进度取帧、播完停在最后一帧不再循环；
    为 None 时按墙钟循环播放。
    """

    target = pygame.Rect(rect)
    frames, duration = _gif_frames(relative_path)
    if elapsed is None:
        frame = frames[(pygame.time.get_ticks() // duration) % len(frames)]
    else:
        index = min(len(frames) - 1, max(0, int(elapsed * 1000 // duration)))
        frame = frames[index]
    if contain:
        scale = min(
            target.width / max(1, frame.get_width()),
            target.height / max(1, frame.get_height()),
        )
        size = (
            max(1, round(frame.get_width() * scale)),
            max(1, round(frame.get_height() * scale)),
        )
        draw_rect = pygame.Rect((0, 0), size)
        if align == "midbottom":
            draw_rect.midbottom = target.midbottom
        else:
            draw_rect.center = target.center
    else:
        size = target.size
        draw_rect = target

    transform = pygame.transform.smoothscale if smooth else pygame.transform.scale
    screen.blit(transform(frame, size), draw_rect)
    return draw_rect


def text_surface(font, text, color, max_width=None) -> pygame.Surface:
    """绘制一行文本，必要时按像素宽度截断。

    与界面层的 fit_text 走同一条渲染路径，主字体缺字时逐字回退到全字库字体。
    """

    # 局部导入：ui_theme 与本模块互不依赖，避免模块级循环导入。
    from utils.ui_theme import fit_text, render_text

    if max_width is None:
        return render_text(font, text, color)
    return fit_text(font, text, max_width, color)
