
import pygame
from src.state_sync.state_manager import StateManager
from src.game_engine.game_world import GameWorld
from src.game_engine.tank import Tank
import traceback

try:
    pygame.init()
    pygame.display.set_mode((100, 100)) # Minimal display for image loading

    world = GameWorld(800, 600)
    state_manager = StateManager()
    state_manager.attach_world(world)
    
    # Setup local player
    local_player_id = 1
    state_manager.local_player_id = local_player_id
    
    # Spawn local player tank
    player_tank = world.spawn_tank("player", tank_id=local_player_id, position=(100, 100))
    print(f"Initial Active: {player_tank.active}")
    
    # Simulate receiving a state where the local player is MISSING (destroyed on server)
    remote_state = {
        "tanks": [
            {
                "id": 2,
                "type": "enemy",
                "x": 200,
                "y": 200,
                "dir": 0,
                "vx": 0,
                "vy": 0,
                "hp": 100,
                "shield": False
            }
        ],
        "bullets": [],
        "d_walls": [],
        "exps": [],
        "meta": {}
    }
    
    # Decode state
    state_manager.decode_state(remote_state)
    
    print(f"Final Active: {player_tank.active}")
    
    if not player_tank.active:
        print("TEST PASSED: Tank is inactive.")
    else:
        print("TEST FAILED: Tank is still active.")

except Exception:
    traceback.print_exc()
finally:
    pygame.quit()
