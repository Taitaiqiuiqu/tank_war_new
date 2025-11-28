import pygame
import pygame_gui
from pygame_gui.ui_manager import UIManager

class UIManagerWrapper:
    """pygame_gui UIManager 的封装类，用于统一管理 UI 主题和资源。"""
    
    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # 初始化 UIManager
        self.manager = UIManager((screen_width, screen_height))
        
        # 设置中文字体
        font_path = get_chinese_font()
        if font_path:
            print(f"Loading font: {font_path}")
            self.manager.add_font_paths("chinese", font_path)
            
            # 加载主题文件
            import os
            theme_path = os.path.join(os.path.dirname(__file__), 'theme.json')
            try:
                self.manager.get_theme().load_theme(theme_path)
            except Exception as e:
                print(f"Failed to load theme: {e}")

        
    def handle_event(self, event: pygame.event.Event):
        """处理 UI 事件"""
        self.manager.process_events(event)
        
    def update(self, time_delta: float):
        """更新 UI 状态"""
        self.manager.update(time_delta)
        
    def draw_ui(self, window_surface: pygame.Surface):
        """绘制 UI"""
        self.manager.draw_ui(window_surface)
        
    def clear(self):
        """清除所有 UI 元素"""
        self.manager.clear_and_reset()

    def get_manager(self):
        """获取原始 manager 实例"""
        return self.manager


def get_chinese_font() -> str | None:
    """寻找可用的中文字体路径"""
    # 常见中文字体文件名 (Windows)
    font_names = [
        "msyh", "msyhbd", # 微软雅黑
        "simhei",         # 黑体
        "simsun",         # 宋体
        "kaiti",          # 楷体
        "arialuni",       # Arial Unicode MS
    ]
    
    for name in font_names:
        try:
            font_path = pygame.font.match_font(name)
            if font_path:
                return font_path
        except Exception:
            continue
            
    # 如果找不到，尝试系统默认
    return pygame.font.match_font("arial")
