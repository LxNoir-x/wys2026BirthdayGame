import math
import random
import time

import pygame

from config import PLAYER_GRAVITY, SCREEN_HEIGHT, SCREEN_WIDTH, TARGET_DELTA
from entities.player import Player
from platforms.fragile_platform import EndlessFragilePlatform
from platforms.moving_platform import MovingPlatform
from platforms.static_platform import StaticPlatform
from platforms.surface_platform import IcePlatform, SwampPlatform
from states.game_state import GameState
from utils.keyboard_utils import KeyboardUtils
from utils.ui_art import draw_image, load_image, scaled_image
from utils.ui_theme import (
    UI_COLORS,
    draw_button,
    draw_panel,
    fit_text,
    get_font,
)

PLATFORM_ART = {
    "normal_0": "images/ui/endless/platforms/normal_0.png",
    "normal_1": "images/ui/endless/platforms/normal_1.png",
    "fragile": "images/ui/endless/platforms/fragile.png",
    "ice": "images/ui/endless/platforms/ice.png",
    "swamp": "images/ui/endless/platforms/swamp.png",
    "moving": "images/ui/endless/platforms/moving.png",
    "moving_rail": "images/ui/endless/platforms/moving_rail.png",
}
# 素材的原始高宽比（用于在保持外形的前提下缩放贴图）。
ART_RATIO = {
    "normal_0": 61 / 555,
    "normal_1": 196 / 274,
    "fragile": 75 / 56,
    "ice": 192 / 162,
    "swamp": 97 / 267,
    "moving": 125 / 210,
}

# 移动平台素材自上而下为：栏杆 → 车体 → 车轮。碰撞盒顶边应对齐车体顶边，
# 让玩家站在车体上而不是压在最顶端的栏杆上（素材实测车体顶边在 47/125 处）。
MOVING_BODY_TOP_RATIO = 47 / 125
# 移动平台轨道在素材高度中的位置与高度：对齐主线车体，让轨道位于车体中部，
# 而不是压在平台顶部的栏杆上。
MOVING_RAIL_CENTER_RATIO = 65 / 125
MOVING_RAIL_HEIGHT = 16

# PSD 原稿为 1920x1080，运行时先按 2/3 缩放到 1280x720；平台再乘 0.8 收缩，避免整尺寸过大。
DESIGN_SCALE = SCREEN_WIDTH / 1920 * 0.8
_DESIGN_SIZE_CACHE = {}


def _design_size(art_name):
    """返回平台素材按 PSD→运行时比例缩放后的设计尺寸。"""

    if art_name not in _DESIGN_SIZE_CACHE:
        image = load_image(PLATFORM_ART[art_name])
        _DESIGN_SIZE_CACHE[art_name] = (
            max(1, round(image.get_width() * DESIGN_SCALE)),
            max(1, round(image.get_height() * DESIGN_SCALE)),
        )
    return _DESIGN_SIZE_CACHE[art_name]


# 普通平台按设计尺寸显得过大，再额外收缩到 0.8 倍（贴图高度随宽度等比缩放）。
PLATFORM_EXTRA_SCALE = {
    "normal_0": 0.8,
    "normal_1": 0.8,
}


def _platform_width(art_name):
    """返回该平台在无尽关最终使用的碰撞/贴图宽度。"""

    width, _ = _design_size(art_name)
    return max(1, round(width * PLATFORM_EXTRA_SCALE.get(art_name, 1.0)))

FLOOD_DELAY_SECONDS = 10.0
FLOOD_BASE_SPEED = 82.0
# 数据流纹理的滚动速度（像素/毫秒）。
FLOOD_DATA_SCROLL_SPEED = 0.05

# 无尽关 HUD 布局，取自 ui_expect（PSD 1920x1080 设计，运行时按 2/3 还原）。
HUD_SCALE = SCREEN_WIDTH / 1920
HUD_LEFT_FRAME = pygame.Rect(18, 21, 345, 181)
HUD_LEFT_TITLE = pygame.Rect(37, 34, 106, 12)
HUD_ROW_LABEL_X = 77
HUD_ROW_LABEL_YS = (71, 108, 145)
# 行贴图里「标签」部分的宽度（设计像素），右侧的示例数值不使用。
HUD_ROW_LABELS = (
    ("left_height", 80),
    ("left_time", 80),
    ("left_history", 168),
)
# 动态数值右对齐的位置（对应设计里示例数值的右缘）。
HUD_ROW_VALUE_RIGHT = 304
HUD_RIGHT_FRAME = pygame.Rect(1094, 25, 147, 37)
HUD_RIGHT_PROGRESS = pygame.Rect(1137, 34, 62, 19)


class EndlessState(GameState):
    def __init__(self, game):
        super().__init__(game)
        self.player = Player(game)
        # 强制玩家位于窗口最底部正中央（站在地面上）
        self.player.rect.midbottom = (SCREEN_WIDTH // 2, SCREEN_HEIGHT)
        # 在无尽模式下允许玩家越过屏幕顶部以实现无限游玩
        self.player.allow_top_overflow = True

        self.start_baseline = self.player.rect.top

        self.platforms = []          # 所有平台
        self.decorations = []        # 无碰撞贴图（索道滑轨等）
        self.camera_y = 0             # 相机偏移，初始为0，玩家显示在底部
        self.score = 0
        self.last_time = time.time()
        self.start_time = time.time()
        self.elapsed = 0.0
        self.best_score = int(game.save_data.get("endless_best_height", 0))
        self.highest_y = SCREEN_HEIGHT
        self.last_spawn_ref = None

        # 黑色数据流：开爬 10 秒后开始上涨，触碰即淘汰。
        self.flood_y = float(SCREEN_HEIGHT)
        self.flood_active = False

        self.game_over = False
        self.game_over_buttons = {}
        self.selected_button = 0

        self._init_platforms()
        self.highest_y = self.start_baseline
        self.score = 0

        # 直接采用玩家真实参数推算可达距离，避免与 Player 的手感不一致。
        self.gravity_per_frame = PLAYER_GRAVITY
        self.player_max_horiz_speed = float(self.player.run_speed)
        self.player_max_jump_v = math.sqrt(2 * PLAYER_GRAVITY * self.player.jump_height)
        self.max_vertical_reach = self._discrete_jump_height()
        time_to_apex = self.player_max_jump_v / self.gravity_per_frame
        self.max_horizontal_reach = int(self.player_max_horiz_speed * time_to_apex * 0.95)
        # 生成新平台时对垂直间距再留余量，保证玩家能跳上去并调整落点。
        self.platform_jump_margin = 0.8

        self.paused = False
        self.debug_overlay_enabled = False
        self.has_left_ground = False

    def _discrete_jump_height(self):
        """按玩家逐帧积分的方式计算实际最大跳跃高度。"""

        height = 0.0
        vy = -self.player_max_jump_v
        while vy < 0:
            vy += self.gravity_per_frame
            if vy >= 0:
                break
            height -= vy
        return height

    # ==================== 平台构造 ====================

    def _make_platform(self, kind, x, y, width, height=15):
        if kind == "fragile":
            return EndlessFragilePlatform(
                x, y, width, height, PLATFORM_ART["fragile"], (0, 0),
                (width, max(20, int(width * ART_RATIO["fragile"]))),
            )
        if kind == "swamp":
            return SwampPlatform(
                x, y, width, height, PLATFORM_ART["swamp"], (0, 0),
                (width, max(18, int(width * ART_RATIO["swamp"]))),
                movement_multiplier=0.6, jump_multiplier=0.7,
            )
        if kind == "ice":
            return IcePlatform(
                x, y, width, height, PLATFORM_ART["ice"], (0, 0),
                (width, max(18, int(width * ART_RATIO["ice"]))),
                movement_multiplier=1.5, jump_multiplier=1.5,
            )
        normal = kind if kind in ("normal_0", "normal_1") else random.choice(
            ("normal_0", "normal_1")
        )
        art = PLATFORM_ART[normal]
        # 普通平台同样按素材原始比例缩放，避免被压进 15px 碰撞框而挤压缩小。
        art_size = (width, max(12, int(width * ART_RATIO[normal])))
        return StaticPlatform(
            pygame.Rect(x, y, width, height), art_path=art, art_size=art_size
        )

    def _make_moving(self, x, y, width, speed, travel):
        art_size = (width, max(18, int(width * ART_RATIO["moving"])))
        # 运动行程（同时就是滑轨长度）必须落在窗口内：平台右缘最多到达窗口右缘，
        # 否则平台与滑轨会滑出屏幕外。
        travel = max(0, min(travel, SCREEN_WIDTH - width - x))
        # 贴图整体上移，使素材里的车体顶边正好落在碰撞盒顶边（y）上：
        # 玩家沿碰撞盒站立即站在车体上，护栏位于脚下之上。
        body_top_offset = -round(art_size[1] * MOVING_BODY_TOP_RATIO)
        platform = MovingPlatform(
            x, y, width, 15, speed, travel,
            art_path=PLATFORM_ART["moving"], art_offset=(0, body_top_offset),
            art_size=art_size,
        )
        # 索道滑轨只做视觉装饰，没有碰撞体，允许玩家上下穿越。
        # 与主线一致：轨道位于车体中部，避免压住顶部栏杆；
        # 长度正好覆盖平台左右移动的行程：极限位置并集为 [x, x + travel + width]。
        rail_center_y = y + round(
            art_size[1] * (MOVING_RAIL_CENTER_RATIO - MOVING_BODY_TOP_RATIO)
        )
        rail_rect = pygame.Rect(
            x,
            rail_center_y - MOVING_RAIL_HEIGHT // 2,
            travel + width,
            MOVING_RAIL_HEIGHT,
        )
        self.decorations.append(
            {"rect": rail_rect, "art": PLATFORM_ART["moving_rail"]}
        )
        return platform

    def _init_platforms(self):
        """在玩家上方生成几层初始平台，让玩家开始攀登"""
        base_y = SCREEN_HEIGHT - 100
        gap = 80
        for i in range(5):
            y = base_y - i * gap
            if i == 1:
                kind = "ice"
            elif i == 2:
                kind = "swamp"
            else:
                kind = "normal_0"
            width = _platform_width(kind)
            x = random.randint(SCREEN_WIDTH // 2 - 100, SCREEN_WIDTH // 2 + 100)
            x = max(40, min(SCREEN_WIDTH - width - 40, x))
            self.platforms.append(self._make_platform(kind, x, y, width))
            self.highest_y = min(self.highest_y, y)

    # ==================== 输入 ====================

    def handle_events(self, events):
        for event in events:
            if self.game_over:
                self._handle_game_over_event(event)
                continue
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F12:
                    self.debug_overlay_enabled = not self.debug_overlay_enabled
                    continue
                if event.key == pygame.K_ESCAPE:
                    from states.settings_state import SettingsState

                    self.game.change_state(
                        SettingsState(self.game, return_state=self, initial_tab="operations")
                    )
                elif event.key in (pygame.K_SPACE, pygame.K_w):
                    self.player.jump()

    def _handle_game_over_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_a):
                self.selected_button = (self.selected_button - 1) % 2
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.selected_button = (self.selected_button + 1) % 2
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self._activate_game_over(self.selected_button)
        elif event.type == pygame.MOUSEMOTION:
            for index, rect in enumerate(self.game_over_buttons.values()):
                if rect.collidepoint(event.pos):
                    self.selected_button = index
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for index, rect in enumerate(self.game_over_buttons.values()):
                if rect.collidepoint(event.pos):
                    self._activate_game_over(index)

    def _activate_game_over(self, index):
        if index == 0:
            self.game.change_state(EndlessState(self.game))
            return
        from states.main_menu_state import MainMenuState

        self.game.change_state(MainMenuState(self.game))

    # ==================== 更新 ====================

    def update(self, dt):
        current_time = time.time()
        dt = current_time - self.last_time
        if dt < TARGET_DELTA:
            pygame.time.wait(int((TARGET_DELTA - dt) * 1000))
            dt = TARGET_DELTA
        self.last_time = current_time

        if self.game_over:
            self.elapsed = self._ended_elapsed
            return

        keys = KeyboardUtils.get_keys_pressed()
        if keys['w'] or keys['space'] or keys['up']:
            self.player.jump()

        for plat in self.platforms:
            plat.update(dt, player_rect=self.player.rect)

        self.player.update(self.platforms, None, None, dt=dt)
        self.elapsed = time.time() - self.start_time

        self.highest_y = min(self.highest_y, self.player.rect.top)

        desired_above = 8
        num_above = sum(1 for p in self.platforms if p.rect.y < self.player.rect.top)
        while num_above < desired_above:
            ref = min(p.rect.y for p in self.platforms) if self.platforms else self.player.rect.top
            self._spawn_platform_above(ref)
            num_above += 1
        if self.platforms:
            self.last_spawn_ref = None

        if self.player.rect.centery < SCREEN_HEIGHT * 2 // 3:
            target_camera = self.player.rect.centery - SCREEN_HEIGHT // 2
        else:
            target_camera = 0

        lerp_speed = 10.0
        t = min(lerp_speed * dt, 1.0)
        self.camera_y += (target_camera - self.camera_y) * t

        self._clean_below()
        self._update_flood(dt)

        self.score = max(0, int((self.start_baseline - self.highest_y) // 10))
        self.game.achievement_system.check_achievement("reach_height_325", self.score)
        self.game.achievement_system.check_achievement("reach_height_1020", self.score)
        self.game.achievement_system.check_achievement("reach_height_1136", self.score)
        self.game.achievement_system.check_achievement("reach_height_3809", self.score)

        if self.game_over:
            return

        if (
            not self.flood_active
            and self.has_left_ground
            and self.player.rect.bottom >= SCREEN_HEIGHT - 5
        ):
            self._reset_climb()
            return

        if self.player.rect.bottom < SCREEN_HEIGHT - 5:
            self.has_left_ground = True

    def _update_flood(self, dt):
        if not self.flood_active:
            if self.elapsed < FLOOD_DELAY_SECONDS:
                return
            self.flood_active = True
        difficulty = min(1.0, self.score / 2000.0)
        self.flood_y -= (FLOOD_BASE_SPEED + 30.0 * difficulty) * dt
        if self.player.rect.bottom >= self.flood_y:
            self._game_over()

    def _game_over(self):
        if self.game_over:
            return
        self.game_over = True
        self._ended_elapsed = self.elapsed
        self.best_score = max(self.best_score, self.score)
        self.game.save_data["endless_best_height"] = self.best_score
        self.game.save_progress()

    def _reset_climb(self):
        """跌落到底部（数据流尚未上涨时）保留记录并从初始路线重新开始。"""

        self.best_score = max(self.best_score, self.score)
        self.game.save_data["endless_best_height"] = self.best_score
        self.game.save_progress()

        self.player = Player(self.game)
        self.player.rect.midbottom = (SCREEN_WIDTH // 2, SCREEN_HEIGHT)
        self.player.allow_top_overflow = True
        self.platforms = []
        self.decorations = []
        self.camera_y = 0
        self.score = 0
        self.start_baseline = self.player.rect.top
        self.highest_y = self.start_baseline
        self.last_spawn_ref = None
        self.has_left_ground = False
        self._init_platforms()
        self.highest_y = self.start_baseline
        self.game.ui_manager.show_toast(
            "重新攀登",
            "已跌回起点，攀爬高度重新计数。",
            UI_COLORS["gold"],
        )

    def _spawn_platform_above(self, reference_y):
        if not self.platforms:
            ref_x = max(80, min(SCREEN_WIDTH - 180, self.player.rect.x))
            ref_y = self.player.rect.top
        else:
            ref_plat = min(self.platforms, key=lambda p: p.rect.y)
            ref_y = ref_plat.rect.y
            ref_x = ref_plat.rect.x

        current_height = self.score
        difficulty = min(1.0, current_height / 2000.0)

        min_gap = 60 + int(40 * difficulty)
        max_gap = min(
            int(self.max_vertical_reach * self.platform_jump_margin),
            min_gap + 70 + int(30 * difficulty),
        )
        max_gap = max(min_gap, max_gap)

        moving_probability = 0.20 + 0.25 * difficulty if current_height > 300 else 0.0
        swamp_probability = 0.08 + 0.12 * difficulty if current_height > 500 else 0.0
        ice_probability = 0.10 + 0.08 * difficulty if current_height > 200 else 0.0
        fragile_probability = 0.10 + 0.10 * difficulty if current_height > 400 else 0.0

        roll = random.random()
        if roll < moving_probability:
            kind = "moving"
        elif roll < moving_probability + swamp_probability:
            kind = "swamp"
        elif roll < moving_probability + swamp_probability + ice_probability:
            kind = "ice"
        elif roll < (
            moving_probability + swamp_probability + ice_probability + fragile_probability
        ):
            kind = "fragile"
        else:
            kind = random.choice(("normal_0", "normal_1"))

        # 平台宽度取素材设计尺寸（PSD 1920x1080 按 2/3 还原），普通平台再额外收缩。
        width = _platform_width(kind)

        max_horiz = int(self.max_horizontal_reach * (0.55 + 0.25 * difficulty))
        max_horiz = max(1, max_horiz)

        source_platform = min(self.platforms, key=lambda p: p.rect.y) if self.platforms else None
        x = max(40, min(SCREEN_WIDTH - width - 40, ref_x))
        new_y = ref_y - min_gap
        placed = False
        if source_platform is not None:
            for _ in range(16):
                gap = random.randint(min_gap, max_gap)
                candidate_y = ref_y - gap
                candidate_x = ref_x + random.randint(-max_horiz, max_horiz)
                candidate_x = max(40, min(SCREEN_WIDTH - width - 40, candidate_x))
                if self._is_reachable(source_platform, candidate_x, candidate_y, width):
                    x = candidate_x
                    new_y = candidate_y
                    placed = True
                    break
            if not placed:
                x, new_y = self._fallback_placement(
                    source_platform, width, min_gap, ref_y
                )

        if kind == "moving":
            speed = random.uniform(1.5 + difficulty, 3.0 + difficulty)
            travel = random.randint(150, 250)
            plat = self._make_moving(x, new_y, width, speed, travel)
        else:
            plat = self._make_platform(kind, x, new_y, width)

        self.platforms.append(plat)
        return True

    def _is_reachable(self, source_platform, x, y, width):
        """判断玩家是否能从下方平台跳到目标矩形 (x, y, width)。

        平台是实体，玩家头顶会被上方平台底部挡住，因此当目标平台与下方平台
        水平重叠时，下方平台必须留出至少一个身位的净空作为起跳点，否则跳不上去。
        """

        vertical_gap = source_platform.rect.y - y
        if vertical_gap <= 0 or vertical_gap > self.max_vertical_reach * self.platform_jump_margin:
            return False

        target = pygame.Rect(x, y, width, 15)
        overlap = min(source_platform.rect.right, target.right) - max(
            source_platform.rect.left, target.left
        )
        if overlap <= 0:
            horizontal_gap = max(
                0,
                target.left - source_platform.rect.right,
                source_platform.rect.left - target.right,
            )
            return horizontal_gap <= self.max_horizontal_reach

        clear_left = min(source_platform.rect.right, target.left) - source_platform.rect.left
        clear_right = source_platform.rect.right - max(
            source_platform.rect.left, target.right
        )
        return max(clear_left, clear_right) >= self.player.rect.width

    def _fallback_placement(self, source_platform, width, min_gap, ref_y):
        """随机尝试失败后的保底位置：保证玩家一定能从下方平台跳上去。"""

        margin = 40
        sides = (
            source_platform.rect.right,
            source_platform.rect.left - width,
        )
        valid = [sx for sx in sides if margin <= sx <= SCREEN_WIDTH - width - margin]
        if valid:
            return random.choice(valid), ref_y - min_gap

        # 两侧都放不下时，放到下方平台正上方，并留出一个身位的起跳净空。
        clear = self.player.rect.width + 6
        x = max(margin, min(SCREEN_WIDTH - width - margin, source_platform.rect.left + clear))
        return x, ref_y - min_gap

    def _clean_below(self):
        threshold = self.camera_y + SCREEN_HEIGHT + 600
        self.platforms = [p for p in self.platforms if p.rect.y < threshold]
        self.decorations = [d for d in self.decorations if d["rect"].y < threshold]

    # ==================== 绘制 ====================

    def draw(self, screen):
        screen.blit(
            scaled_image("images/ui/endless/background.png", screen.get_size()),
            (0, 0),
        )

        for decoration in self.decorations:
            rect = decoration["rect"].copy()
            rect.y -= self.camera_y
            if -80 < rect.y < SCREEN_HEIGHT + 80:
                draw_image(screen, decoration["art"], rect, smooth=True)

        for plat in self.platforms:
            screen_rect = plat.rect.copy()
            screen_rect.y -= self.camera_y
            if -120 < screen_rect.y < SCREEN_HEIGHT + 120:
                original_y = plat.rect.y
                plat.rect.y = screen_rect.y
                plat.draw(screen, [])
                plat.rect.y = original_y

        player_screen_rect = self.player.rect.copy()
        player_screen_rect.y -= self.camera_y
        original_y = self.player.rect.y
        self.player.rect.y = player_screen_rect.y
        self.player.draw(screen, [])
        self.player.rect.y = original_y

        self._draw_flood(screen)
        self._draw_hud(screen)
        if self.game_over:
            self._draw_game_over(screen)
        if self.debug_overlay_enabled:
            from utils.debug_overlay import draw_debug_overlay

            draw_debug_overlay(screen, self)

    def _draw_flood(self, screen):
        if not self.flood_active:
            return
        surface_y = int(self.flood_y - self.camera_y)
        if surface_y >= SCREEN_HEIGHT:
            return
        surface_y = max(surface_y, -SCREEN_HEIGHT)
        height = SCREEN_HEIGHT - surface_y
        if height <= 0:
            return

        flood = pygame.Surface((SCREEN_WIDTH, height), pygame.SRCALPHA)

        # 黑色水体：water.png 顶部自带柔边，用作水面，下方用纯黑补满。
        water_image = load_image("images/ui/endless/blackflow/water.png")
        water_height = max(
            1, round(water_image.get_height() * SCREEN_WIDTH / water_image.get_width())
        )
        flood.blit(
            scaled_image(
                "images/ui/endless/blackflow/water.png", (SCREEN_WIDTH, water_height)
            ),
            (0, 0),
        )
        if height > water_height:
            flood.fill((0, 0, 0, 255), (0, water_height, SCREEN_WIDTH, height - water_height))

        # 数据流纹理：纵向平铺并随时间向上滚动，营造流动的数据感。
        data_image = load_image("images/ui/endless/blackflow/data.png")
        data_height = max(
            1, round(data_image.get_height() * SCREEN_WIDTH / data_image.get_width())
        )
        data_tile = scaled_image(
            "images/ui/endless/blackflow/data.png", (SCREEN_WIDTH, data_height)
        )
        offset = int(pygame.time.get_ticks() * FLOOD_DATA_SCROLL_SPEED) % data_height
        y = -offset
        while y < height:
            flood.blit(data_tile, (0, y))
            y += data_height

        flood.set_alpha(240)
        screen.blit(flood, (0, surface_y))

    def _draw_hud(self, screen):
        draw_image(
            screen, "images/ui/endless/hud/left_frame.png", HUD_LEFT_FRAME, smooth=True
        )
        draw_image(
            screen, "images/ui/endless/hud/left_title.png", HUD_LEFT_TITLE, smooth=True
        )

        # 高度/时间/历史是实时数值：用行贴图提供标签，数值用文字实时绘制。
        caption = get_font(self.game.font_cache, "caption")
        values = (
            (str(self.score), UI_COLORS["gold"]),
            (
                f"{int(self.elapsed // 60)}:{int(self.elapsed % 60):02d}",
                UI_COLORS["accent"],
            ),
            (str(self.best_score), UI_COLORS["text"]),
        )
        for (name, label_width), y, (value, color) in zip(
            HUD_ROW_LABELS, HUD_ROW_LABEL_YS, values
        ):
            self._draw_hud_label(screen, name, label_width, HUD_ROW_LABEL_X, y)
            value_x = HUD_ROW_LABEL_X + round(label_width * HUD_SCALE) + 8
            value_surface = fit_text(caption, value, HUD_ROW_VALUE_RIGHT - value_x, color)
            screen.blit(
                value_surface,
                value_surface.get_rect(right=HUD_ROW_VALUE_RIGHT, centery=y + 12),
            )

        draw_image(
            screen, "images/ui/endless/hud/right_frame.png", HUD_RIGHT_FRAME, smooth=True
        )
        draw_image(
            screen,
            "images/ui/endless/hud/right_progress.png",
            HUD_RIGHT_PROGRESS,
            smooth=True,
        )

    def _draw_hud_label(self, screen, name, design_width, x, y):
        """只取行贴图左侧的标签部分绘制（右侧示例数值不用）。"""

        image = load_image(f"images/ui/endless/hud/{name}.png")
        label = image.subsurface(pygame.Rect(0, 0, design_width, image.get_height()))
        size = (
            max(1, round(design_width * HUD_SCALE)),
            max(1, round(image.get_height() * HUD_SCALE)),
        )
        screen.blit(pygame.transform.smoothscale(label, size), (x, y))

    def _draw_game_over(self, screen):
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        screen.blit(overlay, (0, 0))

        panel = pygame.Rect(0, 0, 520, 320)
        panel.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        draw_panel(screen, panel, fill=(16, 22, 36), border=UI_COLORS["red"], radius=16)

        title_font = get_font(self.game.font_cache, "title")
        body = get_font(self.game.font_cache, "body")
        screen.blit(
            fit_text(title_font, "数据侵蚀", panel.width - 60, UI_COLORS["red"]),
            (panel.x + 30, panel.y + 32),
        )
        screen.blit(
            fit_text(body, "黑色数据流吞没了你，本次攀爬结束。", panel.width - 60, UI_COLORS["text"]),
            (panel.x + 30, panel.y + 92),
        )
        screen.blit(
            fit_text(body, f"时间  {int(self.elapsed // 60)}:{int(self.elapsed % 60):02d}", 200, UI_COLORS["accent"]),
            (panel.x + 30, panel.y + 134),
        )
        screen.blit(
            fit_text(body, f"高度  {self.score}", 200, UI_COLORS["gold"]),
            (panel.x + 30, panel.y + 172),
        )
        screen.blit(
            fit_text(body, f"历史最高  {self.best_score}", 260, UI_COLORS["text"]),
            (panel.x + 30, panel.y + 204),
        )

        button_font = get_font(self.game.font_cache, "button")
        button_y = panel.bottom - 76
        restart = pygame.Rect(panel.x + 40, button_y, 200, 52)
        menu = pygame.Rect(panel.right - 240, button_y, 200, 52)
        self.game_over_buttons = {"restart": restart, "menu": menu}
        draw_button(
            screen, restart, "重新开始", button_font,
            variant="primary" if self.selected_button == 0 else "secondary",
        )
        draw_button(
            screen, menu, "返回主菜单", button_font,
            variant="primary" if self.selected_button == 1 else "secondary",
        )
