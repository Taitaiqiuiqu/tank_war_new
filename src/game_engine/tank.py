import pygame
import math
from src.game_engine.game_object import GameObject
from src.game_engine.bullet import Bullet
from src.utils.resource_manager import resource_manager

class Tank(GameObject):
    """坦克类"""
    
    # 方向常量
    UP = 0
    RIGHT = 1
    DOWN = 2
    LEFT = 3
    
    def __init__(self, x, y, tank_type='player', tank_id=1, skin_id=1):
        """初始化坦克
        
        Args:
            x: 位置x坐标
            y: 位置y坐标
            tank_type: 坦克类型 'player' 或 'enemy'
            tank_id: 坦克ID，用于区分不同的坦克(逻辑ID)
            skin_id: 皮肤ID，用于显示(视觉ID)
        """
        super().__init__(x, y, 30, 30)
        self.tank_type = tank_type
        self.tank_id = tank_id
        self.skin_id = skin_id
        self.direction = self.UP
        self.speed = 2
        self.shoot_cooldown = 0
        self.max_shoot_cooldown = 20  # 射击冷却帧数
        self.shield_active = False
        self.shield_duration = 0
        self.max_shield_duration = 60  # 护盾持续帧数
        
        # 动画相关
        self.animation_frame = 0
        self.animation_counter = 0
        self.animation_speed = 5  # 每5帧切换一次动画
        
        # 移动状态
        self.is_moving = False
        self.move_sound_playing = False
        
        # 加载坦克图像
        self.images = self._load_tank_images()
        self.current_image = self.images[self.direction][0] if self.images[self.direction] else None
    
    def _load_tank_images(self):
        """加载坦克图像
        
        Returns:
            图像字典，按方向和状态组织
        """
        # 使用资源管理器加载真实图片
        images = resource_manager.load_tank_images(self.tank_type, self.skin_id, level=0)
        
        # 如果加载失败，使用占位符
        if not images or not any(images.values()):
            print(f"警告: 无法加载坦克图片 {self.tank_type}_{self.skin_id}，使用占位符")
            images = self._create_placeholder_images()
        
        return images
    
    def _create_placeholder_images(self):
        """创建占位符图像（备用方案）"""
        images = {0: [], 1: [], 2: [], 3: []}
        color = (0, 0, 255) if self.tank_type == 'player' else (255, 0, 0)
        
        for direction in range(4):
            surface = pygame.Surface((30, 30), pygame.SRCALPHA)
            pygame.draw.rect(surface, color, (0, 0, 30, 30))
            # 绘制炮管（调整位置以适应30x30）
            if direction == self.UP:
                pygame.draw.rect(surface, (128, 128, 128), (13, 0, 4, 15))
            elif direction == self.RIGHT:
                pygame.draw.rect(surface, (128, 128, 128), (15, 13, 15, 4))
            elif direction == self.DOWN:
                pygame.draw.rect(surface, (128, 128, 128), (13, 15, 4, 15))
            elif direction == self.LEFT:
                pygame.draw.rect(surface, (128, 128, 128), (0, 13, 15, 4))
            
            images[direction] = [surface, surface.copy()]
        
        return images
    
    def update(self):
        """更新坦克状态"""
        super().update()
        
        # 更新射击冷却
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        
        # 更新护盾状态
        if self.shield_active:
            self.shield_duration -= 1
            if self.shield_duration <= 0:
                self.shield_active = False
        
        # 更新移动状态
        self.is_moving = (self.velocity_x != 0 or self.velocity_y != 0)
        
        # 更新动画帧
        if self.is_moving:
            self.animation_counter += 1
            if self.animation_counter >= self.animation_speed:
                self.animation_counter = 0
                self.animation_frame = (self.animation_frame + 1) % len(self.images[self.direction])
        else:
            self.animation_frame = 0
            self.animation_counter = 0
        
        # 更新当前图像
        if self.images[self.direction]:
            self.current_image = self.images[self.direction][self.animation_frame]
        
        # 播放移动音效
        if self.is_moving and not self.move_sound_playing:
            sound_name = "player_move" if self.tank_type == "player" else "enemy_move"
            resource_manager.play_sound(sound_name, loops=-1)
            self.move_sound_playing = True
        elif not self.is_moving and self.move_sound_playing:
            sound_name = "player_move" if self.tank_type == "player" else "enemy_move"
            resource_manager.stop_sound(sound_name)
            self.move_sound_playing = False
    
    def render(self, screen):
        """渲染坦克"""
        if self.visible and self.current_image:
            screen.blit(self.current_image, (self.x, self.y))
            
            # 渲染护盾
            if self.shield_active:
                shield_frames = resource_manager.get_shield_frames()
                if shield_frames:
                    # 使用护盾动画
                    frame_index = (pygame.time.get_ticks() // 100) % len(shield_frames)
                    shield_img = shield_frames[frame_index]
                    # 居中显示护盾
                    shield_x = self.x + (self.width - shield_img.get_width()) // 2
                    shield_y = self.y + (self.height - shield_img.get_height()) // 2
                    screen.blit(shield_img, (shield_x, shield_y))
                else:
                    # 备用：绘制半透明的护盾圆圈
                    shield_surface = pygame.Surface((self.width + 10, self.height + 10), pygame.SRCALPHA)
                    pygame.draw.circle(shield_surface, (0, 191, 255, 100), 
                                       (self.width // 2 + 5, self.height // 2 + 5), 
                                       self.width // 2 + 5)
                    screen.blit(shield_surface, (self.x - 5, self.y - 5))
    
    def move(self, direction):
        """移动坦克
        
        Args:
            direction: 移动方向
        """
        self.direction = direction
        self.velocity_x = 0
        self.velocity_y = 0
        
        if direction == self.UP:
            self.velocity_y = -self.speed
        elif direction == self.RIGHT:
            self.velocity_x = self.speed
        elif direction == self.DOWN:
            self.velocity_y = self.speed
        elif direction == self.LEFT:
            self.velocity_x = -self.speed
    
    def stop(self):
        """停止移动"""
        self.velocity_x = 0
        self.velocity_y = 0
    
    def shoot(self):
        """射击
        
        Returns:
            Bullet: 发射的子弹对象，如果冷却中则返回None
        """
        if self.shoot_cooldown > 0:
            return None
        
        # 播放射击音效
        resource_manager.play_sound("fire")
        
        # 计算子弹的初始位置（从炮管前端射出）
        bullet_x = self.x + self.width // 2 - 2
        bullet_y = self.y + self.height // 2 - 2
        
        # 根据方向调整子弹初始位置
        if self.direction == self.UP:
            bullet_y = self.y
        elif self.direction == self.RIGHT:
            bullet_x = self.x + self.width
        elif self.direction == self.DOWN:
            bullet_y = self.y + self.height
        elif self.direction == self.LEFT:
            bullet_x = self.x
        
        # 创建子弹
        bullet = Bullet(bullet_x, bullet_y, self.direction, owner=self)
        
        # 设置冷却
        self.shoot_cooldown = self.max_shoot_cooldown
        
        return bullet
    
    def activate_shield(self):
        """激活护盾"""
        self.shield_active = True
        self.shield_duration = self.max_shield_duration
    
    def handle_collision(self, other):
        """处理碰撞
        
        Args:
            other: 碰撞的另一个游戏对象
        """
        # 如果碰到墙壁或其他坦克，停止移动
        if isinstance(other, Tank) or hasattr(other, 'is_wall') and other.is_wall:
            # 回退一步，防止穿透
            self.x -= self.velocity_x
            self.y -= self.velocity_y
            self.rect.x = self.x
            self.rect.y = self.y
            self.stop()
        
        # 如果被子弹击中
        elif hasattr(other, 'owner') and other.owner != self:
            if not self.shield_active:
                self.take_damage(50)  # 假设子弹伤害为50
