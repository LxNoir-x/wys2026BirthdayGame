"""主线开始前的游玩注意事项。"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import ClassVar

import pygame

from config import SCREEN_HEIGHT, SCREEN_WIDTH, load_notice_font
from states.game_state import GameState
from utils.ui_art import draw_background
from utils.ui_theme import (
    UI_COLORS,
    draw_button,
    draw_panel,
    fit_text,
    get_font,
    wrap_text,
)

DEFAULT_NOTICE = (
    "游玩前注意事项\n\n"
    "本游戏包含快速闪烁、屏幕故障风格演出、音效与较高对比度画面。"
    "对闪烁画面、光敏性癫痫或类似不适敏感的玩家，请谨慎游玩；如出现不适，请立即暂停并休息。\n\n"
    "本游戏所有原创内容创作期间未使用AI功能，详情参照制作名单，最终解释权归创作团队所有，"
    "未经授权，不得转载、复制、修改、提取素材，或作其他任何商业用途。\n\n"
    "如您在游玩过程中遇到任何Bug或有改进建议，欢迎通过官方渠道（开发者邮件/社群）与我们联系，"
    "您的每一条反馈都是我们进步的动力。\n\n"    
    "点击“同意并进入”即表示您已阅读并完全理解以上所有提示内容，"
    "并愿意自行承担因未遵守须知而可能产生的后果。\n\n"
    "祝您游玩愉快！"
)


class NoticeState(GameState):
    """在游戏启动时展示安全说明与授权提示。"""

    BACK_RECT: ClassVar = pygame.Rect(40, 638, 130, 44)
    CONTINUE_RECT: ClassVar = pygame.Rect(922, 628, 300, 56)
    CONTENT_RECT: ClassVar = pygame.Rect(110, 126, 1060, 470)

    def __init__(self, game, resume_recovery=True):
        super().__init__(game)
        # Keep the legacy argument for old callers; the notice now always leads to the menu.
        self.resume_recovery = resume_recovery
        self.notice_font_cache = load_notice_font()
        self.scroll_y = 0.0
        self.max_scroll = 0.0
        self.lines: list[str] = []
        self._load_notice()

    def _load_notice(self):
        candidates = []
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            candidates.append(Path(meipass) / "assets" / "text" / "game_notice.txt")
        candidates.append(
            Path(__file__).resolve().parents[1] / "assets" / "text" / "game_notice.txt"
        )
        text = None
        for path in candidates:
            try:
                if path.is_file():
                    text = path.read_text(encoding="utf-8").strip()
                    break
            except OSError:
                continue
        text = text or DEFAULT_NOTICE
        font = get_font(self.notice_font_cache, "body")
        self.lines = []
        for paragraph in text.splitlines():
            if not paragraph.strip():
                self.lines.append("")
            else:
                self.lines.extend(
                    wrap_text(font, paragraph.strip(), self.CONTENT_RECT.width - 64)
                )

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                    self._back()
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    self._continue()
                elif event.key in (pygame.K_UP, pygame.K_w, pygame.K_PAGEUP):
                    self._scroll(-70 if event.key != pygame.K_PAGEUP else -420)
                elif event.key in (pygame.K_DOWN, pygame.K_s, pygame.K_PAGEDOWN):
                    self._scroll(70 if event.key != pygame.K_PAGEDOWN else 420)
                elif event.key == pygame.K_HOME:
                    self.scroll_y = 0.0
                elif event.key == pygame.K_END:
                    self.scroll_y = self.max_scroll
            elif event.type == pygame.MOUSEWHEEL:
                self._scroll(-event.y * 70)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.BACK_RECT.collidepoint(event.pos):
                    self._back()
                elif self.CONTINUE_RECT.collidepoint(event.pos):
                    self._continue()

    def update(self, dt):
        return None

    def draw(self, screen):
        latest = self.game.ending_history[-1] if self.game.ending_history else None
        if latest == "BE":
            background = "images/ui/main_menu_be.png"
        elif latest == "TE":
            background = "images/ui/main_menu_te.png"
        elif latest and latest.startswith("HE"):
            background = "images/ui/main_menu_he.png"
        else:
            background = "images/ui/main_menu_default.png"
        draw_background(screen, background)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((4, 12, 17, 226))
        screen.blit(overlay, (0, 0))

        title_font = get_font(self.notice_font_cache, "title")
        title = fit_text(title_font, "游玩前注意事项", 760, UI_COLORS["text"])
        screen.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, 62)))

        draw_panel(
            screen,
            self.CONTENT_RECT,
            fill=(10, 28, 36),
            border=UI_COLORS["accent"],
            radius=6,
            shadow=False,
        )
        body = get_font(self.notice_font_cache, "body")
        line_height = body.get_linesize() + 6
        content_height = (
            sum(line_height if line else line_height // 2 for line in self.lines) + 32
        )
        viewport = self.CONTENT_RECT.inflate(-32, -28)
        self.max_scroll = max(0.0, content_height - viewport.height)
        self.scroll_y = max(0.0, min(self.scroll_y, self.max_scroll))
        y = viewport.top + 12 - int(self.scroll_y)
        screen.set_clip(viewport)
        for line in self.lines:
            if line:
                screen.blit(
                    fit_text(body, line, viewport.width, UI_COLORS["text"]),
                    (viewport.left, y),
                )
                y += line_height
            else:
                y += line_height // 2
        screen.set_clip(None)

        draw_button(
            screen,
            self.BACK_RECT,
            "返回",
            get_font(self.notice_font_cache, "caption"),
            "secondary",
        )
        draw_button(
            screen,
            self.CONTINUE_RECT,
            "同意并进入",
            get_font(self.notice_font_cache, "button"),
            "primary",
        )
        hint = fit_text(
            get_font(self.notice_font_cache, "micro"),
            "滚轮 / ↑↓ 浏览，Enter 进入",
            360,
            UI_COLORS["muted"],
        )
        screen.blit(hint, hint.get_rect(bottomleft=(220, 670)))

    def _scroll(self, amount):
        self.scroll_y = max(0.0, min(self.max_scroll, self.scroll_y + amount))

    def _continue(self):
        from states.main_menu_state import MainMenuState

        self.game.change_state(MainMenuState(self.game))

    def _back(self):
        from states.main_menu_state import MainMenuState

        self.game.change_state(MainMenuState(self.game))
