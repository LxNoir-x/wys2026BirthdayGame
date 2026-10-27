"""按场景管理背景音乐。"""

from __future__ import annotations

import random
from typing import ClassVar

import pygame

from utils.ui_art import asset_path


class AudioSystem:
    TRACKS: ClassVar = {
        "menu": ("audio/bgm_v3/01_沉沦者梦呓_主界面.ogg",),
        "battle": (
            "audio/bgm_v3/02_树海晕动症_战斗曲1.ogg",
            "audio/bgm_v3/03_居民们的狂欢节_战斗曲2.ogg",
            "audio/bgm_v3/10_致幻的占卜_345层.ogg",
        ),
        "ending_he": ("audio/bgm_v3/09_La Alumbrada_秘境行商.ogg",),
        "cmdb": ("audio/bgm_v3/CMDB的bgm.ogg",),
        # BE/TE 的结局演出与其主界面共用同一首曲子，保持过场到菜单不断续。
        "be_theme": ("audio/bgm_v3/be结局+主界面bgm.ogg",),
        "te_theme": ("audio/bgm_v3/te主界面bgm.ogg",),
    }
    SFX: ClassVar = {
        "menu_click": "audio/bgm_v3/初始主界面点击.ogg",
        "click": "audio/bgm_v3/正常点击音.ogg",
        "toggle": "audio/bgm_v3/开关音.ogg",
        "jump": "audio/bgm_v3/跳跃音.ogg",
    }
    # 主界面 he/be 曲目互相切换时的淡出淡入总时长（秒）。
    FADE_SECONDS: ClassVar = 0.6

    def __init__(self, game):
        self.game = game
        self.master_volume = 1.0
        self.music_volume = 0.5
        self.sfx_volume = 1.0
        self.is_playing = False
        self.is_paused = False
        self.current_scene = None
        self.current_track = None
        self._sfx_cache = {}
        # 淡出淡入状态：None 表示未在过渡；否则记录目标曲目、阶段与已用时长。
        self._fade = None
        self._fade_factor = 1.0
        pygame.mixer.init()

    def play_scene(self, scene: str, *, force=False):
        """切换到场景对应曲目；战斗场景每次进入时随机选曲。"""

        tracks = self.TRACKS.get(scene)
        if not tracks:
            return
        if not force and scene == self.current_scene and self.is_playing:
            return

        self._fade = None
        self._fade_factor = 1.0
        track = random.choice(tracks)
        pygame.mixer.music.load(str(asset_path(track)))
        pygame.mixer.music.set_volume(self._music_gain())
        pygame.mixer.music.play(-1)
        self.current_scene = scene
        self.current_track = track
        self.is_playing = True
        self.is_paused = False

    def play_scene_fading(self, scene, duration=None):
        """淡出当前曲目后再淡入目标曲目，用于主界面 he/be 之间的平滑接续。"""

        tracks = self.TRACKS.get(scene)
        if not tracks or scene == self.current_scene or not self.is_playing:
            return
        self._fade = {
            "scene": scene,
            "track": random.choice(tracks),
            "elapsed": 0.0,
            "duration": max(0.1, duration or self.FADE_SECONDS),
            "phase": "out",
        }

    def _start_faded_track(self, fade):
        """淡出结束：加载目标曲目，以 0 音量起播，转入淡入阶段。"""

        pygame.mixer.music.load(str(asset_path(fade["track"])))
        self._fade_factor = 0.0
        pygame.mixer.music.set_volume(0.0)
        pygame.mixer.music.play(-1)
        self.current_scene = fade["scene"]
        self.current_track = fade["track"]
        self.is_playing = True
        self.is_paused = False
        fade["phase"] = "in"
        fade["elapsed"] = 0.0

    def play_random_bgm(self):
        """兼容旧调用：默认进入主菜单曲目。"""

        self.play_scene("menu")

    def stop_bgm(self):
        pygame.mixer.music.stop()
        self.is_playing = False
        self.is_paused = False
        self._fade = None
        self._fade_factor = 1.0

    def pause_bgm(self):
        if self.is_playing and not self.is_paused:
            pygame.mixer.music.pause()
            self.is_paused = True

    def resume_bgm(self):
        if self.is_playing and self.is_paused:
            pygame.mixer.music.unpause()
            self.is_paused = False

    @staticmethod
    def _clamp(volume):
        return max(0.0, min(1.0, float(volume)))

    def _sfx_gain(self):
        """音效实际增益为主音量与音效音量的乘积。"""

        return self.master_volume * self.sfx_volume

    def play_sfx(self, name):
        """按名称播放音效；首次播放时懒加载，文件缺失时静默跳过。"""

        sound = self._sfx_cache.get(name)
        if sound is None:
            path = self.SFX.get(name)
            if not path:
                return
            try:
                sound = pygame.mixer.Sound(str(asset_path(path)))
            except (FileNotFoundError, OSError, pygame.error):
                self.SFX.pop(name, None)
                return
            sound.set_volume(self._sfx_gain())
            self._sfx_cache[name] = sound
        sound.play()

    def _refresh_sfx_volume(self):
        gain = self._sfx_gain()
        for sound in self._sfx_cache.values():
            sound.set_volume(gain)

    def _music_gain(self):
        """音乐实际增益为主音量、音乐音量与淡入淡出系数的乘积。"""

        return self.master_volume * self.music_volume * self._fade_factor

    def set_master_volume(self, volume):
        self.master_volume = self._clamp(volume)
        pygame.mixer.music.set_volume(self._music_gain())
        self._refresh_sfx_volume()

    def set_music_volume(self, volume):
        self.music_volume = self._clamp(volume)
        pygame.mixer.music.set_volume(self._music_gain())

    def set_sfx_volume(self, volume):
        self.sfx_volume = self._clamp(volume)
        self._refresh_sfx_volume()

    def get_master_volume(self):
        return self.master_volume

    def get_music_volume(self):
        return self.music_volume

    def get_sfx_volume(self):
        return self.sfx_volume

    def set_volume(self, volume):
        """兼容旧调用：等价于调整音乐音量。"""

        self.set_music_volume(volume)

    def get_volume(self):
        return self.music_volume

    def update(self, dt):
        """推进淡出淡入过渡：先降当前曲目音量，归零后换曲再升回原音量。"""

        fade = self._fade
        if not fade:
            return
        half = max(0.01, fade["duration"] / 2)
        fade["elapsed"] += max(0.0, float(dt))
        elapsed = fade["elapsed"]
        if fade["phase"] == "out":
            if elapsed < half:
                self._fade_factor = max(0.0, 1.0 - elapsed / half)
            else:
                self._start_faded_track(fade)
        elif elapsed >= half:
            self._fade_factor = 1.0
            self._fade = None
        else:
            self._fade_factor = min(1.0, elapsed / half)
        pygame.mixer.music.set_volume(self._music_gain())
