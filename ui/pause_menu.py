"""暂停菜单绘制：操作、键位说明与音量三个页签。"""

from __future__ import annotations

import pygame

from utils.ui_art import draw_background, draw_image, load_image
from utils.ui_theme import UI_COLORS, fit_text, get_font

# 源 PSD 画布为 1920x1080，运行时按 1280x720 缩放到 2/3。
PSD_SCALE = 2 / 3

TAB_SPECS = (
    ("actions", pygame.Rect(319, 208, 75, 75), "tab_actions", (37, 48)),
    ("controls", pygame.Rect(319, 296, 75, 75), "tab_controls", (47, 33)),
    ("audio", pygame.Rect(319, 382, 75, 75), "tab_audio", (37, 56)),
)

ACTION_BUTTONS = (
    ("continue", pygame.Rect(458, 238, 453, 52), "frame_1.png", "continue.png"),
    ("restart", pygame.Rect(458, 298, 453, 52), "frame_2.png", "restart.png"),
    ("level_select", pygame.Rect(458, 358, 453, 52), "frame_3.png", "level_select.png"),
    ("skip", pygame.Rect(458, 418, 453, 52), "frame_4.png", "skip.png"),
    ("streamer", pygame.Rect(458, 478, 453, 52), "frame_4.png", None),
)

# 操作说明：直接使用 PSD 导出的按键与动作文本原画（坐标为 PSD 像素框）。
CONTROL_ENTRIES = (
    ("ctrl_label_up", (662, 365, 32, 33)),
    ("ctrl_key_w", (931, 365, 59, 33)),
    ("ctrl_label_left", (1061, 365, 32, 33)),
    ("ctrl_key_a", (1333, 365, 53, 33)),
    ("ctrl_label_down", (662, 444, 32, 33)),
    ("ctrl_key_s", (940, 444, 50, 33)),
    ("ctrl_label_right", (1061, 444, 32, 33)),
    ("ctrl_key_d", (1333, 444, 53, 33)),
    ("ctrl_label_jump", (662, 523, 72, 33)),
    ("ctrl_key_space", (849, 523, 142, 33)),
    ("ctrl_label_lever", (663, 602, 151, 33)),
    ("ctrl_key_e", (941, 602, 50, 33)),
    ("ctrl_label_pause", (1064, 602, 72, 33)),
    ("ctrl_key_esc", (1291, 602, 95, 33)),
)

# 音量调节：标签、滑条、滑块原画（坐标为 PSD 像素框）。
SLIDER_SPECS = (
    ("master", "audio_label_master", (665, 365, 101, 47), (793, 386, 588, 7), (1346, 379, 21, 21)),
    ("music", "audio_label_music", (665, 451, 101, 47), (793, 471, 588, 7), (1346, 464, 21, 21)),
    ("sfx", "audio_label_sfx", (665, 537, 101, 47), (793, 561, 588, 7), (1346, 554, 21, 21)),
)


def _scaled(rect):
    """把 PSD 像素框换算成运行时矩形。"""

    x, y, width, height = rect
    return pygame.Rect(
        round(x * PSD_SCALE),
        round(y * PSD_SCALE),
        max(1, round(width * PSD_SCALE)),
        max(1, round(height * PSD_SCALE)),
    )


# 选择浮标：普通按钮用 cursor，主播模式按钮用专用的 cursor_special。
CURSOR_ASSET = "images/ui/pause/cursor.png"
CURSOR_SPECIAL_ASSET = "images/ui/pause/cursor_special.png"
CURSOR_SIZE = _scaled((0, 0, 438, 128)).size
CURSOR_SPECIAL_SIZE = _scaled((0, 0, 536, 128)).size
# cursor.png 是左右分离的两半：左边一臂、右边一臂，中间留给按钮文字。
# 记录两臂在素材里的原始列范围，绘制时按文字宽度把两臂向外让开。
CURSOR_LEFT_SLICE = (0, 0, 114, 128)
CURSOR_RIGHT_SLICE = (324, 0, 114, 128)
# 两臂外移后与文字之间至少保留的间隙（像素）。
CURSOR_TEXT_GAP = 8
# 主播模式开关文字专用贴图（与其它按钮的文字原画同为 2/3 缩放）。
STREAMER_ON_ASSET = "images/ui/pause/live_on.png"
STREAMER_OFF_ASSET = "images/ui/pause/live_off.png"
STREAMER_LABEL_SIZE = _scaled((0, 0, 342, 47)).size


def draw_pause_menu(
    screen,
    font_cache,
    *,
    skip_label="直接跳关",
    active_tab="actions",
    selected_index=0,
    volumes=None,
    hovered_slider=None,
    streamer_mode=False,
    hovered_index=None,
    action_items=None,
):
    """绘制暂停菜单并返回统一使用的可见/点击矩形。"""

    draw_background(screen, "images/ui/pause.png")
    volumes = volumes or {"master": 1.0, "music": 0.5, "sfx": 1.0}
    menu_rect = pygame.Rect(406, 205, 557, 365)
    mouse_position = pygame.mouse.get_pos()

    tab_rects = {}
    for tab, slot, prefix, icon_size in TAB_SPECS:
        draw_image(screen, f"images/ui/pause/{prefix}_frame.png", slot, smooth=True)
        icon_asset = f"{prefix}_selected.png" if tab == active_tab else f"{prefix}_normal.png"
        icon_rect = pygame.Rect((0, 0), icon_size)
        icon_rect.center = slot.center
        draw_image(screen, f"images/ui/pause/{icon_asset}", icon_rect, smooth=True)
        tab_rects[tab] = slot

    buttons = {}
    sliders = {}
    hovered = None
    cursor = None
    if active_tab == "actions":
        buttons, hovered, cursor = _draw_actions(
            screen,
            font_cache,
            skip_label,
            selected_index,
            hovered_index,
            streamer_mode,
            mouse_position,
            action_items,
        )
    elif active_tab == "controls":
        _draw_controls(screen)
    else:
        sliders = _draw_audio(screen, volumes, hovered_slider, mouse_position)

    return {
        "menu_rect": menu_rect,
        "tabs": tab_rects,
        "buttons": buttons,
        "sliders": sliders,
        "hovered": hovered,
        "cursor": cursor,
    }


def _draw_actions(
    screen,
    font_cache,
    skip_label,
    selected_index,
    hovered_index,
    streamer_mode,
    mouse_position,
    action_items,
):
    items = list(action_items) if action_items is not None else [
        (name, None) for name, *_rest in ACTION_BUTTONS
    ]
    slots = ACTION_BUTTONS[: len(items)]
    hovered = next(
        (
            index
            for index, (_name, rect, _frame, _label) in enumerate(slots)
            if rect.collidepoint(mouse_position)
        ),
        None,
    )
    if hovered is not None:
        cursor_index = hovered
    elif hovered_index is not None:
        cursor_index = hovered_index
    else:
        cursor_index = selected_index
    cursor_index = max(0, min(len(items) - 1, int(cursor_index)))

    label_font = get_font(font_cache, "button")
    buttons = {}
    label_widths = {}
    for (name, custom_label), (_slot_name, rect, frame_asset, label_asset) in zip(
        items, slots
    ):
        draw_image(screen, f"images/ui/pause/{frame_asset}", rect, smooth=True)
        if custom_label is not None:
            # 有文字标签时统一沿用“最上面选项”的字号与颜色，三个选项保持一致；
            # 删除存档在二次确认态仍保留红色。
            color = UI_COLORS["red"] if name == "clear" else UI_COLORS["text"]
            label = fit_text(label_font, custom_label, rect.width - 60, color)
            label_widths[name] = label.get_width()
            screen.blit(label, label.get_rect(center=rect.center))
        elif name == "streamer":
            # 无文字标签（旧调用）时仍用专用贴图。
            asset = STREAMER_ON_ASSET if streamer_mode else STREAMER_OFF_ASSET
            label_rect = pygame.Rect((0, 0), STREAMER_LABEL_SIZE)
            label_rect.center = rect.center
            draw_image(screen, asset, label_rect, smooth=True)
        elif name == "skip" and skip_label != "直接跳关":
            label = fit_text(label_font, skip_label, 200, UI_COLORS["text"])
            label_widths[name] = label.get_width()
            screen.blit(label, label.get_rect(center=rect.center))
        else:
            label_rect = pygame.Rect(0, 0, 149, 31)
            label_rect.center = rect.center
            draw_image(screen, f"images/ui/pause/{label_asset}", label_rect, smooth=True)
        buttons[name] = rect

    cursor_name = items[cursor_index][0]
    cursor_slot = slots[cursor_index][1]
    if cursor_name == "streamer":
        cursor_rect = pygame.Rect((0, 0), CURSOR_SPECIAL_SIZE)
        cursor_rect.center = cursor_slot.center
        draw_image(screen, CURSOR_SPECIAL_ASSET, cursor_rect, smooth=True)
    else:
        _draw_split_cursor(
            screen, cursor_slot.center, label_widths.get(cursor_name, 0)
        )
    return buttons, hovered, cursor_index


_CURSOR_PIECE_CACHE: list[pygame.Surface] | None = None


def _cursor_pieces():
    """把光标素材切成左右两臂并缩放到运行时尺寸（只做一次）。"""

    global _CURSOR_PIECE_CACHE
    if _CURSOR_PIECE_CACHE is None:
        source = load_image(CURSOR_ASSET)
        scale_x = CURSOR_SIZE[0] / source.get_width()
        scale_y = CURSOR_SIZE[1] / source.get_height()
        pieces = []
        for left, top, width, height in (CURSOR_LEFT_SLICE, CURSOR_RIGHT_SLICE):
            piece = source.subsurface(pygame.Rect(left, top, width, height)).copy()
            pieces.append(
                pygame.transform.smoothscale(
                    piece,
                    (max(1, round(width * scale_x)), max(1, round(height * scale_y))),
                )
            )
        _CURSOR_PIECE_CACHE = pieces
    return _CURSOR_PIECE_CACHE


def _draw_split_cursor(screen, center, text_width):
    """按文字宽度绘制光标左右两臂：文字变长时两臂各向外让开，自身尺寸不变。"""

    left_piece, right_piece = _cursor_pieces()
    half = CURSOR_SIZE[0] // 2
    inner_gap = half - left_piece.get_width()
    extra = max(0, text_width // 2 + CURSOR_TEXT_GAP - inner_gap)
    left_rect = left_piece.get_rect(midright=(center[0] - inner_gap - extra, center[1]))
    right_rect = right_piece.get_rect(midleft=(center[0] + inner_gap + extra, center[1]))
    screen.blit(left_piece, left_rect)
    screen.blit(right_piece, right_rect)


def _draw_controls(screen):
    for asset, box in CONTROL_ENTRIES:
        draw_image(screen, f"images/ui/pause/{asset}.png", _scaled(box), smooth=True)


def _draw_audio(screen, volumes, hovered_slider, mouse_position):
    sliders = {}
    for name, label_asset, label_box, bar_box, knob_box in SLIDER_SPECS:
        label_rect = _scaled(label_box)
        bar_rect = _scaled(bar_box)
        knob_size = _scaled(knob_box).size
        draw_image(screen, f"images/ui/pause/{label_asset}.png", label_rect, smooth=True)
        draw_image(screen, "images/ui/pause/audio_bar.png", bar_rect, smooth=True)

        value = max(0.0, min(1.0, float(volumes.get(name, 0.5))))
        hovered = hovered_slider == name or bar_rect.inflate(0, 40).collidepoint(
            mouse_position
        )
        knob_center_x = bar_rect.left + round(bar_rect.width * value)
        knob_rect = pygame.Rect((0, 0), knob_size)
        knob_rect.center = (knob_center_x, bar_rect.centery)
        if hovered:
            knob_rect.inflate_ip(4, 4)
        draw_image(screen, "images/ui/pause/audio_knob.png", knob_rect, smooth=True)

        sliders[name] = bar_rect.inflate(0, 34)
    return sliders
