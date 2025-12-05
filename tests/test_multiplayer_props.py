import unittest
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pygame
from src.game_engine.game_world import GameWorld
from src.game_engine.tank import Tank
from src.game_engine.wall import Wall
from src.state_sync.state_manager import StateManager

class TestMultiplayerPropSync(unittest.TestCase):
    def setUp(self):
        pygame.init()
        # Mock display for image loading
        pygame.display.set_mode((1, 1))
        self.world = GameWorld(800, 600)
        self.state_manager = StateManager()
        self.state_manager.attach_world(self.world)
        
    def test_prop_sync(self):
        """Test that props are synced in network state"""
        # Spawn a prop
        self.world.prop_manager.spawn_prop(100, 100, prop_type=1)
        
        # Encode state
        state = self.state_manager.encode_state()
        
        # Check props in state
        self.assertIn("props", state)
        self.assertEqual(len(state["props"]), 1)
        self.assertEqual(state["props"][0]["type"], 1)
        self.assertEqual(state["props"][0]["x"], 100)
        self.assertEqual(state["props"][0]["y"], 100)
        
    def test_tank_level_sync(self):
        """Test that tank level is synced"""
        player = self.world.spawn_tank("player", tank_id=1, position=(100, 100))
        player.level = 2
        player.has_boat = True
        
        # Encode state
        state = self.state_manager.encode_state()
        
        # Check tank state
        tank_data = next((t for t in state["tanks"] if t["id"] == 1), None)
        self.assertIsNotNone(tank_data)
        self.assertEqual(tank_data["level"], 2)
        self.assertTrue(tank_data["has_boat"])
        
    def test_wall_type_sync(self):
        """Test that wall type changes are synced"""
        # Create walls
        self.world.spawn_wall(100, 100, Wall.BRICK)
        self.world.spawn_wall(150, 100, Wall.STEEL)
        
        # Encode state
        state = self.state_manager.encode_state()
        
        # Check wall changes
        self.assertIn("c_walls", state)
        # Should have 2 active walls
        self.assertEqual(len(state["c_walls"]), 2)

if __name__ == '__main__':
    unittest.main()
