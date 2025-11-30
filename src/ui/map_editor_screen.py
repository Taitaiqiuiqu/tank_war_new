"""
地图编辑器界面
"""
import json
import os
import pygame
import pygame_gui
from pygame_gui.elements import UIButton, UILabel, UITextEntryLine
from pygame_gui.windows import UIFileDialog, UIMessageWindow

from src.ui.screen_manager import BaseScreen
from src.utils.resource_manager import resource_manager
from src.game_engine.wall import Wall


class MapEditorScreen(BaseScreen):
    """地图编辑器屏幕"""
    
    GRID_SIZE = 50
    MAP_WIDTH = 800  # 基础地图宽度
    GAME_HEIGHT = 600  # 实际游戏区域高度
    TOOLBAR_HEIGHT = 90  # 工具栏高度
    MAP_HEIGHT = GAME_HEIGHT + TOOLBAR_HEIGHT  # 包含工具栏在内的总高度
    GRID_COLS = MAP_WIDTH // GRID_SIZE  # 16
    GRID_ROWS = GAME_HEIGHT // GRID_SIZE  # 12
    
    # 工具类型（对应wall.py中的常量）
    TOOL_BRICK = 1      # 砖块（可摧毁）
    TOOL_STEEL = 2      # 钢块（不可摧毁）
    TOOL_GRASS = 3      # 草地
    TOOL_RIVER = 4      # 河流
    TOOL_BASE = 5       # 基地（老鹰）
    TOOL_ERASER = 99    # 橡皮擦（特殊工具）
    TOOL_PLAYER_SPAWN = 100  # 玩家出生点
    TOOL_ENEMY_SPAWN = 101   # 敌人出生点
    
    def __init__(self, surface, context, ui_manager, network_manager=None):
        super().__init__(surface, context, ui_manager, network_manager)
        self.current_tool = self.TOOL_BRICK
        self.walls = []  # List of {x, y, type}
        self.player_spawn = [400, 550]
        self.enemy_spawn = [400, 50]
        self.is_dragging = False
        self.map_name = "new_map"
        
        # 工具栏高度 - 现在依赖窗口管理器动态获取
        self.toolbar_height = 90
        
    def on_enter(self):
        super().on_enter()
        
        # 进入编辑器时，通过窗口管理器调整窗口大小
        try:
            window_manager = self.get_window_manager()
            if window_manager:
                # 使用窗口管理器的预设配置进入地图编辑器模式
                window_manager.resize_to_config('map_editor')
            else:
                print("警告: 无法获取窗口管理器")
        except Exception as e:
            print(f"进入编辑器时调整窗口大小时出错: {e}")
        
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
    
    def handle_event(self, event):
        # 移除 super().handle_event(event)，因为 ScreenManager 已经处理了 UI 事件
        # 避免双重处理导致的问题
        
        if event.type == pygame.KEYDOWN:
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
            elif event.key == pygame.K_6:
                self.current_tool = self.TOOL_ERASER
            elif event.key == pygame.K_7:
                self.current_tool = self.TOOL_PLAYER_SPAWN
            elif event.key == pygame.K_8:
                self.current_tool = self.TOOL_ENEMY_SPAWN
        
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            # 使用文本内容进行判断，避免对象ID不一致的问题
            btn_text = getattr(event.ui_element, 'text', '')
            
            if btn_text == '砖墙' or event.ui_element == self.btn_brick:
                self.current_tool = self.TOOL_BRICK
            elif btn_text == '钢墙' or event.ui_element == self.btn_steel:
                self.current_tool = self.TOOL_STEEL
            elif btn_text == '草地' or event.ui_element == self.btn_grass:
                self.current_tool = self.TOOL_GRASS
            elif btn_text == '河流' or event.ui_element == self.btn_river:
                self.current_tool = self.TOOL_RIVER
            elif btn_text == '基地' or event.ui_element == self.btn_base:
                self.current_tool = self.TOOL_BASE
            elif btn_text == '橡皮擦' or event.ui_element == self.btn_eraser:
                self.current_tool = self.TOOL_ERASER
            elif btn_text == '玩家出生点' or event.ui_element == self.btn_player_spawn:
                self.current_tool = self.TOOL_PLAYER_SPAWN
            elif btn_text == '敌人出生点' or event.ui_element == self.btn_enemy_spawn:
                self.current_tool = self.TOOL_ENEMY_SPAWN
            elif btn_text == '保存' or event.ui_element == self.btn_save:
                self._save_map()
            elif btn_text == '加载' or event.ui_element == self.btn_load:
                self._load_map()
            elif btn_text == '清空' or event.ui_element == self.btn_clear:
                self.walls.clear()
            elif btn_text == '返回' or event.ui_element == self.btn_back:
                self.context.next_state = "menu"
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
                self.walls.clear()
            elif event.ui_element == self.btn_back:
                self.context.next_state = "menu"
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                self.is_dragging = True
                self._handle_click(event.pos)
            elif event.button == 3:  # Right click
                self._remove_wall_at(event.pos)
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.is_dragging = False
        
        elif event.type == pygame.MOUSEMOTION:
            if self.is_dragging:
                self._handle_click(event.pos)
    
    def _handle_click(self, pos):
        """处理鼠标点击"""
        x, y = pos
        
        # 检查是否在地图区域内（工具栏占用了前90像素的高度）
        if y < 90:
            return
        
        # 转换为网格坐标，直接使用屏幕坐标计算（窗口已增大，无需偏移）
        grid_x = (x // self.GRID_SIZE) * self.GRID_SIZE
        # 游戏坐标系的y坐标（从90像素开始，对应游戏中的0坐标）
        grid_y = ((y - 90) // self.GRID_SIZE) * self.GRID_SIZE
        
        # 检查边界，确保在有效地图范围内
        if grid_x < 0 or grid_x >= self.MAP_WIDTH or grid_y < 0 or grid_y >= self.MAP_HEIGHT:
            return
        
        if self.current_tool == self.TOOL_ERASER:
            self._remove_wall_at(pos)
        elif self.current_tool == self.TOOL_PLAYER_SPAWN:
            # 检查该位置是否有墙体或老鹰或敌人出生点
            has_wall = any(w['x'] == grid_x and w['y'] == grid_y for w in self.walls)
            overlaps_enemy_spawn = grid_x == self.enemy_spawn[0] and grid_y == self.enemy_spawn[1]
            # 如果没有墙体和敌人出生点，则放置玩家出生点
            if not has_wall and not overlaps_enemy_spawn:
                self.player_spawn = [grid_x, grid_y]
        elif self.current_tool == self.TOOL_ENEMY_SPAWN:
            # 检查该位置是否有墙体或老鹰或玩家出生点
            has_wall = any(w['x'] == grid_x and w['y'] == grid_y for w in self.walls)
            overlaps_player_spawn = grid_x == self.player_spawn[0] and grid_y == self.player_spawn[1]
            # 如果没有墙体和玩家出生点，则放置敌人出生点
            if not has_wall and not overlaps_player_spawn:
                self.enemy_spawn = [grid_x, grid_y]
        else:
            # 放置墙体或老鹰，使用游戏坐标系
            # 检查是否与玩家出生点重叠
            overlaps_player_spawn = grid_x == self.player_spawn[0] and grid_y == self.player_spawn[1]
            # 检查是否与敌人出生点重叠
            overlaps_enemy_spawn = grid_x == self.enemy_spawn[0] and grid_y == self.enemy_spawn[1]
            # 检查该位置是否已有墙体（如果有则不再添加，包括其他墙体和老鹰）
            wall_exists = any(w['x'] == grid_x and w['y'] == grid_y for w in self.walls)
            
            # 只有当不重叠时才放置墙体或老鹰
            if not wall_exists and not overlaps_player_spawn and not overlaps_enemy_spawn:
                # 先移除该位置的墙体（为了避免意外的重复）
                self.walls = [w for w in self.walls if not (w['x'] == grid_x and w['y'] == grid_y)]
                # 添加新墙体或老鹰
                self.walls.append({'x': grid_x, 'y': grid_y, 'type': self.current_tool})
    
    def _remove_wall_at(self, pos):
        """删除指定位置的墙体"""
        x, y = pos
        if y < 90:
            return
        
        grid_x = (x // self.GRID_SIZE) * self.GRID_SIZE
        grid_y = ((y - 90) // self.GRID_SIZE) * self.GRID_SIZE
        
        # 查找并删除对应位置的墙体
        # 注意：这里的grid_y已经是游戏坐标系中的y坐标
        self.walls = [w for w in self.walls if not (w['x'] == grid_x and w['y'] == grid_y)]
    
    def _save_map(self):
        """保存地图"""
        self.map_name = self.map_name_entry.get_text()
        
        # 保存地图数据，确保地图尺寸和游戏中一致
        # 注意：
        # 1. 地图尺寸应保持与游戏窗口一致（800x600）
        # 2. 墙体和出生点的y坐标已经是游戏坐标系中的坐标（不包含工具栏偏移）
        map_data = {
            "name": self.map_name,
            "width": self.MAP_WIDTH,
            "height": self.GAME_HEIGHT,  # 保存游戏区域高度600，不包含工具栏
            "walls": self.walls,        # 墙体坐标已经是正确的游戏坐标系
            "player_spawns": [self.player_spawn],
            "enemy_spawns": [self.enemy_spawn]
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
        except Exception as e:
            print(f"保存地图失败: {e}")
    
    def _load_map(self):
        """加载地图"""
        map_name = self.map_name_entry.get_text()
        filename = os.path.join("maps", f"{map_name}.json")
        
        if not os.path.exists(filename):
            print(f"地图文件不存在: {filename}")
            return
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                map_data = json.load(f)
            
            self.walls = map_data.get('walls', [])
            player_spawns = map_data.get('player_spawns', [[400, 550]])
            enemy_spawns = map_data.get('enemy_spawns', [[400, 50]])
            
            self.player_spawn = player_spawns[0] if player_spawns else [400, 550]
            self.enemy_spawn = enemy_spawns[0] if enemy_spawns else [400, 50]
            
            print(f"地图已加载: {filename}")
        except Exception as e:
            print(f"加载地图失败: {e}")
    
    def handle_window_resized(self, width, height):
        """处理窗口大小改变"""
        # 地图编辑器应保持固定的游戏区域高度
        current_game_height = self.GAME_HEIGHT
        current_toolbar_height = self.TOOLBAR_HEIGHT
        current_total_height = current_game_height + current_toolbar_height
        
        # 如果窗口高度不够，尝试调整工具栏高度
        if height < current_total_height:
            # 计算最小需要的工具栏高度
            min_toolbar_height = 60  # 最小工具栏高度
            available_game_height = height - min_toolbar_height
            
            if available_game_height > 400:  # 确保有足够的游戏区域
                self.TOOLBAR_HEIGHT = min_toolbar_height
                self.GAME_HEIGHT = available_game_height
            else:
                # 如果高度太小，保持原始设置但缩放显示
                self.GAME_HEIGHT = max(400, height * 0.7)
                self.TOOLBAR_HEIGHT = max(60, height * 0.1)
        else:
            # 高度充足，保持原始设置
            self.TOOLBAR_HEIGHT = 90
            self.GAME_HEIGHT = 600
        
        # 重新计算网格参数
        self.GRID_COLS = self.MAP_WIDTH // self.GRID_SIZE
        self.GRID_ROWS = self.GAME_HEIGHT // self.GRID_SIZE
        
        # 调整布局
        self._update_layout()
        
        print(f"地图编辑器已响应窗口大小改变: {width}x{height}")
        print(f"游戏区域: {self.MAP_WIDTH}x{self.GAME_HEIGHT}, 工具栏: {self.TOOLBAR_HEIGHT}")
        print(f"网格大小: {self.GRID_COLS}列 x {self.GRID_ROWS}行")
        
    def _update_layout(self):
        """更新布局以适应新的窗口大小"""
        # 重新计算工具栏位置
        surface_height = getattr(self, 'surface_height', 600)
        surface_width = getattr(self, 'surface_width', 800)
        
        # 确保工具栏在底部
        self.toolbar_y = surface_height - self.TOOLBAR_HEIGHT
        self.toolbar_height = self.TOOLBAR_HEIGHT
        
        # 重新创建工具栏按钮以适应新的窗口大小
        self._create_toolbar_buttons()

    def render(self):
        """渲染编辑器"""
        self.surface.fill((40, 40, 40))
        
        # 移除 self.manager.update(0.016) - 由 ScreenManager 统一调用
        
        # 绘制地图画布（从y=90开始）
        canvas_y_offset = 90
        
        # 绘制网格 - 现在可以显示完整的600像素高度游戏区域
        for row in range(self.GRID_ROWS):
            for col in range(self.GRID_COLS):
                x = col * self.GRID_SIZE
                y = row * self.GRID_SIZE + canvas_y_offset
                pygame.draw.rect(self.surface, (60, 60, 60), 
                               (x, y, self.GRID_SIZE, self.GRID_SIZE), 1)
        
        # 绘制墙体 - 渲染时将游戏坐标系转换为屏幕坐标系
        for wall in self.walls:
            # 游戏坐标系转换为屏幕坐标系，加上工具栏偏移
            x = wall['x']
            y = wall['y'] + canvas_y_offset
            wall_type = wall['type']
            
            # 获取墙体图片
            wall_img = resource_manager.get_wall_image(wall_type)
            if wall_img:
                self.surface.blit(wall_img, (x, y))
            else:
                # 备用颜色
                colors = {
                    1: (139, 69, 19),   # 砖墙 - 棕色
                    2: (128, 128, 128), # 钢墙 - 灰色
                    3: (34, 139, 34),   # 草地 - 绿色
                    4: (0, 191, 255),   # 河流 - 蓝色
                    5: (255, 215, 0)    # 基地 - 金色
                }
                color = colors.get(wall_type, (255, 255, 255))
                pygame.draw.rect(self.surface, color, (x, y, self.GRID_SIZE, self.GRID_SIZE))
        
        # 绘制出生点 - 渲染时将游戏坐标系转换为屏幕坐标系
        # 玩家出生点 - 蓝色圆圈
        player_x = self.player_spawn[0] + self.GRID_SIZE // 2
        player_y = self.player_spawn[1] + self.GRID_SIZE // 2 + canvas_y_offset
        pygame.draw.circle(self.surface, (0, 0, 255), (player_x, player_y), 15, 3)
        
        # 敌人出生点 - 红色圆圈
        enemy_x = self.enemy_spawn[0] + self.GRID_SIZE // 2
        enemy_y = self.enemy_spawn[1] + self.GRID_SIZE // 2 + canvas_y_offset
        pygame.draw.circle(self.surface, (255, 0, 0), (enemy_x, enemy_y), 15, 3)
        
        # 绘制当前工具提示
        tool_names = {
            self.TOOL_BRICK: "砖墙 (1)",
            self.TOOL_STEEL: "钢墙 (2)",
            self.TOOL_GRASS: "草地 (3)",
            self.TOOL_RIVER: "河流 (4)",
            self.TOOL_BASE: "基地 (5)",
            self.TOOL_ERASER: "橡皮擦 (6)",
            self.TOOL_PLAYER_SPAWN: "玩家出生点 (7)",
            self.TOOL_ENEMY_SPAWN: "敌人出生点 (8)"
        }
        tool_text = f"当前工具: {tool_names.get(self.current_tool, '未知')}"
        text_surf = self.small_font.render(tool_text, True, (255, 255, 255))
        self.surface.blit(text_surf, (10, self.surface.get_height() - 30))
        
        # 绘制窗口信息提示
        info_text = f"地图编辑器窗口大小: {self.surface.get_width()}x{self.surface.get_height()} - 可编辑完整游戏区域"
        info_surf = self.small_font.render(info_text, True, (180, 180, 180))
        self.surface.blit(info_surf, (10, self.surface.get_height() - 60))
        
        # 移除 self.manager.draw_ui(self.surface) - 由 ScreenManager 统一调用
