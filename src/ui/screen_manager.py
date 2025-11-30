from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

import pygame
import pygame_gui

from src.ui.ui_components import UIManagerWrapper


@dataclass
class ScreenContext:
    """向具体屏幕传递的共享上下文数据占位符。"""

    title: str = "坦克大战 - 联机测试版"
    subtitle: str = "按下 Enter 开始，Esc 退出"
    
    # 状态跳转控制
    next_state: Optional[str] = None
    
    # 联机相关
    is_host: bool = False
    username: str = "Player"
    game_mode: str = "single"  # 'single' or 'multi'
    
    # 坦克选择
    player_tank_id: int = 1
    enemy_tank_id: int = 1  # For multiplayer sync


class BaseScreen:
    """所有 UI 屏幕的基类，提供统一接口。"""

    def __init__(self, surface: pygame.Surface, context: ScreenContext, ui_manager: UIManagerWrapper, network_manager=None):
        self.surface = surface
        self.context = context
        self.ui_manager = ui_manager
        self.network_manager = network_manager
        
        from src.ui.ui_components import get_chinese_font
        font_path = get_chinese_font()
        if font_path:
            self.font = pygame.font.Font(font_path, 26)
            self.small_font = pygame.font.Font(font_path, 18)
        else:
            self.font = pygame.font.SysFont("simhei", 26)
            self.small_font = pygame.font.SysFont("simhei", 18)
            
        self.manager = ui_manager.get_manager() # 便捷访问 pygame_gui manager

    def on_enter(self):
        """进入屏幕时的回调（用于初始化 UI 元素）。"""
        pass

    def on_exit(self):
        """退出屏幕时的回调（用于清理 UI 元素）。"""
        self.ui_manager.clear()

    def handle_event(self, event: pygame.event.Event):
        """处理输入事件（子类按需覆盖）。"""
        # 默认将事件传递给 UI 管理器
        # 子类可以在此基础上添加自定义事件处理
        self.ui_manager.handle_event(event)

    def update(self, time_delta: float):
        """执行屏幕动画/状态更新。"""
        pass

    def render(self):
        """将屏幕绘制到 surface。"""
        pass

    def get_window_manager(self):
        """获取GameEngine的WindowManager实例"""
        # 通过ScreenManager获取WindowManager
        # 这里假设ScreenManager会被设置到上下文中或通过其他方式可访问
        screen_manager = getattr(self.context, 'screen_manager', None)
        if screen_manager and hasattr(screen_manager, 'get_window_manager'):
            return screen_manager.get_window_manager()
        return None


class TextScreen(BaseScreen):
    """使用居中文本占位的简单屏幕."""

    def __init__(self, surface: pygame.Surface, context: ScreenContext, ui_manager: UIManagerWrapper, title: str, description: str, network_manager=None):
        super().__init__(surface, context, ui_manager, network_manager)
        self.title = title
        self.description = description

    def render(self):
        width, height = self.surface.get_size()
        self.surface.fill((24, 24, 24))
        title_surface = self.font.render(self.title, True, (255, 255, 255))
        desc_surface = self.small_font.render(self.description, True, (180, 180, 180))
        self.surface.blit(title_surface, title_surface.get_rect(center=(width // 2, height // 2 - 20)))
        self.surface.blit(desc_surface, desc_surface.get_rect(center=(width // 2, height // 2 + 20)))
        
        # 绘制 UI 元素（如果有）
        self.ui_manager.draw_ui(self.surface)


class ScreenManager:
    """负责管理不同 UI 屏幕的简单状态机。"""

    def __init__(self, surface: pygame.Surface, network_manager=None):
        self.surface = surface
        self.context = ScreenContext()
        self.screens: Dict[str, BaseScreen] = {}
        self.current_state = "menu"
        self.network_manager = network_manager
        self.game_engine = None  # 将由GameEngine设置
        
        # 将ScreenManager设置到上下文中，以便BaseScreen可以访问
        self.context.screen_manager = self
        
        # 初始化 UI 管理器
        width, height = surface.get_size()
        self.ui_manager = UIManagerWrapper(width, height)
        
        self._init_default_screens()
        
        # 初始化当前屏幕
        current_screen = self._get_current_screen()
        if current_screen:
            current_screen.on_enter()

    def get_window_manager(self):
        """获取GameEngine的WindowManager实例"""
        if self.game_engine and hasattr(self.game_engine, 'window_manager'):
            return self.game_engine.window_manager
        return None

    def notify_window_resized(self, width, height):
        """
        通知窗口大小已改变，更新UI管理器
        
        Args:
            width: 新的窗口宽度
            height: 新的窗口高度
        """
        # 更新UI管理器以适应新窗口大小
        self.ui_manager.set_resolution(width, height)
        
        # 重新初始化当前屏幕以适应新窗口大小
        current_screen = self._get_current_screen()
        if current_screen:
            # 保持当前状态不变，只刷新UI元素
            current_screen.on_exit()
            current_screen.on_enter()
            
        print(f"ScreenManager已响应窗口大小改变: {width}x{height}")

    # ------------------------------------------------------------------ #
    # 生命周期接口（供 GameEngine 调用）
    # ------------------------------------------------------------------ #
    def handle_event(self, event: pygame.event.Event):
        # 1. 先让 UI 管理器处理事件
        self.ui_manager.handle_event(event)
        
        # 2. 再让当前屏幕处理事件
        screen = self._get_current_screen()
        if screen:
            screen.handle_event(event)

    def update(self, requested_state: Optional[str] = None):
        # 计算时间增量
        time_delta = 1.0 / 60.0
        
        # 检查 context 中的状态跳转请求
        if self.context.next_state:
            requested_state = self.context.next_state
            self.context.next_state = None
        
        if requested_state and requested_state != self.current_state:
            self.set_state(requested_state)
            
        # 更新 UI 管理器
        self.ui_manager.update(time_delta)
        
        screen = self._get_current_screen()
        if screen:
            screen.update(time_delta)

    def render(self):
        screen = self._get_current_screen()
        if screen:
            screen.render()
            # 统一绘制 UI
            self.ui_manager.draw_ui(self.surface)

    # ------------------------------------------------------------------ #
    # 状态切换与注册
    # ------------------------------------------------------------------ #
    def set_state(self, state: str):
        if state not in self.screens:
            raise ValueError(f"未注册的屏幕状态: {state}")
            
        old_state = self.current_state
        
        # 退出旧屏幕
        old_screen = self._get_current_screen()
        if old_screen:
            old_screen.on_exit()
        
        # 先更新状态，这样 resize 回调会通知到新屏幕
        self.current_state = state
        
        # 如果退出的是地图编辑器屏幕，恢复窗口大小
        if old_state == "map_editor" and self.game_engine and self.game_engine.window_manager:
            self.game_engine.window_manager.restore_original_size()
        
        # 进入新屏幕
        new_screen = self._get_current_screen()
        if new_screen:
            # 确保UI管理器是空的
            self.ui_manager.clear()
            new_screen.on_enter()

    def register_screen(self, state: str, screen: BaseScreen):
        self.screens[state] = screen

    # ------------------------------------------------------------------ #
    # 内部工具
    # ------------------------------------------------------------------ #
    def _init_default_screens(self):
        # 延迟导入以避免循环依赖
        from src.ui.menu_screens import MainMenuScreen, SinglePlayerSetupScreen, LobbyScreen, RoomScreen
        from src.ui.map_editor_screen import MapEditorScreen
        
        self.register_screen(
            "menu",
            MainMenuScreen(self.surface, self.context, self.ui_manager, self.network_manager)
        )
        self.register_screen(
            "single_setup",
            SinglePlayerSetupScreen(self.surface, self.context, self.ui_manager, self.network_manager)
        )
        self.register_screen(
            "lobby",
            LobbyScreen(self.surface, self.context, self.ui_manager, self.network_manager)
        )
        self.register_screen(
            "room",
            RoomScreen(self.surface, self.context, self.ui_manager, self.network_manager)
        )
        self.register_screen(
            "game",
            TextScreen(
                self.surface,
                self.context,
                self.ui_manager,
                title="游戏加载中",
                description="请稍候，等待同步数据...",
                network_manager=self.network_manager
            ),
        )
        self.register_screen(
            "settings",
            TextScreen(
                self.surface,
                self.context,
                self.ui_manager,
                title="设置",
                description="即将支持自定义键位/音量",
                network_manager=self.network_manager
            ),
        )
        self.register_screen(
            "map_editor",
            MapEditorScreen(self.surface, self.context, self.ui_manager, self.network_manager)
        )

    def _get_current_screen(self) -> Optional[BaseScreen]:
        return self.screens.get(self.current_state)
