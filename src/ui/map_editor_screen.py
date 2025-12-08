"""
地图编辑器界面 - 适配16:9屏幕比例和动态分辨率
"""
# 必须在导入pygame_gui之前初始化i18n
import src.ui.init_i18n

import json
import os
import pygame
import pygame_gui
from pygame_gui.elements import UIButton, UILabel, UITextEntryLine
from pygame_gui.windows import UIFileDialog, UIMessageWindow

from src.ui.screen_manager import BaseScreen
from src.utils.resource_manager import resource_manager
from src.game_engine.wall import Wall
from src.config.game_config import config


class MapEditorScreen(BaseScreen):
    """地图编辑器屏幕 - 使用与游戏世界一致的固定网格大小"""
    
    # 使用与游戏相同的网格大小
    GRID_SIZE = config.GRID_SIZE
    
    # 固定的网格行列数（与游戏世界保持一致）
    FIXED_GRID_COLS = 28
    FIXED_GRID_ROWS = 21
    
    # 根据固定网格计算的地图尺寸
    DEFAULT_MAP_WIDTH = FIXED_GRID_COLS * GRID_SIZE
    DEFAULT_GAME_HEIGHT = FIXED_GRID_ROWS * GRID_SIZE
    
    TOOLBAR_HEIGHT = 90  # 工具栏高度
    
    # 工具类型（对应wall.py中的常量）
    TOOL_BRICK = Wall.BRICK      # 砖块（可摧毁）
    TOOL_STEEL = Wall.STEEL      # 钢块（不可摧毁）
    TOOL_GRASS = Wall.GRASS      # 草地
    TOOL_RIVER = Wall.RIVER      # 河流
    TOOL_BASE = Wall.BASE       # 基地（老鹰）
    TOOL_ERASER = 99    # 橡皮擦（特殊工具）
    TOOL_PLAYER_SPAWN = 100  # 玩家出生点
    TOOL_ENEMY_SPAWN = 101   # 敌人出生点
    
    def __init__(self, surface, context, ui_manager, network_manager=None):
        super().__init__(surface, context, ui_manager, network_manager)
        self.current_tool = self.TOOL_BRICK
        self.walls = []  # List of {x, y, type}
        
        # 初始化空的出生点列表，不自动添加出生点
        self.player_spawns = []  # 玩家出生点
        self.enemy_spawns = []  # 敌人出生点
        
        self.is_dragging = False
        self.map_name = "new_map"
        
        # 初始化尺寸参数（基于固定网格）
        self.MAP_WIDTH = self.DEFAULT_MAP_WIDTH
        self.GAME_HEIGHT = self.DEFAULT_GAME_HEIGHT
        self.MAP_HEIGHT = self.GAME_HEIGHT + self.TOOLBAR_HEIGHT
        
        # 使用固定的网格参数（与游戏世界保持一致）
        self.GRID_COLS = self.FIXED_GRID_COLS
        self.GRID_ROWS = self.FIXED_GRID_ROWS
        
        # 工具栏高度
        self.toolbar_height = self.TOOLBAR_HEIGHT
        
        # 画布偏移量（用于渲染）
        self.canvas_y_offset = self.TOOLBAR_HEIGHT
        
        # 计算并保存宽高比
        self.ASPECT_RATIO = self.MAP_WIDTH / self.GAME_HEIGHT
        
    def on_enter(self):
        super().on_enter()
        
        # 确保使用最新的UI管理器实例
        self.manager = self.ui_manager.get_manager()
        
        # 创建工具栏按钮
        self._create_toolbar_buttons()
    
    def on_exit(self):
        """退出地图编辑器时的清理工作"""
        # 清理当前屏幕的UI元素
        self.ui_manager.clear()
        super().on_exit()
    
    def _create_toolbar_buttons(self):
        """创建工具栏按钮（用于窗口大小改变时重新创建）"""
        # 确保使用最新的UI管理器实例
        self.manager = self.ui_manager.get_manager()
        
        # 清除可能存在的旧UI元素（防止重复）
        self.ui_manager.clear()
        
        # 工具栏按钮
        btn_y = 10
        btn_spacing = 80
        
        self.btn_brick = UIButton(
            relative_rect=pygame.Rect((10, btn_y), (70, 30)),
            text='砖墙',
            manager=self.manager
        )
        
        self.btn_steel = UIButton(
            relative_rect=pygame.Rect((10 + btn_spacing, btn_y), (70, 30)),
            text='钢墙',
            manager=self.manager
        )
        
        self.btn_grass = UIButton(
            relative_rect=pygame.Rect((10 + btn_spacing * 2, btn_y), (70, 30)),
            text='草地',
            manager=self.manager
        )
        
        self.btn_river = UIButton(
            relative_rect=pygame.Rect((10 + btn_spacing * 3, btn_y), (70, 30)),
            text='河流',
            manager=self.manager
        )
        
        self.btn_base = UIButton(
            relative_rect=pygame.Rect((10 + btn_spacing * 4, btn_y), (70, 30)),
            text='基地',
            manager=self.manager
        )
        
        self.btn_eraser = UIButton(
            relative_rect=pygame.Rect((10 + btn_spacing * 5, btn_y), (70, 30)),
            text='橡皮擦',
            manager=self.manager
        )
        
        # 第二行按钮
        btn_y2 = 50
        self.btn_player_spawn = UIButton(
            relative_rect=pygame.Rect((10, btn_y2), (100, 30)),
            text='玩家出生点',
            manager=self.manager
        )
        
        self.btn_enemy_spawn = UIButton(
            relative_rect=pygame.Rect((120, btn_y2), (100, 30)),
            text='敌人出生点',
            manager=self.manager
        )
        
        # 功能按钮
        self.btn_save = UIButton(
            relative_rect=pygame.Rect((230, btn_y2), (70, 30)),
            text='保存',
            manager=self.manager
        )
        
        self.btn_load = UIButton(
            relative_rect=pygame.Rect((310, btn_y2), (70, 30)),
            text='加载',
            manager=self.manager
        )
        
        self.btn_clear = UIButton(
            relative_rect=pygame.Rect((390, btn_y2), (70, 30)),
            text='清空',
            manager=self.manager
        )
        
        self.btn_back = UIButton(
            relative_rect=pygame.Rect((470, btn_y2), (70, 30)),
            text='返回',
            manager=self.manager
        )
        
        # 地图名称输入
        UILabel(
            relative_rect=pygame.Rect((550, btn_y2), (80, 30)),
            text='地图名称:',
            manager=self.manager
        )
        
        self.map_name_entry = UITextEntryLine(
            relative_rect=pygame.Rect((640, btn_y2), (150, 30)),
            manager=self.manager
        )
        self.map_name_entry.set_text(self.map_name)
        
        # 显示当前网格信息
        grid_info = f"网格: {self.GRID_COLS}x{self.GRID_ROWS} (尺寸: {self.MAP_WIDTH}x{self.GAME_HEIGHT})"
        self.grid_info_label = UILabel(
            relative_rect=pygame.Rect((800, btn_y2), (250, 30)),
            text=grid_info,
            manager=self.manager
        )
    
    def handle_event(self, event):
        # 处理UI事件
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.btn_brick:
                self.current_tool = self.TOOL_BRICK
            elif event.ui_element == self.btn_steel:
                self.current_tool = self.TOOL_STEEL
            elif event.ui_element == self.btn_grass:
                self.current_tool = self.TOOL_GRASS
            elif event.ui_element == self.btn_river:
                self.current_tool = self.TOOL_RIVER
            elif event.ui_element == self.btn_base:
                self.current_tool = self.TOOL_BASE
            elif event.ui_element == self.btn_eraser:
                self.current_tool = self.TOOL_ERASER
            elif event.ui_element == self.btn_player_spawn:
                self.current_tool = self.TOOL_PLAYER_SPAWN
            elif event.ui_element == self.btn_enemy_spawn:
                self.current_tool = self.TOOL_ENEMY_SPAWN
            elif event.ui_element == self.btn_save:
                self._save_map()
            elif event.ui_element == self.btn_load:
                self._load_map()
            elif event.ui_element == self.btn_clear:
                self._clear_map()
            elif event.ui_element == self.btn_back:
                # 返回到主菜单
                if hasattr(self.context, 'screen_manager'):
                    self.context.screen_manager.set_state("menu")
                else:
                    print("无法获取屏幕管理器")
        
        # 处理鼠标事件
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # 左键点击
                pos = pygame.mouse.get_pos()
                self._handle_click(pos)
                self.is_dragging = True
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:  # 左键释放
                self.is_dragging = False
        
        elif event.type == pygame.MOUSEMOTION:
            if self.is_dragging:
                pos = pygame.mouse.get_pos()
                self._handle_click(pos)
        
        # 处理键盘事件
        elif event.type == pygame.KEYDOWN:
            # 添加键盘快捷键支持
            if event.key == pygame.K_1:
                self.current_tool = self.TOOL_BRICK
            elif event.key == pygame.K_2:
                self.current_tool = self.TOOL_STEEL
            elif event.key == pygame.K_3:
                self.current_tool = self.TOOL_GRASS
            elif event.key == pygame.K_4:
                self.current_tool = self.TOOL_RIVER
            elif event.key == pygame.K_5:
                self.current_tool = self.TOOL_BASE
            elif event.key == pygame.K_e:
                self.current_tool = self.TOOL_ERASER
            elif event.key == pygame.K_p:
                self.current_tool = self.TOOL_PLAYER_SPAWN
            elif event.key == pygame.K_q:
                self.current_tool = self.TOOL_ENEMY_SPAWN
            elif event.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_CTRL:
                self._save_map()
            elif event.key == pygame.K_l and pygame.key.get_mods() & pygame.KMOD_CTRL:
                self._load_map()
            elif event.key == pygame.K_ESCAPE:
                # 返回到主菜单
                if hasattr(self.context, 'screen_manager'):
                    self.context.screen_manager.set_state("menu")
                else:
                    print("无法获取屏幕管理器")
        
        # 处理窗口大小改变事件
        elif event.type == pygame.VIDEORESIZE:
            self.handle_window_resized(event.size[0], event.size[1])
    
    def _handle_click(self, pos):
        """处理鼠标点击 - 使用与游戏相同的坐标系统，适应居中显示的界面"""
        x, y = pos
        
        # 计算地图区域的居中偏移量和缩放因子（与渲染保持一致）
        window_width, window_height = self.surface.get_size()
        map_width = self.MAP_WIDTH
        map_height = self.GAME_HEIGHT
        toolbar_height = self.TOOLBAR_HEIGHT
        
        # 计算缩放比例，确保地图完整显示在屏幕上
        available_width = window_width
        available_height = window_height - toolbar_height
        
        # 计算水平和垂直缩放比例
        scale_x = available_width / map_width
        scale_y = available_height / map_height
        
        # 使用较小的缩放比例，确保地图完整显示
        scale_factor = min(scale_x, scale_y, 1.0)  # 不超过1.0倍缩放
        
        # 计算缩放后的地图尺寸
        scaled_map_width = int(map_width * scale_factor)
        scaled_map_height = int(map_height * scale_factor)
        scaled_grid_size = int(self.GRID_SIZE * scale_factor)
        
        # 计算居中偏移
        x_offset = (window_width - scaled_map_width) // 2
        y_offset = (window_height - toolbar_height - scaled_map_height) // 2 + toolbar_height
        
        # 检查是否在地图区域内
        if y < y_offset or y >= y_offset + scaled_map_height or x < x_offset or x >= x_offset + scaled_map_width:
            return
        
        # 转换为网格坐标，考虑缩放因子
        grid_x = (x - x_offset) // scaled_grid_size
        grid_y = (y - y_offset) // scaled_grid_size
        
        # 转换为游戏坐标系，使用原始GRID_SIZE
        game_x = grid_x * self.GRID_SIZE
        game_y = grid_y * self.GRID_SIZE
        
        # 检查边界，确保在有效地图范围内
        if game_x < 0 or game_x >= self.MAP_WIDTH or game_y < 0 or game_y >= self.GAME_HEIGHT:
            return
        
        if self.current_tool == self.TOOL_ERASER:
            self._remove_item_at(game_x, game_y)
        elif self.current_tool == self.TOOL_PLAYER_SPAWN:
            # 检查该位置是否有墙体或敌人出生点
            has_wall = any(w['x'] == game_x and w['y'] == game_y for w in self.walls)
            overlaps_enemy = any(s[0] == game_x and s[1] == game_y for s in self.enemy_spawns)
            overlaps_player = any(s[0] == game_x and s[1] == game_y for s in self.player_spawns)
            
            # 如果没有墙体、敌人出生点且不重复，则放置玩家出生点
            if not has_wall and not overlaps_enemy and not overlaps_player:
                self.player_spawns.append([game_x, game_y])
        elif self.current_tool == self.TOOL_ENEMY_SPAWN:
            # 检查该位置是否有墙体或玩家出生点
            has_wall = any(w['x'] == game_x and w['y'] == game_y for w in self.walls)
            overlaps_player = any(s[0] == game_x and s[1] == game_y for s in self.player_spawns)
            overlaps_enemy = any(s[0] == game_x and s[1] == game_y for s in self.enemy_spawns)
            
            # 如果没有墙体、玩家出生点且不重复，则放置敌人出生点
            if not has_wall and not overlaps_player and not overlaps_enemy:
                self.enemy_spawns.append([game_x, game_y])
        else:
            # 放置墙体
            # 检查是否与玩家出生点或敌人出生点重叠
            overlaps_player = any(s[0] == game_x and s[1] == game_y for s in self.player_spawns)
            overlaps_enemy = any(s[0] == game_x and s[1] == game_y for s in self.enemy_spawns)
            
            # 只有当不重叠时才放置墙体
            if not overlaps_player and not overlaps_enemy:
                # 先移除该位置的墙体（为了避免意外的重复）
                self.walls = [w for w in self.walls if not (w['x'] == game_x and w['y'] == game_y)]
                # 添加新墙体
                self.walls.append({'x': game_x, 'y': game_y, 'type': self.current_tool})
    
    def _remove_item_at(self, game_x, game_y):
        """删除指定位置的物品（墙体或出生点） - 使用游戏坐标系"""
        # 删除墙体
        self.walls = [w for w in self.walls if not (w['x'] == game_x and w['y'] == game_y)]
        
        # 删除玩家出生点
        self.player_spawns = [s for s in self.player_spawns if not (s[0] == game_x and s[1] == game_y)]
        
        # 删除敌人出生点
        self.enemy_spawns = [s for s in self.enemy_spawns if not (s[0] == game_x and s[1] == game_y)]
    
    def _save_map(self):
        """保存地图 - 使用标准化的地图格式，支持任意屏幕比例和分辨率"""
        self.map_name = self.map_name_entry.get_text()
        
        # 确保地图名称有效
        if not self.map_name.strip():
            self.map_name = "new_map"
        
        # 保存地图数据，支持16:9比例和自适应游戏窗口尺寸
        # 1. 保存墙体的网格坐标而非绝对像素坐标
        # 2. 记录原始地图尺寸、网格大小和宽高比用于适配
        grid_size = self.GRID_SIZE
        
        # 将墙体坐标转换为网格坐标
        wall_grid_data = []
        for wall in self.walls:
            grid_x = wall['x'] // grid_size
            grid_y = wall['y'] // grid_size
            wall_grid_data.append({
                "grid_x": grid_x,
                "grid_y": grid_y,
                "type": wall['type']
            })
        
        # 将出生点转换为网格坐标
        player_spawns_grid = []
        for spawn in self.player_spawns:
            grid_x = spawn[0] // grid_size
            grid_y = spawn[1] // grid_size
            player_spawns_grid.append([grid_x, grid_y])
        
        enemy_spawns_grid = []
        for spawn in self.enemy_spawns:
            grid_x = spawn[0] // grid_size
            grid_y = spawn[1] // grid_size
            enemy_spawns_grid.append([grid_x, grid_y])
        
        map_data = {
            "name": self.map_name,
            "original_width": self.MAP_WIDTH,
            "original_height": self.GAME_HEIGHT,
            "aspect_ratio": self.ASPECT_RATIO,  # 保存宽高比
            "grid_size": grid_size,
            "wall_grid_data": wall_grid_data,  # 使用网格坐标
            "player_spawns_grid": player_spawns_grid,
            "enemy_spawns_grid": enemy_spawns_grid,
            "walls": self.walls,  # 保留原始绝对坐标以便向后兼容
            "player_spawns": self.player_spawns,
            "enemy_spawns": self.enemy_spawns
        }
        
        # 确保maps目录存在
        maps_dir = "maps"
        if not os.path.exists(maps_dir):
            os.makedirs(maps_dir)
        
        # 保存文件
        filename = os.path.join(maps_dir, f"{self.map_name}.json")
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(map_data, f, indent=2, ensure_ascii=False)
            print(f"地图已保存: {filename}")
            print(f"地图尺寸: {self.MAP_WIDTH}x{self.GAME_HEIGHT}, 比例: {self.ASPECT_RATIO:.2f}:1")
            print(f"墙体数量: {len(self.walls)}, 玩家出生点: {len(self.player_spawns)}, 敌人出生点: {len(self.enemy_spawns)}")
        except Exception as e:
            print(f"保存地图失败: {e}")
    
    def _load_map(self):
        """加载地图 - 支持16:9比例适配"""
        self.map_name = self.map_name_entry.get_text()
        filename = os.path.join("maps", f"{self.map_name}.json")
        
        if not os.path.exists(filename):
            print(f"地图文件不存在: {filename}")
            return
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                map_data = json.load(f)
            
            # 检查是否有网格数据（新格式）
            if 'wall_grid_data' in map_data:
                # 使用网格坐标数据加载，并根据当前尺寸进行调整
                grid_size = map_data.get('grid_size', self.GRID_SIZE)
                
                # 加载墙体数据
                self.walls = []
                for wall_grid in map_data['wall_grid_data']:
                    # 直接使用游戏网格大小转换为像素坐标
                    game_x = wall_grid['grid_x'] * self.GRID_SIZE
                    game_y = wall_grid['grid_y'] * self.GRID_SIZE
                    
                    self.walls.append({
                        'x': game_x,
                        'y': game_y,
                        'type': wall_grid['type']
                    })
                
                # 加载玩家出生点
                self.player_spawns = []
                for spawn_grid in map_data.get('player_spawns_grid', []):
                    game_x = spawn_grid[0] * self.GRID_SIZE
                    game_y = spawn_grid[1] * self.GRID_SIZE
                    self.player_spawns.append([game_x, game_y])
                
                # 加载敌人出生点
                self.enemy_spawns = []
                for spawn_grid in map_data.get('enemy_spawns_grid', []):
                    game_x = spawn_grid[0] * self.GRID_SIZE
                    game_y = spawn_grid[1] * self.GRID_SIZE
                    self.enemy_spawns.append([game_x, game_y])
            else:
                # 旧格式处理 - 兼容旧地图
                self.walls = map_data.get('walls', [])
                self.player_spawns = map_data.get('player_spawns', [])
                self.enemy_spawns = map_data.get('enemy_spawns', [])
                
                # 确保出生点在地图范围内
                self.player_spawns = [spawn for spawn in self.player_spawns 
                                     if 0 <= spawn[0] < self.MAP_WIDTH and 0 <= spawn[1] < self.GAME_HEIGHT]
                self.enemy_spawns = [spawn for spawn in self.enemy_spawns 
                                    if 0 <= spawn[0] < self.MAP_WIDTH and 0 <= spawn[1] < self.GAME_HEIGHT]
            
            # 确保有默认出生点
            if not self.player_spawns:
                # 根据当前尺寸设置默认玩家出生点
                mid_x = self.MAP_WIDTH // 2
                spawn_y = self.GAME_HEIGHT - self.GRID_SIZE
                self.player_spawns = [[mid_x - self.GRID_SIZE * 2, spawn_y], [mid_x + self.GRID_SIZE * 2, spawn_y]]
            
            if not self.enemy_spawns:
                # 根据当前尺寸设置默认敌人出生点
                spawn_y = self.GRID_SIZE
                self.enemy_spawns = [[self.GRID_SIZE * 2, spawn_y], [self.MAP_WIDTH // 2, spawn_y], [self.MAP_WIDTH - self.GRID_SIZE * 2, spawn_y]]
            
            print(f"地图已加载: {filename}")
            print(f"加载了 {len(self.walls)} 个墙体，{len(self.player_spawns)} 个玩家出生点，{len(self.enemy_spawns)} 个敌人出生点")
        except Exception as e:
            print(f"加载地图失败: {e}")
    
    def _clear_map(self):
        """清空地图"""
        self.walls = []
        self.player_spawns = []
        self.enemy_spawns = []
        
        print("地图已清空")
    
    def handle_window_resized(self, width, height):
        """处理窗口大小改变，保持固定的网格行列数"""
        # 保持固定的网格尺寸和行列数
        # 使用与游戏世界一致的固定尺寸
        self.MAP_WIDTH = self.DEFAULT_MAP_WIDTH
        self.GAME_HEIGHT = self.DEFAULT_GAME_HEIGHT
        self.MAP_HEIGHT = self.GAME_HEIGHT + self.TOOLBAR_HEIGHT
        
        # 保持固定的网格参数
        self.GRID_COLS = self.FIXED_GRID_COLS
        self.GRID_ROWS = self.FIXED_GRID_ROWS
        
        # 调整布局
        self._update_layout()
        
        print(f"地图编辑器已响应窗口大小改变: {width}x{height}")
        print(f"游戏区域: {self.MAP_WIDTH}x{self.GAME_HEIGHT}, 工具栏: {self.TOOLBAR_HEIGHT}")
        print(f"固定网格大小: {self.GRID_COLS}列 x {self.GRID_ROWS}行")
        
    def _update_layout(self):
        """更新布局以适应新的窗口大小"""
        # 重新创建工具栏按钮以适应新的窗口大小
        self._create_toolbar_buttons()
    
    def render(self):
        """渲染编辑器 - 使用与游戏相同的坐标系统，将界面居中显示"""
        self.surface.fill((40, 40, 40))
        
        # 获取窗口尺寸
        window_width, window_height = self.surface.get_size()
        map_width = self.MAP_WIDTH
        map_height = self.GAME_HEIGHT
        toolbar_height = self.TOOLBAR_HEIGHT
        
        # 计算缩放比例，确保地图完整显示在屏幕上
        available_width = window_width
        available_height = window_height - toolbar_height
        
        # 计算水平和垂直缩放比例
        scale_x = available_width / map_width
        scale_y = available_height / map_height
        
        # 使用较小的缩放比例，确保地图完整显示
        scale_factor = min(scale_x, scale_y, 1.0)  # 不超过1.0倍缩放
        
        # 计算缩放后的地图尺寸
        scaled_map_width = int(map_width * scale_factor)
        scaled_map_height = int(map_height * scale_factor)
        scaled_grid_size = int(self.GRID_SIZE * scale_factor)
        
        # 计算居中偏移
        x_offset = (window_width - scaled_map_width) // 2
        y_offset = (window_height - toolbar_height - scaled_map_height) // 2 + toolbar_height
        
        # 绘制网格
        for row in range(self.GRID_ROWS):
            for col in range(self.GRID_COLS):
                x = col * scaled_grid_size + x_offset
                y = row * scaled_grid_size + y_offset
                pygame.draw.rect(self.surface, (60, 60, 60), 
                               (x, y, scaled_grid_size, scaled_grid_size), 1)
        
        # 绘制墙体 - 渲染时将游戏坐标系转换为屏幕坐标系并缩放
        for wall in self.walls:
            # 计算网格坐标
            grid_x = wall['x'] // self.GRID_SIZE
            grid_y = wall['y'] // self.GRID_SIZE
            
            # 转换为屏幕坐标并缩放
            x = grid_x * scaled_grid_size + x_offset
            y = grid_y * scaled_grid_size + y_offset
            wall_type = wall['type']
            
            # 获取墙体图片
            wall_img = resource_manager.get_wall_image(wall_type)
            if wall_img:
                # 缩放墙体图片以适应当前网格大小
                scaled_wall_img = pygame.transform.scale(wall_img, (scaled_grid_size, scaled_grid_size))
                self.surface.blit(scaled_wall_img, (x, y))
            else:
                # 备用：绘制彩色方块
                color = (255, 128, 0)  # 默认砖块颜色
                if wall_type == Wall.STEEL:
                    color = (128, 128, 128)
                elif wall_type == Wall.GRASS:
                    color = (0, 255, 0)
                elif wall_type == Wall.RIVER:
                    color = (0, 0, 255)
                elif wall_type == Wall.BASE:
                    color = (255, 0, 0)
                pygame.draw.rect(self.surface, color, 
                               (x, y, scaled_grid_size, scaled_grid_size))
        
        # 绘制出生点
        for spawn in self.player_spawns:
            # 计算网格坐标
            grid_x = spawn[0] // self.GRID_SIZE
            grid_y = spawn[1] // self.GRID_SIZE
            
            # 转换为屏幕坐标并缩放
            x = grid_x * scaled_grid_size + x_offset
            y = grid_y * scaled_grid_size + y_offset
            
            # 绘制玩家出生点（蓝色圆圈）
            radius = scaled_grid_size // 3
            pygame.draw.circle(self.surface, (0, 0, 255), 
                              (x + scaled_grid_size//2, y + scaled_grid_size//2), 
                              radius)
        
        for spawn in self.enemy_spawns:
            # 计算网格坐标
            grid_x = spawn[0] // self.GRID_SIZE
            grid_y = spawn[1] // self.GRID_SIZE
            
            # 转换为屏幕坐标并缩放
            x = grid_x * scaled_grid_size + x_offset
            y = grid_y * scaled_grid_size + y_offset
            
            # 绘制敌人出生点（红色圆圈）
            radius = scaled_grid_size // 3
            pygame.draw.circle(self.surface, (255, 0, 0), 
                              (x + scaled_grid_size//2, y + scaled_grid_size//2), 
                              radius)
        
        # 不再绘制工具提示和地图信息
        
        # 绘制UI
        self.manager.draw_ui(self.surface)
