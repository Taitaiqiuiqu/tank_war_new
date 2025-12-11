import os
import threading
from typing import Dict, List, Optional, Tuple

import pygame


class VideoAsset:
    """缓存视频帧与音频，便于在游戏循环中高效播放。"""

    def __init__(
        self,
        name: str,
        frames: List[pygame.Surface],
        fps: int,
        placeholder: bool = False,
        audio: Optional[pygame.mixer.Sound] = None,
    ):
        self.name = name
        self.frames = frames
        self.fps = max(1, fps)
        self.placeholder = placeholder or len(frames) <= 1
        self.duration_ms = int(len(frames) / self.fps * 1000) if frames else 0
        self.size = frames[0].get_size() if frames else (0, 0)
        self.audio = audio


class VideoInstance:
    """一次播放实例，包含位置、区域与优先级。"""

    def __init__(
        self,
        asset: VideoAsset,
        priority: int,
        area: str,
        size_ratio: float = 0.2,
        position: Optional[Tuple[int, int]] = None,
    ):
        self.asset = asset
        self.priority = priority
        self.area = area  # "world" 或 "screen" 或 "fullscreen"
        self.size_ratio = size_ratio
        self.position = position
        self.start_ticks = pygame.time.get_ticks()
        self.audio_channel: Optional[pygame.mixer.Channel] = None

    def is_finished(self, now_ms: int) -> bool:
        if not self.asset.frames:
            return True
        return now_ms - self.start_ticks >= max(1, self.asset.duration_ms)

    def current_frame(self, now_ms: int) -> pygame.Surface:
        if not self.asset.frames:
            return None
        elapsed = now_ms - self.start_ticks
        frame_idx = min(len(self.asset.frames) - 1, int((elapsed / 1000.0) * self.asset.fps))
        return self.asset.frames[frame_idx]


class VideoPlaybackController:
    """
    统一管理视频播放及优先级。

    - 优先级：更大的值代表更高优先级。
    - 低优先级在高优先级播放时不触发。
    - 支持三个播放区域：world（随游戏世界缩放）、screen（UI层）、fullscreen（覆盖整个屏幕）。
    """

    DEFAULT_CONFIG = {
        "victory": {"file": "笑.mp4", "priority": 100, "area": "fullscreen", "size_ratio": 1.0},
        "defeat": {"file": "诶呀，气死我了.mp4", "priority": 100, "area": "fullscreen", "size_ratio": 1.0},
        "grenade_pickup": {"file": "颗秒.mp4", "priority": 80, "area": "fullscreen", "size_ratio": 1.0},
        "player_killed_by_enemy": {
            "file": "难道他真的是赋能哥.mp4",
            "priority": 60,
            "area": "world",
            "size_ratio": 0.22,
        },
        "teammate_out_of_lives": {
            "file": "别怕，还有我呢.mp4",
            "priority": 50,
            "area": "world",
            "size_ratio": 0.18,
        },
    }

    def __init__(self, video_dir: str):
        self.video_dir = video_dir
        self.assets: Dict[str, VideoAsset] = {}
        self.active: Optional[VideoInstance] = None
        self._moviepy = None
        self._moviepy_ready = False
        self._moviepy_error_logged = False
        self.debug = bool(int(os.environ.get("VIDEO_DEBUG", "0")))
        self._preload_started = False
        self._ensure_backend()
        # 为视频音频预留混音通道，确保有可用通道
        if pygame.mixer.get_init() and pygame.mixer.get_num_channels() < 16:
            pygame.mixer.set_num_channels(16)

    def _ensure_backend(self):
        """尝试加载 moviepy 后端，失败则使用占位帧。"""
        try:
            import moviepy as mp

            # 兼容 moviepy 2.x 不再提供 editor 子模块
            if not hasattr(mp, "VideoFileClip"):
                raise ImportError("moviepy 缺少 VideoFileClip")

            self._moviepy = mp
            self._moviepy_ready = True
        except Exception as exc:  # pragma: no cover - 可选依赖
            self._moviepy_ready = False
            if not self._moviepy_error_logged:
                print(f"[Video] moviepy 不可用，将使用占位图播放: {exc}")
                self._moviepy_error_logged = True

    def _make_placeholder(self, text: str, size: Tuple[int, int] = (320, 180)) -> pygame.Surface:
        surface = pygame.Surface(size, pygame.SRCALPHA)
        surface.fill((20, 20, 20, 220))
        pygame.draw.rect(surface, (80, 160, 255), surface.get_rect(), 3)
        try:
            font = pygame.font.SysFont("consolas", 18)
        except Exception:
            font = None
        if font:
            label = font.render(text, True, (200, 200, 200))
            label_rect = label.get_rect(center=surface.get_rect().center)
            surface.blit(label, label_rect)
        return surface

    def _load_asset(self, filename: str, fps_limit: int = 15) -> VideoAsset:
        if filename in self.assets:
            return self.assets[filename]

        path = os.path.join(self.video_dir, filename)
        frames: List[pygame.Surface] = []
        placeholder = False
        audio_sound = None

        if self._moviepy_ready and os.path.exists(path):
            try:
                clip = self._moviepy.VideoFileClip(path)
                target_fps = min(fps_limit, int(clip.fps) if clip.fps else fps_limit)
                for frame in clip.iter_frames(fps=target_fps, dtype="uint8"):
                    surf = pygame.image.frombuffer(frame.tobytes(), frame.shape[1::-1], "RGB")
                    frames.append(surf.convert())
                if self.debug:
                    print(f"[Video] Loaded {filename}: {len(frames)} frames @ {target_fps}fps, size={frames[0].get_size()}")

                # 尝试提取音频为临时 wav，并加载为 pygame Sound
                if clip.audio is not None:
                    import tempfile

                    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmpf:
                        tmp_path = tmpf.name
                    try:
                        clip.audio.write_audiofile(tmp_path, fps=44100, logger=None)
                        audio_sound = pygame.mixer.Sound(tmp_path)
                        if self.debug:
                            print(f"[Video] Loaded audio for {filename}: {tmp_path}")
                    except Exception as exc:
                        if self.debug:
                            print(f"[Video] Audio load failed for {filename}: {exc}")
            except Exception as exc:  # pragma: no cover - 依赖外部环境
                print(f"[Video] 加载视频失败 {filename}: {exc}")
                frames.append(self._make_placeholder(filename))
                placeholder = True
        else:
            frames.append(self._make_placeholder(filename))
            placeholder = True

        asset = VideoAsset(filename, frames, fps_limit if frames else 1, placeholder=placeholder, audio=audio_sound)
        self.assets[filename] = asset
        return asset

    def preload_all(self, async_load: bool = True):
        """
        预加载默认配置中的所有视频，避免首次播放卡顿。
        async_load=True 时使用线程后台加载，避免阻塞主线程。
        """
        if self._preload_started:
            return
        self._preload_started = True

        def _work():
            for cfg in self.DEFAULT_CONFIG.values():
                self._load_asset(cfg["file"])
            if self.debug:
                print("[Video] Preload finished")

        if async_load:
            threading.Thread(target=_work, daemon=True).start()
        else:
            _work()

    def play(self, event_key: str, position: Optional[Tuple[int, int]] = None, size_ratio: Optional[float] = None):
        """按事件触发播放，遵循优先级互斥策略。"""
        cfg = self.DEFAULT_CONFIG.get(event_key)
        if not cfg:
            return

        asset = self._load_asset(cfg["file"])
        priority = cfg["priority"]

        # 高优先级占用，低优先级不触发
        if self.active and self.active.priority > priority:
            return

        # 更高优先级到来，直接替换
        if self.active and self.active.priority <= priority:
            self._stop_active()

        instance = VideoInstance(
            asset=asset,
            priority=priority,
            area=cfg["area"],
            size_ratio=size_ratio if size_ratio is not None else cfg.get("size_ratio", 0.2),
            position=position,
        )
        self.active = instance
        # 播放音频
        if asset.audio:
            try:
                channel = pygame.mixer.find_channel(True)
                channel.play(asset.audio)
                self.active.audio_channel = channel
            except Exception as exc:
                if self.debug:
                    print(f"[Video] play audio failed for {asset.name}: {exc}")

        if self.debug:
            pos_str = f" pos={position}" if position else ""
            print(f"[Video] play {event_key} -> {asset.name} priority={priority} area={cfg['area']} ratio={self.active.size_ratio}{pos_str}")

    def update(self, now_ms: Optional[int] = None):
        """更新播放状态。"""
        if not now_ms:
            now_ms = pygame.time.get_ticks()
        if self.active and self.active.is_finished(now_ms):
            self._stop_active()

    def _stop_active(self):
        if self.active:
            if self.active.audio_channel:
                try:
                    self.active.audio_channel.stop()
                except Exception:
                    pass
            self.active = None

    # ------------------------------------------------------------------ #
    # 渲染
    # ------------------------------------------------------------------ #
    def render_world(self, surface: pygame.Surface):
        if not self.active or self.active.area != "world":
            return
        frame = self.active.current_frame(pygame.time.get_ticks())
        if not frame:
            return
        target_rect = self._compute_rect(surface, frame, self.active.size_ratio, self.active.position)
        if target_rect:
            scaled = pygame.transform.smoothscale(frame, (target_rect.width, target_rect.height))
            surface.blit(scaled, target_rect.topleft)

    def render_screen(self, surface: pygame.Surface):
        if not self.active or self.active.area not in ("screen", "fullscreen"):
            return
        frame = self.active.current_frame(pygame.time.get_ticks())
        if not frame:
            return

        if self.active.area == "fullscreen":
            target_rect = surface.get_rect()
        else:
            target_rect = self._compute_rect(surface, frame, self.active.size_ratio, None)
        if target_rect:
            scaled = pygame.transform.smoothscale(frame, (target_rect.width, target_rect.height))
            surface.blit(scaled, target_rect.topleft)

    def _compute_rect(
        self, surface: pygame.Surface, frame: pygame.Surface, ratio: float, position: Optional[Tuple[int, int]]
    ) -> Optional[pygame.Rect]:
        """根据比例与位置计算目标矩形。"""
        sw, sh = surface.get_size()
        fw, fh = frame.get_size()
        if sw == 0 or sh == 0 or fw == 0 or fh == 0:
            return None

        target_w = max(32, int(sw * ratio))
        target_h = int(target_w * fh / fw)
        if target_h > sh * ratio * 1.5:
            target_h = int(sh * ratio)
            target_w = int(target_h * fw / fh)

        if position:
            cx, cy = position
            x = max(0, min(cx - target_w // 2, sw - target_w))
            y = max(0, min(cy - target_h // 2, sh - target_h))
        else:
            x = (sw - target_w) // 2
            y = (sh - target_h) // 3  # 略微靠上，避免挡 UI

        return pygame.Rect(x, y, target_w, target_h)

