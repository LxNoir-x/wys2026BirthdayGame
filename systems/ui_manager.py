"""全局 Toast 通知。"""

from __future__ import annotations

import pygame

from config import COLORS, SCREEN_WIDTH
from utils.ui_theme import UI_COLORS, draw_panel, fit_text, get_font, wrap_text

CARD_FILL = (169, 194, 190)
CARD_BORDER = (40, 66, 67)
CARD_HEADER_FILL = (75, 105, 104)
CARD_HEADER_TEXT = (235, 244, 240)
CARD_TITLE_TEXT = (19, 43, 45)


class Toast:
    """固定在右上角的轻量通知。"""

    def __init__(self, title, message, accent, duration=4.0):
        self.title = str(title)
        self.message = str(message)
        self.accent = accent
        self.duration = max(1.0, float(duration))
        self.time_left = self.duration

    def update(self, dt):
        self.time_left -= dt
        return self.time_left > 0

    def _message_lines(self, font, max_width):
        lines = []
        paragraphs = self.message.splitlines() or [""]
        for paragraph in paragraphs:
            lines.extend(wrap_text(font, paragraph, max_width))
        return lines

    def height(self, font_cache):
        if not self.message:
            return 62
        body = get_font(font_cache, "caption")
        line_count = max(1, len(self._message_lines(body, 316)))
        return (34 if not self.title else 70) + line_count * 22

    def draw(self, screen, font_cache, y):
        title_font = get_font(font_cache, "button")
        body_font = get_font(font_cache, "caption")
        lines = self._message_lines(body_font, 316) if self.message else []
        width = 380
        height = 62 if not lines else (34 if not self.title else 70) + len(lines) * 22
        x = SCREEN_WIDTH - width - 28

        elapsed = self.duration - self.time_left
        fade_in = min(1.0, elapsed / 0.22)
        fade_out = min(1.0, self.time_left / 0.35)
        alpha = int(255 * min(fade_in, fade_out))
        if alpha <= 0:
            return

        canvas = pygame.Surface((width, height), pygame.SRCALPHA)
        draw_panel(
            canvas,
            pygame.Rect(0, 0, width, height),
            fill=(24, 33, 52),
            border=self.accent,
            radius=12,
            shadow=False,
        )
        pygame.draw.rect(
            canvas, (*self.accent, 240), (0, 0, 5, height), border_radius=3
        )
        if self.title:
            title = fit_text(title_font, self.title, width - 46, self.accent)
            canvas.blit(title, (22, 13))
        for index, line in enumerate(lines[:4]):
            canvas.blit(
                fit_text(body_font, line, width - 50, UI_COLORS["text"]),
                (22, (18 if not self.title else 43) + index * 22),
            )
        canvas.set_alpha(alpha)
        screen.blit(canvas, (x, y))


class AchievementToast(Toast):
    """使用关卡内成就卡样式，只显示成就名称。"""

    WIDTH = 260
    HEIGHT = 92

    def height(self, font_cache):
        return self.HEIGHT

    def draw(self, screen, font_cache, y):
        header_font = get_font(font_cache, "caption")
        title_font = get_font(font_cache, "button")
        x = SCREEN_WIDTH - self.WIDTH - 28

        elapsed = self.duration - self.time_left
        alpha = int(
            255
            * min(
                1.0,
                elapsed / 0.22,
                self.time_left / 0.35,
            )
        )
        if alpha <= 0:
            return

        canvas = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)
        draw_panel(
            canvas,
            pygame.Rect(0, 0, self.WIDTH, self.HEIGHT),
            fill=CARD_FILL,
            border=CARD_BORDER,
            radius=4,
            shadow=False,
        )
        pygame.draw.rect(canvas, CARD_HEADER_FILL, (18, 14, self.WIDTH - 36, 34))
        header = header_font.render("- 成就解锁 -", True, CARD_HEADER_TEXT)
        canvas.blit(header, header.get_rect(center=(self.WIDTH // 2, 31)))

        name = fit_text(
            title_font,
            f"「{self.title}」",
            self.WIDTH - 32,
            CARD_TITLE_TEXT,
        )
        canvas.blit(name, name.get_rect(center=(self.WIDTH // 2, 65)))

        canvas.set_alpha(alpha)
        screen.blit(canvas, (x, y))


class CollectibleToast(Toast):
    """只显示藏品名称的精简获得卡片。"""

    WIDTH = 260
    HEIGHT = 96

    def height(self, font_cache):
        return self.HEIGHT

    def draw(self, screen, font_cache, y):
        header_font = get_font(font_cache, "caption")
        name_font = get_font(font_cache, "button")
        x = SCREEN_WIDTH - self.WIDTH - 28
        elapsed = self.duration - self.time_left
        alpha = int(255 * min(1.0, elapsed / 0.22, self.time_left / 0.35))
        if alpha <= 0:
            return

        canvas = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)
        draw_panel(
            canvas,
            pygame.Rect(0, 0, self.WIDTH, self.HEIGHT),
            fill=CARD_FILL,
            border=CARD_BORDER,
            radius=4,
            shadow=False,
        )
        pygame.draw.rect(canvas, CARD_HEADER_FILL, (18, 14, self.WIDTH - 36, 34))
        header = header_font.render("- 获得藏品 -", True, CARD_HEADER_TEXT)
        canvas.blit(header, header.get_rect(center=(self.WIDTH // 2, 31)))
        name = fit_text(
            name_font,
            f"「{self.title}」",
            self.WIDTH - 32,
            CARD_TITLE_TEXT,
        )
        canvas.blit(name, name.get_rect(center=(self.WIDTH // 2, 66)))
        canvas.set_alpha(alpha)
        screen.blit(canvas, (x, y))


class SkinToast(Toast):
    """外观切换通知，复用藏品/成就卡片的卡片外框。"""

    WIDTH = 260
    HEIGHT = 96

    def __init__(
        self, title, message="", accent=None, duration=4.0, header="- 外观切换 -"
    ):
        super().__init__(title, message, accent, duration)
        self.header = header

    def height(self, font_cache):
        return self.HEIGHT

    def draw(self, screen, font_cache, y):
        header_font = get_font(font_cache, "caption")
        name_font = get_font(font_cache, "button")
        x = SCREEN_WIDTH - self.WIDTH - 28
        elapsed = self.duration - self.time_left
        alpha = int(255 * min(1.0, elapsed / 0.22, self.time_left / 0.35))
        if alpha <= 0:
            return

        canvas = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)
        draw_panel(
            canvas,
            pygame.Rect(0, 0, self.WIDTH, self.HEIGHT),
            fill=CARD_FILL,
            border=CARD_BORDER,
            radius=4,
            shadow=False,
        )
        pygame.draw.rect(canvas, CARD_HEADER_FILL, (18, 14, self.WIDTH - 36, 34))
        header = header_font.render(self.header, True, CARD_HEADER_TEXT)
        canvas.blit(header, header.get_rect(center=(self.WIDTH // 2, 31)))
        name = fit_text(
            name_font,
            f"「{self.title}」",
            self.WIDTH - 32,
            CARD_TITLE_TEXT,
        )
        canvas.blit(name, name.get_rect(center=(self.WIDTH // 2, 66)))
        canvas.set_alpha(alpha)
        screen.blit(canvas, (x, y))


class UIManager:
    def __init__(self, game):
        self.game = game
        self.toasts = []
        # 兼容旧代码读取该属性；实际通知统一走同一个 Toast 列表。
        self.achievement_notifications = self.toasts
        self.floating_text_system = None

    def show_toast(self, title, message="", accent=None, duration=4.0):
        self.toasts.append(
            Toast(title, message, accent or UI_COLORS["accent"], duration)
        )
        self.toasts[:] = self.toasts[-4:]

    def show_achievement_notification(self, name):
        self.toasts.append(
            AchievementToast(name, "", UI_COLORS["gold"], duration=5.0)
        )
        self.toasts[:] = self.toasts[-4:]

    def show_collectible_notification(self, name):
        self.toasts.append(
            CollectibleToast(name, "", UI_COLORS["gold"], duration=4.0)
        )
        self.toasts[:] = self.toasts[-4:]

    def show_skin_notification(self, name, header="- 外观切换 -"):
        self.toasts.append(
            SkinToast(
                name,
                "",
                UI_COLORS["gold"],
                duration=4.0,
                header=header,
            )
        )
        self.toasts[:] = self.toasts[-4:]

    def show_floating_text(
        self,
        x,
        y,
        text,
        color=COLORS["GOLD"],
        duration=1.5,
        speed=20,
        size=24,
    ):
        # 旧接口仍保留，视觉表现统一为右上角 Toast。
        del x, y, speed, size
        self.show_toast("提示", text, color, duration)

    def update(self, dt):
        self.toasts[:] = [toast for toast in self.toasts if toast.update(dt)]

    def draw(self, screen, font_cache):
        y = 24
        for toast in self.toasts:
            toast.draw(screen, font_cache, y)
            y += toast.height(font_cache) + 12
