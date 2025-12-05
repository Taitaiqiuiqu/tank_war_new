import unittest
import pygame
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.game_engine.game_world import GameWorld
from src.game_engine.tank import Tank
from src.game_engine.wall import Wall
from src.items.prop import Prop

class TestProps(unittest.TestCase):
    def setUp(self):
        pygame.init()
        # Mock display for image loading
        pygame.display.set_mode((1, 1))
        self.world = GameWorld(800, 600)
        self.player = self.world.spawn_tank("player", tank_id=1, position=(100, 100))
        
    def test_star_upgrade(self):
        """Test Star prop upgrades player level"""
        initial_level = self.player.level
        self.world._apply_prop_effect(self.player, 1) # Star
        self.assertEqual(self.player.level, initial_level + 1)
        
    def test_pistol_upgrade(self):
        """Test Pistol prop upgrades"""
        self.player.level = 0
        self.world._apply_prop_effect(self.player, 7) # Pistol
        self.assertEqual(self.player.level, 2)
        
        self.player.level = 2
        self.world._apply_prop_effect(self.player, 7) # Pistol
        self.assertEqual(self.player.level, 3)
        
    def test_helmet_shield(self):
        """Test Helmet activates shield"""
        self.player.shield_active = False
        self.world._apply_prop_effect(self.player, 5) # Helmet
        self.assertTrue(self.player.shield_active)
        self.assertEqual(self.player.shield_duration, self.player.max_shield_duration)
        
    def test_boat_logic(self):
        """Test Boat enables water crossing"""
        self.assertFalse(self.player.has_boat)
        self.world._apply_prop_effect(self.player, 8) # Boat
        self.assertTrue(self.player.has_boat)
        self.assertTrue(self.player.boat_shield_active)
        
    def test_clock_freeze(self):
        """Test Clock freezes enemies"""
        self.world.freeze_enemies_timer = 0
        self.world._apply_prop_effect(self.player, 3) # Clock
        self.assertEqual(self.world.freeze_enemies_timer, 600)
        
    def test_shovel_fortify(self):
        """Test Shovel fortifies base"""
        # Create base and surrounding walls
        base = self.world.spawn_wall(400, 550, Wall.BASE)
        brick = self.world.spawn_wall(350, 550, Wall.BRICK)
        
        self.world._apply_prop_effect(self.player, 4) # Shovel
        
        # Check if brick became steel
        new_wall = next((w for w in self.world.walls if w.x == 350 and w.y == 550), None)
        self.assertIsNotNone(new_wall)
        self.assertEqual(new_wall.wall_type, Wall.STEEL)
        self.assertTrue(self.world.base_fortified)
        
        # Test restore
        self.world._restore_base()
        restored_wall = next((w for w in self.world.walls if w.x == 350 and w.y == 550), None)
        self.assertEqual(restored_wall.wall_type, Wall.BRICK)

if __name__ == '__main__':
    unittest.main()
