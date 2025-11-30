#!/usr/bin/env python3
"""
测试地图编辑器按钮功能
"""
import os
import sys
import pygame
import pygame_gui

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.ui.ui_components import UIManagerWrapper
from src.ui.screen_manager import ScreenManager, ScreenContext
from src.ui.map_editor_screen import MapEditorScreen

def test_map_editor_buttons():
    """测试地图编辑器按钮功能"""
    print("测试地图编辑器按钮功能...")
    
    # 初始化pygame
    pygame.init()
    
    # 创建测试窗口
    test_window_size = (800, 690)
    screen = pygame.display.set_mode(test_window_size)
    pygame.display.set_caption("地图编辑器按钮测试")
    
    # 创建UI管理器
    ui_wrapper = UIManagerWrapper(test_window_size[0], test_window_size[1])
    ui_manager = ui_wrapper.get_manager()
    
    # 创建上下文
    context = ScreenContext()
    context.next_state = None
    
    # 创建地图编辑器屏幕
    map_editor = MapEditorScreen(screen, context, ui_manager)
    
    # 模拟进入地图编辑器
    map_editor.on_enter()
    
    print("地图编辑器初始化完成")
    
    # 测试按钮是否存在
    buttons = [
        'btn_brick', 'btn_steel', 'btn_grass', 'btn_river', 'btn_base', 'btn_eraser',
        'btn_player_spawn', 'btn_enemy_spawn', 'btn_save', 'btn_load', 'btn_clear', 'btn_back'
    ]
    
    missing_buttons = []
    for button_name in buttons:
        if not hasattr(map_editor, button_name):
            missing_buttons.append(button_name)
        else:
            print(f"✓ {button_name} 按钮存在")
    
    if missing_buttons:
        print(f"❌ 缺失按钮: {missing_buttons}")
    else:
        print("✓ 所有按钮都存在")
    
    # 测试事件处理
    test_events = [
        pygame_gui.UI_BUTTON_PRESSED,
        pygame.MOUSEBUTTONDOWN,
        pygame.MOUSEBUTTONUP,
        pygame.MOUSEMOTION
    ]
    
    print("测试事件处理...")
    for event_type in test_events:
        try:
            if event_type == pygame_gui.UI_BUTTON_PRESSED:
                # 创建模拟按钮事件
                mock_event = pygame.event.Event(event_type, {'ui_element': map_editor.btn_brick})
            else:
                mock_event = pygame.event.Event(event_type, {'pos': (100, 100)})
            
            map_editor.handle_event(mock_event)
            print(f"✓ 事件类型 {event_type} 处理成功")
        except Exception as e:
            print(f"❌ 事件类型 {event_type} 处理失败: {e}")
    
    # 测试窗口大小改变
    print("测试窗口大小改变...")
    try:
        map_editor.handle_window_resized(800, 600)
        print("✓ 窗口大小改变处理成功")
    except Exception as e:
        print(f"❌ 窗口大小改变处理失败: {e}")
    
    print("测试完成！")
    pygame.quit()

if __name__ == "__main__":
    test_map_editor_buttons()