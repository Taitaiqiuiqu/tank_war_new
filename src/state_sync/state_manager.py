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
        for tank in self.world.tanks:
            if tank.active:
                tanks.append({
                    "id": tank.tank_id,
                    "type": tank.tank_type,
                    "x": tank.x,
                    "y": tank.y,
                    "dir": tank.direction,
                    "hp": getattr(tank, "health", 100),
                    "shield": tank.shield_active
                })
                
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
                
        return {
            "ts": time.time(),
            "tanks": tanks,
            "bullets": bullets,
            "d_walls": destroyed_walls,
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
        
        # Update existing or spawn new
        for t_data in remote_tanks.values():
            tid = t_data["id"]
            # Find tank by ID
            tank = next((t for t in self.world.tanks if t.tank_id == tid), None)
            if tank:
                # Interpolation could go here, but for now direct set
                tank.x = t_data["x"]
                tank.y = t_data["y"]
                tank.direction = t_data["dir"]
                tank.shield_active = t_data["shield"]
                tank.active = True
            else:
                # Spawn new tank
                new_tank = self.world.spawn_tank(t_data["type"], tid, (t_data["x"], t_data["y"]))
                new_tank.direction = t_data["dir"]
        
        # Disable missing tanks (except local player? No, Client is dumb terminal)
        for tank in self.world.tanks:
            if tank.tank_id not in remote_tanks:
                tank.active = False # Or destroy?
                
        # 2. Sync Bullets (Re-create all for simplicity, or pool)
        # Clearing and re-adding is easiest for sync but heavy.
        # Let's try to match? No, bullets are transient.
        # Simple approach: Clear all bullets and spawn from state.
        self.world.bullets.clear() # This might kill local bullets visual effects?
        # Ideally we want to identify bullets, but they don't have IDs.
        # For MVP, just replacing is fine.
        for b_data in state.get("bullets", []):
            # We need an owner for the bullet, find it by ID
            owner_id = b_data["owner"]
            owner = next((t for t in self.world.tanks if t.tank_id == owner_id), None)
            if owner:
                b = self.world.spawn_bullet(owner)
                if b:
                    b.x = b_data["x"]
                    b.y = b_data["y"]
                    b.direction = b_data["dir"]
            else:
                # Owner might be dead or unknown, just spawn generic bullet?
                # Or skip.
                pass
                
        # 3. Sync Walls
        d_walls = set(state.get("d_walls", []))
        for idx, wall in enumerate(self.world.walls):
            if idx in d_walls:
                wall.active = False
            else:
                wall.active = True
                
        # 4. Meta
        meta = state.get("meta", {})
        self.world.game_over = meta.get("over", False)
        self.world.winner = meta.get("win")

