import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock pygame and pygame_gui BEFORE importing modules that use them
sys.modules['pygame'] = MagicMock()
sys.modules['pygame_gui'] = MagicMock()
sys.modules['pygame_gui.elements'] = MagicMock()
sys.modules['pygame_gui.windows'] = MagicMock()

# Now we can import the class to test
# We need to mock BaseScreen and resource_manager as well since they are imported
with patch('src.ui.screen_manager.BaseScreen') as MockBaseScreen, \
     patch('src.utils.resource_manager.resource_manager') as MockResourceManager:
    
    from src.ui.map_editor_screen import MapEditorScreen

    class TestMapEditorSpawns(unittest.TestCase):
        def setUp(self):
            self.surface = MagicMock()
            self.context = MagicMock()
            self.ui_manager = MagicMock()
            self.editor = MapEditorScreen(self.surface, self.context, self.ui_manager)
            
            # Reset spawns for testing
            self.editor.player_spawns = []
            self.editor.enemy_spawns = []
            self.editor.walls = []

        def test_add_multiple_player_spawns(self):
            self.editor.current_tool = MapEditorScreen.TOOL_PLAYER_SPAWN
            
            # Click at (100, 190) -> Grid (100, 100) (since y offset is 90)
            # 190 - 90 = 100. 100 // 50 * 50 = 100.
            self.editor._handle_click((100, 190))
            self.assertEqual(len(self.editor.player_spawns), 1)
            self.assertEqual(self.editor.player_spawns[0], [100, 100])
            
            # Click at (200, 190) -> Grid (200, 100)
            self.editor._handle_click((200, 190))
            self.assertEqual(len(self.editor.player_spawns), 2)
            self.assertEqual(self.editor.player_spawns[1], [200, 100])
            
            # Click again at same spot -> Should not add duplicate
            self.editor._handle_click((200, 190))
            self.assertEqual(len(self.editor.player_spawns), 2)

        def test_add_multiple_enemy_spawns(self):
            self.editor.current_tool = MapEditorScreen.TOOL_ENEMY_SPAWN
            
            self.editor._handle_click((100, 190))
            self.assertEqual(len(self.editor.enemy_spawns), 1)
            
            self.editor._handle_click((200, 190))
            self.assertEqual(len(self.editor.enemy_spawns), 2)

        def test_remove_spawn_points(self):
            # Setup
            self.editor.player_spawns = [[100, 100], [200, 100]]
            self.editor.enemy_spawns = [[300, 100]]
            
            # Remove player spawn at [100, 100]
            # Click at (110, 200) -> 200-90=110 -> 100
            self.editor._remove_item_at((110, 200))
            
            self.assertEqual(len(self.editor.player_spawns), 1)
            self.assertEqual(self.editor.player_spawns[0], [200, 100])
            
            # Remove enemy spawn
            self.editor._remove_item_at((310, 200))
            self.assertEqual(len(self.editor.enemy_spawns), 0)

        def test_overlap_protection(self):
            self.editor.player_spawns = [[100, 100]]
            
            # Try to add enemy spawn at same location
            self.editor.current_tool = MapEditorScreen.TOOL_ENEMY_SPAWN
            self.editor._handle_click((100, 190))
            
            # Should not add
            self.assertEqual(len(self.editor.enemy_spawns), 0)
            
            # Try to add wall at same location
            self.editor.current_tool = MapEditorScreen.TOOL_BRICK
            self.editor._handle_click((100, 190))
            
            # Should not add wall
            self.assertEqual(len(self.editor.walls), 0)

if __name__ == '__main__':
    unittest.main()
