import os
import threading
import atexit
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
        if not self.asset or not self.asset.frames:
            return None
        try:
            elapsed = now_ms - self.start_ticks
            frame_idx = min(len(self.asset.frames) - 1, int((elapsed / 1000.0) * self.asset.fps))
            if frame_idx < 0 or frame_idx >= len(self.asset.frames):
                return None
            return self.asset.frames[frame_idx]
        except Exception as exc:
            print(f"[Video] 获取视频帧时发生错误: {exc}")
            return None


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
        self._preload_completed = False  # 预加载是否完成
        self._preload_progress = 0.0  # 预加载进度 (0.0 - 1.0)
        self._preload_status = ""  # 预加载状态文本
        self._preload_current_file = ""  # 当前正在加载的文件
        self._load_lock = threading.Lock()  # 保护资源加载的线程锁
        self._loading_flags: Dict[str, threading.Event] = {}  # 跟踪正在加载的资源
        self._temp_files: List[str] = []  # 跟踪临时文件以便清理
        self._reload_attempts: Dict[str, int] = {}  # 跟踪每个资源的重试次数
        self._max_reload_attempts = 3  # 最大重试次数
        self._reload_delay = 1.0  # 重试延迟（秒）
        self._ensure_backend()
        # 为视频音频预留混音通道，确保有可用通道
        if pygame.mixer.get_init() and pygame.mixer.get_num_channels() < 16:
            pygame.mixer.set_num_channels(16)
        # 注册清理函数
        atexit.register(self._cleanup_temp_files)

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
        # 如果已经加载，检查是否是占位符
        if filename in self.assets:
            asset = self.assets[filename]
            # 如果是在主线程中调用，且当前是占位符，尝试重新加载
            import threading
            if threading.current_thread() is threading.main_thread() and asset.placeholder:
                # 在主线程中，如果之前加载的是占位符，尝试重新加载
                print(f"[Video] 在主线程中重新加载视频 {filename}（之前是占位符）")
                # 移除占位符，重新加载
                del self.assets[filename]
            else:
                return asset

        # 检查是否正在加载（避免重复加载）
        import threading
        is_main_thread = threading.current_thread() is threading.main_thread()
        
        with self._load_lock:
            if filename in self._loading_flags:
                # 等待其他线程完成加载
                loading_event = self._loading_flags[filename]
                self._load_lock.release()
                try:
                    loading_event.wait(timeout=30.0)  # 最多等待30秒
                    # 加载完成后再次检查
                    if filename in self.assets:
                        return self.assets[filename]
                finally:
                    self._load_lock.acquire()
            
            # 标记为正在加载
            loading_event = threading.Event()
            self._loading_flags[filename] = loading_event

        # 重要：如果不在主线程中，直接返回占位符，不进行任何视频加载操作
        # 这样可以避免在非主线程中操作 pygame 或 moviepy 导致的线程安全问题
        if not is_main_thread:
            print(f"[Video] 警告：在后台线程中加载视频 {filename}，将使用占位符（稍后在主线程中加载）")
            frames = [self._make_placeholder(filename)]
            asset = VideoAsset(filename, frames, 1, placeholder=True, audio=None)
            
            with self._load_lock:
                self.assets[filename] = asset
                if filename in self._loading_flags:
                    del self._loading_flags[filename]
                loading_event.set()
            
            return asset

        # 以下代码只在主线程中执行
        try:
            path = os.path.join(self.video_dir, filename)
            frames: List[pygame.Surface] = []
            placeholder = False
            audio_sound = None
            tmp_path = None
            clip = None

            # 检查视频文件是否存在
            if not os.path.exists(path):
                print(f"[Video] 警告：视频文件不存在: {path}")
                frames.append(self._make_placeholder(filename))
                placeholder = True
            elif self._moviepy_ready and os.path.exists(path):
                try:
                    clip = self._moviepy.VideoFileClip(path)
                    target_fps = min(fps_limit, int(clip.fps) if clip.fps else fps_limit)
                    
                    # 在主线程中提取所有帧数据并创建 pygame Surface
                    try:
                        frame_count = 0
                        for frame in clip.iter_frames(fps=target_fps, dtype="uint8"):
                            try:
                                # 确保 pygame 已初始化
                                if not pygame.get_init():
                                    raise RuntimeError("pygame 未初始化")
                                
                                surf = pygame.image.frombuffer(frame.tobytes(), frame.shape[1::-1], "RGB")
                                frames.append(surf.convert())
                                frame_count += 1
                                
                                # 限制最大帧数，避免内存溢出
                                if frame_count > 1000:  # 约66秒的视频（15fps）
                                    if self.debug:
                                        print(f"[Video] 警告：视频帧数过多，截断到 {frame_count} 帧")
                                    break
                            except Exception as exc:
                                if self.debug:
                                    print(f"[Video] 创建 Surface 失败（帧 {frame_count}）: {exc}")
                                # 如果创建失败，使用占位符
                                frames.clear()
                                frames.append(self._make_placeholder(filename))
                                placeholder = True
                                break
                        
                        if frames and not placeholder:
                            if self.debug:
                                print(f"[Video] Loaded {filename}: {len(frames)} frames @ {target_fps}fps, size={frames[0].get_size()}")

                            # 尝试提取音频为临时 wav，并加载为 pygame Sound
                            if clip.audio is not None:
                                import tempfile

                                try:
                                    # 确保 pygame.mixer 已初始化
                                    if not pygame.mixer.get_init():
                                        if self.debug:
                                            print(f"[Video] pygame.mixer 未初始化，跳过音频加载")
                                    else:
                                        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmpf:
                                            tmp_path = tmpf.name
                                        
                                        try:
                                            # 使用 logger=None 来禁用输出
                                            clip.audio.write_audiofile(tmp_path, fps=44100, logger=None)
                                            # 将临时文件路径保存以便后续清理
                                            with self._load_lock:
                                                self._temp_files.append(tmp_path)
                                            
                                            # 再次检查 mixer 是否可用
                                            if pygame.mixer.get_init():
                                                audio_sound = pygame.mixer.Sound(tmp_path)
                                                if self.debug:
                                                    print(f"[Video] Loaded audio for {filename}: {tmp_path}")
                                            else:
                                                if self.debug:
                                                    print(f"[Video] pygame.mixer 在加载音频时未初始化，跳过")
                                                # 清理临时文件
                                                if tmp_path and os.path.exists(tmp_path):
                                                    try:
                                                        os.unlink(tmp_path)
                                                    except Exception:
                                                        pass
                                                tmp_path = None
                                        except Exception as exc:
                                            if self.debug:
                                                print(f"[Video] Audio load failed for {filename}: {exc}")
                                            import traceback
                                            if self.debug:
                                                traceback.print_exc()
                                            # 清理失败的临时文件
                                            if tmp_path and os.path.exists(tmp_path):
                                                try:
                                                    os.unlink(tmp_path)
                                                except Exception:
                                                    pass
                                            tmp_path = None
                                except Exception as exc:
                                    if self.debug:
                                        print(f"[Video] 音频提取准备失败 {filename}: {exc}")
                    except Exception as exc:
                        print(f"[Video] 在主线程中加载视频时发生错误 {filename}: {exc}")
                        import traceback
                        traceback.print_exc()
                        frames.clear()
                        frames.append(self._make_placeholder(filename))
                        placeholder = True
                except Exception as exc:  # pragma: no cover - 依赖外部环境
                    print(f"[Video] 加载视频失败 {filename}: {exc}")
                    import traceback
                    traceback.print_exc()
                    frames.append(self._make_placeholder(filename))
                    placeholder = True
                finally:
                    # 确保 clip 被正确关闭
                    if clip is not None:
                        try:
                            clip.close()
                        except Exception as exc:
                            if self.debug:
                                print(f"[Video] 关闭 clip 时出错: {exc}")
            else:
                frames.append(self._make_placeholder(filename))
                placeholder = True

            asset = VideoAsset(filename, frames, fps_limit if frames else 1, placeholder=placeholder, audio=audio_sound)
            
            # 保存资源并通知等待的线程
            with self._load_lock:
                self.assets[filename] = asset
                if filename in self._loading_flags:
                    del self._loading_flags[filename]
                loading_event.set()
            
            return asset
        except Exception as exc:
            print(f"[Video] 加载资源时发生错误 {filename}: {exc}")
            import traceback
            traceback.print_exc()
            # 创建占位资源
            frames = [self._make_placeholder(filename)]
            asset = VideoAsset(filename, frames, 1, placeholder=True, audio=None)
            
            with self._load_lock:
                self.assets[filename] = asset
                if filename in self._loading_flags:
                    del self._loading_flags[filename]
                loading_event.set()
            
            return asset

    def preload_all(self, async_load: bool = True, force_reload: bool = False, progress_callback=None):
        """
        预加载默认配置中的所有视频，避免首次播放卡顿。
        
        Args:
            async_load: True 时使用线程后台加载，避免阻塞主线程
            force_reload: True 时强制重新加载所有视频（即使已加载）
        """
        if self._preload_started and not force_reload:
            return
        
        if force_reload:
            # 清除已加载的资源
            with self._load_lock:
                self.assets.clear()
                self._reload_attempts.clear()
        
        self._preload_started = True
        self._preload_completed = False

        def _work():
            import threading
            is_main_thread = threading.current_thread() is threading.main_thread()
            
            if not is_main_thread:
                # 在后台线程中，只标记需要加载，实际加载在主线程中进行
                print("[Video] 预加载在后台线程中启动，将在主线程中实际加载")
                for cfg in self.DEFAULT_CONFIG.values():
                    filename = cfg["file"]
                    # 创建占位符，标记需要加载
                    if filename not in self.assets:
                        placeholder = self._make_placeholder(filename)
                        asset = VideoAsset(filename, [placeholder], 1, placeholder=True, audio=None)
                        with self._load_lock:
                            self.assets[filename] = asset
                self._preload_completed = True
                if self.debug:
                    print("[Video] 预加载标记完成（后台线程）")
            else:
                # 在主线程中，实际加载视频
                loaded_count = 0
                failed_count = 0
                config_list = list(self.DEFAULT_CONFIG.values())
                total = len(config_list)
                
                for idx, cfg in enumerate(config_list):
                    filename = cfg["file"]
                    self._preload_current_file = filename
                    self._preload_progress = (idx + 1) / total if total > 0 else 0.0
                    self._preload_status = f"加载视频: {filename}"
                    
                    if progress_callback:
                        try:
                            progress_callback(self._preload_progress, self._preload_status)
                        except:
                            pass
                    
                    try:
                        asset = self._load_asset(filename)
                        if asset and not asset.placeholder:
                            loaded_count += 1
                            if self.debug:
                                print(f"[Video] 预加载成功: {filename}")
                        else:
                            failed_count += 1
                            if self.debug:
                                print(f"[Video] 预加载失败（占位符）: {filename}")
                    except Exception as exc:
                        failed_count += 1
                        print(f"[Video] 预加载异常 {filename}: {exc}")
                
                self._preload_completed = True
                self._preload_progress = 1.0
                self._preload_status = "视频加载完成"
                self._preload_current_file = ""
                print(f"[Video] 预加载完成: {loaded_count} 成功, {failed_count} 失败/占位符")

        if async_load:
            threading.Thread(target=_work, daemon=True).start()
        else:
            _work()
    
    def preload_all_sync(self):
        """
        在主线程中同步预加载所有视频（阻塞调用）。
        用于确保视频在游戏开始前已加载完成。
        """
        self.preload_all(async_load=False, force_reload=False)
    
    def reload_failed_assets(self):
        """
        重新加载所有失败的资源（占位符）。
        在主线程中调用，用于复加载机制。
        """
        import threading
        if threading.current_thread() is not threading.main_thread():
            print("[Video] 警告：reload_failed_assets 应在主线程中调用")
            return
        
        reload_count = 0
        with self._load_lock:
            failed_files = [
                filename for filename, asset in self.assets.items()
                if asset.placeholder and filename not in self._loading_flags
            ]
        
        for filename in failed_files:
            # 检查重试次数
            attempts = self._reload_attempts.get(filename, 0)
            if attempts >= self._max_reload_attempts:
                if self.debug:
                    print(f"[Video] 跳过重试 {filename}（已达到最大重试次数 {self._max_reload_attempts}）")
                continue
            
            try:
                # 移除旧资源，准备重新加载
                with self._load_lock:
                    if filename in self.assets:
                        del self.assets[filename]
                
                # 重新加载
                asset = self._load_asset(filename)
                if asset and not asset.placeholder:
                    reload_count += 1
                    self._reload_attempts[filename] = 0  # 重置重试计数
                    if self.debug:
                        print(f"[Video] 复加载成功: {filename}")
                else:
                    self._reload_attempts[filename] = attempts + 1
                    if self.debug:
                        print(f"[Video] 复加载失败: {filename} (尝试 {self._reload_attempts[filename]}/{self._max_reload_attempts})")
            except Exception as exc:
                self._reload_attempts[filename] = attempts + 1
                print(f"[Video] 复加载异常 {filename}: {exc}")
        
        if reload_count > 0:
            print(f"[Video] 复加载完成: {reload_count} 个资源成功重新加载")
    
    def get_preload_status(self) -> Dict[str, any]:
        """
        获取预加载状态信息。
        
        Returns:
            包含预加载状态的字典
        """
        total = len(self.DEFAULT_CONFIG)
        loaded = sum(1 for asset in self.assets.values() if not asset.placeholder)
        placeholder = sum(1 for asset in self.assets.values() if asset.placeholder)
        
        return {
            "started": self._preload_started,
            "completed": self._preload_completed,
            "total": total,
            "loaded": loaded,
            "placeholder": placeholder,
            "progress": self._preload_progress if self._preload_started else (loaded / total if total > 0 else 0.0),
            "status": self._preload_status,
            "current_file": self._preload_current_file
        }
    
    def get_preload_progress(self) -> float:
        """获取预加载进度 (0.0 - 1.0)"""
        return self._preload_progress
    
    def is_preload_complete(self) -> bool:
        """检查预加载是否完成"""
        return self._preload_completed and self._preload_progress >= 1.0

    def play(self, event_key: str, position: Optional[Tuple[int, int]] = None, size_ratio: Optional[float] = None):
        """按事件触发播放，遵循优先级互斥策略。"""
        try:
            cfg = self.DEFAULT_CONFIG.get(event_key)
            if not cfg:
                return

            filename = cfg["file"]
            
            # 安全地加载资源（如果还在加载中，会等待或返回占位符）
            asset = self._load_asset(filename)
            if not asset or not asset.frames:
                print(f"[Video] 警告：无法加载视频资源 {filename}，跳过播放")
                return
            
            # 如果加载的是占位符，尝试在主线程中重新加载
            if asset.placeholder:
                import threading
                if threading.current_thread() is threading.main_thread():
                    # 在主线程中，尝试重新加载
                    attempts = self._reload_attempts.get(filename, 0)
                    if attempts < self._max_reload_attempts:
                        if self.debug:
                            print(f"[Video] 检测到占位符，尝试重新加载 {filename} (尝试 {attempts + 1}/{self._max_reload_attempts})")
                        try:
                            # 移除旧资源
                            with self._load_lock:
                                if filename in self.assets:
                                    del self.assets[filename]
                            
                            # 重新加载
                            asset = self._load_asset(filename)
                            if asset.placeholder:
                                self._reload_attempts[filename] = attempts + 1
                            else:
                                self._reload_attempts[filename] = 0  # 重置计数
                                if self.debug:
                                    print(f"[Video] 重新加载成功: {filename}")
                        except Exception as exc:
                            self._reload_attempts[filename] = attempts + 1
                            if self.debug:
                                print(f"[Video] 重新加载失败: {filename}, {exc}")
            
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
                    # 确保 pygame.mixer 已初始化
                    if not pygame.mixer.get_init():
                        if self.debug:
                            print(f"[Video] pygame.mixer 未初始化，跳过音频播放")
                    else:
                        channel = pygame.mixer.find_channel(True)
                        if channel:
                            channel.play(asset.audio)
                            self.active.audio_channel = channel
                        else:
                            if self.debug:
                                print(f"[Video] 无法找到可用的音频通道")
                except Exception as exc:
                    if self.debug:
                        print(f"[Video] play audio failed for {asset.name}: {exc}")
                    import traceback
                    if self.debug:
                        traceback.print_exc()

            if self.debug:
                pos_str = f" pos={position}" if position else ""
                placeholder_str = " (占位符)" if asset.placeholder else ""
                print(f"[Video] play {event_key} -> {asset.name}{placeholder_str} priority={priority} area={cfg['area']} ratio={self.active.size_ratio}{pos_str}")
        except Exception as exc:
            print(f"[Video] 播放视频时发生错误 {event_key}: {exc}")
            import traceback
            traceback.print_exc()
            # 不抛出异常，避免闪退

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
        try:
            frame = self.active.current_frame(pygame.time.get_ticks())
            if not frame:
                return
            target_rect = self._compute_rect(surface, frame, self.active.size_ratio, self.active.position)
            if target_rect:
                scaled = pygame.transform.smoothscale(frame, (target_rect.width, target_rect.height))
                surface.blit(scaled, target_rect.topleft)
        except Exception as exc:
            if self.debug:
                print(f"[Video] render_world 错误: {exc}")
            # 不抛出异常，避免闪退

    def render_screen(self, surface: pygame.Surface):
        if not self.active or self.active.area not in ("screen", "fullscreen"):
            return
        try:
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
        except Exception as exc:
            if self.debug:
                print(f"[Video] render_screen 错误: {exc}")
            # 不抛出异常，避免闪退

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

    def _cleanup_temp_files(self):
        """清理所有临时音频文件"""
        for tmp_path in self._temp_files:
            try:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
            except Exception:
                pass
        self._temp_files.clear()

