#!/usr/bin/env python3
"""
测试地图编辑器按钮修复效果
"""
import pygame
import pygame_gui
import sys
import os

# 添加项目根目录到路径
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

def test_map_editor_button_fix():
    """测试地图编辑器按钮是否在窗口大小改变后仍然有效"""
    pygame.init()
    
    # 创建测试窗口
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("地图编辑器按钮测试")
    
    # 创建UI管理器
    from src.ui.ui_components import UIManagerWrapper
    ui_manager = UIManagerWrapper(800, 600)
    
    # 创建屏幕上下文
    from src.ui.screen_manager import ScreenContext
    context = ScreenContext()
    
    # 导入地图编辑器
    try:
        from src.ui.map_editor_screen import MapEditorScreen
        
        # 创建地图编辑器实例
        map_editor = MapEditorScreen(screen, context, ui_manager, None)
        
        print("✓ 地图编辑器实例创建成功")
        
        # 进入地图编辑器状态
        map_editor.on_enter()
        print("✓ 地图编辑器进入成功")
        
        # 检查按钮是否已创建
        if hasattr(map_editor, 'btn_brick') and map_editor.btn_brick:
            print("✓ 砖墙按钮已创建")
        else:
            print("✗ 砖墙按钮未创建")
            
        if hasattr(map_editor, 'btn_steel') and map_editor.btn_steel:
            print("✓ 钢墙按钮已创建")
        else:
            print("✗ 钢墙按钮未创建")
        
        # 模拟窗口大小改变
        print("\n--- 模拟窗口大小改变 ---")
        try:
            # 调用 _update_layout 模拟窗口大小改变（不需要参数）
            map_editor._update_layout()
            print("✓ 窗口大小调整成功")
            
            # 检查按钮在窗口调整后是否仍然存在
            if hasattr(map_editor, 'btn_brick') and map_editor.btn_brick:
                print("✓ 窗口调整后砖墙按钮仍然存在")
            else:
                print("✗ 窗口调整后砖墙按钮丢失")
                
            if hasattr(map_editor, 'btn_steel') and map_editor.btn_steel:
                print("✓ 窗口调整后钢墙按钮仍然存在")
            else:
                print("✗ 窗口调整后钢墙按钮丢失")
                
        except Exception as e:
            print(f"✗ 窗口调整失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 测试退出
        print("\n--- 测试退出清理 ---")
        try:
            map_editor.on_exit()
            print("✓ 退出清理成功")
        except Exception as e:
            print(f"✗ 退出清理失败: {e}")
            import traceback
            traceback.print_exc()
            
        print("\n=== 测试完成 ===")
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        pygame.quit()

if __name__ == "__main__":
    test_map_editor_button_fix()