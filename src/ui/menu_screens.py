# 必须在导入pygame_gui之前初始化i18n
import src.ui.init_i18n

import pygame
import pygame_gui
from pygame_gui.elements import UIButton, UILabel, UISelectionList, UIImage, UITextEntryLine, UIDropDownMenu
from pygame_gui.windows import UIMessageWindow

from src.ui.screen_manager import BaseScreen, ScreenContext
from src.ui.ui_components import UIManagerWrapper
from src.utils.resource_manager import resource_manager
from src.utils.map_loader import map_loader
from src.utils.level_progress import load_level_progress


class MainMenuScreen(BaseScreen):
    """主菜单屏幕"""

    def on_enter(self):
        super().on_enter()
        
        # 创建主菜单按钮
        center_x = self.surface.get_width() // 2
        center_y = self.surface.get_height() // 2
        btn_width = 200
        btn_height = 50
        spacing = 20
        
        self.btn_single = UIButton(
            relative_rect=pygame.Rect((center_x - btn_width // 2, center_y - 100), (btn_width, btn_height)),
            text='单机模式',
            manager=self.manager
        )
        
        self.btn_multi = UIButton(
            relative_rect=pygame.Rect((center_x - btn_width // 2, center_y - 100 + (btn_height + spacing) * 1), (btn_width, btn_height)),
            text='联机模式',
            manager=self.manager
        )
        
        self.btn_settings = UIButton(
            relative_rect=pygame.Rect((center_x - btn_width // 2, center_y - 100 + (btn_height + spacing) * 2), (btn_width, btn_height)),
            text='设置',
            manager=self.manager
        )
        
        self.btn_map_editor = UIButton(
            relative_rect=pygame.Rect((center_x - btn_width // 2, center_y - 100 + (btn_height + spacing) * 3), (btn_width, btn_height)),
            text='地图编辑器',
            manager=self.manager
        )
        
        self.btn_exit = UIButton(
            relative_rect=pygame.Rect((center_x - btn_width // 2, center_y - 100 + (btn_height + spacing) * 4), (btn_width, btn_height)),
            text='退出游戏',
            manager=self.manager
        )

    def handle_event(self, event: pygame.event.Event):
        super().handle_event(event)
        
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.btn_single:
                # 进入单机模式选择界面
                self.context.next_state = "single_mode_select"
                
            elif event.ui_element == self.btn_multi:
                self.context.next_state = "lobby"
                
            elif event.ui_element == self.btn_settings:
                self.context.next_state = "settings"
                
            elif event.ui_element == self.btn_map_editor:
                self.context.next_state = "map_editor"
                
            elif event.ui_element == self.btn_exit:
                pygame.event.post(pygame.event.Event(pygame.QUIT))

    def render(self):
        self.surface.fill((30, 30, 30))
        # 绘制标题
        title_surf = self.font.render("坦克大战", True, (255, 215, 0))
        self.surface.blit(title_surf, title_surf.get_rect(center=(self.surface.get_width() // 2, 100)))


class SingleModeSelectScreen(BaseScreen):
    """单机模式选择屏幕"""
    
    def on_enter(self):
        super().on_enter()
        
        center_x = self.surface.get_width() // 2
        center_y = self.surface.get_height() // 2
        btn_width = 200
        btn_height = 50
        spacing = 20
        
        # 标题
        UILabel(
            relative_rect=pygame.Rect((center_x - 100, 100), (200, 30)),
            text="选择游戏模式",
            manager=self.manager,
            object_id="@title"
        )
        
        # 自由模式按钮
        self.btn_free_mode = UIButton(
            relative_rect=pygame.Rect((center_x - btn_width // 2, center_y - 50), (btn_width, btn_height)),
            text='自由模式',
            manager=self.manager
        )
        
        # 关卡模式按钮
        self.btn_level_mode = UIButton(
            relative_rect=pygame.Rect((center_x - btn_width // 2, center_y + 20), (btn_width, btn_height)),
            text='关卡模式',
            manager=self.manager
        )
        
        # 返回按钮
        self.btn_back = UIButton(
            relative_rect=pygame.Rect((center_x - btn_width // 2, center_y + 90), (btn_width, btn_height)),
            text='返回主菜单',
            manager=self.manager
        )
    
    def handle_event(self, event: pygame.event.Event):
        super().handle_event(event)
        
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.btn_free_mode:
                # 进入自由模式设置
                self.context.next_state = "single_setup"
            elif event.ui_element == self.btn_level_mode:
                # 进入关卡选择界面
                self.context.next_state = "level_select"
            elif event.ui_element == self.btn_back:
                # 返回主菜单
                self.context.next_state = "menu"
    
    def render(self):
        self.surface.fill((30, 30, 30))
        # 绘制背景
        pygame.draw.rect(
            self.surface, 
            (40, 40, 40), 
            (self.surface.get_width() // 2 - 180, 30, 360, 300),
            border_radius=10
        )


class SinglePlayerSetupScreen(BaseScreen):
    """单机模式设置屏幕"""
    
    def on_enter(self):
        super().on_enter()
        # Initialize font for statistics display
        self.small_font = pygame.font.SysFont('SimHei', 16)
        
        center_x = self.surface.get_width() // 2
        
        self.tank_id = 1
        self.context.player_tank_id = 1
        
        UILabel(
            relative_rect=pygame.Rect((center_x - 100, 50), (200, 30)),
            text="选择你的坦克",
            manager=self.manager
        )
        
        # Tank Image Display
        self.image_rect = pygame.Rect((center_x - 50, 100), (100, 100))
        self.tank_image_element = None
        self._update_tank_image()
        
        # Selection Buttons
        self.btn_prev = UIButton(
            relative_rect=pygame.Rect((center_x - 160, 130), (100, 40)),
            text='< 上一个',
            manager=self.manager
        )
        
        self.btn_next = UIButton(
            relative_rect=pygame.Rect((center_x + 60, 130), (100, 40)),
            text='下一个 >',
            manager=self.manager
        )
        
        # Map selection section
        UILabel(
            relative_rect=pygame.Rect((center_x - 300, 220), (200, 30)),
            text="选择地图",
            manager=self.manager
        )
        
        # Get available maps
        self._load_available_maps()
        
        # Map selection list (replacing dropdown)
        self.map_selection_list = UISelectionList(
            relative_rect=pygame.Rect((center_x - 300, 260), (200, 120)),
            item_list=self.map_display_names,
            default_selection=self.map_display_names[0],
            manager=self.manager
        )
        
        # Map preview area
        UILabel(
            relative_rect=pygame.Rect((center_x + 50, 220), (200, 30)),
            text="地图预览",
            manager=self.manager
        )
        
        # Preview surface
        self.preview_rect = pygame.Rect((center_x + 50, 260), (200, 120))
        self.preview_surface = pygame.Surface((200, 120))
        self.preview_surface.fill((60, 60, 60))
        
        # Create preview image element
        self.preview_image = UIImage(
            relative_rect=self.preview_rect,
            image_surface=self.preview_surface,
            manager=self.manager
        )
        
        # Update preview with first map
        self._update_map_preview(self.map_names[0])
        
        self.context.selected_map = self.map_names[0]
        
        # Difficulty Selection
        UILabel(
            relative_rect=pygame.Rect((center_x + 50, 130), (100, 30)),
            text="敌人难度",
            manager=self.manager
        )
        
        from src.game_engine.ai_config import get_difficulty_names, get_difficulty_key_by_name, DEFAULT_DIFFICULTY, DIFFICULTY_CONFIGS
        self.difficulty_names = get_difficulty_names()
        default_diff_name = DIFFICULTY_CONFIGS[DEFAULT_DIFFICULTY]["name"]
        
        self.difficulty_dropdown = UIDropDownMenu(
            options_list=self.difficulty_names,
            starting_option=default_diff_name,
            relative_rect=pygame.Rect((center_x + 50, 160), (100, 30)),
            manager=self.manager
        )
        print(f"[DEBUG] Dropdown init: options={self.difficulty_names}, start={default_diff_name}")
        # Set default in context
        self.context.enemy_difficulty = DEFAULT_DIFFICULTY
        
        self.btn_start = UIButton(
            relative_rect=pygame.Rect((center_x - 100, 400), (200, 50)),
            text='开始游戏',
            manager=self.manager
        )
        
        self.btn_back = UIButton(
            relative_rect=pygame.Rect((center_x - 100, 470), (200, 50)),
            text='返回',
            manager=self.manager
        )

    def _update_tank_image(self):
        if self.tank_image_element:
            self.tank_image_element.kill()
            
        # Load tank image (Level 0, UP direction)
        # resource_manager.load_tank_images returns dict[dir][frame]
        images = resource_manager.load_tank_images('player', self.tank_id, 0)
        if images and images.get(0):
            surf = images[0][0]
            # Scale up for UI
            surf = pygame.transform.scale(surf, (100, 100))
        else:
            surf = pygame.Surface((100, 100))
            surf.fill((0, 255, 0))
            
        self.tank_image_element = UIImage(
            relative_rect=self.image_rect,
            image_surface=surf,
            manager=self.manager
        )

    def handle_event(self, event: pygame.event.Event):
        # Note: Do NOT call super().handle_event(event) here!
        # ScreenManager already calls ui_manager.handle_event() before calling this method.
        # Calling super() would process the event twice, causing event.text to become None.
        
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.btn_start:
                self.context.next_state = "game"
                self.context.game_mode = "single"
            elif event.ui_element == self.btn_back:
                self.context.next_state = "single_mode_select"
            elif event.ui_element == self.btn_prev:
                self.tank_id -= 1
                if self.tank_id < 1: self.tank_id = 4
                self.context.player_tank_id = self.tank_id
                self._update_tank_image()
            elif event.ui_element == self.btn_next:
                self.tank_id += 1
                if self.tank_id > 4: self.tank_id = 1
                self.context.player_tank_id = self.tank_id
                self._update_tank_image()
        elif event.type == pygame_gui.UI_SELECTION_LIST_NEW_SELECTION:
            if event.ui_element == self.map_selection_list:
                # Get selected map name from mapping dictionary
                selected_text = event.text
                if hasattr(self, 'map_name_mapping') and selected_text in self.map_name_mapping:
                    selected_map = self.map_name_mapping[selected_text]
                    self.context.selected_map = selected_map
                    # 调试日志
                    print(f"地图选择: {selected_text} -> {selected_map}")
                    # Update preview
                    self._update_map_preview(selected_map)
        elif event.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
            if event.ui_element == self.difficulty_dropdown:
                from src.game_engine.ai_config import get_difficulty_key_by_name
                
                # Fallback to selected_option if event.text is None
                text = event.text if hasattr(event, 'text') and event.text is not None else self.difficulty_dropdown.selected_option
                
                print(f"[DEBUG] Dropdown Event Dict: {event.__dict__}")
                print(f"[DEBUG] Dropdown State: selected={self.difficulty_dropdown.selected_option}, options={self.difficulty_dropdown.options_list}")
                
                if text is None or text == "None":
                    text = "普通"
                
                selected_difficulty = get_difficulty_key_by_name(text)
                self.context.enemy_difficulty = selected_difficulty
                print(f"难度选择: {text} -> {selected_difficulty}")


    def _load_available_maps(self):
        """加载可用地图列表"""
        available_maps = map_loader.get_available_maps()
        
        # Create map display names with metadata and mapping
        self.map_names = []
        self.map_display_names = []
        # 添加映射字典，直接存储显示名称到地图名称的映射
        self.map_name_mapping = {}
        
        # 处理默认地图
        self.map_names.append("default")
        self.map_display_names.append("默认地图")
        self.map_name_mapping["默认地图"] = "default"
        
        # 处理其他地图
        for map_info in available_maps:
            if isinstance(map_info, dict) and "filename" in map_info:
                map_name = map_info["filename"]
                self.map_names.append(map_name)
                
                try:
                    # Try to get map details
                    map_data = map_loader.load_map(map_name)
                    if map_data and 'name' in map_data:
                        # Add map stats to display name
                        wall_count = len(map_data.get('walls', []))
                        display_name = f"{map_data['name']} ({wall_count} 个障碍物)"
                    else:
                        display_name = map_info.get("name", map_name.replace(".json", ""))
                except Exception as e:
                    print(f"加载地图 {map_name} 时出错: {e}")
                    display_name = map_info.get("name", map_name.replace(".json", ""))
                
                self.map_display_names.append(display_name)
                self.map_name_mapping[display_name] = map_name
            elif isinstance(map_info, str):
                # 兼容旧格式
                map_name = map_info
                self.map_names.append(map_name)
                
                if map_name == "default":
                    display_name = "默认地图"
                else:
                    try:
                        map_data = map_loader.load_map(map_name)
                        if map_data and 'name' in map_data:
                            wall_count = len(map_data.get('walls', []))
                            display_name = f"{map_data['name']} ({wall_count} 个障碍物)"
                        else:
                            display_name = map_name
                    except Exception as e:
                        print(f"加载地图 {map_name} 时出错: {e}")
                        display_name = map_name
                
                self.map_display_names.append(display_name)
                self.map_name_mapping[display_name] = map_name
        
        # Ensure we have at least one option
        if not self.map_display_names:
            self.map_display_names = ["默认地图"]
            self.map_names = ["default"]
            self.map_name_mapping = {"默认地图": "default"}
    
    def _update_map_preview(self, map_name):
        """更新地图预览图像"""
        # Clear preview surface
        self.preview_surface.fill((60, 60, 60))
        
        # Default map or empty preview
        if map_name == "default":
            # Draw default map placeholder
            font = pygame.font.SysFont('SimHei', 14)
            text = font.render("默认地图", True, (200, 200, 200))
            self.preview_surface.blit(text, text.get_rect(center=(100, 60)))
        else:
            # Load actual map data and draw preview
            map_data = map_loader.load_map(map_name)
            if map_data and 'walls' in map_data:
                # Calculate scaling factor
                scale_x = 200 / 800  # Map width from 800 to 200
                scale_y = 120 / 600  # Map height from 600 to 120
                
                # Draw walls
                for wall in map_data['walls']:
                    wall_type = wall.get('type', 1)
                    
                    # Calculate scaled position and size
                    x = int(wall['x'] * scale_x)
                    y = int(wall['y'] * scale_y)
                    w = int(50 * scale_x)
                    h = int(50 * scale_y)
                    
                    # Load and draw actual wall image
                    wall_img = resource_manager.get_wall_image(wall_type)
                    if wall_img:
                        scaled_img = pygame.transform.scale(wall_img, (w, h))
                        self.preview_surface.blit(scaled_img, (x, y))
                    else:
                        # Fallback to colored rectangle if image not available
                        if wall_type == 1:  # Brick
                            color = (165, 42, 42)
                        elif wall_type == 2:  # Steel
                            color = (192, 192, 192)
                        elif wall_type == 3:  # Grass
                            color = (0, 128, 0)
                        elif wall_type == 4:  # River
                            color = (0, 0, 128)
                        elif wall_type == 5:  # Base
                            color = (255, 0, 0)
                        else:
                            color = (128, 128, 128)
                        pygame.draw.rect(self.preview_surface, color, (x, y, w, h))
                
                # Draw spawn points with actual tank images
                # Player spawn - use different tank skins (1-4) for different spawn points
                player_spawns = map_data.get('player_spawns', [])
                if player_spawns:
                    for idx, spawn in enumerate(player_spawns):
                        x = int(spawn[0] * scale_x)
                        y = int(spawn[1] * scale_y)
                        tank_id = (idx % 4) + 1  # Cycle through tank skins 1-4
                        
                        # Load player tank image
                        images = resource_manager.load_tank_images('player', tank_id, 0)
                        if images and images.get(0):
                            tank_img = images[0][0]
                            scaled_size = int(30 * scale_x)  # Tank is 30x30
                            scaled_img = pygame.transform.scale(tank_img, (scaled_size, scaled_size))
                            self.preview_surface.blit(scaled_img, (x, y))
                        else:
                            # Fallback to colored circle
                            pygame.draw.circle(self.preview_surface, (0, 255, 0), 
                                              (x + int(15 * scale_x), y + int(15 * scale_y)), 
                                              int(10 * scale_x))
                
                # Enemy spawn - use enemy tank image
                enemy_spawns = map_data.get('enemy_spawns', [])
                if enemy_spawns:
                    for spawn in enemy_spawns:
                        x = int(spawn[0] * scale_x)
                        y = int(spawn[1] * scale_y)
                        
                        # Load enemy tank image
                        images = resource_manager.load_tank_images('enemy', 1, 0)
                        if images and images.get(0):
                            tank_img = images[0][0]
                            scaled_size = int(30 * scale_x)  # Tank is 30x30
                            scaled_img = pygame.transform.scale(tank_img, (scaled_size, scaled_size))
                            self.preview_surface.blit(scaled_img, (x, y))
                        else:
                            # Fallback to colored circle
                            pygame.draw.circle(self.preview_surface, (255, 0, 0), 
                                              (x + int(15 * scale_x), y + int(15 * scale_y)), 
                                              int(10 * scale_x))
        
        # Update preview image
        if hasattr(self, 'preview_image'):
            self.preview_image.kill()
        self.preview_image = UIImage(
            relative_rect=self.preview_rect,
            image_surface=self.preview_surface,
            manager=self.manager
        )
    
    def on_exit(self):
        """清理UI元素"""
        # 清理选择列表
        if hasattr(self, 'map_selection_list'):
            self.map_selection_list.kill()
        # 清理预览图像
        if hasattr(self, 'preview_image'):
            self.preview_image.kill()
        # 清理坦克图像
        if hasattr(self, 'tank_image_element'):
            self.tank_image_element.kill()
        # 清理按钮
        if hasattr(self, 'btn_prev'):
            self.btn_prev.kill()
        if hasattr(self, 'btn_next'):
            self.btn_next.kill()
        if hasattr(self, 'btn_start'):
            self.btn_start.kill()
        if hasattr(self, 'btn_back'):
            self.btn_back.kill()
        if hasattr(self, 'difficulty_dropdown'):
            self.difficulty_dropdown.kill()
        # 调用父类方法
        super().on_exit()
    
    def render(self):
        self.surface.fill((40, 40, 50))
        
        # Draw map statistics
        if hasattr(self, 'context') and hasattr(self.context, 'selected_map'):
            selected_map = self.context.selected_map
            map_data = map_loader.load_map(selected_map)
            
            if map_data and selected_map != "default":
                center_x = self.surface.get_width() // 2
                
                # Display map info
                stats_text = f"地图: {map_data.get('name', selected_map)}"
                stats_surf = self.small_font.render(stats_text, True, (200, 200, 200))
                self.surface.blit(stats_surf, (center_x - 150, 390))
                
                wall_count = len(map_data.get('walls', []))
                wall_text = f"障碍物数量: {wall_count}"
                wall_surf = self.small_font.render(wall_text, True, (200, 200, 200))
                self.surface.blit(wall_surf, (center_x - 150, 420))


class LobbyScreen(BaseScreen):
    """联机大厅屏幕"""
    
    def on_enter(self):
        super().on_enter()
        
        self.surface_width = self.surface.get_width()
        self.surface_height = self.surface.get_height()
        
        # 计算中心位置
        center_x = self.surface_width // 2
        
        # 用户名输入 - 居中显示
        label_width = 100
        entry_width = 200
        total_width = label_width + entry_width + 10  # 10像素间距
        start_x = center_x - total_width // 2
        
        UILabel(
            relative_rect=pygame.Rect((start_x, 50), (label_width, 30)),
            text="用户名:",
            manager=self.manager
        )
        self.username_entry = UITextEntryLine(
            relative_rect=pygame.Rect((start_x + label_width + 10, 50), (entry_width, 30)),
            manager=self.manager
        )
        self.username_entry.set_text("Player1")
        
        # 房间列表 - 居中显示
        room_list_width = 500
        room_list_height = 300
        room_list_x = center_x - room_list_width // 2
        
        UILabel(
            relative_rect=pygame.Rect((room_list_x, 100), (200, 30)),
            text="房间列表:",
            manager=self.manager
        )
        self.room_list = UISelectionList(
            relative_rect=pygame.Rect((room_list_x, 140), (room_list_width, room_list_height)),
            item_list=[], 
            manager=self.manager
        )
        
        # 按钮 - 放在房间列表右侧，与房间列表顶部对齐
        btn_width = 150
        btn_height = 50
        btn_spacing = 20
        btn_start_x = room_list_x + room_list_width + 30
        btn_start_y = 140
        
        self.btn_create = UIButton(
            relative_rect=pygame.Rect((btn_start_x, btn_start_y), (btn_width, btn_height)),
            text='创建房间',
            manager=self.manager
        )
        
        self.btn_join = UIButton(
            relative_rect=pygame.Rect((btn_start_x, btn_start_y + btn_height + btn_spacing), (btn_width, btn_height)),
            text='加入房间',
            manager=self.manager
        )
        
        self.btn_refresh = UIButton(
            relative_rect=pygame.Rect((btn_start_x, btn_start_y + (btn_height + btn_spacing) * 2), (btn_width, btn_height)),
            text='刷新列表',
            manager=self.manager
        )
        
        # 返回按钮 - 放在左下角，保持原位置
        self.btn_back = UIButton(
            relative_rect=pygame.Rect((50, 500), (100, 50)),
            text='返回',
            manager=self.manager
        )
        
        # Auto start client discovery
        # Access NetworkManager via GameEngine? No direct access.
        # But we can assume GameEngine holds NetworkManager and we can access it via global?
        # No, that's bad design.
        # We need to access NetworkManager.
        # In main.py: game = GameEngine(). game.screen_manager...
        # ScreenManager doesn't have NetworkManager.
        # We should pass NetworkManager to ScreenManager or use a Singleton/Global.
        # For now, let's import the instance from main? No, circular.
        # Let's assume ScreenManager has it?
        # Hack: GameEngine sets it on ScreenManager.
        # Or better: NetworkManager is a singleton or global module?
        # Let's use `src.utils.service_locator` pattern or just import the class if it was static.
        # But it's an instance.
        # Let's add `network_manager` to `ScreenContext`? No, context is data.
        # Let's add it to `BaseScreen` via `ScreenManager`.
        # We need to update `ScreenManager` to accept `network_manager`.
        
        # Start client discovery when entering lobby (only if not already started)
        if hasattr(self, 'network_manager') and self.network_manager.stats.role == "standalone":
            self.network_manager.start_client()
            self.network_manager.broadcast_discovery()
        
        self.discovery_timer = 0  # Timer for periodic discovery broadcasts

    def update(self, time_delta: float):
        super().update(time_delta)
        # Periodic discovery broadcast
        if hasattr(self, 'network_manager') and self.network_manager.stats.role == "client":
            if not hasattr(self, 'discovery_timer'):
                self.discovery_timer = 0
                
            self.discovery_timer += time_delta
            if self.discovery_timer > 2.0:  # Broadcast every 2 seconds
                self.network_manager.broadcast_discovery()
                self.discovery_timer = 0
            
            # Update room list (only if UI is initialized)
            if hasattr(self, 'room_list'):
                rooms = [f"{r[1]} ({r[0]})" for r in self.network_manager.found_servers]
                # Only update if changed to avoid flickering/resetting selection
                # UISelectionList doesn't expose current items easily, but we can check if it matches our cache
                # Or just set it, pygame_gui might handle it.
                # But to be safe and efficient:
                current_items = getattr(self, '_cached_room_list', [])
                if rooms != current_items:
                    print(f"[UI] Updating room list: {rooms}")
                    self.room_list.set_item_list(rooms)
                    self._cached_room_list = rooms

    def handle_event(self, event: pygame.event.Event):
        super().handle_event(event)
        
        if event.type == pygame_gui.UI_SELECTION_LIST_NEW_SELECTION:
            if event.ui_element == self.room_list:
                self.selected_room = event.text
                print(f"[UI] Room selected: {self.selected_room}")
                
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.btn_create:
                # ... (existing code) ...
                # Start Host
                if hasattr(self, 'network_manager'):
                    # Critical: Stop client discovery mode before starting host!
                    # Otherwise start_host() returns early because _running is True.
                    self.network_manager.stop()
                    self.network_manager.start_host()
                self.context.next_state = "room"
                self.context.is_host = True
                self.context.game_mode = "multi"
                
            elif event.ui_element == self.btn_join:
                # Join selected
                # Use manually tracked selection as get_single_selection() can be unreliable
                selected = getattr(self, 'selected_room', None)
                print(f"[UI] Join clicked. Selected: {selected}")
                if selected:
                    # Parse IP from string "RoomName (IP)"
                    ip = selected.split('(')[-1].strip(')')
                    if hasattr(self, 'network_manager'):
                        # Don't call start_client again, already started in on_enter
                        if self.network_manager.connect_to_server(ip):
                            self.context.next_state = "room"
                            self.context.is_host = False
                            self.context.game_mode = "multi"
                        
            elif event.ui_element == self.btn_refresh:
                if hasattr(self, 'network_manager'):
                    # Just broadcast, don't restart client
                    self.network_manager.broadcast_discovery()
                    # Clear found servers to force refresh
                    self.network_manager.found_servers.clear()
                    # Also clear cache to ensure UI updates
                    self._cached_room_list = []

            elif event.ui_element == self.btn_back:
                if hasattr(self, 'network_manager'):
                    self.network_manager.stop()
                self.context.next_state = "menu"

    def render(self):
        self.surface.fill((30, 50, 50))


class RoomScreen(BaseScreen):
    """房间等待屏幕"""
    
    def on_enter(self):
        super().on_enter()
        
        UILabel(
            relative_rect=pygame.Rect((50, 50), (200, 30)),
            text="等待玩家...",
            manager=self.manager
        )
        
        # 玩家列表
        self.player_list = UISelectionList(
            relative_rect=pygame.Rect((50, 100), (300, 100)),
            item_list=["Player1 (Host)"], 
            manager=self.manager
        )
        
        # Ready State Tracking
        self.local_ready = False
        self.remote_ready = False
        
        # Map Selection (Host Only)
        UILabel(
            relative_rect=pygame.Rect((50, 210), (100, 30)),
            text="选择地图:",
            manager=self.manager
        )
        
        # Load available maps
        self._load_available_maps()
        
        self.map_selection_list = UISelectionList(
            relative_rect=pygame.Rect((50, 250), (300, 100)),
            item_list=self.map_display_names,
            default_selection=self.map_display_names[0],
            manager=self.manager
        )
        
        # Initialize selected map
        self.selected_map = self.map_names[0]
        self.context.selected_map = self.selected_map
        
        # Disable map selection for client
        if not getattr(self.context, 'is_host', False):
            self.map_selection_list.disable()
            
        # Difficulty Selection (Host Only)
        UILabel(
            relative_rect=pygame.Rect((50, 360), (100, 30)),
            text="敌人难度:",
            manager=self.manager
        )
        
        from src.game_engine.ai_config import get_difficulty_names, get_difficulty_key_by_name, DEFAULT_DIFFICULTY, DIFFICULTY_CONFIGS
        self.difficulty_names = get_difficulty_names()
        default_diff_name = DIFFICULTY_CONFIGS[DEFAULT_DIFFICULTY]["name"]
        
        self.difficulty_dropdown = UIDropDownMenu(
            options_list=self.difficulty_names,
            starting_option=default_diff_name,
            relative_rect=pygame.Rect((160, 360), (150, 30)),
            manager=self.manager
        )
        
        # Initialize difficulty
        self.context.enemy_difficulty = DEFAULT_DIFFICULTY
        
        if not getattr(self.context, 'is_host', False):
            self.difficulty_dropdown.disable()
        
        # Tank Selection UI
        self.local_tank_id = 1
        self.remote_tank_id = 1
        self.context.player_tank_id = 1
        self.context.enemy_tank_id = 1
        
        # Local Tank (Right side)
        UILabel(relative_rect=pygame.Rect((400, 250), (100, 30)), text="你的坦克", manager=self.manager)
        self.local_image_rect = pygame.Rect((400, 290), (100, 100))
        self.local_image_elem = None
        
        self.btn_prev = UIButton(relative_rect=pygame.Rect((400, 400), (45, 30)), text='<', manager=self.manager)
        self.btn_next = UIButton(relative_rect=pygame.Rect((455, 400), (45, 30)), text='>', manager=self.manager)
        
        # Remote Tank (Right side below local) - Display Only
        UILabel(relative_rect=pygame.Rect((550, 250), (100, 30)), text="对手坦克", manager=self.manager)
        self.remote_image_rect = pygame.Rect((550, 290), (100, 100))
        self.remote_image_elem = None
        
        self._update_images()

        self.btn_ready = UIButton(
            relative_rect=pygame.Rect((400, 100), (150, 50)),
            text='准备',
            manager=self.manager
        )
        
        # Ready status label
        self.ready_status_label = UILabel(
            relative_rect=pygame.Rect((400, 160), (250, 30)),
            text="状态: 未准备",
            manager=self.manager
        )
        
        # 仅房主可见
        self.btn_start = UIButton(
            relative_rect=pygame.Rect((560, 100), (150, 50)),
            text='开始游戏',
            manager=self.manager
        )
        if not getattr(self.context, 'is_host', False):
            self.btn_start.hide()
        else:
            self.btn_start.disable()  # Disabled until both ready
            
        self.btn_leave = UIButton(
            relative_rect=pygame.Rect((50, 500), (150, 50)),
            text='离开房间',
            manager=self.manager
        )

    def _load_available_maps(self):
        """加载可用地图列表"""
        from src.utils.map_loader import map_loader
        available_maps = map_loader.get_available_maps()
        if not available_maps:
            available_maps = ["default"]
        
        self.map_names = available_maps
        self.map_display_names = []
        self.map_name_mapping = {}
        
        for map_name in available_maps:
            if map_name == "default":
                display_name = "默认地图"
            else:
                map_data = map_loader.load_map(map_name)
                if map_data and 'name' in map_data:
                    wall_count = len(map_data.get('walls', []))
                    display_name = f"{map_data['name']} ({wall_count} 个障碍物)"
                else:
                    display_name = map_name
            
            self.map_display_names.append(display_name)
            self.map_name_mapping[display_name] = map_name
        
        if not self.map_display_names:
            self.map_display_names = ["默认地图"]
            self.map_names = ["default"]
            self.map_name_mapping = {"默认地图": "default"}
    
    def _update_images(self):
        # Local
        if self.local_image_elem: self.local_image_elem.kill()
        images = resource_manager.load_tank_images('player', self.local_tank_id, 0)
        surf = pygame.transform.scale(images[0][0], (100, 100)) if images and images.get(0) else pygame.Surface((100, 100))
        self.local_image_elem = UIImage(relative_rect=self.local_image_rect, image_surface=surf, manager=self.manager)
        
        # Remote
        if self.remote_image_elem: self.remote_image_elem.kill()
        images = resource_manager.load_tank_images('player', self.remote_tank_id, 0)
        surf = pygame.transform.scale(images[0][0], (100, 100)) if images and images.get(0) else pygame.Surface((100, 100))
        self.remote_image_elem = UIImage(relative_rect=self.remote_image_rect, image_surface=surf, manager=self.manager)
    
    def _update_ready_status(self):
        """更新准备状态显示"""
        if self.context.is_host:
            status = f"你: {'已准备' if self.local_ready else '未准备'} | 对手: {'已准备' if self.remote_ready else '未准备'}"
        else:
            status = f"你: {'已准备' if self.local_ready else '未准备'} | 房主: {'已准备' if self.remote_ready else '未准备'}"
        
        self.ready_status_label.set_text(status)
        
        # Enable/Disable start button for host
        if self.context.is_host and hasattr(self, 'btn_start'):
            if self.local_ready and self.remote_ready and self.network_manager.stats.connected:
                self.btn_start.enable()
            else:
                self.btn_start.disable()

    def update(self, time_delta: float):
        super().update(time_delta)
        # Check connection status
        if hasattr(self, 'network_manager'):
            if self.network_manager.stats.connected:
                self.player_list.set_item_list(["Player1 (Host)", "Player2 (Client)"])
            else:
                self.player_list.set_item_list(["Player1 (Host)"])
                # Reset remote ready if disconnected
                if self.remote_ready:
                    self.remote_ready = False
                    self._update_ready_status()
                
            if self.context.is_host:
                # Host: Check for lobby updates from client
                msgs = self.network_manager.get_inputs()
                for msg in msgs:
                    if msg.get("type") == "lobby_update":
                        payload = msg.get("payload")
                        if payload and "tank_id" in payload:
                            self.remote_tank_id = payload["tank_id"]
                            self.context.enemy_tank_id = self.remote_tank_id
                            self._update_images()
                    elif msg.get("type") == "ready_state":
                        payload = msg.get("payload")
                        if payload is not None:
                            self.remote_ready = payload.get("is_ready", False)
                            self._update_ready_status()
            else:
                # Client: Check for game start and lobby updates
                self.network_manager.get_latest_state()
                
                events = self.network_manager.get_events()
                for event in events:
                    if event.get("type") == "game_start":
                        payload = event.get("payload")
                        if payload:
                            # Game Start!
                            self.context.enemy_tank_id = payload["p1_tank_id"]
                            self.context.player_tank_id = payload["p2_tank_id"]
                            self.context.selected_map = payload.get("map_name", "default")
                            
                            # Store map data if provided by host
                            if "map_data" in payload:
                                self.context.received_map_data = payload["map_data"]
                                print(f"[Client] 接收到地图数据: {self.context.selected_map}")
                            else:
                                self.context.received_map_data = None
                            
                            self.local_tank_id = self.context.player_tank_id
                            
                            self.context.next_state = "game"
                    
                    elif event.get("type") == "lobby_update":
                        payload = event.get("payload")
                        if payload and "tank_id" in payload:
                            self.remote_tank_id = payload["tank_id"]
                            self.context.enemy_tank_id = self.remote_tank_id
                            self._update_images()
                    
                    elif event.get("type") == "map_selection":
                        payload = event.get("payload")
                        if payload and "map_name" in payload:
                            self.selected_map = payload["map_name"]
                            self.context.selected_map = self.selected_map
                            # Update UI to show selected map
                            if hasattr(self, 'map_name_mapping'):
                                for display_name, map_name in self.map_name_mapping.items():
                                    if map_name == self.selected_map:
                                        # Find and select in list
                                        break
                    
                    elif event.get("type") == "difficulty_update":
                        payload = event.get("payload")
                        if payload and "difficulty" in payload:
                            diff_key = payload["difficulty"]
                            self.context.enemy_difficulty = diff_key
                            # Update UI
                            from src.game_engine.ai_config import DIFFICULTY_CONFIGS
                            if diff_key in DIFFICULTY_CONFIGS:
                                diff_name = DIFFICULTY_CONFIGS[diff_key]["name"]
                                # Update dropdown selection without triggering event
                                # pygame_gui doesn't have a clean set_selected_option that doesn't trigger?
                                # Actually it's fine if it triggers as we check is_host
                                # But for client, the dropdown is disabled anyway.
                                # We just need to update the displayed text.
                                # There isn't a direct set_selected method in older versions, let's check.
                                # Assuming standard usage:
                                self.difficulty_dropdown.selected_option = diff_name
                                self.difficulty_dropdown.menu_states['closed'].finish()
                                self.difficulty_dropdown.menu_states['closed'].start()
                                # Or just kill and recreate? No that's ugly.
                                # Let's try setting selected_option directly if possible or use internal method.
                                # A safer way is just to let it be if it's disabled, but we want to see what host picked.
                                # Let's try:
                                # self.difficulty_dropdown.selected_option = diff_name
                                # self.difficulty_dropdown.rebuild() 
                                # But rebuild might not be available.
                                # Simple hack: just print for now, UI update might need recreation.
                                print(f"[Client] 收到难度更新: {diff_name}")
                                # Recreate dropdown to update text (safest)
                                rect = self.difficulty_dropdown.relative_rect
                                manager = self.difficulty_dropdown.ui_manager
                                self.difficulty_dropdown.kill()
                                self.difficulty_dropdown = UIDropDownMenu(
                                    options_list=self.difficulty_names,
                                    starting_option=diff_name,
                                    relative_rect=rect,
                                    manager=manager
                                )
                                self.difficulty_dropdown.disable()
                    
                    elif event.get("type") == "ready_state":
                        payload = event.get("payload")
                        if payload is not None:
                            self.remote_ready = payload.get("is_ready", False)
                            self._update_ready_status()

    def handle_event(self, event: pygame.event.Event):
        super().handle_event(event)
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.btn_leave:
                if hasattr(self, 'network_manager'):
                    self.network_manager.stop()
                self.context.next_state = "lobby"
            elif event.ui_element == self.btn_start:
                # Host starts game
                if hasattr(self, 'network_manager'):
                    # Load map data to send to client
                    map_data = None
                    if self.selected_map != "default":
                        from src.utils.map_loader import map_loader
                        map_data = map_loader.load_map(self.selected_map)
                        if map_data:
                            print(f"[Host] 发送地图数据: {self.selected_map}")
                    
                    # Send Game Start with tank IDs, map name, and map data
                    self.network_manager.send_game_start(self.local_tank_id, self.remote_tank_id, self.selected_map, map_data)
                
                self.context.player_tank_id = self.local_tank_id
                self.context.enemy_tank_id = self.remote_tank_id
                self.context.selected_map = self.selected_map
                self.context.next_state = "game"
                
            elif event.ui_element == self.btn_prev:
                self.local_tank_id -= 1
                if self.local_tank_id < 1: self.local_tank_id = 4
                self._update_images()
                if hasattr(self, 'network_manager'):
                    self.network_manager.send_lobby_update(self.local_tank_id)
                    
            elif event.ui_element == self.btn_next:
                self.local_tank_id += 1
                if self.local_tank_id > 4: self.local_tank_id = 1
                self._update_images()
                if hasattr(self, 'network_manager'):
                    self.network_manager.send_lobby_update(self.local_tank_id)

            elif event.ui_element == self.btn_ready:
                # Toggle ready state
                self.local_ready = not self.local_ready
                self.btn_ready.set_text('取消准备' if self.local_ready else '准备')
                self._update_ready_status()
                
                # Send ready state to other player
                if hasattr(self, 'network_manager'):
                    self.network_manager.send_ready_state(self.local_ready)
        
        elif event.type == pygame_gui.UI_SELECTION_LIST_NEW_SELECTION:
            if event.ui_element == self.map_selection_list:
                # Only host can change map
                if self.context.is_host:
                    selected_text = event.text
                    if hasattr(self, 'map_name_mapping') and selected_text in self.map_name_mapping:
                        self.selected_map = self.map_name_mapping[selected_text]
                        self.context.selected_map = self.selected_map
                        print(f"地图选择: {selected_text} -> {self.selected_map}")
                        
                        # Send map selection to client
                        if hasattr(self, 'network_manager'):
                            self.network_manager.send_event("map_selection", {"map_name": self.selected_map})
                            
        elif event.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
            if hasattr(self, 'difficulty_dropdown') and event.ui_element == self.difficulty_dropdown:
                if self.context.is_host:
                    from src.game_engine.ai_config import get_difficulty_key_by_name
                    # Fallback to selected_option if event.text is None
                    text = event.text if event.text is not None else self.difficulty_dropdown.selected_option
                    
                    if text is None or text == "None":
                        text = "普通"
                        
                    selected_difficulty = get_difficulty_key_by_name(text)
                    self.context.enemy_difficulty = selected_difficulty
                    print(f"[Host] 难度选择: {text} -> {selected_difficulty}")
                    
                    # Broadcast to client
                    if hasattr(self, 'network_manager'):
                        self.network_manager.send_event("difficulty_update", {"difficulty": selected_difficulty})

    def render(self):
        self.surface.fill((50, 30, 30))


# 已在文件开头导入：from src.utils.level_progress import load_level_progress

# 在SinglePlayerSetupScreen类之后添加LevelSelectScreen类

class LevelSelectScreen(BaseScreen):
    """关卡选择屏幕"""
    
    def on_enter(self):
        super().on_enter()
        
        center_x = self.surface.get_width() // 2
        center_y = self.surface.get_height() // 2
        
        # 标题
        UILabel(
            relative_rect=pygame.Rect((center_x - 150, 30), (300, 40)),
            text="选择关卡",
            manager=self.manager,
            object_id="@title"
        )
        
        # 加载关卡进度
        self.progress = load_level_progress()
        self.unlocked_levels = self.progress["unlocked_levels"]
        self.max_level = self.progress["max_level"]
        
        # 关卡按钮配置
        self.level_buttons = []
        self.level_locks = []
        self.num_columns = 5  # 每行显示5个关卡
        self.button_size = (80, 80)
        self.spacing = 20
        
        # 计算起始位置，使关卡按钮居中显示
        total_width = (self.button_size[0] + self.spacing) * self.num_columns - self.spacing
        start_x = center_x - total_width // 2
        start_y = 100
        
        # 创建关卡按钮
        for level in range(1, self.max_level + 1):
            # 计算按钮位置
            row = (level - 1) // self.num_columns
            col = (level - 1) % self.num_columns
            x = start_x + col * (self.button_size[0] + self.spacing)
            y = start_y + row * (self.button_size[1] + self.spacing)
            
            # 关卡按钮
            btn = UIButton(
                relative_rect=pygame.Rect((x, y), self.button_size),
                text=f"第{level}关",
                manager=self.manager
            )
            self.level_buttons.append(btn)
            
            # 检查关卡是否已解锁
            if level not in self.unlocked_levels:
                # 为未解锁的关卡创建锁定图标
                lock_rect = pygame.Rect((x + 20, y + 20), (40, 40))
                btn.disable()
        
        # 难度选择下拉框
        UILabel(
            relative_rect=pygame.Rect((center_x - 300, 350), (200, 30)),
            text="敌人难度",
            manager=self.manager
        )
        
        from src.game_engine.ai_config import get_difficulty_names, DEFAULT_DIFFICULTY
        difficulty_names = get_difficulty_names()
        self.difficulty_dropdown = UIDropDownMenu(
            options_list=difficulty_names,
            starting_option=difficulty_names[1],  # 默认普通难度
            relative_rect=pygame.Rect((center_x - 300, 380), (200, 30)),
            manager=self.manager
        )
        
        # 选择坦克按钮
        self.btn_select_tank = UIButton(
            relative_rect=pygame.Rect((center_x - 150, 430), (300, 50)),
            text="选择坦克",
            manager=self.manager
        )
        
        # 返回按钮
        self.btn_back = UIButton(
            relative_rect=pygame.Rect((center_x - 150, 490), (300, 50)),
            text="返回",
            manager=self.manager
        )
        
        # 当前选择的关卡
        self.selected_level = None
    
    def handle_event(self, event: pygame.event.Event):
        super().handle_event(event)
        
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            # 检查是否点击了关卡按钮
            for i, btn in enumerate(self.level_buttons):
                if event.ui_element == btn:
                    level = i + 1
                    if level in self.unlocked_levels:
                        self.selected_level = level
                        print(f"已选择关卡: {level}")
                        # 更新所有关卡按钮的样式，高亮当前选中的关卡
                        for j, other_btn in enumerate(self.level_buttons):
                            if j == i:
                                # 选中的关卡按钮使用不同样式
                                other_btn.set_text(f"> 第{level}关 <")
                            else:
                                other_btn.set_text(f"第{j+1}关")
                    break
            
            # 选择坦克按钮
            if event.ui_element == self.btn_select_tank:
                if self.selected_level:
                    # 保存选择的关卡和难度
                    self.context.selected_level = self.selected_level
                    from src.game_engine.ai_config import get_difficulty_key_by_name
                    self.context.enemy_difficulty = get_difficulty_key_by_name(
                        self.difficulty_dropdown.selected_option
                    )
                    # 跳转到坦克选择界面
                    self.context.next_state = "level_tank_select"
            
            # 返回按钮
            if event.ui_element == self.btn_back:
                self.context.next_state = "single_mode_select"
    
    def render(self):
        self.surface.fill((30, 30, 30))
        
        # 绘制关卡背景
        pygame.draw.rect(
            self.surface, 
            (40, 40, 40), 
            (self.surface.get_width() // 2 - 280, 80, 560, 250),
            border_radius=10
        )
        
        # 为未解锁的关卡绘制锁定图标
        for i, btn in enumerate(self.level_buttons):
            level = i + 1
            if level not in self.unlocked_levels:
                # 获取按钮位置
                btn_rect = btn.get_relative_rect()
                # 绘制锁定图标
                lock_text = self.small_font.render("🔒", True, (255, 0, 0))
                lock_x = btn_rect.x + btn_rect.width // 2 - lock_text.get_width() // 2
                lock_y = btn_rect.y + btn_rect.height // 2 - lock_text.get_height() // 2
                self.surface.blit(lock_text, (lock_x, lock_y))
        
        # 提示信息
        if self.selected_level:
            tips_text = f"已选择: 第{self.selected_level}关"
        else:
            tips_text = "请选择一个关卡"
        
        tips_surf = self.small_font.render(tips_text, True, (200, 200, 200))
        self.surface.blit(
            tips_surf, 
            tips_surf.get_rect(center=(self.surface.get_width() // 2, 330))
        )


# 添加关卡坦克选择屏幕
class LevelTankSelectScreen(BaseScreen):
    """关卡模式的坦克选择屏幕"""
    
    def on_enter(self):
        super().on_enter()
        # Initialize font for statistics display
        self.small_font = pygame.font.SysFont('SimHei', 16)
        
        center_x = self.surface.get_width() // 2
        
        self.tank_id = 1
        self.context.player_tank_id = 1
        
        UILabel(
            relative_rect=pygame.Rect((center_x - 100, 50), (200, 30)),
            text="选择你的坦克",
            manager=self.manager
        )
        
        # Tank Image Display
        self.image_rect = pygame.Rect((center_x - 50, 100), (100, 100))
        self.tank_image_element = None
        self._update_tank_image()
        
        # Selection Buttons
        self.btn_prev = UIButton(
            relative_rect=pygame.Rect((center_x - 160, 130), (100, 40)),
            text='< 上一个',
            manager=self.manager
        )
        
        self.btn_next = UIButton(
            relative_rect=pygame.Rect((center_x + 60, 130), (100, 40)),
            text='下一个 >',
            manager=self.manager
        )
        
        # 开始游戏按钮
        self.btn_start = UIButton(
            relative_rect=pygame.Rect((center_x - 150, 280), (300, 50)),
            text='开始游戏',
            manager=self.manager
        )
        
        # 返回按钮
        self.btn_back = UIButton(
            relative_rect=pygame.Rect((center_x - 150, 350), (300, 50)),
            text='返回',
            manager=self.manager
        )
    
    def _update_tank_image(self):
        """更新坦克图像显示"""
        from src.utils.resource_manager import resource_manager
        # Load tank image (Level 0, UP direction)
        # resource_manager.load_tank_images returns dict[dir][frame]
        images = resource_manager.load_tank_images('player', self.tank_id, 0)
        if images and images.get(0):
            surf = images[0][0]
            # Scale up for UI
            surf = pygame.transform.scale(surf, (100, 100))
            if self.tank_image_element:
                self.tank_image_element.kill()
            self.tank_image_element = UIImage(
                relative_rect=self.image_rect,
                image_surface=surf,
                manager=self.manager
            )
    
    def handle_event(self, event: pygame.event.Event):
        super().handle_event(event)
        
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.btn_prev:
                self.tank_id = (self.tank_id - 2) % 4 + 1  # 循环到上一个坦克
                self.context.player_tank_id = self.tank_id
                self._update_tank_image()
            elif event.ui_element == self.btn_next:
                self.tank_id = self.tank_id % 4 + 1  # 循环到下一个坦克
                self.context.player_tank_id = self.tank_id
                self._update_tank_image()
            elif event.ui_element == self.btn_start:
                # 保存玩家选择的坦克皮肤
                self.context.player_skin = self.tank_id
                # 设置游戏模式为关卡模式
                self.context.game_mode = "level"
                # 开始游戏
                self.context.next_state = "game"
            elif event.ui_element == self.btn_back:
                self.context.next_state = "level_select"
    
    def render(self):
        self.surface.fill((30, 30, 30))
        # 绘制背景
        pygame.draw.rect(
            self.surface, 
            (40, 40, 40), 
            (self.surface.get_width() // 2 - 180, 30, 360, 400),
            border_radius=10
        )


class SettingsScreen(BaseScreen):
    """设置界面屏幕"""
    
    def on_enter(self):
        super().on_enter()
        
        center_x = self.surface.get_width() // 2
        center_y = self.surface.get_height() // 2
        btn_width = 200
        btn_height = 50
        spacing = 20
        
        # 标题
        UILabel(
            relative_rect=pygame.Rect((center_x - 100, 50), (200, 30)),
            text="游戏设置",
            manager=self.manager,
            object_id="@title"
        )
        
        # 显示模式设置
        UILabel(
            relative_rect=pygame.Rect((center_x - 200, center_y - 100), (200, 30)),
            text="显示模式",
            manager=self.manager
        )
        
        # 显示模式选项
        self.display_mode_options = ["窗口显示", "全屏显示"]
        self.display_mode_dropdown = UIDropDownMenu(
            options_list=self.display_mode_options,
            starting_option=self.display_mode_options[0],  # 默认窗口显示
            relative_rect=pygame.Rect((center_x + 10, center_y - 100), (150, 30)),
            manager=self.manager
        )
        
        # 应用按钮
        self.btn_apply = UIButton(
            relative_rect=pygame.Rect((center_x - 200, center_y + 50), (150, 40)),
            text="应用设置",
            manager=self.manager
        )
        
        # 返回按钮
        self.btn_back = UIButton(
            relative_rect=pygame.Rect((center_x + 50, center_y + 50), (150, 40)),
            text="返回主菜单",
            manager=self.manager
        )
        
        # 当前显示模式状态
        self.is_fullscreen = False
        
    def handle_event(self, event: pygame.event.Event):
        super().handle_event(event)
        
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.btn_apply:
                # 应用显示模式设置
                selected_mode = self.display_mode_dropdown.selected_option
                self._apply_display_mode(selected_mode)
            elif event.ui_element == self.btn_back:
                # 返回主菜单
                self.context.next_state = "menu"
        
    def _apply_display_mode(self, mode):
        """应用显示模式设置"""
        window_manager = self.get_window_manager()
        if not window_manager:
            print("无法获取WindowManager实例")
            return
        
        if mode == "全屏显示" and not self.is_fullscreen:
            # 切换到全屏模式
            window_manager.toggle_fullscreen(True)
            self.is_fullscreen = True
            print("切换到全屏显示")
        elif mode == "窗口显示" and self.is_fullscreen:
            # 切换到窗口模式
            window_manager.toggle_fullscreen(False)
            self.is_fullscreen = False
            print("切换到窗口显示")
    
    def render(self):
        self.surface.fill((30, 30, 30))
        # 绘制背景
        pygame.draw.rect(
            self.surface, 
            (40, 40, 40), 
            (self.surface.get_width() // 2 - 250, 30, 500, 300),
            border_radius=10
        )