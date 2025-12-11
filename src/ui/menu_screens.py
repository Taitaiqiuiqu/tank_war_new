# 必须在导入pygame_gui之前初始化i18n
import src.ui.init_i18n

import pygame
import pygame_gui
from pygame_gui.elements import UIButton, UILabel, UISelectionList, UIImage, UITextEntryLine, UIDropDownMenu, UIPanel, UIHorizontalSlider
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
        
        # 在主菜单时开始预加载资源（异步，不阻塞）
        from src.utils.resource_manager import resource_manager
        from src.ui.video_manager import VideoPlaybackController
        import os
        
        # 预加载图片和音频资源（如果还没加载）
        if not resource_manager.is_preload_complete():
            resource_manager.preload_all()
        
        # 初始化并预加载视频资源（如果还没有）
        if not hasattr(self.context, 'video_manager'):
            video_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "videos"))
            self.context.video_manager = VideoPlaybackController(video_dir)
        
        video_manager = self.context.video_manager
        if not video_manager.is_preload_complete():
            video_manager.preload_all(async_load=True)
        
        # 像素风卡片布局
        w, h = self.surface.get_size()
        card_w = min(520, max(420, int(w * 0.45)))
        padding = 24
        btn_block_h = 5 * 56 + 4 * 14  # 5个按钮 + 4个间距
        card_h = max(480, padding * 2 + 60 + btn_block_h)
        card_x = (w - card_w) // 2
        card_y = max(60, (h - card_h) // 2)
        btn_w = card_w - padding * 2
        btn_h = 56
        spacing = 14
        
        self.panel = UIPanel(
            relative_rect=pygame.Rect(card_x, card_y, card_w, card_h),
            manager=self.manager,
            object_id="#main_menu_panel"
        )
        
        # 标题
        UILabel(
            relative_rect=pygame.Rect(padding, padding, btn_w, 40),
            text="坦克大战",
            manager=self.manager,
            container=self.panel,
            object_id="@title"
        )
        
        btn_y = padding + 60
        self.btn_single = UIButton(
            relative_rect=pygame.Rect(padding, btn_y, btn_w, btn_h),
            text='单机模式',
            manager=self.manager,
            container=self.panel
        )
        self.btn_multi = UIButton(
            relative_rect=pygame.Rect(padding, btn_y + (btn_h + spacing) * 1, btn_w, btn_h),
            text='联机模式',
            manager=self.manager,
            container=self.panel
        )
        self.btn_settings = UIButton(
            relative_rect=pygame.Rect(padding, btn_y + (btn_h + spacing) * 2, btn_w, btn_h),
            text='设置',
            manager=self.manager,
            container=self.panel
        )
        self.btn_map_editor = UIButton(
            relative_rect=pygame.Rect(padding, btn_y + (btn_h + spacing) * 3, btn_w, btn_h),
            text='地图编辑器',
            manager=self.manager,
            container=self.panel
        )
        self.btn_exit = UIButton(
            relative_rect=pygame.Rect(padding, btn_y + (btn_h + spacing) * 4, btn_w, btn_h),
            text='退出游戏',
            manager=self.manager,
            container=self.panel
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
        scale = getattr(self.ui_manager, "scale_rect", lambda r: r)
        
        center_x = self.surface.get_width() // 2
        center_y = self.surface.get_height() // 2
        btn_width = 200
        btn_height = 50
        spacing = 20
        
        # 标题
        UILabel(
            relative_rect=scale(pygame.Rect((center_x - 100, 100), (200, 30))),
            text="选择游戏模式",
            manager=self.manager,
            object_id="@title"
        )
        
        # 自由模式按钮
        self.btn_free_mode = UIButton(
            relative_rect=scale(pygame.Rect((center_x - btn_width // 2, center_y - 50), (btn_width, btn_height))),
            text='自由模式',
            manager=self.manager
        )
        
        # 关卡模式按钮
        self.btn_level_mode = UIButton(
            relative_rect=scale(pygame.Rect((center_x - btn_width // 2, center_y + 20), (btn_width, btn_height))),
            text='关卡模式',
            manager=self.manager
        )
        
        # 返回按钮
        self.btn_back = UIButton(
            relative_rect=scale(pygame.Rect((center_x - btn_width // 2, center_y + 90), (btn_width, btn_height))),
            text='返回主菜单',
            manager=self.manager
        )
    
    def handle_event(self, event: pygame.event.Event):
        super().handle_event(event)
        
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.btn_free_mode:
                # 进入自由模式设置 - 先选择坦克
                self.context.next_state = "tank_select"
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


class TankSelectScreen(BaseScreen):
    """坦克选择屏幕"""
    
    def on_enter(self):
        super().on_enter()
        
        center_x = self.surface.get_width() // 2
        center_y = self.surface.get_height() // 2
        
        self.tank_id = 1
        self.context.player_tank_id = 1
        
        # 标题
        UILabel(
            relative_rect=pygame.Rect((center_x - 150, center_y - 200), (300, 50)),
            text="选择你的坦克",
            manager=self.manager
        )
        
        # Tank Image Display - 增大尺寸并调整位置
        self.image_rect = pygame.Rect((center_x - 100, center_y - 150), (200, 200))
        self.tank_image_element = None
        self._update_tank_image()
        
        # Selection Buttons - 增大尺寸
        self.btn_prev = UIButton(
            relative_rect=pygame.Rect((center_x - 250, center_y - 80), (120, 60)),
            text='< 上一个',
            manager=self.manager
        )
        
        self.btn_next = UIButton(
            relative_rect=pygame.Rect((center_x + 130, center_y - 80), (120, 60)),
            text='下一个 >',
            manager=self.manager
        )
        
        # 下一步按钮 - 增大尺寸并调整位置
        self.btn_next_step = UIButton(
            relative_rect=pygame.Rect((center_x - 120, center_y + 80), (240, 60)),
            text='下一步',
            manager=self.manager
        )
        
        # 返回按钮 - 增大尺寸并调整位置
        self.btn_back = UIButton(
            relative_rect=pygame.Rect((center_x - 120, center_y + 160), (240, 60)),
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
            # Scale up for UI - 增大尺寸
            surf = pygame.transform.scale(surf, (200, 200))
        else:
            surf = pygame.Surface((200, 200))
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
            if event.ui_element == self.btn_next_step:
                # 进入地图和难度选择界面
                self.context.next_state = "single_setup"
            elif event.ui_element == self.btn_back:
                # 返回单机模式选择界面
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
    
    def render(self):
        self.surface.fill((40, 40, 50))
    
    def on_exit(self):
        """清理UI元素"""
        # 清理坦克图像
        if hasattr(self, 'tank_image_element'):
            self.tank_image_element.kill()
        # 清理按钮
        if hasattr(self, 'btn_prev'):
            self.btn_prev.kill()
        if hasattr(self, 'btn_next'):
            self.btn_next.kill()
        if hasattr(self, 'btn_next_step'):
            self.btn_next_step.kill()
        if hasattr(self, 'btn_back'):
            self.btn_back.kill()
        # 调用父类方法
        super().on_exit()


class SinglePlayerSetupScreen(BaseScreen):
    """单机模式设置屏幕 - 地图和AI难度选择"""
    
    def on_enter(self):
        super().on_enter()
        scale = getattr(self.ui_manager, "scale_rect", lambda r: r)
        
        center_x = self.surface.get_width() // 2
        center_y = self.surface.get_height() // 2
        
        # 标题
        UILabel(
            relative_rect=scale(pygame.Rect((center_x - 150, 80), (300, 40))),
            text="选择地图和难度",
            manager=self.manager
        )
        
        # Map selection section
        map_section_y = 160
        
        UILabel(
            relative_rect=scale(pygame.Rect((center_x - 350, map_section_y), (200, 40))),
            text="选择地图",
            manager=self.manager
        )
        
        # Get available maps
        self._load_available_maps()
        
        # Map selection list - 增大尺寸
        self.map_selection_list = UISelectionList(
            relative_rect=scale(pygame.Rect((center_x - 350, map_section_y + 50), (250, 200))),
            item_list=self.map_display_names,
            default_selection=self.map_display_names[0],
            manager=self.manager
        )
        
        # Map preview area
        UILabel(
            relative_rect=scale(pygame.Rect((center_x + 50, map_section_y), (200, 40))),
            text="地图预览",
            manager=self.manager
        )
        
        # Preview surface - 增大尺寸
        self.preview_rect = scale(pygame.Rect((center_x + 50, map_section_y + 50), (300, 200)))
        self.preview_surface = pygame.Surface((self.preview_rect.width, self.preview_rect.height))
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
        
        # Difficulty Selection - 位置下移，避免重叠
        difficulty_y = map_section_y + 280
        
        UILabel(
            relative_rect=scale(pygame.Rect((center_x - 100, difficulty_y), (200, 40))),
            text="敌人难度",
            manager=self.manager
        )
        
        from src.game_engine.ai_config import get_difficulty_names, get_difficulty_key_by_name, DEFAULT_DIFFICULTY, DIFFICULTY_CONFIGS
        self.difficulty_names = get_difficulty_names()
        default_diff_name = DIFFICULTY_CONFIGS[DEFAULT_DIFFICULTY]["name"]
        
        self.difficulty_dropdown = UIDropDownMenu(
            options_list=self.difficulty_names,
            starting_option=default_diff_name,
            relative_rect=scale(pygame.Rect((center_x + 120, difficulty_y), (150, 40))),
            manager=self.manager
        )
        print(f"[DEBUG] Dropdown init: options={self.difficulty_names}, start={default_diff_name}")
        # Set default in context
        self.context.enemy_difficulty = DEFAULT_DIFFICULTY
        
        # Buttons - 增大尺寸并调整位置
        self.btn_start = UIButton(
            relative_rect=scale(pygame.Rect((center_x - 120, difficulty_y + 80), (240, 60))),
            text='开始游戏',
            manager=self.manager
        )
        
        self.btn_back = UIButton(
            relative_rect=scale(pygame.Rect((center_x - 120, difficulty_y + 160), (240, 60))),
            text='返回',
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
                # 返回坦克选择界面
                self.context.next_state = "tank_select"
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


    def _update_maps_for_game_mode(self, game_mode):
        """根据游戏模式更新地图列表"""
        if game_mode == "level":
            # 关卡模式：加载联机关卡地图
            self._load_multiplayer_level_maps()
        else:
            # 其他模式：加载普通地图
            self._load_available_maps()
        
        # 更新地图选择列表
        if hasattr(self, 'map_selection_list'):
            # 更新列表
            self.map_selection_list.set_item_list(self.map_display_names)
            
            # 设置默认选择（如果列表不为空）
            if self.map_display_names:
                self.selected_map = self.map_names[0]
                self.context.selected_map = self.selected_map
    
    def _load_multiplayer_level_maps(self):
        """加载联机关卡地图列表"""
        from src.utils.multiplayer_level_progress import get_available_multiplayer_levels
        from src.utils.multiplayer_map_generator import multiplayer_map_generator
        
        available_levels = get_available_multiplayer_levels()
        
        self.map_names = []
        self.map_display_names = []
        self.map_name_mapping = {}
        
        for level_info in available_levels:
            if level_info["unlocked"]:
                level_num = level_info["level"]
                map_name = f"level_{level_num}"
                display_name = f"关卡 {level_num}"
                
                # 检查地图文件是否存在，不存在则生成
                if not multiplayer_map_generator.load_multiplayer_map("level", map_name):
                    multiplayer_map_generator.generate_level_map(level_num)
                
                self.map_names.append(map_name)
                self.map_display_names.append(display_name)
                self.map_name_mapping[display_name] = map_name
    
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
            font = pygame.font.SysFont('SimHei', 18)
            text = font.render("默认地图", True, (200, 200, 200))
            self.preview_surface.blit(text, text.get_rect(center=(150, 100)))
        else:
            # Load actual map data and draw preview
            map_data = map_loader.load_map(map_name)
            if map_data and 'walls' in map_data:
                # Calculate scaling factor based on actual map size
                map_width = map_data.get('width', 800)
                map_height = map_data.get('height', 600)
                
                # Calculate scaling factors while maintaining aspect ratio
                # Updated to match new preview size (300x200)
                scale_x = 300 / map_width
                scale_y = 200 / map_height
                
                # Use the smaller scaling factor to fit the entire map in preview area
                scale = min(scale_x, scale_y)
            
                # Draw walls
                for wall in map_data['walls']:
                    wall_type = wall.get('type', 1)
                    
                    # Calculate scaled position and size
                    x = int(wall['x'] * scale)
                    y = int(wall['y'] * scale)
                    w = int(50 * scale)
                    h = int(50 * scale)
                
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
                        x = int(spawn[0] * scale)
                        y = int(spawn[1] * scale)
                        tank_id = (idx % 4) + 1  # Cycle through tank skins 1-4
                        
                        # Load player tank image
                        images = resource_manager.load_tank_images('player', tank_id, 0)
                        if images and images.get(0):
                            tank_img = images[0][0]
                            scaled_size = int(30 * scale)  # Tank is 30x30
                            scaled_img = pygame.transform.scale(tank_img, (scaled_size, scaled_size))
                            self.preview_surface.blit(scaled_img, (x, y))
                        else:
                            # Fallback to colored circle
                            pygame.draw.circle(self.preview_surface, (0, 255, 0), 
                                              (x + int(15 * scale), y + int(15 * scale)), 
                                              int(10 * scale))
            
                # Enemy spawn - use enemy tank image
                enemy_spawns = map_data.get('enemy_spawns', [])
                if enemy_spawns:
                    for spawn in enemy_spawns:
                        x = int(spawn[0] * scale)
                        y = int(spawn[1] * scale)
                        
                        # Load enemy tank image
                        images = resource_manager.load_tank_images('enemy', 1, 0)
                        if images and images.get(0):
                            tank_img = images[0][0]
                            scaled_size = int(30 * scale)  # Tank is 30x30
                            scaled_img = pygame.transform.scale(tank_img, (scaled_size, scaled_size))
                            self.preview_surface.blit(scaled_img, (x, y))
                        else:
                            # Fallback to colored circle
                            pygame.draw.circle(self.preview_surface, (255, 0, 0), 
                                              (x + int(15 * scale), y + int(15 * scale)), 
                                              int(10 * scale))
        
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
        # 清理按钮
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


class LobbyScreen(BaseScreen):
    """联机大厅屏幕"""
    
    def on_enter(self):
        super().on_enter()
        
        w, h = self.surface.get_size()
        margin = 24
        col1 = min(560, max(480, int(w * 0.55)))
        col2 = max(360, w - col1 - margin * 3)
        card_h = h - margin * 2
        padding = 16
        line_h = 32
        
        # 左侧：房间列表卡片
        self.left_panel = UIPanel(
            relative_rect=pygame.Rect(margin, margin, col1, card_h),
            manager=self.manager,
            object_id="#lobby_left"
        )
        
        UILabel(
            relative_rect=pygame.Rect(padding, padding, col1 - padding * 2, line_h),
            text="房间列表",
            manager=self.manager,
            container=self.left_panel
        )
        
        self.status_label = UILabel(
            relative_rect=pygame.Rect(padding, padding + line_h + 6, 220, line_h),
            text="状态: 初始化中...",
            manager=self.manager,
            container=self.left_panel
        )
        
        list_y = padding + line_h * 2 + 16
        list_h = card_h - list_y - padding - 60
        self.room_list = UISelectionList(
            relative_rect=pygame.Rect(padding, list_y, col1 - padding * 2, list_h),
            item_list=[], 
            manager=self.manager,
            container=self.left_panel
        )
        
        self.btn_refresh = UIButton(
            relative_rect=pygame.Rect(padding, card_h - padding - 44, 140, 44),
            text='刷新列表',
            manager=self.manager,
            container=self.left_panel
        )
        
        # 右侧：操作卡片
        right_x = margin * 2 + col1
        self.right_panel = UIPanel(
            relative_rect=pygame.Rect(right_x, margin, col2, card_h),
            manager=self.manager,
            object_id="#lobby_right"
        )
        
        UILabel(
            relative_rect=pygame.Rect(padding, padding, col2 - padding * 2, line_h),
            text="玩家信息",
            manager=self.manager,
            container=self.right_panel
        )
        
        UILabel(
            relative_rect=pygame.Rect(padding, padding + line_h + 6, 80, line_h),
            text="用户名:",
            manager=self.manager,
            container=self.right_panel
        )
        self.username_entry = UITextEntryLine(
            relative_rect=pygame.Rect(padding + 80 + 8, padding + line_h + 6, col2 - padding * 2 - 88, line_h),
            manager=self.manager,
            container=self.right_panel
        )
        self.username_entry.set_text("Player1")
        self.context.username = self.username_entry.get_text()
        
        btn_w = col2 - padding * 2
        btn_h = 48
        btn_y = padding + line_h * 2 + 24
        
        self.btn_create = UIButton(
            relative_rect=pygame.Rect(padding, btn_y, btn_w, btn_h),
            text='创建房间',
            manager=self.manager,
            container=self.right_panel
        )
        
        self.btn_join = UIButton(
            relative_rect=pygame.Rect(padding, btn_y + btn_h + 12, btn_w, btn_h),
            text='加入房间',
            manager=self.manager,
            container=self.right_panel
        )
        
        self.btn_back = UIButton(
            relative_rect=pygame.Rect(padding, card_h - padding - 48, btn_w, 48),
            text='返回',
            manager=self.manager,
            container=self.right_panel
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
        
        # Initialize discovery timer if not exists
        if not hasattr(self, 'discovery_timer'):
            self.discovery_timer = 0
            
        # Initialize status update timer
        if not hasattr(self, 'status_update_timer'):
            self.status_update_timer = 0
            
        # Periodic discovery broadcast
        if hasattr(self, 'network_manager') and self.network_manager.stats.role == "client":
            self.discovery_timer += time_delta
            if self.discovery_timer > 1.5:  # Broadcast every 1.5 seconds for more responsive updates
                self.network_manager.broadcast_discovery()
                self.discovery_timer = 0
            
            # Update room list and status more frequently
            self.status_update_timer += time_delta
            if self.status_update_timer > 0.5:  # Update UI every 0.5 seconds
                self.status_update_timer = 0
                
                # Update room list (only if UI is initialized)
                if hasattr(self, 'room_list'):
                    # Get server info with player count if available
                    rooms = []
                    for server in self.network_manager.found_servers:
                        ip, name = server
                        # Try to get player count from network manager stats
                        player_count = getattr(self.network_manager.stats, 'player_count', '?')
                        rooms.append(f"{name} ({ip}) - 玩家: {player_count}")
                    
                    # Only update if changed to avoid flickering/resetting selection
                    current_items = getattr(self, '_cached_room_list', [])
                    if rooms != current_items:
                        print(f"[UI] Updating room list: {rooms}")
                        self.room_list.set_item_list(rooms)
                        self._cached_room_list = rooms
                
                # Update connection status indicator
                if hasattr(self, 'status_label'):
                    if self.network_manager.stats.connected:
                        self.status_label.set_text("状态: 已连接")
                        self.status_label.colour = (0, 255, 0)  # Green for connected
                    else:
                        self.status_label.set_text("状态: 搜索中...")
                        self.status_label.colour = (255, 255, 0)  # Yellow for searching
                
                # Handle status reset timer for refresh operation
                if hasattr(self, 'status_reset_timer'):
                    self.status_reset_timer += time_delta
                    if self.status_reset_timer > 1.0:  # Reset after 1 second
                        self.status_reset_timer = 0

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
                # 记录本地/远程用户名，供后续显示生命值等
                self.context.username = self.username_entry.get_text()
                self.context.remote_username = "Player2"
                self.context.next_state = "room"
                self.context.is_host = True
                self.context.game_mode = "multi"
                
            elif event.ui_element == self.btn_join:
                # Join selected
                # Use manually tracked selection as get_single_selection() can be unreliable
                selected = getattr(self, 'selected_room', None)
                print(f"[UI] Join clicked. Selected: {selected}")
                if selected:
                    # Parse IP from string "RoomName (IP) - 玩家: ?"
                    # Use regex to extract IP address more reliably
                    import re
                    ip_match = re.search(r'\((\d+\.\d+\.\d+\.\d+)\)', selected)
                    if ip_match:
                        ip = ip_match.group(1)
                    else:
                        # Fallback to original method if regex fails
                        ip = selected.split('(')[-1].strip(')')
                        # Remove any trailing text after the IP
                        if ' ' in ip:
                            ip = ip.split(' ')[0]
                    if hasattr(self, 'network_manager'):
                        # Don't call start_client again, already started in on_enter
                        if self.network_manager.connect_to_server(ip):
                            self.context.next_state = "room"
                            self.context.is_host = False
                            self.context.game_mode = "multi"
                            self.context.username = self.username_entry.get_text()
                            self.context.remote_username = "Player1"
                        
            elif event.ui_element == self.btn_refresh:
                if hasattr(self, 'network_manager'):
                    # Update status to show refreshing
                    self.status_label.set_text("状态: 刷新中...")
                    self.status_label.colour = (100, 150, 255)  # Blue for refreshing
                    
                    # Just broadcast, don't restart client
                    self.network_manager.broadcast_discovery()
                    # Clear found servers to force refresh
                    self.network_manager.found_servers.clear()
                    # Also clear cache to ensure UI updates
                    self._cached_room_list = []
                    
                    # Reset status after a short delay
                    if hasattr(self, 'status_reset_timer'):
                        self.status_reset_timer = 0
                    else:
                        self.status_reset_timer = 0

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
        w, h = self.surface.get_size()
        margin = 24
        col_left = 360
        col_right = w - col_left - margin * 3
        col_right = max(540, col_right)
        card_h = h - margin * 2
        padding = 16
        line_h = 30
        
        self.local_ready = False
        self.remote_ready = False
        self._sent_initial_ready = False
        self._sent_name = False  # 防止重复发送昵称
        
        # 左侧：玩家与准备
        self.left_panel = UIPanel(
            relative_rect=pygame.Rect(margin, margin, col_left, card_h),
            manager=self.manager,
            object_id="#room_left"
        )
        
        UILabel(
            relative_rect=pygame.Rect(padding, padding, col_left - padding * 2, line_h),
            text="玩家与状态",
            manager=self.manager,
            container=self.left_panel
        )
        
        self.connection_status = UILabel(
            relative_rect=pygame.Rect(padding, padding + line_h + 6, col_left - padding * 2, line_h),
            text="状态: 初始化中...",
            manager=self.manager,
            container=self.left_panel
        )
        
        self.player_list = UISelectionList(
            relative_rect=pygame.Rect(padding, padding + line_h * 2 + 16, col_left - padding * 2, 140),
            item_list=["Player1 (Host)"], 
            manager=self.manager,
            container=self.left_panel
        )
        
        # 准备与离开
        self.btn_ready = UIButton(
            relative_rect=pygame.Rect(padding, card_h - padding - 140, col_left - padding * 2, 44),
            text='准备',
            manager=self.manager,
            container=self.left_panel
        )
        
        self.ready_status_label = UILabel(
            relative_rect=pygame.Rect(padding, card_h - padding - 140 + 52, col_left - padding * 2, 28),
            text="状态: 未准备",
            manager=self.manager,
            container=self.left_panel
        )
        
        self.btn_leave = UIButton(
            relative_rect=pygame.Rect(padding, card_h - padding - 44, col_left - padding * 2, 44),
            text='离开房间',
            manager=self.manager,
            container=self.left_panel
        )
        
        # 右侧：房主设置 + 坦克选择
        right_x = margin * 2 + col_left
        self.right_panel = UIPanel(
            relative_rect=pygame.Rect(right_x, margin, col_right, card_h),
            manager=self.manager,
            object_id="#room_right"
        )
        
        UILabel(
            relative_rect=pygame.Rect(padding, padding, col_right - padding * 2, line_h),
            text="房间设置",
            manager=self.manager,
            container=self.right_panel
        )
        
        # 游戏模式
        UILabel(
            relative_rect=pygame.Rect(padding, padding + line_h + 6, 90, line_h),
            text="游戏模式:",
            manager=self.manager,
            container=self.right_panel
        )
        self.game_mode_dropdown = UIDropDownMenu(
            options_list=["合作模式", "对战模式", "混战模式", "关卡模式"],
            starting_option="合作模式",
            relative_rect=pygame.Rect(padding + 100, padding + line_h + 6, 180, line_h),
            manager=self.manager,
            container=self.right_panel
        )
        self.context.multiplayer_game_mode = "coop"
        if not getattr(self.context, 'is_host', False):
            self.game_mode_dropdown.disable()
        
        # 关卡/地图区域
        maps_y = padding + line_h * 2 + 20
        UILabel(
            relative_rect=pygame.Rect(padding, maps_y, 90, line_h),
            text="选择地图:",
            manager=self.manager,
            container=self.right_panel
        )
        
        self._load_available_maps()
        list_w = int(col_right * 0.55)
        list_h = 160
        self.map_selection_list = UISelectionList(
            relative_rect=pygame.Rect(padding, maps_y + line_h + 8, list_w, list_h),
            item_list=self.map_display_names,
            default_selection=self.map_display_names[0],
            manager=self.manager,
            container=self.right_panel
        )
        self.selected_map = self.map_names[0]
        self.context.selected_map = self.selected_map
        if not getattr(self.context, 'is_host', False):
            self.map_selection_list.disable()
        
        # 难度
        UILabel(
            relative_rect=pygame.Rect(padding + list_w + 16, maps_y, 90, line_h),
            text="敌人难度:",
            manager=self.manager,
            container=self.right_panel
        )
        from src.game_engine.ai_config import get_difficulty_names, get_difficulty_key_by_name, DEFAULT_DIFFICULTY, DIFFICULTY_CONFIGS
        self.difficulty_names = get_difficulty_names()
        default_diff_name = DIFFICULTY_CONFIGS[DEFAULT_DIFFICULTY]["name"]
        self.difficulty_dropdown = UIDropDownMenu(
            options_list=self.difficulty_names,
            starting_option=default_diff_name,
            relative_rect=pygame.Rect(padding + list_w + 16, maps_y + line_h + 8, 180, line_h),
            manager=self.manager,
            container=self.right_panel
        )
        self.context.enemy_difficulty = DEFAULT_DIFFICULTY
        if not getattr(self.context, 'is_host', False):
            self.difficulty_dropdown.disable()
        
        # 坦克选择区域
        tanks_y = maps_y + line_h + list_h + 32
        UILabel(
            relative_rect=pygame.Rect(padding, tanks_y, 100, line_h),
            text="你的坦克",
            manager=self.manager,
            container=self.right_panel
        )
        self.local_image_rect = pygame.Rect(padding, tanks_y + line_h + 6, 100, 100)
        self.local_image_elem = None
        self.btn_prev = UIButton(
            relative_rect=pygame.Rect(padding, tanks_y + line_h + 6 + 110, 48, 32),
            text='<',
            manager=self.manager,
            container=self.right_panel
        )
        self.btn_next = UIButton(
            relative_rect=pygame.Rect(padding + 58, tanks_y + line_h + 6 + 110, 48, 32),
            text='>',
            manager=self.manager,
            container=self.right_panel
        )
        
        UILabel(
            relative_rect=pygame.Rect(padding + 180, tanks_y, 100, line_h),
            text="对手坦克",
            manager=self.manager,
            container=self.right_panel
        )
        self.remote_image_rect = pygame.Rect(padding + 180, tanks_y + line_h + 6, 100, 100)
        self.remote_image_elem = None
        
        self.local_tank_id = 1
        self.remote_tank_id = 1
        self.context.player_tank_id = 1
        self.context.enemy_tank_id = 1
        self._update_images()
        
        # 开始游戏按钮（仅房主）
        self.btn_start = UIButton(
            relative_rect=pygame.Rect(col_right - padding - 180, card_h - padding - 48, 180, 48),
            text='开始游戏',
            manager=self.manager,
            container=self.right_panel
        )
        if not getattr(self.context, 'is_host', False):
            self.btn_start.hide()
        else:
            self.btn_start.disable()
        
        # 进入房间时，立即发送自己的坦克选择给对方（房主和客户端都需要）
        if hasattr(self, 'network_manager') and self.network_manager.stats.connected:
            print(f"[Room] 进入房间，发送初始坦克选择: {self.local_tank_id} (is_host: {self.context.is_host})")
            self.network_manager.send_lobby_update(self.local_tank_id)

    def _load_available_maps(self):
        """加载可用地图列表"""
        from src.utils.map_loader import map_loader
        available_maps = map_loader.get_available_maps()
        
        self.map_names = []
        self.map_display_names = []
        self.map_name_mapping = {}
        
        if not available_maps:
            # 处理默认地图情况
            self.map_names = ["default"]
            self.map_display_names = ["默认地图"]
            self.map_name_mapping = {"默认地图": "default"}
            return
        
        for map_info in available_maps:
            # map_info是包含地图信息的字典
            map_identifier = map_info["filename"]  # 使用文件名作为唯一标识符
            
            try:
                map_data = map_loader.load_map(map_identifier)
                if map_data and 'name' in map_data:
                    wall_count = len(map_data.get('walls', []))
                    display_name = f"{map_data['name']} ({wall_count} 个障碍物)"
                else:
                    display_name = map_identifier.replace(".json", "")
            except Exception as e:
                print(f"加载地图 {map_identifier} 时出错: {e}")
                display_name = map_identifier.replace(".json", "")
            
            self.map_names.append(map_identifier)
            self.map_display_names.append(display_name)
            self.map_name_mapping[display_name] = map_identifier
    
    def _update_images(self):
        # Local
        if self.local_image_elem: self.local_image_elem.kill()
        images = resource_manager.load_tank_images('player', self.local_tank_id, 0)
        surf = pygame.transform.scale(images[0][0], (100, 100)) if images and images.get(0) else pygame.Surface((100, 100))
        self.local_image_elem = UIImage(relative_rect=self.local_image_rect, image_surface=surf, manager=self.manager, container=self.right_panel)
        
        # Remote
        if self.remote_image_elem: self.remote_image_elem.kill()
        images = resource_manager.load_tank_images('player', self.remote_tank_id, 0)
        surf = pygame.transform.scale(images[0][0], (100, 100)) if images and images.get(0) else pygame.Surface((100, 100))
        self.remote_image_elem = UIImage(relative_rect=self.remote_image_rect, image_surface=surf, manager=self.manager, container=self.right_panel)
    
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
        
        # Initialize update timer if not exists
        if not hasattr(self, 'room_update_timer'):
            self.room_update_timer = 0
            
        self.room_update_timer += time_delta
        
        # Update UI every 0.5 seconds for more responsive feel
        # Track if we've sent initial ready state
        if not hasattr(self, '_sent_initial_ready'):
            self._sent_initial_ready = False
        
        # Process network messages every frame (not just every 0.5s) for immediate response
        if hasattr(self, 'network_manager'):
            if self.network_manager.stats.connected:
                # 首次连接后同步昵称
                if not self._sent_name:
                    player_id = 1 if self.context.is_host else 2
                    self.network_manager.send_event("player_name", {
                        "id": player_id,
                        "name": self.context.username
                    })
                    self._sent_name = True

                # Send initial ready state if not sent yet
                if not self._sent_initial_ready:
                    self.network_manager.send_ready_state(self.local_ready)
                    self._sent_initial_ready = True
                
                # Update UI elements every 0.5s to avoid flickering
                if self.room_update_timer > 0.5:
                    self.room_update_timer = 0
                    
                    # Update player list based on connection
                    host_name = self.context.username if self.context.is_host else getattr(self.context, "remote_username", "Player1")
                    client_name = getattr(self.context, "remote_username", "Player2") if self.context.is_host else self.context.username
                    self.player_list.set_item_list([
                        f"{host_name} (Host)",
                        f"{client_name} (Client)"
                    ])
                    
                    # Update connection status label
                    if hasattr(self, 'connection_status'):
                        self.connection_status.set_text("状态: 已连接")
                        self.connection_status.colour = (0, 255, 0)  # Green for connected
                
                # Process network messages (every frame for immediate response)
                if self.context.is_host:
                    # Host: Check for lobby updates from client
                    msgs = self.network_manager.get_inputs()
                    for msg in msgs:
                        if msg.get("type") == "lobby_update":
                            payload = msg.get("payload")
                            if payload and "tank_id" in payload:
                                new_tank_id = payload["tank_id"]
                                print(f"[Host] 收到客户端坦克选择更新: {new_tank_id} (当前显示: {self.remote_tank_id})")
                                self.remote_tank_id = new_tank_id
                                self.context.enemy_tank_id = self.remote_tank_id
                                self._update_images()
                                print(f"[Host] 已更新对手坦克显示为: {self.remote_tank_id}")
                                # 房主收到客户端的坦克选择后，将自己的坦克选择发送给客户端（确保同步）
                                self.network_manager.send_lobby_update(self.local_tank_id)
                        elif msg.get("type") == "ready_state":
                            payload = msg.get("payload")
                            if payload is not None:
                                self.remote_ready = payload.get("is_ready", False)
                                self._update_ready_status()
                                # 主机收到客户端准备状态后，将自己的准备状态发送给客户端
                                self.network_manager.send_ready_state(self.local_ready)
                        elif msg.get("type") == "player_name":
                            payload = msg.get("payload", {})
                            if payload.get("id") == 2 and payload.get("name"):
                                self.context.remote_username = payload["name"]
                                # 更新玩家列表显示
                                host_name = self.context.username
                                client_name = self.context.remote_username
                                self.player_list.set_item_list([
                                    f"{host_name} (Host)",
                                    f"{client_name} (Client)"
                                ])
                else:
                    # Client: Check for game start and lobby updates
                    # 每帧都检查事件，不要等待0.5秒，确保及时响应
                    self.network_manager.get_latest_state()
                    
                    events = self.network_manager.get_events()
                    if events:
                        print(f"[Client] 收到 {len(events)} 个事件: {[e.get('type') for e in events]}")
                    
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
                                
                                # Store game mode
                                self.context.multiplayer_game_mode = payload.get("game_mode", "coop")
                                self.context.level_number = payload.get("level_number")
                                
                                print(f"[Client] 游戏模式: {self.context.multiplayer_game_mode}")
                                if self.context.level_number:
                                    print(f"[Client] 关卡编号: {self.context.level_number}")
                                
                                self.local_tank_id = self.context.player_tank_id
                                
                                self.context.next_state = "game"
                        
                        elif event.get("type") == "lobby_update":
                            payload = event.get("payload")
                            if payload and "tank_id" in payload:
                                new_tank_id = payload["tank_id"]
                                print(f"[Client] 收到房主坦克选择更新: {new_tank_id} (当前显示: {self.remote_tank_id})")
                                self.remote_tank_id = new_tank_id
                                self.context.enemy_tank_id = self.remote_tank_id
                                self._update_images()
                                print(f"[Client] 已更新对手坦克显示为: {self.remote_tank_id}")
                                # 客户端收到房主的坦克选择后，将自己的坦克选择发送给房主（确保同步）
                                self.network_manager.send_lobby_update(self.local_tank_id)
                        
                        elif event.get("type") == "ready_state":
                            payload = event.get("payload")
                            if payload is not None:
                                self.remote_ready = payload.get("is_ready", False)
                                self._update_ready_status()
                                # 客户端收到主机准备状态后，将自己的准备状态发送给主机
                                self.network_manager.send_ready_state(self.local_ready)
                        
                        elif event.get("type") == "player_name":
                            payload = event.get("payload", {})
                            if payload.get("id") == 1 and payload.get("name"):
                                self.context.remote_username = payload["name"]
                                # 更新玩家列表显示
                                host_name = self.context.remote_username
                                client_name = self.context.username
                                self.player_list.set_item_list([
                                    f"{host_name} (Host)",
                                    f"{client_name} (Client)"
                                ])
                        
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
                        
                        elif event.get("type") == "game_mode_update":
                            payload = event.get("payload")
                            if payload and "game_mode" in payload:
                                game_mode = payload["game_mode"]
                                self.context.multiplayer_game_mode = game_mode
                                # Update UI
                                game_mode_map = {
                                    "coop": "合作模式",
                                    "pvp": "对战模式",
                                    "mixed": "混战模式",
                                    "level": "关卡模式"
                                }
                                game_mode_name = game_mode_map.get(game_mode, "合作模式")
                                
                                # Update dropdown selection
                                rect = self.game_mode_dropdown.relative_rect
                                manager = self.game_mode_dropdown.ui_manager
                                self.game_mode_dropdown.kill()
                                self.game_mode_dropdown = UIDropDownMenu(
                                    options_list=["合作模式", "对战模式", "混战模式", "关卡模式"],
                                    starting_option=game_mode_name,
                                    relative_rect=rect,
                                    manager=manager
                                )
                                self.game_mode_dropdown.disable()
                                
                                # Update maps for this game mode
                                self._update_maps_for_game_mode(game_mode)
                        
                        elif event.get("type") == "ready_state":
                            payload = event.get("payload")
                            if payload is not None:
                                self.remote_ready = payload.get("is_ready", False)
                                self._update_ready_status()
            else:
                # Disconnected - update UI every 0.5s
                if self.room_update_timer > 0.5:
                    self.room_update_timer = 0
                    self.player_list.set_item_list(["Player1 (Host)"])
                    
                    # Reset remote ready if disconnected
                    if self.remote_ready:
                        self.remote_ready = False
                        self._update_ready_status()
                    
                    # Reset initial ready state flag when disconnected
                    self._sent_initial_ready = False
                    self._sent_name = False
                    
                    # Update connection status label if exists
                    if hasattr(self, 'connection_status'):
                        self.connection_status.set_text("状态: 连接断开")
                        self.connection_status.colour = (255, 0, 0)  # Red for disconnected

    def on_exit(self):
        """清理房间屏幕资源"""
        super().on_exit()
        
        # 清理网络连接（如果存在）
        if hasattr(self, 'network_manager'):
            print("[RoomScreen] 清理网络连接...")
            self.network_manager.stop()
        
        # 清理UI元素
        if hasattr(self, 'left_panel'):
            self.left_panel.kill()
        if hasattr(self, 'right_panel'):
            self.right_panel.kill()
        if hasattr(self, 'btn_ready'):
            self.btn_ready.kill()
        if hasattr(self, 'btn_leave'):
            self.btn_leave.kill()
        if hasattr(self, 'btn_start'):
            self.btn_start.kill()
        if hasattr(self, 'btn_prev'):
            self.btn_prev.kill()
        if hasattr(self, 'btn_next'):
            self.btn_next.kill()
        if hasattr(self, 'map_selection_list'):
            self.map_selection_list.kill()
        if hasattr(self, 'game_mode_dropdown'):
            self.game_mode_dropdown.kill()
        if hasattr(self, 'difficulty_dropdown'):
            self.difficulty_dropdown.kill()
        if hasattr(self, 'player_list'):
            self.player_list.kill()
        if hasattr(self, 'connection_status'):
            self.connection_status.kill()
        if hasattr(self, 'ready_status_label'):
            self.ready_status_label.kill()
        if hasattr(self, 'local_image_elem'):
            self.local_image_elem.kill()
        if hasattr(self, 'remote_image_elem'):
            self.remote_image_elem.kill()
        
        # 清理房间状态
        self.local_ready = False
        self.remote_ready = False
        self._sent_initial_ready = False
        self._sent_name = False
        
        # 清理上下文中的联机状态（但不完全清除，因为可能还要返回大厅）
        # 只清理房间相关的临时状态
        if hasattr(self.context, 'local_tank_id'):
            delattr(self.context, 'local_tank_id')
        if hasattr(self.context, 'remote_tank_id'):
            delattr(self.context, 'remote_tank_id')
    
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
                    from src.utils.map_loader import map_loader
                    # 始终尝试加载地图数据（包括默认地图），便于客户端缺图时使用
                    map_data = map_loader.load_map(self.selected_map)
                    if map_data:
                        print(f"[Host] 发送地图数据: {self.selected_map}")
                    else:
                        print(f"[Host] 未找到地图文件 {self.selected_map}，将发送空地图数据")
                    
                    # Get game mode
                    game_mode = getattr(self.context, 'multiplayer_game_mode', 'coop')
                    
                    # For level mode, extract level number
                    level_number = None
                    if game_mode == "level" and self.selected_map.startswith("level_"):
                        try:
                            level_number = int(self.selected_map.split("_")[1])
                        except (IndexError, ValueError):
                            pass
                    
                    # Send Game Start with tank IDs, map name, map data, and game mode
                    self.network_manager.send_game_start(
                        self.local_tank_id, 
                        self.remote_tank_id, 
                        self.selected_map, 
                        map_data,
                        game_mode=game_mode,
                        level_number=level_number
                    )
                
                self.context.player_tank_id = self.local_tank_id
                self.context.enemy_tank_id = self.remote_tank_id
                self.context.selected_map = self.selected_map
                self.context.next_state = "game"
                
            elif event.ui_element == self.btn_prev:
                self.local_tank_id -= 1
                if self.local_tank_id < 1: self.local_tank_id = 4
                self._update_images()
                if hasattr(self, 'network_manager'):
                    print(f"[Room] 选择坦克: {self.local_tank_id} (is_host: {self.context.is_host})")
                    self.network_manager.send_lobby_update(self.local_tank_id)
                    
            elif event.ui_element == self.btn_next:
                self.local_tank_id += 1
                if self.local_tank_id > 4: self.local_tank_id = 1
                self._update_images()
                if hasattr(self, 'network_manager'):
                    print(f"[Room] 选择坦克: {self.local_tank_id} (is_host: {self.context.is_host})")
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
            
            elif hasattr(self, 'game_mode_dropdown') and event.ui_element == self.game_mode_dropdown:
                if self.context.is_host:
                    # Fallback to selected_option if event.text is None
                    text = event.text if event.text is not None else self.game_mode_dropdown.selected_option
                    
                    if text is None or text == "None":
                        text = "合作模式"
                    
                    # Map UI text to game mode
                    game_mode_map = {
                        "合作模式": "coop",
                        "对战模式": "pvp",
                        "混战模式": "mixed",
                        "关卡模式": "level"
                    }
                    
                    selected_game_mode = game_mode_map.get(text, "coop")
                    self.context.multiplayer_game_mode = selected_game_mode
                    print(f"[Host] 游戏模式选择: {text} -> {selected_game_mode}")
                    
                    # 根据游戏模式更新地图列表
                    self._update_maps_for_game_mode(selected_game_mode)
                    
                    # Broadcast to client
                    if hasattr(self, 'network_manager'):
                        self.network_manager.send_event("game_mode_update", {"game_mode": selected_game_mode})

    def _update_maps_for_game_mode(self, game_mode):
        """根据游戏模式更新地图列表"""
        if game_mode == "level":
            # 关卡模式：加载联机关卡地图
            self._load_multiplayer_level_maps()
        else:
            # 其他模式：加载普通地图
            self._load_available_maps()
        
        # 更新地图选择列表
        if hasattr(self, 'map_selection_list'):
            # 更新列表
            self.map_selection_list.set_item_list(self.map_display_names)
            
            # 设置默认选择（如果列表不为空）
            if self.map_display_names:
                self.selected_map = self.map_names[0]
                self.context.selected_map = self.selected_map
    
    def _load_multiplayer_level_maps(self):
        """加载联机关卡地图列表"""
        from src.utils.multiplayer_level_progress import get_available_multiplayer_levels
        from src.utils.multiplayer_map_generator import multiplayer_map_generator
        
        available_levels = get_available_multiplayer_levels()
        
        self.map_names = []
        self.map_display_names = []
        self.map_name_mapping = {}
        
        for level_info in available_levels:
            if level_info["unlocked"]:
                level_num = level_info["level"]
                map_name = f"level_{level_num}"
                display_name = f"关卡 {level_num}"
                
                # 检查地图文件是否存在，不存在则生成
                if not multiplayer_map_generator.load_multiplayer_map("level", map_name):
                    multiplayer_map_generator.generate_level_map(level_num)
                
                self.map_names.append(map_name)
                self.map_display_names.append(display_name)
                self.map_name_mapping[display_name] = map_name
    
    def _load_available_maps(self):
        """加载可用地图列表"""
        from src.utils.map_loader import map_loader
        
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
                            display_name = map_name.replace(".json", "")
                    except Exception as e:
                        print(f"加载地图 {map_name} 时出错: {e}")
                        display_name = map_name.replace(".json", "")
                
                self.map_display_names.append(display_name)
                self.map_name_mapping[display_name] = map_name

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
                try:
                    lock_text = self.small_font.render("🔒", True, (255, 0, 0))
                except Exception:
                    lock_text = self.small_font.render("锁", True, (255, 0, 0))
                if lock_text.get_width() > 0 and lock_text.get_height() > 0:
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

        # AI 目标权重滑条
        UILabel(
            relative_rect=pygame.Rect((center_x - 200, center_y - 40), (200, 30)),
            text="AI 攻击玩家权重",
            manager=self.manager
        )
        self.ai_player_slider = UIHorizontalSlider(
            relative_rect=pygame.Rect((center_x + 10, center_y - 40), (150, 25)),
            start_value=self.context.ai_player_weight,
            value_range=(0.5, 2.0),
            manager=self.manager
        )
        self.ai_player_value = UILabel(
            relative_rect=pygame.Rect((center_x + 170, center_y - 40), (60, 25)),
            text=f"{self.context.ai_player_weight:.2f}",
            manager=self.manager
        )

        UILabel(
            relative_rect=pygame.Rect((center_x - 200, center_y), (200, 30)),
            text="AI 攻击基地权重",
            manager=self.manager
        )
        self.ai_base_slider = UIHorizontalSlider(
            relative_rect=pygame.Rect((center_x + 10, center_y), (150, 25)),
            start_value=self.context.ai_base_weight,
            value_range=(0.5, 2.0),
            manager=self.manager
        )
        self.ai_base_value = UILabel(
            relative_rect=pygame.Rect((center_x + 170, center_y), (60, 25)),
            text=f"{self.context.ai_base_weight:.2f}",
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
                # 保存AI权重到上下文
                self.context.ai_player_weight = float(self.ai_player_slider.get_current_value())
                self.context.ai_base_weight = float(self.ai_base_slider.get_current_value())
                # 如果有游戏引擎实例，更新运行时权重
                engine = getattr(self.context, "screen_manager", None)
                if engine and getattr(engine, "game_engine", None):
                    ge = engine.game_engine
                    ge.ai_player_weight = self.context.ai_player_weight
                    ge.ai_base_weight = self.context.ai_base_weight
                # 更新显示数值
                self.ai_player_value.set_text(f"{self.context.ai_player_weight:.2f}")
                self.ai_base_value.set_text(f"{self.context.ai_base_weight:.2f}")
            elif event.ui_element == self.btn_back:
                # 返回主菜单
                self.context.next_state = "menu"
        elif event.type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED:
            if event.ui_element == self.ai_player_slider:
                self.ai_player_value.set_text(f"{self.ai_player_slider.get_current_value():.2f}")
            elif event.ui_element == self.ai_base_slider:
                self.ai_base_value.set_text(f"{self.ai_base_slider.get_current_value():.2f}")
        
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