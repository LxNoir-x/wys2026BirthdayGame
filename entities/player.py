"""
玩家实体模块
负责玩家的移动、跳跃、碰撞检测和动画渲染
"""

import math
import os
import sys

import pygame

from config import (
    COLORS,
    DAMAGE_INVULNERABILITY_SECONDS,
    PLAYER_GRAVITY,
    PLAYER_JUMP_HEIGHT_DEFAULT,
    PLAYER_RUN_SPEED_DEFAULT,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)
from platforms.bouncing_platform import BouncingPlatform
from platforms.fragile_platform import FragilePlatform
from platforms.speed_platform import SpeedPlatform
from utils.keyboard_utils import KeyboardUtils


class Player:
    """
    玩家类
    
    负责管理玩家的物理属性、移动控制、碰撞检测和动画渲染
    
    Attributes:
        rect: 玩家碰撞盒
        vx: 水平速度
        vy: 垂直速度
        jumping: 是否正在跳跃
        last_jump: 上次跳跃时间戳
        on_moving: 当前所在的移动平台
        game: 游戏实例
        color: 玩家颜色
        no_damage: 是否无伤状态
        got_collect: 是否获得收集品
        reached_goal: 是否到达终点
        collision_radius: 碰撞检测半径
        pulse_phase: 脉冲动画相位
        allow_top_overflow: 是否允许越过屏幕顶部（无尽模式）
        
        # 动画相关
        idle_frames: 空闲动画帧列表
        move_frames: 移动动画帧列表
        jumpup_frames: 跳跃上升动画帧列表
        jumpfall_frames: 跳跃下落动画帧列表
        duang_frame: 碰撞特效帧
        current_frames: 当前使用的动画帧列表
        current_frame: 当前帧索引
        frame_time: 帧时间计数器
        frame_duration: 每帧显示时间（秒）
        facing_right: 是否朝右
        is_moving: 是否正在移动
        is_jumping: 是否正在跳跃
        is_falling: 是否正在下落
        show_duang: 是否显示碰撞特效
        duang_timer: 碰撞特效计时器
        on_ground: 是否在地面上
    """
    
    def __init__(self, game=None):
        """
        初始化玩家
        
        Args:
            game: 游戏实例（可选）
        """
        # 初始化碰撞盒（屏幕底部中央）
        self.rect = pygame.Rect(SCREEN_WIDTH // 2 - 13, SCREEN_HEIGHT - 60, 26, 36)
        
        # 速度属性
        self.vx = 0.0
        self.vy = 0.0
        self.run_speed = float(
            getattr(game, "developer_run_speed", PLAYER_RUN_SPEED_DEFAULT)
        )
        self.jump_height = float(
            getattr(game, "developer_jump_height", PLAYER_JUMP_HEIGHT_DEFAULT)
        )
        
        # 跳跃属性
        self.jumping = False
        self.last_jump = 0
        
        # 平台相关
        self.on_moving = None
        self.game = game
        
        # 状态属性
        self.color = COLORS["GOLD"]
        self.no_damage = True
        self.got_collect = False
        self.reached_goal = False
        self.damage_handler = None
        self.damage_cooldown = 0.0
        self.last_damage_reason = None
        self.fall_origin_y = None
        self.last_support_y = None
        self.surface_multiplier = 1.0
        self.surface_jump_multiplier = 1.0
        self.visual_state = "normal"
        self.collision_radius = 120
        self.pulse_phase = 0
        self.allow_top_overflow = False  # 用于无尽模式
        self.allow_bottom_fall = False
        
        # 初始化动画帧
        self._init_animation_frames()
    
    def _init_animation_frames(self):
        """初始化动画帧（内部方法）"""
        # 动画帧列表
        self.idle_frames = []
        self.move_frames = []
        self.jumpup_frames = []
        self.jumpfall_frames = []
        self.duang_frame = None
        
        # 当前动画状态
        self.current_frames = None
        self.current_frame = 0
        self.frame_time = 0
        self.frame_duration = 0.1
        
        # 状态标志
        self.facing_right = True
        self.is_moving = False
        self.is_jumping = False
        self.is_falling = False
        self.show_duang = False
        self.duang_timer = 0
        self.on_ground = False
        self.loaded_skin_id = None
        
        # 尝试加载 GIF 动画
        self._load_gif_animations()
    
    def _load_gif_animations(self):
        """加载 GIF 动画帧（内部方法）"""
        try:
            from PIL import Image
            
            # 获取资源路径
            def resource_path(relative_path):
                try:
                    base_path = sys._MEIPASS
                except AttributeError:
                    base_path = os.path.abspath(".")
                return os.path.join(base_path, relative_path.replace("/", os.sep))
            
            skin_id = (
                self.game.shop_system.get_current_skin()
                if self.game and hasattr(self.game, "shop_system")
                else "default"
            )
            skin_folders = {"default": "0", "endgame": "A", "maid": "B", "be": "C"}
            folder = skin_folders.get(skin_id, "0")
            names = (
                {
                    "idle": "idle.gif",
                    "move": "move.gif",
                    "jump": "jumpup.gif",
                    "fall": "jumpfall.gif",
                }
                if folder == "0"
                else {
                    "idle": "idle.gif",
                    "move": "move.gif",
                    "jump": "jump.gif",
                    "fall": "fall.gif",
                }
            )

            def load_frames(filename):
                frames = []
                image = Image.open(
                    resource_path(f"assets/images/player/skin/{folder}/{filename}")
                )
                for index in range(image.n_frames):
                    image.seek(index)
                    frame = image.convert("RGBA")
                    surface = pygame.image.fromstring(
                        frame.tobytes("raw", "RGBA"), frame.size, "RGBA"
                    )
                    frames.append(pygame.transform.scale(surface, (40, 50)))
                return frames

            self.idle_frames = load_frames(names["idle"])
            self.move_frames = load_frames(names["move"])
            self.jumpup_frames = load_frames(names["jump"])
            self.jumpfall_frames = load_frames(names["fall"])

            duang_png_path = resource_path(
                f"assets/images/player/skin/{folder}/duang.png"
            )
            try:
                self.duang_frame = pygame.image.load(duang_png_path).convert_alpha()
                self.duang_frame = pygame.transform.scale(self.duang_frame, (40, 50))
            except (FileNotFoundError, OSError, pygame.error):
                # 部分皮肤没有 duang.png；缺少时只是不画碰撞特效，不影响其它动画。
                self.duang_frame = None
            self.loaded_skin_id = skin_id
            self.current_frames = self.idle_frames if self.idle_frames else None
        except (FileNotFoundError, OSError, pygame.error):
            # 如果加载失败，使用默认圆形绘制
            self.current_frames = None

    def update(
        self,
        platforms,
        collect_item,
        goal_point,
        dt,
        check_bounds=True,
        hazards=None,
        blockers=None,
    ):
        """
        更新玩家状态
        
        Args:
            platforms: 平台列表
            collect_item: 收集品（可选）
            goal_point: 终点（可选）
            dt: 时间增量（秒）
            check_bounds: 是否检查边界
            hazards: 伤害源列表（可选）
            blockers: 未开启的门或栅栏碰撞盒（可选）
        """
        self.damage_cooldown = max(0.0, self.damage_cooldown - dt)

        self.previous_rect = self.rect.copy()

        # 更新移动
        keys = KeyboardUtils.get_keys_pressed()
        movement = self._update_movement(keys, dt)

        # 在交互判定前完成物理解算，避免读取移动前的位置。
        nearby_platforms = self._get_nearby_platforms(platforms)
        self._move_with_platform_collisions(nearby_platforms, dt, movement)
        
        # 检查边界
        if check_bounds:
            self._update_bounds()
        
        # 更新脉冲相位
        self.pulse_phase += dt * 3
        
        # 更新朝向和状态
        self._update_animation_state()
        
        # 更新碰撞特效
        self._update_duang_effect(dt)
        
        # 更新动画帧
        self._update_animation_frame(dt)
        
        # 检查收集品碰撞
        if (
            collect_item
            and not collect_item.collected
            and not self.got_collect
            and self.rect.inflate(64, 64).colliderect(collect_item.rect)
        ):
            self.got_collect = True
            collect_item.collected = True
        
        # 更新敌人碰撞
        all_enemies = []
        for p in platforms:
            for e in p.enemies:
                if e.alive and e.visible:
                    all_enemies.append(e)
        self._update_enemy_collision(all_enemies)

        # 门和栅栏只阻挡玩家，不属于伤害源。
        self._resolve_blockers(blockers or [])

        # 先处理门/栅栏，再判断终点，避免穿过未开启的出口。
        if goal_point and not self.reached_goal and self.rect.colliderect(goal_point.rect):
            self.reached_goal = True
        
        # 地刺等显式伤害源。敌人不在正式需求的伤害源范围内。
        self._update_hazard_collision(hazards or [])

    def _update_movement(self, keys, dt):
        """更新玩家移动（内部方法）"""
        # 移动参数
        max_speed = self.run_speed * self.surface_multiplier
        ground_acc = 1.2 * self.surface_multiplier
        air_acc = 0.8 * self.surface_multiplier
        ground_friction = 0.72
        air_resistance = 0.90
        
        # 水平移动
        if keys['a'] or keys['left']:
            acc = ground_acc if self._is_on_ground() else air_acc
            self.vx = max(-max_speed, self.vx - acc)
        elif keys['d'] or keys['right']:
            acc = ground_acc if self._is_on_ground() else air_acc
            self.vx = min(max_speed, self.vx + acc)
        else:
            if self._is_on_ground():
                # 冰面仍比普通地面滑，沼泽更快停下；所有表面都使用提高后的摩擦。
                friction = max(
                    0.62,
                    min(0.84, ground_friction + (self.surface_multiplier - 1) * 0.2),
                )
            else:
                friction = air_resistance
            self.vx *= friction ** max(0.0, dt * 60)
            if abs(self.vx) < 0.3:
                self.vx = 0.0
        
        # 垂直移动（加速下落）
        if keys['s'] or keys['down']:
            self.vy += 0.9
        else:
            self.vy += PLAYER_GRAVITY
        self.vy = min(self.vy, 15)
        
        return self.vx * dt * 60, self.vy * dt * 60

    def _move_with_platform_collisions(self, platforms, dt, movement):
        """以小步移动并在每一步解算碰撞，防止跨过薄墙或平台。"""
        dx, dy = movement
        steps = max(1, math.ceil(max(abs(dx), abs(dy)) / 4))
        step_dx = dx / steps
        step_dy = dy / steps

        for _ in range(steps):
            self.previous_rect = self.rect.copy()
            self.rect.x += step_dx
            self.rect.y += step_dy
            self._update_platform_collision(platforms, dt / steps, follow_moving=False)
            if self.vx == 0:
                step_dx = 0
            if self.vy == 0:
                step_dy = 0

        # 移动平台本帧只应带动玩家一次，不能随碰撞子步重复叠加位移。
        if self.on_moving:
            self.rect.x += getattr(
                self.on_moving,
                "delta_x",
                self.on_moving.speed * self.on_moving.dir,
            )
            self.rect.y += getattr(self.on_moving, "delta_y", 0)

        self._refresh_ground_support(platforms)

    def _refresh_ground_support(self, platforms):
        """在碰撞子步结束后重新确认脚下支撑，避免水平子步清空落地状态。"""

        if not self.allow_bottom_fall and self.rect.bottom >= SCREEN_HEIGHT - 5:
            self.on_ground = True
            self.on_moving = None
            self.last_support_y = SCREEN_HEIGHT
            self.surface_multiplier = 1.0
            self.surface_jump_multiplier = 1.0
            self.jumping = False
            return

        for platform in platforms:
            rect = platform.get_rect()
            horizontal_overlap = min(self.rect.right, rect.right) - max(
                self.rect.left,
                rect.left,
            )
            if (
                horizontal_overlap > 0
                and abs(self.rect.bottom - rect.top) <= 2
                and self.vy >= 0
            ):
                self.on_ground = True
                self.on_moving = platform if hasattr(platform, "dir") else None
                self.last_support_y = rect.top
                self.fall_origin_y = None
                self.surface_multiplier = getattr(
                    platform,
                    "movement_multiplier",
                    1.0,
                )
                self.surface_jump_multiplier = getattr(
                    platform,
                    "jump_multiplier",
                    1.0,
                )
                self.jumping = False
                return

    def _is_on_ground(self):
        """检查是否在地面上（内部方法）"""
        return (
            self.on_ground
            or self.on_moving is not None
            or (not self.allow_bottom_fall and self.rect.bottom >= SCREEN_HEIGHT - 5)
        )

    def _update_bounds(self):
        """更新边界限制（内部方法）"""
        # 左右边界
        if self.rect.left < 0:
            self.rect.left = 0
            self.vx = 0.0
        elif self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH
            self.vx = 0.0
        
        # 底部边界
        if not self.allow_bottom_fall and self.rect.bottom >= SCREEN_HEIGHT - 5:
            self.rect.bottom = SCREEN_HEIGHT
            self.vy = 0.0

    def _get_nearby_platforms(self, platforms):
        """返回全部平台，避免长柱在中心点距离过滤后漏掉碰撞。"""
        return platforms

    def _update_platform_collision(self, platforms, dt, *, follow_moving=True):
        """更新平台碰撞（内部方法）"""
        previous_support_y = self.last_support_y
        self.on_moving = None
        self.on_ground = False
        current_support_y = None
        current_surface_multiplier = 1.0
        current_surface_jump_multiplier = 1.0

        if previous_support_y is not None and self.fall_origin_y is None:
            # 本帧未落回任何支撑面时，记录离开支撑面的高度。
            self.fall_origin_y = previous_support_y
        
        for p in platforms:
            pr = p.get_rect()
            if pr.width == 0:
                continue

            if self.rect.colliderect(pr):
                previous_rect = self.previous_rect
                # 下落时的平台碰撞
                if self.vy > 0 and previous_rect.bottom <= pr.top:
                    self.rect.bottom = pr.top

                    # 处理特殊平台
                    if isinstance(p, BouncingPlatform):
                        self.vy = -p.bounce_power
                    elif isinstance(p, FragilePlatform):
                        p.trigger_crack()
                        self.vy = 0.0
                    elif isinstance(p, SpeedPlatform):
                        self.vx += p.speed_boost * p.direction
                        self.vy = 0.0
                    else:
                        self.vy = 0.0
                    
                    self.jumping = False
                    self.on_ground = True
                    current_support_y = pr.top
                    current_surface_multiplier = getattr(p, "movement_multiplier", 1.0)
                    current_surface_jump_multiplier = getattr(p, "jump_multiplier", 1.0)
                    if hasattr(p, "dir"):
                        self.on_moving = p
                    break

                # 上升时的平台碰撞（头部碰撞）
                elif self.vy < 0 and previous_rect.top >= pr.bottom:
                    self.rect.top = pr.bottom
                    self.vy = 0.0
                    self.show_duang = True
                    self.duang_timer = 0
                    if self.jumpfall_frames:
                        self.current_frames = self.jumpfall_frames
                        self.current_frame = 0
                        self.frame_time = 0
                    break

                # 固定块和平台必须完整阻挡玩家，不能从侧面穿过。
                elif self.vx > 0 and previous_rect.right <= pr.left:
                    self.rect.right = pr.left
                    self.vx = 0.0
                    break
                elif self.vx < 0 and previous_rect.left >= pr.right:
                    self.rect.left = pr.right
                    self.vx = 0.0
                    break

                # 若本帧位移已进入实体内部，仍必须将玩家推出完整碰撞体。
                # 这覆盖高速斜向移动和上一帧边缘取整造成的重叠，不能允许
                # 玩家留在长柱或黑色方块内部。
                else:
                    overlap_x = min(self.rect.right, pr.right) - max(self.rect.left, pr.left)
                    overlap_y = min(self.rect.bottom, pr.bottom) - max(self.rect.top, pr.top)
                    if overlap_x <= overlap_y:
                        if previous_rect.centerx <= pr.centerx:
                            self.rect.right = pr.left
                        else:
                            self.rect.left = pr.right
                        self.vx = 0.0
                    elif previous_rect.centery <= pr.centery:
                        self.rect.bottom = pr.top
                        self.vy = 0.0
                        self.on_ground = True
                        current_support_y = pr.top
                    else:
                        self.rect.top = pr.bottom
                        self.vy = 0.0
                    break
            
        # 检查是否在地面
        if not self.allow_bottom_fall and self.rect.bottom >= SCREEN_HEIGHT - 5:
            self.on_ground = True
            current_support_y = SCREEN_HEIGHT
        
        # 更新跳跃状态
        if self.on_ground or self.on_moving is not None:
            self.jumping = False
        
        # 高低差只改变落点；伤害统一由显式机关负责。
        if current_support_y is not None:
            self.fall_origin_y = None
            self.last_support_y = current_support_y
            self.surface_multiplier = current_surface_multiplier
            self.surface_jump_multiplier = current_surface_jump_multiplier
        else:
            self.last_support_y = None
            self.surface_multiplier = 1.0
            self.surface_jump_multiplier = 1.0

        # 跟随移动平台
        if self.on_moving and follow_moving:
            self.rect.x += getattr(
                self.on_moving,
                "delta_x",
                self.on_moving.speed * self.on_moving.dir,
            )
            self.rect.y += getattr(self.on_moving, "delta_y", 0)

    def _update_enemy_collision(self, enemies):
        """更新敌人碰撞（内部方法）"""
        for enemy in enemies:
            if (
                enemy.alive
                and self.rect.colliderect(enemy.rect)
                and self.vy > 0
                and self.rect.bottom <= enemy.rect.top + 15
            ):
                enemy.kill()
                self.vy = -12

    def _update_hazard_collision(self, hazards):
        """检查正式配置的伤害源。"""
        for hazard in hazards:
            if getattr(hazard, "dangerous", hazard.visible) and self.rect.colliderect(hazard.rect):
                self.take_damage("spike")
                if hasattr(hazard, "consume"):
                    hazard.consume()
                break

    def _resolve_blockers(self, blockers):
        for blocker in blockers:
            if not self.rect.colliderect(blocker):
                continue

            overlap_x = min(self.rect.right, blocker.right) - max(self.rect.left, blocker.left)
            overlap_y = min(self.rect.bottom, blocker.bottom) - max(self.rect.top, blocker.top)
            if overlap_x <= overlap_y:
                if self.vx > 0:
                    self.rect.right = blocker.left
                elif self.vx < 0:
                    self.rect.left = blocker.right
                elif self.rect.centerx < blocker.centerx:
                    self.rect.right = blocker.left
                else:
                    self.rect.left = blocker.right
                self.vx = 0.0
            elif self.vy > 0:
                self.rect.bottom = blocker.top
                self.vy = 0.0
            else:
                self.rect.top = blocker.bottom
                self.vy = 0.0

    def take_damage(self, reason):
        """记录一次受伤并通知玩法状态。

        无敌时间在玩家层处理，避免同一地刺或同一次落地被连续计数。
        """
        if self.damage_cooldown > 0:
            return False

        self.damage_cooldown = DAMAGE_INVULNERABILITY_SECONDS
        self.last_damage_reason = reason
        self.no_damage = False
        if self.damage_handler:
            self.damage_handler(reason)
        return True

    def _update_animation_state(self):
        """更新动画状态（内部方法）"""
        # 更新移动状态
        if abs(self.vx) > 0.5:
            self.is_moving = True
            self.facing_right = self.vx > 0.5
        else:
            self.is_moving = False
        
        # 更新跳跃状态
        if self.vy < 0:
            self.is_jumping = True
            self.is_falling = False
        elif self.vy > 0:
            self.is_jumping = False
            self.is_falling = True
        else:
            self.is_jumping = False
            self.is_falling = False

    def _update_duang_effect(self, dt):
        """更新碰撞特效（内部方法）"""
        if self.show_duang:
            self.duang_timer += dt
            if self.duang_timer >= 0.2:
                self.show_duang = False
                self.duang_timer = 0

    def _update_animation_frame(self, dt):
        """更新动画帧（内部方法）"""
        # 根据状态切换动画
        if self.show_duang:
            pass  # 显示碰撞特效时不切换动画
        elif self.is_jumping and self.jumpup_frames:
            if self.current_frames != self.jumpup_frames:
                self.current_frames = self.jumpup_frames
                self.current_frame = 0
                self.frame_time = 0
        elif self.is_falling and self.jumpfall_frames and not self.on_ground:
            if self.current_frames != self.jumpfall_frames:
                self.current_frames = self.jumpfall_frames
                self.current_frame = 0
                self.frame_time = 0
        elif self.is_moving and self.move_frames and self.on_ground:
            if self.current_frames != self.move_frames:
                self.current_frames = self.move_frames
                self.current_frame = 0
                self.frame_time = 0
        elif (
            not self.is_moving
            and self.on_ground
            and self.idle_frames
            and self.current_frames != self.idle_frames
        ):
            self.current_frames = self.idle_frames
            self.current_frame = 0
            self.frame_time = 0
        
        # 更新帧索引
        if self.current_frames:
            self.frame_time += dt
            if self.frame_time >= self.frame_duration:
                self.current_frame = (self.current_frame + 1) % len(self.current_frames)
                self.frame_time = 0

    def jump(self):
        """玩家跳跃"""
        now = pygame.time.get_ticks()
        if not self.jumping and now - self.last_jump > 100:
            base_velocity = math.sqrt(2 * PLAYER_GRAVITY * self.jump_height)
            self.vy = -base_velocity * self.surface_jump_multiplier
            self.jumping = True
            self.last_jump = now
            self.on_moving = None
            if self.game is not None:
                self.game.audio_system.play_sfx("jump")

    def draw(self, screen, dirty_rects):
        """
        绘制玩家
        
        Args:
            screen: pygame 显示表面
            dirty_rects: 需要重绘的区域列表
        """
        # 更新皮肤颜色
        if self.game and hasattr(self.game, 'shop_system'):
            skin_id = self.game.shop_system.get_current_skin()
            self.color = self.game.shop_system.get_skin_color(skin_id)
            if skin_id != self.loaded_skin_id:
                self.idle_frames = []
                self.move_frames = []
                self.jumpup_frames = []
                self.jumpfall_frames = []
                self.duang_frame = None
                self._load_gif_animations()
        
        # 使用 GIF 动画绘制
        if self.current_frames:
            current_frame = self.current_frames[self.current_frame]
            
            # 根据朝向翻转
            if not self.facing_right:
                current_frame = pygame.transform.flip(current_frame, True, False)
            
            # 计算绘制位置
            image_rect = current_frame.get_rect(center=self.rect.center)
            
            # 绘制碰撞特效
            if self.show_duang and self.duang_frame:
                duang_frame = self.duang_frame
                if not self.facing_right:
                    duang_frame = pygame.transform.flip(duang_frame, True, False)
                duang_rect = duang_frame.get_rect(center=self.rect.center)
                screen.blit(duang_frame, duang_rect)
                dirty_rects.append(duang_rect.inflate(10, 10))
            else:
                screen.blit(current_frame, image_rect)
                dirty_rects.append(image_rect.inflate(10, 10))
        else:
            # 备用绘制：圆形玩家
            cx, cy = self.rect.center
            pulse = 1 + 0.05 * math.sin(self.pulse_phase)
            radius = int(25 * pulse)
            
            # 发光效果
            glow = pygame.Surface((radius*2+40, radius*2+40), pygame.SRCALPHA)
            for i in range(20, 0, -4):
                alpha = int(100 * (1 - i/20))
                color = (*self.color, alpha)
                pygame.draw.circle(glow, color, (radius+20, radius+20), radius + i)
            screen.blit(glow, (cx - radius - 20, cy - radius - 20))
            
            # 主体
            circle = pygame.draw.circle(screen, self.color, (cx, cy), radius)
            dirty_rects.append(circle.inflate(40, 40))
        
        self._draw_visual_state(screen, dirty_rects)

    def _draw_visual_state(self, screen, dirty_rects):
        """绘制理智异常和保护模式的占位视觉状态。"""
        if self.visual_state == "normal":
            return

        effect_rect = self.rect.inflate(28, 28)
        if self.visual_state == "protection":
            pygame.draw.ellipse(screen, COLORS["CYAN"], effect_rect, 2)
            pygame.draw.arc(screen, COLORS["GREEN"], effect_rect.inflate(8, 8), 0.3, 2.5, 3)
        else:
            color = COLORS["RED"] if self.visual_state == "beast" else COLORS["MAGENTA"]
            pygame.draw.rect(screen, color, effect_rect, 2, border_radius=8)
            for index in range(3):
                y = self.rect.top - 8 + index * 8
                offset = int(math.sin(self.pulse_phase * 2 + index) * 5)
                pygame.draw.line(
                    screen,
                    color,
                    (self.rect.left - 12 + offset, y),
                    (self.rect.right + 12 + offset, y),
                    2,
                )
            if self.visual_state == "beast":
                pygame.draw.polygon(
                    screen,
                    color,
                    [
                        (self.rect.left - 8, self.rect.top + 8),
                        (self.rect.left - 22, self.rect.top - 10),
                        (self.rect.left + 2, self.rect.top - 2),
                    ],
                )
                pygame.draw.polygon(
                    screen,
                    color,
                    [
                        (self.rect.right + 8, self.rect.top + 8),
                        (self.rect.right + 22, self.rect.top - 10),
                        (self.rect.right - 2, self.rect.top - 2),
                    ],
                )
        dirty_rects.append(effect_rect.inflate(24, 24))
