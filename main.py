import os

# 关键修复: 启用SDL的IME候选词窗口显示
# 这会让输入法的候选词窗口正常显示
os.environ['SDL_IME_SHOW_UI'] = '1'

# 必须在导入pygame之前初始化i18n，否则pygame_gui的下拉菜单会失效
import src.ui.init_i18n

import pygame
import sys

from src.game_engine.game import GameEngine

# 初始化pygame
pygame.init()
pygame.mixer.init()

# 启用中文输入法支持 (IME - Input Method Editor)
pygame.key.set_text_input_rect(pygame.Rect(0, 0, 800, 600))
try:
    pygame.scrap.init()  # 初始化剪贴板支持
except:
    pass  # 某些系统可能不支持剪贴板

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
