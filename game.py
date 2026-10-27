"""游戏核心模块。

负责状态切换、主线运行上下文和跨次启动的进度持久化。
"""

from __future__ import annotations

import random
import sys

import pygame

from config import (
    FPS,
    MAIN_LEVEL_IDS,
    PLAYER_JUMP_HEIGHT_DEFAULT,
    PLAYER_RUN_SPEED_DEFAULT,
    SAN_FATAL_DAMAGE_COUNT,
    SAN_INITIAL,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    STORY_MAX_HEALTH,
    STORY_RECOVERY_HEALTH,
    TUTORIAL_LEVEL_ID,
    load_chinese_font,
)
from systems.achievement_system import AchievementSystem
from systems.audio_system import AudioSystem
from systems.progress_store import ProgressStore
from systems.shop_system import ShopSystem
from systems.ui_manager import UIManager
from ui.video_player import VideoPlayer


class Game:
    """游戏主类。"""

    def __init__(self, save_path=None):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("wys2026BirthdayGame")
        try:
            from utils.ui_art import asset_path

            pygame.display.set_icon(
                pygame.image.load(str(asset_path("images/app_icon.png")))
            )
        except (FileNotFoundError, OSError, pygame.error):
            pass
        self.clock = pygame.time.Clock()
        pygame.key.set_repeat(0, 0)
        pygame.event.set_allowed(
            [
                pygame.QUIT,
                pygame.KEYDOWN,
                pygame.KEYUP,
                pygame.MOUSEBUTTONDOWN,
                pygame.MOUSEBUTTONUP,
                pygame.MOUSEMOTION,
                pygame.MOUSEWHEEL,
            ]
        )

        self.font_cache = load_chinese_font()
        self.video_player = VideoPlayer(self.screen, self.font_cache)
        self.event_bus = EventBus()

        self.progress_store = ProgressStore(save_path)
        # 首次进入（无存档文件，或上次清档已删除存档）才展示游玩注意事项。
        self.is_first_launch = not self.progress_store.path.exists()
        self.save_data = self.progress_store.load()
        valid_level_ids = (TUTORIAL_LEVEL_ID, *MAIN_LEVEL_IDS)
        # 正式版移除了部分关卡，旧存档里这些关卡的星级记录直接丢弃，不再引用。
        self.level_progress = {
            int(level_id): int(stars)
            for level_id, stars in self.save_data.get("level_progress", {}).items()
            if str(level_id).lstrip("-").isdigit()
            and int(level_id) in valid_level_ids
        }
        for level_id in valid_level_ids:
            self.level_progress.setdefault(level_id, 0)

        self.collected_items = set(self.save_data.get("collected_items", []))
        self.ending_history = list(
            dict.fromkeys(self.save_data.get("ending_history", []))
        )
        self.story_session = self._new_story_session()
        saved_story = self.save_data.get("story", {})
        if isinstance(saved_story, dict):
            for key in self.story_session:
                if key in saved_story:
                    self.story_session[key] = saved_story[key]
        if self.story_session.get("order"):
            self.story_session["order"] = self._normalize_story_order(
                self.story_session["order"]
            )
        # 旧存档可能停在正式版已移除的关卡上：放弃该局主线，避免引用不存在的关卡。
        if self.story_session.get("level") not in valid_level_ids:
            self.story_session = self._new_story_session()
        saved_recovery = self.save_data.get("recovery", {})
        if saved_recovery.get("active") and saved_recovery.get("level") not in valid_level_ids:
            self.clear_recovery()
        self.story_session["damage_count"] = max(
            0,
            min(SAN_FATAL_DAMAGE_COUNT, int(self.story_session.get("damage_count", 0))),
        )
        self.story_session["san"] = self._san_for_damage_count(
            self.story_session["damage_count"]
        )
        if self.story_session.get("recovery_mode"):
            self.story_session["health"] = STORY_RECOVERY_HEALTH
        else:
            # 血量由累计受伤次数决定，避免旧存档补默认字段后显示为满血。
            self.story_session["health"] = max(
                STORY_RECOVERY_HEALTH,
                STORY_MAX_HEALTH - self.story_session["damage_count"],
            )
        self.active_ending = None
        # SAN 计数达到上限后写入的永久锁定标记：不再累计 SAN/检定，血量恒定 1，
        # 保护模式下结局按全藏品判定 TE/HE。
        self.sanity_broken = bool(self.save_data.get("sanity_broken", False))
        if self.sanity_broken:
            self.story_session["health"] = STORY_RECOVERY_HEALTH
            self.story_session["recovery_mode"] = True
        self.streamer_mode = bool(
            self.save_data.get("settings", {}).get("streamer_mode", False)
        )
        # 自由挑战（非主线）的跨关卡受伤计数，用于判定全通时能否拿 TE。
        self.free_damage_count = int(self.save_data.get("free_damage_count", 0))
        self.developer_run_speed = PLAYER_RUN_SPEED_DEFAULT
        self.developer_jump_height = PLAYER_JUMP_HEIGHT_DEFAULT

        self.ui_manager = UIManager(self)
        self.achievement_system = AchievementSystem(self)
        self.shop_system = ShopSystem(self)
        self.achievement_system.sync_collectible_achievements()
        self.audio_system = AudioSystem(self)

        if self.is_first_launch:
            from states.notice_state import NoticeState

            # 首次进入停在注意事项；该状态没有 music_scene，BGM 保持停滞。
            self.current_state = NoticeState(self)
        else:
            from states.main_menu_state import MainMenuState

            self.current_state = MainMenuState(self)
        if not self.has_recovery and self.has_story_resume:
            self.ui_manager.show_toast(
                "检测到主线进度",
                "点击开始主线后继续当前关卡。",
                duration=8.0,
            )

    # ==================== 存档 ====================

    def save_progress(self):
        """把运行时进度整理为 JSON 可序列化结构并保存。"""

        self.save_data["level_progress"] = {
            str(level_id): stars for level_id, stars in self.level_progress.items()
        }
        self.save_data["collected_items"] = sorted(self.collected_items)
        self.save_data["achievements"] = self.achievement_system.to_save()
        self.save_data["skins"] = self.shop_system.to_save()
        self.save_data["ending_history"] = list(self.ending_history)
        self.save_data["settings"] = {"streamer_mode": self.streamer_mode}
        self.save_data["story"] = self._story_to_save()
        self.save_data["sanity_broken"] = self.sanity_broken
        self.save_data["free_damage_count"] = self.free_damage_count
        self.progress_store.save(self.save_data)

    def _new_story_session(self):
        return {
            "active": False,
            "order": [],
            "index": -1,
            "level": None,
            "damage_count": 0,
            "san": SAN_INITIAL,
            "health": STORY_MAX_HEALTH,
            "te_eligible": True,
            "recovery_mode": False,
            "mental_flicker": False,
            "mental_broken": False,
            "visual_state": "beast"
            if "BE" in getattr(self, "ending_history", [])
            else "normal",
        }

    def _story_to_save(self):
        story = self._new_story_session()
        for key in story:
            story[key] = self.story_session.get(key, story[key])
        return story

    @staticmethod
    def _normalize_story_order(order):
        """保留已有主线顺序，并把版本更新后新增的关卡补到末尾。"""

        normalized = []
        for level_id in order if isinstance(order, (list, tuple)) else []:
            if level_id in MAIN_LEVEL_IDS and level_id not in normalized:
                normalized.append(level_id)
        normalized.extend(
            level_id for level_id in MAIN_LEVEL_IDS if level_id not in normalized
        )
        return normalized

    @property
    def has_recovery(self):
        recovery = self.save_data.get("recovery", {})
        return bool(recovery.get("active"))

    @property
    def has_story_resume(self):
        return bool(
            self.story_session.get("active")
            and self.story_session.get("level") is not None
            and self.story_session.get("order")
        )

    # ==================== 主线流程 ====================

    def start_main_story(self, resume_recovery=True):
        """开始新的主线，或恢复 SAN 计数达到上限前保存的关卡。"""

        recovery = self.save_data.get("recovery", {})
        if resume_recovery and recovery.get("active"):
            self.story_session = {
                "active": True,
                "order": self._normalize_story_order(recovery.get("order", [])),
                "index": int(recovery.get("index", 0)),
                "level": recovery.get("level"),
                "damage_count": int(
                    recovery.get("damage_count", SAN_FATAL_DAMAGE_COUNT)
                ),
                "san": SAN_FATAL_DAMAGE_COUNT,
                "health": STORY_RECOVERY_HEALTH,
                "te_eligible": False,
                "recovery_mode": True,
                "visual_state": "normal",
            }
            return self.launch_story_level(
                self.story_session["level"], self.story_session["index"]
            )

        if resume_recovery and self.has_story_resume:
            state = self.launch_story_level(
                self.story_session["level"], self.story_session["index"]
            )
            self.ui_manager.show_toast(
                "主线进度恢复",
                "已恢复当前主线关卡和受伤进度。",
                duration=5.0,
            )
            return state

        self.story_session = self._new_story_session()
        self.story_session.update(
            {
                "active": True,
                "order": random.sample(list(MAIN_LEVEL_IDS), len(MAIN_LEVEL_IDS)),
                # 理智崩溃锁定后，重新开始主线也保持免检定、血量 1、锁 HE。
                "recovery_mode": self.sanity_broken,
                "visual_state": "normal",
            }
        )
        self.save_progress()
        return self.launch_story_level(TUTORIAL_LEVEL_ID, -1)

    def launch_story_level(self, level_id, story_index):
        """创建主线关卡状态并记录当前恢复点。"""

        from states.play_state import PlayState

        self.story_session["active"] = True
        self.story_session["level"] = level_id
        self.story_session["index"] = story_index
        if self.story_session.get("recovery_mode"):
            recovery_reason = self.save_data.get("recovery", {}).get("reason", "fatal")
            self.save_recovery(recovery_reason)
        else:
            self.save_progress()
        state = PlayState(
            self,
            level_id,
            story_mode=True,
            story_index=story_index,
            recovery_mode=self.story_session["recovery_mode"],
        )
        self.change_state(state)
        return state

    def advance_story(self):
        """从结算页进入下一关或结局。"""

        if not self.story_session.get("active"):
            return

        current_level = self.story_session.get("level")
        current_index = int(self.story_session.get("index", -1))
        if current_level == TUTORIAL_LEVEL_ID:
            next_index = 0
        else:
            next_index = current_index + 1

        story_finished = next_index >= len(self.story_session["order"])
        # 血量剩余 3 检定失败：主线全部走完即结算 BE，不再按藏品判定 TE/HE。
        if story_finished and self.story_session.get("mental_broken"):
            self.finish_story_ending("BE")
            return
        # 保护模式（致命伤害恢复 / 理智崩溃锁定）必然已经受伤到上限，无伤的 TE
        # 不可能达成，因此只结算 HE。保护模式只在主线真正走完时结算结局：星级会
        # 跨局保留（上一轮通关或自由挑战都能拿星），若按“全关卡有星”提前结算，
        # 通关 BE 后（理智崩溃锁定仍在）玩家一进下一关就会被凭空结算成 HE。
        protection = bool(
            self.story_session.get("recovery_mode") or self.sanity_broken
        )
        if protection and story_finished:
            self.finish_story_ending("HE")
            return

        if story_finished:
            self.finish_story_ending()
            return

        self.launch_story_level(self.story_session["order"][next_index], next_index)

    def unlock_ending_rewards(self, ending_type):
        """结算结局对应的成就与外观解锁（正式结算与开发者快捷共用）。"""

        if ending_type in {"HE", "HE_RECOVERY", "TE"}:
            self.achievement_system.unlock("complete_main_story")
        # 任一结局（HE/BE/TE）通关都解锁皮肤3 女仆外观。
        self.shop_system.unlock_maid()
        if ending_type == "TE":
            self.achievement_system.unlock("te_ending")
            self.shop_system.unlock_endgame()
        elif ending_type == "BE":
            self.achievement_system.unlock("be_ending")

    def finish_story_ending(self, ending_type=None, *, preserve_recovery=False):
        """根据主线状态结算 HE/TE/BE。"""

        if self.streamer_mode:
            ending_type = "HE"

        if ending_type is None:
            # TE 只要求全程无伤，不再要求集齐藏品。保护模式（致命伤害恢复 /
            # 理智崩溃锁定，或开发者工具强制）下必定已受伤到上限、血量恒 1，
            # 永不给 TE，只结算 HE。
            protection = bool(
                self.sanity_broken or self.story_session.get("recovery_mode")
            )
            if not protection and self.story_session["damage_count"] == 0:
                ending_type = "TE"
            else:
                ending_type = "HE"

        self.unlock_ending_rewards(ending_type)

        if ending_type in self.ending_history:
            self.ending_history.remove(ending_type)
        self.ending_history.append(ending_type)
        self.story_session["visual_state"] = (
            "beast"
            if ending_type == "BE"
            else self.story_session.get("visual_state", "normal")
        )
        self.active_ending = ending_type
        self.story_session["active"] = False
        self.story_session["level"] = None
        if not preserve_recovery:
            if (
                ending_type in {"HE", "HE_RECOVERY", "TE"}
                and (self.sanity_broken or self.story_session.get("recovery_mode"))
                and self.has_stars_on_all_levels()
            ):
                # 保护模式下已通关全部非 S 关卡：永久解除保护并回满血量，
                # 再进入 HE/TE 结局。
                self.lift_protection()
            else:
                self.clear_recovery()
        self.save_progress()

        from states.ending_state import EndingState

        self.change_state(EndingState(self, ending_type))

    def register_story_damage(self, reason, *, bypass_streamer_mode=False):
        """登记一次主线受伤并返回需要的演出类型。"""

        if (
            not self.story_session.get("active")
            or self.story_session.get("recovery_mode")
            or self.sanity_broken
            or (self.streamer_mode and not bypass_streamer_mode)
        ):
            return None

        damage_count = min(
            SAN_FATAL_DAMAGE_COUNT,
            int(self.story_session.get("damage_count", 0)) + 1,
        )
        self.story_session["damage_count"] = damage_count
        self.story_session["san"] = self._san_for_damage_count(damage_count)
        self.story_session["health"] = max(
            STORY_RECOVERY_HEALTH,
            STORY_MAX_HEALTH - damage_count,
        )
        self.story_session["te_eligible"] = False
        self.achievement_system.unlock("first_damage")

        if damage_count >= SAN_FATAL_DAMAGE_COUNT:
            # 理智彻底崩溃：写入永久锁定标记，随后由 FatalErrorState 蓝屏并强制退出。
            self.sanity_broken = True
            self.story_session["recovery_mode"] = True
            self.save_recovery()
            return "FATAL"
        if damage_count in {5, 7}:
            self.achievement_system.unlock("first_mental_check")
            if random.randint(1, 2) == 1:
                self.save_progress()
                return "MENTAL_CHECK_SUCCESS"
            if damage_count >= 7:
                # 血量剩余 3 检定失败：结算固定 BE 立绘，主线全部走完后结算 BE。
                self.story_session["mental_broken"] = True
            else:
                # 血量剩余 5 检定失败：结算立绘在正常/BE 之间高频闪烁，结局不锁 BE。
                self.story_session["mental_flicker"] = True
            self.save_progress()
            return "MENTAL_CHECK_FAILURE"
        if damage_count == 3:
            self.save_progress()
            return "SAN_WARNING_3"

        self.save_progress()
        return "DAMAGE"

    @staticmethod
    def _san_for_damage_count(damage_count):
        return max(SAN_INITIAL, min(SAN_FATAL_DAMAGE_COUNT, int(damage_count)))

    def save_recovery(self, reason="fatal"):
        self.story_session["health"] = STORY_RECOVERY_HEALTH
        self.save_data["recovery"] = {
            "active": True,
            "level": self.story_session.get("level"),
            "order": list(self.story_session.get("order", [])),
            "index": self.story_session.get("index", 0),
            "damage_count": self.get_story_damage_count(),
            "san": self.get_story_san(),
            "health": STORY_RECOVERY_HEALTH,
            "reason": reason,
        }
        self.save_progress()

    def clear_recovery(self):
        self.save_data["recovery"] = {
            "active": False,
            "level": None,
            "order": [],
            "index": -1,
            "damage_count": 0,
            "san": 0,
            "health": STORY_MAX_HEALTH,
            "reason": None,
        }
        self.story_session["recovery_mode"] = False

    def lift_protection(self):
        """全部非 S 关卡通关后解除保护模式：复位锁定、清空恢复点并回满血量。"""

        self.sanity_broken = False
        self.clear_recovery()
        self.story_session["damage_count"] = 0
        self.story_session["san"] = SAN_INITIAL
        self.story_session["health"] = STORY_MAX_HEALTH
        self.story_session["te_eligible"] = True
        self.story_session["mental_flicker"] = False

    def set_streamer_mode(self, enabled):
        self.streamer_mode = bool(enabled)
        self.save_progress()

    def register_free_damage(self):
        """自由挑战受伤：累计跨关卡的「无伤」计数（全通判定 TE 时使用）。"""

        self.free_damage_count += 1
        self.save_progress()

    def reset_free_damage(self):
        """从追忆进入自由挑战时清零，作为一次挑战的起点。"""

        self.free_damage_count = 0
        self.save_progress()

    def clear_all_progress(self):
        self.save_data = self.progress_store.clear()
        self.level_progress = {
            level_id: 0 for level_id in (TUTORIAL_LEVEL_ID, *MAIN_LEVEL_IDS)
        }
        self.collected_items = set()
        self.ending_history = []
        self.story_session = self._new_story_session()
        self.active_ending = None
        self.sanity_broken = False
        self.streamer_mode = False
        self.achievement_system = AchievementSystem(self)
        self.shop_system = ShopSystem(self)

    # ==================== 藏品与成就 ====================

    def collect_item(self, item_id):
        if not item_id or item_id in self.collected_items:
            return False
        self.collected_items.add(item_id)
        self.achievement_system.check_achievement(
            "collect_all_items", self.has_all_main_collectibles()
        )
        self.achievement_system.sync_collectible_achievements()
        self.save_progress()
        return True

    def is_item_collected(self, item_id):
        return item_id in self.collected_items

    def has_all_main_collectibles(self):
        from levels.level_data import MAIN_COLLECTIBLE_IDS

        return set(MAIN_COLLECTIBLE_IDS).issubset(self.collected_items)

    def next_level_without_stars(self):
        """除 S 关（无尽模式）外，返回第一个还没有星星的关卡 id；全部有星时为 None。"""

        for level_id in (TUTORIAL_LEVEL_ID, *MAIN_LEVEL_IDS):
            if self.level_progress.get(level_id, 0) <= 0:
                return level_id
        return None

    def has_stars_on_all_levels(self):
        """除 S 关（无尽模式）外，所有关卡都至少拿到一颗星。"""

        return self.next_level_without_stars() is None

    def get_story_damage_count(self):
        return int(self.story_session.get("damage_count", 0))

    def get_story_san(self):
        return int(self.story_session.get("san", SAN_INITIAL))

    def get_story_health(self):
        """返回主线当前血量；恢复模式或理智崩溃锁定后始终固定为 1。"""

        if self.sanity_broken or self.story_session.get("recovery_mode"):
            return STORY_RECOVERY_HEALTH
        return max(
            STORY_RECOVERY_HEALTH,
            min(
                STORY_MAX_HEALTH,
                int(self.story_session.get("health", STORY_MAX_HEALTH)),
            ),
        )

    # ==================== 主循环 ====================

    def run(self):
        # 由当前状态决定起始 BGM：注意事项页没有 music_scene，保持静默（停滞）。
        if scene := getattr(self.current_state, "music_scene", None):
            self.audio_system.play_scene(scene)

        while True:
            dt = self.clock.tick(FPS) / 1000.0
            events = pygame.event.get()
            filtered_events = []
            for event in events:
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type not in (pygame.TEXTINPUT, pygame.TEXTEDITING):
                    filtered_events.append(event)

            self.current_state.handle_events(filtered_events)
            self.current_state.update(dt)
            self.audio_system.update(dt)
            self.ui_manager.update(dt)
            self.current_state.draw(self.screen)
            self.ui_manager.draw(self.screen, self.font_cache)
            pygame.display.flip()

    def change_state(self, new_state):
        self.current_state = new_state
        if scene := getattr(new_state, "music_scene", None):
            self.audio_system.play_scene(scene)


class EventBus:
    """简单事件总线，供旧扩展模式继续使用。"""

    def __init__(self):
        self.listeners = {}

    def on(self, event_name, callback):
        self.listeners.setdefault(event_name, []).append(callback)

    def emit(self, event_name, data=None):
        for callback in self.listeners.get(event_name, []):
            callback(data)
