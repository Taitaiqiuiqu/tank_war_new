"""
暂停菜单UI组件
"""
# 必须在导入pygame_gui之前初始化i18n
import src.ui.init_i18n

import pygame
import pygame_gui
from pygame_gui.elements import UIButton, UILabel

class PauseMenuOverlay:
    """游戏暂停菜单覆盖层"""
    
    def __init__(self, surface: pygame.Surface, ui_manager: pygame_gui.UIManager):
        self.surface = surface
        self.manager = ui_manager
        self.active = True
        
        # 创建半透明背景
        self.background = pygame.Surface(surface.get_size())
        self.background.set_alpha(180)
        self.background.fill((0, 0, 0))
        
        # 计算居中位置
        center_x = surface.get_width() // 2
        center_y = surface.get_height() // 2
        
        # 创建UI元素
        self._create_ui(center_x, center_y)
    
    def _create_ui(self, center_x: int, center_y: int):
        """创建暂停菜单UI元素"""
        btn_width = 200
        btn_height = 50
        spacing = 20
        
        # 标题
        self.title_label = UILabel(
            relative_rect=pygame.Rect((center_x - 100, center_y - 120), (200, 40)),
            text='游戏暂停',
            manager=self.manager
        )
        
        # 继续游戏按钮
        self.btn_continue = UIButton(
            relative_rect=pygame.Rect((center_x - btn_width // 2, center_y - 40), (btn_width, btn_height)),
            text='继续游戏',
            manager=self.manager
        )
        
        # 重新开始按钮
        self.btn_restart = UIButton(
            relative_rect=pygame.Rect((center_x - btn_width // 2, center_y - 40 + btn_height + spacing), (btn_width, btn_height)),
            text='重新开始',
            manager=self.manager
        )
        
        # 退出按钮
        self.btn_exit = UIButton(
            relative_rect=pygame.Rect((center_x - btn_width // 2, center_y - 40 + (btn_height + spacing) * 2), (btn_width, btn_height)),
            text='退出到主菜单',
            manager=self.manager
        )
    
    def handle_event(self, event: pygame.event.Event) -> str:
        """
        处理暂停菜单事件
        
        Returns:
            str: 'continue', 'restart', 'exit', 或 None
        """
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.btn_continue:
                return 'continue'
            elif event.ui_element == self.btn_restart:
                return 'restart'
            elif event.ui_element == self.btn_exit:
                return 'exit'
        return None
    
    def render(self):
        """渲染暂停菜单（背景遮罩）"""
        self.surface.blit(self.background, (0, 0))
    
    def cleanup(self):
        """清理UI元素"""
        if hasattr(self, 'title_label'):
            self.title_label.kill()
        if hasattr(self, 'btn_continue'):
            self.btn_continue.kill()
        if hasattr(self, 'btn_restart'):
            self.btn_restart.kill()
        if hasattr(self, 'btn_exit'):
            self.btn_exit.kill()
        self.active = False
