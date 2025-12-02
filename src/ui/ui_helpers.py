"""
UI辅助工具模块
提供通用的UI增强功能，包括工具提示、淡入淡出效果、字符计数器等
"""
import pygame
import time
from typing import Optional, Tuple


class TemporaryMessage:
    """临时消息显示器，支持淡入淡出效果"""
    
    def __init__(self, text: str, duration: float = 3.0, font_size: int = 16):
        """
        初始化临时消息
        
        Args:
            text: 要显示的文本
            duration: 显示持续时间（秒）
            font_size: 字体大小
        """
        self.text = text
        self.duration = duration
        self.font = pygame.font.SysFont('SimHei', font_size)
        self.start_time = time.time()
        self.fade_duration = 0.5  # 淡入淡出持续时间
        
    def is_active(self) -> bool:
        """检查消息是否仍然活跃"""
        return time.time() - self.start_time < self.duration
    
    def get_alpha(self) -> int:
        """获取当前透明度（0-255）"""
        elapsed = time.time() - self.start_time
        
        # 淡入阶段
        if elapsed < self.fade_duration:
            return int(255 * (elapsed / self.fade_duration))
        
        # 淡出阶段
        elif elapsed > self.duration - self.fade_duration:
            remaining = self.duration - elapsed
            return int(255 * (remaining / self.fade_duration))
        
        # 完全显示阶段
        else:
            return 255
    
    def render(self, surface: pygame.Surface, position: Tuple[int, int]):
        """
        渲染消息到指定表面
        
        Args:
            surface: 目标表面
            position: 渲染位置 (x, y)
        """
        if not self.is_active():
            return
        
        alpha = self.get_alpha()
        
        # 渲染文本
        text_surface = self.font.render(self.text, True, (255, 255, 255))
        
        # 创建带透明度的表面
        temp_surface = pygame.Surface(text_surface.get_size(), pygame.SRCALPHA)
        temp_surface.fill((0, 0, 0, 0))
        
        # 绘制半透明背景
        bg_rect = temp_surface.get_rect()
        bg_rect.inflate_ip(20, 10)
        bg_surface = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        bg_surface.fill((50, 50, 50, int(alpha * 0.8)))
        
        # 组合背景和文本
        final_surface = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        final_surface.blit(bg_surface, (0, 0))
        
        # 设置文本透明度
        text_surface.set_alpha(alpha)
        text_rect = text_surface.get_rect(center=(bg_rect.width // 2, bg_rect.height // 2))
        final_surface.blit(text_surface, text_rect)
        
        # 绘制到目标表面
        surface.blit(final_surface, position)


class CharacterCounter:
    """字符计数器，用于文本输入框"""
    
    def __init__(self, max_length: int = 8):
        """
        初始化字符计数器
        
        Args:
            max_length: 最大字符数
        """
        self.max_length = max_length
        self.font = pygame.font.SysFont('SimHei', 12)
    
    def get_counter_text(self, current_text: str) -> str:
        """
        获取计数器文本
        
        Args:
            current_text: 当前输入的文本
            
        Returns:
            格式化的计数器文本，如 "5/8"
        """
        current_length = len(current_text)
        return f"{current_length}/{self.max_length}"
    
    def is_valid(self, text: str) -> bool:
        """
        检查文本是否在长度限制内
        
        Args:
            text: 要检查的文本
            
        Returns:
            是否有效
        """
        return len(text) <= self.max_length
    
    def render(self, surface: pygame.Surface, position: Tuple[int, int], current_text: str):
        """
        渲染计数器
        
        Args:
            surface: 目标表面
            position: 渲染位置
            current_text: 当前文本
        """
        counter_text = self.get_counter_text(current_text)
        current_length = len(current_text)
        
        # 根据剩余字符数选择颜色
        if current_length >= self.max_length:
            color = (255, 100, 100)  # 红色 - 已达上限
        elif current_length >= self.max_length * 0.8:
            color = (255, 200, 100)  # 橙色 - 接近上限
        else:
            color = (150, 150, 150)  # 灰色 - 正常
        
        text_surface = self.font.render(counter_text, True, color)
        surface.blit(text_surface, position)


class TankSkinNames:
    """坦克皮肤名称映射"""
    
    SKIN_NAMES = {
        1: "轻型坦克",
        2: "中型坦克",
        3: "重型坦克",
        4: "超重坦克"
    }
    
    @classmethod
    def get_name(cls, tank_id: int) -> str:
        """
        获取坦克皮肤名称
        
        Args:
            tank_id: 坦克ID (1-4)
            
        Returns:
            坦克皮肤名称
        """
        return cls.SKIN_NAMES.get(tank_id, f"坦克 {tank_id}")


class CountdownTimer:
    """倒计时计时器"""
    
    def __init__(self, duration: float = 3.0):
        """
        初始化倒计时
        
        Args:
            duration: 倒计时时长（秒）
        """
        self.duration = duration
        self.start_time = None
        self.font = pygame.font.SysFont('SimHei', 24)
    
    def start(self):
        """开始倒计时"""
        self.start_time = time.time()
    
    def is_active(self) -> bool:
        """检查倒计时是否仍在进行"""
        if self.start_time is None:
            return False
        return time.time() - self.start_time < self.duration
    
    def get_remaining(self) -> int:
        """获取剩余秒数"""
        if self.start_time is None:
            return int(self.duration)
        
        elapsed = time.time() - self.start_time
        remaining = max(0, self.duration - elapsed)
        return int(remaining) + 1  # 向上取整
    
    def render(self, surface: pygame.Surface, position: Tuple[int, int]):
        """
        渲染倒计时
        
        Args:
            surface: 目标表面
            position: 渲染位置
        """
        if not self.is_active():
            return
        
        remaining = self.get_remaining()
        text = f"战斗即将开始... 剩余 {remaining} 秒"
        
        # 根据剩余时间改变颜色
        if remaining <= 1:
            color = (255, 100, 100)  # 红色
        elif remaining <= 2:
            color = (255, 200, 100)  # 橙色
        else:
            color = (255, 255, 100)  # 黄色
        
        text_surface = self.font.render(text, True, color)
        text_rect = text_surface.get_rect(center=position)
        surface.blit(text_surface, text_rect)


def create_tooltip_text(base_text: str, description: str = "", shortcut: str = "") -> str:
    """
    创建工具提示文本
    
    Args:
        base_text: 基础文本
        description: 描述信息
        shortcut: 快捷键
        
    Returns:
        格式化的工具提示文本
    """
    parts = [base_text]
    
    if description:
        parts.append(f"({description})")
    
    if shortcut:
        parts.append(f"[{shortcut}]")
    
    return " ".join(parts)


def validate_map_name(name: str) -> Tuple[bool, str]:
    """
    验证地图名称
    
    Args:
        name: 地图名称
        
    Returns:
        (是否有效, 错误消息)
    """
    if not name:
        return False, "地图名称不能为空"
    
    if len(name) > 20:
        return False, "地图名称不能超过20个字符"
    
    # 检查特殊字符
    invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    for char in invalid_chars:
        if char in name:
            return False, f"地图名称不能包含特殊字符: {char}"
    
    return True, ""
