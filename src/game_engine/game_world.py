import random
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import pygame

from src.game_engine.bullet import Bullet
from src.game_engine.game_object import GameObject
from src.game_engine.tank import Tank
from src.game_engine.wall import Wall
from src.game_engine.wall import Wall
from src.items.prop import PropManager
from src.utils.resource_manager import resource_manager
from src.config.game_config import config


class Explosion(GameObject):
    """爆炸特效，使用真实的爆炸动画帧。"""

    def __init__(self, x: int, y: int, radius: int = None, duration: int = None):
        if radius is None:
            radius = config.EXPLOSION_DEFAULT_RADIUS
        if duration is None:
            duration = config.EXPLOSION_DEFAULT_DURATION
        super().__init__(x - radius, y - radius, radius * 2, radius * 2)
        self.radius = radius
        self.duration = duration
        self.elapsed = 0
        
        # 加载爆炸动画帧
        self.frames = resource_manager.get_explosion_frames()
        if not self.frames:
            # 备用：颜色循环
            self.frames = None
            self.color_cycle = [
                (255, 255, 128),
                (255, 200, 64),
                (255, 128, 0),
                (200, 64, 0),
            ]

    def update(self):
        super().update()
        self.elapsed += 1
        if self.elapsed >= self.duration:
            self.destroy()

    def render(self, screen):
        if not self.visible:
            return
        
        if self.frames:
            # 使用真实爆炸动画帧
            frame_index = min(int((self.elapsed / self.duration) * len(self.frames)), len(self.frames) - 1)
            frame = self.frames[frame_index]
            # 居中显示爆炸
            x = self.x + self.radius - frame.get_width() // 2
            y = self.y + self.radius - frame.get_height() // 2
            screen.blit(frame, (x, y))
        else:
            # 备用：绘制圆形爆炸
            progress = min(1.0, self.elapsed / max(1, self.duration))
            current_radius = int(self.radius * (1 + progress * 0.5))
            color_index = min(int(progress * len(self.color_cycle)), len(self.color_cycle) - 1)
            pygame.draw.circle(screen, self.color_cycle[color_index], self.get_center(), current_radius)


class Star(GameObject):
    """星星特效，在敌人生成前显示。"""

    def __init__(self, x: int, y: int, duration: int = None, callback=None):
        if duration is None:
            duration = config.STAR_EFFECT_DURATION
        super().__init__(x - 25, y - 25, config.WALL_WIDTH, config.WALL_HEIGHT)
        self.duration = duration
        self.elapsed = 0
        self.callback = callback  # 特效结束后的回调函数
        
        # 加载星星动画帧
        self.frames = resource_manager.get_star_frames()
        if not self.frames:
            # 备用：黄色闪烁圆形
            self.frames = None

    def update(self):
        super().update()
        self.elapsed += 1
        if self.elapsed >= self.duration:
            # 特效结束，调用回调
            if self.callback:
                self.callback()
            self.destroy()

    def render(self, screen):
        if not self.visible:
            return
        
        if self.frames:
            # 循环播放星星动画
            frame_index = (self.elapsed // config.STAR_ANIMATION_INTERVAL) % len(self.frames)
            frame = self.frames[frame_index]
            # 居中显示星星
            x = self.x + (self.width - frame.get_width()) // 2
            y = self.y + (self.height - frame.get_height()) // 2
            screen.blit(frame, (x, y))
        else:
            # 备用：绘制闪烁的黄色圆形
            alpha = int(128 + 127 * (self.elapsed % 10) / 10)
            surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            pygame.draw.circle(surface, (255, 255, 0, alpha), (self.width // 2, self.height // 2), 20)
            screen.blit(surface, (self.x, self.y))


class GameWorld:
    """游戏世界管理类，负责管理所有游戏对象和核心玩法逻辑。"""

    def __init__(self, width: int, height: int):
        """初始化游戏世界。

        Args:
            width: 世界宽度
            height: 世界高度
        """
        self.width = width
        self.height = height
        self.bounds = pygame.Rect(0, 0, width, height)

        # 游戏对象列表
        self.game_objects: List[GameObject] = []
        self.tanks: List[Tank] = []
        self.bullets: List[Bullet] = []
        self.walls: List[Wall] = []
        self.explosions: List[Explosion] = []
        self.stars: List[Star] = []

        # 游戏状态
        self.game_over = False
        self.winner: Optional[str] = None
        self.player_scores: Dict[str, int] = {}
        self.spawn_points: Dict[str, List[Tuple[int, int]]] = {"player": [], "enemy": []}
        self.debug_overlay = False
        
        # 坦克生命系统
        self.tank_lives: Dict[int, int] = {}  # {tank_id: remaining_lives}
        self.tank_info: Dict[int, Dict] = {}  # {tank_id: {type, skin_id, spawn_point}}
        self.tank_info: Dict[int, Dict] = {}  # {tank_id: {type, skin_id, spawn_point}}
        self.respawn_timers: Dict[int, int] = {}  # {tank_id: frames_until_respawn}

        # 道具管理器
        self.prop_manager = PropManager()
        
        # 道具效果计时器
        self.freeze_enemies_timer = 0
        self.fortify_base_timer = 0
        self.base_fortified = False
        self.original_base_walls = [] # 存储基地周围墙体的原始状态 (x, y, type)

    # ----------------------------------------------------------------------
    # 对象管理
    # ----------------------------------------------------------------------
    def add_object(self, game_object: GameObject):
        """添加游戏对象并自动分类。"""
        if game_object not in self.game_objects:
            self.game_objects.append(game_object)

        if isinstance(game_object, Tank):
            self.tanks.append(game_object)
        elif isinstance(game_object, Bullet):
            self.bullets.append(game_object)
        elif isinstance(game_object, Wall):
            self.walls.append(game_object)
        elif isinstance(game_object, Explosion):
            self.explosions.append(game_object)
        elif isinstance(game_object, Star):
            self.stars.append(game_object)

    def remove_object(self, game_object: GameObject):
        """移除游戏对象。"""
        if game_object in self.game_objects:
            self.game_objects.remove(game_object)

        if isinstance(game_object, Tank) and game_object in self.tanks:
            self.tanks.remove(game_object)
        elif isinstance(game_object, Bullet) and game_object in self.bullets:
            self.bullets.remove(game_object)
        elif isinstance(game_object, Wall) and game_object in self.walls:
            self.walls.remove(game_object)
        elif isinstance(game_object, Explosion) and game_object in self.explosions:
            self.explosions.remove(game_object)
        elif isinstance(game_object, Star) and game_object in self.stars:
            self.stars.remove(game_object)

    def reset(self):
        """清空世界，方便重新开局或重新同步。"""
        self.game_objects.clear()
        self.tanks.clear()
        self.bullets.clear()
        self.walls.clear()
        self.explosions.clear()
        self.stars.clear()
        self.game_over = False
        self.winner = None
        
        # 清理道具
        self.prop_manager.props.empty()
        
        # 重置道具效果计时器
        self.freeze_enemies_timer = 0
        self.fortify_base_timer = 0
        self.base_fortified = False
        self.original_base_walls = []
        
        # 清理坦克生命和重生计时器
        self.tank_lives.clear()
        self.tank_info.clear()
        self.respawn_timers.clear()

    def enable_debug_overlay(self, enabled: bool = True):
        """开启或关闭调试叠加层（显示对象数量等信息）。"""
        self.debug_overlay = enabled

    # ----------------------------------------------------------------------
    # 生成/加载工具
    # ----------------------------------------------------------------------
    def register_spawn_points(self, tank_type: str, points: Iterable[Tuple[int, int]]):
        """注册出生点，支持联机模式动态刷新。"""
        if tank_type not in self.spawn_points:
            raise ValueError(f"未知的坦克类型: {tank_type}")
        self.spawn_points[tank_type] = list(points)

    def spawn_tank(
        self,
        tank_type: str = "player",
        tank_id: int = 1,
        position: Optional[Tuple[int, int]] = None,
        skin_id: int = 1,
        delay_spawn: bool = False,
    ) -> Optional[Tank]:
        """生成坦克并加入世界。
        
        Args:
            delay_spawn: 如果True，延迟生成（用于显示星星特效后再生成）
        """
        spawn_pos = position or self._get_spawn_point(tank_type)
        
        # 如果需要延迟生成（用于重生），先显示星星，然后在回调中生成坦克
        if delay_spawn:
            def spawn_callback():
                self._create_tank(tank_type, tank_id, spawn_pos, skin_id)
            self.trigger_star(spawn_pos, callback=spawn_callback)
            return None
        else:
            # 直接生成（初始生成）
            return self._create_tank(tank_type, tank_id, spawn_pos, skin_id)
    
    def _create_tank(self, tank_type: str, tank_id: int, spawn_pos: Tuple[int, int], skin_id: int) -> Tank:
        """内部方法：创建并添加坦克。"""
        tank = Tank(spawn_pos[0], spawn_pos[1], tank_type=tank_type, tank_id=tank_id, skin_id=skin_id)
        # 自动激活出生护盾
        tank.activate_shield()
        self.add_object(tank)
        
        # 记录坦克信息用于重生
        if tank_id not in self.tank_lives:
            self.tank_lives[tank_id] = config.TANK_DEFAULT_LIVES  # 默认3条命
        self.tank_info[tank_id] = {
            "type": tank_type,
            "skin_id": skin_id,
            "spawn_point": spawn_pos
        }
        
        return tank

    def spawn_bullet(self, tank: Tank) -> Optional[Bullet]:
        """让指定坦克射击，并将子弹加入世界。"""
        bullet = tank.shoot()
        if bullet:
            self.add_object(bullet)
        return bullet

    def spawn_wall(self, x: int, y: int, wall_type: int = Wall.BRICK) -> Wall:
        """生成单块墙体。"""
        wall = Wall(x, y, wall_type=wall_type)
        self.add_object(wall)
        return wall

    def load_map_layout(self, layout: Sequence[Sequence[int]], tile_size: int = 50):
        """根据二维数组布局生成地形。

        Args:
            layout: 二维数组，值参考 Wall 常量（0 代表空地）
            tile_size: 每块地形的像素尺寸
        """
        for row_idx, row in enumerate(layout):
            for col_idx, cell in enumerate(row):
                if cell and cell in (Wall.BRICK, Wall.STEEL, Wall.GRASS, Wall.RIVER, Wall.BASE):
                    self.spawn_wall(col_idx * tile_size, row_idx * tile_size, wall_type=cell)

    def trigger_explosion(self, center: Tuple[int, int], radius: int = 18, duration: int = 18):
        """在指定位置创建爆炸效果。"""
        explosion = Explosion(center[0], center[1], radius=radius, duration=duration)
        self.add_object(explosion)
    
    def trigger_star(self, center: Tuple[int, int], duration: int = None, callback=None):
        """在指定位置创建星星特效。"""
        if duration is None:
            duration = config.STAR_EFFECT_DURATION
        star = Star(center[0] + 15, center[1] + 15, duration=duration, callback=callback)
        self.add_object(star)

    # ----------------------------------------------------------------------
    # 游戏循环
    # ----------------------------------------------------------------------
    def update(self):
        """更新游戏世界。"""
        for obj in list(self.game_objects):
            if obj.active:
                obj.update()
                self._check_boundaries(obj)
            else:
                # 特殊处理墙体：检查道具掉落但不移除（保留索引用于网络同步）
                if isinstance(obj, Wall):
                    # 使用标记防止重复掉落（墙体对象会保留在列表中）
                    if obj.destructible and not getattr(obj, '_prop_dropped', False):
                        # 墙体被破坏，触发道具掉落
                        if random.random() < config.WALL_DROP_RATE:
                            self.prop_manager.spawn_prop(obj.x, obj.y)
                            print(f"[Prop] 墙体被破坏，掉落道具于 ({obj.x}, {obj.y})")
                        # 标记已掉落，防止重复
                        obj._prop_dropped = True
                    # 不移除墙体对象（保留索引）
                else:
                    # 其他对象正常处理
                    self._on_object_destroyed(obj)
                    self.remove_object(obj)
        
        # 处理重生计时器
        # 处理重生计时器
        for tank_id in list(self.respawn_timers.keys()):
            self.respawn_timers[tank_id] -= 1
            if self.respawn_timers[tank_id] <= 0:
                self._respawn_tank(tank_id)
                del self.respawn_timers[tank_id]

        # 更新道具
        self.prop_manager.update()
        
        # 处理道具效果计时器
        if self.freeze_enemies_timer > 0:
            self.freeze_enemies_timer -= 1
            # 冻结所有敌人
            for tank in self.tanks:
                if tank.tank_type == "enemy":
                    tank.stop()
                    # 也可以禁止射击，但需要修改Tank类或AI
                    
        if self.fortify_base_timer > 0:
            self.fortify_base_timer -= 1
            if self.fortify_base_timer <= 0:
                self._restore_base()
        
        # 检查坦克是否在河流上（用于显示boat shield）
        for tank in self.tanks:
            if tank.active and tank.has_boat:
                # 检查坦克中心点是否在河流上
                center_x = tank.x + tank.width // 2
                center_y = tank.y + tank.height // 2
                on_river = False
                for wall in self.walls:
                    if wall.wall_type == Wall.RIVER and wall.active:
                        if wall.rect.collidepoint(center_x, center_y):
                            on_river = True
                            break
                tank.is_on_river = on_river
            else:
                tank.is_on_river = False

        self._check_collisions()
        self._check_game_status()

    def render(self, screen):
        """分层渲染世界。"""
        # 1. 除草地外的墙体
        for wall in self.walls:
            if wall.visible and wall.wall_type != Wall.GRASS:
                wall.render(screen)

        # 2. 坦克
        for tank in self.tanks:
            if tank.visible:
                tank.render(screen)

        # 3. 子弹
        for bullet in self.bullets:
            if bullet.visible:
                bullet.render(screen)

        # 4. 爆炸特效
        for explosion in self.explosions:
            if explosion.visible:
                explosion.render(screen)
        
        # 4.5. 星星特效
        for star in self.stars:
            if star.visible:
                star.render(screen)
                
        # 4.6 道具
        self.prop_manager.draw(screen)

        # 5. 草地覆盖

        # 5. 草地覆盖
        for wall in self.walls:
            if wall.visible and wall.wall_type == Wall.GRASS:
                wall.render(screen)

        # 绘制地图边界线，区分地图和黑边
        # 顶部边界：从(0, 0)到(self.width-1, 0)
        pygame.draw.line(screen, (255, 255, 255), (0, 0), (self.width - 1, 0), 2)
        # 底部边界：从(0, self.height-1)到(self.width-1, self.height-1)
        pygame.draw.line(screen, (255, 255, 255), (0, self.height - 1), (self.width - 1, self.height - 1), 2)
        # 左侧边界：从(0, 0)到(0, self.height-1)
        pygame.draw.line(screen, (255, 255, 255), (0, 0), (0, self.height - 1), 2)
        # 右侧边界：从(self.width-1, 0)到(self.width-1, self.height-1)
        pygame.draw.line(screen, (255, 255, 255), (self.width - 1, 0), (self.width - 1, self.height - 1), 2)

        if self.debug_overlay:
            self._render_debug_overlay(screen)

    # ----------------------------------------------------------------------
    # 内部工具
    # ----------------------------------------------------------------------
    def _get_spawn_point(self, tank_type: str) -> Tuple[int, int]:
        points = self.spawn_points.get(tank_type) or []
        if points:
            return random.choice(points)
        # 默认中心点，保证不会抛异常
        return self.width // 2, self.height // 2

    def _on_object_destroyed(self, obj: GameObject):
        if isinstance(obj, Tank):
            # 播放爆炸音效
            resource_manager.play_sound("boom")
            self.trigger_explosion(obj.get_center(), radius=config.TANK_EXPLOSION_RADIUS, duration=config.TANK_EXPLOSION_DURATION)
            
            # 处理坦克重生
            tank_id = obj.tank_id
            if tank_id in self.tank_lives:
                self.tank_lives[tank_id] -= 1
                if self.tank_lives[tank_id] > 0:
                    # 还有命，90帧后重生 (3秒)
                    self.respawn_timers[tank_id] = config.RESPAWN_TIME
                # 否则不重生，游戏结束由_check_game_status判断
                # 否则不重生，游戏结束由_check_game_status判断
            
            # 敌人死亡掉落道具 (25%概率)
            if obj.tank_type == "enemy" and random.random() < config.ENEMY_DROP_RATE:
                self.prop_manager.spawn_prop(obj.x, obj.y)
                
        elif isinstance(obj, Bullet):
            self.trigger_explosion(obj.get_center(), radius=config.BULLET_EXPLOSION_RADIUS, duration=config.BULLET_EXPLOSION_DURATION)
        elif isinstance(obj, Wall) and obj.destructible:
            # 墙体被破坏也有小概率掉落道具 (5%)
            if random.random() < config.WALL_DROP_RATE:
                self.prop_manager.spawn_prop(obj.x, obj.y)
    
    def _respawn_tank(self, tank_id: int):
        """重生坦克"""
        if tank_id not in self.tank_info:
            return
        
        info = self.tank_info[tank_id]
        # 重新生成坦克，延迟生成以显示星星特效
        self.spawn_tank(
            tank_type=info["type"],
            tank_id=tank_id,
            position=info["spawn_point"],
            skin_id=info["skin_id"],
            delay_spawn=True  # 先显示星星，然后生成
        )

    def _check_boundaries(self, obj: GameObject):
        """确保对象在世界范围内。"""
        if isinstance(obj, Bullet):
            if not self.bounds.colliderect(obj.rect):
                obj.destroy()
            return

        clamped_x = max(0, min(obj.x, self.width - obj.width))
        clamped_y = max(0, min(obj.y, self.height - obj.height))
        if (clamped_x, clamped_y) != (obj.x, obj.y):
            obj.x = clamped_x
            obj.y = clamped_y
            obj.rect.topleft = (obj.x, obj.y)
            if hasattr(obj, "stop"):
                obj.stop()

    def _check_collisions(self):
        """执行基础碰撞检测（坦克-坦克、坦克-墙、子弹-坦克、子弹-墙）。"""
        # 坦克 vs 坦克
        for idx, tank in enumerate(self.tanks):
            if not tank.active:
                continue
            for other in self.tanks[idx + 1 :]:
                if not other.active:
                    continue
                if tank.rect.colliderect(other.rect):
                    tank.handle_collision(other)
                    other.handle_collision(tank)

        # 坦克 vs 墙
        for tank in self.tanks:
            if not tank.active:
                continue
            for wall in self.walls:
                if not wall.active or wall.passable:
                    continue
                if tank.rect.colliderect(wall.rect):
                    tank.handle_collision(wall)
                    wall.handle_collision(tank)

        # 子弹 vs 坦克
        for bullet in list(self.bullets):
            if not bullet.active:
                continue
            for tank in self.tanks:
                if not tank.active or tank is bullet.owner:
                    continue
                if bullet.rect.colliderect(tank.rect):
                    bullet.handle_collision(tank)
                    tank.handle_collision(bullet)
                    if not bullet.active:
                        break

        # 子弹 vs 墙
        for bullet in list(self.bullets):
            if not bullet.active:
                continue
            for wall in self.walls:
                if not wall.active or wall.shoot_through:
                    continue
                if bullet.rect.colliderect(wall.rect):
                    bullet.handle_collision(wall)
                    wall.handle_collision(bullet)
                    break

                    wall.handle_collision(bullet)
                    break
        
        # 玩家 vs 道具
        for tank in self.tanks:
            if tank.tank_type == "player" and tank.active:
                hit_props = self.prop_manager.check_collision(tank.rect)
                for prop in hit_props:
                    self._apply_prop_effect(tank, prop.type)
                    # 播放吃道具音效
                    resource_manager.play_sound("get_prop") # 假设有这个音效，或者用其他代替

    def _apply_prop_effect(self, player: Tank, prop_type: int):
        """应用道具效果"""
        print(f"Player got prop: {prop_type}")
        
        if prop_type == 1: # 坦克 (加命)
            # 增加一条生命
            if player.tank_id in self.tank_lives:
                self.tank_lives[player.tank_id] += 1
                
        elif prop_type == 2: # 时钟 (时间静止)
            # 规定时间内敌方坦克静止不动
            self.freeze_enemies_timer = config.FREEZE_ENEMIES_DURATION # 10秒
            
        elif prop_type == 3: # 铁锹 (基地防御)
            # 基地周围红砖变钢墙，并修复
            self._fortify_base()
            self.fortify_base_timer = config.FORTIFY_BASE_DURATION # 20秒
            
        elif prop_type == 4: # 手榴弹 (全屏杀)
            # 玩家捡起：全场敌军坦克爆炸
            for tank in list(self.tanks):
                if tank.tank_type == "enemy" and tank.active:
                    tank.take_damage(config.GRENADE_DAMAGE) # 秒杀
                    
        elif prop_type == 5: # 五角星 (武器升级)
            # 吃一个：增加射击速度，变成两发炮弹 (Level 1)
            # 吃两个：升级到最高火力，可消灭铁块 (Level 2)
            # 吃三个：可消灭草地 (Level 3)
            player.upgrade(1)
            
        elif prop_type == 6: # 头盔 (无敌)
            # 坦克周围张开能量防壁，免疫所有攻击
            player.activate_shield() # 默认10秒
                
        elif prop_type == 7: # 手枪 (超级武器)
            # 升级到二级 (破钢)
            # 连续吃两个升级到三级 (破草)
            if player.level < 2:
                player.set_level(2)
            else:
                player.set_level(3)
                
        elif prop_type == 8: # 船 (水上行走)
            # 可过河，抵挡一次攻击
            player.enable_boat()


    def _fortify_base(self):
        """强化基地周围墙体"""
        if self.base_fortified:
            return # 已经在强化状态，重置计时器即可（在update中处理）
            
        self.base_fortified = True
        self.original_base_walls = []
        
        # 找到基地位置
        base = next((w for w in self.walls if w.wall_type == Wall.BASE), None)
        if not base:
            return
            
        base_center_x = base.x // 50
        base_center_y = base.y // 50
        
        # 基地周围 3x3 区域 (除了基地本身)
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                if dx == 0 and dy == 0:
                    continue
                
                tx = base_center_x + dx
                ty = base_center_y + dy
                
                # 边界检查：确保坐标在地图范围内
                # 动态计算行列数
                cols = self.width // 50
                rows = self.height // 50
                if tx < 0 or tx >= cols or ty < 0 or ty >= rows:
                    continue  # 跳过超出边界的格子
                
                # 查找该位置的墙
                target_wall = next((w for w in self.walls if w.x == tx * 50 and w.y == ty * 50), None)
                
                # 额外检查：确保不覆盖基地
                if target_wall and target_wall.wall_type == Wall.BASE:
                    continue
                
                if target_wall:
                    # 记录原始状态
                    self.original_base_walls.append((target_wall.x, target_wall.y, target_wall.wall_type))
                    # 移除旧墙
                    self.remove_object(target_wall)
                else:
                    # 如果是空地，也记录下来以便恢复为空地（或者我们只强化现有的墙？）
                    # 通常是把周围一圈变成钢墙，不管原来是什么
                    self.original_base_walls.append((tx * 50, ty * 50, None))
                
                # 生成钢墙
                print(f"[Fortify] 在网格 ({tx}, {ty}) 生成钢墙，像素位置: ({tx * 50}, {ty * 50})")
                self.spawn_wall(tx * 50, ty * 50, Wall.STEEL)

    def _restore_base(self):
        """恢复基地周围墙体"""
        if not self.base_fortified:
            return
            
        self.base_fortified = False
        
        # 找到基地位置
        base = next((w for w in self.walls if w.wall_type == Wall.BASE), None)
        if not base:
            return
        
        base_center_x = base.x // 50
        base_center_y = base.y // 50
        
        # 清除当前的钢墙
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                if dx == 0 and dy == 0:
                    continue
                tx = base_center_x + dx
                ty = base_center_y + dy
                
                target_wall = next((w for w in self.walls if w.x == tx * 50 and w.y == ty * 50), None)
                if target_wall and target_wall.wall_type == Wall.STEEL:
                    self.remove_object(target_wall)
        
        # 恢复原始墙体
        # 恢复原始墙体
        for x, y, w_type in self.original_base_walls:
            if w_type is not None:
                self.spawn_wall(x, y, w_type)
            # 如果是None，说明原来是空地，不需要生成墙
    
    def _check_game_status(self):
        """根据存活坦克和剩余生命值判断游戏胜负。"""
        if self.game_over:
            return

        # 检查玩家方是否还有有效生命（活跃坦克或剩余生命值）
        player_has_lives = False
        for tank in self.tanks:
            if tank.tank_type == "player":
                # 如果坦克活跃，或者有剩余生命值（正在重生），则玩家方仍有效
                if tank.active or (tank.tank_id in self.tank_lives and self.tank_lives[tank.tank_id] > 0):
                    player_has_lives = True
                    break
        
        # 检查敌人方是否还有有效生命
        enemy_has_lives = False
        for tank in self.tanks:
            if tank.tank_type == "enemy":
                # 如果坦克活跃，或者有剩余生命值（正在重生），则敌人方仍有效
                if tank.active or (tank.tank_id in self.tank_lives and self.tank_lives[tank.tank_id] > 0):
                    enemy_has_lives = True
                    break

        # 判断游戏胜负
        if not player_has_lives and not enemy_has_lives:
            self.game_over = True
            self.winner = "draw"
        elif not player_has_lives:
            self.game_over = True
            self.winner = "enemy"
        elif not enemy_has_lives:
            self.game_over = True
            self.winner = "player"

    def _render_debug_overlay(self, screen):
        """绘制调试数据，便于快速了解当前状态。"""
        font = pygame.font.SysFont("consolas", 14)
        lines = [
            f"Tanks: {len(self.tanks)}",
            f"Bullets: {len(self.bullets)}",
            f"Walls: {len(self.walls)}",
            f"Explosions: {len(self.explosions)}",
            f"GameOver: {self.game_over} Winner: {self.winner or '-'}",
        ]
        for idx, text in enumerate(lines):
            surface = font.render(text, True, (0, 255, 0))
            screen.blit(surface, (5, 5 + idx * 16))