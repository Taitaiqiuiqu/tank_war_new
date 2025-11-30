"""
窗口管理器 - 统一管理游戏窗口大小控制
"""
import pygame


class WindowManager:
    """窗口管理器，负责统一处理窗口大小控制"""
    
    def __init__(self, game_surface):
        """
        初始化窗口管理器
        
        Args:
            game_surface: pygame 表面对象
        """
        self.game_surface = game_surface
        self.original_width, self.original_height = game_surface.get_size()
        self.current_width, self.current_height = self.original_width, self.original_height
        
        # 预定义的窗口大小配置
        self.window_configs = {
            'default': (800, 600),
            'map_editor': (800, 690),
            'fullscreen': (1920, 1080)  # 可以扩展支持全屏
        }
        
        # 回调函数列表，窗口大小改变时调用
        self.resize_callbacks = []
        
        # 防止重复调整的标记
        self._is_resizing = False
        
    def register_resize_callback(self, callback):
        """
        注册窗口大小改变回调函数
        
        Args:
            callback: 回调函数，接收 (width, height) 作为参数
        """
        if callback not in self.resize_callbacks:
            self.resize_callbacks.append(callback)
    
    def unregister_resize_callback(self, callback):
        """
        注销窗口大小改变回调函数
        
        Args:
            callback: 回调函数
        """
        if callback in self.resize_callbacks:
            self.resize_callbacks.remove(callback)
    
    def _notify_resize_callbacks(self, width, height):
        """通知所有注册的回调函数窗口大小已改变"""
        for callback in self.resize_callbacks:
            try:
                callback(width, height)
            except Exception as e:
                print(f"窗口大小回调函数执行错误: {e}")
    
    def set_window_size(self, width, height):
        """
        设置窗口大小并调用回调函数
        
        Args:
            width: 新窗口宽度
            height: 新窗口高度
        """
        # 防止重复调整
        if self._is_resizing:
            print("重复调整窗口大小被阻止")
            return
            
        # 检查是否真的需要调整大小
        if self.current_width == width and self.current_height == height:
            print("窗口大小相同，无需调整")
            return
            
        try:
            self._is_resizing = True
            
            # 设置新窗口大小
            self.game_surface = pygame.display.set_mode((width, height))
            self.current_width, self.current_height = width, height
            
            # 调用回调函数通知窗口大小改变
            self._notify_resize_callbacks(width, height)
            
            print(f"窗口大小已调整为: {width}x{height}")
            
        except Exception as e:
            print(f"调整窗口大小时出错: {e}")
        finally:
            self._is_resizing = False
    
    def get_size(self):
        """获取当前窗口大小"""
        return self.current_width, self.current_height
    
    def resize_to_config(self, config_name):
        """
        根据预定义配置调整窗口大小
        
        Args:
            config_name: 配置名称 ('default', 'map_editor', 'fullscreen')
        """
        if config_name in self.window_configs:
            width, height = self.window_configs[config_name]
            self.set_window_size(width, height)
        else:
            print(f"未知的窗口配置: {config_name}")
    
    def restore_original_size(self):
        """恢复原始窗口大小"""
        self.set_window_size(self.original_width, self.original_height)
    
    def get_original_size(self):
        """获取原始窗口大小"""
        return self.original_width, self.original_height
    
    def is_same_size(self, width, height):
        """
        检查当前窗口大小是否与指定大小相同
        
        Args:
            width: 要比较的宽度
            height: 要比较的高度
            
        Returns:
            bool: 如果大小相同返回 True，否则返回 False
        """
        return self.current_width == width and self.current_height == height
    
    def add_window_config(self, name, width, height):
        """
        添加新的窗口大小配置
        
        Args:
            name: 配置名称
            width: 宽度
            height: 高度
        """
        self.window_configs[name] = (width, height)
        print(f"已添加窗口配置 '{name}': {width}x{height}")
    
    def get_window_config(self, name):
        """
        获取指定窗口配置
        
        Args:
            name: 配置名称
            
        Returns:
            tuple: (width, height) 或 None 如果配置不存在
        """
        return self.window_configs.get(name)
    
    def reset_to_default(self):
        """重置为默认窗口大小"""
        self.resize_to_config('default')
    
    def __str__(self):
        """返回窗口管理器的字符串表示"""
        return f"WindowManager({self.current_width}x{self.current_height}, 原始: {self.original_width}x{self.original_height})"