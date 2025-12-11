import os
import heapq
import random
from typing import List, Optional, Tuple
import ctypes

import pygame

from src.game_engine.game_world import GameWorld
from src.game_engine.tank import Tank
from src.game_engine.wall import Wall
from src.network.network_manager import NetworkManager
from src.state_sync.state_manager import StateManager
from src.ui.screen_manager import ScreenManager
from src.ui.pause_menu import PauseMenuOverlay
from src.ui.video_manager import VideoPlaybackController
from src.utils.resource_manager import resource_manager
from src.utils.map_loader import map_loader
from src.game_engine.window_manager import WindowManager
from src.config.game_config import config


class EnemyAIController:
    """增强型敌人AI：支持4个难度等级"""

    def __init__(self, tank_id: int, world: GameWorld, difficulty: str = "normal", player_weight: float = 1.0, base_weight: float = 1.0):
        from src.game_engine.ai_config import get_difficulty_config
        import random
        
        self.tank_id = tank_id
        self.world = world
        self.difficulty = difficulty
        self.config = get_difficulty_config(difficulty)
        self.player_weight = player_weight
        self.base_weight = base_weight
        
        # 初始化计时器为随机值，确保敌人立即开始移动
        min_interval, max_interval = self.config["direction_interval"]
        self.direction_timer = random.randint(min_interval, max_interval)
        
        min_interval, max_interval = self.config["shoot_interval"]
        self.shoot_timer = random.randint(min_interval, max_interval)
        
        self.role = None  # For Hell difficulty team coordination
        self.turn_timer = 0  # 方向调转计时器
        self.target_direction = None  # 目标方向
        # 防止卡住：记录上一次位置与卡住帧计数
        self._last_pos = None
        self._stuck_frames = 0
        # 威胁感知与状态
        self.threat_scores = {}  # tank_id -> score
        self._state = "attack"   # attack / defend / retreat / flank
        self._state_timer = 0

    def _turn_to_direction(self, tank, target_direction):
        """
        将坦克调转至目标方向
        
        Args:
            tank: 坦克实例
            target_direction: 目标方向
            
        Returns:
            bool: 是否已完成调转
        """
        if tank.direction == target_direction:
            # 方向一致，无需调转
            return True
        
        if self.turn_timer <= 0:
            # 开始调转方向
            self.target_direction = target_direction
            self.turn_timer = 3  # 设置调转时间（3帧）
            return False
        else:
            # 正在调转中
            self.turn_timer -= 1
            if self.turn_timer <= 0:
                # 调转完成，保持方向与移动的一致性
                return True
            return False

    def update(self):
        # 检查敌人是否被冻结
        if self.world.freeze_enemies_timer > 0:
            return
        
        # 动态查找坦克实例 - 只控制敌人坦克
        tank = next((t for t in self.world.tanks if t.tank_id == self.tank_id and t.active and t.tank_type == "enemy"), None)
        if not tank:
            return

        # 更新威胁感知（最近伤害来源，衰减）
        self._update_threat(tank)
        # 基于状态机调整行为
        self._update_state(tank)

        # 如果长时间未移动，强制换向避免卡住
        current_pos = (tank.x, tank.y)
        if self._last_pos is None:
            self._last_pos = current_pos
        moved_dist = ( (current_pos[0] - self._last_pos[0]) ** 2 + (current_pos[1] - self._last_pos[1]) ** 2 ) ** 0.5
        if moved_dist < 1:
            self._stuck_frames += 1
        else:
            self._stuck_frames = 0
            self._last_pos = current_pos
        if self._stuck_frames > 30:  # 约0.5秒@60fps
            self._force_unstuck(tank)
            self._stuck_frames = 0
            # 重新计时，避免立即再次卡住
            min_interval, max_interval = self.config["direction_interval"]
            self.direction_timer = random.randint(min_interval, max_interval)
            return

        # 子弹威胁优先级高：发现必躲场景立即闪避
        if self.config.get("dodge") and self._should_dodge(tank):
            self._dodge_bullet(tank)
            return

        # 只在速度配置改变时应用速度（避免每次更新都重置）
        if tank.speed != self.config["speed"]:
            tank.speed = self.config["speed"]

        # Update timers
        self.direction_timer -= 1
        self.shoot_timer -= 1
        
        # Movement logic based on difficulty - 只在计时器到0时执行
        if self.direction_timer <= 0:
            self._update_movement(tank)
            min_interval, max_interval = self.config["direction_interval"]
            self.direction_timer = random.randint(min_interval, max_interval)
        
        # Shooting logic - 只在计时器到0时执行
        if self.shoot_timer <= 0:
            self._update_shooting(tank)
            min_interval, max_interval = self.config["shoot_interval"]
            self.shoot_timer = random.randint(min_interval, max_interval)
    
    def _update_movement(self, tank):
        """更新移动逻辑"""
        if self.config["tracking"]:
            self._move_with_tracking(tank)
        else:
            self._move_random(tank)
    
    def _move_random(self, tank):
        """随机移动（简单难度）"""
        direction = random.choice([Tank.UP, Tank.RIGHT, Tank.DOWN, Tank.LEFT])
        
        # 先调转方向，再移动
        if self._turn_to_direction(tank, direction):
            tank.move(direction)        # move方法内部已设置方向

    def _force_unstuck(self, tank):
        """卡住时强制换一个新方向移动。"""
        # 优先尝试远离边界/墙体
        directions = [Tank.UP, Tank.RIGHT, Tank.DOWN, Tank.LEFT]
        scores = {}
        for d in directions:
            dx = 0
            dy = 0
            if d == Tank.UP:
                dy = -1
            elif d == Tank.DOWN:
                dy = 1
            elif d == Tank.LEFT:
                dx = -1
            elif d == Tank.RIGHT:
                dx = 1
            # 边界惩罚：越靠近边界分越低
            nx = tank.x + dx * config.GRID_SIZE
            ny = tank.y + dy * config.GRID_SIZE
            border_penalty = (
                (0 - nx if nx < 0 else 0)
                + (nx - (self.world.width - tank.width) if nx > self.world.width - tank.width else 0)
                + (0 - ny if ny < 0 else 0)
                + (ny - (self.world.height - tank.height) if ny > self.world.height - tank.height else 0)
            )
            wall_penalty = 0
            for w in self.world.walls:
                if not w.active or getattr(w, "passable", False):
                    continue
                if abs((w.x - nx)) < config.GRID_SIZE and abs((w.y - ny)) < config.GRID_SIZE:
                    wall_penalty += 2
            scores[d] = -border_penalty - wall_penalty
        best_dir = max(scores, key=scores.get)
        if self._turn_to_direction(tank, best_dir):
            tank.move(best_dir)
    
    def _move_with_tracking(self, tank):
        """带追踪的移动（普通+难度）"""
        # 1. 选择目标（考虑威胁与状态）
        base = self._find_player_base()
        target, target_is_base = self._select_target(tank, base)
        if not target:
            self._move_random(tank)
            return
        
        # Calculate distance
        dx = target.x - tank.x
        dy = target.y - tank.y
        distance = (dx**2 + dy**2)**0.5
        
        # Check if should track based on probability
        tracking_prob = self.config.get("tracking_prob", 0.7)
        if not target_is_base and random.random() > tracking_prob:
            self._move_random(tank)
            return
        
        # 基地相关移动策略
        if target_is_base:
            if distance > 200:
                direction = self._choose_axis_direction(dx, dy, tank.direction)
                if self._turn_to_direction(tank, direction):
                    tank.move(direction)
            # 近距离攻基：若被挡，专注拆墙
            if not self._is_shooting_path_clear(tank, base):
                wall_blocker = self._find_first_blocker_to(base)
                if wall_blocker and getattr(wall_blocker, "destructible", False):
                    self._attack_blocker(tank, wall_blocker)
            return
        
        # 玩家坦克相关移动策略
        # 状态决策：撤退/侧翼/进攻
        if self._state == "retreat":
            direction = self._choose_axis_direction(-dx, -dy, tank.direction)
            if self._turn_to_direction(tank, direction):
                tank.move(direction)
            return

        # Safe distance logic (Hard+) 或防守状态保持距离
        safe_distance = self.config.get("safe_distance", 0)
        desired_distance = safe_distance if self._state in ("defend", "flank") else safe_distance
        if desired_distance > 0 and distance < desired_distance:
            direction = self._choose_axis_direction(-dx, -dy, tank.direction)
            if self._turn_to_direction(tank, direction):
                tank.move(direction)
            return

        # 侧翼：为目标制造横向偏移
        if self._state == "flank":
            flank_offset = 120
            if abs(dx) > abs(dy):
                target_x = target.x
                target_y = target.y + (flank_offset if random.random() < 0.5 else -flank_offset)
            else:
                target_x = target.x + (flank_offset if random.random() < 0.5 else -flank_offset)
                target_y = target.y
            dx = target_x - tank.x
            dy = target_y - tank.y

        # 路径规划（简单网格 BFS）优先
        next_dir = self._next_direction_via_path(tank, target)
        if next_dir is not None:
            if self._turn_to_direction(tank, next_dir):
                tank.move(next_dir)
            return
        
        # Dodge bullets (Normal+) 已在 update 中提前处理
        
        # Move towards player - 修复方向判断，增加稳定性
        direction = self._choose_axis_direction(dx, dy, tank.direction)
        if self._turn_to_direction(tank, direction):
            tank.move(direction)        # move方法内部已设置方向
    
    def _update_shooting(self, tank):
        """更新射击逻辑"""
        if self.config.get("prediction"):
            self._shoot_with_prediction(tank)
        else:
            # 不使用预判时，优先考虑基地作为目标
            target = self._select_target_player(tank)
            if target:
                # 检查目标是否在射击范围内
                if self.difficulty in ["easy"] or self._is_target_in_firing_arc(tank, target):
                    self.world.spawn_bullet(tank)
    
    def _shoot_with_prediction(self, tank):
        """带预判的射击"""
        # 使用新的目标选择系统（可能返回玩家坦克或基地）
        target = self._select_target_player(tank)
        if not target:
            self.world.spawn_bullet(tank)
            return
        # 避免持续在卡位时空放，若多次失败可尝试换位
        
        # 检查目标类型
        is_base = hasattr(target, "wall_type") and target.wall_type == Wall.BASE
        
        # 根据目标类型和难度调整预判策略
        if is_base:
            # 基地是静止目标，不需要预判，直接瞄准
            pred_x = target.x
            pred_y = target.y
        else:
            # 玩家坦克是移动目标，需要预判
            if self.difficulty == "easy":
                # 简单难度使用基本预判
                prediction_frames = self.config.get("prediction_frames", 5)
                pred_x = target.x + target.velocity_x * prediction_frames
                pred_y = target.y + target.velocity_y * prediction_frames
            elif self.difficulty == "normal":
                # 普通难度考虑移动方向
                prediction_frames = self.config.get("prediction_frames", 10)
                pred_x = target.x + target.velocity_x * prediction_frames
                pred_y = target.y + target.velocity_y * prediction_frames
            else:
                # 困难和地狱难度使用高级预判
                # 计算子弹飞行时间（基于距离和子弹速度）
                dx = target.x - tank.x
                dy = target.y - tank.y
                distance = (dx**2 + dy**2)**0.5
                
                # 子弹速度（假设为固定值，可从config获取）
                bullet_speed = getattr(config, "BULLET_SPEED", 6)
                flight_time_frames = max(5, int(distance / bullet_speed))  # 至少5帧
                
                # 基础预判：考虑当前速度
                pred_x = target.x + target.velocity_x * flight_time_frames
                pred_y = target.y + target.velocity_y * flight_time_frames
                
                # 高级预判：考虑加速度和移动趋势
                if self.difficulty == "hell":
                    # 尝试预测玩家可能的移动方向变化
                    # 检查玩家是否在直线移动
                    if abs(target.velocity_x) > abs(target.velocity_y):
                        # 水平移动，可能继续水平方向
                        pred_x += target.velocity_x * 2  # 增加额外预判
                    else:
                        # 垂直移动，可能继续垂直方向
                        pred_y += target.velocity_y * 2  # 增加额外预判
        
        # Determine best shooting direction - 修复预判方向，增加稳定性
        dx = pred_x - tank.x
        dy = pred_y - tank.y
        
        # Choose direction closest to predicted position with stability
        if abs(dx) > abs(dy) + 20:  # 增加20像素的缓冲，避免频繁切换
            # 预测位置在右边(dx>0)，向右射击；在左边(dx<0)，向左射击
            target_dir = Tank.RIGHT if dx > 0 else Tank.LEFT
        elif abs(dy) > abs(dx) + 20:  # 增加20像素的缓冲
            # 预测位置在下边(dy>0)，向下射击；在上边(dy<0)，向上射击
            target_dir = Tank.DOWN if dy > 0 else Tank.UP
        else:
            # 当dx和dy接近时，优先保持当前射击方向
            if tank.direction in [Tank.LEFT, Tank.RIGHT, Tank.UP, Tank.DOWN]:
                target_dir = tank.direction  # 保持当前方向
            else:
                # 默认选择水平方向
                target_dir = Tank.RIGHT if dx > 0 else Tank.LEFT
        
        # 先调转方向，再射击
        if self._turn_to_direction(tank, target_dir):
            # 检查射击路径是否清晰（仅在困难和地狱难度使用）
            if self.difficulty in ["easy", "normal"] or self._is_shooting_path_clear(tank, target):
                # Aim and shoot - 确保坦克方向和射击方向一致
                self.world.spawn_bullet(tank)
    
    def _is_shooting_path_clear(self, tank, target):
        """
        检查射击路径是否被障碍物阻挡且目标在有效射击范围内
        
        Args:
            tank: 射击的坦克
            target: 目标玩家
            
        Returns:
            bool: 路径是否清晰且目标在有效射击范围内
        """
        # 1. 首先检查目标是否在坦克的有效射击角度内（避免死角射击）
        if not self._is_target_in_firing_arc(tank, target):
            return False
        
        # 2. 检查直线上是否有墙体
        # 获取所有可阻挡子弹的墙体
        obstacles = [wall for wall in self.world.walls if wall.active and not wall.shoot_through]
        
        # 获取坦克和目标的中心位置
        tank_center = (tank.x + tank.width // 2, tank.y + tank.height // 2)
        target_center = (target.x + target.width // 2, target.y + target.height // 2)
        
        # 3. 检查是否有障碍物在射击路径上
        for obstacle in obstacles:
            if obstacle is target:
                continue
            # 检查障碍物矩形是否与射击线段相交
            if self._line_rect_intersection(tank_center, target_center, obstacle.rect):
                return False
        
        # 4. 检查其他坦克是否阻挡了射击路径
        for other_tank in self.world.tanks:
            if other_tank is tank or other_tank is target or not other_tank.active:
                continue
            
            if self._line_rect_intersection(tank_center, target_center, other_tank.rect):
                return False
        
        return True
        
    def _is_target_in_firing_arc(self, tank, target):
        """
        检查目标是否在坦克的有效射击角度内（避免射击死角）
        
        Args:
            tank: 射击的坦克
            target: 目标（可以是坦克或基地）
            
        Returns:
            bool: 目标是否在有效射击范围内
        """
        # 获取坦克和目标的中心位置
        tank_center = (tank.x + tank.width // 2, tank.y + tank.height // 2)
        target_center = (target.x + target.width // 2, target.y + target.height // 2)
        
        # 计算目标相对于坦克的方向向量
        dx = target_center[0] - tank_center[0]
        dy = target_center[1] - tank_center[1]
        
        # 根据难度调整射击精度阈值
        if self.difficulty in ["easy", "normal"]:
            # 简单和普通难度：较宽松的射击角度
            threshold = tank.width  # 左右/上下偏差不超过坦克宽度
        else:
            # 困难和地狱难度：更精确的射击角度
            threshold = tank.width * 0.7  # 偏差不超过坦克宽度的70%
        
        # 根据坦克当前朝向检查目标是否在正前方
        if tank.direction == Tank.UP:
            # 向上射击：目标应该在坦克上方，且左右偏差不超过阈值
            return dy < 0 and abs(dx) < threshold
        elif tank.direction == Tank.DOWN:
            # 向下射击：目标应该在坦克下方，且左右偏差不超过阈值
            return dy > 0 and abs(dx) < threshold
        elif tank.direction == Tank.LEFT:
            # 向左射击：目标应该在坦克左侧，且上下偏差不超过阈值
            return dx < 0 and abs(dy) < threshold
        elif tank.direction == Tank.RIGHT:
            # 向右射击：目标应该在坦克右侧，且上下偏差不超过阈值
            return dx > 0 and abs(dy) < threshold
        
        return False
        
    def _line_rect_intersection(self, p1, p2, rect):
        """
        检查线段p1-p2是否与矩形rect相交
        
        Args:
            p1: 线段起点(x, y)
            p2: 线段终点(x, y)
            rect: pygame.Rect对象
            
        Returns:
            bool: 是否相交
        """
        # 矩形的四条边
        rect_edges = [
            ((rect.left, rect.top), (rect.right, rect.top)),  # 上边
            ((rect.right, rect.top), (rect.right, rect.bottom)),  # 右边
            ((rect.right, rect.bottom), (rect.left, rect.bottom)),  # 下边
            ((rect.left, rect.bottom), (rect.left, rect.top))  # 左边
        ]
        
        # 检查线段是否与矩形的任何一条边相交
        for edge_p1, edge_p2 in rect_edges:
            if self._line_intersection(p1, p2, edge_p1, edge_p2):
                return True
        
        # 检查线段是否完全在矩形内部
        if rect.collidepoint(p1) and rect.collidepoint(p2):
            return True
        
        return False
        
    def _line_intersection(self, p1, p2, p3, p4):
        """
        检查线段p1-p2和线段p3-p4是否相交
        使用向量叉积法
        
        Args:
            p1, p2: 第一条线段的端点
            p3, p4: 第二条线段的端点
            
        Returns:
            bool: 是否相交
        """
        # 计算叉积
        def cross(o, a, b):
            return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
        
        # 计算各个点的叉积
        d1 = cross(p3, p4, p1)
        d2 = cross(p3, p4, p2)
        d3 = cross(p1, p2, p3)
        d4 = cross(p1, p2, p4)
        
        # 线段相交的条件
        if ((d1 > 0 and d2 < 0) or (d1 < 0 and d2 > 0)) and ((d3 > 0 and d4 < 0) or (d3 < 0 and d4 > 0)):
            return True
        
        # 检查端点是否在另一条线段上
        if d1 == 0 and self._is_point_on_segment(p3, p4, p1):
            return True
        if d2 == 0 and self._is_point_on_segment(p3, p4, p2):
            return True
        if d3 == 0 and self._is_point_on_segment(p1, p2, p3):
            return True
        if d4 == 0 and self._is_point_on_segment(p1, p2, p4):
            return True
        
        return False
        
    def _is_point_on_segment(self, p1, p2, p):
        """
        检查点p是否在线段p1-p2上
        
        Args:
            p1, p2: 线段端点
            p: 要检查的点
            
        Returns:
            bool: 是否在线段上
        """
        return (min(p1[0], p2[0]) <= p[0] <= max(p1[0], p2[0]) and
                min(p1[1], p2[1]) <= p[1] <= max(p1[1], p2[1]))
    
    def _find_nearest_player(self, tank):
        """查找最近的玩家（兼容旧代码）"""
        players = [t for t in self.world.tanks if t.active and t.tank_type == "player"]
        if not players:
            return None
        
        min_dist = float('inf')
        nearest = None
        for player in players:
            dist = (player.x - tank.x)**2 + (player.y - tank.y)**2
            if dist < min_dist:
                min_dist = dist
                nearest = player
        return nearest
        
    def _find_player_base(self):
        """查找玩家基地（唯一的BASE类型墙体）"""
        bases = [wall for wall in self.world.walls if wall.active and wall.wall_type == Wall.BASE]
        return bases[0] if bases else None

    def _select_target_player(self, tank):
        """选择最优目标，基于多种因素
        
        优先级因素（从高到低）：
        1. 玩家基地（最高优先级目标）
        2. 玩家坦克
            - 距离（基础因素）
            - 玩家是否正在射击（高优先级）
            - 玩家是否有护盾（低优先级）
            - 玩家剩余生命值（低生命值优先）
            - 玩家是否静止（静止目标更容易命中）
        """
        # 1. 首先检查是否有玩家基地可以攻击
        base = self._find_player_base()
        if base:
            # 计算到基地的距离
            dx = base.x - tank.x
            dy = base.y - tank.y
            base_dist = (dx**2 + dy**2)**0.5
            
            # 根据难度决定是否优先攻击基地
            if self.difficulty in ["hard", "hell"]:
                # 困难和地狱难度优先攻击基地
                # 检查是否可以直接射击基地
                if self._is_shooting_path_clear(tank, base):
                    return base
            elif self.difficulty == "normal":
                # 普通难度：如果基地距离较近且可以直接射击，则优先攻击
                if base_dist < 300 and self._is_shooting_path_clear(tank, base):
                    return base
        
        # 2. 如果没有合适的基地目标，则选择玩家坦克
        players = [t for t in self.world.tanks if t.active and t.tank_type == "player"]
        if not players:
            # 如果没有玩家坦克，返回基地作为目标
            return base
            
        # 距离+威胁+护盾加权
        def _score(p):
            dist2 = (p.x - tank.x) ** 2 + (p.y - tank.y) ** 2
            threat = self.threat_scores.get(p.tank_id, 0)
            has_shield = getattr(p, "shield_active", False)
            shield_penalty = 40000 if has_shield else 0
            return dist2 - threat * 5000 + shield_penalty

        best_player = min(players, key=_score)

        # 3. 比较攻击玩家和攻击基地的优先级（基地仍有较高基础权重）
        if base and best_player:
            player_dist = ((best_player.x - tank.x) ** 2 + (best_player.y - tank.y) ** 2) ** 0.5
            player_score = 1000 / (player_dist + 1)
            base_score = 1500 / (base_dist + 1)
            if self.difficulty == "hell":
                base_score *= 1.5
            elif self.difficulty == "hard":
                base_score *= 1.2
            if base_score > player_score:
                return base

        return best_player
    
    def _should_dodge(self, tank):
        """检查是否应该躲避子弹"""
        dodge_prob = self.config.get("dodge_prob", 0.3)
        if random.random() > dodge_prob:
            return False
        
        # Check for incoming bullets
        for bullet in self.world.bullets:
            if not bullet.active or bullet.owner == tank:
                continue
            
            # Simple collision prediction
            if self._bullet_will_hit(bullet, tank):
                return True
        return False
    
    # ------------------------------------------------------------------ #
    # 感知 / 状态 / 路径
    # ------------------------------------------------------------------ #
    def _update_threat(self, tank):
        """根据最近伤害来源更新威胁分数并衰减。"""
        # 衰减
        for k in list(self.threat_scores.keys()):
            self.threat_scores[k] *= 0.98
            if self.threat_scores[k] < 1:
                del self.threat_scores[k]
        # 最近伤害来源加分
        hitter = getattr(tank, "last_hit_by", None)
        if hitter and getattr(hitter, "tank_type", None) == "player":
            tid = hitter.tank_id
            self.threat_scores[tid] = self.threat_scores.get(tid, 0) + 20

    def _update_state(self, tank):
        """简单状态机：进攻/防守/撤退/侧翼。"""
        self._state_timer = max(0, self._state_timer - 1)
        health_ratio = tank.health / max(1, config.DEFAULT_HEALTH)
        # 撤退条件：血量低或附近高威胁
        high_threat = max(self.threat_scores.values()) if self.threat_scores else 0
        # 近距压制：玩家靠太近也触发撤退
        close_player = any(
            ((p.x - tank.x) ** 2 + (p.y - tank.y) ** 2) ** 0.5 < 120
            for p in self.world.tanks
            if p.tank_type == "player" and p.active
        )
        if health_ratio < 0.3 or high_threat > 50 or close_player:
            self._state = "retreat"
            self._state_timer = 60
            return
        # 侧翼：周期性触发
        if self._state_timer == 0 and random.random() < 0.15:
            self._state = "flank"
            self._state_timer = 90
            return
        # 防守：如果基地存在且可见，且难度较高时偶尔守
        if self._state_timer == 0 and self.difficulty in ["hard", "hell"] and random.random() < 0.2:
            self._state = "defend"
            self._state_timer = 90
            return
        if self._state_timer == 0:
            self._state = "attack"

    def _select_target(self, tank, base):
        """结合威胁与基地优先，返回目标与是否基地。"""
        players = [t for t in self.world.tanks if t.active and t.tank_type == "player"]
        target = None
        target_is_base = False
        if players:
            def _score(p):
                dist2 = (p.x - tank.x) ** 2 + (p.y - tank.y) ** 2
                threat = self.threat_scores.get(p.tank_id, 0)
                shield_penalty = 40000 if getattr(p, "shield_active", False) else 0
                return dist2 - threat * 5000 + shield_penalty
            target = min(players, key=_score)
        if base:
            # 基地优先权重
            if not target:
                return base, True
            base_dist = ((base.x - tank.x) ** 2 + (base.y - tank.y) ** 2) ** 0.5
            target_dist = ((target.x - tank.x) ** 2 + (target.y - tank.y) ** 2) ** 0.5
            base_score = (1500 / (base_dist + 1)) * max(0.1, self.base_weight)
            target_score = (1000 / (target_dist + 1)) * max(0.1, self.player_weight)
            if self.difficulty in ["hard", "hell"]:
                base_score *= 1.4 if self.difficulty == "hell" else 1.25
            if base_score > target_score:
                # 若基地被墙阻挡，沿射线找第一块阻挡物，若可破坏则锁定拆除
                blocker = self._find_first_blocker_to(base)
                if blocker and getattr(blocker, "destructible", False):
                    return blocker, False
                # 若找不到阻挡或不可破坏，则仍以基地为目标
                return base, True
        return target, False

    def _find_first_blocker_to(self, target):
        """沿射线找到首个阻挡物（墙/基地），用于拆墙或判定遮挡。"""
        tank = next((t for t in self.world.tanks if t.tank_id == self.tank_id and t.active), None)
        if not tank:
            return None
        tank_center = (tank.x + tank.width // 2, tank.y + tank.height // 2)
        tgt_center = (target.x + target.width // 2, target.y + target.height // 2)
        # 收集阻挡物（不可穿墙体）
        blockers = [
            w for w in self.world.walls
            if w.active and not getattr(w, "shoot_through", False)
        ]
        # 按距离排序，取最近的相交阻挡
        blockers.sort(key=lambda w: (w.x - target.x) ** 2 + (w.y - target.y) ** 2)
        for w in blockers:
            if self._line_rect_intersection(tank_center, tgt_center, w.rect):
                return w
        return None

    def _attack_blocker(self, tank, blocker):
        """朝阻挡物移动/射击，尝试拆除。"""
        dx = blocker.x - tank.x
        dy = blocker.y - tank.y
        direction = self._choose_axis_direction(dx, dy, tank.direction)
        if self._turn_to_direction(tank, direction):
            tank.move(direction)
        # 如果在同轴上，直接射击
        if self._is_shooting_path_clear(tank, blocker) or self._is_target_in_firing_arc(tank, blocker):
            self.world.spawn_bullet(tank)

    def _choose_axis_direction(self, dx, dy, current_dir):
        """带缓冲的轴向选择，降低抖动。"""
        if abs(dx) > abs(dy) + 20:
            return Tank.RIGHT if dx > 0 else Tank.LEFT
        if abs(dy) > abs(dx) + 20:
            return Tank.DOWN if dy > 0 else Tank.UP
        # 接近对角时保持当前方向
        if current_dir in [Tank.LEFT, Tank.RIGHT]:
            return Tank.RIGHT if dx > 0 else Tank.LEFT
        return Tank.DOWN if dy > 0 else Tank.UP

    def _next_direction_via_path(self, tank, target):
        """A* 寻路，使用危险度代价图。返回下一步方向或 None。"""
        if not target:
            return None
        grid = config.GRID_SIZE
        cols = max(1, self.world.width // grid)
        rows = max(1, self.world.height // grid)
        start = self._closest_free_cell(int((tank.x + tank.width * 0.5) // grid), int((tank.y + tank.height * 0.5) // grid), cols, rows)
        goal = self._closest_free_cell(int((target.x + target.width * 0.5) // grid), int((target.y + target.height * 0.5) // grid), cols, rows)
        if start == goal:
            return None

        # 构建代价图：基础1，危险区域提高代价；对墙体膨胀一圈提高代价，减少贴墙蹭卡
        blocked = set()
        for w in self.world.walls:
            if not w.active:
                continue
            if getattr(w, "passable", False):
                continue
            blocked.add((int(w.x // grid), int(w.y // grid)))

        danger = [[1.0 for _ in range(rows)] for _ in range(cols)]
        # 墙体膨胀：周围一圈提高代价，避免贴墙路径
        for bx, by in blocked:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    nx, ny = bx + dx, by + dy
                    if 0 <= nx < cols and 0 <= ny < rows:
                        danger[nx][ny] += 3.0
        # 玩家位置增加危险半径
        for p in self.world.tanks:
            if p.tank_type != "player" or not p.active:
                continue
            px, py = int(p.x // grid), int(p.y // grid)
            for dx in range(-3, 4):
                for dy in range(-3, 4):
                    nx, ny = px + dx, py + dy
                    if 0 <= nx < cols and 0 <= ny < rows:
                        danger[nx][ny] += max(0, 4 - (abs(dx) + abs(dy))) * 1.5
            # 直线视野惩罚（硬/地狱更重）
            los_penalty = 4.0 if self.difficulty == "hell" else 2.5 if self.difficulty == "hard" else 1.5
            # 同行
            for x in range(cols):
                if self._line_clear((px, py), (x, py), blocked):
                    danger[x][py] += los_penalty
            # 同列
            for y in range(rows):
                if self._line_clear((px, py), (px, y), blocked):
                    danger[px][y] += los_penalty
        # 子弹轨迹危险
        for b in self.world.bullets:
            if not b.active:
                continue
            bx, by = int(b.x // grid), int(b.y // grid)
            if 0 <= bx < cols and 0 <= by < rows:
                danger[bx][by] += 7
                # 沿子弹方向扩散危险（更少直线穿越）
                spread_len = 3
                dx = 1 if b.velocity_x > 0 else -1 if b.velocity_x < 0 else 0
                dy = 1 if b.velocity_y > 0 else -1 if b.velocity_y < 0 else 0
                for i in range(1, spread_len + 1):
                    sx = bx + dx * i
                    sy = by + dy * i
                    if 0 <= sx < cols and 0 <= sy < rows:
                        danger[sx][sy] += 3

        def heuristic(a, b):
            return abs(a[0] - b[0]) + abs(a[1] - b[1])

        open_set = []
        heapq.heappush(open_set, (0, start))
        came_from = {start: None}
        g_score = {start: 0}
        dirs = [(1,0),(-1,0),(0,1),(0,-1)]

        while open_set:
            _, current = heapq.heappop(open_set)
            if current == goal:
                break
            cx, cy = current
            for dx, dy in dirs:
                nx, ny = cx + dx, cy + dy
                if nx < 0 or ny < 0 or nx >= cols or ny >= rows:
                    continue
                if (nx, ny) in blocked:
                    continue
                step_cost = danger[nx][ny]
                tentative = g_score[current] + step_cost
                if tentative < g_score.get((nx, ny), float("inf")):
                    g_score[(nx, ny)] = tentative
                    came_from[(nx, ny)] = current
                    f = tentative + heuristic((nx, ny), goal)
                    heapq.heappush(open_set, (f, (nx, ny)))

        if goal not in came_from:
            return None
        # 回溯获取下一步
        step = goal
        while came_from[step] and came_from[step] != start:
            step = came_from[step]
        nx, ny = step
        sx, sy = start
        if nx > sx:
            return Tank.RIGHT
        if nx < sx:
            return Tank.LEFT
        if ny > sy:
            return Tank.DOWN
        if ny < sy:
            return Tank.UP
        return None

    def _closest_free_cell(self, gx, gy, cols, rows):
        """若目标格被墙堵塞或越界，寻找最近的可通行格。"""
        if 0 <= gx < cols and 0 <= gy < rows:
            if not any(
                w.active and not getattr(w, "passable", False)
                and int(w.x // config.GRID_SIZE) == gx
                and int(w.y // config.GRID_SIZE) == gy
                for w in self.world.walls
            ):
                return (gx, gy)
        from collections import deque
        q = deque()
        q.append((gx, gy))
        visited = set([(gx, gy)])
        dirs = [(1,0),(-1,0),(0,1),(0,-1)]
        while q:
            x, y = q.popleft()
            if 0 <= x < cols and 0 <= y < rows:
                blocked_here = any(
                    w.active and not getattr(w, "passable", False)
                    and int(w.x // config.GRID_SIZE) == x
                    and int(w.y // config.GRID_SIZE) == y
                    for w in self.world.walls
                )
                if not blocked_here:
                    return (x, y)
            for dx, dy in dirs:
                nx, ny = x + dx, y + dy
                if (nx, ny) not in visited and -1 <= nx <= cols and -1 <= ny <= rows:
                    visited.add((nx, ny))
                    q.append((nx, ny))
        return (max(0, min(cols - 1, gx)), max(0, min(rows - 1, gy)))

    def _line_clear(self, a, b, blocked):
        """网格直线是否有阻挡（用于视野惩罚）。"""
        ax, ay = a
        bx, by = b
        if ax == bx:
            step = 1 if by > ay else -1
            for y in range(ay + step, by, step):
                if (ax, y) in blocked:
                    return False
        elif ay == by:
            step = 1 if bx > ax else -1
            for x in range(ax + step, bx, step):
                if (x, ay) in blocked:
                    return False
        return True
    
    def _bullet_will_hit(self, bullet, tank):
        """预测子弹是否会击中坦克"""
        # Simple check: is bullet moving towards tank?
        dx = tank.x - bullet.x
        dy = tank.y - bullet.y
        
        # Check if bullet is close and moving towards tank
        if bullet.direction == Tank.UP and dy < 0 and abs(dx) < 30 and abs(dy) < 200:
            return True
        if bullet.direction == Tank.DOWN and dy > 0 and abs(dx) < 30 and abs(dy) < 200:
            return True
        if bullet.direction == Tank.LEFT and dx < 0 and abs(dy) < 30 and abs(dx) < 200:
            return True
        if bullet.direction == Tank.RIGHT and dx > 0 and abs(dy) < 30 and abs(dx) < 200:
            return True
        return False
    
    def _dodge_bullet(self, tank):
        """躲避子弹"""
        # Find dangerous bullet
        for bullet in self.world.bullets:
            if not bullet.active or bullet.owner == tank:
                continue
            if self._bullet_will_hit(bullet, tank):
                # Move perpendicular to bullet direction - 修复躲避逻辑，增加稳定性
                # 优先选择与当前坦克方向垂直的方向，避免频繁切换
                if bullet.direction == Tank.UP or bullet.direction == Tank.DOWN:
                    # 子弹从上往下或从下往上，向左右躲避
                    # 优先选择与当前方向一致的水平方向
                    if tank.direction in [Tank.LEFT, Tank.RIGHT]:
                        dodge_dir = tank.direction  # 保持当前水平方向
                    else:
                        dodge_dir = Tank.LEFT if random.random() < 0.5 else Tank.RIGHT
                else:
                    # 子弹从左往右或从右往左，向上下躲避
                    # 优先选择与当前方向一致的垂直方向
                    if tank.direction in [Tank.UP, Tank.DOWN]:
                        dodge_dir = tank.direction  # 保持当前垂直方向
                    else:
                        dodge_dir = Tank.UP if random.random() < 0.5 else Tank.DOWN
                
                # 先调转方向，再移动
                if self._turn_to_direction(tank, dodge_dir):
                    tank.move(dodge_dir)        # move方法内部已设置方向
                return
        
        # Fallback to random
        self._move_random(tank)



class GameEngine:
    """游戏引擎核心类，负责协调各个模块的工作"""

    def __init__(self, enable_network: bool = False):
        """初始化游戏引擎"""
        # Enable DPI Awareness on Windows to prevent auto-scaling
        # This fixes the issue where 2560x1440 window becomes larger than screen on scaled displays
        try:
            # Try to set ProcessDpiAwareness (Windows 8.1+)
            # 0 = Unaware, 1 = System DPI Aware, 2 = Per Monitor DPI Aware
            # We use System DPI Aware (1) to ensure the window size matches physical pixels
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
            print("DPI Awareness set to System DPI Aware (1)")
        except Exception:
            try:
                # Fallback for Windows Vista/7/8
                ctypes.windll.user32.SetProcessDPIAware()
                print("DPI Awareness set via SetProcessDPIAware")
            except Exception as e:
                print(f"Failed to set DPI awareness: {e}")

        # 获取显示器信息，设置合适的窗口大小
        # 首先尝试使用pygame获取分辨率
        info = pygame.display.Info()
        pygame_width, pygame_height = info.current_w, info.current_h
        
        # 然后使用ctypes获取Windows显示器的实际物理分辨率（不受显示缩放影响）
        try:
            # 定义DEVMODE结构用于存储显示设置信息
            class DEVMODE(ctypes.Structure):
                _fields_ = [
                    ('dmDeviceName', ctypes.c_wchar * 32),
                    ('dmSpecVersion', ctypes.c_short),
                    ('dmDriverVersion', ctypes.c_short),
                    ('dmSize', ctypes.c_short),
                    ('dmDriverExtra', ctypes.c_short),
                    ('dmFields', ctypes.c_uint),
                    ('dmOrientation', ctypes.c_short),
                    ('dmPaperSize', ctypes.c_short),
                    ('dmPaperLength', ctypes.c_short),
                    ('dmPaperWidth', ctypes.c_short),
                    ('dmScale', ctypes.c_short),
                    ('dmCopies', ctypes.c_short),
                    ('dmDefaultSource', ctypes.c_short),
                    ('dmPrintQuality', ctypes.c_short),
                    ('dmColor', ctypes.c_short),
                    ('dmDuplex', ctypes.c_short),
                    ('dmYResolution', ctypes.c_short),
                    ('dmTTOption', ctypes.c_short),
                    ('dmCollate', ctypes.c_short),
                    ('dmFormName', ctypes.c_wchar * 32),
                    ('dmLogPixels', ctypes.c_short),
                    ('dmBitsPerPel', ctypes.c_short),
                    ('dmPelsWidth', ctypes.c_uint),
                    ('dmPelsHeight', ctypes.c_uint),
                    ('dmDisplayFlags', ctypes.c_uint),
                    ('dmDisplayFrequency', ctypes.c_uint),
                    ('dmICMMethod', ctypes.c_uint),
                    ('dmICMIntent', ctypes.c_uint),
                    ('dmMediaType', ctypes.c_uint),
                    ('dmDitherType', ctypes.c_uint),
                    ('dmReserved1', ctypes.c_uint),
                    ('dmReserved2', ctypes.c_uint),
                    ('dmPanningWidth', ctypes.c_uint),
                    ('dmPanningHeight', ctypes.c_uint),
                ]
            
            user32 = ctypes.windll.user32
            devmode = DEVMODE()
            devmode.dmSize = ctypes.sizeof(DEVMODE)
            
            # 获取主显示器的默认显示设置
            if user32.EnumDisplaySettingsW(None, -1, ctypes.byref(devmode)):
                physical_width = devmode.dmPelsWidth
                physical_height = devmode.dmPelsHeight
                print(f"EnumDisplaySettings获取的实际物理分辨率: {physical_width}x{physical_height}")
                
                # 使用物理分辨率而不是pygame检测的缩放后分辨率
                screen_width, screen_height = physical_width, physical_height
                print(f"当前显示器分辨率: {screen_width}x{screen_height}")
            else:
                # 如果EnumDisplaySettings调用失败，尝试另一种方法
                user32 = ctypes.windll.user32
                # 获取屏幕的物理宽度和高度（像素）
                physical_width = user32.GetSystemMetrics(0)  # SM_CXSCREEN
                physical_height = user32.GetSystemMetrics(1)  # SM_CYSCREEN
                print(f"GetSystemMetrics获取的分辨率: {physical_width}x{physical_height}")
                
                # 使用这个分辨率
                screen_width, screen_height = physical_width, physical_height
                print(f"当前显示器分辨率: {screen_width}x{screen_height}")
        except Exception as e:
            # 如果ctypes调用失败，回退到pygame获取的分辨率
            screen_width, screen_height = pygame_width, pygame_height
            print(f"使用pygame获取的分辨率: {screen_width}x{screen_height}")
        
        # 确保窗口大小不会超过显示器分辨率
        # 同时保证窗口有合理的最小尺寸
        min_width, min_height = config.MIN_WINDOW_WIDTH, config.MIN_WINDOW_HEIGHT
        
        # 如果显示器分辨率足够大，使用接近显示器分辨率的窗口大小
        # 否则使用显示器分辨率作为窗口大小
        if screen_width >= config.DEFAULT_WINDOW_WIDTH and screen_height >= config.DEFAULT_WINDOW_HEIGHT:
            # 在高分辨率显示器上使用默认窗口大小
            window_width, window_height = config.DEFAULT_WINDOW_WIDTH, config.DEFAULT_WINDOW_HEIGHT
            print(f"使用默认窗口大小: {window_width}x{window_height}")
        else:
            # 在低分辨率显示器上使用显示器分辨率
            window_width, window_height = screen_width, screen_height
            print(f"使用显示器分辨率作为窗口大小: {window_width}x{window_height}")
        
        # 确保窗口大小不小于最小值
        window_width = max(window_width, min_width)
        window_height = max(window_height, min_height)
        
        # 设置游戏窗口 - 添加RESIZABLE标志
        self.screen = pygame.display.set_mode((window_width, window_height), pygame.RESIZABLE)
        self.window_manager = WindowManager(self.screen)
        self.screen_width, self.screen_height = self.window_manager.get_size()
        pygame.display.set_caption("坦克大战 - 单机试玩")
        
        # 注册窗口大小改变回调
        self.window_manager.register_resize_callback(self._on_window_resized)
        
        # 存储原始窗口尺寸
        self.original_width = self.screen_width
        self.original_height = self.screen_height
        
        # 核心模块
        self.network_manager = NetworkManager()
        self.screen_manager = ScreenManager(self.screen, self.network_manager)
        # 将GameEngine实例传递给ScreenManager
        self.screen_manager.game_engine = self
        self.state_manager = StateManager()
        # AI 目标权重（可在设置中调整）
        self.ai_player_weight = getattr(self.screen_manager.context, "ai_player_weight", 1.0)
        self.ai_base_weight = getattr(self.screen_manager.context, "ai_base_weight", 1.0)
        # 创建游戏世界，以1920*1080为基准，固定行列数（28列*21行）
        # 1920*1080的4:3比例对应1440*1080，向下取整为50倍数后为1400*1050
        grid_size = 50
        game_world_width = 28 * grid_size  # 28列
        game_world_height = 21 * grid_size  # 21行
        self.game_world = GameWorld(game_world_width, game_world_height)
        self.state_manager.attach_world(self.game_world)
        video_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "videos"))
        # 验证视频目录是否存在
        if not os.path.exists(video_dir):
            print(f"[Video] 警告：视频目录不存在: {video_dir}")
        else:
            print(f"[Video] 视频目录: {video_dir}")
        self.video_manager = VideoPlaybackController(video_dir)
        # 后台预加载视频与音频，减少首次播放卡顿
        # 注意：在客户端模式下，预加载可能在线程中进行，会使用占位符
        # 实际视频会在主线程中按需加载
        self.video_manager.preload_all(async_load=True)
        
        # 宽高比适配相关
        self.game_world_aspect_ratio = 4/3  # 游戏世界保持4:3比例
        self.render_surface = None  # 中间渲染表面
        self.update_render_surface()  # 初始化中间渲染表面

        # 游戏状态
        self.is_running = True
        self.current_state = "menu"  # menu, lobby, game, settings
        self.enable_network = enable_network
        self.player_tank: Optional[Tank] = None
        self.enemy_controllers: List[EnemyAIController] = []
        self._movement_stack: List[int] = []
        
        # 全屏状态跟踪
        self.is_fullscreen = False
        
        # AI难度锁定（游戏开始时设置，之后不变）
        self.game_difficulty: Optional[str] = None
        
        # 敌人ID计数器 (预留1-4给玩家，敌人从10开始)
        self.next_enemy_id = 10
        
        # 本地玩家ID (用于重生后重新获取控制权)
        self.local_player_id: Optional[int] = None
        
        # 暂停菜单
        self.paused: bool = False
        self.pause_menu: Optional[PauseMenuOverlay] = None
        
        # 播放游戏开始音效
        resource_manager.play_sound("start")
        
        # 关卡系统
        self.current_level = 1
        self.max_level = 10  # 默认10关
        self.game_won = False
        
        # 联机关卡模式特殊属性
        # 默认为 single，避免单机模式被误判为联机模式导致关卡不解锁
        self.multiplayer_game_mode = "single"  # 当前联机/关卡模式
        self.level_number = None  # 当前关卡编号
        self.time_limit = None  # 时间限制（秒）
        self.time_remaining = None  # 剩余时间
        self.score_target = None  # 目标得分
        self.current_score = 0  # 当前得分
        self.level_start_time = None  # 关卡开始时间

    def resize_window(self, width, height):
        """调整窗口大小
        
        Args:
            width: 新的窗口宽度
            height: 新的窗口高度
        """
        self.window_manager.set_window_size(width, height)
        self.screen_width = width
        self.screen_height = height
        self.screen = self.window_manager.game_surface
        
        # 通知ScreenManager窗口大小已改变，但不重新创建对象
        if self.screen_manager:
            self.screen_manager.notify_window_resized(width, height)
            
        # 更新渲染表面，但不重新创建游戏世界
        self.update_render_surface()
        
    def restore_window(self):
        """恢复窗口到原始尺寸"""
        self.resize_window(self.original_width, self.original_height)
        
    def _on_window_resized(self, width, height):
        """
        窗口大小改变时的回调函数
        
        Args:
            width: 新的窗口宽度
            height: 新的窗口高度
        """
        # 添加窗口大小限制
        MIN_WIDTH = config.MIN_WINDOW_WIDTH
        MIN_HEIGHT = config.MIN_WINDOW_HEIGHT
        
        if width < MIN_WIDTH or height < MIN_HEIGHT:
            print(f"窗口大小不能小于 {MIN_WIDTH}x{MIN_HEIGHT}，忽略调整")
            return
        
        # 更新窗口相关属性
        self.screen_width = width
        self.screen_height = height
        self.screen = self.window_manager.game_surface
        
        # 更新中间渲染表面
        self.update_render_surface()
        
        # 通知ScreenManager窗口大小已改变
        if self.screen_manager:
            self.screen_manager.notify_window_resized(width, height)
            
        print(f"游戏引擎已响应窗口大小改变: {width}x{height} (游戏状态已保留)")
        
    def _setup_single_player_world(self, player_tank_id=1, map_name="default"):
        """初始化单机模式对象。"""
        self._movement_stack.clear()
        self.enemy_controllers.clear()  # 清除旧的控制器
        grid_size = config.GRID_SIZE
        
        # 重置游戏世界，清除旧的游戏对象
        self.game_world.reset()
        
        # 播放游戏开始音效
        from src.utils.resource_manager import resource_manager
        resource_manager.play_sound("start")
        
        # 锁定游戏难度（从context读取，游戏过程中不再改变）
        self.game_difficulty = getattr(self.screen_manager.context, 'enemy_difficulty', 'normal')
        print(f"[Game] 单人模式难度已锁定: {self.game_difficulty}")
        
        # 标记当前为单机模式，确保结算逻辑走单机分支
        self.multiplayer_game_mode = "single"

        # Try to load custom map or generate level map
        map_data = None
        if map_name != "default":
            map_data = map_loader.load_map(map_name, config.GRID_SIZE)
            if map_data:
                print(f"加载自定义地图: {map_data.get('name', map_name)}")
        else:
            # 使用关卡地图生成器
            from src.utils.level_map_generator import generate_level_map
            map_data = generate_level_map(self.current_level, 
                                        self.game_world.width, 
                                        self.game_world.height)
            print(f"生成关卡地图: {map_data.get('name', '关卡地图')}")
        
        if map_data:
            # Load from map file or generated map
            # Calculate map offset to center the map in the game world
            map_width = map_data.get('width', 800)
            map_height = map_data.get('height', 600)
            
            # Calculate offset to center map in game world
            offset_x = (self.game_world.width - map_width) // 2
            offset_y = (self.game_world.height - map_height) // 2
            
            # Spawn points - Single player mode only uses first player spawn
            player_spawns = map_data.get('player_spawns', [[400, 550]])
            enemy_spawns = map_data.get('enemy_spawns', [[400, 50]])
            
            # Single player: only use first player spawn point
            player_spawn = tuple(player_spawns[0]) if player_spawns else (400, 550)
            enemy_spawn = tuple(enemy_spawns[0]) if enemy_spawns else (400, 50)
            
            # Apply offset to spawn points
            player_spawn = (player_spawn[0] + offset_x, player_spawn[1] + offset_y)
            enemy_spawn = (enemy_spawn[0] + offset_x, enemy_spawn[1] + offset_y)
            
            self.game_world.register_spawn_points("player", [player_spawn])
            self.game_world.register_spawn_points("enemy", [enemy_spawn])
            
            self.local_player_id = player_tank_id
            self.player_tank = self.game_world.spawn_tank("player", tank_id=player_tank_id, position=player_spawn, skin_id=player_tank_id)
            
            # 生成敌人 (使用动态ID)
            enemy_id = self.next_enemy_id
            self.next_enemy_id += 1
            self.game_world.spawn_tank("enemy", tank_id=enemy_id, position=enemy_spawn)
            self.enemy_controllers.append(EnemyAIController(
                enemy_id,
                self.game_world,
                difficulty=self.game_difficulty,
                player_weight=getattr(self, "ai_player_weight", 1.0),
                base_weight=getattr(self, "ai_base_weight", 1.0),
            ))
            
            # Load walls with offset
            walls = map_data.get('walls', [])
            # 按照固定顺序加载墙体，确保客户端和服务端使用相同的ID
            # 按照坐标排序（先y后x），确保加载顺序一致
            sorted_walls = sorted(walls, key=lambda w: (w.get('y', 0), w.get('x', 0)))
            
            # 重置墙体ID计数器，确保从1开始
            self.game_world.next_wall_id = 1
            self.game_world.wall_id_map.clear()
            
            for wall in sorted_walls:
                x = wall.get('x', 0) + offset_x
                y = wall.get('y', 0) + offset_y
                wall_type = wall.get('type', 0)
                # 不指定wall_id，让系统自动分配（按顺序）
                self.game_world.spawn_wall(x, y, wall_type)
        else:
            # Use default map
            # 调整坦克出生点（适应30x30坦克）
            player_spawn = (self.screen_width // 2 - 15, self.screen_height - 100)
            enemy_spawn = (self.screen_width // 2 - 15, 50)

            self.game_world.register_spawn_points("player", [player_spawn])
            self.game_world.register_spawn_points("enemy", [enemy_spawn])

            self.local_player_id = player_tank_id
            self.player_tank = self.game_world.spawn_tank("player", tank_id=player_tank_id, position=player_spawn)
            
            # 生成敌人 (使用动态ID)
            enemy_id = self.next_enemy_id
            self.next_enemy_id += 1
            self.game_world.spawn_tank("enemy", tank_id=enemy_id, position=enemy_spawn)
            self.enemy_controllers.append(EnemyAIController(
                enemy_id,
                self.game_world,
                difficulty=self.game_difficulty,
                player_weight=getattr(self, "ai_player_weight", 1.0),
                base_weight=getattr(self, "ai_base_weight", 1.0),
            ))

            # 使用50x50网格创建地图布局
            # 重要：按照固定顺序生成墙体，确保客户端和服务端使用相同的ID
            # 重置墙体ID计数器
            self.game_world.next_wall_id = 1
            self.game_world.wall_id_map.clear()
            
            # 收集所有墙体数据，然后按坐标排序
            default_walls = []
            
            # 中间一排砖墙（第6行，y=300）
            for col in range(4, 12):  # 列4-11
                x = col * grid_size
                y = 6 * grid_size
                default_walls.append((x, y, Wall.BRICK))
            
            # 左侧钢墙（列1）
            for row in range(2, 10):  # 行2-9
                x = 1 * grid_size
                y = row * grid_size
                default_walls.append((x, y, Wall.STEEL))
            
            # 右侧钢墙（列14）
            for row in range(2, 10):  # 行2-9
                x = 14 * grid_size
                y = row * grid_size
                default_walls.append((x, y, Wall.STEEL))
            
            # 添加一些草地（列7-8，行4-5）
            for col in range(7, 9):
                for row in range(4, 6):
                    x = col * grid_size
                    y = row * grid_size
                    default_walls.append((x, y, Wall.GRASS))
            
            # 添加河流（列10，行3-8）
            for row in range(3, 9):
                x = 10 * grid_size
                y = row * grid_size
                default_walls.append((x, y, Wall.RIVER))
            
            # 添加基地（老鹰）在底部中央
            base_x = (self.screen_width // 2) - 25  # 居中
            base_y = self.screen_height - 100  # 底部
            default_walls.append((base_x, base_y, Wall.BASE))
            
            # 按照坐标排序（先y后x），确保加载顺序一致
            default_walls.sort(key=lambda w: (w[1], w[0]))
            
            # 按顺序生成墙体
            for x, y, wall_type in default_walls:
                self.game_world.spawn_wall(x, y, wall_type)

    def setup_multiplayer_world(self, p1_tank_id, p2_tank_id, map_name="default", game_mode="coop", level_number=None):
        """初始化联机模式对象
        
        Args:
            p1_tank_id: 玩家1坦克ID
            p2_tank_id: 玩家2坦克ID
            map_name: 地图名称
            game_mode: 游戏模式 ("coop"合作, "pvp"对战, "mixed"混战, "level"关卡)
            level_number: 关卡编号（仅关卡模式使用）
        """
        self.game_world.reset()
        self._movement_stack.clear()
        self.enemy_controllers.clear()  # 清除旧的控制器
        grid_size = config.GRID_SIZE
        
        # 播放游戏开始音效
        from src.utils.resource_manager import resource_manager
        resource_manager.play_sound("start")
        
        # 锁定游戏难度（从context读取，游戏过程中不再改变）
        self.game_difficulty = getattr(self.screen_manager.context, 'enemy_difficulty', 'normal')
        print(f"[Game] 联机模式难度已锁定: {self.game_difficulty}")
        
        # Store game mode and level for later use
        self.multiplayer_game_mode = game_mode
        self.level_number = level_number
        print(f"[Game] 游戏模式: {game_mode}, 关卡编号: {level_number}")
        
        # 根据游戏模式初始化世界
        if game_mode == "level":
            self._setup_level_mode(p1_tank_id, p2_tank_id, map_name, level_number)
        elif game_mode == "pvp":
            self._setup_pvp_mode(p1_tank_id, p2_tank_id, map_name)
        elif game_mode == "mixed":
            self._setup_mixed_mode(p1_tank_id, p2_tank_id, map_name)
        else:  # coop (default)
            self._setup_coop_mode(p1_tank_id, p2_tank_id, map_name)
    
    def _setup_coop_mode(self, p1_tank_id, p2_tank_id, map_name):
        """设置合作模式"""
        self._load_map_and_setup_players(p1_tank_id, p2_tank_id, map_name)
        
        # 设置GameWorld的游戏模式属性
        self.game_world.game_mode = "coop"
        
        # 生成敌人
        enemy_id = self.next_enemy_id
        self.next_enemy_id += 1
        self.game_world.spawn_tank("enemy", tank_id=enemy_id, position=self.enemy_spawn)
        self.enemy_controllers.append(EnemyAIController(enemy_id, self.game_world, difficulty=self.game_difficulty))
    
    def _setup_pvp_mode(self, p1_tank_id, p2_tank_id, map_name):
        """设置对战模式"""
        self._load_map_and_setup_players(p1_tank_id, p2_tank_id, map_name)
        
        # 设置GameWorld的游戏模式属性
        self.game_world.game_mode = "pvp"
        
        # PvP模式不生成敌人，玩家直接对战
        print("[Game] PvP模式: 玩家对战，不生成敌人")
    
    def _setup_mixed_mode(self, p1_tank_id, p2_tank_id, map_name):
        """设置混战模式"""
        self._load_map_and_setup_players(p1_tank_id, p2_tank_id, map_name)
        
        # 设置GameWorld的游戏模式属性
        self.game_world.game_mode = "mixed"
        
        # 生成更多敌人，玩家既要合作又要竞争
        enemy_count = 3  # 混战模式生成更多敌人
        for i in range(enemy_count):
            enemy_id = self.next_enemy_id
            self.next_enemy_id += 1
            # 稍微分散敌人位置
            enemy_pos = (self.enemy_spawn[0] + i * 50, self.enemy_spawn[1])
            self.game_world.spawn_tank("enemy", tank_id=enemy_id, position=enemy_pos)
            self.enemy_controllers.append(EnemyAIController(enemy_id, self.game_world, difficulty=self.game_difficulty))
        
        print(f"[Game] 混战模式: 生成了{enemy_count}个敌人")
    
    def _setup_level_mode(self, p1_tank_id, p2_tank_id, map_name, level_number):
        """设置关卡模式"""
        # 加载关卡地图
        if level_number:
            from src.utils.multiplayer_level_progress import get_multiplayer_level_config
            from src.utils.multiplayer_map_generator import multiplayer_map_generator
            
            level_config = get_multiplayer_level_config(level_number)
            if level_config:
                # 尝试加载关卡地图，如果不存在则生成
                level_map_name = f"level_{level_number}"
                map_data = map_loader.load_map(level_map_name, config.GRID_SIZE)
                
                if not map_data:
                    # 地图不存在，生成新地图
                    print(f"[Game] 关卡{level_number}地图不存在，生成新地图")
                    map_data = multiplayer_map_generator.generate_level_map(level_number)
                
                # 使用关卡配置和地图数据
                self._load_map_and_setup_players(p1_tank_id, p2_tank_id, level_map_name, level_config, map_data)
                
                # 根据关卡配置生成敌人
                enemy_count = level_config.get('enemy_count', 1)
                enemy_types = level_config.get('enemy_types', ['enemy'])
                
                for i in range(enemy_count):
                    enemy_id = self.next_enemy_id
                    self.next_enemy_id += 1
                    enemy_pos = (self.enemy_spawn[0] + i * 50, self.enemy_spawn[1])
                    enemy_type = enemy_types[i % len(enemy_types)]
                    self.game_world.spawn_tank(enemy_type, tank_id=enemy_id, position=enemy_pos)
                    
                    # 根据关卡配置设置敌人难度
                    enemy_difficulty = level_config.get('enemy_difficulty', self.game_difficulty)
                    self.enemy_controllers.append(EnemyAIController(enemy_id, self.game_world, difficulty=enemy_difficulty))
                
                print(f"[Game] 关卡模式: 关卡{level_number}, 敌人数量{enemy_count}, 敌人类型{enemy_types}")
                
                # 设置关卡特殊条件
                if level_config.get('time_limit'):
                    # 实现时间限制功能
                    self.time_limit = level_config['time_limit']
                    self.time_remaining = self.time_limit
                    self.level_start_time = pygame.time.get_ticks()  # 记录关卡开始时间
                    print(f"[Game] 关卡{level_number}有时间限制: {self.time_limit}秒")
                
                if level_config.get('score_target'):
                    # 实现目标得分功能
                    self.score_target = level_config['score_target']
                    self.current_score = 0  # 重置当前得分
                    print(f"[Game] 关卡{level_number}有目标得分: {self.score_target}")
                
                # 设置GameWorld的游戏模式属性
                self.game_world.game_mode = "level"
                self.game_world.level_number = level_number
                self.game_world.time_limit = self.time_limit
                self.game_world.score_target = self.score_target
            else:
                # 回退到普通合作模式
                print(f"[Game] 关卡{level_number}配置未找到，回退到合作模式")
                self._setup_coop_mode(p1_tank_id, p2_tank_id, map_name)
        else:
            # 回退到普通合作模式
            print("[Game] 未指定关卡编号，回退到合作模式")
            self._setup_coop_mode(p1_tank_id, p2_tank_id, map_name)
    
    def _load_map_and_setup_players(self, p1_tank_id, p2_tank_id, map_name, level_config=None, preloaded_map_data=None):
        """加载地图并设置玩家（通用方法）"""
        grid_size = config.GRID_SIZE
        
        # Load Map
        map_data = None
        
        # Priority 1: Use preloaded map data (for level mode)
        if preloaded_map_data:
            map_data = preloaded_map_data
            print(f"[Map] 使用预加载的地图数据: {map_data.get('name', map_name)}")
        # Priority 2: Use received map data from host (for client)
        elif hasattr(self.screen_manager.context, 'received_map_data') and self.screen_manager.context.received_map_data:
            map_data = self.screen_manager.context.received_map_data
            print(f"[Map] 使用接收的地图数据: {map_data.get('name', map_name) if map_data else 'None'}")
            # Clear the received map data to avoid reusing it
            self.screen_manager.context.received_map_data = None
        # Priority 3: Load from local file (for host or if client didn't receive map data)
        if not map_data:
            if map_name != "default":
                map_data = map_loader.load_map(map_name, config.GRID_SIZE)
                if map_data:
                    print(f"[Map] 从本地文件加载地图: {map_data.get('name', map_name)}")
                else:
                    print(f"[Map] 警告: 无法加载地图 {map_name}，将使用默认地图")
            else:
                print(f"[Map] 使用默认地图")
        
        # Default Spawns
        p1_spawn = (self.screen_width // 2 - 100, self.screen_height - 100)
        p2_spawn = (self.screen_width // 2 + 100, self.screen_height - 100)
        enemy_spawn = (self.screen_width // 2 - 15, 50)
        
        # Calculate map offset to center the map in the game world
        offset_x = 0
        offset_y = 0
        
        if map_data:
            # Calculate map dimensions from map data
            map_width = map_data.get('width', 800)
            map_height = map_data.get('height', 600)
            
            # Calculate offset to center map in game world
            offset_x = (self.game_world.width - map_width) // 2
            offset_y = (self.game_world.height - map_height) // 2
            
            # Use map spawns if available
            # Multiplayer mode: use both player spawn points (P1 and P2)
            player_spawns = map_data.get('player_spawns', [])
            if len(player_spawns) >= 2:
                p1_spawn = tuple(player_spawns[0])
                p2_spawn = tuple(player_spawns[1])
            elif len(player_spawns) == 1:
                # Fallback: if only one spawn, offset P2 from P1
                p1_spawn = tuple(player_spawns[0])
                p2_spawn = (p1_spawn[0] + 100, p1_spawn[1])
            
            enemy_spawns = map_data.get('enemy_spawns', [])
            if enemy_spawns:
                enemy_spawn = tuple(enemy_spawns[0])
            
            # Apply offset to spawn points
            p1_spawn = (p1_spawn[0] + offset_x, p1_spawn[1] + offset_y)
            p2_spawn = (p2_spawn[0] + offset_x, p2_spawn[1] + offset_y)
            enemy_spawn = (enemy_spawn[0] + offset_x, enemy_spawn[1] + offset_y)
                
        # Store spawn points for use in mode-specific setup
        self.p1_spawn = p1_spawn
        self.p2_spawn = p2_spawn
        self.enemy_spawn = enemy_spawn
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.map_data = map_data
        
        # Set game mode in game world
        self.game_world.game_mode = self.multiplayer_game_mode
        
        # Determine which tank is local player
        is_host = self.network_manager.stats.role == "host"
        
        # Spawn P1 (Host) - Logic ID 1
        p1 = self.game_world.spawn_tank("player", tank_id=1, position=p1_spawn, skin_id=p1_tank_id)
        
        # P2 Spawn (Client) - Logic ID 2
        p2 = self.game_world.spawn_tank("player", tank_id=2, position=p2_spawn, skin_id=p2_tank_id)
        
        if is_host:
            self.player_tank = p1
            self.local_player_id = 1
        else:
            self.player_tank = p2
            self.local_player_id = 2
        
        # Load map walls
        # 重要：按照固定顺序加载墙体，确保客户端和服务端使用相同的ID
        if map_data:
            walls = map_data.get('walls', [])
            # 按照坐标排序（先y后x），确保加载顺序一致
            # 这样客户端和服务端会分配相同的墙体ID
            sorted_walls = sorted(walls, key=lambda w: (w.get('y', 0), w.get('x', 0)))
            
            # 重置墙体ID计数器，确保从1开始
            self.game_world.next_wall_id = 1
            self.game_world.wall_id_map.clear()
            
            for wall in sorted_walls:
                x = wall.get('x', 0) + offset_x
                y = wall.get('y', 0) + offset_y
                wall_type = wall.get('type', 0)
                # 不指定wall_id，让系统自动分配（按顺序）
                self.game_world.spawn_wall(x, y, wall_type)
        else:
            # Default Map
            # 重要：按照固定顺序生成墙体，确保客户端和服务端使用相同的ID
            # 重置墙体ID计数器
            self.game_world.next_wall_id = 1
            self.game_world.wall_id_map.clear()
            
            # 收集所有墙体数据，然后按坐标排序
            default_walls = []
            
            # 中间一排砖墙（第6行，y=300）
            for col in range(4, 12):  # 列4-11
                x = col * grid_size
                y = 6 * grid_size
                default_walls.append((x, y, Wall.BRICK))
            
            # 左侧钢墙（列1）
            for row in range(2, 10):  # 行2-9
                x = 1 * grid_size
                y = row * grid_size
                default_walls.append((x, y, Wall.STEEL))
            
            # 右侧钢墙（列14）
            for row in range(2, 10):  # 行2-9
                x = 14 * grid_size
                y = row * grid_size
                default_walls.append((x, y, Wall.STEEL))
            
            # 添加一些草地（列7-8，行4-5）
            for col in range(7, 9):
                for row in range(4, 6):
                    x = col * grid_size
                    y = row * grid_size
                    default_walls.append((x, y, Wall.GRASS))
            
            # 添加河流（列10，行3-8）
            for row in range(3, 9):
                x = 10 * grid_size
                y = row * grid_size
                default_walls.append((x, y, Wall.RIVER))
            
            # 添加基地（老鹰）在底部中央
            base_x = (self.screen_width // 2) - 25  # 居中
            base_y = self.screen_height - 100  # 底部
            default_walls.append((base_x, base_y, Wall.BASE))
            
            # 按照坐标排序（先y后x），确保加载顺序一致
            default_walls.sort(key=lambda w: (w[1], w[0]))
            
            # 按顺序生成墙体
            for x, y, wall_type in default_walls:
                self.game_world.spawn_wall(x, y, wall_type)

    def handle_event(self, event):
        """处理游戏事件"""
        self.screen_manager.handle_event(event)
        
        # 处理窗口大小变化事件
        if event.type == pygame.VIDEORESIZE:
            width, height = event.size
            # 限制最小窗口尺寸
            width = max(width, config.MIN_WINDOW_WIDTH)
            height = max(height, config.MIN_WINDOW_HEIGHT)
            self.resize_window(width, height)
            return

        if self.current_state != "game":
            return

        # ESC键暂停/恢复
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._toggle_pause()
            return
        
        # 如果暂停中，让暂停菜单处理事件
        if self.paused and self.pause_menu:
            action = self.pause_menu.handle_event(event)
            if action == 'continue':
                self._toggle_pause()
            elif action == 'restart':
                self._restart_game()
            elif action == 'exit':
                self._exit_to_menu()
            return  # 暂停时不处理游戏事件

        if event.type == pygame.KEYDOWN:
            # 调试功能：Ctrl+数字键生成道具
            if pygame.key.get_mods() & pygame.KMOD_CTRL:
                if event.key >= pygame.K_1 and event.key <= pygame.K_8:
                    prop_id = event.key - pygame.K_1 + 1  # K_1=49, 转换为1-8
                    self._spawn_cheat_prop(prop_id)
                    return
            
            if event.key in (pygame.K_w, pygame.K_UP):
                self._push_direction(Tank.UP)
            elif event.key in (pygame.K_d, pygame.K_RIGHT):
                self._push_direction(Tank.RIGHT)
            elif event.key in (pygame.K_s, pygame.K_DOWN):
                self._push_direction(Tank.DOWN)
            elif event.key in (pygame.K_a, pygame.K_LEFT):
                self._push_direction(Tank.LEFT)
            elif event.key == pygame.K_SPACE:
                self._player_shoot()
            elif event.key == pygame.K_F1:
                self.game_world.enable_debug_overlay(not self.game_world.debug_overlay)

        elif event.type == pygame.KEYUP:
            if event.key in (pygame.K_w, pygame.K_UP):
                self._release_direction(Tank.UP)
            elif event.key in (pygame.K_d, pygame.K_RIGHT):
                self._release_direction(Tank.RIGHT)
            elif event.key in (pygame.K_s, pygame.K_DOWN):
                self._release_direction(Tank.DOWN)
            elif event.key in (pygame.K_a, pygame.K_LEFT):
                self._release_direction(Tank.LEFT)

    def update(self):
        """更新游戏状态"""
        now_ms = pygame.time.get_ticks()
        self.video_manager.update(now_ms)
        
        # 定期尝试重新加载失败的视频资源（复加载机制）
        # 每5秒检查一次，避免过于频繁
        if not hasattr(self, '_last_reload_check'):
            self._last_reload_check = now_ms
        elif now_ms - self._last_reload_check > 5000:  # 5秒
            self._last_reload_check = now_ms
            # 只在主线程中执行（update 在主线程中）
            self.video_manager.reload_failed_assets()
        
        # 如果暂停，只更新UI管理器，跳过游戏逻辑
        if self.paused:
            # 更新UI管理器以处理暂停菜单
            time_delta = 1.0 / 60.0
            self.screen_manager.ui_manager.update(time_delta)
            return
        
        # Network Update
        if self.enable_network:
            self.network_manager.update()
            
            role = self.network_manager.stats.role
            
            if role == "client":
                # Client: Send Input -> Receive State -> Render
                # 1. Send Input
                # We need to capture current input state. 
                # Since handle_event updates _movement_stack, we can just send that?
                # Or better, send the raw key states or the resulting direction.
                # Let's send the current intended move direction and shoot status.
                input_data = {
                    "move": self._movement_stack[-1] if self._movement_stack else -1,
                    # "shoot": False # Don't send shoot here, it's an event handled by _player_shoot
                }
                self.network_manager.send_input(input_data)
                
                # 2. Client-Side Prediction: Update local player tank
                if self.player_tank and self.player_tank.active:
                    # Store previous position for error calculation
                    prev_x, prev_y = self.player_tank.x, self.player_tank.y
                    
                    # Apply movement based on current input state
                    if self._movement_stack:
                        # Get current movement direction
                        current_dir = self._movement_stack[-1]
                        if current_dir != -1:
                            # Apply movement with same physics as server
                            self.player_tank.move(current_dir)
                        else:
                            self.player_tank.stop()
                    else:
                        self.player_tank.stop()
                    
                    # Update tank physics (position, collision, etc.)
                    self.player_tank.update()
                    
                    # Store prediction for later reconciliation
                    if not hasattr(self, '_client_prediction'):
                        self._client_prediction = {}
                    self._client_prediction['last_pos'] = (prev_x, prev_y)
                    self._client_prediction['current_pos'] = (self.player_tank.x, self.player_tank.y)
                
                # 2.5. Update game world objects (for visual effects and animations)
                # 确保客户端模式（不执行权威逻辑）
                self.game_world.is_client_mode = True
                # Update bullets, explosions, and other game objects
                for bullet in self.game_world.bullets:
                    bullet.update()
                for explosion in self.game_world.explosions:
                    explosion.update()
                for star in self.game_world.stars:
                    star.update()
                # Update prop manager if exists
                if hasattr(self.game_world, 'prop_manager'):
                    self.game_world.prop_manager.update()
                
                # 3. Receive State and Reconcile
                remote_state = self.network_manager.get_latest_state()
                if remote_state:
                    # Server reconciliation: check if our prediction was correct
                    my_tank_data = remote_state.get('my_tank')
                    if my_tank_data and self.player_tank:
                        server_x = my_tank_data['x']
                        server_y = my_tank_data['y']
                        local_x = self.player_tank.x
                        local_y = self.player_tank.y
                        
                        # Calculate prediction error
                        error = ((server_x - local_x)**2 + (server_y - local_y)**2)**0.5
                        
                        # Only correct if error is significant to reduce jitter
                        if error > 2:  # Reduced threshold for more responsive correction
                            # If error is HUGE, it's a teleport/respawn
                            if error > 30:  # Reduced threshold for teleport detection
                                self.player_tank.x = server_x
                                self.player_tank.y = server_y
                                self.player_tank.rect.topleft = (server_x, server_y)
                                # Reset velocity to prevent continued drift
                                if hasattr(self.player_tank, 'vx'):
                                    self.player_tank.vx = 0
                                if hasattr(self.player_tank, 'vy'):
                                    self.player_tank.vy = 0
                            else:
                                # Adaptive correction based on error magnitude
                                # Larger errors get stronger correction
                                alpha = min(0.5, max(0.1, error / 20))
                                self.player_tank.x = local_x + (server_x - local_x) * alpha
                                self.player_tank.y = local_y + (server_y - local_y) * alpha
                                self.player_tank.rect.topleft = (self.player_tank.x, self.player_tank.y)
                    
                    # Apply state for other entities (other players, bullets, etc.)
                    self.state_manager.decode_state(remote_state)
                    
                    # 消费同步的事件（用于触发视频播放等客户端效果）
                    self._consume_game_events()
                    
                    # 检查游戏是否结束（客户端）
                    if self.game_world.game_over:
                        if self._check_game_over():
                            # 游戏结束，停止所有音效
                            pygame.mixer.stop()
                            self._play_game_over_video()
                            # 设置游戏结果并显示游戏结束屏幕
                            winner = self.game_world.winner
                            if self.multiplayer_game_mode == "pvp":
                                # PvP模式：根据本地玩家ID判断是否获胜
                                is_host = self.network_manager.stats.role == "host"
                                local_player_key = "player1" if is_host else "player2"
                                self.screen_manager.context.game_won = (winner == local_player_key)
                            elif self.multiplayer_game_mode == "mixed":
                                # 混战模式：根据本地玩家ID判断是否获胜
                                is_host = self.network_manager.stats.role == "host"
                                local_player_key = "player1" if is_host else "player2"
                                self.screen_manager.context.game_won = (winner == local_player_key)
                            else:
                                # 合作模式和关卡模式：winner为"player"表示获胜
                                self.screen_manager.context.game_won = (winner == "player")
                            # 通知屏幕管理器切换到游戏结束屏幕
                            self.screen_manager.set_state("game_over")
                
            elif role == "host":
                # Host: Receive Inputs -> Update Physics -> Send State
                # 1. Receive Inputs
                messages = self.network_manager.get_inputs()
                for msg in messages:
                    if msg.get("type") == "input":
                        inp = msg.get("payload")
                        if not inp:
                            continue
                        # Apply input to Player 2 (Client)
                        # Find client tank (P2 - Logic ID 2)
                        client_tank = next((t for t in self.game_world.tanks if t.tank_id == 2 and t.active), None)
                        if client_tank:
                            move_dir = inp.get("move", -1)
                            # print(f"[Host] Processing input for P2: move={move_dir}")
                            if move_dir != -1:
                                client_tank.move(move_dir)
                            else:
                                client_tank.stop()
                            
                            # Process shoot input
                            if inp.get("shoot"):
                                self.game_world.spawn_bullet(client_tank)
                        else:
                            tank_ids = [t.tank_id for t in self.game_world.tanks if t.active]
                            print(f"[Host] Error: Client tank (ID 2) not found! Active tanks: {tank_ids}")
                            
                # 2. Update Physics - 只有在游戏未结束时才更新
                if self.current_state == "game" and not self.game_world.game_over:
                    # 确保服务端模式（执行权威逻辑）
                    self.game_world.is_client_mode = False
                    # 应用本地主机的移动输入
                    self._apply_player_direction()
                    # 更新本地玩家坦克的物理状态（应用移动后的碰撞检测等）
                    if self.player_tank and self.player_tank.active:
                        self.player_tank.update()
                    # 更新客户端坦克的物理状态（应用移动后的碰撞检测等）
                    client_tank = next((t for t in self.game_world.tanks if t.tank_id == 2 and t.active), None)
                    if client_tank:
                        client_tank.update()
                    # 更新敌人AI（必须在游戏世界更新之前，因为AI会调用move等方法）
                    self._update_enemy_ai()
                    # 更新所有敌人坦克的物理状态
                    for tank in self.game_world.tanks:
                        if tank.tank_type == "enemy" and tank.active:
                            tank.update()
                    # 更新游戏世界（处理碰撞、子弹等）
                    self.game_world.update()
                    
                    # 在消费事件之前，先让状态管理器捕获事件（用于同步到客户端）
                    # 这样确保事件在清空之前被捕获
                    if hasattr(self.state_manager, 'world') and self.state_manager.world:
                        self.state_manager._captured_events = []
                        if hasattr(self.game_world, 'events'):
                            self.state_manager._captured_events = list(self.game_world.events)
                    
                    # 消费事件（触发本地视频播放等效果）
                    self._consume_game_events()
                    
                    # 更新关卡模式特殊条件
                    if self.multiplayer_game_mode == "level":
                        self._update_level_conditions()
                    
                    # 检查游戏是否结束
                    if self._check_game_over():
                        # 游戏结束，停止所有音效
                        pygame.mixer.stop()
                        self._play_game_over_video()
                        # 设置游戏结果并显示游戏结束屏幕
                        # 根据游戏模式判断是否获胜
                        winner = self.game_world.winner
                        if self.multiplayer_game_mode == "pvp":
                            # PvP模式：根据本地玩家ID判断是否获胜
                            is_host = self.network_manager.stats.role == "host"
                            local_player_key = "player1" if is_host else "player2"
                            self.screen_manager.context.game_won = (winner == local_player_key)
                        elif self.multiplayer_game_mode == "mixed":
                            # 混战模式：根据本地玩家ID判断是否获胜
                            is_host = self.network_manager.stats.role == "host"
                            local_player_key = "player1" if is_host else "player2"
                            self.screen_manager.context.game_won = (winner == local_player_key)
                        else:
                            # 合作模式和关卡模式：winner为"player"表示获胜
                            self.screen_manager.context.game_won = (winner == "player")
                        # 通知屏幕管理器切换到游戏结束屏幕
                        self.screen_manager.set_state("game_over")
                        # 向客户端发送最终状态，避免客户端卡在旧画面
                        try:
                            final_state = self.state_manager.encode_state()
                            self.network_manager.send_state(final_state)
                        except Exception as e:
                            print(f"[Game] Failed to send final state: {e}")
                        # 不要立即重置游戏世界，等回到主菜单时再重置
                    else:
                        # 3. Send State - 只有游戏未结束时才发送状态
                        state = self.state_manager.encode_state()
                        self.network_manager.send_state(state)
        
        else:
            # Single Player
            # 只有在游戏未结束时才更新游戏世界
            if self.current_state == "game" and not self.game_world.game_over:
                # 统一移动调用时机：先更新所有坦克的移动状态
                self._apply_player_direction()  # 玩家坦克移动
                self._update_enemy_ai()          # 敌人坦克移动
                
                # 然后更新游戏世界（处理物理和碰撞）
                self.game_world.update()
                self._consume_game_events()
                
                # 更新关卡模式特殊条件
                if self.multiplayer_game_mode == "level":
                    self._update_level_conditions()
                
                # 检查游戏是否结束
                if self._check_game_over():
                    # 游戏结束，停止所有音效
                    pygame.mixer.stop()
                    self._play_game_over_video()
                    # 设置游戏结果并显示游戏结束屏幕
                    # 单机模式：winner为"player"表示获胜
                    self.screen_manager.context.game_won = self.game_world.winner == "player"
                    # 通知屏幕管理器切换到游戏结束屏幕
                    self.screen_manager.set_state("game_over")
                    # 不要立即重置游戏世界，等回到主菜单时再重置

        # UI Update
        self.screen_manager.update()
        
        # Sync State
        if self.screen_manager.current_state != self.current_state:
            self.current_state = self.screen_manager.current_state
            
            if self.current_state == "game":
                # 在游戏开始前，尝试同步预加载关键视频（如果还未完成）
                # 这可以确保视频在需要时已准备好
                if not self.video_manager._preload_completed:
                    status = self.video_manager.get_preload_status()
                    if status["progress"] < 0.5:  # 如果加载进度小于50%，尝试同步预加载
                        print("[Video] 游戏开始前同步预加载视频...")
                        self.video_manager.preload_all_sync()
                
                # Initialize Game World
                mode = self.screen_manager.context.game_mode
                if mode == "single":
                    self.enable_network = False
                    selected_map = getattr(self.screen_manager.context, 'selected_map', 'default')
                    self._setup_single_player_world(self.screen_manager.context.player_tank_id, selected_map)
                elif mode == "multi":
                    self.enable_network = True
                    # Determine P1/P2 IDs
                    # Determine P1/P2 IDs (Logic IDs)
                    # P1 is always 1, P2 is always 2
                    p1_logic_id = 1
                    p2_logic_id = 2
                    
                    # Skin IDs from context
                    p1_skin = self.screen_manager.context.player_tank_id if self.network_manager.stats.role == "host" else self.screen_manager.context.enemy_tank_id
                    p2_skin = self.screen_manager.context.enemy_tank_id if self.network_manager.stats.role == "host" else self.screen_manager.context.player_tank_id
                    
                    # Map Name from context
                    selected_map = getattr(self.screen_manager.context, 'selected_map', 'default')
                    
                    # Get game mode and level number
                    game_mode = getattr(self.screen_manager.context, 'multiplayer_game_mode', 'coop')
                    level_number = getattr(self.screen_manager.context, 'level_number', None)
                        
                    self.setup_multiplayer_world(p1_skin, p2_skin, selected_map, game_mode, level_number)
                    
                    # Set player IDs for state manager
                    if self.network_manager.stats.role == "host":
                        self.state_manager.client_tank_id = p2_logic_id  # For encoding my_tank
                        self.state_manager.local_player_id = None  # Host doesn't skip
                    else:
                        self.state_manager.client_tank_id = None  # Client doesn't send my_tank
                        self.state_manager.local_player_id = p2_logic_id  # Skip this in decode
                elif mode == "level":
                    self.enable_network = False
                    # 设置当前关卡为选择的关卡
                    self.current_level = self.screen_manager.context.selected_level
                    selected_map = "default"  # 关卡模式使用生成的地图
                    player_skin = getattr(self.screen_manager.context, 'player_skin', 1)
                    self._setup_single_player_world(player_skin, selected_map)

        self.state_manager.update()

    # ------------------------------------------------------------------ #
    # 游戏事件 -> 视频触发
    # ------------------------------------------------------------------ #
    def _consume_game_events(self):
        events = self.game_world.consume_events()
        if events:
            role = getattr(self.network_manager.stats, 'role', 'standalone') if hasattr(self, 'network_manager') and self.enable_network else 'standalone'
            print(f"[{role.capitalize()}] 消费 {len(events)} 个事件: {[e.get('type', 'unknown') for e in events]}")
        
        for event in events:
            etype = event.get("type")
            data = event.get("data", {}) or {}
            if etype == "grenade_pickup":
                print(f"[Event] 触发手榴弹视频播放")
                self.video_manager.play("grenade_pickup")
            elif etype == "player_killed_by_enemy":
                pos = data.get("position")
                print(f"[Event] 触发玩家被击败视频播放，位置: {pos}")
                self.video_manager.play("player_killed_by_enemy", position=pos)
            elif etype == "player_life_depleted":
                depleted_id = data.get("tank_id")
                pos = self._get_teammate_focus_position(depleted_id)
                print(f"[Event] 触发队友生命耗尽视频播放，位置: {pos}")
                self.video_manager.play("teammate_out_of_lives", position=pos)
            elif etype == "prop_pickup":
                # 播放道具拾取音效（客户端也能听到）
                from src.utils.resource_manager import resource_manager
                try:
                    resource_manager.play_sound("get_prop")
                except Exception:
                    pass  # 如果音效不存在，忽略错误

    def _get_teammate_focus_position(self, depleted_id: Optional[int]) -> Tuple[int, int]:
        """找到仍然存活/有命的队友位置，用于显示鼓励视频。"""
        other_id = None
        if depleted_id == 1:
            other_id = 2
        elif depleted_id == 2:
            other_id = 1

        if other_id:
            active_tank = next(
                (t for t in self.game_world.tanks if t.tank_type == "player" and t.tank_id == other_id and t.active),
                None,
            )
            if active_tank:
                return active_tank.get_center()

            lives_left = self.game_world.tank_lives.get(other_id, 0)
            if lives_left > 0:
                spawn = self.game_world.tank_info.get(other_id, {}).get("spawn_point")
                if spawn and len(spawn) == 2:
                    return int(spawn[0]), int(spawn[1])

        # 回退：使用世界中心
        return self.game_world.width // 2, self.game_world.height // 2

    def _play_game_over_video(self):
        winner = getattr(self.game_world, "winner", None)
        player_wins = winner in ("player", "player1", "player2")
        key = "victory" if player_wins else "defeat"
        self.video_manager.play(key)

    def update_render_surface(self):
        """更新中间渲染表面尺寸"""
        # 游戏世界保持固定尺寸（28列*21行）
        grid_size = 50
        game_world_width = 28 * grid_size  # 28列
        game_world_height = 21 * grid_size  # 21行
        
        # 创建或更新中间渲染表面
        self.render_surface = pygame.Surface((game_world_width, game_world_height))
        
        # 更新游戏世界尺寸
        if self.game_world:
            self.game_world.width = game_world_width
            self.game_world.height = game_world_height
            self.game_world.bounds = pygame.Rect(0, 0, game_world_width, game_world_height)
    
    def render(self):
        """渲染游戏画面 - 实现宽高比适配"""
        # 1. 填充背景为黑色
        self.screen.fill((0, 0, 0))

        if self.current_state == "game":
            # 2. 确保中间渲染表面尺寸正确
            self.update_render_surface()
            
            # 3. 清空中间渲染表面
            self.render_surface.fill((0, 0, 0))
            
            # 4. 将游戏世界渲染到中间表面
            self.game_world.render(self.render_surface)
            self.video_manager.render_world(self.render_surface)
            
            # 5. 计算缩放比例和居中位置
            # 获取当前窗口的实际大小
            current_width, current_height = pygame.display.get_surface().get_size()
            
            # 计算游戏世界和窗口的宽高比
            game_world_aspect = self.render_surface.get_width() / self.render_surface.get_height()
            window_aspect = current_width / current_height
            
            # 根据宽高比决定缩放基准
            if window_aspect >= game_world_aspect:
                # 窗口更宽，以高度为基准缩放，保持游戏世界宽高比
                scale_factor = current_height / self.render_surface.get_height()
                scaled_width = int(self.render_surface.get_width() * scale_factor)
                scaled_height = current_height
            else:
                # 窗口更窄，以宽度为基准缩放，保持游戏世界宽高比
                scale_factor = current_width / self.render_surface.get_width()
                scaled_width = current_width
                scaled_height = int(self.render_surface.get_height() * scale_factor)
            
            # 计算居中位置
            x_offset = (current_width - scaled_width) // 2
            y_offset = (current_height - scaled_height) // 2
            
            # 6. 缩放并绘制游戏世界到主窗口
            scaled_surface = pygame.transform.scale(self.render_surface, (scaled_width, scaled_height))
            self.screen.blit(scaled_surface, (x_offset, y_offset))
            
            # 8. 绘制生命值显示（在非游戏区域）
            self._draw_lives_display(x_offset, y_offset, scaled_width, scaled_height)
            
            # 7. 渲染暂停菜单
            if self.paused and self.pause_menu:
                # 渲染半透明背景
                self.pause_menu.render()
                # 渲染UI元素（按钮和标签）
                self.screen_manager.ui_manager.draw_ui(self.screen)
        else:
            # 菜单界面直接渲染到主窗口
            self.screen_manager.render()

        # 视频覆盖层（全屏/界面层）
        self.video_manager.render_screen(self.screen)
        pygame.display.flip()

    def _draw_lives_display(self, x_offset, y_offset, scaled_width, scaled_height):
        """在非游戏区域绘制玩家和敌人的生命值显示
        
        Args:
            x_offset: 游戏世界在屏幕上的x偏移量
            y_offset: 游戏世界在屏幕上的y偏移量
            scaled_width: 游戏世界的缩放后宽度
            scaled_height: 游戏世界的缩放后高度
        """
        # 初始化字体
        if not hasattr(self, 'lives_font'):
            self.lives_font = pygame.font.SysFont('SimHei', 24)
            self.lives_small_font = pygame.font.SysFont('SimHei', 18)
        
        # 计算生命值显示区域
        left_margin = x_offset // 2  # 左侧黑边的中间位置
        right_margin = x_offset + scaled_width + (x_offset // 2)  # 右侧黑边的中间位置
        
        # 统计玩家生命值（按坦克ID区分），并读取自定义昵称
        lives_p1 = self.game_world.tank_lives.get(1, 0)
        lives_p2 = self.game_world.tank_lives.get(2, 0)
        name_p1 = getattr(self.screen_manager.context, "username", "玩家1")
        name_p2 = getattr(self.screen_manager.context, "remote_username", "玩家2")
        
        # 左侧显示玩家1
        p1_text = f"{name_p1}"
        p1_lives_text = f"{lives_p1}"
        
        p1_title_surface = self.lives_font.render(p1_text, True, (0, 255, 0))
        p1_title_rect = p1_title_surface.get_rect(
            center=(left_margin, scaled_height // 4)
        )
        self.screen.blit(p1_title_surface, p1_title_rect)
        
        p1_lives_surface = self.lives_font.render(p1_lives_text, True, (255, 255, 0))
        p1_lives_rect = p1_lives_surface.get_rect(
            center=(left_margin, scaled_height // 4 + 30)
        )
        self.screen.blit(p1_lives_surface, p1_lives_rect)
        
        # 右侧显示玩家2
        p2_text = f"{name_p2}"
        p2_lives_text = f"{lives_p2}"
        
        p2_title_surface = self.lives_font.render(p2_text, True, (0, 200, 255))
        p2_title_rect = p2_title_surface.get_rect(
            center=(right_margin, scaled_height // 4)
        )
        self.screen.blit(p2_title_surface, p2_title_rect)
        
        p2_lives_surface = self.lives_font.render(p2_lives_text, True, (255, 255, 0))
        p2_lives_rect = p2_lives_surface.get_rect(
            center=(right_margin, scaled_height // 4 + 30)
        )
        self.screen.blit(p2_lives_surface, p2_lives_rect)

        # 混战模式显示比分（仅 mixed 模式）
        if getattr(self.game_world, "game_mode", "") == "mixed":
            score_p1 = self.game_world.player_scores.get("player1", 0)
            score_p2 = self.game_world.player_scores.get("player2", 0)
            
            score_font = self.lives_small_font
            
            p1_score_surface = score_font.render(f"得分: {score_p1}", True, (0, 255, 0))
            p1_score_rect = p1_score_surface.get_rect(
                center=(left_margin, scaled_height // 4 + 60)
            )
            self.screen.blit(p1_score_surface, p1_score_rect)
            
            p2_score_surface = score_font.render(f"得分: {score_p2}", True, (0, 200, 255))
            p2_score_rect = p2_score_surface.get_rect(
                center=(right_margin, scaled_height // 4 + 60)
            )
            self.screen.blit(p2_score_surface, p2_score_rect)
    
    def _check_game_over(self) -> bool:
        """检查游戏是否结束"""
        if self.game_world.game_over:
            # 处理不同游戏模式的游戏结束逻辑
            if getattr(self, "multiplayer_game_mode", "single") not in (None, "single"):
                # 联机或其他模式
                return self._handle_multiplayer_game_over()
            else:
                # 单机模式
                return self._handle_single_player_game_over()
        return False
    
    def _handle_single_player_game_over(self) -> bool:
        """处理单机模式的游戏结束逻辑"""
        if self.game_world.winner == "player":
            # 玩家获胜，解锁下一关卡
            from src.utils.level_progress import unlock_next_level
            unlock_next_level(self.current_level)

            # 准备“下一关”按钮用的上下文数据（仅关卡模式生效）
            ctx = getattr(self, "screen_manager", None).context if getattr(self, "screen_manager", None) else None
            if ctx:
                next_level = self.current_level + 1
                ctx.next_level = next_level if next_level <= self.max_level else None

            # 结束本局，交给结算界面决定去向
            if self.current_level < self.max_level:
                print(f"[Game] 第 {self.current_level} 关完成！可选择进入第 {self.current_level + 1} 关。")
            else:
                print(f"[Game] 恭喜！您已通关所有 {self.max_level} 关！")
            self.game_won = True
            return True
        else:
            # 玩家失败，游戏结束
            ctx = getattr(self, "screen_manager", None).context if getattr(self, "screen_manager", None) else None
            if ctx:
                ctx.next_level = None
            print(f"[Game] 第 {self.current_level} 关失败！游戏结束。")
            return True
    
    def _handle_multiplayer_game_over(self) -> bool:
        """处理联机模式的游戏结束逻辑"""
        winner = self.game_world.winner
        
        if self.multiplayer_game_mode == "level":
            # 关卡模式：处理关卡进度
            if winner == "player":
                # 玩家获胜，解锁下一联机关卡
                from src.utils.multiplayer_level_progress import complete_multiplayer_level
                complete_multiplayer_level(self.level_number)
                print(f"[Game] 联机关卡 {self.level_number} 完成！")
            else:
                print(f"[Game] 联机关卡 {self.level_number} 失败！")
        elif self.multiplayer_game_mode == "pvp":
            # 对战模式：显示胜负结果
            if winner == "player1":
                print("[Game] 对战模式：玩家1获胜！")
            elif winner == "player2":
                print("[Game] 对战模式：玩家2获胜！")
            else:
                print("[Game] 对战模式：平局！")
        elif self.multiplayer_game_mode == "mixed":
            # 混战模式：显示胜负结果
            if winner == "player1":
                print("[Game] 混战模式：玩家1获胜！")
            elif winner == "player2":
                print("[Game] 混战模式：玩家2获胜！")
            elif winner == "draw":
                print("[Game] 混战模式：平局！")
            else:
                print("[Game] 混战模式：挑战失败！")
        else:  # coop
            # 合作模式：显示胜负结果
            if winner == "player":
                print("[Game] 合作模式：挑战成功！")
            else:
                print("[Game] 合作模式：挑战失败！")
        
        # 联机模式下，游戏结束就是结束
        return True
    
    def _prepare_next_level(self):
        """准备进入下一关卡"""
        # 增加关卡数
        self.current_level += 1
        
        # 重置游戏世界
        self.game_world.reset()
        
        # 清除旧的敌人控制器
        self.enemy_controllers.clear()
        
        # 根据当前游戏模式重新设置游戏世界
        if hasattr(self.screen_manager.context, 'is_multiplayer') and self.screen_manager.context.is_multiplayer:
            # 联机模式
            p1_skin = getattr(self.screen_manager.context, 'p1_skin', 1)
            p2_skin = getattr(self.screen_manager.context, 'p2_skin', 2)
            selected_map = getattr(self.screen_manager.context, 'selected_map', 'default')
            
            # Get game mode and level number
            game_mode = getattr(self.screen_manager.context, 'multiplayer_game_mode', 'coop')
            level_number = getattr(self.screen_manager.context, 'level_number', None)
            
            self.setup_multiplayer_world(p1_skin, p2_skin, selected_map, game_mode, level_number)
        else:
            # 单机模式
            player_skin = getattr(self.screen_manager.context, 'player_skin', 1)
            selected_map = getattr(self.screen_manager.context, 'selected_map', 'default')
            self._setup_single_player_world(player_skin, selected_map)
        
        print(f"[Game] 第 {self.current_level} 关已准备就绪！")
    
    def _update_level_conditions(self):
        """更新关卡模式的特殊条件（时间限制和目标得分）"""
        if not self.level_start_time:
            self.level_start_time = pygame.time.get_ticks()
        
        # 更新时间限制
        if self.time_limit is not None:
            current_time = pygame.time.get_ticks()
            elapsed_seconds = (current_time - self.level_start_time) / 1000.0
            self.time_remaining = max(0, self.time_limit - elapsed_seconds)
            
            # 同步到GameWorld以便网络传输
            self.game_world.time_remaining = self.time_remaining
            
            # 检查时间是否耗尽
            if self.time_remaining <= 0:
                print(f"[Game] 时间耗尽！关卡失败！")
                self.game_world.game_over = True
                self.game_world.winner = "enemy"
                return
        
        # 更新目标得分
        if self.score_target is not None:
            # 计算当前得分（可以根据实际游戏规则调整）
            # 这里简单计算：击败敌人得分 + 剩余时间奖励
            enemy_count = len([t for t in self.game_world.tanks if t.tank_type == "enemy" and not t.active])
            self.current_score = enemy_count * 100  # 每击败一个敌人得100分
            
            # 如果有时间限制，剩余时间可以转换为额外分数
            if self.time_remaining is not None:
                self.current_score += int(self.time_remaining * 10)  # 每秒剩余时间10分
            
            # 同步到GameWorld以便网络传输
            self.game_world.current_score = self.current_score
            
            # 检查是否达到目标得分
            if self.current_score >= self.score_target:
                print(f"[Game] 达到目标得分 {self.score_target}！关卡胜利！")
                self.game_world.game_over = True
                self.game_world.winner = "player"
                return

    # ------------------------------------------------------------------ #
    # 玩家控制
    # ------------------------------------------------------------------ #
    def _push_direction(self, direction: int):
        if direction in self._movement_stack:
            self._movement_stack.remove(direction)
        self._movement_stack.append(direction)
        # 移除立即调用，改为在游戏更新时统一调用

    def _release_direction(self, direction: int):
        if direction in self._movement_stack:
            self._movement_stack.remove(direction)
        # 移除立即调用，改为在游戏更新时统一调用

    def _apply_player_direction(self):
        # Client-Side Prediction: Both client and host move local player immediately
        
        # 重生检查：如果当前引用的坦克失效，尝试根据ID重新获取
        if (not self.player_tank or not self.player_tank.active) and self.local_player_id:
            # 尝试在活跃坦克列表中找到自己的坦克
            new_tank = next((t for t in self.game_world.tanks if t.tank_id == self.local_player_id and t.active), None)
            if new_tank:
                print(f"[Control] 重新获取玩家坦克引用 (ID: {self.local_player_id})")
                self.player_tank = new_tank

        if not self.player_tank or not self.player_tank.active:
            return
        if self._movement_stack:
            self.player_tank.move(self._movement_stack[-1])
        else:
            self.player_tank.stop()

    def _player_shoot(self):
        if self.enable_network and self.network_manager.stats.role == "client":
            # Client: Send shoot command
            self.network_manager.send_input({"move": self._movement_stack[-1] if self._movement_stack else -1, "shoot": True})
        else:
            # Host or Single: Shoot locally
            if self.player_tank and self.player_tank.active:
                self.game_world.spawn_bullet(self.player_tank)

    # ------------------------------------------------------------------ #
    # 敌人 AI
    # ------------------------------------------------------------------ #
    def _update_enemy_ai(self):
        """更新敌人AI"""
        # 检查是否有新生成的敌人需要分配AI控制器
        active_enemy_ids = {t.tank_id for t in self.game_world.tanks if t.active and t.tank_type == "enemy"}
        current_controller_ids = {c.tank_id for c in self.enemy_controllers}
        
        # 为新敌人创建控制器
        new_enemy_ids = active_enemy_ids - current_controller_ids
        for tank_id in new_enemy_ids:
            # 使用锁定的游戏难度，而不是从context读取（防止重生时难度改变）
            difficulty = self.game_difficulty if self.game_difficulty else 'normal'
            self.enemy_controllers.append(EnemyAIController(
                tank_id,
                self.game_world,
                difficulty,
                player_weight=getattr(self, "ai_player_weight", 1.0),
                base_weight=getattr(self, "ai_base_weight", 1.0),
            ))
            print(f"[AI] 为坦克 {tank_id} 创建AI控制器，难度: {difficulty}")
            
        # 移除已死亡敌人的控制器
        self.enemy_controllers = [c for c in self.enemy_controllers if c.tank_id in active_enemy_ids]
        
        # 更新所有控制器
        for controller in self.enemy_controllers:
            controller.player_weight = getattr(self, "ai_player_weight", 1.0)
            controller.base_weight = getattr(self, "ai_base_weight", 1.0)
            controller.update()
    
    def _toggle_pause(self):
        """切换暂停状态"""
        self.paused = not self.paused
        if self.paused:
            # 创建暂停菜单
            self.pause_menu = PauseMenuOverlay(self.screen, self.screen_manager.ui_manager.manager)
        else:
            # 销毁暂停菜单
            if self.pause_menu:
                self.pause_menu.cleanup()
                self.pause_menu = None

    def _restart_game(self):
        """重新开始游戏"""
        if self.pause_menu:
            self.pause_menu.cleanup()
            self.pause_menu = None
        self.paused = False
        
        # 重置关卡系统
        self.current_level = 1
        self.game_won = False
        
        # 重新初始化游戏世界
        self.game_world.reset()
        if hasattr(self.screen_manager.context, 'game_mode'):
            if self.screen_manager.context.game_mode == 'single':
                player_tank_id = getattr(self.screen_manager.context, 'player_tank_id', 1)
                map_name = getattr(self.screen_manager.context, 'selected_map', 'default')
                self._setup_single_player_world(player_tank_id, map_name)

    def _exit_to_menu(self):
        """退出到主菜单"""
        if self.pause_menu:
            self.pause_menu.cleanup()
            self.pause_menu = None
        self.paused = False
        
        # 停止所有音效
        pygame.mixer.stop()
        
        # 清理游戏状态
        self.game_world.reset()
        self.enemy_controllers.clear()
        self._movement_stack.clear()
        
        # 清理状态管理器
        if hasattr(self.state_manager, 'latest_snapshot'):
            self.state_manager.latest_snapshot = None
        if hasattr(self.state_manager, '_captured_events'):
            self.state_manager._captured_events = []
        if hasattr(self.state_manager, 'pending_remote_state'):
            self.state_manager.pending_remote_state = None
        
        # 清理视频管理器
        if hasattr(self, 'video_manager'):
            self.video_manager._stop_active()
        
        # 清理上下文状态
        if hasattr(self.screen_manager, 'context'):
            if hasattr(self.screen_manager.context, 'game_won'):
                self.screen_manager.context.game_won = False
            if hasattr(self.screen_manager.context, 'next_level'):
                self.screen_manager.context.next_level = None
        
        # 切换到菜单状态
        self.current_state = "menu"
        
        # 通知ScreenManager切换到菜单屏幕
        self.screen_manager.set_state("menu")
    
    def _spawn_cheat_prop(self, prop_id: int):
        """调试功能：在玩家坦克前方生成指定道具
        
        Args:
            prop_id: 道具ID (1-8)
        """
        if not self.player_tank or not self.player_tank.active:
            print(f"[Cheat] 无法生成道具：玩家坦克不存在或未激活")
            return
        
        # 获取玩家坦克位置和方向
        tank_x = self.player_tank.x
        tank_y = self.player_tank.y
        direction = self.player_tank.direction
        
        # 根据坦克方向计算道具生成位置（坦克前方50像素）
        offset = 50
        if direction == Tank.UP:
            prop_x = tank_x
            prop_y = tank_y - offset
        elif direction == Tank.RIGHT:
            prop_x = tank_x + offset
            prop_y = tank_y
        elif direction == Tank.DOWN:
            prop_x = tank_x
            prop_y = tank_y + offset
        elif direction == Tank.LEFT:
            prop_x = tank_x - offset
            prop_y = tank_y
        else:
            prop_x = tank_x
            prop_y = tank_y
        
        # 确保道具在地图范围内
        prop_x = max(0, min(prop_x, self.screen_width - 30))
        prop_y = max(0, min(prop_y, self.screen_height - 30))
        
        # 生成道具
        self.game_world.prop_manager.spawn_prop(prop_x, prop_y, prop_id)
        print(f"[Cheat] 生成道具 {prop_id} 于位置 ({prop_x}, {prop_y})")
