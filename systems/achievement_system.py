"""成就系统。"""

from __future__ import annotations

from typing import ClassVar


class AchievementSystem:
    """管理成就定义、解锁通知和存档同步。"""

    COLLECTION_GROUPS: ClassVar[dict[str, set[str]]] = {
        "collect_omgw": {
            "golden_crow_swaddle",
            "mystery_fragment",
            "worn_travel_bag",
        },
        "collect_ovo": {
            "mechanical_compass",
            "universal_terminal",
            "mystery_fragment",
        },
        "collect_oqtv": {
            "cat_idol",
            "standard_weapon",
            "power_equipment",
            "universal_terminal",
        },
        "collect_smk": {
            "mechanical_compass",
            "gun_maintenance_kit",
            "cotton_tent",
        },
    }

    def __init__(self, game):
        self.game = game
        self.achievements = {
            "reach_height_325": {
                "name": "喂，咋这样。",
                "description": "无尽模式高度首次达到325",
                "category": "无尽模式",
                "points": 50,
                "include_in_all": True,
            },
            "reach_height_1020": {
                "name": "步步高升，前途光明。",
                "description": "无尽模式高度首次达到1020",
                "category": "无尽模式",
                "points": 75,
                "include_in_all": True,
            },
            "reach_height_1136": {
                "name": "最初的锋芒。",
                "description": "无尽模式高度首次达到1136",
                "category": "无尽模式",
                "points": 100,
                "include_in_all": True,
            },
            "reach_height_3809": {
                "name": "真拿你没办法，坐好咯。",
                "description": "无尽模式高度首次达到3809",
                "category": "无尽模式",
                "points": 200,
                "include_in_all": True,
            },
            "first_damage": {
                "name": "你会痛吗？",
                "description": "第一次受到伤害",
                "category": "受伤",
                "points": 50,
                "include_in_all": True,
            },
            "first_mental_check": {
                "name": "你好？",
                "description": "第一次出现理智检定",
                "category": "受伤",
                "points": 75,
                "include_in_all": True,
            },
            "be_ending": {
                "name": "你直面了最终的最终。",
                "description": "触发BE结局",
                "category": "受伤",
                "points": 100,
                "include_in_all": True,
            },
            "complete_main_story": {
                "name": "太阳落下了，普通的一天就这样结束。",
                "description": "完成全部主线",
                "category": "其它",
                "points": 150,
                "include_in_all": True,
            },
            "te_ending": {
                "name": "黑色的飞鸟飞回巢穴，黑色的飞鸟飞向天空。",
                "description": "触发TE结局",
                "category": "其它",
                "points": 150,
                "include_in_all": True,
            },
            "collect_all_items": {
                "name": "收集癖的大胜利！",
                "description": "收集全部主线藏品",
                "category": "其它",
                "points": 150,
                "include_in_all": True,
            },
            "collect_omgw": {
                "name": "你无法掌控命运的齿轮，但是请务必相信你自己。",
                "description": "获得 OMGW 全员的藏品",
                "category": "其它",
                "points": 100,
                "include_in_all": True,
            },
            "collect_ovo": {
                "name": "没关系，你们有很多很多的明天。",
                "description": "获得 OVO 全员的藏品",
                "category": "其它",
                "points": 100,
                "include_in_all": True,
            },
            "collect_oqtv": {
                "name": "我们的旅程结束了，但是属于我们的夏天永不结束。",
                "description": "获得 OQTV 的藏品",
                "category": "其它",
                "points": 125,
                "include_in_all": True,
            },
            "collect_smk": {
                "name": "是第一个，但永远不是最后一个。",
                "description": "获得 SMK 的藏品",
                "category": "其它",
                "points": 100,
                "include_in_all": True,
            },
            "poke_preview": {
                "name": "戳一戳",
                "description": "“你”拍了拍维云斯的头发现在下是个憨憨",
                "category": "其它",
                "points": 50,
                "include_in_all": True,
            },
            "all_achievements": {
                "name": "您达成了全部的成就",
                "description": "制作组由衷感谢您对于我们游戏的喜爱。",
                "category": "其它",
                "points": 300,
                "include_in_all": False,
            },
        }

        for achievement in self.achievements.values():
            achievement["completed"] = False

        self.total_points = 0
        self.unlocked_achievements = 0
        self._load_from_save()

    def _load_from_save(self):
        saved = self.game.save_data.get("achievements", {})
        if not isinstance(saved, dict):
            return

        for achievement_id, achievement in self.achievements.items():
            if saved.get(achievement_id):
                achievement["completed"] = True
                self.total_points += achievement["points"]
                self.unlocked_achievements += 1

    def check_achievement(self, achievement_id, *args):
        """按旧调用接口检查成就，未知 ID 直接忽略。"""
        aliases = {"normal_end": "complete_main_story"}
        achievement_id = aliases.get(achievement_id, achievement_id)
        if achievement_id not in self.achievements:
            return False

        completed = False
        if achievement_id.startswith("reach_height_"):
            threshold = int(achievement_id.rsplit("_", 1)[-1])
            completed = bool(args and args[0] >= threshold)
        elif achievement_id in {
            "first_damage",
            "first_mental_check",
            "be_ending",
            "complete_main_story",
            "te_ending",
            "collect_all_items",
            "poke_preview",
        }:
            completed = bool(args[0]) if args else True

        if completed:
            return self.unlock(achievement_id)
        return False

    def unlock(self, achievement_id):
        if achievement_id not in self.achievements:
            return False
        if self.achievements[achievement_id]["completed"]:
            return False

        achievement = self.achievements[achievement_id]
        achievement["completed"] = True
        self.total_points += achievement["points"]
        self.unlocked_achievements += 1
        self.game.ui_manager.show_achievement_notification(achievement["name"])
        self._maybe_unlock_all()
        self.game.save_progress()
        return True

    def sync_collectible_achievements(self):
        """根据现有藏品补发组合收集成就，兼容旧存档。"""

        collected = set(self.game.collected_items)
        unlocked = []
        for achievement_id, required_items in self.COLLECTION_GROUPS.items():
            if required_items.issubset(collected) and self.unlock(achievement_id):
                unlocked.append(achievement_id)
        return unlocked

    def _maybe_unlock_all(self):
        if self.achievements["all_achievements"]["completed"]:
            return
        required = (
            achievement
            for achievement in self.achievements.values()
            if achievement["include_in_all"]
        )
        if all(achievement["completed"] for achievement in required):
            achievement = self.achievements["all_achievements"]
            achievement["completed"] = True
            self.total_points += achievement["points"]
            self.unlocked_achievements += 1
            self.game.ui_manager.show_achievement_notification(achievement["name"])

    def to_save(self):
        return {
            achievement_id: achievement["completed"]
            for achievement_id, achievement in self.achievements.items()
        }

    def get_total_points(self):
        return self.total_points

    def get_unlocked_achievements(self):
        return self.unlocked_achievements

    def get_all_achievements(self):
        return self.achievements
