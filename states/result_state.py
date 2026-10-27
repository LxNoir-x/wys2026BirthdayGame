"""关卡结算状态。"""

from __future__ import annotations

import random

import pygame

from config import STORY_MAX_HEALTH
from states.game_state import GameState
from states.main_menu_state import MainMenuState
from utils.ui_art import asset_path, draw_image, load_image, scaled_image
from utils.ui_theme import UI_COLORS, fit_text, get_font

# 每关结算立绘：关卡 -> 立绘文件名（对应 assets/images/ui/result/characters/）。
LEVEL_CHARACTERS = {
    0: "维云斯",
    1: "流星飞",
    2: "剑圣",
    3: "时差",
    5: "里雪",
    6: "号角鸽",
    7: "萧然",
    8: "e某人",
    9: "霍里",
    11: "血狼",
    12: "笋干",
    13: "sweep",
    14: "冰",
    15: "粽子",
    16: "msc",
    17: "子龙",
    19: "鬼",
    20: "odd",
}
# BE 立绘仅个别角色与正常人形不同名。
BE_CHARACTERS = {14: "阿冰"}

# 结算示意图的按钮/信息条布局（与导出素材同源，按 1280x720 换算）。
PANEL_RECT = (36, 59, 866, 565)
CHIP_ORIGIN = (101, 241, 149, 41)
CHIP_STEP = 174.7
STAR_ORIGIN = (276, 340, 60, 63)
STAR_STEP = 156.0
BUTTON_ORIGIN = (90, 527, 243, 49)
BUTTON_STEP = 261.3
# 剪影素材缺失时的兜底恢复区域：只把这一段的立绘稿盖回按钮之上。
CHARACTER_OVERLAP_RECT = pygame.Rect(720, 510, 560, 90)
# 人像区的红框装饰素材（PSD「装饰框」图层 382x370），画在所有图层最上层。
# 落位由 PSD bbox (1345,121,1727,491) 按 2/3 换算，作为各角色的基准位置。
RESULT_RED_FRAME_ASSET = "images/ui/result/decoration.png"
RESULT_RED_FRAME_RECT = pygame.Rect(897, 81, 255, 247)
# 正常形态下各角色红框相对基准位置的位移（向右为 +dx，向上为 -dy）。
# 键与 LEVEL_CHARACTERS 的立绘文件名一致；未列出的角色沿用基准位置。
RED_FRAME_NORMAL_OFFSETS = {
    "维云斯": (20, -60),
    "萧然": (-15, -60),
    "msc": (-9, -45),
    "霍里": (0, -45),
    "粽子": (0, -60),
    "流星飞": (0, -60),
    "时差": (0, -60),
    "里雪": (0, -35),
    "冰": (0, -60),
    "号角鸽": (0, -40),
    "血狼": (15, -51),
    "剑圣": (95, -60),
    "e某人": (0, -35),
    "笋干": (10, -60),
    "子龙": (0, -45),
    "鬼": (60, -9),
    "odd": (0, -60),
}

# 不绘制红框的角色：sweep 的 normal/be 立绘都不加红框，其余角色一律加。
RED_FRAME_SKIP = frozenset({"sweep"})
# BE 形态下额外不绘制红框的角色（当前无；保留该开关便于个别角色临时撤框）。
RED_FRAME_BE_SKIP = frozenset()

# BE 形态下各角色红框相对基准位置的位移（向右为 +dx，向上为 -dy）。
# 键与 LEVEL_CHARACTERS 的立绘文件名一致；未列出的角色沿用基准位置。
RED_FRAME_BE_OFFSETS = {
    "维云斯": (0, 0),
    "萧然": (-15, 15),
    "msc": (0, -10),
    "霍里": (-5, 50),
    "粽子": (-10, 0),
    "流星飞": (-38, 98),
    "时差": (-40, 0),
    "里雪": (-20, -10),
    "冰": (5, -30),
    "血狼": (-122, 66),
    "剑圣": (-111, 51),
    "e某人": (40, -30),
    "笋干": (0, -45),
    "子龙": (-35, 15),
    "鬼": (10, -7),
    "odd": (-20, -40),
    "号角鸽": (0, -40),
}

# 硬化后的角色剪影缓存：键为 (剪影资源, 宽, 高)。
_HARD_MASK_CACHE: dict[tuple[str, int, int], pygame.Surface] = {}
# 强制不透明的立绘稿缓存：键为 (立绘资源, 宽, 高)。
_OPAQUE_BASE_CACHE: dict[tuple[str, int, int], pygame.Surface] = {}


def _opaque_scaled(asset, size):
    """缩放立绘稿并强制 alpha=255。

    立绘稿本身完全不透明，但 smoothscale 会把 alpha 从 255 降到 253：先画底图
    时整幅被压暗 1，之后 `_draw_character_over` 回贴的像素却是原亮度，于是被回
    贴的区域比周围"亮 1"，形成带硬边的矩形痕迹（剪影导出时闭合的红框轮廓被
    `fill_enclosed_holes` 填实成实心矩形，痕迹正好落在两个装饰框矩形上）。
    强制不透明后，回贴即逐像素精确覆盖，痕迹消失。
    """

    key = (asset, size[0], size[1])
    cached = _OPAQUE_BASE_CACHE.get(key)
    if cached is None:
        cached = scaled_image(asset, size).copy()
        alpha = pygame.surfarray.pixels_alpha(cached)
        alpha[:] = 255
        del alpha
        _OPAQUE_BASE_CACHE[key] = cached
    return cached


# 缩放并硬化 alpha 后的红框缓存：键为 (宽, 高)。
_RED_FRAME_CACHE: dict[tuple[int, int], pygame.Surface] = {}
# alpha 硬化阈值：低于该值的缩放插值像素直接丢弃，避免细线糊成一团。
_RED_FRAME_ALPHA_THRESHOLD = 80


def _scaled_red_frame(size):
    """把红框素材缩放到目标尺寸并硬化 alpha。

    素材是一条细红线，smoothscale 到 2/3 尺寸后每个可见像素都会被插值成
    半透明（实测 alpha 均值仅约 162），贴上去像被擦淡/糊掉；这里把 alpha
    还原为不透明，保住细线的清晰度（素材透明像素本身是橙红色，不会产生黑边）。
    """

    key = (size[0], size[1])
    cached = _RED_FRAME_CACHE.get(key)
    if cached is None:
        import numpy as np

        cached = pygame.transform.smoothscale(load_image(RESULT_RED_FRAME_ASSET), size)
        alpha = pygame.surfarray.pixels_alpha(cached)
        alpha[:] = np.where(alpha >= _RED_FRAME_ALPHA_THRESHOLD, 255, 0)
        del alpha
        _RED_FRAME_CACHE[key] = cached
    return cached


def _mask_asset(art_asset):
    """由立绘稿路径推出同名的剪影路径（characters/ 下多一层 masks/）。"""

    return art_asset.replace("characters/", "characters/masks/", 1)


class ResultState(GameState):
    # 结算图从全黑淡入的时长，避免过场/黑屏结束后画面“蹦出来”。
    INTRO_FADE_SECONDS = 0.5

    def __init__(
        self,
        game,
        level,
        stars,
        time_str,
        story_mode=False,
        story_index=None,
        entry_damage_count=None,
        entry_te_eligible=None,
    ):
        super().__init__(game)
        self.level = level
        self.stars = stars
        self.time_str = time_str
        self.story_mode = story_mode
        self.story_index = story_index
        self.entry_damage_count = entry_damage_count
        self.entry_te_eligible = entry_te_eligible

        self.chip_rects = [
            pygame.Rect(
                CHIP_ORIGIN[0] + round(index * CHIP_STEP), CHIP_ORIGIN[1],
                CHIP_ORIGIN[2], CHIP_ORIGIN[3],
            )
            for index in range(3)
        ]
        self.star_rects = [
            pygame.Rect(
                STAR_ORIGIN[0] + round(index * STAR_STEP), STAR_ORIGIN[1],
                STAR_ORIGIN[2], STAR_ORIGIN[3],
            )
            for index in range(3)
        ]
        self.button_rects = [
            pygame.Rect(
                BUTTON_ORIGIN[0] + round(index * BUTTON_STEP), BUTTON_ORIGIN[1],
                BUTTON_ORIGIN[2], BUTTON_ORIGIN[3],
            )
            for index in range(3)
        ]
        self.restart_rect = self.button_rects[0]
        self.next_rect = self.button_rects[1]
        self.menu_rect = self.button_rects[2]
        self.selected_index = None

        # 理智动摇时，立绘在正常/BE 之间以不可预判的录像故障节奏切换。
        self.flicker_timer = 0.0
        self.flicker_show_be = False
        self.flicker_interval = random.uniform(0.8, 2.0)
        self.glitch_time = 0.0
        self.glitch_duration = 0.0
        self._scanlines = None
        self.intro_elapsed = 0.0

    # ==================== 立绘选择 ====================

    @staticmethod
    def _exists(relative_path):
        try:
            return asset_path(relative_path).exists()
        except (OSError, ValueError):
            return False

    def _normal_asset(self):
        name = LEVEL_CHARACTERS.get(self.level, "维云斯")
        return f"images/ui/result/characters/normal/{name}.png"

    def _level_be_asset(self):
        """本关立绘对应的 BE 版本；个别关缺 BE 素材时回退本关正常立绘。"""

        name = BE_CHARACTERS.get(self.level, LEVEL_CHARACTERS.get(self.level, "维云斯"))
        asset = f"images/ui/result/characters/be/{name}.png"
        return asset if self._exists(asset) else self._normal_asset()

    def _flicker_active(self):
        return bool(
            not self.game.sanity_broken
            and not self._mental_broken()
            and self.story_mode
            and self.game.story_session.get("mental_flicker")
        )

    def _mental_broken(self):
        """血量剩余 3 检定失败：结算固定使用 BE 立绘，不再闪烁。"""

        return bool(self.game.story_session.get("mental_broken"))

    def _in_protection(self):
        """是否处于保护模式：与主线结算口径一致（剧情恢复或理智崩坏永久锁定）。

        保护模式由致命伤害触发时会同时写入 sanity_broken；从恢复存档继续时
        只有 recovery_mode，因此两处都要判断，否则保护模式下会错画成正常立绘。
        """

        return bool(
            self.game.sanity_broken
            or self.game.story_session.get("recovery_mode")
        )

    def _base_form(self):
        """当前显示的立绘形态：'be'（理智崩坏 / 保护模式 / 故障切到 BE）或 'normal'。"""

        if (
            self._mental_broken()
            or self._in_protection()
            or (self._flicker_active() and self.flicker_show_be)
        ):
            return "be"
        return "normal"

    def _base_asset(self):
        if self._base_form() == "be":
            return self._level_be_asset()
        return self._normal_asset()

    def _base_mask_asset(self):
        return _mask_asset(self._base_asset())

    def _red_frame_rect(self):
        """当前立绘下红框的落位；返回 None 表示该角色不绘制红框。"""

        name = LEVEL_CHARACTERS.get(self.level, "维云斯")
        if name in RED_FRAME_SKIP:
            return None
        if self._base_form() == "be":
            if name in RED_FRAME_BE_SKIP:
                return None
            dx, dy = RED_FRAME_BE_OFFSETS.get(name, (0, 0))
        else:
            dx, dy = RED_FRAME_NORMAL_OFFSETS.get(name, (0, 0))
        return RESULT_RED_FRAME_RECT.move(dx, dy)

    def update(self, dt):
        self.intro_elapsed = min(
            self.INTRO_FADE_SECONDS, self.intro_elapsed + max(0.0, float(dt))
        )
        if self._flicker_active():
            self.glitch_time = max(0.0, self.glitch_time - dt)
            self.flicker_timer += dt
            if self.flicker_timer >= self.flicker_interval:
                self.flicker_timer = 0.0
                self.flicker_show_be = not self.flicker_show_be
                self.flicker_interval = random.uniform(0.8, 2.0)
                self.glitch_duration = random.uniform(0.08, 0.15)
                self.glitch_time = self.glitch_duration
        else:
            self.flicker_show_be = False
            self.glitch_time = 0.0

    # ==================== 输入 ====================

    def handle_events(self, events):
        for event in events:
            if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
                continue
            if self.restart_rect.collidepoint(event.pos):
                self._activate(0)
            elif self.next_rect.collidepoint(event.pos):
                self._activate(1)
            elif self.menu_rect.collidepoint(event.pos):
                self._activate(2)

    def _activate(self, index):
        if index == 0:
            if self.story_mode:
                if self.entry_damage_count is not None:
                    self.game.story_session.update(
                        {
                            "damage_count": self.entry_damage_count,
                            "san": self.game._san_for_damage_count(
                                self.entry_damage_count
                            ),
                            "health": self.game.get_story_health()
                            if self.game.story_session.get("recovery_mode")
                            else max(1, STORY_MAX_HEALTH - self.entry_damage_count),
                            "te_eligible": self.entry_te_eligible,
                        }
                    )
                self.game.launch_story_level(self.level, self.story_index)
            elif (
                self.game.story_session.get("active")
                and self.entry_damage_count is not None
            ):
                # 主线进行中重打旧关：重新开始前把主线状态回滚到进入本关时，
                # 重打中累计的受伤不能通过反复重开泄漏进主线进度。
                self.game.story_session.update(
                    {
                        "damage_count": self.entry_damage_count,
                        "san": self.game._san_for_damage_count(
                            self.entry_damage_count
                        ),
                        "health": self.game.get_story_health()
                        if self.game.story_session.get("recovery_mode")
                        else max(1, STORY_MAX_HEALTH - self.entry_damage_count),
                        "te_eligible": self.entry_te_eligible,
                    }
                )
                self.game.save_progress()
                from states.play_state import PlayState

                self.game.change_state(
                    PlayState(
                        self.game,
                        self.level,
                        entry_damage_count=self.entry_damage_count,
                        entry_te_eligible=self.entry_te_eligible,
                    )
                )
            else:
                from states.play_state import PlayState

                self.game.change_state(PlayState(self.game, self.level))
            return
        if index == 1:
            if self.story_mode:
                self.game.advance_story()
            elif self.game.story_session.get("active"):
                # 主线进行中重打旧关：不推进主线，回到关卡选择页面。
                from states.level_select_state import LevelSelectState

                self.game.change_state(LevelSelectState(self.game))
            else:
                from states.level_select_state import LevelSelectState
                from states.play_state import PlayState

                next_level = self.game.next_level_without_stars()
                if next_level is None:
                    # 自由挑战没有结局：除 S 关外全部拿星后回到追忆选关。
                    self.game.change_state(LevelSelectState(self.game))
                else:
                    # 还有没拿到星星的关卡：下一关直接跳到其中一关。
                    self.game.change_state(PlayState(self.game, next_level))
            return
        self.game.change_state(MainMenuState(self.game))

    # ==================== 绘制 ====================

    def draw(self, screen):
        scene = pygame.Surface(screen.get_size()).convert()
        base = _opaque_scaled(self._base_asset(), screen.get_size())
        scene.blit(base, (0, 0))
        self._draw_info(scene)
        self._draw_stars(scene)
        self._draw_buttons(scene)
        self._draw_character_over(scene, base)

        self._present_scene(screen, scene)
        # 人像红框装饰画在所有图层最上层，确保始终可见、不被擦除。
        red_frame = self._red_frame_rect()
        if red_frame is not None:
            screen.blit(_scaled_red_frame(red_frame.size), red_frame)
        self._draw_intro_fade(screen)

    def _draw_intro_fade(self, screen):
        """结算图入场：从全黑 0.5s 淡入。"""

        if self.intro_elapsed >= self.INTRO_FADE_SECONDS:
            return
        progress = self.intro_elapsed / self.INTRO_FADE_SECONDS
        alpha = round(255 * (1 - progress))
        if alpha <= 0:
            return
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, alpha))
        screen.blit(overlay, (0, 0))

    def _patch_panel(self, screen, panel, rect):
        local = pygame.Rect(
            rect.x - PANEL_RECT[0],
            rect.y - PANEL_RECT[1],
            rect.width,
            rect.height,
        )
        screen.blit(panel, rect.topleft, local)

    def _draw_info(self, screen):
        panel = scaled_image("images/ui/result/panel.png", PANEL_RECT[2:])
        labels = (
            f"用时  {self.time_str}",
            f"星级  {self.stars}/3",
            "主线记录" if self.story_mode else "自由挑战",
        )
        caption = get_font(self.game.font_cache, "caption")
        for rect, label in zip(self.chip_rects, labels):
            patch = rect.inflate(8, 8)
            self._patch_panel(screen, panel, patch)
            draw_image(screen, "images/ui/result/chip_frame.png", rect, smooth=True)
            text = fit_text(caption, label, rect.width - 18, UI_COLORS["text"])
            screen.blit(text, text.get_rect(center=rect.center))

    def _draw_stars(self, screen):
        panel = scaled_image("images/ui/result/panel.png", PANEL_RECT[2:])
        for index, rect in enumerate(self.star_rects):
            self._patch_panel(screen, panel, rect.inflate(10, 10))
            if index < self.stars:
                draw_image(
                    screen,
                    "images/ui/result/star_core.png",
                    pygame.Rect(rect.x + 3, rect.y + 5, 54, 55),
                    smooth=False,
                )
            draw_image(screen, "images/ui/result/star_outline.png", rect, smooth=False)

    def _draw_buttons(self, screen):
        next_label = "进入下一关" if self.story_mode else "下一关"
        button_font = get_font(self.game.font_cache, "button")
        mouse_pos = pygame.mouse.get_pos()
        for rect, label in (
            (self.button_rects[0], "重新开始"),
            (self.button_rects[1], next_label),
            (self.button_rects[2], "主菜单"),
        ):
            draw_image(screen, "images/ui/result/button_base.png", rect, smooth=True)
            if rect.collidepoint(mouse_pos):
                draw_image(
                    screen,
                    "images/ui/result/button_selected.png",
                    rect,
                    smooth=True,
                )
            label_surface = fit_text(
                button_font, label, rect.width - 24, UI_COLORS["text"]
            )
            screen.blit(label_surface, label_surface.get_rect(center=rect.center))

    def _draw_character_over(self, scene, base):
        """把角色重新盖回动态按钮之上，按钮的描边不会压到立绘。

        剪影由 tools/export_result_masks.py 从结算 PSD 导出：立绘稿与"只有
        界面"的参考图逐像素做差即得角色像素，暗色衣袖同样能正确识别，因此
        不会再出现按钮黑白边画到立绘上层的问题。
        """

        mask = self._character_mask(scene.get_size())
        if mask is None:
            # 剪影缺失时退回整块恢复，至少不会把按钮画到角色上。
            scene.blit(base, CHARACTER_OVERLAP_RECT, CHARACTER_OVERLAP_RECT)
            return
        # 直接取剪影的 alpha 作为回贴蒙版，不要用 BLEND_RGBA_MULT：MULT 在
        # pygame 里按 /256 取整，即使 alpha=255 也会把像素压暗约 1，剪影里被
        # fill_enclosed_holes 填实的红框矩形就会呈现为一整块"暗 1"的硬边痕迹。
        layer = base.copy()
        layer_alpha = pygame.surfarray.pixels_alpha(layer)
        layer_alpha[:] = pygame.surfarray.array_alpha(mask)
        del layer_alpha
        scene.blit(layer, (0, 0))

    def _character_mask(self, size):
        """载入剪影并硬化为 0/255 遮罩（alpha 即角色覆盖范围）。

        剪影经 smoothscale 缩放后不会留下 alpha=255 的像素（实测最大仅 253），
        轮廓上还有约 2500 个半透明像素；用它们做 BLEND_RGBA_MULT 回贴时，角色
        会被整体压成半透明、轮廓处透出底下的按钮，看起来像被擦除或糊掉。
        因此先按 128 阈值把 alpha 硬化，回贴时角色像素才完整不透明。
        """

        try:
            asset = self._base_mask_asset()
        except (FileNotFoundError, OSError, pygame.error):
            return None
        key = (asset, size[0], size[1])
        cached = _HARD_MASK_CACHE.get(key)
        if cached is None:
            import numpy as np

            try:
                cached = scaled_image(asset, size).copy()
            except (FileNotFoundError, OSError, pygame.error):
                return None
            alpha = pygame.surfarray.pixels_alpha(cached)
            alpha[:] = np.where(alpha >= 128, 255, 0)
            del alpha
            _HARD_MASK_CACHE[key] = cached
        return cached

    def _present_scene(self, screen, scene):
        """合成低亮度机械故障、撕裂、色差和常驻 CRT 纹理。"""

        if not self._flicker_active():
            screen.blit(scene, (0, 0))
            return

        width, height = screen.get_size()
        jitter_x = random.randint(-3, 3) if self.glitch_time > 0 else 0
        jitter_y = random.randint(-2, 2) if self.glitch_time > 0 else 0
        screen.fill((0, 0, 0))

        if self.glitch_time > 0:
            red = scene.copy()
            red.fill((255, 42, 42), special_flags=pygame.BLEND_RGB_MULT)
            red.set_alpha(34)
            cyan = scene.copy()
            cyan.fill((42, 235, 255), special_flags=pygame.BLEND_RGB_MULT)
            cyan.set_alpha(28)
            screen.blit(red, (jitter_x - 3, jitter_y))
            screen.blit(cyan, (jitter_x + 3, jitter_y))

        screen.blit(scene, (jitter_x, jitter_y))
        if self.glitch_time > 0:
            for _index in range(random.randint(2, 5)):
                strip_height = random.randint(4, 18)
                strip_y = random.randint(0, max(0, height - strip_height))
                offset = random.randint(-14, 14)
                source = pygame.Rect(0, strip_y, width, strip_height)
                screen.blit(scene, (offset, strip_y + jitter_y), source)

            flash = pygame.Surface((width, height), pygame.SRCALPHA)
            if random.random() < 0.82:
                flash.fill((0, 0, 0, random.randint(28, 62)))
            else:
                flash.fill((255, 255, 255, random.randint(10, 22)))
            screen.blit(flash, (0, 0))

        self._draw_signal_texture(screen)

    def _draw_signal_texture(self, screen):
        size = screen.get_size()
        if self._scanlines is None or self._scanlines.get_size() != size:
            self._scanlines = pygame.Surface(size, pygame.SRCALPHA)
            for y in range(0, size[1], 3):
                pygame.draw.line(
                    self._scanlines,
                    (7, 18, 20, 15),
                    (0, y),
                    (size[0], y),
                )
        screen.blit(self._scanlines, (0, 0))

        noise = pygame.Surface((320, 180), pygame.SRCALPHA)
        for _index in range(180):
            value = random.randint(130, 220)
            noise.set_at(
                (random.randrange(320), random.randrange(180)),
                (value, value, value, random.randint(5, 14)),
            )
        screen.blit(pygame.transform.scale(noise, size), (0, 0))
