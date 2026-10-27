"""普通关卡与主线关卡玩法状态。"""

from __future__ import annotations

import random
import time

import pygame

from config import (
    COLORS,
    PLAYER_JUMP_HEIGHT_MAX,
    PLAYER_JUMP_HEIGHT_MIN,
    PLAYER_RUN_SPEED_MAX,
    PLAYER_RUN_SPEED_MIN,
    SAN_FATAL_DAMAGE_COUNT,
    SAN_INITIAL,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    STORY_MAX_HEALTH,
    STORY_RECOVERY_HEALTH,
    TUTORIAL_LEVEL_ID,
    get_level_gradient,
)
from entities.player import Player
from levels.level_data import (
    COLLECTIBLE_BY_ID,
    LEVEL_ART,
    LEVEL_TITLES,
    LEVELS,
    MAIN_COLLECTIBLE_IDS,
    level_operation_code,
)
from levels.level_factory import create_level
from states.game_state import GameState
from states.result_state import ResultState
from utils.draw_utils import draw_gradient_background
from utils.keyboard_utils import KeyboardUtils
from utils.ui_art import (
    draw_background,
    draw_image,
    draw_level_map,
    draw_level_map_layers,
    level_map_layout_rect,
    level_map_surface_top,
    load_image,
)
from utils.ui_theme import (
    UI_COLORS,
    draw_chip,
    draw_panel,
    fit_text,
    get_font,
    wrap_text,
)

# 关内背包图标的描边：与打开背包时的高亮同色，沿图标外轮廓 1px。
BAG_ASSET = "images/ui/gameplay/bag.png"
BAG_OUTLINE_COLOR = (165, 231, 190)
_BAG_OUTLINE_CACHE: dict[tuple[int, int], pygame.Surface] = {}


class PlayState(GameState):
    """管理单个关卡的运行状态。"""

    music_scene = "battle"
    DEVELOPER_PANEL_RECT = pygame.Rect(104, 70, 1072, 590)
    BAG_RECT = pygame.Rect(1160, 598, 70, 72)
    BAG_PAGE_SIZE = 10
    BAG_RACK_RECT = pygame.Rect(295, 597, 690, 111)
    BAG_SHADOW_RECT = pygame.Rect(293, 595, 694, 115)
    MENTAL_CHECK_SECONDS = 2.8
    MENTAL_CHECK_RESULT_SECONDS = 1.35
    INTRO_HOLD_SECONDS = 2.0
    INTRO_FADE_SECONDS = 0.6
    MYSTERY_MESSAGES = (
        "什么幸福者退让，我已经开始不幸者惨叫了，开始侥幸者胡闹了，开始自由者搏击了，开始苦难者陈述了，开始爱国者之死了，开始保存者自刎了，开始全知者盲区了，开始引航者试炼了，开始弑君者落地了，开始探索者的银淞止境了，开始沉沦者的黑流树海了",
        "啊啊啊啊啊啊啊啊啊，宝宝，你是个常态不阻挡，DPS低，没法伤，没真伤没穿透，回转慢，技力消耗高，攻击力低，攻速慢，不吃奶没自回，自扣血，没闪避，没锁血，没有防御，再部署时间极长，基建制造站批发，通用一技能，23技能不对空，没模组，上场还要扣费用的超超超超超小杯干员",
        "Tell Me👏 Tell Me👏  鏡👏よ鏡👏  一番👏好きな👏私👏👏になるの👏👏",
        "别闹",
        (
            "看到您直接喊维云斯，我心里咯噔一下，您是怎么想的呢？维云斯也是能直呼其名的？"
            "他是草莓酱香女仆咖啡厅队员、oqtv神人队长、温蒂高手、仙术杯s5冠军、sweep组员、"
            "推坑轴鼻祖、养老院院主、超级鸡马高手、暴打老板领域大神，黎博利小伙、正统术特玩家、"
            "林雨霞厨、蓟县广c歌姬、红温翻面煎蛋大厨，赝波行动1136攻略者，通天联赛初赛3416"
            "最高分获得者，仙术杯#5复赛fmvp3202，骑士被维云箱刺杀高手，通天国际联赛#1冠军，"
            "净罪行动940登顶全网首杀，仙术杯美愿最高分3809拥有者，明日方舟知名三冠王，是磨术师"
            "心里最柔软的地方，这名字太重，您承担不了在这名字后面付出的一切，请您尊称他一声，维神，谢谢！"
        ),
        (
            "所以3809是什么意思🤔，难道是出自明日方舟集成战略up主2025年6月29日的直播，彼时由"
            "龙哥哥今天又鸽了主办的明日方舟集成战略民间赛事仙术杯第七届正在如火如荼地展开中，本届"
            "仙术杯采取团队赛的形式，作为云霄一羽队长出战决赛，使用术特美愿艾拉开，靠着惊人的运营"
            "和熟练度，耗时4小时42分完成了245连打最终得分3809吗"
        ),
        "留意关卡边框或有特殊效果",
        "有些你觉得是bug的地方，也有可能是神秘机制残留",
        "按E进行交互",
        "博士在卫戍协议的一生构成了风花雪月四个字，突袭是来去自由永不停留的风，谢拉格是磅礴恢宏的雪，叙拉古是隐匿云中的月，金币是根本不够花，打一辈子卫是一生，明日方舟是四个字，把我当臭狗一样玩耍是构，发牌员是风字",
        "(兴奋地旋转液泡）(愉悦地鼓动柔软的膜)(激动地扇动多褶的皮)(激动地开合柔软的触肢)(兴奋地扇动多褶的翼膜)(急促地颤动胶质的躯体)(迷惑地摇动细密的触须)(愉悦地颤动胶质的躯体)(兴奋地摇动细密的触须)",
        "你是在商店里出生的恋家果，是大狗追猎前掉落的喷气背包，是失与得换出的板藤，是悲伤的红遇见的血孩子，是果腹，是复得之轮；不像隔壁孩子一样一辈子都是个枯苔藓球",
        "事已至此，去马头边找点薯条，为什么是马头，因为马头牛逼。",
        "你们一定很期待那六个字对吧，听懂掌声。",
        "[2026hpybrd1020]故夢固梦邀请你加入卫戍协议:生日【聚会模拟】",
        "打开燕国地图的秦王看了180秒广告",
        "骗你的，孩子。集齐所有小彩蛋也是没有成就的。",
    )

    def __init__(
        self,
        game,
        level,
        story_mode=False,
        story_index=None,
        recovery_mode=False,
        entry_damage_count=None,
        entry_te_eligible=None,
    ):
        super().__init__(game)

        self.level = level
        self.story_mode = story_mode
        self.story_index = story_index
        self.recovery_mode = recovery_mode
        # 主线进行中从关卡选择重打旧关（自由模式进入）：受伤照常累计进主线
        # 并触发检定，SAN/血量按主线当前进度显示；但通关不推进主线进度。
        self.story_linked = story_mode or bool(game.story_session.get("active"))
        self.entry_damage_count = (
            game.get_story_damage_count()
            if entry_damage_count is None and self.story_linked
            else int(entry_damage_count or 0)
        )
        self.entry_te_eligible = (
            bool(game.story_session.get("te_eligible", True))
            if entry_te_eligible is None and self.story_linked
            else bool(entry_te_eligible)
        )
        self.player = Player(game)
        self.player.allow_bottom_fall = True
        self.player.visual_state = "normal"
        (
            self.platforms,
            self.collect_item,
            self.goal_point,
            self.hazards,
            self.mechanics,
        ) = create_level(level, game.font_cache)
        level_data = LEVELS[level]
        if spawn_layout_id := level_data.get("spawn_layout_id"):
            if not level_data.get("map"):
                raise ValueError(f"Level {level} defines spawn_layout_id without a map")
            self.player.rect.topleft = level_map_layout_rect(
                level_data["map"], spawn_layout_id
            ).topleft
        elif spawn := level_data.get("spawn"):
            self.player.rect.topleft = spawn
        self.spawn_point = self.player.rect.topleft

        # 布局驱动关卡生成后，校正异常悬浮的出口门与下方地形对齐。
        self._repair_door_placement()
        self.bg_gradient = get_level_gradient(level)
        self.damage_count = 0
        self.san = game.get_story_san() if self.story_linked else SAN_INITIAL
        self.health = (
            game.get_story_health() if self.story_linked else STORY_MAX_HEALTH
        )

        if self.collect_item and game.is_item_collected(self.collect_item.item_id):
            self.collect_item.collected = True
            self.player.got_collect = True

        self.player.damage_handler = self._on_player_damage
        self.player.no_damage = self._damage_count() == 0

        self.start_time = time.time()
        self.last_time = time.time()
        self.paused = False
        self.skip_to_victory = False
        self.story_interacted = False
        self.interact_requested = False
        self.damage_flash_timer = 0.0
        self.mental_check_timer = 0.0
        self.mental_check_result = None
        # 加载页底部的抽象文案每次进关随机一条，固定下来避免逐帧重绘闪烁。
        self.mystery_message = random.choice(self.MYSTERY_MESSAGES)
        self.loading_timer = self.INTRO_HOLD_SECONDS + self.INTRO_FADE_SECONDS
        self.victory_handled = False
        self.developer_menu_open = False
        self.debug_overlay_enabled = False
        self.teleport_armed = False
        self.developer_buttons = self._developer_action_rects()
        self.developer_sliders = self._developer_slider_rects()
        self.active_developer_slider = None
        self.bag_open = False
        self.bag_page = 0
        self.bag_item_rects = []
        self.bag_prev_rect = pygame.Rect(0, 0, 0, 0)
        self.bag_next_rect = pygame.Rect(0, 0, 0, 0)

    # 出口门只在明显悬空时向下吸附到实心砖面，绝不上抬到草尖。
    DOOR_SNAP_LOWER = -10
    DOOR_SNAP_UPPER = 50

    def _repair_door_placement(self) -> None:
        """让出口门底面落在正下方实心地形的完整砖面上。

        PSD 布局已经按砖面基准放置出口门；碰撞体却因草叶 alpha 量化把顶边
        抬到草尖，早期逻辑据此把门整体上提，造成悬空。这里改为：向下寻找
        支撑面，用满宽实心行还原真正的砖面基准，只在门明显悬空时下落，任何
        情况下都不再上抬，并同步终点与飞行地刺走廊。
        """
        moved = False
        level_data = LEVELS[self.level]
        map_path = level_data.get("map")
        element_offsets = level_data.get("element_offsets")
        for door in self.mechanics.doors:
            original_rect = door.rect.copy()
            support_top = None
            for platform in self.platforms:
                rect = platform.get_rect()
                if rect.width == 0 or rect.height == 0:
                    continue
                if (
                    rect.left < door.rect.right
                    and rect.right > door.rect.left
                    and rect.top >= door.rect.bottom + self.DOOR_SNAP_LOWER
                    and (support_top is None or rect.top < support_top)
                ):
                    support_top = rect.top
            if support_top is None:
                continue
            surface_top = support_top
            if map_path:
                brick_top = level_map_surface_top(
                    map_path,
                    door.rect.left,
                    door.rect.right,
                    support_top - 6,
                    support_top + 60,
                    element_offsets,
                )
                if brick_top is not None:
                    surface_top = brick_top
            gap = surface_top - door.rect.bottom
            if not (self.DOOR_SNAP_LOWER <= gap <= self.DOOR_SNAP_UPPER):
                continue
            # gap <= 0 表示门已贴合或已扎入砖面，保持 PSD 原始位置，不再上抬。
            if gap <= 0:
                continue
            door.rect.bottom = surface_top
            moved = True
            if self.goal_point.rect == original_rect:
                self.goal_point.rect = door.rect.copy()

        if not moved:
            return
        # 门的位置变化后，重新计算飞行地刺到最近实体的触发走廊。
        blockers = [platform.rect for platform in self.platforms]
        blockers.extend(door.rect for door in self.mechanics.doors)
        blockers.extend(gate.rect for gate in self.mechanics.gates)
        for hazard in self.hazards:
            hazard.configure_trigger(blockers)

    def force_victory(self):
        self.skip_to_victory = True

    def restart_level(self):
        """按进入本关时的受伤状态重新创建关卡。"""

        if self.story_linked:
            self.game.story_session.update(
                {
                    "damage_count": self.entry_damage_count,
                    "san": self.game._san_for_damage_count(self.entry_damage_count),
                    "health": self.game.get_story_health()
                    if self.recovery_mode
                    else max(1, STORY_MAX_HEALTH - self.entry_damage_count),
                    "te_eligible": self.entry_te_eligible,
                }
            )
            self.game.save_progress()
        return PlayState(
            self.game,
            self.level,
            story_mode=self.story_mode,
            story_index=self.story_index,
            recovery_mode=self.recovery_mode,
            entry_damage_count=self.entry_damage_count,
            entry_te_eligible=self.entry_te_eligible,
        )

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F12:
                    if event.mod & pygame.KMOD_SHIFT:
                        self.developer_menu_open = True
                        self.active_developer_slider = None
                    else:
                        self.debug_overlay_enabled = not self.debug_overlay_enabled
                    continue
                if event.key == pygame.K_ESCAPE and self.developer_menu_open:
                    self.developer_menu_open = False
                    self.active_developer_slider = None
                elif event.key == pygame.K_ESCAPE and self.teleport_armed:
                    self.teleport_armed = False
                elif self.developer_menu_open:
                    continue
                elif event.key == pygame.K_b:
                    self._open_collectibles()
                elif event.key in (pygame.K_SPACE, pygame.K_w, pygame.K_UP):
                    self.player.jump()
                elif event.key == pygame.K_ESCAPE:
                    from states.pause_menu_state import PauseMenuState

                    self.game.change_state(PauseMenuState(self.game, self))
                elif event.key in (pygame.K_e, pygame.K_x):
                    if self.story_interacted:
                        self.story_interacted = False
                    else:
                        self.interact_requested = True
                        self._check_story_blocks()
                elif event.key == pygame.K_RETURN and self.story_interacted:
                    self.story_interacted = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.developer_menu_open:
                    for slider, rect in self.developer_sliders.items():
                        if rect.collidepoint(event.pos):
                            self.active_developer_slider = slider
                            self._set_developer_slider(slider, event.pos[0])
                            break
                    else:
                        for action, rect in self.developer_buttons.items():
                            if rect.collidepoint(event.pos):
                                self._run_developer_action(action)
                                break
                    continue
                if self.teleport_armed:
                    self._teleport_player(event.pos)
                    self.teleport_armed = False
                    continue
                if self.BAG_RECT.collidepoint(event.pos):
                    self._open_collectibles()
                    continue
                if self.bag_open and self.bag_next_rect.collidepoint(event.pos):
                    max_page = self._max_bag_page()
                    self.bag_page = (self.bag_page + 1) % (max_page + 1)
                    continue
                if self.story_interacted:
                    self.story_interacted = False
            elif event.type == pygame.MOUSEWHEEL and self.bag_open:
                if event.y > 0:
                    self.bag_page = max(0, self.bag_page - 1)
                elif event.y < 0:
                    self.bag_page = min(self._max_bag_page(), self.bag_page + 1)
            elif event.type == pygame.MOUSEMOTION:
                if self.developer_menu_open and self.active_developer_slider:
                    self._set_developer_slider(
                        self.active_developer_slider,
                        event.pos[0],
                    )
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.active_developer_slider = None

    def _teleport_player(self, position) -> None:
        """将玩家安全地放到一次性开发者选点的位置。"""

        self.player.rect.center = position
        self.player.rect.clamp_ip(pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
        self.player.previous_rect = self.player.rect.copy()
        self.player.vx = 0.0
        self.player.vy = 0.0
        self.player.jumping = False
        self.player.on_ground = False
        self.player.on_moving = None
        self.player.last_support_y = None
        self.player.fall_origin_y = None

    def _open_collectibles(self) -> None:
        """在关卡内展开背包，不中断当前关卡。"""

        self.bag_open = not self.bag_open
        self.bag_page = min(self.bag_page, self._max_bag_page())

    def _bag_items(self):
        return [
            item_id
            for item_id in MAIN_COLLECTIBLE_IDS
            if self.game.is_item_collected(item_id)
        ]

    def _max_bag_page(self):
        return max(0, (len(self._bag_items()) - 1) // self.BAG_PAGE_SIZE)

    @classmethod
    def _developer_action_rects(cls):
        """返回开发者面板统一使用的可见和点击矩形。"""

        panel = cls.DEVELOPER_PANEL_RECT
        left = panel.x + 34
        top = panel.y + 224
        width = 324
        height = 58
        gap_x = 16
        gap_y = 8
        actions = (
            "teleport",
            "respawn",
            "damage",
            "next_damage_event",
            "reset_damage",
            "collectible",
            "unlock_mechanics",
            "achievement",
            "victory",
            "ending_be",
            "ending_te",
            "ending_he",
            "unlock_be",
            "unlock_he",
            "unlock_te",
        )
        rects = {
            action: pygame.Rect(
                left + (index % 3) * (width + gap_x),
                top + (index // 3) * (height + gap_y),
                width,
                height,
            )
            for index, action in enumerate(actions)
        }
        # 保护模式快捷入口不占用 3 列网格，单独放在标题行右侧，保留原有动作排布。
        rects["protection"] = pygame.Rect(panel.right - 260, panel.y + 14, 226, 58)
        return rects

    @classmethod
    def _developer_slider_rects(cls):
        panel = cls.DEVELOPER_PANEL_RECT
        return {
            "run_speed": pygame.Rect(panel.x + 34, panel.y + 116, 494, 82),
            "jump_height": pygame.Rect(panel.x + 544, panel.y + 116, 494, 82),
        }

    @staticmethod
    def _developer_slider_track(rect):
        return pygame.Rect(rect.x + 18, rect.bottom - 27, rect.width - 36, 8)

    def _set_developer_slider(self, slider, mouse_x):
        track = self._developer_slider_track(self.developer_sliders[slider])
        ratio = max(0.0, min(1.0, (mouse_x - track.left) / track.width))
        if slider == "run_speed":
            value = PLAYER_RUN_SPEED_MIN + ratio * (
                PLAYER_RUN_SPEED_MAX - PLAYER_RUN_SPEED_MIN
            )
            value = round(value, 1)
            self.game.developer_run_speed = value
            self.player.run_speed = value
            return
        value = PLAYER_JUMP_HEIGHT_MIN + ratio * (
            PLAYER_JUMP_HEIGHT_MAX - PLAYER_JUMP_HEIGHT_MIN
        )
        value = round(value / 5) * 5.0
        self.game.developer_jump_height = value
        self.player.jump_height = value

    def _run_developer_action(self, action):
        """执行一个明确、可重复的关卡调试动作。"""

        enabled, unavailable_reason = self._developer_action_availability(action)
        if not enabled:
            self.game.ui_manager.show_toast(
                "当前操作不可用",
                unavailable_reason,
                UI_COLORS["gold"],
            )
            return

        if action == "teleport":
            self.developer_menu_open = False
            self.teleport_armed = True
        elif action == "respawn":
            self._teleport_player(self.spawn_point)
            self.game.ui_manager.show_toast("开发者工具", "已返回当前关卡出生点。")
        elif action == "damage":
            self._developer_simulate_damage()
        elif action == "next_damage_event":
            self._developer_jump_to_next_damage_event()
        elif action == "reset_damage":
            self._developer_reset_damage()
        elif action == "collectible":
            self._developer_collect_current_item()
        elif action == "unlock_mechanics":
            self._developer_unlock_mechanics()
        elif action == "achievement":
            self._developer_complete_random_achievement()
        elif action == "victory":
            self.developer_menu_open = False
            self.force_victory()
        elif action in {"ending_be", "ending_te", "ending_he"}:
            self.developer_menu_open = False
            self._developer_play_ending(action.removeprefix("ending_").upper())
        elif action in {"unlock_be", "unlock_he", "unlock_te"}:
            self._developer_unlock_ending(action.removeprefix("unlock_").upper())
        elif action == "protection":
            self._developer_enter_protection()

    def _developer_enter_protection(self):
        """开发者快捷：让当前主线立即进入保护模式。"""

        self.game.story_session["recovery_mode"] = True
        self.recovery_mode = True
        self.health = STORY_RECOVERY_HEALTH
        self.game.save_recovery("developer")
        self.developer_menu_open = False
        self.game.ui_manager.show_toast(
            "保护模式启动",
            "当前主线已进入保护模式：血量固定 1，免疫致命伤害。",
            UI_COLORS["red"],
            duration=3.0,
        )

    def _developer_play_ending(self, ending_type):
        """立即停止本关并播放指定结局演示。"""

        from states.ending_state import EndingState

        self.game.change_state(EndingState(self.game, ending_type))

    def _developer_unlock_ending(self, ending_type):
        """开发者快捷：解锁结局的成就与外观，并把主菜单封面切换到该结局。"""

        # 主菜单按 active_ending 优先取封面，必须先切过去，否则会停留在旧结局。
        self.game.active_ending = ending_type
        # 与正式结算一致：HE 解锁 maid、TE 解锁 endgame 等，避免只切封面没解锁皮肤。
        self.game.unlock_ending_rewards(ending_type)
        if ending_type in self.game.ending_history:
            self.game.ui_manager.show_toast(
                f"已切换到 {ending_type} 封面", "该结局此前已解锁。"
            )
            return
        self.game.ending_history.append(ending_type)
        self.game.save_progress()
        self.game.ui_manager.show_toast(
            f"已解锁 {ending_type} 结局", "返回主菜单即可看到对应封面。"
        )

    def _developer_action_availability(self, action):
        """统一控制开发者操作的显示状态和点击行为。"""

        if (
            action in {"damage", "next_damage_event", "reset_damage"}
            and self.recovery_mode
        ):
            return False, "剧情恢复后处于隐形无敌状态，受伤与 SAN 不再变化。"
        if action == "protection" and not self.story_mode:
            return False, "保护模式只作用于主线关卡。"
        if action == "protection" and (self.recovery_mode or self.game.sanity_broken):
            return False, "当前主线已处于保护模式。"
        if action == "next_damage_event" and not self.story_mode:
            return False, "SAN 检定节点只存在于故事模式。"
        if action == "collectible" and self.collect_item is None:
            return False, "当前关卡没有可收集的藏品。"
        if action == "achievement":
            achievements = self.game.achievement_system.get_all_achievements()
            if not any(
                achievement_id != "all_achievements"
                and not achievement["completed"]
                for achievement_id, achievement in achievements.items()
            ):
                return False, "所有可单独完成的成就均已解锁。"
        return True, ""

    def _developer_simulate_damage(self):
        if self.recovery_mode:
            self.game.ui_manager.show_toast(
                "无法模拟受伤",
                "当前是剧情恢复后的隐形无敌状态。",
                UI_COLORS["gold"],
            )
            return
        self.developer_menu_open = False
        self._on_player_damage("developer", bypass_streamer_mode=True)

    def _developer_jump_to_next_damage_event(self):
        if not self.story_mode:
            self.game.ui_manager.show_toast(
                "仅限主线",
                "SAN 节点只存在于故事模式。",
                UI_COLORS["gold"],
            )
            return
        if self.recovery_mode:
            self.game.ui_manager.show_toast(
                "无法调整 SAN",
                "当前是剧情恢复后的隐形无敌状态。",
                UI_COLORS["gold"],
            )
            return

        current = self.game.get_story_damage_count()
        target = next((value for value in (3, 5, 7, 10) if value > current), None)
        if target is None:
            self.game.ui_manager.show_toast("已到最终节点", "当前受伤次数已经达到 10。")
            return

        before_target = target - 1
        self.game.story_session.update(
            {
                "damage_count": before_target,
                "san": self.game._san_for_damage_count(before_target),
                "te_eligible": False,
                "visual_state": "normal",
            }
        )
        self.developer_menu_open = False
        self._on_player_damage("developer", bypass_streamer_mode=True)

    def _developer_reset_damage(self):
        if self.recovery_mode:
            self.game.ui_manager.show_toast(
                "无法重置状态",
                "恢复流程必须继续到主线结束。",
                UI_COLORS["gold"],
            )
            return

        if self.story_mode:
            self.game.story_session.update(
                {
                    "damage_count": 0,
                    "san": SAN_INITIAL,
                    "te_eligible": True,
                    "visual_state": "normal",
                }
            )
            self.game.save_progress()
        else:
            self.damage_count = 0
            self.san = SAN_INITIAL
        self.player.no_damage = True
        self.player.visual_state = "normal"
        self.player.damage_cooldown = 0.0
        self.damage_flash_timer = 0.0
        self.game.ui_manager.show_toast(
            "状态已重置", "受伤 0 次，SAN 计数 0/10。", UI_COLORS["green"]
        )

    def _developer_collect_current_item(self):
        if not self.collect_item:
            self.game.ui_manager.show_toast("当前关卡无藏品", "没有可收集的藏品。")
            return
        item_id = self.collect_item.item_id
        if self.game.is_item_collected(item_id):
            self.game.ui_manager.show_toast(
                "藏品已收集", COLLECTIBLE_BY_ID[item_id]["name"]
            )
            return
        self.collect_item.collected = True
        self.player.got_collect = True
        self.game.collect_item(item_id)
        item = COLLECTIBLE_BY_ID[item_id]
        self.game.ui_manager.show_toast(
            "开发者工具：获得藏品",
            f"{item['helper']} · {item['name']}",
            UI_COLORS["gold"],
        )

    def _developer_unlock_mechanics(self):
        for key in self.mechanics.keys:
            key.collected = True
        for door in self.mechanics.doors:
            door.unlocked = True
        for lever in self.mechanics.levers:
            lever.activated = True
        for gate in self.mechanics.gates:
            gate.open = True
        self.mechanics.update(self.player.rect, False)
        self.game.ui_manager.show_toast(
            "机关已解锁",
            "钥匙、门、拉杆与栅栏已全部完成。",
            UI_COLORS["green"],
        )

    def _developer_complete_random_achievement(self):
        achievements = self.game.achievement_system.get_all_achievements()
        candidates = [
            achievement_id
            for achievement_id, achievement in achievements.items()
            if achievement_id != "all_achievements" and not achievement["completed"]
        ]
        if not candidates:
            self.game.ui_manager.show_toast(
                "没有可完成的成就",
                "所有可单独完成的成就均已解锁。",
                UI_COLORS["gold"],
            )
            return
        self.game.achievement_system.unlock(random.choice(candidates))

    def update(self, dt):
        if self.loading_timer > 0:
            self.loading_timer = max(0.0, self.loading_timer - dt)
            if self.loading_timer == 0:
                self.start_time = time.time()
                self.last_time = self.start_time
            return
        if self.mental_check_timer > 0:
            self.mental_check_timer = max(0.0, self.mental_check_timer - dt)
            self.last_time = time.time()
            if self.mental_check_timer == 0:
                # 检定失败不再当场跳结局：结算立绘与结局由 game 侧标记决定。
                self.mental_check_result = None
            return
        if self.skip_to_victory:
            self._victory(skip=True)
            return

        current_time = time.time()
        dt = max(0.0, min(current_time - self.last_time, 0.1))
        self.last_time = current_time
        if dt == 0:
            dt = 1 / 60

        keys = KeyboardUtils.get_keys_pressed()
        if keys["w"] or keys["space"] or keys["up"]:
            self.player.jump()
        if keys["e"] or keys["x"]:
            self.interact_requested = True
            self._check_story_blocks()

        for platform in self.platforms:
            platform.update(dt, player_rect=self.player.rect)
        for hazard in self.hazards:
            hazard.update(dt, player_rect=self.player.rect)
        self.mechanics.update(self.player.rect, self.interact_requested)
        self.interact_requested = False

        goal_to_check = self.goal_point if self.mechanics.goal_unlocked else None
        self.player.update(
            self.platforms,
            self.collect_item
            if self.collect_item and not self.collect_item.collected
            else None,
            goal_to_check,
            dt,
            check_bounds=True,
            hazards=self.hazards,
            blockers=self.mechanics.get_blockers(),
        )
        if self.game.current_state is not self:
            return
        if self.player.rect.bottom >= SCREEN_HEIGHT:
            self.player.take_damage("fall")
            if self.game.current_state is not self:
                return
            self._teleport_player(self.spawn_point)

        self.goal_point.update(dt)

        if (
            self.collect_item
            and self.collect_item.collected
            and not self.game.is_item_collected(self.collect_item.item_id)
            and self.game.collect_item(self.collect_item.item_id)
        ):
            item = COLLECTIBLE_BY_ID.get(self.collect_item.item_id, {})
            name = item.get("name", "藏品")
            self.game.ui_manager.show_collectible_notification(name)

        self.damage_flash_timer = max(0.0, self.damage_flash_timer - dt)

        if self.player.reached_goal:
            self._victory(skip=False)

    def _on_player_damage(self, reason, *, bypass_streamer_mode=False):
        if (
            self.recovery_mode
            or self.game.sanity_broken
            or (self.game.streamer_mode and not bypass_streamer_mode)
        ):
            return

        if self.story_linked:
            event = self.game.register_story_damage(
                reason,
                bypass_streamer_mode=bypass_streamer_mode,
            )
            self.damage_count = self.game.get_story_damage_count()
            self.san = self.game.get_story_san()
            self.health = self.game.get_story_health()
        else:
            self.damage_count += 1
            self.san = min(SAN_FATAL_DAMAGE_COUNT, self.damage_count)
            self.health = max(1, STORY_MAX_HEALTH - self.damage_count)
            self.game.achievement_system.unlock("first_damage")
            event = "DAMAGE"

        if event:
            self.damage_flash_timer = 0.25

        if event == "SAN_WARNING_3":
            self.game.ui_manager.show_toast(
                "",
                "血液流失加剧，你的意识需要保持清醒。",
                UI_COLORS["purple"],
                duration=4.0,
            )
        elif event in {"MENTAL_CHECK_SUCCESS", "MENTAL_CHECK_FAILURE"}:
            self.mental_check_result = event
            self.mental_check_timer = self.MENTAL_CHECK_SECONDS
        elif event == "FATAL":
            from states.fatal_error_state import FatalErrorState

            self.game.ui_manager.show_toast(
                "保护模式启动",
                "检测到致命伤害，保护模式启动。",
                UI_COLORS["red"],
                duration=3.0,
            )
            self.game.change_state(FatalErrorState(self.game))

    def _damage_count(self):
        if self.story_linked:
            return self.game.get_story_damage_count()
        return self.damage_count

    def _victory(self, skip=False):
        if self.victory_handled:
            return
        self.victory_handled = True

        elapsed = time.time() - self.start_time
        no_damage = self._damage_count() == self.entry_damage_count
        has_collectible = bool(
            self.collect_item and self.game.is_item_collected(self.collect_item.item_id)
        ) or self.level == TUTORIAL_LEVEL_ID
        stars = 1 if skip else self._calculate_stars(no_damage, has_collectible)
        if stars > self.game.level_progress.get(self.level, 0):
            self.game.level_progress[self.level] = stars
        self.game.save_progress()

        time_str = f"{int(elapsed // 60)}:{int(elapsed % 60):02d}"
        result_state = ResultState(
            self.game,
            self.level,
            stars,
            time_str,
            story_mode=self.story_mode,
            story_index=self.story_index,
            entry_damage_count=self.entry_damage_count,
            entry_te_eligible=self.entry_te_eligible,
        )
        if skip:
            # 开发者快捷：跳过结算前的黑屏/频谱视频与其音频，直接进入结算动画。
            self.game.audio_system.stop_bgm()
            self.game.change_state(result_state)
            return

        from states.video_state import CompletionVideoState

        self.game.change_state(
            CompletionVideoState(self.game, result_state, self.level)
        )

    @staticmethod
    def _calculate_stars(no_damage, has_collectible):
        return 1 + int(bool(no_damage)) + int(bool(has_collectible))

    def _check_story_blocks(self):
        """剧情方块仅作为可选交互，不再阻塞终点。"""
        self.mechanics.update(self.player.rect, True)
        for platform in self.platforms:
            platform.update(0, player_rect=self.player.rect)
            for block in platform.story_blocks:
                block.update(0, platform=platform, player_rect=self.player.rect)
                if block.active and block.show_prompt and block.activate_story():
                    self.story_interacted = True

    def draw(self, screen):
        draw_gradient_background(screen, self.bg_gradient[0], self.bg_gradient[1])
        level_art = LEVEL_ART.get(self.level)
        if level_art:
            try:
                draw_background(screen, level_art)
            except (FileNotFoundError, pygame.error):
                pass

        map_path = LEVELS[self.level].get("map")
        foreground_layer_paths = LEVELS[self.level].get("foreground_layer_paths")
        element_offsets = LEVELS[self.level].get("element_offsets")
        self.mechanics.draw_gates(screen, [])
        if map_path:
            draw_level_map(
                screen,
                map_path,
                excluded_element_types={"spike"},
                excluded_layer_paths=foreground_layer_paths or frozenset(),
                element_offsets=element_offsets,
            )

        for platform in self.platforms:
            platform.draw(screen, [])
        for hazard in self.hazards:
            hazard.draw(screen, [])
        if map_path and foreground_layer_paths:
            # 前景框条画在机关之后，才能盖住位于其下方的刺。
            draw_level_map_layers(
                screen, map_path, foreground_layer_paths, element_offsets=element_offsets
            )
        self.mechanics.draw_foreground(screen, [])
        if self.collect_item and not self.collect_item.collected:
            self.collect_item.update(1 / 60)
            self.collect_item.draw(screen, [])
        self.goal_point.draw(screen, [])
        self.player.draw(screen, [])

        self._draw_ui(screen)
        if self.bag_open:
            self._draw_bag_overlay(screen)
        if self.teleport_armed:
            self._draw_teleport_hint(screen)
        if self.debug_overlay_enabled:
            from utils.debug_overlay import draw_debug_overlay

            draw_debug_overlay(screen, self)
        if self.developer_menu_open:
            self._draw_developer_menu(screen)
        if self.damage_flash_timer > 0:
            self._draw_damage_flash(screen)
        if self.loading_timer > 0:
            self._draw_loading_overlay(screen)
        if self.mental_check_timer > 0:
            self._draw_mental_check_overlay(screen)

    def _draw_mental_check_overlay(self, screen):
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 4, 7, 226))
        screen.blit(overlay, (0, 0))

        if self.mental_check_timer > self.MENTAL_CHECK_RESULT_SECONDS:
            message = "进行神经流数据检定……请稍等……"
            color = (177, 224, 215)
        elif self.mental_check_result == "MENTAL_CHECK_SUCCESS":
            message = "你找回了理智，那么，请继续吧。"
            color = (126, 238, 180)
        else:
            message = "神经流数据检定失败……"
            color = (255, 105, 118)

        frame = pygame.time.get_ticks() // 85
        noise = "#%?/\\01"
        glitched = "".join(
            noise[(index + frame) % len(noise)]
            if character.strip() and (index + frame) % 7 == 0
            else character
            for index, character in enumerate(message)
        )
        font = get_font(self.game.font_cache, "medium")
        text = fit_text(font, glitched, SCREEN_WIDTH - 180, color)
        jitter_x = (-2, 1, 3, -1)[frame % 4]
        screen.blit(
            text,
            text.get_rect(center=(SCREEN_WIDTH // 2 + jitter_x, SCREEN_HEIGHT // 2)),
        )
        for y in range(70 + frame % 11, SCREEN_HEIGHT, 34):
            pygame.draw.line(screen, (48, 88, 84), (0, y), (SCREEN_WIDTH, y), 1)

    def _draw_ui(self, screen):
        if LEVELS[self.level].get("hud_style") == "compact":
            self._draw_compact_ui(screen)
            return

        level_label = (
            LEVEL_TITLES[self.level]
            if self.level == TUTORIAL_LEVEL_ID
            else f"第{self.level}关"
        )
        elapsed = time.time() - self.start_time
        san = self.game.get_story_san() if self.story_linked else self.san
        status = "生命稳定"

        hud = pygame.Rect(24, 22, SCREEN_WIDTH - 48, 64)
        draw_panel(
            screen,
            hud,
            fill=(18, 27, 42),
            border=UI_COLORS["border"],
            radius=10,
            shadow=False,
        )
        caption = get_font(self.game.font_cache, "caption")
        body = get_font(self.game.font_cache, "body")
        try:
            draw_image(
                screen,
                "images/ui/gameplay/bag.png",
                pygame.Rect(38, 30, 32, 36),
                smooth=False,
            )
            draw_image(
                screen,
                "images/ui/gameplay/key.png",
                pygame.Rect(80, 34, 18, 32),
                smooth=False,
            )
        except (FileNotFoundError, pygame.error):
            pass
        screen.blit(fit_text(body, level_label, 174, UI_COLORS["text"]), (112, 35))
        draw_chip(
            screen,
            pygame.Rect(252, 37, 132, 28),
            "主线" if self.story_mode else "自由关卡",
            get_font(self.game.font_cache, "micro"),
            UI_COLORS["purple"] if self.story_mode else UI_COLORS["accent"],
        )
        time_text = f"{int(elapsed // 60)}:{int(elapsed % 60):02d}"
        time_surface = fit_text(body, f"时间  {time_text}", 180, UI_COLORS["accent"])
        screen.blit(
            time_surface, time_surface.get_rect(center=(SCREEN_WIDTH // 2, hud.centery))
        )
        screen.blit(
            fit_text(caption, status, 260, UI_COLORS["text"]),
            (SCREEN_WIDTH - 350, 34),
        )
        draw_chip(
            screen,
            pygame.Rect(SCREEN_WIDTH - 154, 37, 108, 28),
            "SAN",
            get_font(self.game.font_cache, "micro"),
            UI_COLORS["red"] if san >= 5 else UI_COLORS["purple"],
        )
        if self.story_interacted:
            self._draw_dialogue_overlay(screen)

    @staticmethod
    def _bag_outline(size):
        """返回背包图标沿外轮廓 1px 的描边，按尺寸缓存。"""

        cached = _BAG_OUTLINE_CACHE.get(size)
        if cached is None:
            silhouette = pygame.mask.from_surface(
                pygame.transform.scale(load_image(BAG_ASSET), size), 40
            )
            cached = pygame.Surface((size[0] + 2, size[1] + 2), pygame.SRCALPHA)
            ring = silhouette.to_surface(
                setcolor=BAG_OUTLINE_COLOR, unsetcolor=(0, 0, 0, 0)
            )
            for offset in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                cached.blit(ring, (1 + offset[0], 1 + offset[1]))
            # 挖掉图标本体，只留下沿轮廓的一圈。
            cached.blit(
                silhouette.to_surface(
                    setcolor=(255, 255, 255, 0), unsetcolor=(255, 255, 255, 255)
                ),
                (1, 1),
                special_flags=pygame.BLEND_RGBA_MULT,
            )
            _BAG_OUTLINE_CACHE[size] = cached
        return cached

    def _draw_compact_ui(self, screen):
        """使用正式素材绘制随 SAN 实时变化的紧凑状态栏。"""

        origin = pygame.Vector2(28, 22)
        draw_image(
            screen,
            "images/ui/gameplay/status/base.png",
            pygame.Rect(origin.x, origin.y, 294, 56),
            smooth=False,
        )
        fill_rect = pygame.Rect(origin.x + 69, origin.y + 23, 218, 22)
        fill_surface = pygame.transform.scale(
            load_image("images/ui/gameplay/status/fill.png"),
            fill_rect.size,
        )
        remaining_ratio = self.health / STORY_MAX_HEALTH
        remaining_width = round(fill_rect.width * remaining_ratio)
        if remaining_width > 0:
            screen.blit(
                fill_surface,
                fill_rect,
                pygame.Rect(0, 0, remaining_width, fill_rect.height),
            )
        draw_image(
            screen,
            "images/ui/gameplay/status/frame.png",
            pygame.Rect(origin.x + 63, origin.y + 18, 230, 33),
            smooth=False,
        )
        draw_image(
            screen,
            "images/ui/gameplay/status/portrait.png",
            # 左缘不动、宽度逐次 +1px，使头像视觉中心右移，每次约半个像素。
            pygame.Rect(origin.x, origin.y + 2, 56, 53),
            smooth=False,
        )
        outline = self._bag_outline(self.BAG_RECT.size)
        screen.blit(outline, (self.BAG_RECT.x - 1, self.BAG_RECT.y - 1))
        draw_image(
            screen,
            BAG_ASSET,
            self.BAG_RECT,
            smooth=False,
        )
        if self.bag_open:
            pygame.draw.rect(
                screen,
                (165, 231, 190),
                self.BAG_RECT.inflate(6, 6),
                2,
                border_radius=4,
            )

    def _draw_bag_overlay(self, screen):
        """用原素材在关卡底部渲染已获得藏品，悬停时显示名称。"""

        rack = self.BAG_RACK_RECT
        draw_image(
            screen,
            "images/ui/gameplay/backpack/shadow.png",
            self.BAG_SHADOW_RECT,
        )
        draw_image(
            screen,
            "images/ui/gameplay/backpack/rack.png",
            rack,
        )

        scale = rack.width / 1035
        slot_size = max(1, round(75 * scale))
        slot_top = rack.y + round(76 * scale)
        column_pitch = 824 / 9

        items = self._bag_items()
        max_page = self._max_bag_page()
        self.bag_page = min(self.bag_page, max_page)
        start = self.bag_page * self.BAG_PAGE_SIZE
        visible_items = items[start : start + self.BAG_PAGE_SIZE]

        mouse_position = pygame.mouse.get_pos()
        self.bag_item_rects = []
        hovered_item = None
        for index in range(self.BAG_PAGE_SIZE):
            rect = pygame.Rect(
                rack.x + round((68 + index * column_pitch) * scale),
                slot_top,
                slot_size,
                slot_size,
            )
            if index >= len(visible_items):
                continue
            item_id = visible_items[index]
            self.bag_item_rects.append((item_id, rect))
            icon_rect = rect.inflate(-6, -6)
            image = load_image(f"images/collectibles/{item_id}.png")
            factor = min(
                icon_rect.width / image.get_width(),
                icon_rect.height / image.get_height(),
            )
            target = pygame.Rect(
                0,
                0,
                max(1, round(image.get_width() * factor)),
                max(1, round(image.get_height() * factor)),
            )
            target.center = rect.center
            draw_image(
                screen,
                f"images/collectibles/{item_id}.png",
                target,
                smooth=True,
            )
            if rect.collidepoint(mouse_position):
                hovered_item = item_id
                draw_image(
                    screen,
                    "images/ui/gameplay/backpack/selector.png",
                    rect,
                )

        micro = get_font(self.game.font_cache, "micro")
        if not items:
            empty = fit_text(micro, "尚未获得藏品", rack.width, (150, 186, 170))
            screen.blit(empty, empty.get_rect(center=rack.center))
            self.bag_next_rect = pygame.Rect(0, 0, 0, 0)
        elif max_page > 0:
            self.bag_next_rect = pygame.Rect(rack.right - 34, rack.bottom - 24, 26, 16)
            draw_image(
                screen,
                "images/ui/gameplay/backpack/next_page.png",
                self.bag_next_rect,
            )
        else:
            self.bag_next_rect = pygame.Rect(0, 0, 0, 0)

        self.bag_prev_rect = pygame.Rect(0, 0, 0, 0)

        if hovered_item:
            name = COLLECTIBLE_BY_ID[hovered_item]["name"]
            tooltip = fit_text(micro, name, 240, UI_COLORS["text"])
            tooltip_rect = tooltip.get_rect(
                midbottom=(mouse_position[0], rack.y - 8)
            ).inflate(18, 10)
            tooltip_rect.clamp_ip(
                pygame.Rect(8, 8, SCREEN_WIDTH - 16, SCREEN_HEIGHT - 16)
            )
            draw_panel(
                screen,
                tooltip_rect,
                fill=(12, 34, 29),
                border=(128, 188, 155),
                radius=3,
                shadow=False,
            )
            screen.blit(tooltip, tooltip.get_rect(center=tooltip_rect.center))

    def _draw_dialogue_overlay(self, screen):
        """使用需求中的对话框素材显示一次已触发的剧情提示。"""

        frame = pygame.Rect(126, 492, 1028, 220)
        try:
            draw_image(screen, "images/ui/gameplay/dialogue_frame.png", frame)
        except (FileNotFoundError, pygame.error):
            return
        message = "记录已同步。继续向上，直到抵达终点。"
        font = get_font(self.game.font_cache, "body")
        screen.blit(
            fit_text(font, message, frame.width - 100, UI_COLORS["text"]),
            (frame.x + 48, frame.y + 78),
        )
        hint = get_font(self.game.font_cache, "micro").render(
            "E / Enter / 点击  关闭", True, UI_COLORS["muted"]
        )
        screen.blit(hint, (frame.right - 110, frame.bottom - 46))

    def _draw_loading_overlay(self, screen):
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((4, 11, 15, 255))
        pygame.draw.line(overlay, (133, 186, 178), (92, 335), (1188, 335), 2)
        operation = fit_text(
            get_font(self.game.font_cache, "caption"),
            level_operation_code(self.level),
            760,
            (133, 186, 178),
        )
        title = fit_text(
            get_font(self.game.font_cache, "large"),
            LEVEL_TITLES[self.level],
            900,
            UI_COLORS["text"],
        )
        message_font = get_font(self.game.font_cache, "caption")
        message_lines = wrap_text(
            message_font,
            f"【{self.mystery_message}】",
            1080,
        )
        overlay.blit(operation, operation.get_rect(center=(640, 286)))
        overlay.blit(title, title.get_rect(center=(640, 385)))
        visible_message_lines = message_lines
        if self.level == TUTORIAL_LEVEL_ID:
            hint = fit_text(
                get_font(self.game.font_cache, "body"),
                "点按 ASWD 进行上下左右移动    点按 E 进行交互",
                900,
                (211, 229, 224),
            )
            overlay.blit(hint, hint.get_rect(center=(640, 485)))

        message_step = message_font.get_linesize() + 3
        message_y = 687 - (len(visible_message_lines) - 1) * message_step
        pygame.draw.line(
            overlay,
            (69, 104, 98),
            (180, message_y - 22),
            (1100, message_y - 22),
            1,
        )
        for line in visible_message_lines:
            message = fit_text(message_font, line, 1080, (167, 190, 186))
            overlay.blit(message, message.get_rect(center=(640, message_y)))
            message_y += message_step

        opacity = 255
        if self.loading_timer < self.INTRO_FADE_SECONDS:
            opacity = round(255 * self.loading_timer / self.INTRO_FADE_SECONDS)
        overlay.set_alpha(max(0, min(255, opacity)))
        screen.blit(overlay, (0, 0))

    def _draw_developer_menu(self, screen):
        """绘制仅在关卡内可用的开发者工具覆盖层。"""

        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 188))
        screen.blit(overlay, (0, 0))
        panel = self.DEVELOPER_PANEL_RECT
        draw_panel(
            screen, panel, fill=(20, 31, 49), border=UI_COLORS["accent"], radius=14
        )
        title_font = get_font(self.game.font_cache, "button")
        body_font = get_font(self.game.font_cache, "caption")
        micro_font = get_font(self.game.font_cache, "micro")
        screen.blit(
            title_font.render("关卡开发者工具", True, UI_COLORS["accent"]),
            (panel.x + 34, panel.y + 18),
        )
        damage_count = self._damage_count()
        san = self.game.get_story_san() if self.story_linked else self.san
        mode = "主线" if self.story_mode else "自由关卡"
        protection = (
            " · 隐形无敌"
            if self.recovery_mode
            else " · 主播保护"
            if self.game.streamer_mode
            else ""
        )
        status = (
            f"{mode}{protection}    第 {self.level} 关    "
            f"受伤 {damage_count} 次    SAN {san}/{SAN_FATAL_DAMAGE_COUNT}"
        )
        screen.blit(
            body_font.render(status, True, UI_COLORS["text"]),
            (panel.x + 34, panel.y + 54),
        )
        description = (
            "调试操作会直接影响当前关卡和存档；“模拟受伤”会让受伤和 SAN 计数各 +1。"
        )
        screen.blit(
            micro_font.render(description, True, UI_COLORS["muted"]),
            (panel.x + 34, panel.y + 84),
        )

        self._draw_developer_slider(
            screen,
            self.developer_sliders["run_speed"],
            "横向跑动速度",
            self.player.run_speed,
            PLAYER_RUN_SPEED_MIN,
            PLAYER_RUN_SPEED_MAX,
            f"{self.player.run_speed:.1f}",
        )
        self._draw_developer_slider(
            screen,
            self.developer_sliders["jump_height"],
            "跳跃高度",
            self.player.jump_height,
            PLAYER_JUMP_HEIGHT_MIN,
            PLAYER_JUMP_HEIGHT_MAX,
            f"{round(self.player.jump_height)} px",
        )

        action_content = {
            "teleport": ("选择位置传送", "关闭面板后，在地图中左键放置角色", "primary"),
            "respawn": ("返回出生点", "回到当前关卡的初始出生位置", "secondary"),
            "damage": ("模拟受伤 +1", "累计受伤一次，并让 SAN 计数 +1", "danger"),
            "next_damage_event": (
                "跳到下个 SAN 节点",
                "依次测试第 3、5、7、10 次受伤",
                "danger",
            ),
            "reset_damage": (
                "重置受伤与 SAN",
                "恢复为受伤 0 次、SAN 计数 0/10",
                "success",
            ),
            "collectible": ("获得当前藏品", "立即收集并保存本关藏品", "secondary"),
            "unlock_mechanics": ("解锁全部机关", "完成钥匙、门、拉杆和栅栏", "success"),
            "achievement": ("随机完成成就", "随机解锁一个尚未完成的成就", "success"),
            "victory": ("直接完成本关", "进入本关结算；主线可继续下一关", "primary"),
            "ending_be": ("结局·BE", "直接播放 BE 结局演示", "danger"),
            "ending_te": ("结局·TE", "直接播放 TE 结局演示", "primary"),
            "ending_he": ("结局·HE", "直接播放 HE 结局演示", "success"),
            "unlock_be": ("解锁 BE 结局", "解锁 BE 主菜单封面，便于调试切换", "danger"),
            "unlock_he": ("解锁 HE 结局", "解锁 HE 主菜单封面，便于调试切换", "success"),
            "unlock_te": ("解锁 TE 结局", "解锁 TE 主菜单封面，便于调试切换", "primary"),
            "protection": ("进入保护模式", "血量固定 1、免疫致命伤害", "success"),
        }
        for action, rect in self.developer_buttons.items():
            title, detail, variant = action_content[action]
            enabled, _ = self._developer_action_availability(action)
            self._draw_developer_action(screen, rect, title, detail, variant, enabled)

        hint = body_font.render("Shift+F12 / Esc 关闭", True, UI_COLORS["muted"])
        screen.blit(hint, (panel.x + 34, panel.bottom - 38))

    def _draw_developer_slider(
        self,
        screen,
        rect,
        label,
        value,
        minimum,
        maximum,
        value_text,
    ):
        hovered = rect.collidepoint(pygame.mouse.get_pos())
        border = UI_COLORS["accent"] if hovered else UI_COLORS["border"]
        fill = UI_COLORS["surface_hover"] if hovered else UI_COLORS["surface_alt"]
        draw_panel(screen, rect, fill=fill, border=border, radius=9, shadow=False)

        font = get_font(self.game.font_cache, "caption")
        value_font = get_font(self.game.font_cache, "micro")
        screen.blit(
            font.render(label, True, UI_COLORS["text"]), (rect.x + 18, rect.y + 12)
        )
        value_surface = value_font.render(value_text, True, UI_COLORS["accent"])
        screen.blit(
            value_surface, (rect.right - value_surface.get_width() - 18, rect.y + 16)
        )

        track = self._developer_slider_track(rect)
        ratio = (value - minimum) / (maximum - minimum)
        pygame.draw.rect(screen, (10, 17, 28), track, border_radius=4)
        filled = track.copy()
        filled.width = round(track.width * ratio)
        pygame.draw.rect(screen, UI_COLORS["accent"], filled, border_radius=4)
        knob_x = track.left + round(track.width * ratio)
        pygame.draw.circle(screen, UI_COLORS["text"], (knob_x, track.centery), 9)
        pygame.draw.circle(screen, UI_COLORS["accent"], (knob_x, track.centery), 9, 2)

    def _draw_developer_action(self, screen, rect, title, detail, variant, enabled):
        style = {
            "primary": (UI_COLORS["accent"], UI_COLORS["accent_soft"]),
            "secondary": (UI_COLORS["border"], UI_COLORS["surface_alt"]),
            "success": (UI_COLORS["green"], (39, 100, 78)),
            "danger": (UI_COLORS["red"], (108, 48, 62)),
        }
        border, fill = style[variant]
        hovered = enabled and rect.collidepoint(pygame.mouse.get_pos())
        if not enabled:
            border, fill = UI_COLORS["border"], (35, 42, 57)
        elif hovered:
            fill = UI_COLORS["surface_hover"]
        draw_panel(screen, rect, fill=fill, border=border, radius=10, shadow=False)

        title_color = UI_COLORS["text"] if enabled else UI_COLORS["muted"]
        title_surface = fit_text(
            get_font(self.game.font_cache, "body"),
            title,
            rect.width - 32,
            title_color,
        )
        screen.blit(title_surface, (rect.x + 16, rect.y + 9))
        detail_surface = fit_text(
            get_font(self.game.font_cache, "micro"),
            detail,
            rect.width - 32,
            UI_COLORS["muted"],
        )
        screen.blit(detail_surface, (rect.x + 16, rect.y + 38))

    def _draw_teleport_hint(self, screen):
        hint_rect = pygame.Rect(SCREEN_WIDTH // 2 - 160, 100, 320, 36)
        draw_panel(
            screen,
            hint_rect,
            fill=(20, 31, 49),
            border=UI_COLORS["gold"],
            radius=9,
            shadow=False,
        )
        hint = fit_text(
            get_font(self.game.font_cache, "caption"),
            "传送模式：在地图中左键选择位置，Esc 取消",
            hint_rect.width - 20,
            UI_COLORS["gold"],
        )
        screen.blit(hint, hint.get_rect(center=hint_rect.center))

    def _draw_damage_flash(self, screen):
        alpha = int(90 * (self.damage_flash_timer / 0.25))
        overlay = pygame.Surface((SCREEN_WIDTH, 12), pygame.SRCALPHA)
        overlay.fill((*COLORS["RED"], alpha))
        screen.blit(overlay, (0, 0))
        screen.blit(overlay, (0, 708))
