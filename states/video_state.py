"""关卡结算前的黑屏与音频频谱视频状态。"""

from states.game_state import GameState

SPECTRUM_LEVELS = frozenset(
    {1, 2, 3, 5, 6, 7, 8, 9, 11, 12, 13, 14, 15, 16, 17, 19, 20}
)


def spectrum_assets(level):
    if level not in SPECTRUM_LEVELS:
        return None
    stem = f"{level:02d}"
    return (
        f"videos/spectrum/{stem}.mp4",
        f"videos/spectrum/{stem}.ogg",
    )


class CompletionVideoState(GameState):
    """静默黑屏 0.5 秒后播放视频，并在解码 EOF 后进入结算。"""

    BLACK_SECONDS = 0.5

    def __init__(self, game, result_state, level):
        super().__init__(game)
        self.result_state = result_state
        self.level = int(level)
        self.black_elapsed = 0.0
        self.phase = "black"
        self.player = game.video_player
        self.assets = spectrum_assets(self.level)
        self.game.audio_system.stop_bgm()

    def handle_events(self, events):
        # 该过场按素材自然结束，不提供跳过或进度控制。
        return None

    def update(self, dt):
        if self.phase == "black":
            self.black_elapsed += max(0.0, float(dt))
            if self.black_elapsed < self.BLACK_SECONDS:
                return
            if not self.assets or not self.player.load(*self.assets):
                self._finish()
                return
            audio = self.game.audio_system
            self.player.play(audio.get_master_volume() * audio.get_sfx_volume())
            self.phase = "video"
            return

        if self.phase == "video":
            self.player.update(dt)
            if self.player.finished:
                self._finish()

    def draw(self, screen):
        screen.fill((0, 0, 0))
        if self.phase == "video":
            self.player.draw(screen.get_rect())

    def _finish(self):
        if self.phase == "done":
            return
        self.phase = "done"
        self.player.reset()
        self.game.change_state(self.result_state)


# 保留旧导入名称，调用语义统一为结算前自动播放。
VideoState = CompletionVideoState
