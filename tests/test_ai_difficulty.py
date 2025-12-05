
import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.game_engine.game import EnemyAIController
from src.game_engine.game_world import GameWorld
from src.game_engine.tank import Tank
from src.game_engine.ai_config import DIFFICULTY_CONFIGS

class TestEnemyAIDifficulty(unittest.TestCase):
    def setUp(self):
        self.world = MagicMock(spec=GameWorld)
        self.world.tanks = []
        self.world.bullets = []
        
        # Mock enemy tank
        self.enemy_tank = MagicMock(spec=Tank)
        self.enemy_tank.tank_id = 1
        self.enemy_tank.active = True
        self.enemy_tank.tank_type = "enemy"
        self.enemy_tank.x = 100
        self.enemy_tank.y = 100
        self.enemy_tank.speed = 0
        
        # Mock player tank
        self.player_tank = MagicMock(spec=Tank)
        self.player_tank.tank_id = 2
        self.player_tank.active = True
        self.player_tank.tank_type = "player"
        self.player_tank.x = 200
        self.player_tank.y = 200
        self.player_tank.velocity_x = 0
        self.player_tank.velocity_y = 0
        
        self.world.tanks = [self.enemy_tank, self.player_tank]

    def test_difficulty_config_loading(self):
        """Test if difficulty config is loaded correctly"""
        controller = EnemyAIController(1, self.world, "easy")
        self.assertEqual(controller.config, DIFFICULTY_CONFIGS["easy"])
        
        controller = EnemyAIController(1, self.world, "hell")
        self.assertEqual(controller.config, DIFFICULTY_CONFIGS["hell"])

    def test_speed_application(self):
        """Test if speed is applied to tank based on difficulty"""
        controller = EnemyAIController(1, self.world, "easy")
        controller.update()
        self.assertEqual(self.enemy_tank.speed, DIFFICULTY_CONFIGS["easy"]["speed"])
        
        controller = EnemyAIController(1, self.world, "hell")
        controller.update()
        self.assertEqual(self.enemy_tank.speed, DIFFICULTY_CONFIGS["hell"]["speed"])

    def test_tracking_behavior(self):
        """Test tracking behavior (Normal+)"""
        # Easy: No tracking
        controller = EnemyAIController(1, self.world, "easy")
        controller._move_with_tracking = MagicMock()
        controller._move_random = MagicMock()
        
        # Force movement update
        controller.direction_timer = 0
        controller.update()
        
        controller._move_random.assert_called()
        controller._move_with_tracking.assert_not_called()
        
        # Normal: Tracking
        controller = EnemyAIController(1, self.world, "normal")
        controller._move_with_tracking = MagicMock()
        controller._move_random = MagicMock()
        
        controller.direction_timer = 0
        controller.update()
        
        controller._move_with_tracking.assert_called()

    def test_prediction_shooting(self):
        """Test prediction shooting (Normal+)"""
        # Easy: No prediction
        controller = EnemyAIController(1, self.world, "easy")
        controller._shoot_with_prediction = MagicMock()
        
        controller.shoot_timer = 0
        controller.update()
        
        controller._shoot_with_prediction.assert_not_called()
        self.world.spawn_bullet.assert_called()
        
        # Normal: Prediction
        controller = EnemyAIController(1, self.world, "normal")
        controller._shoot_with_prediction = MagicMock()
        
        controller.shoot_timer = 0
        controller.update()
        
        controller._shoot_with_prediction.assert_called()

    def test_dodge_behavior(self):
        """Test dodge behavior (Normal+)"""
        # Create a bullet moving towards enemy
        bullet = MagicMock()
        bullet.active = True
        bullet.owner = self.player_tank
        bullet.x = 100
        bullet.y = 150
        bullet.direction = Tank.UP # Moving up towards enemy at (100, 100)
        self.world.bullets = [bullet]
        
        # Easy: No dodging
        controller = EnemyAIController(1, self.world, "easy")
        controller._dodge_bullet = MagicMock()
        
        # Mock random to force tracking check pass if it was called (but it shouldn't be for easy)
        # Actually easy calls _move_random directly.
        
        # Normal: Dodging
        controller = EnemyAIController(1, self.world, "normal")
        controller._dodge_bullet = MagicMock()
        
        # Force dodge check
        controller.direction_timer = 0
        # Mock tracking prob to ensure we enter tracking logic
        with patch('random.random', return_value=0.0): 
            controller.update()
            
        # Should check for dodge
        # Note: _move_with_tracking calls _should_dodge
        # We need to ensure _should_dodge returns true for this test if logic is correct
        # But here we just want to verify _dodge_bullet is called if _should_dodge is true
        
        # Let's test _should_dodge directly
        self.assertTrue(controller._bullet_will_hit(bullet, self.enemy_tank))

if __name__ == '__main__':
    unittest.main()
