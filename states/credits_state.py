"""主线完成后可查看的制作名单。"""

from __future__ import annotations

from typing import ClassVar

import pygame

from config import SCREEN_HEIGHT, SCREEN_WIDTH
from states.game_state import GameState
from utils.ui_art import draw_background
from utils.ui_theme import UI_COLORS, draw_button, fit_text, get_font, wrap_text

CREDIT_SECTIONS = (
    ("出品", "鸿门宴工作室"),
    ("制作人", "上班就是死了"),
    ("游戏策划", "上班就是死了"),
    ("关卡设计", "_Yoriko、上班就是死了、Qin雪伊_"),
    ("程序草案", "白灵咕咕子"),
    ("程序原案", "楚如非LxNoiR"),
    ("程序开发", "楚如非LxNoiR、邶柒EvATive7"),
    ("角色美术", "紧急峥嵘战功、查瑟斯、苍迟迟迟迟迟迟迟迟迟"),
    ("场景美术", "_Yoriko、苍迟迟迟迟迟迟迟迟迟"),
    ("UI设计", "_Yoriko、苍迟迟迟迟迟迟迟迟迟"),
    ("文案", "上班就是死了"),
    ("藏品设计", "上班就是死了、紧急峥嵘战功"),
    ("pv", "小句、上班就是死了"),
    ("音乐来源", "塞壬唱片-MSR、Falcom Sound Team jdk"),
    ("测试", "Lycoris、白灵咕咕子、维云斯"),
    (
        "参与录制",
        (
            "重生之冰、Disillusion号角鸽、E某人QAQ、剑圣Kensei、"
            "金乌___、进修小超人、绝命笋干、里雪りあ、MR流星飞、"
            "绵阳怪兽、欧的堵、SWEEP分遣队、time_x_x_、血狼破军、"
            "萧然Q、有毒的粽子、子龙浑身都是肾"
        ),
    ),
    (
        "特别感谢",
        (
            "鸾风风风风、陌念秋、维云斯舰礼组、不愿署名的神秘赞助团队、"
            "不明六字神秘人、给予我们帮助的朋友们"
        ),
    ),
    # 单句脚注：整行居中展示，不参与两栏排布。
    "我们对以各种形式参与合作、予以支持的各位，表示充分理解与诚挚感谢。",
)


class CreditsState(GameState):
    """滚动显示版本 8 文档中的完整制作名单。"""

    BACK_RECT: ClassVar = pygame.Rect(36, 28, 104, 42)
    VIEWPORT: ClassVar = pygame.Rect(248, 132, 784, 520)

    def __init__(self, game):
        super().__init__(game)
        self.scroll_y = 0.0
        self.max_scroll = 0.0

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                    self._back()
                elif event.key in (pygame.K_UP, pygame.K_w, pygame.K_PAGEUP):
                    self._scroll(-80 if event.key != pygame.K_PAGEUP else -420)
                elif event.key in (pygame.K_DOWN, pygame.K_s, pygame.K_PAGEDOWN):
                    self._scroll(80 if event.key != pygame.K_PAGEDOWN else 420)
                elif event.key == pygame.K_HOME:
                    self.scroll_y = 0.0
                elif event.key == pygame.K_END:
                    self.scroll_y = self.max_scroll
            elif event.type == pygame.MOUSEWHEEL:
                self._scroll(-event.y * 70)
            elif (
                event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and self.BACK_RECT.collidepoint(event.pos)
            ):
                self._back()

    def update(self, dt):
        return None

    def draw(self, screen):
        background = (
            "images/ui/main_menu_he.png"
            if any(ending.startswith("HE") for ending in self.game.ending_history)
            else "images/ui/main_menu_default.png"
        )
        draw_background(screen, background)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((4, 12, 17, 228))
        screen.blit(overlay, (0, 0))
        draw_button(
            screen,
            self.BACK_RECT,
            "返回",
            get_font(self.game.font_cache, "caption"),
            "secondary",
        )
        title = fit_text(
            get_font(self.game.font_cache, "title"),
            "制作名单",
            SCREEN_WIDTH - 240,
            UI_COLORS["text"],
        )
        screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 72)))

        body = get_font(self.game.font_cache, "body")
        caption = get_font(self.game.font_cache, "caption")
        line_height = caption.get_linesize() + 6
        y = self.VIEWPORT.top - int(self.scroll_y)
        screen.set_clip(self.VIEWPORT)
        for entry in CREDIT_SECTIONS:
            if isinstance(entry, str):
                lines = wrap_text(caption, entry, self.VIEWPORT.width - 48)
                for index, line in enumerate(lines):
                    surface = fit_text(
                        caption, line, self.VIEWPORT.width - 48, UI_COLORS["text"]
                    )
                    screen.blit(
                        surface,
                        surface.get_rect(
                            centerx=self.VIEWPORT.centerx,
                            top=y + index * line_height + 3,
                        ),
                    )
                y += len(lines) * line_height + 24
                continue
            label, value = entry
            label_surface = fit_text(body, label, 180, UI_COLORS["accent"])
            screen.blit(label_surface, (self.VIEWPORT.left + 12, y))
            lines = wrap_text(caption, value, self.VIEWPORT.width - 236)
            for index, line in enumerate(lines):
                screen.blit(
                    fit_text(caption, line, self.VIEWPORT.width - 236, UI_COLORS["text"]),
                    (self.VIEWPORT.left + 212, y + index * line_height + 3),
                )
            y += max(body.get_linesize(), len(lines) * line_height) + 24
        screen.set_clip(None)
        content_height = y + int(self.scroll_y) - self.VIEWPORT.top
        self.max_scroll = max(0.0, content_height - self.VIEWPORT.height)
        self.scroll_y = min(self.scroll_y, self.max_scroll)

        hint = fit_text(caption, "滚轮 / 方向键浏览", 260, UI_COLORS["muted"])
        screen.blit(hint, hint.get_rect(bottomright=(SCREEN_WIDTH - 36, SCREEN_HEIGHT - 24)))

    def _scroll(self, amount):
        self.scroll_y = max(0.0, min(self.max_scroll, self.scroll_y + amount))

    def _back(self):
        from states.main_menu_state import MainMenuState

        self.game.change_state(MainMenuState(self.game))