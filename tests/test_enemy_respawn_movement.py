import unittest
import pygame
from src.game_engine.game import GameEngine, EnemyAIController
from src.game_engine.tank import Tank

class TestEnemyRespawnMovement(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.engine = GameEngine()
        # Setup single player world
        self.engine._setup_single_player_world()
        
    def tearDown(self):
        pygame.quit()

    def test_enemy_respawn_movement(self):
        # 1. Get the initial enemy tank
        initial_enemy = next((t for t in self.engine.game_world.tanks if t.tank_type == 'enemy'), None)
        self.assertIsNotNone(initial_enemy, "Initial enemy should exist")
        initial_id = initial_enemy.tank_id
        
        # 2. Simulate updates to ensure it moves (AI update)
        # Force AI update
        self.engine._update_enemy_ai()
        self.engine.game_world.update()
        
        # 3. Destroy the enemy
        initial_enemy.take_damage(1000) # Kill it
        self.engine.game_world.update() # Process destruction
        
        # Verify it's gone or inactive
        self.assertFalse(initial_enemy.active, "Enemy should be inactive after taking damage")
        
        # 4. Simulate time passing for respawn (90 frames + buffer)
        print("Simulating respawn delay...")
        for _ in range(120):
            self.engine.game_world.update()
            
        # 5. Check for new enemy
        new_enemy = next((t for t in self.engine.game_world.tanks if t.tank_type == 'enemy' and t.active), None)
        self.assertIsNotNone(new_enemy, "New enemy should have respawned")
        self.assertEqual(new_enemy.tank_id, initial_id, "Respawned tank should have same ID")
        self.assertNotEqual(new_enemy, initial_enemy, "Respawned tank should be a new instance")
        
        # 6. Track position to verify movement
        start_pos = (new_enemy.x, new_enemy.y)
        moved = False
        
        print("Simulating movement after respawn...")
        for _ in range(200): # Give it enough time to move
            self.engine._update_enemy_ai()
            self.engine.game_world.update()
            if (new_enemy.x, new_enemy.y) != start_pos:
                moved = True
                break
                
        self.assertTrue(moved, "Respawned enemy should move")

if __name__ == '__main__':
    unittest.main()
