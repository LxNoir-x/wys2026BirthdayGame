"""持久化游戏进度。

存档只保存可恢复的游戏状态，不保存 pygame 对象或运行时状态。所有系统
通过 :class:`ProgressStore` 读写同一份 JSON，避免各模块各自维护一套存档。
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any

SAVE_VERSION = 6


def default_save_path() -> Path:
    """返回存档路径：打包后跟随 exe，开发环境放在项目目录，均不写入系统盘。"""

    if getattr(sys, "frozen", False):
        # 打包后 __file__ 位于 PyInstaller 内部目录，不能把存档写入临时资源目录，
        # 因此改用 exe 同级目录，便于便携分发。
        base_dir = Path(sys.executable).resolve().parent / "save_data"
    else:
        base_dir = Path(__file__).resolve().parents[1] / "save_data"
    return base_dir / "wys2026BirthdayGame" / "save.json"


def default_save_data() -> dict[str, Any]:
    """构造一份完整的默认存档。"""

    return {
        "version": SAVE_VERSION,
        "level_progress": {},
        "collected_items": [],
        "achievements": {},
        "skins": {
            "unlocked": ["default"],
            "current": "default",
        },
        "ending_history": [],
        "endless_best_height": 0,
        "sanity_broken": False,
        # 自由挑战的跨关卡受伤计数：从追忆进入时清零，全通时须为 0 才可能 TE。
        "free_damage_count": 0,
        "settings": {
            "streamer_mode": False,
        },
        "story": {
            "active": False,
            "order": [],
            "index": -1,
            "level": None,
            "damage_count": 0,
            "san": 0,
            "health": 10,
            "te_eligible": True,
            "recovery_mode": False,
            "visual_state": "normal",
        },
        "recovery": {
            "active": False,
            "level": None,
            "order": [],
            "index": -1,
            "damage_count": 0,
            "san": 0,
            "health": 10,
            "reason": None,
        },
    }


def _merge_defaults(defaults: Any, loaded: Any) -> Any:
    """递归补齐旧版本存档缺失的字段。"""

    if isinstance(defaults, dict):
        loaded_dict = loaded if isinstance(loaded, dict) else {}
        if not defaults:
            # 默认值是空字典表示该字段没有固定结构（关卡星级、成就等），
            # 必须原样沿用存档内容，否则会把已保存的键全部丢掉。
            return copy.deepcopy(loaded_dict)
        return {
            key: _merge_defaults(value, loaded_dict.get(key))
            for key, value in defaults.items()
        }
    if loaded is None:
        return copy.deepcopy(defaults)
    return loaded


class ProgressStore:
    """JSON 存档读写器。

    ``path`` 可用于测试或调试时注入临时文件；正常运行使用平台数据目录。
    """

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path else default_save_path()

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return default_save_data()

        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, TypeError):
            return default_save_data()

        # v6 requires a clean first launch so progress from distributed v5 builds
        # cannot leak into the new level, skin, achievement, and ending rules.
        try:
            loaded_version = int(loaded.get("version", 0))
        except (AttributeError, TypeError, ValueError):
            loaded_version = 0
        if loaded_version < SAVE_VERSION:
            fresh = default_save_data()
            self.save(fresh)
            return fresh

        return _merge_defaults(default_save_data(), loaded)

    def save(self, data: dict[str, Any]) -> None:
        payload = copy.deepcopy(data)
        payload["version"] = SAVE_VERSION
        self.path.parent.mkdir(parents=True, exist_ok=True)

        temporary_path = self.path.with_suffix(f"{self.path.suffix}.tmp")
        temporary_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporary_path.replace(self.path)

    def clear(self) -> dict[str, Any]:
        """删除现有存档，并返回默认数据供当前运行会话继续使用。"""

        if self.path.exists():
            self.path.unlink()
        return default_save_data()
