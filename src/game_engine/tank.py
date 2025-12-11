import pygame
import math
from src.game_engine.game_object import GameObject
from src.game_engine.bullet import Bullet
from src.utils.resource_manager import resource_manager
from src.config.game_config import config

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
        super().__init__(x, y, config.TANK_WIDTH, config.TANK_HEIGHT)
        self.tank_type = tank_type
        self.tank_id = tank_id
        self.skin_id = skin_id
        self.direction = self.UP
        self.speed = config.TANK_BASE_SPEED
        self.shoot_cooldown = 0
        self.max_shoot_cooldown = config.SHOOT_COOLDOWN_BASE  # 射击冷却帧数
        self.shield_active = False
        self.shield_duration = 0
        self.max_shield_duration = config.SHIELD_DURATION  # 护盾持续帧数 (10s * 60fps)
        
        # 道具相关属性
        self.level = config.INITIAL_LEVEL
        self.has_boat = False
        self.boat_shield_active = False
        self.grass_cutter = False  # 是否能削草
        self.steel_breaker = False # 是否能破钢
        self.is_on_river = False # 是否在河上
        
        # 动画相关
        self.animation_frame = 0
        self.animation_counter = 0
        self.animation_speed = config.TANK_ANIMATION_SPEED  # 每5帧切换一次动画
        
        # 移动状态
        self.is_moving = False
        self.move_sound_playing = False
        self.idle_sound_playing = False
        self.last_hit_by = None  # 记录最后击中该坦克的对象，便于触发视频事件
        
        # 加载坦克图像
        self.images = self._load_tank_images()
        self.current_image = self.images[self.direction][0] if self.images[self.direction] else None
    
    def _load_tank_images(self):
        """加载坦克图像
        
        Returns:
            图像字典，按方向和状态组织
        """
        # 使用资源管理器加载真实图片
        images = resource_manager.load_tank_images(self.tank_type, self.skin_id, level=self.level)
        
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
            surface = pygame.Surface((config.TANK_WIDTH, config.TANK_HEIGHT), pygame.SRCALPHA)
            pygame.draw.rect(surface, color, (0, 0, config.TANK_WIDTH, config.TANK_HEIGHT))
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
            # 停止待机音效
            if self.tank_type == "player" and self.idle_sound_playing:
                resource_manager.stop_sound("player_idle")
                self.idle_sound_playing = False
            
            sound_name = "player_move" if self.tank_type == "player" else "enemy_move"
            resource_manager.play_sound(sound_name, loops=-1)
            self.move_sound_playing = True
        elif not self.is_moving and self.move_sound_playing:
            sound_name = "player_move" if self.tank_type == "player" else "enemy_move"
            resource_manager.stop_sound(sound_name)
            self.move_sound_playing = False
        
        # 播放待机音效（仅玩家坦克）
        if self.tank_type == "player" and not self.is_moving and not self.idle_sound_playing:
            resource_manager.play_sound("player_idle", loops=-1)
            self.idle_sound_playing = True
        elif self.tank_type == "player" and self.is_moving and self.idle_sound_playing:
            resource_manager.stop_sound("player_idle")
            self.idle_sound_playing = False
    
    def render(self, screen):
        """渲染坦克"""
        if self.visible and self.current_image:
            screen.blit(self.current_image, (self.x, self.y))
            
            # 渲染护盾
            if self.shield_active:
                shield_frames = resource_manager.get_shield_frames()
                if shield_frames:
                    # 使用护盾动画
                    frame_index = (pygame.time.get_ticks() // config.SHIELD_ANIMATION_INTERVAL) % len(shield_frames)
                    shield_img = shield_frames[frame_index]
                    # 护盾与坦克大小一致，直接覆盖在坦克上
                    screen.blit(shield_img, (self.x, self.y))
                else:
                    # 备用：绘制半透明的护盾圆圈
                    shield_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                    pygame.draw.circle(shield_surface, (0, 191, 255, 128), 
                                       (self.width // 2, self.height // 2), 
                                       self.width // 2)
                    screen.blit(shield_surface, (self.x, self.y))
            
            # 渲染河流护盾 (仅当有船且在水中时)
            if self.has_boat and self.is_on_river:
                 river_shield_img = resource_manager.get_river_shield_image()
                 if river_shield_img:
                     screen.blit(river_shield_img, (self.x, self.y))
    
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
        bullet_x = self.x + self.width // 2 - config.BULLET_SPAWN_OFFSET
        bullet_y = self.y + self.height // 2 - config.BULLET_SPAWN_OFFSET
        
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
        bullets = []
        bullet = Bullet(bullet_x, bullet_y, self.direction, owner=self)
        bullets.append(bullet)

        # 等级1以上：双发子弹 (稍微偏移或连发，这里简单实现为第二发)
        if self.level >= config.LEVEL_1_THRESHOLD and self.tank_type == 'player':
             # 简单的双发实现：稍微延迟或偏移
             # 这里我们暂时只发一发，因为双发需要更复杂的子弹管理或连发逻辑
             # 或者我们可以提高射速来模拟火力增强
             self.max_shoot_cooldown = config.SHOOT_COOLDOWN_UPGRADED # 射速提升
        
        if self.level >= config.LEVEL_2_THRESHOLD:
            bullet.can_break_steel = True
        
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
        if isinstance(other, Tank) or (hasattr(other, 'is_wall') and other.is_wall):
            # 如果是墙体，检查是否是河流且有船
            if hasattr(other, 'wall_type') and other.wall_type == 4 and self.has_boat:
                # 允许通过河流
                return

            # 停止移动（预测性检测已阻止移动，但如果已经移动了需要回退）
            # 检查当前位置是否已经穿透
            if hasattr(other, 'rect'):
                if self.rect.colliderect(other.rect):
                    # 已经穿透，需要回退
                    self.x -= self.velocity_x
                    self.y -= self.velocity_y
                    self.rect.x = self.x
                    self.rect.y = self.y
            self.stop()
        
        # 如果被子弹击中
        elif hasattr(other, 'owner') and other.owner != self:
            if not self.shield_active:
                self.take_damage(config.BULLET_DAMAGE)  # 假设子弹伤害为50

    def upgrade(self, amount=1):
        """升级坦克"""
        if self.tank_type != 'player':
            return
            
        self.level += amount
        if self.level > config.MAX_LEVEL:
            self.level = config.MAX_LEVEL
            
        # 应用等级效果（确保初始等级时使用基础速度）
        if self.level >= config.LEVEL_1_THRESHOLD:
            self.speed = config.TANK_UPGRADED_SPEED # 速度提升
        else:
            # 初始等级（0）时使用基础速度
            self.speed = config.TANK_BASE_SPEED
        if self.level >= config.LEVEL_2_THRESHOLD:
            self.steel_breaker = True
        if self.level >= config.LEVEL_3_THRESHOLD:
            self.grass_cutter = True
            
        # 重新加载图片
        self.images = self._load_tank_images()
        
    def set_level(self, target_level):
        """直接设置等级"""
        if self.tank_type != 'player':
            return
        
        diff = target_level - self.level
        if diff > 0:
            self.upgrade(diff)

    def enable_boat(self):
        """启用船道具"""
        self.has_boat = True
        self.boat_shield_active = True
        # 重新加载图片可能会有船的特效？目前需求是 river_shield 独立显示
        
    def disable_boat(self):
        self.has_boat = False
        self.boat_shield_active = False
