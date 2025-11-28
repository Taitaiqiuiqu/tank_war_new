import pygame
from src.game_engine.game_object import GameObject
from src.utils.resource_manager import resource_manager

class Bullet(GameObject):
    """子弹类"""
    
    def __init__(self, x, y, direction, owner=None):
        """初始化子弹
        
        Args:
            x: 位置x坐标
            y: 位置y坐标
            direction: 子弹方向
            owner: 发射子弹的对象
        """
        super().__init__(x, y, 4, 4)
        self.direction = direction
        self.owner = owner  # 谁发射的子弹
        self.speed = 5
        self.damage = 50
        self.lifetime = 60  # 子弹生命周期（帧数）
        
        # 根据方向设置速度
        self.velocity_x = 0
        self.velocity_y = 0
        
        if direction == 0:  # UP
            self.velocity_y = -self.speed
        elif direction == 1:  # RIGHT
            self.velocity_x = self.speed
        elif direction == 2:  # DOWN
            self.velocity_y = self.speed
        elif direction == 3:  # LEFT
            self.velocity_x = -self.speed
        
        # 加载子弹图像
        self.image = self._load_bullet_image()
    
    def _load_bullet_image(self):
        """加载子弹图像
        
        Returns:
            子弹图像
        """
        # 使用资源管理器加载真实子弹图片
        bullet_img = resource_manager.get_bullet_image()
        
        if bullet_img:
            # 根据方向旋转子弹图片
            if self.direction == 0:  # UP
                return bullet_img
            elif self.direction == 1:  # RIGHT
                return pygame.transform.rotate(bullet_img, -90)
            elif self.direction == 2:  # DOWN
                return pygame.transform.rotate(bullet_img, 180)
            elif self.direction == 3:  # LEFT
                return pygame.transform.rotate(bullet_img, 90)
        
        # 备用：使用简单的黄色矩形
        surface = pygame.Surface((4, 4), pygame.SRCALPHA)
        pygame.draw.rect(surface, (255, 255, 0), (0, 0, 4, 4))
        return surface
    
    def update(self):
        """更新子弹状态"""
        super().update()
        
        # 减少生命周期
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.destroy()
    
    def render(self, screen):
        """渲染子弹"""
        if self.visible:
            screen.blit(self.image, (self.x, self.y))
    
    def handle_collision(self, other):
        """处理碰撞
        
        Args:
            other: 碰撞的另一个游戏对象
        """
        # 子弹不能击中发射者自己
        if other == self.owner:
            return
        
        # 如果碰撞的是坦克或墙体，子弹销毁
        if hasattr(other, 'tank_type') or hasattr(other, 'is_wall'):
            # 对目标造成伤害
            if hasattr(other, 'take_damage'):
                other.take_damage(self.damage)
            
            # 播放子弹销毁音效
            resource_manager.play_sound("bullet_destroy")
            
            # 销毁子弹
            self.destroy()
