import pygame
from src.config.game_config import config

class GameObject:
    """游戏对象基类，所有游戏实体的父类"""
    
    def __init__(self, x, y, width, height):
        """初始化游戏对象
        
        Args:
            x: 位置x坐标
            y: 位置y坐标
            width: 对象宽度
            height: 对象高度
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rect = pygame.Rect(x, y, width, height)
        self.visible = True
        self.active = True
        self.velocity_x = 0
        self.velocity_y = 0
        self.health = config.DEFAULT_HEALTH
    
    def update(self):
        """更新游戏对象状态"""
        # 更新位置
        self.x += self.velocity_x
        self.y += self.velocity_y
        
        # 更新矩形
        self.rect.x = self.x
        self.rect.y = self.y
    
    def render(self, screen):
        """渲染游戏对象
        
        Args:
            screen: 游戏屏幕
        """
        if self.visible:
            # 默认渲染为红色矩形，可以在子类中重写
            pygame.draw.rect(screen, (255, 0, 0), self.rect)
    
    def handle_collision(self, other):
        """处理碰撞
        
        Args:
            other: 碰撞的另一个游戏对象
        """
        pass
    
    def take_damage(self, damage):
        """受到伤害
        
        Args:
            damage: 伤害值
        """
        self.health -= damage
        if self.health <= 0:
            self.destroy()
    
    def destroy(self):
        """销毁对象"""
        self.active = False
        self.visible = False
    
    def get_center(self):
        """获取对象中心点坐标
        
        Returns:
            (x, y): 中心点坐标
        """
        return (self.x + self.width // 2, self.y + self.height // 2)
