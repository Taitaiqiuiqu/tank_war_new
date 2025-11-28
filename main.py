import pygame
import sys
from src.game_engine.game import GameEngine

# 初始化pygame
pygame.init()
pygame.mixer.init()

def main():
    """游戏主入口"""
    # 创建游戏引擎实例
    game = GameEngine()
    
    # 游戏主循环
    running = True
    while running:
        # 处理事件
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            game.handle_event(event)
        
        # 更新游戏状态
        game.update()
        
        # 渲染游戏画面
        game.render()
        
        # 控制帧率
        pygame.time.Clock().tick(60)
    
    # 退出游戏
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
