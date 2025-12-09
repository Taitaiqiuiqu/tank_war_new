#!/usr/bin/env python3
"""
实时调试敌人坦克方向问题
"""

import os
import sys

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def debug_enemy_direction_realtime():
    """实时调试敌人方向问题"""
    print("=== 实时调试敌人坦克方向问题 ===")
    
    # 初始化pygame
    import pygame
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("敌人坦克方向调试")
    
    from src.game_engine.tank import Tank
    from src.game_engine.game_world import GameWorld
    from src.game_engine.game import EnemyAIController, GameEngine
    from src.config.game_config import config
    
    # 创建游戏引擎
    game = GameEngine()
    
    # 设置简单的游戏世界
    game.game_world.reset()
    
    # 创建玩家坦克
    player_tank = Tank(400, 300, 'player', 1, 1)
    game.game_world.spawn_tank('player', tank_id=1, position=(400, 300))
    game.player_tank = player_tank
    game.local_player_id = 1
    
    # 创建敌人坦克
    enemy_tank = Tank(100, 100, 'enemy', 1, 1)
    game.game_world.spawn_tank('enemy', tank_id=2, position=(100, 100))
    
    # 创建敌人AI控制器
    enemy_ai = EnemyAIController(2, game.game_world, 'easy')  # 使用简单难度便于观察
    
    # 添加到敌人控制器列表
    game.enemy_controllers = [enemy_ai]
    
    font = pygame.font.Font(None, 24)
    clock = pygame.time.Clock()
    
    print("开始实时调试...")
    print("观察敌人坦克的移动方向和图像方向是否一致")
    
    running = True
    frame_count = 0
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
        
        # 清屏
        screen.fill((50, 50, 50))
        
        # 更新游戏
        game._update_enemy_ai()
        game.game_world.update()
        
        # 获取敌人坦克
        enemy = next((t for t in game.game_world.tanks if t.tank_id == 2 and t.active), None)
        
        if enemy:
            # 绘制敌人坦克
            if enemy.current_image:
                screen.blit(enemy.current_image, (enemy.x, enemy.y))
            
            # 显示调试信息
            info_texts = [
                f"帧数: {frame_count}",
                f"位置: ({enemy.x}, {enemy.y})",
                f"方向: {enemy.direction} (0=上,1=右,2=下,3=左)",
                f"速度: ({enemy.velocity_x:.1f}, {enemy.velocity_y:.1f})",
                f"移动中: {enemy.is_moving}",
                f"动画帧: {enemy.animation_frame}",
            ]
            
            for i, text in enumerate(info_texts):
                text_surface = font.render(text, True, (255, 255, 255))
                screen.blit(text_surface, (10, 10 + i * 30))
            
            # 检查方向不一致
            direction_names = ["上", "右", "下", "左"]
            velocity_direction = "未知"
            
            if enemy.velocity_x > 0:
                velocity_direction = "右"
            elif enemy.velocity_x < 0:
                velocity_direction = "左"
            elif enemy.velocity_y > 0:
                velocity_direction = "下"
            elif enemy.velocity_y < 0:
                velocity_direction = "上"
            elif enemy.velocity_x == 0 and enemy.velocity_y == 0:
                velocity_direction = "静止"
            
            tank_direction = direction_names[enemy.direction] if 0 <= enemy.direction <= 3 else "未知"
            
            # 高亮显示方向不一致
            if velocity_direction != "静止" and velocity_direction != tank_direction:
                warning_text = f"方向不一致! 速度方向:{velocity_direction}, 坦克朝向:{tank_direction}"
                warning_surface = font.render(warning_text, True, (255, 0, 0))
                screen.blit(warning_surface, (10, 200))
                
                if frame_count % 30 == 0:  # 每30帧打印一次
                    print(f"[警告] {warning_text}")
        
        pygame.display.flip()
        clock.tick(60)
        frame_count += 1
    
    pygame.quit()
    print("调试结束")

if __name__ == "__main__":
    debug_enemy_direction_realtime()