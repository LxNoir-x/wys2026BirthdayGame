"""统一的界面绘制工具。

界面状态只负责排版和交互，颜色、面板、按钮与文字适配集中在这里，避免
每个页面各自绘制一套互相冲突的控件。
"""

from __future__ import annotations

import sys
from pathlib import Path

import pygame

from config import SCREEN_HEIGHT, SCREEN_WIDTH
from utils.draw_utils import draw_gradient_background

UI_COLORS = {
    "bg_top": (10, 15, 28),
    "bg_bottom": (23, 31, 49),
    "surface": (25, 34, 53),
    "surface_alt": (31, 42, 64),
    "surface_hover": (40, 55, 82),
    "text": (238, 242, 249),
    "muted": (147, 163, 186),
    "border": (67, 84, 113),
    "accent": (99, 211, 255),
    "accent_soft": (44, 103, 137),
    "gold": (247, 198, 103),
    "green": (98, 220, 163),
    "red": (255, 113, 128),
    "purple": (190, 143, 255),
}


BUTTON_STYLES = {
    "primary": (UI_COLORS["accent"], UI_COLORS["accent_soft"]),
    "secondary": (UI_COLORS["border"], UI_COLORS["surface_alt"]),
    "success": (UI_COLORS["green"], (39, 100, 78)),
    "danger": (UI_COLORS["red"], (108, 48, 62)),
    "gold": (UI_COLORS["gold"], (111, 83, 43)),
}


def get_font(font_cache, key="body"):
    """获取新字体，兼容旧存档/旧运行环境中的字体缓存。"""

    fallbacks = {
        "title": "large",
        "button": "medium",
        "body": "small",
        "caption": "tiny",
        "micro": "tiny",
        "desc_small": "micro",
    }
    return font_cache.get(key) or font_cache[fallbacks.get(key, "small")]


def draw_ui_background(screen, accent=None):
    """绘制低对比度背景网格，提供统一的页面层级。"""

    draw_gradient_background(screen, UI_COLORS["bg_top"], UI_COLORS["bg_bottom"])
    grid = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    for x in range(0, SCREEN_WIDTH, 80):
        pygame.draw.line(grid, (130, 170, 210, 10), (x, 0), (x, SCREEN_HEIGHT), 1)
    for y in range(0, SCREEN_HEIGHT, 80):
        pygame.draw.line(grid, (130, 170, 210, 9), (0, y), (SCREEN_WIDTH, y), 1)
    screen.blit(grid, (0, 0))

    glow = accent or UI_COLORS["accent"]
    atmosphere = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    pygame.draw.circle(atmosphere, (*glow, 18), (SCREEN_WIDTH - 80, 90), 240)
    pygame.draw.circle(atmosphere, (*UI_COLORS["purple"], 10), (100, SCREEN_HEIGHT - 60), 210)
    screen.blit(atmosphere, (0, 0))


def _with_alpha(color, alpha):
    """补全 RGB 颜色的透明度；已带 alpha 的四元组原样返回。"""

    return color if len(color) == 4 else (*color, alpha)


def draw_panel(screen, rect, fill=None, border=None, radius=14, shadow=True):
    """绘制带阴影的圆角面板。fill/border 可传 RGBA 以绘制半透明面板。"""

    rect = pygame.Rect(rect)
    fill = fill or UI_COLORS["surface"]
    border = border or UI_COLORS["border"]
    if shadow:
        shadow_surface = pygame.Surface((rect.width + 16, rect.height + 16), pygame.SRCALPHA)
        pygame.draw.rect(
            shadow_surface,
            (0, 0, 0, 90),
            (8, 8, rect.width, rect.height),
            border_radius=radius,
        )
        screen.blit(shadow_surface, (rect.x - 8, rect.y - 2))

    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(
        panel, _with_alpha(fill, 242), panel.get_rect(), border_radius=radius
    )
    pygame.draw.rect(
        panel, _with_alpha(border, 220), panel.get_rect(), 1, border_radius=radius
    )
    screen.blit(panel, rect)
    return rect


def draw_button(screen, rect, text, font, variant="secondary", enabled=True, align="center"):
    """绘制统一按钮并返回实际点击矩形。"""

    rect = pygame.Rect(rect)
    mouse_pos = pygame.mouse.get_pos()
    hovered = enabled and rect.collidepoint(mouse_pos)
    border, fill = BUTTON_STYLES.get(variant, BUTTON_STYLES["secondary"])
    if not enabled:
        border, fill = UI_COLORS["border"], (35, 42, 57)
    elif hovered:
        fill = UI_COLORS["surface_hover"]

    if enabled and hovered:
        glow = pygame.Surface((rect.width + 12, rect.height + 12), pygame.SRCALPHA)
        pygame.draw.rect(glow, (*border, 32), glow.get_rect(), border_radius=12)
        screen.blit(glow, (rect.x - 6, rect.y - 6))

    draw_panel(screen, rect, fill=fill, border=border, radius=10, shadow=False)
    label_color = UI_COLORS["text"] if enabled else UI_COLORS["muted"]
    label = fit_text(font, text, rect.width - 26, label_color)
    if align == "left":
        label_rect = label.get_rect(midleft=(rect.left + 16, rect.centery))
    else:
        label_rect = label.get_rect(center=rect.center)
    screen.blit(label, label_rect)
    return rect


def draw_chip(screen, rect, text, font, color=None, fill=None):
    """绘制小型状态标签。"""

    color = color or UI_COLORS["accent"]
    fill = fill or (color[0] // 5, color[1] // 5, color[2] // 5)
    rect = pygame.Rect(rect)
    surface = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(surface, (*fill, 220), surface.get_rect(), border_radius=8)
    pygame.draw.rect(surface, (*color, 180), surface.get_rect(), 1, border_radius=8)
    screen.blit(surface, rect)
    label = fit_text(font, text, rect.width - 12, color)
    screen.blit(label, label.get_rect(center=rect.center))
    return rect


def fit_text(font, text, max_width, color):
    """超出区域时以省略号截断，避免裸露或重叠文字。

    主字体（Cubic-11 像素字体）缺少的生僻字会逐字补字形，见 render_text。
    """

    text = str(text)
    if measure_text(font, text) <= max_width:
        return render_text(font, text, color)
    suffix = "…"
    while text and measure_text(font, text + suffix) > max_width:
        text = text[:-1]
    return render_text(font, text + suffix, color)


# 用未分配码位的字形度量作为"缺字占位字形"的基准。
_MISSING_PROBE = "\uffff"
_FALLBACK_FILE = "SourceHanSansSC-Regular.otf"
_FALLBACK_FONTS: dict[int, pygame.font.Font] = {}

# Cubic-11 是 11 列像素字体，缺字可以由同字体的其它字形左右拼接补出来，
# 这样字形风格和其它文字完全一致。值为 (左部件来源字, 右部件来源字, 从第
# 几个设计列起换用右部件)：凇=冫+松（冰的冫 + 淞的松），铳=钅+充（钢的钅
# + 统的充，统是纟+充，右部件正好是压缩版的充）。
_COMPOSED_GLYPHS = {"凇": ("冰", "淞", 3), "铳": ("钢", "统", 4)}
_GRID_COLUMNS = 11
_COMPOSED_CACHE: dict[tuple, pygame.Surface] = {}


def _fonts_dir():
    root = Path(__file__).resolve().parents[1] / "assets" / "fonts"
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        packed = Path(meipass) / "assets" / "fonts"
        if packed.is_dir():
            return packed
    return root


def _fallback_font(font):
    """返回与主字体同字号的回退字体（覆盖主字体缺失的生僻字）。"""

    size = max(8, round(font.size("汉")[0]))
    cached = _FALLBACK_FONTS.get(size)
    if cached is None:
        path = _fonts_dir() / _FALLBACK_FILE
        try:
            cached = pygame.font.Font(str(path) if path.is_file() else None, size)
        except pygame.error:
            cached = pygame.font.Font(None, size)
        _FALLBACK_FONTS[size] = cached
    return cached


def _ink_rect(surface):
    """返回文本表面的墨迹外接矩形（无墨迹时为空矩形）。"""

    rects = pygame.mask.from_surface(surface, 20).get_bounding_rects()
    if not rects:
        return pygame.Rect(0, 0, 0, 0)
    rect = rects[0].copy()
    for other in rects[1:]:
        rect.union_ip(other)
    return rect


def _composed_glyph(font, character, color):
    """用同字体的其它字形左右拼接出主字体缺失的字。

    画布取来源字的排版框，因此宽高与主字体汉字完全一致，调用方排版不受影响。
    """

    key = (id(font), character, tuple(color))
    cached = _COMPOSED_CACHE.get(key)
    if cached is not None:
        return cached

    left_source, right_source, split_column = _COMPOSED_GLYPHS[character]
    left = font.render(left_source, True, color)
    right = font.render(right_source, True, color)
    width, height = left.get_size()
    minimum, maximum = font.metrics("汉")[0][:2]
    split = minimum + round(split_column * (maximum - minimum) / _GRID_COLUMNS)
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    surface.blit(left, (0, 0), pygame.Rect(0, 0, split, height))
    surface.blit(right, (split, 0), pygame.Rect(split, 0, width - split, height))
    _COMPOSED_CACHE[key] = surface
    return surface


def _text_segments(font, text):
    """按渲染方式把文本切段，返回 [(片段, 方式)]。

    方式取值：``plain`` 主字体直接渲染；``composed`` 用同字体其它字形拼接；
    ``fallback`` 主字体与拼接都补不出，回退到全字库字体。
    """

    probe = font.metrics(_MISSING_PROBE)
    probe = tuple(probe[0]) if probe else None
    segments = []
    for character, metric in zip(text, font.metrics(text)):
        if character in _COMPOSED_GLYPHS:
            kind = "composed"
        elif (
            probe is not None
            and metric is not None
            and tuple(metric) == probe
            and character not in " \n\t"
        ):
            kind = "fallback"
        else:
            kind = "plain"
        if segments and segments[-1][1] == kind:
            segments[-1][0] += character
        else:
            segments.append([character, kind])
    return segments


def measure_text(font, text):
    """测量文本宽度，缺字部分按实际使用的字形计算。"""

    text = str(text)
    if "\n" in text:
        return max((measure_text(font, line) for line in text.split("\n")), default=0)
    total = 0
    for chunk, kind in _text_segments(font, text):
        if kind == "composed":
            # 拼接字的排版框与主字体汉字相同，逐字累加即可。
            total += sum(font.size(character)[0] for character in chunk)
        elif kind == "fallback":
            total += _fallback_font(font).size(chunk)[0]
        else:
            total += font.size(chunk)[0]
    return total


def render_text(font, text, color):
    """渲染文本；主字体缺失的字形逐字补出来，避免显示成缺字占位原点。

    能由同字体其它字形拼出的字（凇、铳）直接拼接，字形风格与其它文字一致；
    补不出的才回退到全字库字体，并按主字体汉字的墨迹中心对齐。画布尺寸与
    主字体单行一致，调用方用 get_rect(center/topleft/...) 排版时位置不变。
    """

    text = str(text)
    segments = _text_segments(font, text)
    if not any(kind != "plain" for _, kind in segments):
        return font.render(text, True, color)

    height = font.get_height()
    target_center = _ink_rect(font.render("汉", True, color)).centery
    parts = []
    for chunk, kind in segments:
        if kind == "composed":
            parts.extend(
                (_composed_glyph(font, character, color), 0) for character in chunk
            )
            continue
        if kind == "plain":
            parts.append((font.render(chunk, True, color), 0))
            continue
        surface = _fallback_font(font).render(chunk, True, color)
        ink = _ink_rect(surface)
        if ink.height:
            # 只收掉上下空白，保留字宽，使总宽度与 measure_text 一致。
            trimmed = pygame.Surface((surface.get_width(), ink.height), pygame.SRCALPHA)
            trimmed.blit(surface, (0, 0), ink)
            surface = trimmed
        parts.append((surface, target_center - surface.get_height() // 2))

    canvas = pygame.Surface(
        (max(1, sum(surface.get_width() for surface, _ in parts)), height), pygame.SRCALPHA
    )
    x = 0
    for surface, y in parts:
        canvas.blit(surface, (x, y))
        x += surface.get_width()
    return canvas


def wrap_text(font, text, max_width):
    """按字体实际宽度换行，兼容中英文混排。"""

    lines = []
    current = ""
    for character in str(text):
        candidate = current + character
        if current and measure_text(font, candidate) > max_width:
            lines.append(current)
            current = character
        else:
            current = candidate
    if current or not lines:
        lines.append(current)
    return lines


def draw_text_lines(screen, lines, font, x, y, color=None, line_gap=5):
    color = color or UI_COLORS["text"]
    line_height = font.get_linesize() + line_gap
    for index, line in enumerate(lines):
        screen.blit(render_text(font, line, color), (x, y + index * line_height))
    return y + len(lines) * line_height


def draw_page_header(screen, font_cache, eyebrow, title, subtitle="", accent=None):
    """绘制统一页面标题区。"""

    accent = accent or UI_COLORS["accent"]
    eyebrow_font = get_font(font_cache, "caption")
    title_font = get_font(font_cache, "title")
    body_font = get_font(font_cache, "caption")
    eyebrow_surface = render_text(eyebrow_font, eyebrow.upper(), accent)
    screen.blit(eyebrow_surface, (72, 36))
    title_surface = render_text(title_font, title, UI_COLORS["text"])
    screen.blit(title_surface, (72, 58))
    if subtitle:
        subtitle_surface = fit_text(body_font, subtitle, 700, UI_COLORS["muted"])
        screen.blit(subtitle_surface, (74, 116))


def draw_scrollbar(screen, rect, scroll, max_scroll, viewport_height, content_height, accent=None):
    """绘制可见且可拖动的滚动条。"""

    if max_scroll <= 0 or content_height <= viewport_height:
        return pygame.Rect(0, 0, 0, 0)
    accent = accent or UI_COLORS["accent"]
    rect = pygame.Rect(rect)
    pygame.draw.rect(screen, (13, 19, 31), rect, border_radius=5)
    ratio = viewport_height / content_height
    thumb_height = max(42, int(rect.height * ratio))
    travel = rect.height - thumb_height
    thumb_y = rect.y + int(travel * (scroll / max_scroll))
    thumb = pygame.Rect(rect.x, thumb_y, rect.width, thumb_height)
    pygame.draw.rect(screen, (*accent, 200), thumb, border_radius=5)
    return thumb
