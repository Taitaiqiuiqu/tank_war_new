
import unittest
from src.state_sync.state_manager import StateManager
from src.game_engine.game_world import GameWorld
from src.game_engine.tank import Tank

class TestTankDestructionSync(unittest.TestCase):
    def setUp(self):
        self.world = GameWorld(800, 600)
        self.state_manager = StateManager()
        self.state_manager.attach_world(self.world)
        
        # Setup local player
        self.local_player_id = 1
        self.state_manager.local_player_id = self.local_player_id
        
        # Spawn local player tank
        self.player_tank = self.world.spawn_tank("player", tank_id=self.local_player_id, position=(100, 100))
        self.assertTrue(self.player_tank.active)
        
    def test_local_player_destruction(self):
        # Simulate receiving a state where the local player is MISSING (destroyed on server)
        # The state only contains an enemy tank
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
        self.state_manager.decode_state(remote_state)
        
        # Check if local player tank is still active
        # CURRENT BEHAVIOR: It should remain active because of the bug
        print(f"Player Tank Active: {self.player_tank.active}")
        
        # If the bug exists, this assertion might fail if I expect False, 
        # but here I want to demonstrate the bug, so I expect True for now, 
        # or I can assert False and see it fail.
        # I will assert False to confirm the bug causes a failure.
        self.assertFalse(self.player_tank.active, "Local player tank should be inactive if missing from server state")

if __name__ == '__main__':
    unittest.main()
