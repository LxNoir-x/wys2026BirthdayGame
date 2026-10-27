"""
游戏配置模块
包含游戏的全局配置参数，如屏幕尺寸、帧率、颜色和字体设置
"""

import sys
from pathlib import Path

import pygame

# ==================== 屏幕配置 ====================
SCREEN_WIDTH = 1280  # 屏幕宽度（像素）
SCREEN_HEIGHT = 720  # 屏幕高度（像素）
FPS = 60  # 游戏帧率（帧/秒）
TARGET_DELTA = 1 / FPS  # 目标帧时间间隔（秒）

# ==================== 主线配置 ====================
# 新手教程固定为 0，正式主线关卡沿用 1-20 的编号区间。正式布局仍由关卡数据提供。
# 正式版移除了三关（4 还之彼身 / 10 切尔诺伯格-破碎大道 / 18 英雄无名），
# 关卡编号保留原值，跳过这些空缺，不做重新编号。
TUTORIAL_LEVEL_ID = 0
MAIN_LEVEL_IDS = (1, 2, 3, 5, 6, 7, 8, 9, 11, 12, 13, 14, 15, 16, 17, 19, 20)
MAIN_LEVEL_COUNT = len(MAIN_LEVEL_IDS)
TOTAL_STORY_LEVELS = MAIN_LEVEL_COUNT + 1

# SAN 是随受伤递增的计数器，达到 10 时进入致命恢复流程。
SAN_INITIAL = 0
SAN_FATAL_DAMAGE_COUNT = 10
STORY_MAX_HEALTH = SAN_FATAL_DAMAGE_COUNT
STORY_RECOVERY_HEALTH = 1
DAMAGE_INVULNERABILITY_SECONDS = 0.8

# 开发者工具中的角色物理调节范围。数值只在当前游戏进程内生效，不写入存档。
PLAYER_RUN_SPEED_DEFAULT = 5.0
PLAYER_RUN_SPEED_MIN = 4.0
PLAYER_RUN_SPEED_MAX = 16.0
PLAYER_JUMP_HEIGHT_DEFAULT = 175.0
PLAYER_JUMP_HEIGHT_MIN = 80.0
PLAYER_JUMP_HEIGHT_MAX = 360.0
PLAYER_GRAVITY = 0.8

# ==================== 颜色配置 ====================
COLORS = {
    "WHITE": (255, 255, 255),  # 白色
    "BLACK": (20, 20, 30),  # 黑色（稍深的背景色）
    "GRAY": (180, 180, 200),  # 灰色
    "DARK_GRAY": (80, 80, 100),  # 深灰色
    "RED": (255, 100, 100),  # 红色
    "GREEN": (100, 255, 150),  # 绿色
    "CYAN": (100, 220, 255),  # 青色
    "GOLD": (255, 215, 0),  # 金色
    "MAGENTA": (255, 100, 200),  # 品红色
    "BROWN": (160, 120, 80),  # 棕色
    "ORANGE": (255, 165, 80),  # 橙色
    "PURPLE": (180, 100, 255),  # 紫色
    "PINK": (255, 180, 200),  # 粉色
    "LIGHT_BLUE": (150, 200, 255),  # 浅蓝色
    "SKY_BLUE": (135, 206, 250),  # 天蓝色
}

# ==================== 关卡背景渐变色 ====================
LEVEL_GRADIENTS = [
    # 每一关的背景渐变色（起始颜色, 结束颜色）
    ((20, 60, 100), (50, 100, 150)),  # 第1关：深蓝色系
    ((80, 30, 50), (150, 50, 80)),  # 第2关：深红色系
    ((30, 80, 120), (80, 150, 200)),  # 第3关：青色系
    ((100, 60, 20), (180, 100, 40)),  # 第4关：橙色系
    ((40, 20, 80), (100, 60, 150)),  # 第5关：紫色系
    ((50, 80, 30), (120, 150, 60)),  # 第6关：绿色系
    ((80, 40, 80), (150, 80, 150)),  # 第7关：紫罗兰色系
    ((20, 80, 80), (60, 150, 150)),  # 第8关：青色系
    ((90, 30, 60), (160, 60, 120)),  # 第9关：玫红色系
    ((40, 60, 90), (100, 120, 180)),  # 第10关：蓝紫色系
    ((60, 40, 90), (120, 80, 180)),  # 第11关：紫色系
    ((30, 60, 40), (80, 120, 80)),  # 第12关：墨绿色系
    ((70, 50, 30), (140, 100, 60)),  # 第13关：棕黄色系
    ((50, 30, 70), (110, 70, 140)),  # 第14关：深紫色系
    ((20, 70, 50), (60, 140, 100)),  # 第15关：青绿色系
    ((45, 45, 65), (90, 90, 140)),  # 第16关：占位
    ((65, 35, 55), (130, 70, 100)),  # 第17关：占位
    ((35, 65, 70), (70, 130, 145)),  # 第18关：占位
    ((25, 45, 42), (58, 88, 76)),  # 第19关：占位
]


def get_level_gradient(level_id):
    """按关卡编号获取背景渐变，教程使用第一组占位颜色。"""

    if level_id <= 0:
        return LEVEL_GRADIENTS[0]
    return LEVEL_GRADIENTS[min(level_id - 1, len(LEVEL_GRADIENTS) - 1)]


# ==================== 字体缓存 ====================
def load_chinese_font():
    """
    加载版本 4 指定的立方体 11 号字体并创建字体缓存。

    字体文件位于 assets/fonts，避免不同电脑上的系统字体导致排版和字形
    不一致。
    如果资源缺失，才退回 pygame 默认字体。

    Returns:
        font_cache: 字体缓存字典，包含 large、medium、small、tiny 四种字号
    """
    font_cache = {}

    font_roots = [Path(__file__).resolve().parent / "assets" / "fonts"]
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        font_roots.insert(0, Path(meipass) / "assets" / "fonts")

    font_dir = next((path for path in font_roots if path.is_dir()), None)
    font_file = "Cubic-11-1.000-R-2.ttf"
    if font_dir and (font_dir / font_file).is_file():
        try:
            font_path = str(font_dir / font_file)
            font_cache["large"] = pygame.font.Font(font_path, 60)
            font_cache["medium"] = pygame.font.Font(font_path, 40)
            font_cache["small"] = pygame.font.Font(font_path, 30)
            font_cache["tiny"] = pygame.font.Font(font_path, 24)
            font_cache["title"] = pygame.font.Font(font_path, 48)
            font_cache["button"] = pygame.font.Font(font_path, 26)
            font_cache["body"] = pygame.font.Font(font_path, 22)
            font_cache["caption"] = pygame.font.Font(font_path, 18)
            font_cache["micro"] = pygame.font.Font(font_path, 16)
            font_cache["desc"] = pygame.font.Font(font_path, 16)
            # 藏品/成就文案框用的更小字号，避免长句顶满文案框。
            font_cache["desc_small"] = pygame.font.Font(font_path, 14)
            return font_cache
        except pygame.error:
            # 字体文件损坏或当前 pygame_ttf 不支持时使用默认字体。
            pass

    # 如果所有中文字体都加载失败，使用默认字体
    font_cache["large"] = pygame.font.Font(None, 60)
    font_cache["medium"] = pygame.font.Font(None, 40)
    font_cache["small"] = pygame.font.Font(None, 30)
    font_cache["tiny"] = pygame.font.Font(None, 24)
    font_cache["title"] = pygame.font.Font(None, 48)
    font_cache["button"] = pygame.font.Font(None, 26)
    font_cache["body"] = pygame.font.Font(None, 22)
    font_cache["caption"] = pygame.font.Font(None, 18)
    font_cache["micro"] = pygame.font.Font(None, 16)
    font_cache["desc"] = pygame.font.Font(None, 16)
    font_cache["desc_small"] = pygame.font.Font(None, 14)

    return font_cache


def load_notice_font():
    """Load Source Han Sans for the safety notice and download guide."""

    font_roots = [Path(__file__).resolve().parent / "assets" / "fonts"]
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        font_roots.insert(0, Path(meipass) / "assets" / "fonts")
    font_dir = next((path for path in font_roots if path.is_dir()), None)
    regular = font_dir / "SourceHanSansSC-Regular.otf" if font_dir else None
    medium = font_dir / "SourceHanSansSC-Medium.otf" if font_dir else None
    bold = font_dir / "SourceHanSansSC-Bold.otf" if font_dir else None

    files = {
        "large": (bold, 60),
        "medium": (bold, 40),
        "small": (medium, 30),
        "tiny": (regular, 24),
        "title": (bold, 48),
        "button": (medium, 26),
        "body": (regular, 19),
        "caption": (regular, 18),
        "micro": (regular, 16),
    }
    cache = {}
    for key, (path, size) in files.items():
        try:
            cache[key] = (
                pygame.font.Font(str(path), size)
                if path and path.is_file()
                else pygame.font.Font(None, size)
            )
        except pygame.error:
            cache[key] = pygame.font.Font(None, size)
    return cache
