from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from src.game_engine.game_world import GameWorld


@dataclass
class StateSnapshot:
    """描述一次状态同步的数据结构。"""

    timestamp: float
    tanks: List[Dict]
    bullets: List[Dict]
    meta: Dict = field(default_factory=dict)


class StateManager:
    """负责在本地维护游戏世界快照并为网络层提供接口的占位实现。"""

    def __init__(self):
        self.world: Optional[GameWorld] = None
        self.latest_snapshot: Optional[StateSnapshot] = None
        self.pending_remote_state: Optional[Dict] = None

    def attach_world(self, world: GameWorld):
        """绑定 GameWorld；UI/网络初始化后调用一次。"""
        self.world = world

    def update(self):
        """在每帧调用，用于生成本地快照或应用远端状态。"""
        if not self.world:
            return
        if self.pending_remote_state:
            self.decode_state(self.pending_remote_state)
            self.pending_remote_state = None
        # Capture events before they're consumed by game engine
        # This ensures events are synced even if they're consumed in the same frame
        # Note: For host, events should be captured BEFORE _consume_game_events() is called
        # If _captured_events is already set (by game engine), use it; otherwise capture now
        if not hasattr(self, '_captured_events') or not self._captured_events:
            self._captured_events = []
            if hasattr(self.world, 'events'):
                self._captured_events = list(self.world.events)
        self.latest_snapshot = self.encode_state()

    def encode_state(self) -> dict:
        """生成完整的世界状态快照"""
        if not self.world:
            return {}
            
        tanks = []
        my_tank_data = None  # Separate data for client's own tank
        
        for tank in self.world.tanks:
            # Include all tanks, not just active ones, to properly sync death state
            tank_data = {
                "id": tank.tank_id,
                "type": tank.tank_type,
                "x": tank.x,
                "y": tank.y,
                "dir": tank.direction,
                "vx": tank.velocity_x,  # For animation
                "vy": tank.velocity_y,  # For animation
                "hp": getattr(tank, "health", 100),
                "shield": tank.shield_active,
                "skin": getattr(tank, "skin_id", 1),
                "level": getattr(tank, "level", 0),
                "has_boat": getattr(tank, "has_boat", False),
                "is_on_river": getattr(tank, "is_on_river", False),
                "active": tank.active  # Explicitly include active state
            }
            
            # Only include position/velocity data for active tanks
            if not tank.active:
                # For inactive tanks, we only need basic info
                tank_data = {
                    "id": tank.tank_id,
                    "type": tank.tank_type,
                    "active": False,
                    "hp": 0
                }
                
            tanks.append(tank_data)
            
            # Mark client's tank separately (will be set by game.py)
            if hasattr(self, 'client_tank_id') and tank.tank_id == self.client_tank_id:
                my_tank_data = tank_data
                
        bullets = []
        for bullet in self.world.bullets:
            if bullet.active:
                bullets.append({
                    "x": bullet.x,
                    "y": bullet.y,
                    "dir": bullet.direction,
                    "owner": getattr(bullet.owner, "tank_id", -1)
                })
                
        # Optimization: Only send destroyed walls and changed wall types
        destroyed_walls = []
        changed_walls = []
        for idx, wall in enumerate(self.world.walls):
            if not wall.active:
                destroyed_walls.append(idx)
            # Track wall type changes (for Shovel effect)
            # We need to store original types to detect changes
            # For now, just send all wall types
            if wall.active:
                changed_walls.append({"idx": idx, "type": wall.wall_type})
                
        # Sync Explosions
        explosions = []
        for exp in self.world.explosions:
            if exp.visible:
                explosions.append({
                    "x": exp.x,
                    "y": exp.y,
                    "r": exp.radius,
                    "d": exp.duration,
                    "e": exp.elapsed
                })

        # Sync Stars
        stars = []
        for star in self.world.stars:
            if star.visible:
                stars.append({
                    "x": star.x,
                    "y": star.y,
                    "d": star.duration,
                    "e": star.elapsed
                })

        # Sync Respawn System
        respawn_data = {
            "lives": dict(self.world.tank_lives),
            "timers": dict(self.world.respawn_timers)
        }
        
        # Sync Props
        props = []
        if hasattr(self.world, 'prop_manager'):
            for prop in self.world.prop_manager.props:
                props.append({
                    "type": prop.type,
                    "x": prop.rect.x,
                    "y": prop.rect.y
                })

        # Sync Events (for video playback and other client-side effects)
        # Use captured events from update() to ensure we get events even if they were consumed
        events = getattr(self, '_captured_events', [])
        if not events and hasattr(self.world, 'events'):
            # Fallback: if capture didn't work, try to get current events
            events = list(self.world.events)
        
        # Debug: log events being synced (only for host)
        if len(events) > 0 and hasattr(self.world, 'is_client_mode') and not self.world.is_client_mode:
            print(f"[Host] 同步 {len(events)} 个事件到客户端: {[e.get('type', 'unknown') for e in events]}")

        return {
            "ts": time.time(),
            "tanks": tanks,
            "my_tank": my_tank_data,  # Client's own tank for reconciliation
            "bullets": bullets,
            "d_walls": destroyed_walls,
            "c_walls": changed_walls,
            "exps": explosions,
            "stars": stars,
            "respawn": respawn_data,
            "props": props,
            "events": events,  # Sync events for client-side video playback
            "meta": {
                "over": self.world.game_over,
                "win": self.world.winner,
                # 添加关卡模式特殊条件同步
                "game_mode": getattr(self.world, "game_mode", None),
                "level_number": getattr(self.world, "level_number", None),
                "time_limit": getattr(self.world, "time_limit", None),
                "time_remaining": getattr(self.world, "time_remaining", None),
                "score_target": getattr(self.world, "score_target", None),
                "current_score": getattr(self.world, "current_score", None),
                # 添加混战模式得分同步
                "player_scores": dict(getattr(self.world, "player_scores", {}))
            }
        }

    def decode_state(self, state: dict):
        """应用远端状态到本地世界"""
        if not self.world or not state:
            return
            
        # 1. Sync Tanks
        remote_tanks = {t["id"]: t for t in state.get("tanks", [])}
        local_player_id = getattr(self, 'local_player_id', None)
        
        # Update existing or spawn new
        for t_data in remote_tanks.values():
            tid = t_data.get("id")
            if tid is None:
                print("[StateManager] 警告：收到无效的坦克数据（缺少ID），跳过")
                continue
            
            # 检查坦克是否活跃（非活跃坦克可能缺少位置信息）
            is_active = t_data.get("active", True)
            
            # Find tank by ID
            tank = next((t for t in self.world.tanks if t.tank_id == tid), None)
            if tank:
                # For local player: only update critical state (health, active), skip position (client-side prediction)
                if local_player_id and tid == local_player_id:
                    # Only sync critical state that client can't predict
                    tank.health = t_data.get("hp", 100)
                    tank.shield_active = t_data.get("shield", False)
                    old_level = tank.level
                    new_level = t_data.get("level", 0)
                    tank.level = new_level
                    # 应用等级效果（如果等级变化）
                    if new_level != old_level:
                        self._apply_level_effects(tank)
                    tank.has_boat = t_data.get("has_boat", False)
                    tank.is_on_river = t_data.get("is_on_river", False)
                    
                    # Special Case: Respawn / Teleport
                    # If tank was inactive (dead) and now active, OR position difference is huge -> Force Sync
                    # 只有在坦克活跃且有位置信息时才进行位置同步
                    if is_active and "x" in t_data and "y" in t_data:
                        # Calculate distance squared
                        dx = tank.x - t_data["x"]
                        dy = tank.y - t_data["y"]
                        dist_sq = dx*dx + dy*dy
                        
                        was_inactive = not tank.active
                        is_teleport = dist_sq > 2500  # > 50 pixels diff (one grid size)
                        
                        if was_inactive or is_teleport:
                            print(f"[Client] Local Player Respawn/Teleport detected! Force syncing pos. Dist: {dist_sq**0.5:.1f}")
                            tank.x = t_data["x"]
                            tank.y = t_data["y"]
                            tank.direction = t_data.get("dir", tank.direction)
                            tank.rect.topleft = (tank.x, tank.y)
                            tank.active = True
                            tank.visible = True
                    elif not is_active:
                        # 如果服务器标记为非活跃，同步状态
                        tank.active = False
                        tank.visible = False
                    
                    # Don't override position/direction for local player (client-side prediction) normally
                else:
                    # For remote players: full state sync
                    # 检查是否有位置信息（活跃坦克应该有）
                    if is_active and "x" in t_data and "y" in t_data:
                        tank.x = t_data["x"]
                        tank.y = t_data["y"]
                        tank.direction = t_data.get("dir", tank.direction)
                        tank.shield_active = t_data.get("shield", False)
                        tank.rect.topleft = (tank.x, tank.y)
                        
                        # Update animation based on velocity (only for active tanks with position)
                        vx = t_data.get("vx", 0)
                        vy = t_data.get("vy", 0)
                        is_moving = (vx != 0 or vy != 0)
                        
                        if is_moving:
                            # Animate tank
                            tank.animation_counter += 1
                            if tank.animation_counter >= tank.animation_speed:
                                tank.animation_counter = 0
                                tank.animation_frame = (tank.animation_frame + 1) % len(tank.images[tank.direction])
                            if tank.images[tank.direction]:
                                tank.current_image = tank.images[tank.direction][tank.animation_frame]
                        else:
                            # Static tank
                            tank.animation_frame = 0
                            tank.animation_counter = 0
                            if tank.images[tank.direction]:
                                tank.current_image = tank.images[tank.direction][0]
                        
                        # Sync tank level and boat state
                        old_level = tank.level
                        new_level = t_data.get("level", 0)
                        tank.level = new_level
                        # 应用等级效果（如果等级变化）
                        if new_level != old_level:
                            self._apply_level_effects(tank)
                        tank.has_boat = t_data.get("has_boat", False)
                        tank.is_on_river = t_data.get("is_on_river", False)
                        
                        # Mark as active/visible
                        tank.active = True
                        tank.visible = True
                    else:
                        # 非活跃坦克或缺少位置信息，只更新状态
                        tank.shield_active = t_data.get("shield", False)
                        tank.active = is_active
                        tank.visible = is_active
                        # 即使非活跃，也同步等级和船状态（如果存在）
                        if "level" in t_data:
                            old_level = tank.level
                            new_level = t_data.get("level", 0)
                            tank.level = new_level
                            if new_level != old_level:
                                self._apply_level_effects(tank)
                        tank.has_boat = t_data.get("has_boat", False)
                        tank.is_on_river = t_data.get("is_on_river", False)
            else:
                # Spawn new tank
                # 检查是否有必要的位置信息
                if not is_active or "x" not in t_data or "y" not in t_data:
                    print(f"[StateManager] 警告：无法生成坦克 {tid}，缺少位置信息或坦克非活跃")
                    continue
                
                tank_type = t_data.get("type", "player")
                spawn_pos = (t_data["x"], t_data["y"])
                skin_id = t_data.get("skin", 1)
                
                try:
                    new_tank = self.world.spawn_tank(tank_type, tid, spawn_pos, skin_id=skin_id)
                    new_tank.direction = t_data.get("dir", 0)
                    # 同步等级并应用效果
                    new_tank.level = t_data.get("level", 0)
                    self._apply_level_effects(new_tank)
                    # 同步其他状态
                    new_tank.has_boat = t_data.get("has_boat", False)
                    new_tank.is_on_river = t_data.get("is_on_river", False)
                    new_tank.shield_active = t_data.get("shield", False)
                    if new_tank.images[new_tank.direction]:
                        new_tank.current_image = new_tank.images[new_tank.direction][0]
                except Exception as exc:
                    print(f"[StateManager] 生成坦克 {tid} 时出错: {exc}")
                    import traceback
                    traceback.print_exc()
                    continue
        
        # Disable missing tanks (including local player if dead!)
        for tank in self.world.tanks:
            if tank.tank_id not in remote_tanks:
                # Tank is dead or removed from server
                if tank.tank_type == "player":
                    print(f"[Client] Player tank {tank.tank_id} died (Not in remote state). Local Player ID: {local_player_id}")
                    # If this is the local player, create death explosion
                    if local_player_id and tank.tank_id == local_player_id:
                        from src.game_engine.game_world import Explosion
                        explosion = Explosion(tank.x + 20, tank.y + 20, 20, 0)
                        self.world.add_object(explosion)
                        print(f"[Client] Created death explosion for local player")
                
                # Mark tank as inactive and invisible
                tank.active = False
                tank.visible = False
                tank.health = 0  # Ensure health is 0 for dead tanks
            else:
                # Tank exists in remote state, ensure it's active if server says so
                remote_tank_data = remote_tanks[tank.tank_id]
                if remote_tank_data.get("active", True):
                    tank.active = True
                    tank.visible = True
                else:
                    tank.active = False
                    tank.visible = False
                
        # 2. Sync Bullets
        self.world.bullets.clear() 
        
        from src.game_engine.bullet import Bullet
        for b_data in state.get("bullets", []):
            owner_id = b_data["owner"]
            owner = next((t for t in self.world.tanks if t.tank_id == owner_id), None)
            b = Bullet(b_data["x"], b_data["y"], b_data["dir"], owner=owner)
            self.world.add_object(b)
                
        # 3. Sync Walls
        d_walls = set(state.get("d_walls", []))
        if d_walls:
            print(f"[Client] Applying {len(d_walls)} destroyed walls: {list(d_walls)[:5]}...")
        for idx, wall in enumerate(self.world.walls):
            if idx in d_walls:
                wall.active = False
                wall.visible = False
            else:
                wall.active = True
                wall.visible = True
        
        # Apply wall type changes (for Shovel effect)
        c_walls = state.get("c_walls", [])
        for wall_data in c_walls:
            idx = wall_data["idx"]
            new_type = wall_data["type"]
            if idx < len(self.world.walls):
                wall = self.world.walls[idx]
                if wall.wall_type != new_type:
                    wall.wall_type = new_type
                    # Reload wall image
                    from src.utils.resource_manager import resource_manager
                    wall.image = resource_manager.get_wall_image(new_type)

        # 4. Sync Explosions
        self.world.explosions.clear()
        from src.game_engine.game_world import Explosion
        for exp_data in state.get("exps", []):
            exp = Explosion(exp_data["x"] + exp_data["r"], exp_data["y"] + exp_data["r"], exp_data["r"], exp_data["d"])
            exp.elapsed = exp_data["e"]
            self.world.add_object(exp)
            
        # 5. Sync Stars
        self.world.stars.clear()
        from src.game_engine.game_world import Star
        for star_data in state.get("stars", []):
            star = Star(star_data["x"] + 25, star_data["y"] + 25, star_data["d"])  # x,y passed to init are center-25, so we reverse it or just pass correct coords
            # Wait, Star init takes x,y as top-left?
            # Star(x, y) calls super(x-25, y-25) if we look at previous edit?
            # Let's check Star.__init__ in game_world.py
            # It was: def __init__(self, x, y, ...): super().__init__(x-25, y-25, 50, 50)
            # So x,y passed to __init__ are the CENTER coordinates.
            # In encode_state, we sent star.x, star.y which are TOP-LEFT coordinates (from GameObject).
            # So we need to convert back to center for Star constructor, OR modify Star constructor, OR just set properties.
            # Easiest: Create Star and set properties.
            # But Star.__init__ loads frames.
            # Let's pass center coordinates: x + width/2, y + height/2.
            # Star width is 50. So center is x+25, y+25.
            star = Star(star_data["x"] + 25, star_data["y"] + 25, star_data["d"])
            star.elapsed = star_data["e"]
            self.world.add_object(star)

        # 6. Sync Respawn System
        respawn_data = state.get("respawn", {})
        if respawn_data:
            # Update lives
            remote_lives = respawn_data.get("lives", {})
            self.world.tank_lives = {int(k): v for k, v in remote_lives.items()}
            
            # Update timers
            remote_timers = respawn_data.get("timers", {})
            self.world.respawn_timers = {int(k): v for k, v in remote_timers.items()}
                
        # 6. Meta
        meta = state.get("meta", {})
        self.world.game_over = meta.get("over", False)
        self.world.winner = meta.get("win")
        
        # 同步关卡模式特殊条件
        if meta.get("game_mode") == "level":
            self.world.game_mode = meta.get("game_mode")
            self.world.level_number = meta.get("level_number")
            self.world.time_limit = meta.get("time_limit")
            self.world.time_remaining = meta.get("time_remaining")
            self.world.score_target = meta.get("score_target")
            self.world.current_score = meta.get("current_score")
        
        # 同步混战模式得分
        if meta.get("player_scores"):
            self.world.player_scores = dict(meta["player_scores"])
        
        # 7. Sync Props
        if hasattr(self.world, 'prop_manager'):
            # Clear existing props (use empty() for sprite groups)
            self.world.prop_manager.props.empty()
            
            # Recreate props from state
            from src.items.prop import Prop
            for prop_data in state.get("props", []):
                prop = Prop(prop_data["x"], prop_data["y"], prop_data["type"])
                self.world.prop_manager.props.add(prop)

        # 8. Sync Events (for client-side video playback)
        # Add events to world's event queue so they can be consumed by game engine
        remote_events = state.get("events", [])
        if remote_events and hasattr(self.world, 'events'):
            # Append remote events to world's event queue
            # These will be consumed by game engine's _consume_game_events()
            if len(remote_events) > 0:
                print(f"[Client] 接收到 {len(remote_events)} 个事件: {[e.get('type', 'unknown') for e in remote_events]}")
            for event in remote_events:
                self.world.events.append(event)

    def _apply_level_effects(self, tank):
        """根据坦克等级应用效果（速度、能力等）"""
        from src.config.game_config import config
        if tank.tank_type != 'player':
            return
        
        # 应用速度效果
        if tank.level >= config.LEVEL_1_THRESHOLD:
            tank.speed = config.TANK_UPGRADED_SPEED
        else:
            tank.speed = config.TANK_BASE_SPEED
        
        # 应用其他等级效果
        tank.steel_breaker = (tank.level >= config.LEVEL_2_THRESHOLD)
        tank.grass_cutter = (tank.level >= config.LEVEL_3_THRESHOLD)
        
        # 重新加载图片以反映等级变化
        if hasattr(tank, '_load_tank_images'):
            tank.images = tank._load_tank_images()
            if tank.images and tank.images.get(tank.direction):
                tank.current_image = tank.images[tank.direction][0]

