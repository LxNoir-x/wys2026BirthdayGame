import random
import time

import pygame

from config import COLORS, SCREEN_HEIGHT, SCREEN_WIDTH, TARGET_DELTA
from entities.player import Player
from platforms.moving_platform import MovingPlatform
from platforms.static_platform import StaticPlatform
from states.game_state import GameState
from utils.keyboard_utils import KeyboardUtils
from utils.ui_theme import (
    UI_COLORS,
    draw_button,
    draw_chip,
    draw_panel,
    draw_ui_background,
    get_font,
)


class SLevelState(GameState):
    def __init__(self, game):
        super().__init__(game)
        self.player = Player(game)
        self.player.rect.midbottom = (SCREEN_WIDTH // 2, SCREEN_HEIGHT)
        self.player.allow_top_overflow = True

        self.start_baseline = self.player.rect.top
        self.platforms = []
        self.camera_y = 0
        self.score = 0
        self.game_over = False
        self.celebration = False
        self.celebration_timer = 0
        self.last_time = time.time()
        self.highest_y = SCREEN_HEIGHT
        self.last_spawn_ref = None

        # 演职表数据
        self.staff_names = ["xx" for _ in range(20)]
        self.staff_displayed = set()
        self.staff_queue = []
        self.staff_scroll_positions = []
        self.staff_opacities = []  # 透明度
        self.staff_speed = 20  # 滚动速度
        self.staff_spacing = 80  # 名字间距

        # 玩家能力参数
        self.player_max_jump_v = 18.0
        self.gravity_per_frame = 0.8
        self.player_max_horiz_speed = 8.5
        self.max_vertical_reach = int((self.player_max_jump_v ** 2) / (2 * self.gravity_per_frame))
        time_to_apex = self.player_max_jump_v / self.gravity_per_frame
        self.max_horizontal_reach = int(self.player_max_horiz_speed * time_to_apex * 0.95)

        self._init_platforms()
        self.highest_y = self.start_baseline
        self.score = 0
        self.paused = False
        self.menu_rect = pygame.Rect(0, 0, 0, 0)

    def _init_platforms(self):
        base_y = SCREEN_HEIGHT - 100
        gap = 80
        for i in range(5):
            y = base_y - i * gap
            x = random.randint(SCREEN_WIDTH // 2 - 100, SCREEN_WIDTH // 2 + 100)
            x = max(40, min(SCREEN_WIDTH - 200, x))
            width = random.randint(120, 150)
            plat = StaticPlatform(pygame.Rect(x, y, width, 15))
            self.platforms.append(plat)
            self.highest_y = min(self.highest_y, y)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.game_over:
                        from states.main_menu_state import MainMenuState
                        self.game.change_state(MainMenuState(self.game))
                    else:
                        from states.settings_state import SettingsState

                        self.game.change_state(
                            SettingsState(
                                self.game,
                                return_state=self,
                                initial_tab="operations",
                            )
                        )
                elif event.key in (pygame.K_SPACE, pygame.K_w) and not self.game_over:
                    self.player.jump()
            elif (
                event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and self.game_over
                and self.menu_rect.collidepoint(event.pos)
            ):
                from states.main_menu_state import MainMenuState

                self.game.change_state(MainMenuState(self.game))

    def update(self, dt):
        if self.game_over:
            return
        current_time = time.time()
        dt = current_time - self.last_time
        if dt < TARGET_DELTA:
            pygame.time.wait(int((TARGET_DELTA - dt)*1000))
            dt = TARGET_DELTA
        self.last_time = current_time

        # 使用新的键盘输入处理模块检测跳跃键
        keys = KeyboardUtils.get_keys_pressed()
        if keys['w'] or keys['space'] or keys['up']:
            self.player.jump()

        self.player.update(self.platforms, None, None, dt=dt)

        for plat in self.platforms:
            plat.update(dt)

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

        new_score = max(0, int((self.start_baseline - self.highest_y) // 10))
        if new_score > self.score:
            self.score = new_score
            # 每10个高度显示2个演职表名字
            if self.score % 10 == 0:
                self._show_staff_names()

        # 移除死亡检测
        if not hasattr(self, 'has_left_ground'):
            self.has_left_ground = False
        if self.player.rect.bottom < SCREEN_HEIGHT - 5:
            self.has_left_ground = True
        
        # 当高度超过100且演职人员表滚动完毕时，进入庆祝模式
        # 因为我太菜了跳不上去，暂时先100
        if self.score > 100 and not self.celebration and not self.staff_queue:
            self.celebration = True
            self.celebration_timer = 0

        # 处理庆祝模式
        if self.celebration:
            # 玩家缓缓升空
            self.player.rect.y -= 50 * dt
            # 相机跟随玩家
            self.camera_y = self.player.rect.centery - SCREEN_HEIGHT // 2
            
            # 增加庆祝计时器
            self.celebration_timer += dt
            
            # 10秒后返回主菜单
            if self.celebration_timer > 10:
                from states.main_menu_state import MainMenuState
                self.game.change_state(MainMenuState(self.game))
        else:
            # 更新演职表显示
            if self.staff_queue:
                # 更新滚动位置和透明度
                for i in range(len(self.staff_scroll_positions)):
                    self.staff_scroll_positions[i] -= self.staff_speed * dt
                    
                    # 更新透明度
                    y_pos = self.staff_scroll_positions[i]
                    if y_pos > SCREEN_HEIGHT - 100:
                        # 进入屏幕时逐渐变亮
                        self.staff_opacities[i] = min(255, self.staff_opacities[i] + 255 * dt * 2)
                    elif y_pos < 100:
                        # 离开屏幕时逐渐变暗
                        self.staff_opacities[i] = max(0, self.staff_opacities[i] - 255 * dt * 2)
                    else:
                        # 中间部分保持完全不透明
                        self.staff_opacities[i] = 255
                
                # 移除已经滚动出屏幕的名字
                while self.staff_queue and self.staff_scroll_positions[0] < -50:
                    self.staff_queue.pop(0)
                    self.staff_scroll_positions.pop(0)
                    self.staff_opacities.pop(0)

    def _show_staff_names(self):
        # 随机选择2个未显示的名字
        available_names = [name for name in self.staff_names if name not in self.staff_displayed]
        if not available_names:
            available_names = self.staff_names
            self.staff_displayed.clear()
        
        # 计算初始位置
        if self.staff_queue:
            last_pos = self.staff_scroll_positions[-1]
            initial_pos = last_pos + self.staff_spacing
        else:
            initial_pos = SCREEN_HEIGHT + 50
        
        for i in range(2):
            if available_names:
                name = random.choice(available_names)
                self.staff_queue.append(name)
                # 初始位置在屏幕底部，与前一个名字保持间距
                self.staff_scroll_positions.append(initial_pos + i * self.staff_spacing)
                # 初始透明度为0，逐渐增加
                self.staff_opacities.append(0)
                self.staff_displayed.add(name)
                available_names.remove(name)

    def _spawn_platform_above(self, reference_y):
        if not self.platforms:
            ref_x = max(80, min(SCREEN_WIDTH - 180, self.player.rect.x))
            ref_y = self.player.rect.top
        else:
            ref_plat = min(self.platforms, key=lambda p: p.rect.y)
            ref_y = ref_plat.rect.y
            ref_x = ref_plat.rect.x

        min_gap = 60
        max_gap = max(min_gap, int(self.max_vertical_reach * 0.85))
        gap = random.randint(min_gap, max_gap)
        new_y = ref_y - gap

        max_horiz = int(self.max_horizontal_reach * 0.9)
        horiz = random.randint(-max_horiz, max_horiz)
        x = ref_x + horiz
        x = max(40, min(SCREEN_WIDTH - 200, x))

        width = random.randint(100, 150)
        
        current_height = self.score
        
        if current_height > 500 and random.random() < 0.5:
            speed = random.uniform(1.5, 3.0)
            range_ = random.randint(150, 250)
            plat = MovingPlatform(x, new_y, width, 15, speed, range_)
        else:
            plat = StaticPlatform(pygame.Rect(x, new_y, width, 15))
        
        self.platforms.append(plat)
        return True

    def _clean_below(self):
        threshold = self.camera_y + SCREEN_HEIGHT + 600
        self.platforms = [p for p in self.platforms if p.rect.y < threshold]

    def draw(self, screen):
        draw_ui_background(screen, UI_COLORS["gold"])

        for plat in self.platforms:
            screen_rect = plat.rect.copy()
            screen_rect.y -= self.camera_y
            if -50 < screen_rect.y < SCREEN_HEIGHT + 50:
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

        hud = pygame.Rect(24, 24, 280, 104)
        draw_panel(screen, hud, fill=(25, 32, 47), border=UI_COLORS["gold"], radius=12, shadow=False)
        caption = get_font(self.game.font_cache, "caption")
        screen.blit(caption.render("S / STAFF ROLL", True, UI_COLORS["gold"]), (46, 44))
        draw_chip(
            screen,
            pygame.Rect(46, 76, 112, 28),
            f"高度  {self.score}",
            caption,
            UI_COLORS["gold"],
        )
        draw_chip(
            screen,
            pygame.Rect(170, 76, 108, 28),
            "演职表" if not self.celebration else "庆祝中",
            caption,
            UI_COLORS["accent"] if not self.celebration else UI_COLORS["green"],
        )

        # 绘制演职表名字
        if self.staff_queue:
            for i, (name, y_pos, opacity) in enumerate(zip(self.staff_queue, self.staff_scroll_positions, self.staff_opacities)):
                # 创建文字表面
                staff_text = self.game.font_cache["medium"].render(name, True, COLORS["CYAN"])
                text_rect = staff_text.get_rect(center=(SCREEN_WIDTH // 2, y_pos))
                
                # 添加光晕效果
                glow_surface = pygame.Surface((text_rect.width + 40, text_rect.height + 20), pygame.SRCALPHA)
                for j in range(20, 0, -4):
                    alpha = int(50 * (1 - j/20) * (opacity/255))
                    color = (*COLORS["CYAN"], alpha)
                    pygame.draw.rect(glow_surface, color, (0, 0, text_rect.width + 40, text_rect.height + 20), border_radius=10)
                glow_rect = glow_surface.get_rect(center=(SCREEN_WIDTH // 2, y_pos))
                screen.blit(glow_surface, glow_rect)
                
                # 绘制文字
                text_surface = pygame.Surface(staff_text.get_size(), pygame.SRCALPHA)
                text_surface.blit(staff_text, (0, 0))
                text_surface.set_alpha(int(opacity))
                screen.blit(text_surface, text_rect)

        # 庆祝模式显示生日快乐
        if self.celebration:
            # 绘制生日快乐文字
            happy_text = self.game.font_cache["large"].render("生日快乐", True, COLORS["GOLD"])
            happy_rect = happy_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            
            # 文字光晕效果
            glow_surface = pygame.Surface((happy_rect.width + 40, happy_rect.height + 20), pygame.SRCALPHA)
            for i in range(20, 0, -4):
                alpha = int(100 * (1 - i/20))
                color = (*COLORS["GOLD"], alpha)
                pygame.draw.rect(glow_surface, color, (0, 0, happy_rect.width + 40, happy_rect.height + 20), border_radius=10)
            glow_rect = glow_surface.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            screen.blit(glow_surface, glow_rect)
            
            # 绘制文字
            screen.blit(happy_text, happy_rect)
        elif self.game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((5, 9, 18, 188))
            screen.blit(overlay, (0, 0))
            result = pygame.Rect(320, 160, 640, 350)
            draw_panel(screen, result, fill=(25, 35, 54), border=UI_COLORS["gold"], radius=16)
            over_text = get_font(self.game.font_cache, "title").render("挑战结束", True, UI_COLORS["gold"])
            screen.blit(over_text, over_text.get_rect(center=(result.centerx, result.y + 70)))
            draw_chip(
                screen,
                pygame.Rect(result.x + 82, result.y + 140, 220, 34),
                f"最高高度  {self.score}",
                caption,
                UI_COLORS["accent"],
            )
            draw_chip(
                screen,
                pygame.Rect(result.x + 338, result.y + 140, 220, 34),
                "演职表未完成",
                caption,
                UI_COLORS["muted"],
            )
            result_hint = caption.render("按 ESC 或点击按钮返回主菜单。", True, UI_COLORS["muted"])
            screen.blit(result_hint, result_hint.get_rect(center=(result.centerx, result.y + 230)))
            self.menu_rect = draw_button(
                screen,
                pygame.Rect(result.x + 150, result.bottom - 70, 340, 48),
                "返回主菜单",
                get_font(self.game.font_cache, "button"),
                "secondary",
            )
