"""基于顺序解码和 EOF 信号的视频播放器。"""

from __future__ import annotations

import cv2
import pygame

from utils.ui_art import asset_path


class VideoPlayer:
    """按源帧率顺序解码视频，并以解码 EOF 标记播放完成。"""

    def __init__(self, screen, font_cache=None):
        self.screen = screen
        self.font_cache = font_cache
        self.cap = None
        self.frame_surface = None
        self.frame_interval = 1 / 25
        self.frame_accumulator = 0.0
        self.video_loaded = False
        self.is_playing = False
        self.is_paused = False
        self.finished = False
        self.audio_path = None
        self._owns_music_channel = False

    def load(self, video_path, audio_path=None):
        """加载首帧；不存在或无法解码时返回 ``False``。"""

        self.reset()
        try:
            resolved_video = asset_path(video_path)
        except (OSError, ValueError):
            return False
        if not resolved_video.is_file():
            return False

        self.cap = cv2.VideoCapture(str(resolved_video))
        if not self.cap.isOpened():
            self.reset()
            return False
        fps = float(self.cap.get(cv2.CAP_PROP_FPS) or 0)
        self.frame_interval = 1 / fps if fps > 0 else 1 / 25
        decoded, frame = self.cap.read()
        if not decoded:
            self.reset()
            return False

        self.frame_surface = self._to_surface(frame)
        self.video_loaded = True
        if audio_path:
            try:
                resolved_audio = asset_path(audio_path)
            except (OSError, ValueError):
                resolved_audio = None
            if resolved_audio and resolved_audio.is_file():
                self.audio_path = resolved_audio
        return True

    def play(self, volume=1.0):
        if not self.video_loaded:
            return False
        self.is_playing = True
        self.is_paused = False
        self.finished = False
        self.frame_accumulator = 0.0
        if self.audio_path:
            pygame.mixer.music.load(str(self.audio_path))
            pygame.mixer.music.set_volume(max(0.0, min(1.0, float(volume))))
            pygame.mixer.music.play()
            self._owns_music_channel = True
        return True

    def update(self, dt):
        if not self.is_playing or self.is_paused or not self.cap:
            return
        self.frame_accumulator += max(0.0, float(dt))
        while self.frame_accumulator >= self.frame_interval and self.is_playing:
            self.frame_accumulator -= self.frame_interval
            decoded, frame = self.cap.read()
            if not decoded:
                self._mark_finished()
                break
            self.frame_surface = self._to_surface(frame)

    def pause(self):
        if not self.is_playing or self.is_paused:
            return
        self.is_paused = True
        if self._owns_music_channel:
            pygame.mixer.music.pause()

    def resume(self):
        if not self.is_playing or not self.is_paused:
            return
        self.is_paused = False
        if self._owns_music_channel:
            pygame.mixer.music.unpause()

    def stop(self):
        self.is_playing = False
        self.is_paused = False
        if self._owns_music_channel:
            pygame.mixer.music.stop()
            self._owns_music_channel = False

    def reset(self):
        self.stop()
        if self.cap:
            self.cap.release()
        self.cap = None
        self.frame_surface = None
        self.frame_interval = 1 / 25
        self.frame_accumulator = 0.0
        self.video_loaded = False
        self.finished = False
        self.audio_path = None

    def draw(self, target_rect=None):
        target_rect = pygame.Rect(target_rect or self.screen.get_rect())
        pygame.draw.rect(self.screen, (0, 0, 0), target_rect)
        if not self.frame_surface:
            return
        source_width, source_height = self.frame_surface.get_size()
        scale = min(
            target_rect.width / source_width,
            target_rect.height / source_height,
        )
        size = (
            max(1, round(source_width * scale)),
            max(1, round(source_height * scale)),
        )
        frame = pygame.transform.smoothscale(self.frame_surface, size)
        self.screen.blit(frame, frame.get_rect(center=target_rect.center))

    def draw_preview(self, x, y, width, height):
        self.draw(pygame.Rect(x, y, width, height))

    @staticmethod
    def _to_surface(frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width = rgb.shape[:2]
        return pygame.image.frombuffer(rgb.tobytes(), (width, height), "RGB").copy()

    def _mark_finished(self):
        self.is_playing = False
        self.is_paused = False
        self.finished = True
        if self._owns_music_channel:
            pygame.mixer.music.stop()
            self._owns_music_channel = False
