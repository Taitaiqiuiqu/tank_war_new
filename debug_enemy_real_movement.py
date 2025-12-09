#!/usr/bin/env python3
"""
调试敌人坦克的实际移动行为
"""

import os
import sys

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def debug_enemy_real_movement():
    """调试敌人实际移动行为"""
    print("=== 调试敌人坦克实际移动行为 ===")
    
    # 模拟游戏更新循环
    from src.game_engine.tank import Tank
    from src.game_engine.game_world import GameWorld
    from src.game_engine.game import EnemyAIController
    import random
    
    # 初始化pygame（为了资源管理）
    import pygame
    pygame.init()
    pygame.display.set_mode((100, 100))
    
    # 创建游戏世界
    from src.config.game_config import config
    world = GameWorld(1400, 1050)
    
    # 创建玩家坦克
    player_tank = Tank(400, 300, 'player', 1, 1)
    world.spawn_tank('player', tank_id=1, position=(400, 300))
    
    # 创建敌人坦克
    enemy_tank = Tank(100, 100, 'enemy', 1, 1)
    world.spawn_tank('enemy', tank_id=2, position=(100, 100))
    
    # 创建敌人AI控制器
    enemy_ai = EnemyAIController(2, world, 'normal')
    
    print("初始状态:")
    print(f"  玩家位置: ({player_tank.x}, {player_tank.y})")
    print(f"  敌人位置: ({enemy_tank.x}, {enemy_tank.y})")
    print(f"  敌人方向: {enemy_tank.direction}")
    print(f"  敌人速度: ({enemy_tank.velocity_x}, {enemy_tank.velocity_y})")
    
    print("\n=== 模拟游戏更新循环 ===")
    
    for frame in range(10):
        print(f"\n--- 帧 {frame + 1} ---")
        
        # 1. 敌人AI更新
        print("敌人AI更新前:")
        print(f"  位置: ({enemy_tank.x}, {enemy_tank.y})")
        print(f"  方向: {enemy_tank.direction}")
        print(f"  速度: ({enemy_tank.velocity_x}, {enemy_tank.velocity_y})")
        
        enemy_ai.update()
        
        print("敌人AI更新后:")
        print(f"  位置: ({enemy_tank.x}, {enemy_tank.y})")
        print(f"  方向: {enemy_tank.direction}")
        print(f"  速度: ({enemy_tank.velocity_x}, {enemy_tank.velocity_y})")
        
        # 2. 游戏世界更新
        world.update()
        
        print("游戏世界更新后:")
        print(f"  位置: ({enemy_tank.x}, {enemy_tank.y})")
        print(f"  方向: {enemy_tank.direction}")
        print(f"  速度: ({enemy_tank.velocity_x}, {enemy_tank.velocity_y})")
        
        # 检查是否有碰撞
        if enemy_tank.velocity_x == 0 and enemy_tank.velocity_y == 0:
            print("  坦克停止移动（可能碰撞）")
    
    print("\n=== 分析 ===")
    print("1. 检查敌人AI是否正确设置了移动方向")
    print("2. 检查游戏世界更新是否影响了移动")
    print("3. 检查碰撞检测是否正确处理")
    
    pygame.quit()

if __name__ == "__main__":
    debug_enemy_real_movement()