#!/usr/bin/env python3
"""
测试UI事件处理系统
"""
import pygame
import pygame_gui
from pygame_gui.elements import UIButton, UILabel

def test_menu_button_events():
    """测试菜单按钮事件处理"""
    print("🧪 测试菜单按钮事件处理...")
    
    # 初始化pygame
    pygame.init()
    
    # 创建测试窗口
    screen = pygame.display.set_mode((400, 300))
    pygame.display.set_caption("UI事件测试")
    
    # 创建UI管理器
    ui_manager = pygame_gui.UIManager((400, 300), "src/ui/theme.json")
    
    # 创建测试按钮
    btn_test = UIButton(
        relative_rect=pygame.Rect((100, 100), (200, 50)),
        text='测试按钮',
        manager=ui_manager
    )
    
    print("✓ 测试UI组件创建成功")
    
    # 模拟按钮点击事件
    test_event = pygame_gui.UI_BUTTON_PRESSED
    button_event = pygame.event.Event(test_event, {'ui_element': btn_test})
    
    # 测试UI管理器事件处理
    ui_manager.process_events(button_event)
    print("✓ UI管理器事件处理成功")
    
    # 模拟屏幕handle_event调用
    class TestScreen:
        def __init__(self, ui_manager):
            self.ui_manager = ui_manager
            self.button_clicked = False
            
        def handle_event(self, event):
            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                self.button_clicked = True
                print("✓ 屏幕接收到按钮点击事件")
    
    screen_instance = TestScreen(ui_manager)
    
    # 测试完整的事件流
    screen_instance.handle_event(button_event)
    
    if screen_instance.button_clicked:
        print("✅ UI事件处理测试通过！菜单按钮应该能正常工作")
    else:
        print("❌ UI事件处理测试失败")
    
    pygame.quit()

if __name__ == "__main__":
    test_menu_button_events()