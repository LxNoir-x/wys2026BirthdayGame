"""运维数据库：皮肤、藏品与成就页面。"""

from __future__ import annotations

from typing import ClassVar

import pygame

from levels.level_data import COLLECTIBLE_BY_ID, MAIN_COLLECTIBLE_IDS
from states.game_state import GameState
from utils.ui_art import (
    draw_background,
    draw_gif_frame,
    draw_image,
    gif_total_seconds,
    load_image,
    text_surface,
)
from utils.ui_theme import (
    draw_text_lines,
    fit_text,
    get_font,
    wrap_text,
)

# 皮肤页仍沿用旧合成底图；藏品页与成就页改用各自的 collectdb 分层素材。
SKINS_BG = "images/ui/archive_skins.png"
# 皮肤页关闭键改用美术素材（与成就页同一张叉掉贴图），不再用代码画像素叉。
SKINS_BTN_CLOSE = (
    "images/achievementsdb/底部窗口/功能按钮/成就界面-ui_0003s_0000s_0002_叉掉.png"
)

# 藏品界面（collectiondb）的分层素材，按 design 2646x1489 → 运行时 1280x720 还原。
COLLECTION_BG = "images/collectiondb/背景组/藏品界面-ui_0004s_0001_背景图.png"
COLLECTION_GLOW = "images/collectiondb/背景组/藏品界面-ui_0004s_0000_光效.png"
COLLECTION_SCREEN = "images/collectiondb/背景组/藏品界面-ui_0004s_0003_显示屏.png"
COLLECTION_WINDOW = "images/collectiondb/button/藏品界面-ui_0003s_0000_窗口底图.png"
COLLECTION_BTN_ZOOM_OUT = "images/collectiondb/button/藏品界面-ui_0003s_0000s_0000_缩小.png"
COLLECTION_BTN_ZOOM_IN = "images/collectiondb/button/藏品界面-ui_0003s_0000s_0001_放大.png"
COLLECTION_BTN_CLOSE = "images/collectiondb/button/藏品界面-ui_0003s_0000s_0002_叉掉.png"
COLLECTION_H_SLIDER = "images/collectiondb/button/藏品界面-ui_0003s_0000s_0005_左右滑块.png"
COLLECTION_V_SLIDER = "images/collectiondb/button/藏品界面-ui_0003s_0000s_0006_上下滑块.png"
COLLECTION_GRID_ART = "images/collectiondb/collection_grid.png"
COLLECTION_SELECTBOX_ART = "images/collectiondb/collection_selectbox.png"
COLLECTION_SELECTING_ART = "images/collectiondb/collection_selecting.png"
COLLECTION_TEXTBOX = "images/collectiondb/藏品文案框/藏品界面-ui_0001s_0000s_0000_藏品文案底框.png"
COLLECTION_QUOTE_LEFT = "images/collectiondb/藏品文案框/藏品界面-ui_0001s_0000s_0000s_0001_左引号.png"
COLLECTION_QUOTE_RIGHT = "images/collectiondb/藏品文案框/藏品界面-ui_0001s_0000s_0000s_0002_右引号.png"
# 竖直滑块上下的切换箭头（button_on 为上行、button_down 为下行）。
COLLECTION_BTN_UP = "images/collectiondb/button/button_on.png"
COLLECTION_BTN_DOWN = "images/collectiondb/button/button_down.png"

# 成就界面（achievementsdb）的分层素材，布局与藏品界面同源。
ACHIEVEMENT_BG = "images/achievementsdb/背景组/成就界面-ui_0004s_0001_背景图.png"
ACHIEVEMENT_GLOW = "images/achievementsdb/背景组/成就界面-ui_0004s_0000_光效.png"
ACHIEVEMENT_SCREEN = "images/achievementsdb/背景组/成就界面-ui_0004s_0003_显示屏.png"
ACHIEVEMENT_WINDOW = "images/achievementsdb/底部窗口/成就界面-ui_0003s_0000_窗口底图.png"
ACHIEVEMENT_BTN_ZOOM_OUT = (
    "images/achievementsdb/底部窗口/装饰按钮/成就界面-ui_0003s_0000s_0000_缩小.png"
)
ACHIEVEMENT_BTN_ZOOM_IN = (
    "images/achievementsdb/底部窗口/装饰按钮/成就界面-ui_0003s_0000s_0001_放大.png"
)
ACHIEVEMENT_BTN_CLOSE = (
    "images/achievementsdb/底部窗口/功能按钮/成就界面-ui_0003s_0000s_0002_叉掉.png"
)
ACHIEVEMENT_H_SLIDER = (
    "images/achievementsdb/底部窗口/装饰按钮/成就界面-ui_0003s_0000s_0005_左右滑块.png"
)
ACHIEVEMENT_V_SLIDER = (
    "images/achievementsdb/底部窗口/功能按钮/成就界面-ui_0003s_0000s_0006_上下滑块.png"
)
ACHIEVEMENT_LIST_BG = (
    "images/achievementsdb/成就栏目/成就界面-ui_0000s_0001s_0005_成就底框.png"
)
ACHIEVEMENT_ITEM = (
    "images/achievementsdb/成就栏目/成就界面-ui_0000s_0001s_0004_成就条目框.png"
)
ACHIEVEMENT_LOCK_ASK = (
    "images/achievementsdb/成就栏目/成就界面-ui_0000s_0001s_0003_未解锁问号.png"
)
ACHIEVEMENT_UNLOCK_BANG = (
    "images/achievementsdb/成就栏目/成就界面-ui_0000s_0001s_0002_解锁感叹号.png"
)
ACHIEVEMENT_SELECTBOX = (
    "images/achievementsdb/成就栏目/成就界面-ui_0000s_0000_成就选择框.png"
)
ACHIEVEMENT_TEXTBOX = (
    "images/achievementsdb/成就文案框/成就界面-ui_0000s_0000s_0001_成就文案底框.png"
)
ACHIEVEMENT_QUOTE_LEFT = (
    "images/achievementsdb/成就文案框/成就界面-ui_0000s_0000s_0000s_0000_左引号.png"
)
ACHIEVEMENT_QUOTE_RIGHT = (
    "images/achievementsdb/成就文案框/成就界面-ui_0000s_0000s_0000s_0001_右引号.png"
)
# 竖直滑块上下的切换箭头（向上/向下）。
ACHIEVEMENT_BTN_UP = (
    "images/achievementsdb/底部窗口/装饰按钮/成就界面-ui_0003s_0000s_0003_向上.png"
)
ACHIEVEMENT_BTN_DOWN = (
    "images/achievementsdb/底部窗口/装饰按钮/成就界面-ui_0003s_0000s_0004_向下.png"
)

# 成就条目原画为 7 条竖直排列（行距 132）；单条由左侧图标框与右侧底框组成。
ACHIEVEMENT_ITEM_ICON = (0, 0, 96, 96)
ACHIEVEMENT_ITEM_PANEL = (132, 0, 552, 96)
_ACHIEVEMENT_ITEM_CACHE: dict[tuple[str, int, int], pygame.Surface] = {}

# 关闭按钮悬停辉光的主色。
_CLOSE_HOVER = (110, 224, 177)


def _achievement_item_surface(part, size):
    key = (part, size[0], size[1])
    surface = _ACHIEVEMENT_ITEM_CACHE.get(key)
    if surface is None:
        source = load_image(ACHIEVEMENT_ITEM)
        entry = ACHIEVEMENT_ITEM_ICON if part == "icon" else ACHIEVEMENT_ITEM_PANEL
        piece = source.subsurface(pygame.Rect(entry)).copy()
        surface = pygame.transform.smoothscale(piece, (key[1], key[2]))
        _ACHIEVEMENT_ITEM_CACHE[key] = surface
    return surface


class ArchiveState(GameState):
    """在合成效果图的留白区域显示真实存档数据。"""

    music_scene = "cmdb"
    TAB_ORDER = ("skins", "collectibles", "achievements")
    TAB_RECTS: ClassVar = {
        "skins": pygame.Rect(777, 39, 100, 52),
        "collectibles": pygame.Rect(880, 39, 115, 52),
        "achievements": pygame.Rect(998, 39, 125, 52),
    }
    # 对齐底图右上角第三个窗口控制方块，避免露出被覆盖的原始关闭图标。
    CLOSE_RECT: ClassVar = pygame.Rect(1172, 58, 32, 32)
    # 电视机内常驻显示当前皮肤的小人；该区域同时是“戳一戳”隐藏成就的点击区。
    COMPUTER_PREVIEW_RECT: ClassVar = pygame.Rect(454, 393, 68, 112)
    # 藏品/成就页显示屏里的小人：常驻当前使用皮肤，与皮肤页电视机预览同位置同尺寸。
    SCREEN_PREVIEW_RECT: ClassVar = pygame.Rect(454, 393, 68, 112)
    SKIN_VIEWPORT: ClassVar = pygame.Rect(786, 110, 380, 505)
    COLLECTIBLE_GRID_RECT: ClassVar = pygame.Rect(791, 116, 370, 493)
    # 藏品界面各层在运行时窗口中的落位（design 2646x1489 × 1280/2646）。
    # 成就界面与藏品界面共用同一套窗口/显示屏/文案框/按钮落位。
    COLLECTION_GLOW_RECT: ClassVar = pygame.Rect(0, 7, 1253, 714)
    COLLECTION_WINDOW_RECT: ClassVar = pygame.Rect(671, 0, 609, 720)
    # 显示屏位于最底层：背景图的电视内屏是一块透明洞（design 723,752,605,358），
    # 洞外由背景图覆盖，洞里透出显示屏素材。
    DB_SCREEN_RECT: ClassVar = pygame.Rect(326, 347, 329, 206)
    COLLECTION_SELECTBOX_RECT: ClassVar = pygame.Rect(887, 58, 87, 31)
    COLLECTION_ZOOM_OUT_RECT: ClassVar = pygame.Rect(1095, 58, 31, 31)
    COLLECTION_ZOOM_IN_RECT: ClassVar = pygame.Rect(1133, 58, 31, 31)
    COLLECTION_CLOSE_RECT: ClassVar = pygame.Rect(1172, 58, 31, 31)
    COLLECTION_H_SLIDER_RECT: ClassVar = pygame.Rect(973, 633, 201, 19)
    COLLECTION_TEXTBOX_RECT: ClassVar = pygame.Rect(44, 587, 671, 86)
    # 竖直滑块上下的切换箭头：贴着滑轨 (SKIN_SCROLL_TRACK) 的上下两端。
    DB_SLIDER_UP_RECT: ClassVar = pygame.Rect(1184, 106, 19, 13)
    DB_SLIDER_DOWN_RECT: ClassVar = pygame.Rect(1184, 636, 19, 13)
    # 底部文案框内的文本块：整块相对文字框上下左右居中（design 194..565）。
    DB_TEXT_BLOCK_WIDTH: ClassVar = 371
    # 文案框内允许的最大文本块宽度：由框宽 671 减去左右引号与留白推得，
    # 保证引号向外伸展时仍落在文案框范围内（成就详情用它避免长句被截断）。
    DB_TEXT_BLOCK_WIDTH_MAX: ClassVar = 588
    DB_QUOTE_SIZE: ClassVar = (16, 12)
    # 左右引号分别贴在文本块左/右边界外侧的留白里。
    DB_QUOTE_LEFT_GAP: ClassVar = 20
    DB_QUOTE_RIGHT_GAP: ClassVar = 21
    # 网格 4 列 × 5 行；正式版 17 件主线藏品占用 17 格，余 3 格留空。
    COLLECTION_COLUMNS: ClassVar = 4
    COLLECTION_VISIBLE_ROWS: ClassVar = 5
    # 成就界面各层落位：与藏品界面同源（design 2646x1489 → 运行时 1280x720）。
    ACHIEVEMENT_SELECTBOX_RECT: ClassVar = pygame.Rect(992, 58, 87, 31)
    ACHIEVEMENT_LIST_RECT: ClassVar = pygame.Rect(791, 116, 370, 493)
    # 成就条目原画 684x888，7 条竖直排列（行距 132，条高 96）。
    # 裁剪区与成就底图的内区一致（底图四周 2px 边框），右缘 1159：
    # 必须容纳 ACHIEVEMENT_ROW_X + ACHIEVEMENT_PANEL_OFFSET + ACHIEVEMENT_PANEL_WIDTH。
    ACHIEVEMENT_VIEWPORT: ClassVar = pygame.Rect(793, 118, 366, 489)
    # 条目框整体（图标框 + 右侧条目框）向右偏移；名称/描述文案与未解锁问号
    # 都以此为水平基准，改这一个值即可整体左右平移。
    ACHIEVEMENT_ROW_X: ClassVar = 811
    ACHIEVEMENT_ROW_ORIGIN_Y: ClassVar = 120
    ACHIEVEMENT_ROW_STEP: ClassVar = 64
    ACHIEVEMENT_ICON_SIZE: ClassVar = 46
    ACHIEVEMENT_PANEL_OFFSET: ClassVar = 64
    ACHIEVEMENT_PANEL_WIDTH: ClassVar = 267
    ACHIEVEMENT_HEADER_HEIGHT: ClassVar = 30
    # “解锁感叹号”“未解锁问号”等比缩放后再各自收缩的像素数。
    ACHIEVEMENT_BANG_SHRINK: ClassVar = 2
    ACHIEVEMENT_ASK_SHRINK: ClassVar = 4
    # 未解锁问号相对条目框的水平偏移。
    ACHIEVEMENT_ASK_OFFSET_X: ClassVar = -83
    ACHIEVEMENT_DETAIL_RECT: ClassVar = pygame.Rect(44, 587, 671, 86)
    # 皮肤页右侧滑块的滑轨：顶部 136 为设定值，底部对齐视口下沿 (615)。
    # 藏品页与成就页的竖直滑块共用这条滑轨与交互。
    SKIN_SCROLL_TRACK: ClassVar = pygame.Rect(1169, 136, 34, 479)
    SKIN_FOLDERS: ClassVar = {"default": "0", "endgame": "A", "maid": "B", "be": "C"}
    # 各皮肤卡片预览贴图：（解锁态, 未解锁剪影）。
    SKIN_PREVIEW_ART: ClassVar = {
        "default": ("initial_unlock_skin.png", "locking.png"),
        "endgame": ("initial_unlock_skin1.png", "locking.png"),
        "maid": ("initial_unlock_skin2.png", "locking.png"),
        "be": ("initial_unlock_skin3.png", "initial_lock_skin3.png"),
    }
    # 个别皮肤卡片贴图的额外缩放（1.0 为铺满预览框），缩放时保持底边不动。
    SKIN_PREVIEW_SCALE: ClassVar = {"be": 0.4}

    def __init__(self, game, tab="skins", return_state=None):
        super().__init__(game)
        self.return_state = return_state
        self.active_tab = tab if tab in self.TAB_ORDER else "skins"
        self.skin_rects = {}
        self.collectible_rects = []
        self.achievement_rows = []
        self.selected_collectible = 0
        self.scroll_y = 0.0
        self.max_scroll = 0.0
        self.collectible_scroll_y = 0.0
        self.collectible_max_scroll = 0.0
        self.collectible_thumb_rect = pygame.Rect(0, 0, 0, 0)
        self.dragging_collectible_scroll = False
        self.collectible_drag_offset = 0
        self.achievement_thumb_rect = pygame.Rect(0, 0, 0, 0)
        self.dragging_achievement_scroll = False
        self.achievement_drag_offset = 0
        self.selected_achievement = None
        self.preview_fall_timer = 0.0
        self.skin_scroll_y = 0.0
        self.skin_max_scroll = 0.0
        self.skin_thumb_rect = pygame.Rect(0, 0, 0, 0)
        self.dragging_skin_scroll = False
        self.skin_drag_offset = 0

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or (
                    event.key == pygame.K_b and self.return_state is not None
                ):
                    self._back_to_menu()
                elif event.key in (pygame.K_1, pygame.K_KP1):
                    self.active_tab = "skins"
                elif event.key in (pygame.K_2, pygame.K_KP2):
                    self.active_tab = "collectibles"
                elif event.key in (pygame.K_3, pygame.K_KP3):
                    self.active_tab = "achievements"
                elif self.active_tab == "achievements":
                    if event.key in (pygame.K_UP, pygame.K_w, pygame.K_PAGEUP):
                        amount = 55 if event.key != pygame.K_PAGEUP else 460
                        self._set_scroll(self.scroll_y - amount)
                    elif event.key in (pygame.K_DOWN, pygame.K_s, pygame.K_PAGEDOWN):
                        amount = 55 if event.key != pygame.K_PAGEDOWN else 460
                        self._set_scroll(self.scroll_y + amount)
                    elif event.key == pygame.K_HOME:
                        self._set_scroll(0)
                    elif event.key == pygame.K_END:
                        self._set_scroll(self.max_scroll)
                elif self.active_tab == "collectibles":
                    if event.key in (pygame.K_UP, pygame.K_w, pygame.K_PAGEUP):
                        amount = 115 if event.key != pygame.K_PAGEUP else 460
                        self._set_collectible_scroll(
                            self.collectible_scroll_y - amount
                        )
                    elif event.key in (pygame.K_DOWN, pygame.K_s, pygame.K_PAGEDOWN):
                        amount = 115 if event.key != pygame.K_PAGEDOWN else 460
                        self._set_collectible_scroll(
                            self.collectible_scroll_y + amount
                        )
                continue

            if event.type == pygame.MOUSEWHEEL:
                if self.active_tab == "achievements":
                    self._set_scroll(self.scroll_y - event.y * 55)
                elif self.active_tab == "collectibles":
                    self._set_collectible_scroll(
                        self.collectible_scroll_y - event.y * 72
                    )
                elif self.active_tab == "skins":
                    self._set_skin_scroll(self.skin_scroll_y - event.y * 55)
                continue

            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.dragging_collectible_scroll = False
                self.dragging_achievement_scroll = False
                self.dragging_skin_scroll = False
                continue

            if event.type == pygame.MOUSEMOTION:
                if self.dragging_collectible_scroll:
                    self._drag_collectible_scroll(event.pos[1])
                    continue
                if self.dragging_achievement_scroll:
                    self._drag_achievement_scroll(event.pos[1])
                    continue
                if self.dragging_skin_scroll:
                    self._drag_skin_scroll(event.pos[1])
                    continue

            if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
                continue
            if self.CLOSE_RECT.collidepoint(event.pos):
                self._back_to_menu()
                return
            for tab, rect in self.TAB_RECTS.items():
                if rect.collidepoint(event.pos):
                    self.active_tab = tab
                    return
            if self.active_tab == "skins":
                if self.skin_thumb_rect.collidepoint(event.pos):
                    self.dragging_skin_scroll = True
                    self.skin_drag_offset = event.pos[1] - self.skin_thumb_rect.y
                    return
                if self.SKIN_SCROLL_TRACK.collidepoint(event.pos):
                    self._set_skin_scroll(
                        self._skin_track_ratio(event.pos[1]) * self.skin_max_scroll
                    )
                    return
                if self.COMPUTER_PREVIEW_RECT.collidepoint(event.pos):
                    # 时长取当前皮肤 die.gif 的一遍长度，播完即回 idle，不循环。
                    skin_id = self.game.shop_system.get_current_skin()
                    folder = self.SKIN_FOLDERS.get(skin_id, "0")
                    self.preview_fall_timer = gif_total_seconds(
                        f"images/player/skin/{folder}/die.gif"
                    )
                    self.game.achievement_system.unlock("poke_preview")
                    return
                self._handle_skin_click(event.pos)
            elif self.active_tab == "collectibles":
                if self.collectible_thumb_rect.collidepoint(event.pos):
                    self.dragging_collectible_scroll = True
                    self.collectible_drag_offset = (
                        event.pos[1] - self.collectible_thumb_rect.y
                    )
                    continue
                if self.SKIN_SCROLL_TRACK.collidepoint(event.pos):
                    self._set_collectible_scroll(
                        self._track_click_ratio(
                            event.pos[1], self.SKIN_SCROLL_TRACK
                        )
                        * self.collectible_max_scroll
                    )
                    continue
                for index, rect in self.collectible_rects:
                    if rect.collidepoint(event.pos):
                        self.selected_collectible = index
                        return
            elif self.active_tab == "achievements":
                if self.achievement_thumb_rect.collidepoint(event.pos):
                    self.dragging_achievement_scroll = True
                    self.achievement_drag_offset = (
                        event.pos[1] - self.achievement_thumb_rect.y
                    )
                    continue
                if self.SKIN_SCROLL_TRACK.collidepoint(event.pos):
                    self._set_scroll(
                        self._track_click_ratio(
                            event.pos[1], self.SKIN_SCROLL_TRACK
                        )
                        * self.max_scroll
                    )
                    continue
                for achievement_id, rect in self.achievement_rows:
                    if rect.collidepoint(event.pos):
                        self.selected_achievement = achievement_id
                        return

    def update(self, dt):
        self._set_scroll(self.scroll_y)
        self._set_collectible_scroll(self.collectible_scroll_y)
        self._set_skin_scroll(self.skin_scroll_y)
        self.preview_fall_timer = max(0.0, self.preview_fall_timer - dt)

    def draw(self, screen):
        if self.active_tab == "collectibles":
            # 藏品页使用 collectiondb 分层素材，自带窗口与关闭按钮。
            self._draw_collectibles(screen)
            return
        if self.active_tab == "achievements":
            # 成就页使用 achievementsdb 分层素材，自带窗口与关闭按钮。
            self._draw_achievements(screen)
            return
        draw_background(screen, SKINS_BG)
        self._draw_skins(screen)
        self._draw_close_button(screen, pygame.mouse.get_pos())

    def _draw_close_button(self, screen, mouse_position):
        """皮肤页关闭键：与藏品/成就页一致，直接贴美术素材叉掉贴图。"""

        self._draw_window_close(
            screen, mouse_position, SKINS_BTN_CLOSE, self.CLOSE_RECT
        )

    def _back_to_menu(self):
        if self.return_state is not None:
            self.game.change_state(self.return_state)
            return
        from states.main_menu_state import MainMenuState

        self.game.change_state(MainMenuState(self.game))

    def _draw_skins(self, screen):
        skins = self.game.shop_system.get_skins()
        current_skin = self.game.shop_system.get_current_skin()
        # 与成就页同序：先画电视小人，再叠光效（同一张素材），
        # 光效压住背景与小人，但随后被卡片与文案盖住。
        self._draw_computer_preview(screen, current_skin)
        draw_image(screen, ACHIEVEMENT_GLOW, self.COLLECTION_GLOW_RECT, smooth=True)
        # 卡片几何取自 db_expect 与背景图差集：370x238，间距 17，起点 (791,116)。
        card_width = 370
        card_height = 238
        card_gap = 17
        card_x = 791
        card_y0 = 116
        skin_count = len(skins)
        content_height = (
            skin_count * card_height + max(0, skin_count - 1) * card_gap
        )
        self.skin_max_scroll = max(0, content_height - self.SKIN_VIEWPORT.height)
        self._set_skin_scroll(self.skin_scroll_y)
        self.skin_rects = {}
        body = self.game.font_cache["body"]
        caption = self.game.font_cache["caption"]
        micro = self.game.font_cache["micro"]
        # 皮肤简介用更小字号，保证整句排在一行内。
        desc_font = self.game.font_cache.get("desc") or micro

        screen.set_clip(self.SKIN_VIEWPORT)
        for index, (skin_id, skin) in enumerate(skins.items()):
            rect = pygame.Rect(
                card_x,
                card_y0
                + index * (card_height + card_gap)
                - int(self.skin_scroll_y),
                card_width,
                card_height,
            )
            if rect.bottom <= self.SKIN_VIEWPORT.top:
                continue
            if rect.top >= self.SKIN_VIEWPORT.bottom:
                break
            self.skin_rects[skin_id] = rect
            unlocked = skin["unlocked"]
            is_current = skin_id == current_skin
            status = "使用中" if is_current else "已解锁" if unlocked else "未解锁"
            accent = (
                (232, 243, 237)
                if is_current
                else (105, 206, 171)
                if unlocked
                else (155, 170, 172)
            )

            base_asset = "back_base.png" if unlocked else "locking_back.png"
            draw_image(screen, f"images/skindb/{base_asset}", rect, smooth=True)

            if not unlocked:
                # 未解锁卡片的内层压一层半透明暗色，使整张卡片呈锁定感。
                inner = rect.inflate(-16, -16)
                shade = pygame.Surface(inner.size, pygame.SRCALPHA)
                shade.fill((0, 0, 0, 96))
                screen.blit(shade, inner.topleft)

            preview = pygame.Rect(rect.x + 26, rect.y + 23, 68, 179)
            unlock_art, lock_art = self.SKIN_PREVIEW_ART.get(
                skin_id, (None, "locking.png")
            )
            preview_scale = self.SKIN_PREVIEW_SCALE.get(skin_id, 1.0)
            if unlocked:
                if unlock_art is None:
                    self._draw_skin_preview(screen, skin_id, preview, unlocked)
                else:
                    self._draw_skin_preview_art(
                        screen, unlock_art, preview, preview_scale
                    )
                shadow_asset = "shadow.png"
            else:
                self._draw_skin_preview_art(screen, lock_art, preview, preview_scale)
                shadow_asset = "locking_shadow.png"
                lock_rect = pygame.Rect(rect.x + 154, rect.y + 20, 162, 197)
                draw_image(screen, "images/skindb/lock.png", lock_rect, smooth=True)

            # 小人脚下的投影。
            shadow = pygame.Rect((0, 0), (60, 21))
            shadow.midbottom = (preview.centerx + 3, preview.bottom + 8)
            draw_image(screen, f"images/skindb/{shadow_asset}", shadow, smooth=True)

            # 状态与说明文字只出现在已解锁卡片上；未解锁卡片仅由锁与暗色剪影表示。
            if unlocked:
                status_surface = fit_text(caption, status, 120, accent)
                screen.blit(
                    status_surface,
                    status_surface.get_rect(center=(rect.x + 303, rect.y + 43)),
                )

                info_x = rect.x + 129
                # 列宽需容纳 16px 简介整句（排版宽度约 204px），否则会折行。
                info_width = 212
                # 与视口求交，避免卡片滚出视口后文案仍悬浮在外。
                screen.set_clip(rect.clip(self.SKIN_VIEWPORT))
                screen.blit(
                    text_surface(body, skin["name"], (219, 237, 232), info_width),
                    (info_x, rect.y + 30),
                )
                description_lines = wrap_text(
                    desc_font, skin.get("description", ""), info_width
                )
                draw_text_lines(
                    screen,
                    description_lines[:3],
                    desc_font,
                    info_x,
                    rect.y + 96,
                    (152, 182, 184),
                    2,
                )
                screen.blit(
                    text_surface(micro, "点击切换外观", (152, 182, 184), info_width),
                    (info_x, rect.bottom - 55),
                )
                screen.set_clip(self.SKIN_VIEWPORT)

        screen.set_clip(None)
        # 右侧竖直滑块：可拖拽，控制皮肤卡片的上下滚动。
        self.skin_thumb_rect = self._draw_skin_scrollbar(screen)
        # 卡片下方的装饰横条，静态贴图。
        draw_image(
            screen,
            "images/skindb/slider2.png",
            pygame.Rect(973, 633, 201, 19),
            smooth=True,
        )

    def _draw_skin_scrollbar(self, screen):
        """按滚动位置绘制皮肤列表滑块，返回可拖拽的滑块区域。"""

        track = self.SKIN_SCROLL_TRACK
        thumb_height = max(1, round(track.width * 258 / 70))
        if self.skin_max_scroll <= 0:
            thumb_y = track.y
        else:
            travel = max(0, track.height - thumb_height)
            thumb_y = track.y + round(
                travel * (self.skin_scroll_y / self.skin_max_scroll)
            )
        thumb_rect = pygame.Rect(track.x, thumb_y, track.width, thumb_height)
        draw_image(screen, "images/skindb/slider.png", thumb_rect, smooth=True)
        return thumb_rect

    def _draw_computer_preview(self, screen, skin_id, rect=None):
        """电视机里常驻显示当前皮肤的小人，皮肤页与藏品页共用。"""

        rect = rect or self.COMPUTER_PREVIEW_RECT
        folder = self.SKIN_FOLDERS.get(skin_id, "0")
        # 点击电视里的小人时，所有皮肤统一播放一遍 die.gif（不循环）；静置时播放 idle.gif。
        animation = "die" if self.preview_fall_timer > 0 else "idle"
        path = f"images/player/skin/{folder}/{animation}.gif"
        elapsed = None
        if animation == "die":
            elapsed = gif_total_seconds(path) - self.preview_fall_timer
        try:
            draw_gif_frame(
                screen,
                path,
                rect,
                smooth=False,
                contain=True,
                align="midbottom",
                elapsed=elapsed,
            )
        except (FileNotFoundError, pygame.error, OSError):
            pygame.draw.rect(screen, (60, 70, 72), rect, 2)

    def _draw_skin_preview(self, screen, skin_id, rect, unlocked):
        folder = self.SKIN_FOLDERS.get(skin_id, "0")
        path = f"images/player/skin/{folder}/idle.gif"
        if not unlocked:
            return
        try:
            draw_gif_frame(
                screen,
                path,
                rect,
                smooth=False,
                contain=True,
                align="midbottom",
            )
        except (FileNotFoundError, pygame.error, OSError):
            pygame.draw.rect(screen, (60, 70, 72), rect, 2)

    def _draw_skin_preview_art(self, screen, name, rect, scale=1.0):
        """按人物实际内容等比缩放：高度铺满预览框、水平居中，避免被压成一条。

        `scale` 为额外缩放（皮肤卡片贴图同理，见 SKIN_PREVIEW_SCALE），缩放时
        以预览框底边为基准，让小人保持在同一条底线上。
        """

        image = load_image(f"images/skindb/{name}")
        content = image.subsurface(image.get_bounding_rect())
        fit = rect.height / content.get_height()
        size = (
            max(1, round(content.get_width() * fit * scale)),
            max(1, round(rect.height * scale)),
        )
        scaled = pygame.transform.smoothscale(content, size)
        screen.blit(scaled, scaled.get_rect(midbottom=rect.midbottom))

    def _handle_skin_click(self, position):
        for skin_id, rect in self.skin_rects.items():
            if not rect.collidepoint(position):
                continue
            skin = self.game.shop_system.get_skins()[skin_id]
            if skin["unlocked"]:
                if self.game.shop_system.set_current_skin(skin_id):
                    self.game.ui_manager.show_skin_notification(
                        skin["name"], "- 外观已更新 -"
                    )
                else:
                    self.game.ui_manager.show_skin_notification(
                        skin["name"], "- 已经在使用 -"
                    )
            return

    def _draw_collectibles(self, screen):
        ids = list(MAIN_COLLECTIBLE_IDS)
        # 最底层先画显示屏；背景图的电视内屏是透明洞，洞外由背景图盖住。
        self._draw_db_screen(screen, COLLECTION_SCREEN)
        # 背景组：底图 → 光效 → 窗口（窗口自带顶部标签栏与窗口框）。
        draw_background(screen, COLLECTION_BG)
        draw_image(screen, COLLECTION_GLOW, self.COLLECTION_GLOW_RECT, smooth=True)
        draw_image(screen, COLLECTION_WINDOW, self.COLLECTION_WINDOW_RECT, smooth=True)
        # 当前页标签高亮；右上角缩小/放大仅装饰，叉掉等同关闭。
        draw_image(
            screen,
            COLLECTION_SELECTBOX_ART,
            self.COLLECTION_SELECTBOX_RECT,
            smooth=True,
        )
        draw_image(
            screen,
            COLLECTION_BTN_ZOOM_OUT,
            self.COLLECTION_ZOOM_OUT_RECT,
            smooth=True,
        )
        draw_image(
            screen,
            COLLECTION_BTN_ZOOM_IN,
            self.COLLECTION_ZOOM_IN_RECT,
            smooth=True,
        )
        self._draw_window_close(
            screen,
            pygame.mouse.get_pos(),
            COLLECTION_BTN_CLOSE,
            self.COLLECTION_CLOSE_RECT,
        )

        grid = self.COLLECTIBLE_GRID_RECT
        inner = pygame.Rect(grid.x + 7, grid.y + 7, grid.width - 14, grid.height - 14)
        columns = self.COLLECTION_COLUMNS
        visible_rows = self.COLLECTION_VISIBLE_ROWS
        cell_w = inner.width / columns
        cell_h = inner.height / visible_rows
        rows = max(visible_rows, (len(ids) + columns - 1) // columns)
        content_height = rows * cell_h
        self.collectible_max_scroll = max(0, round(content_height - inner.height))
        self._set_collectible_scroll(self.collectible_scroll_y)

        draw_image(screen, COLLECTION_GRID_ART, grid, smooth=True)
        self.collectible_rects = []
        origin_y = inner.y - int(self.collectible_scroll_y)
        screen.set_clip(inner)
        for slot_index in range(rows * columns):
            row, column = divmod(slot_index, columns)
            cell = pygame.Rect(
                round(inner.x + column * cell_w),
                round(origin_y + row * cell_h),
                round(cell_w),
                round(cell_h),
            )
            if slot_index >= len(ids):
                continue
            index = slot_index
            item_id = ids[index]
            if cell.bottom > inner.top and cell.top < inner.bottom:
                self.collectible_rects.append((index, cell))
            # 选中高亮垫在藏品图标下方，避免素材中心遮住图标。
            if index == self.selected_collectible:
                selecting = pygame.Rect((0, 0), (107, 110))
                selecting.center = cell.center
                draw_image(screen, COLLECTION_SELECTING_ART, selecting, smooth=True)
            if self.game.is_item_collected(item_id):
                self._draw_collectible_icon(screen, item_id, cell)
            else:
                question = get_font(self.game.font_cache, "body").render(
                    "?", True, (102, 139, 143)
                )
                screen.blit(question, question.get_rect(center=cell.center))
        screen.set_clip(None)

        # 竖直滑块与皮肤页共用滑轨与交互；下方横条为静态装饰。
        self.collectible_thumb_rect = self._draw_db_scrollbar(
            screen,
            COLLECTION_V_SLIDER,
            self.collectible_scroll_y,
            self.collectible_max_scroll,
        )
        draw_image(
            screen, COLLECTION_H_SLIDER, self.COLLECTION_H_SLIDER_RECT, smooth=True
        )
        self._draw_db_slider_arrows(
            screen, COLLECTION_BTN_UP, COLLECTION_BTN_DOWN
        )

        item = COLLECTIBLE_BY_ID[ids[min(self.selected_collectible, len(ids) - 1)]]
        collected = self.game.is_item_collected(item["id"])
        self._draw_collection_display(screen, item, collected)

    def _draw_window_close(self, screen, mouse_position, asset, rect):
        """右上角叉掉按钮：与皮肤页关闭键同坐标，悬停时叠一层辉光。"""

        if rect.collidepoint(mouse_position):
            glow = pygame.Surface(
                (rect.width + 16, rect.height + 16), pygame.SRCALPHA
            )
            pygame.draw.rect(
                glow, (*_CLOSE_HOVER, 80), glow.get_rect(), border_radius=6
            )
            screen.blit(glow, (rect.x - 8, rect.y - 8))
        draw_image(screen, asset, rect, smooth=True)

    def _draw_db_scrollbar(self, screen, asset, scroll_pos, max_scroll):
        """数据库页竖直滑块：滑轨、滑块尺寸与定位方式完全对齐皮肤页。"""

        track = self.SKIN_SCROLL_TRACK
        thumb_height = max(1, round(track.width * 258 / 70))
        if max_scroll <= 0:
            thumb_y = track.y
        else:
            travel = max(0, track.height - thumb_height)
            thumb_y = track.y + round(travel * (scroll_pos / max_scroll))
        thumb_rect = pygame.Rect(track.x, thumb_y, track.width, thumb_height)
        draw_image(screen, asset, thumb_rect, smooth=True)
        return thumb_rect

    def _draw_db_slider_arrows(self, screen, up_asset, down_asset):
        """竖直滑轨上下两端的切换箭头。"""

        draw_image(screen, up_asset, self.DB_SLIDER_UP_RECT, smooth=True)
        draw_image(screen, down_asset, self.DB_SLIDER_DOWN_RECT, smooth=True)

    def _draw_db_screen(self, screen, asset):
        """在最底层画显示屏：背景图的电视内屏是透明洞，洞外由背景图覆盖。"""

        draw_image(screen, asset, self.DB_SCREEN_RECT, smooth=True)

    def _draw_db_textbox(
        self,
        screen,
        box,
        quote_left,
        quote_right,
        title,
        description,
        title_color,
        desc_color=(148, 169, 170),
        desc_font=None,
        block_width=None,
    ):
        """底部文案框：名称 + 引号包裹的文案。

        名称行与文案行都以文字框中心线对齐（上下左右居中），
        左右引号贴在文字块左右外侧的留白里；文案过长时文本块可加宽，
        引号随之向两侧伸展，但始终不超出文案框范围。
        """

        name_font = get_font(self.game.font_cache, "caption")
        desc_font = desc_font or get_font(self.game.font_cache, "micro")
        quote_w, quote_h = self.DB_QUOTE_SIZE
        max_block = 2 * (
            box.width // 2
            - quote_w
            - max(self.DB_QUOTE_LEFT_GAP, self.DB_QUOTE_RIGHT_GAP)
            - 4
        )
        block_width = min(block_width or self.DB_TEXT_BLOCK_WIDTH, max_block)
        name_surface = fit_text(name_font, title, block_width, title_color)
        line_surfaces = [
            fit_text(desc_font, line, block_width, desc_color)
            for line in wrap_text(desc_font, description, block_width)[:2]
        ]
        name_height = name_font.get_linesize()
        desc_step = desc_font.get_linesize() + 1
        content_height = name_height + len(line_surfaces) * desc_step
        top = box.centery - content_height // 2

        screen.blit(name_surface, name_surface.get_rect(midtop=(box.centerx, top)))
        y = top + name_height
        for surface in line_surfaces:
            screen.blit(surface, surface.get_rect(midtop=(box.centerx, y)))
            y += desc_step

        content_width = max(
            [name_surface.get_width()] + [s.get_width() for s in line_surfaces]
        )
        content_left = box.centerx - content_width // 2
        # 左引号与名称行顶对齐，右引号与文案末行顶对齐。
        draw_image(
            screen,
            quote_left,
            pygame.Rect(
                content_left - self.DB_QUOTE_LEFT_GAP - quote_w,
                top + 3,
                quote_w,
                quote_h,
            ),
            smooth=True,
        )
        if line_surfaces:
            draw_image(
                screen,
                quote_right,
                pygame.Rect(
                    content_left + content_width + self.DB_QUOTE_RIGHT_GAP,
                    top + name_height + (len(line_surfaces) - 1) * desc_step + 2,
                    quote_w,
                    quote_h,
                ),
                smooth=True,
            )

    def _draw_collection_display(self, screen, item, collected):
        """底部文案框；电视里贴当前选中藏品的贴图（未收集则电视留空）。"""

        if collected:
            self._draw_collectible_icon(
                screen, item["id"], self.SCREEN_PREVIEW_RECT, padding=6
            )

        box = self.COLLECTION_TEXTBOX_RECT
        draw_image(screen, COLLECTION_TEXTBOX, box, smooth=True)
        self._draw_db_textbox(
            screen,
            box,
            COLLECTION_QUOTE_LEFT,
            COLLECTION_QUOTE_RIGHT,
            item["name"] if collected else "未解锁记录",
            item["description"] if collected else "未收集记录：完成对应关卡后解锁。",
            (224, 239, 233) if collected else (148, 170, 170),
            # 藏品文案偏长：用更小字号，并放宽文本块，让左右引号可各自向外伸展，
            # 上限由文案框宽度决定（引号不会超出文案框）。
            desc_font=get_font(self.game.font_cache, "desc_small"),
            block_width=self.DB_TEXT_BLOCK_WIDTH_MAX,
        )

    def _draw_collectible_icon(self, screen, item_id, rect, padding=22):
        """按原图宽高比缩放并居中绘制藏品图标，避免横纵拉伸变形。"""

        try:
            image = load_image(f"images/collectibles/{item_id}.png")
        except (FileNotFoundError, pygame.error, OSError):
            return
        available = rect.inflate(-padding, -padding)
        scale = min(
            available.width / image.get_width(),
            available.height / image.get_height(),
        )
        size = (
            max(1, round(image.get_width() * scale)),
            max(1, round(image.get_height() * scale)),
        )
        target = pygame.Rect((0, 0), size)
        target.center = rect.center
        draw_image(screen, f"images/collectibles/{item_id}.png", target, smooth=True)

    def _collectible_name(self, item_id):
        return COLLECTIBLE_BY_ID[item_id]["name"]

    def _draw_achievements(self, screen):
        # 最底层先画显示屏；背景图的电视内屏是透明洞，洞外由背景图盖住。
        self._draw_db_screen(screen, ACHIEVEMENT_SCREEN)
        # 背景组：底图 → 小人 → 光效 → 窗口（窗口自带顶部标签栏与窗口框）。
        # 光效压在背景、电视显示屏与小人之上，但仍被窗口与文案盖住。
        draw_background(screen, ACHIEVEMENT_BG)
        self._draw_computer_preview(
            screen,
            self.game.shop_system.get_current_skin(),
            self.SCREEN_PREVIEW_RECT,
        )
        draw_image(screen, ACHIEVEMENT_GLOW, self.COLLECTION_GLOW_RECT, smooth=True)
        draw_image(screen, ACHIEVEMENT_WINDOW, self.COLLECTION_WINDOW_RECT, smooth=True)
        # 当前页标签高亮；右上角缩小/放大仅装饰，叉掉等同关闭。
        draw_image(
            screen,
            ACHIEVEMENT_SELECTBOX,
            self.ACHIEVEMENT_SELECTBOX_RECT,
            smooth=True,
        )
        draw_image(
            screen,
            ACHIEVEMENT_BTN_ZOOM_OUT,
            self.COLLECTION_ZOOM_OUT_RECT,
            smooth=True,
        )
        draw_image(
            screen,
            ACHIEVEMENT_BTN_ZOOM_IN,
            self.COLLECTION_ZOOM_IN_RECT,
            smooth=True,
        )
        self._draw_window_close(
            screen,
            pygame.mouse.get_pos(),
            ACHIEVEMENT_BTN_CLOSE,
            self.COLLECTION_CLOSE_RECT,
        )

        rows = self._achievement_items()
        viewport = self.ACHIEVEMENT_VIEWPORT
        header_height = self.ACHIEVEMENT_HEADER_HEIGHT
        icon_size = self.ACHIEVEMENT_ICON_SIZE
        panel_offset = self.ACHIEVEMENT_PANEL_OFFSET
        panel_width = self.ACHIEVEMENT_PANEL_WIDTH
        row_step = self.ACHIEVEMENT_ROW_STEP
        content_height = sum(
            header_height if kind == "header" else row_step for kind, _ in rows
        )
        self.max_scroll = max(0, content_height - viewport.height)
        self._set_scroll(self.scroll_y)
        self.achievement_rows = []

        draw_image(screen, ACHIEVEMENT_LIST_BG, self.ACHIEVEMENT_LIST_RECT, smooth=True)

        micro = get_font(self.game.font_cache, "micro")
        mouse_position = pygame.mouse.get_pos()
        hovered_achievement = None
        content_y = self.ACHIEVEMENT_ROW_ORIGIN_Y - int(self.scroll_y)
        screen.set_clip(viewport)
        for kind, payload in rows:
            if kind == "header":
                if content_y + header_height >= viewport.top and content_y <= viewport.bottom:
                    label = fit_text(
                        micro, payload, viewport.width - 16, (174, 220, 204)
                    )
                    screen.blit(label, (viewport.x + 6, content_y + 4))
                    pygame.draw.line(
                        screen,
                        (76, 137, 129),
                        (viewport.x + 6, content_y + header_height - 6),
                        (viewport.right - 6, content_y + header_height - 6),
                        1,
                    )
                content_y += header_height
                continue

            achievement_id, achievement = payload
            row_x = self.ACHIEVEMENT_ROW_X
            icon_rect = pygame.Rect(row_x, content_y, icon_size, icon_size)
            frame_rect = pygame.Rect(
                row_x + panel_offset, content_y, panel_width, icon_size
            )
            content_y += row_step
            self.achievement_rows.append((achievement_id, frame_rect))
            if frame_rect.bottom < viewport.top or frame_rect.top > viewport.bottom:
                continue
            completed = achievement["completed"]
            hovered = frame_rect.collidepoint(mouse_position)
            if hovered:
                hovered_achievement = achievement_id

            screen.blit(_achievement_item_surface("icon", icon_rect.size), icon_rect)
            screen.blit(_achievement_item_surface("panel", frame_rect.size), frame_rect)

            if completed:
                # 已解锁：图标框里放“解锁感叹号”，名称与描述写入右侧条目框。
                self._draw_contained(
                    screen,
                    ACHIEVEMENT_UNLOCK_BANG,
                    icon_rect,
                    shrink=self.ACHIEVEMENT_BANG_SHRINK,
                )
                text_x = frame_rect.x + 14
                text_width = frame_rect.right - text_x - 12
                screen.blit(
                    fit_text(
                        micro, achievement["name"], text_width, (220, 239, 232)
                    ),
                    (text_x, frame_rect.y + round(icon_size * 0.16)),
                )
                screen.blit(
                    fit_text(
                        micro,
                        achievement["description"],
                        text_width,
                        (113, 150, 152),
                    ),
                    (text_x, frame_rect.y + round(icon_size * 0.56)),
                )
            else:
                # 未解锁：条目框用问号占位，不暴露名称与描述。
                self._draw_contained(
                    screen,
                    ACHIEVEMENT_LOCK_ASK,
                    frame_rect.move(self.ACHIEVEMENT_ASK_OFFSET_X, 0),
                    scale=0.9,
                    shrink=self.ACHIEVEMENT_ASK_SHRINK,
                )

            if hovered or achievement_id == self.selected_achievement:
                pygame.draw.rect(
                    screen,
                    (150, 214, 199),
                    frame_rect.inflate(2, 2),
                    2,
                    border_radius=3,
                )
        screen.set_clip(None)

        # 竖直滑块与皮肤页共用滑轨与交互；下方横条为静态装饰。
        self.achievement_thumb_rect = self._draw_db_scrollbar(
            screen, ACHIEVEMENT_V_SLIDER, self.scroll_y, self.max_scroll
        )
        draw_image(
            screen, ACHIEVEMENT_H_SLIDER, self.COLLECTION_H_SLIDER_RECT, smooth=True
        )
        self._draw_db_slider_arrows(
            screen, ACHIEVEMENT_BTN_UP, ACHIEVEMENT_BTN_DOWN
        )

        detail_id = hovered_achievement or self.selected_achievement
        self._draw_achievement_detail(screen, detail_id)

    def _draw_contained(self, screen, asset, rect, scale=1.0, shrink=0):
        """按素材原始宽高比等比缩放到目标区域内并居中，最后整体再收缩 shrink 像素。"""

        image = load_image(asset)
        fit = (
            min(rect.width / image.get_width(), rect.height / image.get_height())
            * scale
        )
        size = (
            max(1, round(image.get_width() * fit) - shrink),
            max(1, round(image.get_height() * fit) - shrink),
        )
        target = pygame.Rect((0, 0), size)
        target.center = rect.center
        draw_image(screen, asset, target, smooth=True)
        return target

    def _draw_achievement_detail(self, screen, achievement_id):
        """在左下文案框用原画底框与引号展示悬停或选中成就的完整文案。"""

        box = self.ACHIEVEMENT_DETAIL_RECT
        draw_image(screen, ACHIEVEMENT_TEXTBOX, box, smooth=True)
        if not achievement_id:
            micro = get_font(self.game.font_cache, "micro")
            hint = fit_text(
                micro,
                "将鼠标移到成就条目上查看详情",
                box.width - 120,
                (150, 184, 184),
            )
            screen.blit(hint, hint.get_rect(center=(box.centerx, box.centery)))
            return

        achievement = self.game.achievement_system.get_all_achievements()[achievement_id]
        completed = achievement["completed"]
        self._draw_db_textbox(
            screen,
            box,
            ACHIEVEMENT_QUOTE_LEFT,
            ACHIEVEMENT_QUOTE_RIGHT,
            achievement["name"] if completed else "未解锁成就",
            achievement["description"] if completed else "达成条件暂未记录。",
            (224, 239, 233) if completed else (148, 170, 170),
            # 成就名较长，放宽文本块让整句显示、引号向两侧伸展（不超出文案框）。
            block_width=self.DB_TEXT_BLOCK_WIDTH_MAX,
        )

    def _achievement_items(self):
        achievements = self.game.achievement_system.get_all_achievements()
        rows = []
        category_order = ("无尽模式", "受伤", "其它")
        for category in category_order:
            category_items = [
                (key, value)
                for key, value in achievements.items()
                if key != "all_achievements" and value.get("category") == category
            ]
            if category == "其它" and "all_achievements" in achievements:
                category_items.append(
                    ("all_achievements", achievements["all_achievements"])
                )
            if category_items:
                rows.append(("header", category))
                rows.extend(("item", item) for item in category_items)
        return rows

    def _track_click_ratio(self, mouse_y, track):
        return max(0.0, min(1.0, (mouse_y - track.top) / max(1, track.height)))

    def _drag_scroll_ratio(self, mouse_y, thumb_rect, drag_offset, track):
        if thumb_rect.height <= 0:
            return 0.0
        travel = track.height - thumb_rect.height
        thumb_y = max(
            track.top,
            min(track.bottom - thumb_rect.height, mouse_y - drag_offset),
        )
        return (thumb_y - track.top) / max(1, travel)

    def _set_scroll(self, value):
        self.scroll_y = max(0.0, min(float(value), float(self.max_scroll)))

    def _set_collectible_scroll(self, value):
        self.collectible_scroll_y = max(
            0.0,
            min(float(value), float(self.collectible_max_scroll)),
        )

    def _set_skin_scroll(self, value):
        self.skin_scroll_y = max(0.0, min(float(value), float(self.skin_max_scroll)))

    def _skin_track_ratio(self, mouse_y):
        track = self.SKIN_SCROLL_TRACK
        return max(0.0, min(1.0, (mouse_y - track.top) / max(1, track.height)))

    def _drag_skin_scroll(self, mouse_y):
        if self.skin_max_scroll <= 0 or self.skin_thumb_rect.height <= 0:
            return
        track = self.SKIN_SCROLL_TRACK
        travel = max(1, track.height - self.skin_thumb_rect.height)
        thumb_y = max(
            track.top,
            min(track.bottom - self.skin_thumb_rect.height, mouse_y - self.skin_drag_offset),
        )
        self._set_skin_scroll(
            (thumb_y - track.top) / travel * self.skin_max_scroll
        )

    def _drag_collectible_scroll(self, mouse_y):
        if self.collectible_max_scroll <= 0:
            return
        ratio = self._drag_scroll_ratio(
            mouse_y,
            self.collectible_thumb_rect,
            self.collectible_drag_offset,
            self.SKIN_SCROLL_TRACK,
        )
        self._set_collectible_scroll(ratio * self.collectible_max_scroll)

    def _drag_achievement_scroll(self, mouse_y):
        if self.max_scroll <= 0:
            return
        ratio = self._drag_scroll_ratio(
            mouse_y,
            self.achievement_thumb_rect,
            self.achievement_drag_offset,
            self.SKIN_SCROLL_TRACK,
        )
        self._set_scroll(ratio * self.max_scroll)
