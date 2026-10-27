"""追忆/关卡选择状态。"""

from __future__ import annotations

import math
from typing import ClassVar

import pygame

from config import MAIN_LEVEL_IDS, TUTORIAL_LEVEL_ID
from levels.level_data import LEVEL_COLLECTIBLE_IDS, LEVEL_TITLES, level_operation_code
from states.game_state import GameState
from utils.ui_art import draw_background
from utils.ui_theme import UI_COLORS, draw_button, draw_panel, fit_text, get_font


class LevelSelectState(GameState):
    """在追忆节点图上选择关卡，开始动作由独立按钮或 Enter 触发。"""

    # PSD 原稿为 1920x1080，运行时按 2/3 缩放到 1280x720。
    # 这里记录存档-名字图层的外框，用于点击命中和选中光效。
    NODE_RECTS = (
        pygame.Rect(105, 201, 219, 62),
        pygame.Rect(163, 321, 219, 62),
        pygame.Rect(139, 433, 219, 62),
        pygame.Rect(91, 547, 219, 62),
        pygame.Rect(953, 207, 219, 62),
        pygame.Rect(918, 344, 219, 62),
        pygame.Rect(881, 451, 219, 62),
        pygame.Rect(923, 568, 219, 62),
    )

    # 节点外框包含顶部窗口栏；文字必须落在里面的浅色内容窗中。
    NODE_CONTENT_RECTS = (
        pygame.Rect(113, 222, 203, 31),
        pygame.Rect(171, 343, 203, 31),
        pygame.Rect(147, 455, 203, 31),
        pygame.Rect(99, 569, 203, 31),
        pygame.Rect(961, 228, 203, 31),
        pygame.Rect(926, 365, 203, 31),
        pygame.Rect(889, 472, 203, 31),
        pygame.Rect(931, 589, 203, 31),
    )

    # 无尽模式没有固定的 PSD 节点，由代码使用同一套窗口风格绘制。
    SPECIAL_NODE_RECTS: ClassVar = {
        "s": pygame.Rect(28, 636, 170, 46),
    }

    def __init__(self, game, return_state=None):
        super().__init__(game)
        # 从关卡内暂停/设置进入时携带来源状态：返回键回到该关卡，而不是主菜单。
        self.return_state = return_state
        self.level_ids = [
            level_id
            for level_id in (TUTORIAL_LEVEL_ID, *MAIN_LEVEL_IDS)
            if game.level_progress.get(level_id, 0) > 0
        ]
        self.page = 0
        self.selected_index = 0
        self.selection_time = 0.0
        self.node_rects = []

        self.back_rect = pygame.Rect(32, 28, 88, 40)
        # 中间屏幕的可视区域（对齐 reminiscence.png 里屏幕的空白内区）。
        self.monitor_rect = pygame.Rect(428, 230, 396, 300)
        self.start_rect = pygame.Rect(540, 406, 180, 50)
        self.page_prev_rect = pygame.Rect(1050, 658, 40, 32)
        self.page_next_rect = pygame.Rect(1138, 658, 40, 32)

    @property
    def visible_ids(self):
        start = self.page * len(self.NODE_RECTS)
        return self.level_ids[start : start + len(self.NODE_RECTS)]

    def _visible_nodes(self):
        nodes = [
            {
                "kind": "level",
                "level_id": level_id,
                "rect": self.NODE_RECTS[index],
                "content_rect": self.NODE_CONTENT_RECTS[index],
            }
            for index, level_id in enumerate(self.visible_ids)
        ]
        nodes.extend(
            {
                "kind": kind,
                "level_id": None,
                "rect": rect,
                "content_rect": rect,
            }
            for kind, rect in self.SPECIAL_NODE_RECTS.items()
        )
        return nodes

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                    self._back()
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    self._change_page(-1)
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    self._change_page(1)
                elif event.key in (pygame.K_UP, pygame.K_w):
                    self._move_selection(-1)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self._move_selection(1)
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self._start_selected()
                continue

            if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
                continue

            if self.back_rect.collidepoint(event.pos):
                self._back()
                return
            if self.page_prev_rect.collidepoint(event.pos):
                self._change_page(-1)
                return
            if self.page_next_rect.collidepoint(event.pos):
                self._change_page(1)
                return
            if self.start_rect.collidepoint(event.pos):
                self._start_selected()
                return

            for index, node in enumerate(self.node_rects):
                if node["rect"].collidepoint(event.pos):
                    # 节点点击只改变选中状态，真正开始由开始按钮或 Enter 完成。
                    self.selected_index = index
                    return

    def update(self, dt):
        self.selection_time += dt

    def _max_page(self):
        return max(0, (len(self.level_ids) - 1) // len(self.NODE_RECTS))

    def _change_page(self, amount):
        self.page = max(0, min(self._max_page(), self.page + amount))
        self.selected_index = 0

    def _move_selection(self, amount):
        nodes = self._visible_nodes()
        if not nodes:
            self.selected_index = 0
            return
        self.selected_index = (self.selected_index + amount) % len(nodes)

    def _selected_node(self):
        nodes = self._visible_nodes()
        if not nodes:
            return {
                "kind": "s",
                "level_id": None,
                "rect": self.SPECIAL_NODE_RECTS["s"],
            }
        return nodes[min(self.selected_index, len(nodes) - 1)]

    @staticmethod
    def _node_label(node):
        if node["kind"] == "s":
            return "S"
        level_id = node["level_id"]
        return f"“{LEVEL_TITLES[level_id]}”"

    def _start_selected(self):
        node = self._selected_node()
        if node["kind"] == "s":
            from states.endless_state import EndlessState

            self.game.change_state(EndlessState(self.game))
            return
        from states.play_state import PlayState

        self.game.change_state(PlayState(self.game, node["level_id"]))

    def _back(self):
        if self.return_state is not None:
            if hasattr(self.return_state, "paused"):
                self.return_state.paused = False
            self.game.change_state(self.return_state)
            return
        from states.main_menu_state import MainMenuState

        self.game.change_state(MainMenuState(self.game))

    def draw(self, screen):
        draw_background(screen, "images/ui/reminiscence.png")

        self.node_rects = self._visible_nodes()
        for index, node in enumerate(self.node_rects):
            selected = index == self.selected_index
            if selected:
                self._draw_selection_glow(screen, node["rect"])
            if node["kind"] == "s":
                self._draw_special_node(screen, node)
            else:
                self._draw_node_label(screen, node)

        self._draw_monitor(screen, self._selected_node())
        self._draw_navigation(screen)

    def _draw_node_label(self, screen, node):
        font = get_font(self.game.font_cache, "body")
        content_rect = node["content_rect"]
        label = fit_text(font, self._node_label(node), content_rect.width - 16, (18, 39, 45))
        screen.blit(label, label.get_rect(center=content_rect.center))

    def _draw_special_node(self, screen, node):
        rect = node["rect"]
        draw_panel(
            screen,
            rect,
            fill=(186, 211, 207),
            border=(16, 40, 46),
            radius=3,
            shadow=False,
        )
        pygame.draw.line(screen, (16, 40, 46), (rect.x + 9, rect.y + 12), (rect.right - 9, rect.y + 12), 1)
        for offset in (0, 7, 14):
            pygame.draw.rect(screen, (16, 40, 46), (rect.right - 27 + offset, rect.y + 5, 4, 4))
        font = get_font(self.game.font_cache, "body")
        label = fit_text(font, self._node_label(node), rect.width - 18, (18, 39, 45))
        screen.blit(label, label.get_rect(center=(rect.centerx, rect.y + 30)))

    def _draw_selection_glow(self, screen, rect):
        pulse = (math.sin(self.selection_time * 3.2) + 1.0) * 0.5
        glow_rect = rect.inflate(18, 18)
        glow = pygame.Surface(glow_rect.size, pygame.SRCALPHA)
        for inset, base_alpha in ((0, 34), (5, 62), (10, 108)):
            outline = glow.get_rect().inflate(-inset * 2, -inset * 2)
            alpha = min(180, int(base_alpha + pulse * 24))
            pygame.draw.rect(glow, (*UI_COLORS["accent"], alpha), outline, 2, border_radius=5)
        screen.blit(glow, glow_rect.topleft)

    def _draw_monitor(self, screen, node):
        body = get_font(self.game.font_cache, "body")
        caption = get_font(self.game.font_cache, "caption")

        if node["kind"] == "level":
            level_id = node["level_id"]
            title_text = f"“{LEVEL_TITLES[level_id]}”"
            operation_text = level_operation_code(level_id)
            stars = self.game.level_progress.get(level_id, 0)
            record_text = f"记录：{'★' * stars}{'☆' * (3 - stars)}"
            item_id = LEVEL_COLLECTIBLE_IDS.get(level_id)
            item_state = "已收集" if item_id and self.game.is_item_collected(item_id) else "未收集"
            item_text = f"藏品：{item_state}"
        elif node["kind"] == "s":
            title_text = "S级挑战"
            operation_text = "OPERATION ENDLESS"
            record_text = "模式：无尽挑战"
            item_text = "藏品：特殊关卡"

        # 文字与开始按钮作为一个整体，在中间屏幕上左右、上下居中。
        rows = (
            (fit_text(caption, operation_text, 330, (126, 198, 177)), 8),
            (fit_text(body, title_text, 330, (206, 224, 218)), 12),
            (fit_text(caption, record_text, 300, (166, 192, 192)), 8),
            (fit_text(caption, item_text, 300, (166, 192, 192)), 36),
        )
        content_height = sum(row.get_height() + gap for row, gap in rows) + 50
        y = self.monitor_rect.centery - content_height // 2
        for row, gap in rows:
            screen.blit(
                row, row.get_rect(midtop=(self.monitor_rect.centerx, y))
            )
            y += row.get_height() + gap

        self.start_rect.size = (180, 50)
        self.start_rect.midtop = (self.monitor_rect.centerx, y)
        draw_button(
            screen,
            self.start_rect,
            "开始",
            get_font(self.game.font_cache, "button"),
            variant="primary",
        )

    def _draw_navigation(self, screen):
        button_font = get_font(self.game.font_cache, "button")
        micro_font = get_font(self.game.font_cache, "micro")
        draw_button(screen, self.back_rect, "返回", button_font, variant="secondary")

        draw_panel(
            screen,
            pygame.Rect(806, 658, 232, 32),
            fill=(12, 34, 42),
            border=(142, 203, 196),
            radius=7,
            shadow=False,
        )
        guide = fit_text(micro_font, "↑↓选择  ←→翻页", 216, (216, 239, 232))
        screen.blit(guide, guide.get_rect(center=(922, 674)))

        draw_button(
            screen,
            self.page_prev_rect,
            "‹",
            button_font,
            variant="secondary",
            enabled=self.page > 0,
        )
        draw_panel(
            screen,
            pygame.Rect(1094, 658, 40, 32),
            fill=(12, 34, 42),
            border=(142, 203, 196),
            radius=7,
            shadow=False,
        )
        page_label = f"{self.page + 1}/{self._max_page() + 1}"
        page_surface = fit_text(micro_font, page_label, 34, (216, 239, 232))
        screen.blit(page_surface, page_surface.get_rect(center=(1114, 674)))
        draw_button(
            screen,
            self.page_next_rect,
            "›",
            button_font,
            variant="secondary",
            enabled=self.page < self._max_page(),
        )
