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
                    "skin": getattr(tank, "skin_id", 1)
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
                
        walls = []
        # Optimization: Only send destroyed walls or changes? 
        # For simplicity, we assume static map for now, or send all walls if dynamic.
        # But sending 100+ walls every frame is bad. 
        # Let's assume walls are static for this MVP, or only sync destroyed ones.
        # Better: Send wall states (active/inactive) as a bitmask or list of destroyed indices.
        # For now, let's just sync tanks and bullets for smooth movement.
        # Walls can be synced less frequently or via events.
        # Let's stick to the plan: "Serialize Tanks... Bullets... Walls".
        # To avoid huge packets, we'll only send walls that are *inactive* (destroyed).
        destroyed_walls = []
        for idx, wall in enumerate(self.world.walls):
            if not wall.active:
                destroyed_walls.append(idx)
        
        if destroyed_walls:
            print(f"[Host] Encoding {len(destroyed_walls)} destroyed walls: {destroyed_walls[:5]}...")
            print(f"[Host] Total walls: {len(self.world.walls)}")
                
        # 4. Sync Explosions
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

        return {
            "ts": time.time(),
            "tanks": tanks,
            "my_tank": my_tank_data,  # Client's own tank for reconciliation
            "bullets": bullets,
            "d_walls": destroyed_walls,
            "exps": explosions,
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
            
            # Skip local player (handled by client-side prediction)
            if local_player_id and tid == local_player_id:
                continue
            
            # Find tank by ID
            tank = next((t for t in self.world.tanks if t.tank_id == tid), None)
            if tank:
                # Update position and state
                tank.x = t_data["x"]
                tank.y = t_data["y"]
                tank.direction = t_data["dir"]
                tank.shield_active = t_data["shield"]
                tank.active = True
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
            else:
                # Spawn new tank
                new_tank = self.world.spawn_tank(t_data["type"], tid, (t_data["x"], t_data["y"]), skin_id=t_data.get("skin", 1))
                new_tank.direction = t_data["dir"]
                if new_tank.images[new_tank.direction]:
                    new_tank.current_image = new_tank.images[new_tank.direction][0]
        
        # Disable missing tanks
        for tank in self.world.tanks:
            if tank.tank_id not in remote_tanks:
                tank.active = False
                
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
            print(f"[Client] Total walls: {len(self.world.walls)}")
        for idx, wall in enumerate(self.world.walls):
            if idx in d_walls:
                wall.active = False
                wall.visible = False
            else:
                wall.active = True
                wall.visible = True

        # 4. Sync Explosions
        self.world.explosions.clear()
        from src.game_engine.game_world import Explosion
        for exp_data in state.get("exps", []):
            exp = Explosion(exp_data["x"] + exp_data["r"], exp_data["y"] + exp_data["r"], exp_data["r"], exp_data["d"])
            exp.elapsed = exp_data["e"]
            self.world.add_object(exp)
                
        # 5. Meta
        meta = state.get("meta", {})
        self.world.game_over = meta.get("over", False)
        self.world.winner = meta.get("win")
