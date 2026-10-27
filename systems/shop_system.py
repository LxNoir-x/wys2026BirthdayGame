"""皮肤系统。"""

from __future__ import annotations


class ShopSystem:
    """管理默认、终局与版本 6 新增外观。"""

    def __init__(self, game):
        self.game = game
        self.skins = {
            "default": {
                "name": "默认皮肤",
                "description": "你一直都是这样，不是吗？",
                "unlocked": True,
                "color": (255, 255, 255),
                "achievement": None,
            },
            "endgame": {
                "name": "终局",
                "description": "见证最终的结局，你一直知道你要做什么。",
                "unlocked": False,
                "color": (210, 230, 255),
                "achievement": "te_ending",
            },
            "maid": {
                "name": "□□□□",
                "description": "███████████████",
                "unlocked": False,
                "color": (255, 255, 255),
                "achievement": None,
                "unlock_hint": "",
            },
            "be": {
                "name": "老维的早晨",
                "description": "你睁开眼睛，发现你……变成了……？",
                "unlocked": False,
                "color": (255, 255, 255),
                "achievement": "be_ending",
            },
        }
        self.current_skin = "default"
        self._load_from_save()

    def _load_from_save(self):
        saved = self.game.save_data.get("skins", {})
        unlocked = saved.get("unlocked", ["default"]) if isinstance(saved, dict) else ["default"]
        for skin_id in unlocked:
            if skin_id in self.skins:
                self.skins[skin_id]["unlocked"] = True

        current = saved.get("current") if isinstance(saved, dict) else None
        if current in self.skins and self.skins[current]["unlocked"]:
            self.current_skin = current

    def get_skins(self):
        self._check_achievements()
        return self.skins

    def get_current_skin(self):
        return self.current_skin

    def set_current_skin(self, skin_id):
        self._check_achievements()
        if skin_id in self.skins and self.skins[skin_id]["unlocked"]:
            self.current_skin = skin_id
            self.game.save_progress()
            return True
        return False

    def buy_skin(self, skin_id):
        self._check_achievements()
        return skin_id in self.skins and self.skins[skin_id]["unlocked"]

    def unlock_endgame(self):
        self.skins["endgame"]["unlocked"] = True
        self.game.save_progress()

    def unlock_maid(self):
        self.skins["maid"]["unlocked"] = True
        self.game.save_progress()

    def _check_achievements(self):
        for skin in self.skins.values():
            achievement_id = skin["achievement"]
            if achievement_id and self.game.achievement_system.get_all_achievements().get(
                achievement_id, {}
            ).get("completed"):
                skin["unlocked"] = True

    def to_save(self):
        self._check_achievements()
        return {
            "unlocked": [skin_id for skin_id, skin in self.skins.items() if skin["unlocked"]],
            "current": self.current_skin,
        }

    def get_skin_color(self, skin_id):
        return self.skins.get(skin_id, self.skins["default"])["color"]
