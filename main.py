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
    
    # 检查资源是否已加载，如果没有则先显示加载界面
    from src.utils.resource_manager import resource_manager
    from src.ui.video_manager import VideoPlaybackController
    import os
    
    resource_loaded = resource_manager.is_preload_complete()
    video_loaded = True
    
    # 初始化视频管理器（如果还没有）
    if not hasattr(game.screen_manager.context, 'video_manager'):
        video_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "videos"))
        game.screen_manager.context.video_manager = VideoPlaybackController(video_dir)
    
    video_manager = game.screen_manager.context.video_manager
    video_loaded = video_manager.is_preload_complete()
    
    # 如果资源未完全加载，先显示加载界面
    if not resource_loaded or not video_loaded:
        game.screen_manager.set_state("loading")
    
    # 创建时钟对象用于帧率控制
    clock = pygame.time.Clock()
    
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
        
        # 控制帧率（使用同一个Clock对象）
        clock.tick(60)
    
    # 退出游戏
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
