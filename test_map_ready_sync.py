"""
Test script to verify map and ready state synchronization
"""

import unittest
from src.network.network_manager import NetworkManager

class TestMapAndReadySync(unittest.TestCase):
    def test_network_manager_methods(self):
        """Test that new network methods exist"""
        nm = NetworkManager()
        
        # Check methods exist
        self.assertTrue(hasattr(nm, 'send_map_selection'))
        self.assertTrue(hasattr(nm, 'send_ready_state'))
        self.assertTrue(hasattr(nm, 'send_game_start'))
        
        # Check send_game_start signature accepts map_name
        import inspect
        sig = inspect.signature(nm.send_game_start)
        params = list(sig.parameters.keys())
        self.assertIn('map_name', params)
        
        print("✓ NetworkManager methods verified")
    
    def test_game_engine_setup_multiplayer(self):
        """Test that setup_multiplayer_world accepts map_name"""
        from src.game_engine.game import GameEngine
        import inspect
        
        # Check method signature
        sig = inspect.signature(GameEngine.setup_multiplayer_world)
        params = list(sig.parameters.keys())
        self.assertIn('map_name', params)
        
        print("✓ GameEngine.setup_multiplayer_world signature verified")

if __name__ == '__main__':
    unittest.main()
