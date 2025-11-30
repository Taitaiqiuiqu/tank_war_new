
import unittest
import pygame
from src.game_engine.tank import Tank
from src.game_engine.game_world import GameWorld
from src.state_sync.state_manager import StateManager

class TestTankSkinSync(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((100, 100))
        
    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        self.world = GameWorld(800, 600)
        self.state_manager = StateManager()
        self.state_manager.attach_world(self.world)
        
    def test_tank_skin_separation(self):
        # Spawn a tank with logic ID 1 and skin ID 3
        tank = self.world.spawn_tank("player", tank_id=1, skin_id=3, position=(100, 100))
        
        self.assertEqual(tank.tank_id, 1)
        self.assertEqual(tank.skin_id, 3)
        
        # Encode state
        state = self.state_manager.encode_state()
        tank_data = state["tanks"][0]
        
        self.assertEqual(tank_data["id"], 1)
        self.assertEqual(tank_data["skin"], 3)
        
    def test_decode_skin(self):
        # Simulate receiving state with skin info
        remote_state = {
            "tanks": [
                {
                    "id": 2,
                    "type": "player",
                    "x": 200,
                    "y": 200,
                    "dir": 0,
                    "vx": 0,
                    "vy": 0,
                    "hp": 100,
                    "shield": False,
                    "skin": 4
                }
            ],
            "bullets": [],
            "d_walls": [],
            "exps": [],
            "meta": {}
        }
        
        self.state_manager.decode_state(remote_state)
        
        # Check if tank was spawned with correct skin
        tank = next((t for t in self.world.tanks if t.tank_id == 2), None)
        self.assertIsNotNone(tank)
        self.assertEqual(tank.skin_id, 4)

if __name__ == '__main__':
    unittest.main()
