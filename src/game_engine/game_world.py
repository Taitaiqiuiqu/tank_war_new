import random
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import pygame

from src.game_engine.bullet import Bullet
from src.game_engine.game_object import GameObject
from src.game_engine.tank import Tank
from src.game_engine.wall import Wall
from src.utils.resource_manager import resource_manager


class Explosion(GameObject):
    """爆炸特效，使用真实的爆炸动画帧。"""

    def __init__(self, x: int, y: int, radius: int = 16, duration: int = 18):
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

        # 游戏状态
        self.game_over = False
        self.winner: Optional[str] = None
        self.player_scores: Dict[str, int] = {}
        self.spawn_points: Dict[str, List[Tuple[int, int]]] = {"player": [], "enemy": []}
        self.debug_overlay = False

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

    def reset(self):
        """清空世界，方便重新开局或重新同步。"""
        self.game_objects.clear()
        self.tanks.clear()
        self.bullets.clear()
        self.walls.clear()
        self.explosions.clear()
        self.game_over = False
        self.winner = None

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
    ) -> Tank:
        """生成坦克并加入世界。"""
        spawn_pos = position or self._get_spawn_point(tank_type)
        tank = Tank(spawn_pos[0], spawn_pos[1], tank_type=tank_type, tank_id=tank_id, skin_id=skin_id)
        self.add_object(tank)
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
                # Don't remove walls to preserve indices for network sync
                if not isinstance(obj, Wall):
                    self._on_object_destroyed(obj)
                    self.remove_object(obj)

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

        # 5. 草地覆盖
        for wall in self.walls:
            if wall.visible and wall.wall_type == Wall.GRASS:
                wall.render(screen)

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
            self.trigger_explosion(obj.get_center(), radius=28, duration=24)
        elif isinstance(obj, Bullet):
            self.trigger_explosion(obj.get_center(), radius=12, duration=10)

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

    def _check_game_status(self):
        """根据存活坦克判断游戏胜负。"""
        if self.game_over:
            return

        player_alive = any(t.active and t.tank_type == "player" for t in self.tanks)
        enemy_alive = any(t.active and t.tank_type == "enemy" for t in self.tanks)

        if not player_alive and not enemy_alive:
            self.game_over = True
            self.winner = "draw"
        elif not player_alive:
            self.game_over = True
            self.winner = "enemy"
        elif not enemy_alive:
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