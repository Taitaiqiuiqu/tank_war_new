"""
加载界面 - 显示资源加载进度
"""
import pygame
import pygame_gui
from pygame_gui.elements import UIProgressBar, UILabel, UIPanel
import math

from src.ui.screen_manager import BaseScreen
from src.utils.resource_manager import resource_manager
from src.ui.video_manager import VideoPlaybackController
import os


class LoadingScreen(BaseScreen):
    """加载界面，显示资源加载进度"""
    
    def __init__(self, surface: pygame.Surface, manager: pygame_gui.UIManager, context):
        super().__init__(surface, manager, context)
        self.progress_bar = None
        self.status_label = None
        self.panel = None
        self._loading_complete = False
        self._next_state = None
        self._rotation_angle = 0.0  # 转圈动画角度
        self._rotation_speed = 180.0  # 每秒旋转角度
        self._spinner_radius = 30  # 转圈动画半径（增大50%）
        self._spinner_center = None  # 转圈动画中心点
        
        # 初始化视频管理器（如果还没有）
        if not hasattr(self.context, 'video_manager'):
            video_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "videos"))
            self.context.video_manager = VideoPlaybackController(video_dir)
    
    def on_enter(self):
        """进入加载界面"""
        super().on_enter()
        
        w, h = self.surface.get_size()
        # 增大50%：700 -> 1050, 350 -> 525
        panel_w = 1050
        panel_h = 525
        panel_x = (w - panel_w) // 2
        panel_y = (h - panel_h) // 2
        
        # 创建面板
        self.panel = UIPanel(
            relative_rect=pygame.Rect(panel_x, panel_y, panel_w, panel_h),
            manager=self.manager,
            object_id="#loading_panel"
        )
        
        # 坦克大战标题（大标题，使用亮黄色）
        # 标题更大：60 -> 90
        # 保存标题位置和文本，用于自定义渲染
        self._title_text = "坦克大战"
        self._title_rect = pygame.Rect(40, 40, panel_w - 80, 90)
        # 预加载标题字体
        try:
            font_size = 80
            self._title_font = pygame.font.SysFont(["simhei", "simsun", "microsoftyahei", "arial"], font_size, bold=True)
            if not self._title_font:
                self._title_font = pygame.font.Font(None, font_size)
        except:
            self._title_font = pygame.font.Font(None, font_size)
        
        # 正在加载素材提示
        self.loading_hint_label = UILabel(
            relative_rect=pygame.Rect(40, 150, panel_w - 80, 50),
            text="正在加载素材...",
            manager=self.manager,
            container=self.panel
        )
        
        # 转圈动画区域（在提示文本下方）
        spinner_y = 220
        self._spinner_center = (panel_x + panel_w // 2, panel_y + spinner_y)
        self._spinner_radius = 30  # 增大转圈动画半径
        
        # 进度条
        self.progress_bar = UIProgressBar(
            relative_rect=pygame.Rect(40, 300, panel_w - 80, 40),
            manager=self.manager,
            container=self.panel
        )
        
        # 状态文本
        self.status_label = UILabel(
            relative_rect=pygame.Rect(40, 360, panel_w - 80, 40),
            text="初始化中...",
            manager=self.manager,
            container=self.panel
        )
        
        # 百分比文本
        self.percent_label = UILabel(
            relative_rect=pygame.Rect(40, 420, panel_w - 80, 40),
            text="0%",
            manager=self.manager,
            container=self.panel
        )
        
        # 重置加载状态和动画
        self._loading_complete = False
        self._rotation_angle = 0.0
        self._switch_delay = None
        self._simulated_progress = 0.0
        self._simulated_speed = 0.3  # 每秒增长30%
        # 获取待进入的状态（如果有）
        self._next_state = getattr(self.context, '_pending_game_state', None)
        if not self._next_state:
            self._next_state = getattr(self.context, 'next_state', None)
        # 如果没有指定下一个状态，默认跳转到菜单
        if not self._next_state:
            self._next_state = "menu"
        
        # 开始加载资源
        self._start_loading()
    
    def on_exit(self):
        """退出加载界面"""
        super().on_exit()
        if self.panel:
            self.panel.kill()
        self.panel = None
        self.progress_bar = None
        self.status_label = None
        self.percent_label = None
    
    def _start_loading(self):
        """开始加载资源"""
        # 预加载图片和音频资源（如果还没加载）
        if not resource_manager.is_preload_complete():
            print("[Loading] 开始预加载图片和音频资源...")
            resource_manager.preload_all()
            print(f"[Loading] 资源预加载完成: loaded={resource_manager._resources_loaded}, progress={resource_manager.get_preload_progress()}")
        else:
            # 如果已经加载完成，确保进度是1.0
            if resource_manager.get_preload_progress() < 1.0:
                # 强制设置进度为1.0（资源已加载，只是进度未更新）
                resource_manager._preload_progress = 1.0
            print(f"[Loading] 资源已预加载: loaded={resource_manager._resources_loaded}, progress={resource_manager.get_preload_progress()}")
        
        # 预加载视频资源（同步，带进度回调）
        if hasattr(self.context, 'video_manager'):
            video_manager = self.context.video_manager
            if not video_manager.is_preload_complete():
                print("[Loading] 开始预加载视频资源...")
                video_manager.preload_all(async_load=False, progress_callback=self._on_video_progress)
                print(f"[Loading] 视频预加载完成: completed={video_manager._preload_completed}, progress={video_manager.get_preload_progress()}")
            else:
                # 如果已经加载完成，确保进度是1.0
                if video_manager.get_preload_progress() < 1.0:
                    video_manager._preload_progress = 1.0
                    video_manager._preload_completed = True
                print(f"[Loading] 视频已预加载: completed={video_manager._preload_completed}, progress={video_manager.get_preload_progress()}")
        else:
            print("[Loading] 视频管理器不存在，跳过视频预加载")
    
    def _on_video_progress(self, progress: float, status: str):
        """视频加载进度回调"""
        # 视频加载占40%的权重
        video_progress = progress * 0.4
        
        # 图片和音频资源加载占60%的权重
        resource_progress = resource_manager.get_preload_progress() * 0.6
        
        # 总进度
        total_progress = video_progress + resource_progress
        
        # 更新进度条
        if self.progress_bar:
            self.progress_bar.set_current_progress(total_progress)
        
        # 更新状态文本
        if self.status_label:
            if status:
                self.status_label.set_text(status)
            else:
                self.status_label.set_text(resource_manager.get_preload_status())
        
        # 更新百分比
        if self.percent_label:
            percent = int(total_progress * 100)
            self.percent_label.set_text(f"{percent}%")
    
    def update(self, time_delta: float):
        """更新加载界面"""
        super().update(time_delta)
        
        # 更新转圈动画
        self._rotation_angle += self._rotation_speed * time_delta
        if self._rotation_angle >= 360.0:
            self._rotation_angle -= 360.0
        
        # 检查资源是否真正加载完成
        # 检查资源管理器：如果进度是1.0或状态是"资源加载完成"，认为完成
        resource_progress = resource_manager.get_preload_progress()
        resource_status = resource_manager.get_preload_status()
        resource_loaded = resource_manager._resources_loaded
        resource_complete = resource_manager.is_preload_complete() or (resource_progress >= 1.0) or ("完成" in resource_status)
        
        # 检查视频管理器：如果已完成或不存在，认为完成
        video_complete = True
        video_loaded = True
        video_progress = 1.0
        if hasattr(self.context, 'video_manager'):
            video_manager = self.context.video_manager
            video_loaded = video_manager._preload_completed
            video_progress = video_manager.get_preload_progress()
            
            # 如果视频预加载已完成（_preload_completed=True），即使进度是0.0也认为完成
            # 因为后台线程可能只创建了占位符，但预加载过程已完成
            if video_loaded:
                video_complete = True
                video_progress = 1.0  # 强制设置为1.0，确保显示100%
            else:
                # 如果视频预加载已开始但未完成，检查是否所有视频都已加载（即使是占位符也算完成）
                if video_manager._preload_started:
                    # 检查是否所有视频都已处理（已加载或占位符）
                    total_videos = len(video_manager.DEFAULT_CONFIG)
                    loaded_videos = len(video_manager.assets)
                    if loaded_videos >= total_videos:
                        video_complete = True
                        video_loaded = True
                        video_progress = 1.0
                    else:
                        video_complete = video_manager.is_preload_complete()
                else:
                    # 如果预加载未开始，认为已完成（不需要等待）
                    video_complete = True
                    video_loaded = True
                    video_progress = 1.0
        
        # 调试信息（每60帧打印一次）
        if not hasattr(self, '_debug_counter'):
            self._debug_counter = 0
        self._debug_counter += 1
        if self._debug_counter % 60 == 0:  # 每秒打印一次
            print(f"[Loading] 资源状态: loaded={resource_loaded}, progress={resource_progress:.2f}, status='{resource_status}', complete={resource_complete}")
            print(f"[Loading] 视频状态: loaded={video_loaded}, progress={video_progress:.2f}, complete={video_complete}")
            print(f"[Loading] 总完成状态: resource_complete={resource_complete}, video_complete={video_complete}, 两者都完成={resource_complete and video_complete}")
        
        # 如果资源已加载完成，直接显示100%并准备跳转
        if resource_complete and video_complete:
            # 确保进度条显示100%
            if self.progress_bar:
                self.progress_bar.set_current_progress(1.0)
            if self.percent_label:
                self.percent_label.set_text("100%")
            if self.status_label:
                self.status_label.set_text("加载完成")
            
            # 标记为完成，延迟后切换状态
            if not self._loading_complete:
                self._loading_complete = True
                # 使用一个计数器延迟切换，确保进度条显示100%
                self._switch_delay = 0.5  # 延迟0.5秒后切换
                print(f"[Loading] 资源加载完成，将在0.5秒后切换到: {self._next_state or 'menu'}")
        else:
            # 资源未完成，使用模拟进度（快速增长到90%，然后等待真实加载完成）
            if not hasattr(self, '_simulated_progress'):
                self._simulated_progress = 0.0
                self._simulated_speed = 0.3  # 每秒增长30%
            
            # 模拟进度增长（最多到90%）
            if self._simulated_progress < 0.9:
                self._simulated_progress = min(0.9, self._simulated_progress + self._simulated_speed * time_delta)
            
            # 更新进度条
            if self.progress_bar:
                self.progress_bar.set_current_progress(self._simulated_progress)
            
            # 更新状态文本
            if self.status_label:
                resource_status = resource_manager.get_preload_status()
                video_status = ""
                if hasattr(self.context, 'video_manager'):
                    video_status = self.context.video_manager._preload_status
                
                if video_status:
                    self.status_label.set_text(video_status)
                elif resource_status:
                    self.status_label.set_text(resource_status)
                else:
                    self.status_label.set_text("正在加载素材...")
            
            # 更新百分比
            if self.percent_label:
                percent = int(self._simulated_progress * 100)
                self.percent_label.set_text(f"{percent}%")
        
        # 处理延迟切换（无论_loading_complete状态如何，都要检查延迟）
        if self._loading_complete and hasattr(self, '_switch_delay') and self._switch_delay is not None:
            self._switch_delay -= time_delta
            if self._switch_delay <= 0:
                # 切换到下一个状态
                target_state = self._next_state if self._next_state else "menu"
                print(f"[Loading] 延迟时间到，切换到: {target_state}")
                # 清除待进入状态
                if hasattr(self.context, '_pending_game_state'):
                    delattr(self.context, '_pending_game_state')
                # 直接设置状态，确保跳转
                self.context.next_state = target_state
                # 清除延迟，避免重复切换
                self._switch_delay = None
                print(f"[Loading] 已设置 next_state = {target_state}")
    
    def render(self):
        """渲染加载界面"""
        self.surface.fill((30, 30, 30))
        
        # 绘制转圈动画（在UI元素之前绘制，这样不会被面板遮挡）
        if self._spinner_center:
            center_x, center_y = self._spinner_center
            radius = self._spinner_radius
            
            # 绘制12个点组成转圈动画，形成更流畅的效果
            num_points = 12
            for i in range(num_points):
                angle = math.radians(self._rotation_angle + i * (360 / num_points))
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
                
                # 根据位置计算透明度（前面的点更亮，形成拖尾效果）
                # 使用正弦函数创建更平滑的渐变
                alpha_factor = (math.sin(i * math.pi / num_points * 2) + 1) / 2
                alpha = int(150 + 105 * alpha_factor)
                alpha = max(100, min(255, alpha))
                
                # 绘制点（大小也根据位置变化，增大50%）
                point_size = int(4 + 3 * alpha_factor)
                color = (100, 150, 255)
                pygame.draw.circle(self.surface, color, (int(x), int(y)), point_size)
        
        # 父类会处理UI渲染（包括面板、进度条等）
        
        # 在UI渲染后，绘制标题为亮黄色（确保在最上层）
        if hasattr(self, '_title_text') and hasattr(self, '_title_font') and self.panel:
            try:
                # 获取面板的绝对位置
                panel_rect = self.panel.rect
                title_rect = self._title_rect
                
                # 计算标题在屏幕上的绝对位置
                abs_title_x = panel_rect.x + title_rect.x
                abs_title_y = panel_rect.y + title_rect.y
                
                # 使用预加载的字体
                title_font = self._title_font
                
                # 亮黄色：(255, 255, 150) 或更亮的 (255, 255, 200)
                bright_yellow = (255, 255, 200)
                title_surface = title_font.render(self._title_text, True, bright_yellow)
                
                # 计算居中位置
                title_x = abs_title_x + (title_rect.width - title_surface.get_width()) // 2
                title_y = abs_title_y + (title_rect.height - title_surface.get_height()) // 2
                
                # 绘制标题（带阴影效果，增强可读性）
                shadow_offset = 3
                shadow_surface = title_font.render(self._title_text, True, (0, 0, 0))
                # 绘制阴影（多次绘制形成更明显的阴影）
                for offset_x in range(-shadow_offset, shadow_offset + 1):
                    for offset_y in range(-shadow_offset, shadow_offset + 1):
                        if offset_x != 0 or offset_y != 0:
                            self.surface.blit(shadow_surface, (title_x + offset_x, title_y + offset_y))
                
                # 绘制标题文本（在最上层）
                self.surface.blit(title_surface, (title_x, title_y))
            except Exception as e:
                # 如果字体渲染失败，使用默认方式
                print(f"[Loading] 标题渲染失败: {e}")
                import traceback
                traceback.print_exc()

