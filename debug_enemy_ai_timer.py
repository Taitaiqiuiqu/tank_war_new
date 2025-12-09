#!/usr/bin/env python3
"""
调试敌人AI计时器问题
"""

import os
import sys

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def debug_enemy_ai_timer():
    """调试敌人AI计时器"""
    print("=== 调试敌人AI计时器问题 ===")
    
    # 初始化pygame
    import pygame
    pygame.init()
    pygame.display.set_mode((100, 100))
    
    from src.game_engine.tank import Tank
    from src.game_engine.game_world import GameWorld
    from src.game_engine.game import EnemyAIController
    from src.config.game_config import config
    
    # 创建游戏世界
    world = GameWorld(1400, 1050)
    
    # 创建玩家坦克
    player_tank = Tank(400, 300, 'player', 1, 1)
    world.spawn_tank('player', tank_id=1, position=(400, 300))
    
    # 创建敌人坦克
    enemy_tank = Tank(100, 100, 'enemy', 1, 1)
    world.spawn_tank('enemy', tank_id=2, position=(100, 100))
    
    # 创建敌人AI控制器
    enemy_ai = EnemyAIController(2, world, 'normal')
    
    print("敌人AI初始状态:")
    print(f"  direction_timer: {enemy_ai.direction_timer}")
    print(f"  shoot_timer: {enemy_ai.shoot_timer}")
    print(f"  config: {enemy_ai.config}")
    
    print("\n=== 模拟敌人AI更新 ===")
    
    for frame in range(100):
        print(f"\n--- 帧 {frame + 1} ---")
        print(f"  更新前 direction_timer: {enemy_ai.direction_timer}")
        print(f"  更新前 shoot_timer: {enemy_ai.shoot_timer}")
        
        # 获取敌人坦克状态
        tank = next((t for t in world.tanks if t.tank_id == 2 and t.active and t.tank_type == "enemy"), None)
        if tank:
            print(f"  坦克位置: ({tank.x}, {tank.y})")
            print(f"  坦克速度: ({tank.velocity_x}, {tank.velocity_y})")
            print(f"  坦克方向: {tank.direction}")
        
        # 更新敌人AI
        enemy_ai.update()
        
        print(f"  更新后 direction_timer: {enemy_ai.direction_timer}")
        print(f"  更新后 shoot_timer: {enemy_ai.shoot_timer}")
        
        # 检查是否调用了移动
        if tank:
            if tank.velocity_x != 0 or tank.velocity_y != 0:
                print(f"  *** 坦克移动！速度: ({tank.velocity_x}, {tank.velocity_y}) ***")
            else:
                print(f"  坦克未移动")
        
        # 模拟游戏世界更新
        world.update()
        
        # 如果前10帧都没有移动，退出
        if frame >= 10:
            has_moved = any((t.velocity_x != 0 or t.velocity_y != 0) 
                           for t in world.tanks if t.tank_type == "enemy")
            if not has_moved:
                print(f"\n前{frame + 1}帧敌人坦克都没有移动！")
                break
    
    print("\n=== 分析 ===")
    print("1. 检查direction_timer是否正确递减")
    print("2. 检查direction_timer是否<=0时调用移动")
    print("3. 检查移动逻辑是否正确执行")
    
    pygame.quit()

if __name__ == "__main__":
    debug_enemy_ai_timer()