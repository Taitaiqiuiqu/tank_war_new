#!/usr/bin/env python3
"""
简单调试敌人AI移动逻辑
"""

import os
import sys

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def debug_enemy_simple():
    """简单调试敌人AI"""
    print("=== 简单调试敌人AI移动逻辑 ===")
    
    # 初始化pygame
    import pygame
    pygame.init()
    pygame.display.set_mode((100, 100))
    
    from src.game_engine.tank import Tank
    from src.game_engine.game_world import GameWorld
    from src.game_engine.game import EnemyAIController
    
    # 创建游戏世界
    world = GameWorld(1400, 1050)
    
    # 创建玩家坦克
    player_tank = Tank(400, 300, 'player', 1, 1)
    world.spawn_tank('player', tank_id=1, position=(400, 300))
    
    # 创建敌人坦克
    enemy_tank = Tank(100, 100, 'enemy', 1, 1)
    world.spawn_tank('enemy', tank_id=2, position=(100, 100))
    
    # 创建敌人AI控制器
    enemy_ai = EnemyAIController(2, world, 'easy')  # 使用简单难度
    
    print("测试简单难度的敌人AI（随机移动）")
    
    # 直接测试移动逻辑
    tank = next((t for t in world.tanks if t.tank_id == 2 and t.active and t.tank_type == "enemy"), None)
    if tank:
        print(f"初始坦克状态:")
        print(f"  位置: ({tank.x}, {tank.y})")
        print(f"  方向: {tank.direction}")
        print(f"  速度: ({tank.velocity_x}, {tank.velocity_y})")
        
        # 直接调用移动方法
        print("\n直接调用 tank.move(Tank.RIGHT):")
        tank.move(Tank.RIGHT)
        print(f"  方向: {tank.direction}")
        print(f"  速度: ({tank.velocity_x}, {tank.velocity_y})")
        
        # 测试敌人AI的随机移动
        print("\n测试敌人AI的随机移动:")
        for i in range(5):
            enemy_ai._move_random(tank)
            print(f"  第{i+1}次 - 方向: {tank.direction}, 速度: ({tank.velocity_x}, {tank.velocity_y})")
    
    print("\n=== 测试敌人AI更新 ===")
    
    # 重置敌人AI计时器为0，强制立即移动
    enemy_ai.direction_timer = 0
    enemy_ai.shoot_timer = 0
    
    print("重置计时器为0，调用update():")
    enemy_ai.update()
    
    if tank:
        print(f"  方向: {tank.direction}")
        print(f"  速度: ({tank.velocity_x}, {tank.velocity_y})")
    
    pygame.quit()

if __name__ == "__main__":
    debug_enemy_simple()