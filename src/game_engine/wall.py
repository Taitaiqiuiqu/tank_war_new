import pygame
from src.game_engine.game_object import GameObject
from src.config.game_config import config
from src.utils.resource_manager import resource_manager

class Wall(GameObject):
    """墙体类"""
    
    # 墙体类型常量
    BACKGROUND = 0  # 地图背景
    BRICK = 1    # 砖墙，可以被摧毁
    STEEL = 2    # 钢墙，不可摧毁
    GRASS = 3    # 草地，可以隐藏坦克
    RIVER = 4    # 河流，坦克无法通过
    BASE = 5     # 基地，被摧毁则游戏失败
    
    def __init__(self, x, y, wall_type=BRICK):
        """初始化墙体
        
        Args:
            x: 位置x坐标
            y: 位置y坐标
            wall_type: 墙体类型
        """
        super().__init__(x, y, config.WALL_WIDTH, config.WALL_HEIGHT)
        self.wall_type = wall_type
        self.is_wall = True
        
        # 根据类型设置属性
        self.destructible = False
        self.passable = False
        self.shoot_through = False
        self.hides_tank = False
        self.health = 0 # 默认生命值
        
        if wall_type == self.BRICK or wall_type == self.BASE:
            self.destructible = True
            self.health = config.WALL_HEALTH  # 砖墙和基地的生命值
        elif wall_type == self.GRASS:
            self.passable = True
            self.shoot_through = True
            self.hides_tank = True
        elif wall_type == self.RIVER:
            self.shoot_through = True
        
        # 为可摧毁墙体设置生命值（修复health属性未定义的bug）
        # if self.destructible: # This block is now redundant as health is set above
        #     self.health = 100  # 砖墙和基地的生命值
        
        # 加载墙体图像
        self.image = self._load_wall_image()
    
    def _load_wall_image(self):
        """加载墙体图像
        
        Returns:
            墙体图像
        """
        # 使用资源管理器加载真实墙体图片
        wall_img = resource_manager.get_wall_image(self.wall_type)
        
        if wall_img:
            return wall_img
        
        # 备用：创建占位符表面
        surface = pygame.Surface((config.WALL_WIDTH, config.WALL_HEIGHT), pygame.SRCALPHA)
        
        # 根据墙体类型设置颜色
        if self.wall_type == self.BRICK:
            color = (139, 69, 19)  # 砖红色
        elif self.wall_type == self.STEEL:
            color = (192, 192, 192)  # 钢灰色
        elif self.wall_type == self.GRASS:
            color = (0, 128, 0)  # 绿色，半透明
            surface.set_alpha(128)
        elif self.wall_type == self.RIVER:
            color = (0, 0, 255)  # 蓝色，半透明
            surface.set_alpha(128)
        elif self.wall_type == self.BASE:
            color = (255, 0, 0)  # 红色
        elif self.wall_type == self.BACKGROUND:
            color = (0, 0, 0)  # 黑色背景
        else:
            color = (128, 128, 128)  # 默认灰色
        
        pygame.draw.rect(surface, color, (0, 0, config.WALL_WIDTH, config.WALL_HEIGHT))
        
        # 为基地添加特殊标记
        if self.wall_type == self.BASE:
            pygame.draw.rect(surface, (255, 255, 255), (15, 15, 20, 20))
        
        return surface
    
    def update(self):
        """更新墙体状态"""
        super().update()
    
    def render(self, screen):
        """渲染墙体"""
        if self.visible:
            screen.blit(self.image, (self.x, self.y))
    
    def take_damage(self, damage):
        """受到伤害
        
        Args:
            damage: 伤害值
        """
        # 只有可摧毁的墙体才会受到伤害
        if self.destructible:
            self.health -= damage
            if self.health <= 0:
                # 播放砖块消除音效
                if self.wall_type == self.BRICK:
                    resource_manager.play_sound("brick_destroy")
                self.destroy()
    
    def handle_collision(self, other):
        """处理碰撞
        
        Args:
            other: 碰撞的另一个游戏对象
        """
        # 如果是坦克且墙体不可通过，则阻止坦克移动
        if hasattr(other, 'tank_type') and not self.passable:
            # 检查是否有船且是河流
            if self.wall_type == self.RIVER and getattr(other, 'has_boat', False):
                pass # 可以通过
            else:
                # 回退坦克位置
                other.x -= other.velocity_x
                other.y -= other.velocity_y
                other.rect.x = other.x
                other.rect.y = other.y
                other.stop()
        
        # 如果是子弹且墙体不可穿透，则子弹摧毁（除非墙体是草地或河流）
        elif hasattr(other, 'owner') and not self.shoot_through:
            if self.destructible:
                self.take_damage(other.damage)
            elif self.wall_type == self.STEEL and getattr(other, 'can_break_steel', False):
                # 播放钢墙销毁音效 (如果有的话，暂时用砖块的或者不播放)
                # resource_manager.play_sound("steel_destroy") 
                self.destroy()
