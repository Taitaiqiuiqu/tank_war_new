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
        self.latest_snapshot = self.encode_state()

    def encode_state(self) -> dict:
        """生成完整的世界状态快照"""
        if not self.world:
            return {}
            
        tanks = []
        my_tank_data = None  # Separate data for client's own tank
        
        for tank in self.world.tanks:
            if tank.active:
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
                    "is_on_river": getattr(tank, "is_on_river", False)
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
            "meta": {
                "over": self.world.game_over,
                "win": self.world.winner
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
            tid = t_data["id"]
            
            # Find tank by ID
            tank = next((t for t in self.world.tanks if t.tank_id == tid), None)
            if tank:
                # For local player: only update critical state (health, active), skip position (client-side prediction)
                if local_player_id and tid == local_player_id:
                    # Only sync critical state that client can't predict
                    tank.health = t_data.get("hp", 100)
                    tank.shield_active = t_data["shield"]
                    tank.level = t_data.get("level", 0)
                    tank.has_boat = t_data.get("has_boat", False)
                    tank.is_on_river = t_data.get("is_on_river", False)
                    
                    # Special Case: Respawn / Teleport
                    # If tank was inactive (dead) and now active, OR position difference is huge -> Force Sync
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
                        tank.direction = t_data["dir"]
                        tank.rect.topleft = (tank.x, tank.y)
                        tank.active = True
                        tank.visible = True
                    
                    # Don't override position/direction for local player (client-side prediction) normally
                else:
                    # For remote players: full state sync
                    tank.x = t_data["x"]
                    tank.y = t_data["y"]
                    tank.direction = t_data["dir"]
                    tank.shield_active = t_data["shield"]
                    tank.rect.topleft = (tank.x, tank.y)
                    
                    # Update animation based on velocity
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
                    tank.level = t_data.get("level", 0)
                    tank.has_boat = t_data.get("has_boat", False)
                    tank.is_on_river = t_data.get("is_on_river", False)
                
                # Always mark as active if in remote state
                tank.active = True
                tank.visible = True
            else:
                # Spawn new tank
                new_tank = self.world.spawn_tank(t_data["type"], tid, (t_data["x"], t_data["y"]), skin_id=t_data.get("skin", 1))
                new_tank.direction = t_data["dir"]
                if new_tank.images[new_tank.direction]:
                    new_tank.current_image = new_tank.images[new_tank.direction][0]
        
        # Disable missing tanks (including local player if dead!)
        for tank in self.world.tanks:
            if tank.tank_id not in remote_tanks:
                # Debug log for tank disabling
                if tank.tank_type == "player":
                    print(f"[Client] Disabling tank {tank.tank_id} (Not in remote). Local Player ID: {local_player_id}")
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
        
        # 7. Sync Props
        if hasattr(self.world, 'prop_manager'):
            # Clear existing props (use empty() for sprite groups)
            self.world.prop_manager.props.empty()
            
            # Recreate props from state
            from src.items.prop import Prop
            for prop_data in state.get("props", []):
                prop = Prop(prop_data["x"], prop_data["y"], prop_data["type"])
                self.world.prop_manager.props.add(prop)

