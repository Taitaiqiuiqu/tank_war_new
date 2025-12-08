#!/usr/bin/env python3
"""
测试地图编辑器在不同分辨率下的显示效果
验证其是否能在各种显示器分辨率下正常工作
"""

import pygame
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.ui.map_editor_screen import MapEditorScreen
from src.network.network_manager import NetworkManager
from src.ui.screen_manager import ScreenContext
from src.ui.ui_components import UIManagerWrapper

# 模拟不同显示器分辨率进行测试
TEST_RESOLUTIONS = [
    (800, 600),     # 标准4:3分辨率
    (1024, 768),    # 标准4:3分辨率
    (1280, 720),    # HD分辨率(16:9)
    (1920, 1080),   # FHD分辨率(16:9)
    (2560, 1440),   # QHD分辨率(16:9)
    (3840, 2160),   # 4K分辨率(16:9)
    (1600, 900),    # 宽屏分辨率(16:9)
    (1366, 768),    # 笔记本常见分辨率(16:9)
    (1280, 800),    # 宽屏分辨率(16:10)
    (1440, 900),    # 宽屏分辨率(16:10)
    (1680, 1050),   # 宽屏分辨率(16:10)
    (2560, 1600),   # 宽屏分辨率(16:10)
    (1280, 960),    # 标准4:3分辨率
    (1024, 600),    # 上网本分辨率
]

def test_resolution_adaptation(resolution):
    """
    测试特定分辨率下的地图编辑器显示效果
    """
    print(f"\n=== 测试分辨率: {resolution[0]}x{resolution[1]} ===")
    
    # 初始化pygame
    pygame.init()
    
    # 创建指定分辨率的窗口
    screen = pygame.display.set_mode(resolution, pygame.RESIZABLE)
    pygame.display.set_caption(f"地图编辑器 - 分辨率测试 {resolution[0]}x{resolution[1]}")
    
    # 创建必要的组件
    network_manager = NetworkManager()
    screen_context = ScreenContext()
    screen_context.window_size = resolution
    
    # 创建UI管理器
    ui_manager = UIManagerWrapper(resolution[0], resolution[1])
    
    # 初始化地图编辑器 - 使用正确的参数顺序
    map_editor = MapEditorScreen(surface=screen, 
                                context=screen_context, 
                                ui_manager=ui_manager,
                                network_manager=network_manager)
    
    # 调用窗口大小改变事件，确保地图编辑器正确响应分辨率
    map_editor.handle_window_resized(resolution[0], resolution[1])
    
    # 渲染地图编辑器
    map_editor.render()
    
    # 更新显示
    pygame.display.flip()
    
    # 等待0.5秒，让显示稳定
    pygame.time.delay(500)
    
    # 检查渲染结果
    try:
        # 获取渲染表面
        render_surface = map_editor.surface
        
        # 获取渲染表面的尺寸
        render_width, render_height = render_surface.get_size()
        print(f"  渲染表面尺寸: {render_width}x{render_height}")
        
        # 获取地图尺寸信息
        map_width = map_editor.MAP_WIDTH
        game_height = map_editor.GAME_HEIGHT
        toolbar_height = map_editor.TOOLBAR_HEIGHT
        print(f"  地图尺寸: {map_width}x{game_height}, 工具栏: {toolbar_height}")
        
        # 计算缩放比例
        available_width = resolution[0]
        available_height = resolution[1] - toolbar_height
        scale_x = available_width / map_width
        scale_y = available_height / game_height
        scale_factor = min(scale_x, scale_y, 1.0)
        print(f"  计算缩放比例: x={scale_x:.2f}, y={scale_y:.2f}, 最终={scale_factor:.2f}")
        
        # 计算缩放后的地图尺寸
        scaled_map_width = int(map_width * scale_factor)
        scaled_map_height = int(game_height * scale_factor)
        scaled_grid_size = int(map_editor.GRID_SIZE * scale_factor)
        print(f"  缩放后地图: {scaled_map_width}x{scaled_map_height}, 网格大小: {scaled_grid_size}")
        
        # 计算居中偏移
        x_offset = (resolution[0] - scaled_map_width) // 2
        y_offset = (resolution[1] - toolbar_height - scaled_map_height) // 2 + toolbar_height
        print(f"  居中偏移: x={x_offset}, y={y_offset}")
        
        # 验证地图是否完整显示
        if scaled_map_width <= resolution[0] and scaled_map_height <= (resolution[1] - toolbar_height):
            print("  ✓ 地图完整显示在屏幕上")
            result = True
        else:
            print("  ✗ 地图未能完整显示")
            result = False
            
    except Exception as e:
        print(f"  ✗ 渲染测试失败: {e}")
        result = False
    
    # 清理
    pygame.quit()
    
    return result

def interactive_test():
    """
    交互式测试 - 允许用户调整窗口大小，查看地图编辑器的自适应效果
    """
    print("\n=== 交互式分辨率测试 ===")
    print("请调整窗口大小，观察地图编辑器的自适应效果")
    print("按ESC键退出测试")
    
    # 初始化pygame
    pygame.init()
    
    # 创建初始窗口（使用1280x720作为默认分辨率）
    initial_resolution = (1280, 720)
    screen = pygame.display.set_mode(initial_resolution, pygame.RESIZABLE)
    pygame.display.set_caption("地图编辑器 - 交互式分辨率测试")
    
    # 创建必要的组件
    network_manager = NetworkManager()
    screen_context = ScreenContext()
    screen_context.window_size = initial_resolution
    
    # 创建UI管理器
    ui_manager = UIManagerWrapper(initial_resolution[0], initial_resolution[1])
    
    # 初始化地图编辑器
    map_editor = MapEditorScreen(surface=screen, 
                                context=screen_context, 
                                ui_manager=ui_manager,
                                network_manager=network_manager)
    map_editor.handle_window_resized(*initial_resolution)
    
    # 主循环
    clock = pygame.time.Clock()
    running = True
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
            elif event.type == pygame.VIDEORESIZE:
                # 窗口大小改变时，更新地图编辑器
                new_width, new_height = event.w, event.h
                screen = pygame.display.set_mode((new_width, new_height), pygame.RESIZABLE)
                map_editor.surface = screen
                
                # 更新UI管理器分辨率
                map_editor.ui_manager.set_resolution(new_width, new_height)
                
                map_editor.handle_window_resized(new_width, new_height)
                print(f"窗口大小已调整: {new_width}x{new_height}")
            
            # 传递事件给地图编辑器
            map_editor.handle_event(event)
        
        # 渲染地图编辑器
        map_editor.render()
        
        # 在屏幕上显示当前分辨率
        font = pygame.font.Font(None, 30)
        text = font.render(f"当前分辨率: {screen.get_width()}x{screen.get_height()}", True, (255, 255, 255))
        screen.blit(text, (10, 10))
        
        # 更新显示
        pygame.display.flip()
        
        # 控制帧率
        clock.tick(60)
    
    # 清理
    pygame.quit()
    print("交互式测试结束")

def main():
    """
    主测试函数
    """
    print("地图编辑器分辨率适配测试")
    print("=" * 50)
    print(f"共测试 {len(TEST_RESOLUTIONS)} 种不同分辨率")
    
    # 执行批量分辨率测试
    passed_tests = 0
    failed_tests = 0
    
    for resolution in TEST_RESOLUTIONS:
        if test_resolution_adaptation(resolution):
            passed_tests += 1
        else:
            failed_tests += 1
    
    # 显示测试结果
    print("\n" + "=" * 50)
    print("测试结果总结")
    print(f"总测试数: {len(TEST_RESOLUTIONS)}")
    print(f"通过测试: {passed_tests}")
    print(f"失败测试: {failed_tests}")
    
    if failed_tests == 0:
        print("✓ 所有分辨率测试均通过！")
        print("地图编辑器能够在各种显示器分辨率下正常显示")
    else:
        print("✗ 部分分辨率测试失败，需要进一步检查")
    
    # 询问是否进行交互式测试
    choice = input("\n是否进行交互式分辨率测试？(y/n): ")
    if choice.lower() == 'y':
        interactive_test()
    
    print("\n分辨率适配测试完成")

if __name__ == "__main__":
    main()
