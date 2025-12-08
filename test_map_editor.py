#!/usr/bin/env python3
"""
测试地图编辑器的修改效果
"""
import os
import sys
import pygame
import pygame_gui

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 必须在导入pygame_gui之前初始化i18n
import src.ui.init_i18n

from src.ui.map_editor_screen import MapEditorScreen
from src.ui.screen_manager import ScreenManager


class TestUIManager:
    """测试用的UI管理器包装类"""
    def __init__(self, width, height):
        self.ui_manager = pygame_gui.UIManager((width, height))
    
    def get_manager(self):
        return self.ui_manager
    
    def clear(self):
        pass


class TestScreenManager:
    """测试用的屏幕管理器"""
    def __init__(self, width, height):
        self.ui_manager = TestUIManager(width, height)


def test_map_editor():
    """测试地图编辑器的修改效果"""
    print("测试地图编辑器的修改效果...")
    
    # 初始化pygame
    pygame.init()
    
    # 设置窗口尺寸
    window_width = 1280
    window_height = 720
    screen = pygame.display.set_mode((window_width, window_height), pygame.RESIZABLE)
    pygame.display.set_caption("地图编辑器测试")
    
    # 创建测试用的屏幕管理器
    screen_manager = TestScreenManager(window_width, window_height)
    
    # 创建地图编辑器屏幕
    map_editor = MapEditorScreen(screen, None, screen_manager.ui_manager)
    
    # 进入地图编辑器
    map_editor.on_enter()
    
    print("地图编辑器初始化完成")
    print(f"网格设置: {map_editor.GRID_COLS}列 x {map_editor.GRID_ROWS}行")
    print(f"地图尺寸: {map_editor.MAP_WIDTH}x{map_editor.GAME_HEIGHT} 像素")
    
    # 主循环
    clock = pygame.time.Clock()
    running = True
    
    while running:
        time_delta = clock.tick(60) / 1000.0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                # 处理窗口大小改变
                map_editor.handle_window_resized(event.w, event.h)
            
            # 处理UI事件
            map_editor.manager.process_events(event)
            
            # 处理地图编辑器事件
            map_editor.handle_event(event)
        
        # 更新UI
        map_editor.manager.update(time_delta)
        
        # 渲染地图编辑器
        map_editor.render()
        
        # 更新显示
        pygame.display.flip()
    
    # 退出地图编辑器
    map_editor.on_exit()
    pygame.quit()
    print("测试完成！")


if __name__ == "__main__":
    test_map_editor()