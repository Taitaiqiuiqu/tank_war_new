# Initialize i18n FIRST before any pygame_gui imports
import src.ui.init_i18n  # This must be first!

import pygame
import pygame_gui
from pygame_gui.ui_manager import UIManager

# Monkey patch pygame_gui's translate function to bypass i18n errors
# This prevents the AttributeError when i18n is not properly configured
try:
    from pygame_gui.core import utility
    original_translate = utility.translate
    
    def patched_translate(text, **kwargs):
            """Bypass i18n translation to prevent errors and preserve non-ASCII."""
            if text is None:
                return ""
            try:
                return str(text)
            except Exception:
                return ""
    
    utility.translate = patched_translate
except Exception as e:
    print(f"Warning: Could not patch pygame_gui translate: {e}")

class UIManagerWrapper:
    """pygame_gui UIManager 的封装类，用于统一管理 UI 主题和资源。"""
    
    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.last_focused_element = None  # 跟踪上一个获得焦点的元素
        # 记录基准分辨率用于缩放
        self.base_width = screen_width
        self.base_height = screen_height
        self.scale_x = 1.0
        self.scale_y = 1.0
        
        # 初始化 UIManager
        self.manager = UIManager((screen_width, screen_height))
        
        # 设置中文像素字体
        font_path = get_chinese_font()
        if font_path:
            print(f"✓ 成功加载中文像素字体: {font_path}")
            # 注册两种名称：pixel（主题使用）和 chinese（兼容旧代码）
            self.manager.add_font_paths("pixel", font_path)
            self.manager.add_font_paths("chinese", font_path)
        else:
            print(f"✗ 警告: 未找到中文像素字体，中文输入可能无法正常显示")
        
        # 加载主题文件
        import os
        theme_path = os.path.join(os.path.dirname(__file__), 'theme.json')
        try:
            self.manager.get_theme().load_theme(theme_path)
            print(f"✓ 成功加载UI主题: {theme_path}")
        except Exception as e:
            print(f"✗ 加载主题失败: {e}")

        
    def handle_event(self, event: pygame.event.Event):
        """处理 UI 事件"""
        self.manager.process_events(event)
        
    def update(self, time_delta: float):
        """更新 UI 状态"""
        self.manager.update(time_delta)
        # 更新输入法候选词窗口位置
        self._update_ime_rect()
        
    def draw_ui(self, window_surface: pygame.Surface):
        """绘制 UI"""
        self.manager.draw_ui(window_surface)
        
    def clear(self):
        """清除所有 UI 元素"""
        self.manager.clear_and_reset()

    def get_manager(self):
        """获取原始 manager 实例"""
        return self.manager

    def set_resolution(self, width: int, height: int):
        """设置新的分辨率"""
        self.screen_width = width
        self.screen_height = height
        self.manager.set_window_resolution((width, height))
        # 缩放比例（相对初始分辨率）
        if hasattr(self, "base_width") and hasattr(self, "base_height"):
            self.scale_x = width / self.base_width if self.base_width else 1.0
            self.scale_y = height / self.base_height if self.base_height else 1.0
        else:
            # 记录初始分辨率用于缩放
            self.base_width, self.base_height = width, height
            self.scale_x = 1.0
            self.scale_y = 1.0
    
    def scale_rect(self, rect: pygame.Rect) -> pygame.Rect:
        """
        根据当前缩放比例缩放一个 Rect。
        注意：需要调用方自行决定 anchor（此处简单基于(0,0)缩放）。
        """
        if not hasattr(self, "scale_x"):
            return rect
        return pygame.Rect(
            int(rect.x * self.scale_x),
            int(rect.y * self.scale_y),
            int(rect.width * self.scale_x),
            int(rect.height * self.scale_y),
        )
    
    def _update_ime_rect(self):
        """更新IME候选词窗口位置"""
        try:
            from pygame_gui.elements import UITextEntryLine
            
            # 获取当前获得焦点的元素
            focused_set = self.manager.get_focus_set()
            
            if focused_set and len(focused_set) > 0:
                element = list(focused_set)[0]
                if isinstance(element, UITextEntryLine):
                    # 获取文本框的屏幕位置
                    rect = element.get_abs_rect()
                    # 设置IME候选词窗口位置到文本框下方
                    ime_rect = pygame.Rect(rect.x, rect.y + rect.height, rect.width, 30)
                    pygame.key.set_text_input_rect(ime_rect)
                    self.last_focused_element = element
                    return
            
            # 失去焦点时重置为默认位置
            if self.last_focused_element:
                pygame.key.set_text_input_rect(pygame.Rect(0, 0, 1, 1))
                self.last_focused_element = None
        except Exception as e:
            # 静默失败，不影响正常功能
            pass


def get_chinese_font() -> str | None:
    """寻找可用的中文字体路径"""
    import os
    
    fonts_dir = os.path.join(os.path.dirname(__file__), "fonts")
    
    # 1) 优先使用项目内的像素中文字体（约定名）
    preferred_names = ["全小素.ttf", "pixel_chinese.ttf", "pixel-chinese.ttf", "pixel_cn.ttf"]
    for name in preferred_names:
        candidate = os.path.join(fonts_dir, name)
        if os.path.exists(candidate):
            return candidate
    
    # 2) 若未找到约定名，自动选择 fonts 目录下的第一个 ttf/ttc/otf
    if os.path.isdir(fonts_dir):
        for fname in os.listdir(fonts_dir):
            if fname.lower().endswith((".ttf", ".ttc", ".otf")):
                return os.path.join(fonts_dir, fname)
    
    # 方法1: 尝试 Windows 系统字体的直接路径
    windows_fonts = [
        r"C:\Windows\Fonts\msyh.ttc",      # 微软雅黑
        r"C:\Windows\Fonts\msyhbd.ttc",    # 微软雅黑粗体
        r"C:\Windows\Fonts\simhei.ttf",    # 黑体
        r"C:\Windows\Fonts\simsun.ttc",    # 宋体
        r"C:\Windows\Fonts\kaiti.ttf",     # 楷体
    ]
    
    for font_path in windows_fonts:
        if os.path.exists(font_path):
            return font_path
    
    # 方法2: 使用 pygame 查找字体
    font_names = [
        "microsoftyahei", "msyh", "msyhbd",  # 微软雅黑
        "simhei",                             # 黑体
        "simsun",                             # 宋体
        "kaiti",                              # 楷体
        "arialuni",                           # Arial Unicode MS
    ]
    
    for name in font_names:
        try:
            font_path = pygame.font.match_font(name)
            if font_path:
                return font_path
        except Exception:
            continue
            
    # 方法3: 如果找不到，返回 None（pygame_gui 会使用默认字体）
    return None
