"""主菜单状态。"""

from __future__ import annotations

import random
import sys
from typing import ClassVar

import pygame

from config import MAIN_LEVEL_IDS
from states.game_state import GameState
from states.level_select_state import LevelSelectState
from utils.ui_art import draw_background, load_image, scaled_image
from utils.ui_theme import UI_COLORS, draw_button, draw_panel, fit_text, get_font

# 主界面终端控件的荧光青，与 CRT 监视器/工控终端基色一致。
_MENU_GLOW = (110, 224, 177)

# BE 主标题“维云斯的▢▢▢▢”的第 1、3 个方块会随机频闪乱码。
# 底图是 3556x2000 的合成图，方块原始格子 219x219；第 2 个方块是未损坏的
# 干净空格，用它重建第 1、3 格的底色，再用 luamma.png 叠加故障。
_BE_TITLE_NATIVE_SLOT = 219
_BE_TITLE_NATIVE_TOP = 713
_BE_TITLE_NATIVE_CLEAN_LEFT = 2422
_BE_TITLE_NATIVE_LEFT = (2163, 2681)
# 方格在游戏窗口（1280x720）中的落点，仅覆盖第 1、3 两格。
_BE_TITLE_GLITCH_RECTS = (
    pygame.Rect(779, 257, 79, 79),
    pygame.Rect(965, 257, 79, 79),
)
# luamma.png 中左右两簇乱码分别对应第 1、3 个方块。
_BE_TITLE_LUAMMA_CLUSTERS = ((0, 0, 363, 513), (518, 0, 363, 513))
# 乱码故障层比方块本体每边大 50 像素，居中溢出边框，增强故障感。
_BE_TITLE_GLITCH_GROW = 50

_BE_TITLE_LAYER_CACHE: dict[str, list[pygame.Surface]] = {}


def _be_title_layers() -> dict[str, list[pygame.Surface]]:
    """构建 BE 主标题第 1、3 格的（干净底色、乱码故障）成对素材并缓存。"""

    if "clean" in _BE_TITLE_LAYER_CACHE:
        return _BE_TITLE_LAYER_CACHE

    import numpy as np

    slot = _BE_TITLE_NATIVE_SLOT
    top = _BE_TITLE_NATIVE_TOP
    background = pygame.surfarray.array3d(
        load_image("images/ui/main_menu_be.png")
    ).astype(np.int16)
    reference = background[
        _BE_TITLE_NATIVE_CLEAN_LEFT:_BE_TITLE_NATIVE_CLEAN_LEFT + slot,
        top:top + slot,
    ]
    outline = reference.max(axis=2) > 140
    size = _BE_TITLE_GLITCH_RECTS[0].size

    clean_layers = []
    for left in _BE_TITLE_NATIVE_LEFT:
        tile = background[left:left + slot, top:top + slot].copy()
        bright = tile.max(axis=2) > 130
        # 抹掉方块内部的乱码与破损轮廓，再用干净方块补齐轮廓。
        filler = np.median(tile[~bright].reshape(-1, 3), axis=0)
        tile[bright & ~outline] = filler
        tile[outline] = reference[outline]
        clean_layers.append(
            pygame.transform.smoothscale(
                pygame.surfarray.make_surface(tile.astype(np.uint8)), size
            )
        )

    glitch = load_image("images/ui/luamma.png")
    glitch_size = (size[0] + _BE_TITLE_GLITCH_GROW, size[1] + _BE_TITLE_GLITCH_GROW)
    glitch_layers = [
        pygame.transform.smoothscale(glitch.subsurface(rect).copy(), glitch_size)
        for rect in _BE_TITLE_LUAMMA_CLUSTERS
    ]

    _BE_TITLE_LAYER_CACHE["clean"] = clean_layers
    _BE_TITLE_LAYER_CACHE["glitch"] = glitch_layers
    return _BE_TITLE_LAYER_CACHE


class MainMenuState(GameState):
    """根据最近一次结局显示对应主菜单封面。"""

    music_scene = "menu"
    ESCAPE_RECTS: ClassVar = {
        "continue": pygame.Rect(474, 302, 332, 52),
        "settings": pygame.Rect(474, 370, 332, 52),
        "quit": pygame.Rect(474, 438, 332, 52),
    }
    CONFIRM_RECTS: ClassVar = {
        "cancel": pygame.Rect(468, 426, 160, 50),
        "quit": pygame.Rect(652, 426, 160, 50),
    }
    CREDITS_RECT: ClassVar = pygame.Rect(32, 656, 128, 34)
    # 与制作名单紧邻并排，形成底部的系统级功能区。
    ENDING_SWITCH_RECT: ClassVar = pygame.Rect(168, 656, 84, 34)
    ENDING_FADE_SECONDS: ClassVar = 0.75

    # 每个封面各选项统一使用同一个矩形，同时作为绘制选框与点击命中区。
    MENU_RECTS: ClassVar[dict[str, dict[str, pygame.Rect]]] = {
        "default": {
            "start": pygame.Rect(556, 458, 160, 53),
        },
        "he": {
            "start": pygame.Rect(754, 262, 102, 37),
            "reminiscence": pygame.Rect(730, 295, 186, 39),
            "archive": pygame.Rect(765, 323, 94, 39),
            "settings": pygame.Rect(743, 351, 136, 42),
        },
        "be": {
            "start": pygame.Rect(865, 410, 171, 40),
            "reminiscence": pygame.Rect(787+5, 462+5, 314, 42),
            "archive": pygame.Rect(870, 521+2, 155, 35),
            "settings": pygame.Rect(830+5, 577, 218, 37),
        },
        "te": {
            "start": pygame.Rect(79, 556, 199, 47),
            "reminiscence": pygame.Rect(307, 566, 353, 37),
            "archive": pygame.Rect(694, 562, 169, 41),
            "settings": pygame.Rect(909, 562, 269, 41),
        },
    }

    # 鼠标悬停光标：各封面使用的箭头素材、显示尺寸，以及每个选项上的落点中心。
    # 尺寸与位置由 main_menu_<variant>_expect.png 参考图还原：参考图 = 封面按
    # 运行时比例放大后，把素材原始像素尺寸直接贴上去（he 为 3 倍，be/te/default
    # 为 1.5 倍），落点取该素材贴图矩形在选项上的中心。
    HOVER_CURSORS: ClassVar[dict[str, dict]] = {
        "default": {
            "asset": "images/ui/BE_TE_selecting.png",
            "size": (76, 85),
            "centers": {"start": (526.7, 484.5)},
        },
        "he": {
            "asset": "images/ui/HE_selecting.png",
            "size": (11, 16),
            "centers": {
                "start": (772.3, 279.5),
                "reminiscence": (739.3, 303.5),
                "archive": (775.7, 339.2),
                "settings": (758.5, 365.5),
            },
        },
        "be": {
            "asset": "images/ui/BE_TE_selecting.png",
            "size": (64, 72),
            "centers": {
                "start": (883.7, 430.7),
                "reminiscence": (815.7, 486.0),
                "archive": (890.7, 541.3),
                "settings": (856.0, 596.7),
            },
        },
        "te": {
            "asset": "images/ui/BE_TE_selecting.png",
            "size": (76, 85),
            "centers": {
                "start": (104.0, 583.8),
                "reminiscence": (328.7, 583.8),
                "archive": (720.0, 582.8),
                "settings": (929.3, 582.5),
            },
        },
    }

    def __init__(self, game):
        super().__init__(game)
        self.selected_index = 0
        self.menu_variant = self._initial_variant()
        self.music_scene = self._music_scene_for(self.menu_variant)
        self.transition = None
        self.menu_rects = self.MENU_RECTS[self.menu_variant]
        self.start_rect = pygame.Rect(0, 0, 0, 0)
        self.select_rect = pygame.Rect(0, 0, 0, 0)
        self.archive_rect = pygame.Rect(0, 0, 0, 0)
        self.settings_rect = pygame.Rect(0, 0, 0, 0)
        self.endless_rect = pygame.Rect(0, 0, 0, 0)
        self.achievement_rect = pygame.Rect(0, 0, 0, 0)
        self.shop_rect = pygame.Rect(0, 0, 0, 0)
        self.quit_rect = pygame.Rect(0, 0, 0, 0)
        self.developer_menu_open = False
        self.developer_buttons = []
        self.escape_menu_open = False
        self.exit_confirmation_open = False
        # BE 主标题第 1、3 格的乱码频闪节奏，两格各自独立随机。
        self.title_glitch = [
            {"active": False, "timer": random.uniform(0.2, 1.5)}
            for _ in _BE_TITLE_GLITCH_RECTS
        ]

    def _options(self):
        """当前封面可用的菜单项，按键顺序与矩形表一致。"""

        return tuple(self.menu_rects)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if self.escape_menu_open:
                    if event.key == pygame.K_ESCAPE:
                        if self.exit_confirmation_open:
                            self.exit_confirmation_open = False
                        else:
                            self.escape_menu_open = False
                    continue
                if event.key == pygame.K_F12:
                    self.developer_menu_open = not self.developer_menu_open
                    continue
                if self.developer_menu_open and event.key == pygame.K_ESCAPE:
                    self.developer_menu_open = False
                elif self.developer_menu_open:
                    continue
                elif event.key in (pygame.K_UP, pygame.K_w):
                    options = self._options()
                    self.selected_index = (self.selected_index - 1) % len(options)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    options = self._options()
                    self.selected_index = (self.selected_index + 1) % len(options)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    options = self._options()
                    self.game.audio_system.play_sfx("menu_click")
                    self._activate(options[self.selected_index % len(options)])
                elif event.key == pygame.K_ESCAPE:
                    self.escape_menu_open = True
                elif event.key == pygame.K_c and self.game.ending_history:
                    self._open_credits()
            elif event.type == pygame.MOUSEMOTION:
                if self.escape_menu_open:
                    continue
                for index, key in enumerate(self._options()):
                    rect = self.menu_rects.get(key)
                    if rect and rect.collidepoint(event.pos):
                        self.selected_index = index
                        break
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.escape_menu_open:
                    self._handle_escape_click(event.pos)
                    continue
                if self.developer_menu_open:
                    for target, rect in self.developer_buttons:
                        if rect.collidepoint(event.pos):
                            self._open_developer_target(target)
                            return
                    continue
                if self.transition:
                    continue
                if (
                    len(self._available_variants()) >= 2
                    and self.ENDING_SWITCH_RECT.collidepoint(event.pos)
                ):
                    self._cycle_variant()
                    continue
                if self.game.ending_history and self.CREDITS_RECT.collidepoint(
                    event.pos
                ):
                    self._open_credits()
                    return
                for key, rect in self.menu_rects.items():
                    if rect.collidepoint(event.pos):
                        self.game.audio_system.play_sfx("menu_click")
                        self._activate(key)
                        break

    def _handle_escape_click(self, position):
        if self.exit_confirmation_open:
            if self.CONFIRM_RECTS["cancel"].collidepoint(position):
                self.exit_confirmation_open = False
            elif self.CONFIRM_RECTS["quit"].collidepoint(position):
                pygame.quit()
                sys.exit(0)
            return

        if self.ESCAPE_RECTS["continue"].collidepoint(position):
            self.escape_menu_open = False
        elif self.ESCAPE_RECTS["settings"].collidepoint(position):
            from states.settings_state import SettingsState

            self.game.change_state(SettingsState(self.game, return_state=self))
        elif self.ESCAPE_RECTS["quit"].collidepoint(position):
            self.exit_confirmation_open = True

    def _activate(self, option):
        if option == "start":
            self.game.start_main_story()
        elif option == "reminiscence":
            self.game.change_state(LevelSelectState(self.game))
        elif option == "archive":
            from states.archive_state import ArchiveState

            self.game.change_state(ArchiveState(self.game, "skins"))
        elif option == "settings":
            from states.settings_state import SettingsState

            self.game.change_state(SettingsState(self.game))

    def update(self, dt):
        self._update_title_glitch(dt)
        if not self.transition:
            return
        self.transition["t"] += dt
        if self.transition["t"] >= self.transition["duration"]:
            self.menu_variant = self.transition["to"]
            self.transition = None

    def _update_title_glitch(self, dt):
        """让 BE 主标题第 1、3 格以不可预判的节奏闪烁乱码。"""

        for slot in self.title_glitch:
            slot["timer"] -= dt
            if slot["timer"] > 0:
                continue
            slot["active"] = not slot["active"]
            # 亮起只持续一瞬，熄灭后随机停顿较久，形成“随机出现”的频闪。
            slot["timer"] = (
                random.uniform(0.05, 0.28)
                if slot["active"]
                else random.uniform(0.35, 2.4)
            )

    def _draw_title_glitch(self, screen):
        """用重建的干净底色盖住底图静态乱码，再随机叠加故障乱码。"""

        layers = _be_title_layers()
        for index, rect in enumerate(_BE_TITLE_GLITCH_RECTS):
            screen.blit(layers["clean"][index], rect)
            if not self.title_glitch[index]["active"]:
                continue
            glitch = layers["glitch"][index].copy()
            glitch.set_alpha(random.randint(150, 255))
            jitter = (random.randint(-2, 2), random.randint(-1, 1))
            screen.blit(glitch, glitch.get_rect(center=rect.center).move(jitter))

    @staticmethod
    def _music_scene_for(variant):
        """BE/TE 主界面使用各自结局的主题曲，其余沿用默认主界面曲。"""

        if variant == "be":
            return "be_theme"
        if variant == "te":
            return "te_theme"
        return "menu"

    def _initial_variant(self):
        return self._menu_variant()

    @staticmethod
    def _variant_for_ending(ending):
        if ending == "BE":
            return "be"
        if ending == "TE":
            return "te"
        return "he"

    def _available_variants(self):
        """只返回已解锁结局对应的主界面变体，顺序固定为 he→be→te。"""

        unlocked = {
            self._variant_for_ending(ending) for ending in self.game.ending_history
        }
        return [variant for variant in ("he", "be", "te") if variant in unlocked]

    def _cycle_variant(self):
        if self.transition:
            return
        variants = self._available_variants()
        if len(variants) < 2:
            return
        index = (
            variants.index(self.menu_variant) if self.menu_variant in variants else 0
        )
        target = variants[(index + 1) % len(variants)]
        self.transition = {
            "from": self.menu_variant,
            "to": target,
            "t": 0.0,
            "duration": self.ENDING_FADE_SECONDS,
        }
        # 点击切换时，BGM 同步切到目标版本；he/be 之间用淡出淡入平滑接续，TE 不做过渡。
        self.music_scene = self._music_scene_for(target)
        audio = self.game.audio_system
        if {audio.current_scene, self.music_scene} <= {"menu", "be_theme"}:
            audio.play_scene_fading(self.music_scene)
        else:
            audio.play_scene(self.music_scene)

    def _transition_blend(self):
        """主界面切换的交叉淡化比例：0 = 全旧图，1 = 全新图。

        用 smoothstep 缓动，两端慢、中间快，避免线性淡入淡出的生硬感。
        """

        if not self.transition:
            return None
        progress = min(1.0, self.transition["t"] / self.transition["duration"])
        return progress * progress * (3.0 - 2.0 * progress)

    def _draw_transition_background(self, screen, blend):
        """旧主界面渐隐、新主界面渐显，全程不经过纯黑闪屏。"""

        draw_background(
            screen, f"images/ui/main_menu_{self.transition['from']}.png"
        )
        incoming = scaled_image(
            f"images/ui/main_menu_{self.transition['to']}.png", screen.get_size()
        ).copy()
        incoming.set_alpha(round(255 * blend))
        screen.blit(incoming, (0, 0))

    def _draw_hover_cursor(self, screen, variant, mouse_position):
        """仅在鼠标悬停某个选项时叠加箭头素材；未悬停不绘制任何素材。"""

        spec = self.HOVER_CURSORS.get(variant)
        if not spec:
            return
        for key, rect in self.menu_rects.items():
            if not rect.collidepoint(mouse_position):
                continue
            center = spec["centers"].get(key)
            if center is None:
                return
            cursor = scaled_image(spec["asset"], spec["size"])
            screen.blit(
                cursor,
                cursor.get_rect(center=(round(center[0]), round(center[1]))),
            )
            return

    def _draw_console_button(self, screen, rect, label):
        """绘制底栏工控按钮：微透明面板、状态指示灯与悬停辉光。"""

        rect = pygame.Rect(rect)
        hovered = rect.collidepoint(pygame.mouse.get_pos())
        accent = _MENU_GLOW if hovered else (64, 118, 110)
        if hovered:
            glow = pygame.Surface(
                (rect.width + 12, rect.height + 12), pygame.SRCALPHA
            )
            pygame.draw.rect(glow, (*_MENU_GLOW, 44), glow.get_rect(), border_radius=6)
            screen.blit(glow, (rect.x - 6, rect.y - 6))
        panel = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(panel, (12, 26, 32, 214), panel.get_rect(), border_radius=4)
        pygame.draw.rect(
            panel, (*accent, 235), panel.get_rect(), 1, border_radius=4
        )
        screen.blit(panel, rect)

        dot = pygame.Rect(rect.x + 10, rect.centery - 3, 6, 6)
        pygame.draw.rect(screen, accent, dot)
        color = (238, 255, 248) if hovered else (196, 219, 213)
        font = get_font(self.game.font_cache, "caption")
        surface = fit_text(font, label, rect.width - 34, color)
        screen.blit(surface, surface.get_rect(midleft=(dot.right + 8, rect.centery)))
        return rect

    def _draw_ending_switch(self, screen):
        if len(self._available_variants()) < 2:
            return
        self._draw_console_button(screen, self.ENDING_SWITCH_RECT, "切换")

    def _open_credits(self):
        from states.credits_state import CreditsState

        self.game.change_state(CreditsState(self.game))

    def _open_developer_target(self, target):
        if target == "story":
            self.game.start_main_story()
        elif target == "reminiscence":
            self.game.change_state(LevelSelectState(self.game))
        elif target.startswith("level:"):
            from states.play_state import PlayState

            self.game.change_state(PlayState(self.game, int(target.split(":", 1)[1])))
        elif target.startswith("archive:"):
            from states.archive_state import ArchiveState

            self.game.change_state(ArchiveState(self.game, target.split(":", 1)[1]))
        elif target == "settings":
            from states.settings_state import SettingsState

            self.game.change_state(SettingsState(self.game))
        elif target == "endless":
            from states.endless_state import EndlessState

            self.game.change_state(EndlessState(self.game))
        elif target == "s_level":
            from states.s_level_state import SLevelState

            self.game.change_state(SLevelState(self.game))
        elif target.startswith("ending:"):
            from states.ending_state import EndingState

            ending_type = target.split(":", 1)[1]
            self.game.active_ending = ending_type
            # 与正式结算一致：同步解锁该结局的成就、皮肤，并记入结局历史，
            # 让主菜单的对应封面与「切换」按钮一并解锁。
            self.game.unlock_ending_rewards(ending_type)
            if ending_type not in self.game.ending_history:
                self.game.ending_history.append(ending_type)
                self.game.save_progress()
            self.game.change_state(EndingState(self.game, ending_type))

    def draw(self, screen):
        blend = self._transition_blend()
        if blend is None:
            variant = self.menu_variant
            draw_background(screen, f"images/ui/main_menu_{variant}.png")
        else:
            # 交叉淡化期间动态 UI 用当前占主导的一侧，避免光标/按钮来回跳。
            variant = self.transition["from"] if blend < 0.5 else self.transition["to"]
            self._draw_transition_background(screen, blend)
        if variant == "be":
            self._draw_title_glitch(screen)

        self.menu_rects = self.MENU_RECTS[variant]
        self.start_rect = self.menu_rects.get("start", pygame.Rect(0, 0, 0, 0))
        self.select_rect = self.menu_rects.get("reminiscence", pygame.Rect(0, 0, 0, 0))
        self.archive_rect = self.menu_rects.get("archive", pygame.Rect(0, 0, 0, 0))
        self.settings_rect = self.menu_rects.get("settings", pygame.Rect(0, 0, 0, 0))

        mouse_pos = pygame.mouse.get_pos()
        for index, key in enumerate(self._options()):
            if self.menu_rects[key].collidepoint(mouse_pos):
                self.selected_index = index
        self.selected_index %= len(self.menu_rects)

        # 悬停提示改为箭头素材，不再绘制绿色扫描线/直角括号选择框。
        self._draw_hover_cursor(screen, variant, mouse_pos)
        if self.game.ending_history:
            self._draw_console_button(screen, self.CREDITS_RECT, "制作名单")
        self._draw_ending_switch(screen)

        # 封面没有额外状态面板，结局信息只在鼠标移到屏幕角落时以小字提示，
        # 避免覆盖主创已经完成的构图。
        if self.developer_menu_open:
            self._draw_developer_menu(screen)
        if self.escape_menu_open:
            self._draw_escape_menu(screen)

    def _menu_variant(self):
        latest = getattr(self.game, "active_ending", None)
        if not latest and self.game.ending_history:
            latest = self.game.ending_history[-1]
        if not latest:
            return "default"
        return self._variant_for_ending(latest)

    def _draw_escape_menu(self, screen):
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((2, 8, 12, 205))
        screen.blit(overlay, (0, 0))
        panel = pygame.Rect(424, 220, 432, 338)
        draw_panel(screen, panel, fill=(11, 25, 31), border=UI_COLORS["accent"])
        title = get_font(self.game.font_cache, "button").render(
            "暂停菜单", True, UI_COLORS["text"]
        )
        screen.blit(title, title.get_rect(center=(panel.centerx, panel.y + 48)))

        if self.exit_confirmation_open:
            prompt = get_font(self.game.font_cache, "body").render(
                "确认退出游戏？", True, UI_COLORS["text"]
            )
            screen.blit(prompt, prompt.get_rect(center=(panel.centerx, panel.y + 136)))
            button_font = get_font(self.game.font_cache, "button")
            draw_button(
                screen, self.CONFIRM_RECTS["cancel"], "取消", button_font, "secondary"
            )
            draw_button(
                screen, self.CONFIRM_RECTS["quit"], "退出", button_font, "danger"
            )
            return

        button_font = get_font(self.game.font_cache, "button")
        # 主菜单的 ESC 面板：首个按钮语义是回到主界面本身（关闭该面板）。
        draw_button(
            screen,
            self.ESCAPE_RECTS["continue"],
            "回到主界面",
            button_font,
            "primary",
        )
        draw_button(
            screen, self.ESCAPE_RECTS["settings"], "设置", button_font, "secondary"
        )
        draw_button(
            screen, self.ESCAPE_RECTS["quit"], "退出游戏", button_font, "danger"
        )

    def _draw_developer_menu(self, screen):
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((4, 13, 18, 220))
        screen.blit(overlay, (0, 0))
        panel = pygame.Rect(104, 58, 1072, 604)
        draw_panel(screen, panel)
        title = get_font(self.game.font_cache, "button").render(
            "开发者模式", True, UI_COLORS["accent"]
        )
        subtitle = get_font(self.game.font_cache, "caption").render(
            "点击进入任意界面，F12 或 Esc 关闭", True, UI_COLORS["muted"]
        )
        screen.blit(title, (panel.x + 28, panel.y + 18))
        screen.blit(subtitle, (panel.x + 30, panel.y + 55))

        font = get_font(self.game.font_cache, "micro")
        button_width = 155
        button_height = 42
        gap = 14
        x0 = panel.x + 28
        y = panel.y + 82
        self.developer_buttons = []

        targets = [
            ("主线开始", "story"),
            ("追忆", "reminiscence"),
            ("无尽模式", "endless"),
            ("S 关卡", "s_level"),
            ("皮肤数据库", "archive:skins"),
            ("藏品数据库", "archive:collectibles"),
            ("成就数据库", "archive:achievements"),
            ("设置", "settings"),
            ("结局·BE", "ending:BE"),
            ("结局·TE", "ending:TE"),
            ("结局·HE", "ending:HE"),
        ]
        for index, (label, target) in enumerate(targets):
            column = index % 6
            row = index // 6
            rect = pygame.Rect(
                x0 + column * (button_width + gap),
                y + row * 54,
                button_width,
                button_height,
            )
            draw_button(screen, rect, label, font, variant="secondary")
            self.developer_buttons.append((target, rect))

        level_y = y + 140
        heading = get_font(self.game.font_cache, "caption").render(
            "普通关卡", True, UI_COLORS["accent"]
        )
        screen.blit(heading, (x0, level_y))
        for index, level_id in enumerate(MAIN_LEVEL_IDS):
            column = index % 9
            row = index // 9
            rect = pygame.Rect(
                x0 + column * 108, level_y + 36 + row * 58, 94, button_height
            )
            draw_button(screen, rect, f"第 {level_id} 关", font, variant="primary")
            self.developer_buttons.append((f"level:{level_id}", rect))
