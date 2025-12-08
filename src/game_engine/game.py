import random
from typing import List, Optional
import ctypes

import pygame

from src.game_engine.game_world import GameWorld
from src.game_engine.tank import Tank
from src.game_engine.wall import Wall
from src.network.network_manager import NetworkManager
from src.state_sync.state_manager import StateManager
from src.ui.screen_manager import ScreenManager
from src.ui.pause_menu import PauseMenuOverlay
from src.utils.resource_manager import resource_manager
from src.utils.map_loader import map_loader
from src.game_engine.window_manager import WindowManager
from src.config.game_config import config


class EnemyAIController:
    """增强型敌人AI：支持4个难度等级"""

    def __init__(self, tank_id: int, world: GameWorld, difficulty: str = "normal"):
        from src.game_engine.ai_config import get_difficulty_config
        
        self.tank_id = tank_id
        self.world = world
        self.difficulty = difficulty
        self.config = get_difficulty_config(difficulty)
        
        self.direction_timer = 0
        self.shoot_timer = 0
        self.role = None  # For Hell difficulty team coordination

    def update(self):
        # 动态查找坦克实例 - 只控制敌人坦克
        tank = next((t for t in self.world.tanks if t.tank_id == self.tank_id and t.active and t.tank_type == "enemy"), None)
        if not tank:
            return

        # Apply speed from config
        tank.speed = self.config["speed"]

        # Update timers
        self.direction_timer -= 1
        self.shoot_timer -= 1
        
        # Movement logic based on difficulty
        if self.direction_timer <= 0:
            self._update_movement(tank)
            min_interval, max_interval = self.config["direction_interval"]
            self.direction_timer = random.randint(min_interval, max_interval)
        
        # Shooting logic
        if self.shoot_timer <= 0:
            self._update_shooting(tank)
            min_interval, max_interval = self.config["shoot_interval"]
            self.shoot_timer = random.randint(min_interval, max_interval)
    
    def _update_movement(self, tank):
        """更新移动逻辑"""
        if self.config["tracking"]:
            self._move_with_tracking(tank)
        else:
            self._move_random(tank)
    
    def _move_random(self, tank):
        """随机移动（简单难度）"""
        tank.move(random.choice([Tank.UP, Tank.RIGHT, Tank.DOWN, Tank.LEFT]))
    
    def _move_with_tracking(self, tank):
        """带追踪的移动（普通+难度）"""
        # Find nearest player
        player = self._find_nearest_player(tank)
        if not player:
            self._move_random(tank)
            return
        
        # Calculate distance
        dx = player.x - tank.x
        dy = player.y - tank.y
        distance = (dx**2 + dy**2)**0.5
        
        # Check if should track based on probability
        tracking_prob = self.config.get("tracking_prob", 0.7)
        if random.random() > tracking_prob:
            self._move_random(tank)
            return
        
        # Safe distance logic (Hard+)
        safe_distance = self.config.get("safe_distance", 0)
        if safe_distance > 0 and distance < safe_distance:
            # Move away from player
            if abs(dx) > abs(dy):
                tank.move(Tank.LEFT if dx > 0 else Tank.RIGHT)
            else:
                tank.move(Tank.UP if dy > 0 else Tank.DOWN)
            return
        
        # Dodge bullets (Normal+)
        if self.config.get("dodge") and self._should_dodge(tank):
            self._dodge_bullet(tank)
            return
        
        # Move towards player
        if abs(dx) > abs(dy):
            tank.move(Tank.RIGHT if dx > 0 else Tank.LEFT)
        else:
            tank.move(Tank.DOWN if dy > 0 else Tank.UP)
    
    def _update_shooting(self, tank):
        """更新射击逻辑"""
        if self.config.get("prediction"):
            self._shoot_with_prediction(tank)
        else:
            self.world.spawn_bullet(tank)
    
    def _shoot_with_prediction(self, tank):
        """带预判的射击"""
        player = self._find_nearest_player(tank)
        if not player:
            self.world.spawn_bullet(tank)
            return
        
        # Calculate predicted position
        prediction_frames = self.config.get("prediction_frames", 10)
        pred_x = player.x + player.velocity_x * prediction_frames
        pred_y = player.y + player.velocity_y * prediction_frames
        
        # Determine best shooting direction
        dx = pred_x - tank.x
        dy = pred_y - tank.y
        
        # Choose direction closest to predicted position
        if abs(dx) > abs(dy):
            target_dir = Tank.RIGHT if dx > 0 else Tank.LEFT
        else:
            target_dir = Tank.DOWN if dy > 0 else Tank.UP
        
        # Aim and shoot
        tank.direction = target_dir
        self.world.spawn_bullet(tank)
    
    def _find_nearest_player(self, tank):
        """查找最近的玩家"""
        players = [t for t in self.world.tanks if t.active and t.tank_type == "player"]
        if not players:
            return None
        
        min_dist = float('inf')
        nearest = None
        for player in players:
            dist = (player.x - tank.x)**2 + (player.y - tank.y)**2
            if dist < min_dist:
                min_dist = dist
                nearest = player
        return nearest
    
    def _should_dodge(self, tank):
        """检查是否应该躲避子弹"""
        dodge_prob = self.config.get("dodge_prob", 0.3)
        if random.random() > dodge_prob:
            return False
        
        # Check for incoming bullets
        for bullet in self.world.bullets:
            if not bullet.active or bullet.owner == tank:
                continue
            
            # Simple collision prediction
            if self._bullet_will_hit(bullet, tank):
                return True
        return False
    
    def _bullet_will_hit(self, bullet, tank):
        """预测子弹是否会击中坦克"""
        # Simple check: is bullet moving towards tank?
        dx = tank.x - bullet.x
        dy = tank.y - bullet.y
        
        # Check if bullet is close and moving towards tank
        if bullet.direction == Tank.UP and dy < 0 and abs(dx) < 30 and abs(dy) < 200:
            return True
        if bullet.direction == Tank.DOWN and dy > 0 and abs(dx) < 30 and abs(dy) < 200:
            return True
        if bullet.direction == Tank.LEFT and dx < 0 and abs(dy) < 30 and abs(dx) < 200:
            return True
        if bullet.direction == Tank.RIGHT and dx > 0 and abs(dy) < 30 and abs(dx) < 200:
            return True
        return False
    
    def _dodge_bullet(self, tank):
        """躲避子弹"""
        # Find dangerous bullet
        for bullet in self.world.bullets:
            if not bullet.active or bullet.owner == tank:
                continue
            if self._bullet_will_hit(bullet, tank):
                # Move perpendicular to bullet direction
                if bullet.direction in [Tank.UP, Tank.DOWN]:
                    tank.move(random.choice([Tank.LEFT, Tank.RIGHT]))
                else:
                    tank.move(random.choice([Tank.UP, Tank.DOWN]))
                return
        
        # Fallback to random
        self._move_random(tank)



class GameEngine:
    """游戏引擎核心类，负责协调各个模块的工作"""

    def __init__(self, enable_network: bool = False):
        """初始化游戏引擎"""
        # Enable DPI Awareness on Windows to prevent auto-scaling
        # This fixes the issue where 2560x1440 window becomes larger than screen on scaled displays
        try:
            # Try to set ProcessDpiAwareness (Windows 8.1+)
            # 0 = Unaware, 1 = System DPI Aware, 2 = Per Monitor DPI Aware
            # We use System DPI Aware (1) to ensure the window size matches physical pixels
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
            print("DPI Awareness set to System DPI Aware (1)")
        except Exception:
            try:
                # Fallback for Windows Vista/7/8
                ctypes.windll.user32.SetProcessDPIAware()
                print("DPI Awareness set via SetProcessDPIAware")
            except Exception as e:
                print(f"Failed to set DPI awareness: {e}")

        # 获取显示器信息，设置合适的窗口大小
        # 首先尝试使用pygame获取分辨率
        info = pygame.display.Info()
        pygame_width, pygame_height = info.current_w, info.current_h
        
        # 然后使用ctypes获取Windows显示器的实际物理分辨率（不受显示缩放影响）
        try:
            # 定义DEVMODE结构用于存储显示设置信息
            class DEVMODE(ctypes.Structure):
                _fields_ = [
                    ('dmDeviceName', ctypes.c_wchar * 32),
                    ('dmSpecVersion', ctypes.c_short),
                    ('dmDriverVersion', ctypes.c_short),
                    ('dmSize', ctypes.c_short),
                    ('dmDriverExtra', ctypes.c_short),
                    ('dmFields', ctypes.c_uint),
                    ('dmOrientation', ctypes.c_short),
                    ('dmPaperSize', ctypes.c_short),
                    ('dmPaperLength', ctypes.c_short),
                    ('dmPaperWidth', ctypes.c_short),
                    ('dmScale', ctypes.c_short),
                    ('dmCopies', ctypes.c_short),
                    ('dmDefaultSource', ctypes.c_short),
                    ('dmPrintQuality', ctypes.c_short),
                    ('dmColor', ctypes.c_short),
                    ('dmDuplex', ctypes.c_short),
                    ('dmYResolution', ctypes.c_short),
                    ('dmTTOption', ctypes.c_short),
                    ('dmCollate', ctypes.c_short),
                    ('dmFormName', ctypes.c_wchar * 32),
                    ('dmLogPixels', ctypes.c_short),
                    ('dmBitsPerPel', ctypes.c_short),
                    ('dmPelsWidth', ctypes.c_uint),
                    ('dmPelsHeight', ctypes.c_uint),
                    ('dmDisplayFlags', ctypes.c_uint),
                    ('dmDisplayFrequency', ctypes.c_uint),
                    ('dmICMMethod', ctypes.c_uint),
                    ('dmICMIntent', ctypes.c_uint),
                    ('dmMediaType', ctypes.c_uint),
                    ('dmDitherType', ctypes.c_uint),
                    ('dmReserved1', ctypes.c_uint),
                    ('dmReserved2', ctypes.c_uint),
                    ('dmPanningWidth', ctypes.c_uint),
                    ('dmPanningHeight', ctypes.c_uint),
                ]
            
            user32 = ctypes.windll.user32
            devmode = DEVMODE()
            devmode.dmSize = ctypes.sizeof(DEVMODE)
            
            # 获取主显示器的默认显示设置
            if user32.EnumDisplaySettingsW(None, -1, ctypes.byref(devmode)):
                physical_width = devmode.dmPelsWidth
                physical_height = devmode.dmPelsHeight
                print(f"EnumDisplaySettings获取的实际物理分辨率: {physical_width}x{physical_height}")
                
                # 使用物理分辨率而不是pygame检测的缩放后分辨率
                screen_width, screen_height = physical_width, physical_height
                print(f"当前显示器分辨率: {screen_width}x{screen_height}")
            else:
                # 如果EnumDisplaySettings调用失败，尝试另一种方法
                user32 = ctypes.windll.user32
                # 获取屏幕的物理宽度和高度（像素）
                physical_width = user32.GetSystemMetrics(0)  # SM_CXSCREEN
                physical_height = user32.GetSystemMetrics(1)  # SM_CYSCREEN
                print(f"GetSystemMetrics获取的分辨率: {physical_width}x{physical_height}")
                
                # 使用这个分辨率
                screen_width, screen_height = physical_width, physical_height
                print(f"当前显示器分辨率: {screen_width}x{screen_height}")
        except Exception as e:
            # 如果ctypes调用失败，回退到pygame获取的分辨率
            screen_width, screen_height = pygame_width, pygame_height
            print(f"使用pygame获取的分辨率: {screen_width}x{screen_height}")
        
        # 确保窗口大小不会超过显示器分辨率
        # 同时保证窗口有合理的最小尺寸
        min_width, min_height = config.MIN_WINDOW_WIDTH, config.MIN_WINDOW_HEIGHT
        
        # 如果显示器分辨率足够大，使用接近显示器分辨率的窗口大小
        # 否则使用显示器分辨率作为窗口大小
        if screen_width >= config.DEFAULT_WINDOW_WIDTH and screen_height >= config.DEFAULT_WINDOW_HEIGHT:
            # 在高分辨率显示器上使用默认窗口大小
            window_width, window_height = config.DEFAULT_WINDOW_WIDTH, config.DEFAULT_WINDOW_HEIGHT
            print(f"使用默认窗口大小: {window_width}x{window_height}")
        else:
            # 在低分辨率显示器上使用显示器分辨率
            window_width, window_height = screen_width, screen_height
            print(f"使用显示器分辨率作为窗口大小: {window_width}x{window_height}")
        
        # 确保窗口大小不小于最小值
        window_width = max(window_width, min_width)
        window_height = max(window_height, min_height)
        
        # 设置游戏窗口 - 添加RESIZABLE标志
        self.screen = pygame.display.set_mode((window_width, window_height), pygame.RESIZABLE)
        self.window_manager = WindowManager(self.screen)
        self.screen_width, self.screen_height = self.window_manager.get_size()
        pygame.display.set_caption("坦克大战 - 单机试玩")
        
        # 注册窗口大小改变回调
        self.window_manager.register_resize_callback(self._on_window_resized)
        
        # 存储原始窗口尺寸
        self.original_width = self.screen_width
        self.original_height = self.screen_height
        
        # 核心模块
        self.network_manager = NetworkManager()
        self.screen_manager = ScreenManager(self.screen, self.network_manager)
        # 将GameEngine实例传递给ScreenManager
        self.screen_manager.game_engine = self
        self.state_manager = StateManager()
        # 创建游戏世界，以1920*1080为基准，固定行列数（28列*21行）
        # 1920*1080的4:3比例对应1440*1080，向下取整为50倍数后为1400*1050
        grid_size = 50
        game_world_width = 28 * grid_size  # 28列
        game_world_height = 21 * grid_size  # 21行
        self.game_world = GameWorld(game_world_width, game_world_height)
        self.state_manager.attach_world(self.game_world)
        
        # 宽高比适配相关
        self.game_world_aspect_ratio = 4/3  # 游戏世界保持4:3比例
        self.render_surface = None  # 中间渲染表面
        self.update_render_surface()  # 初始化中间渲染表面

        # 游戏状态
        self.is_running = True
        self.current_state = "menu"  # menu, lobby, game, settings
        self.enable_network = enable_network
        self.player_tank: Optional[Tank] = None
        self.enemy_controllers: List[EnemyAIController] = []
        self._movement_stack: List[int] = []
        
        # 全屏状态跟踪
        self.is_fullscreen = False
        
        # AI难度锁定（游戏开始时设置，之后不变）
        self.game_difficulty: Optional[str] = None
        
        # 敌人ID计数器 (预留1-4给玩家，敌人从10开始)
        self.next_enemy_id = 10
        
        # 本地玩家ID (用于重生后重新获取控制权)
        self.local_player_id: Optional[int] = None
        
        # 暂停菜单
        self.paused: bool = False
        self.pause_menu: Optional[PauseMenuOverlay] = None
        
        # 播放游戏开始音效
        resource_manager.play_sound("start")
        
        # 关卡系统
        self.current_level = 1
        self.max_level = 10  # 默认10关
        self.game_won = False

    def resize_window(self, width, height):
        """调整窗口大小
        
        Args:
            width: 新的窗口宽度
            height: 新的窗口高度
        """
        self.window_manager.set_window_size(width, height)
        self.screen_width = width
        self.screen_height = height
        self.screen = self.window_manager.game_surface
        # 游戏世界保持固定尺寸（28列*21行）
        grid_size = 50
        game_world_width = 28 * grid_size  # 28列
        game_world_height = 21 * grid_size  # 21行
        self.game_world = GameWorld(game_world_width, game_world_height)
        self.state_manager.attach_world(self.game_world)
        # 重新初始化屏幕管理器以适应新的尺寸
        self.screen_manager = ScreenManager(self.screen, self.network_manager)
        # 将GameEngine实例传递给ScreenManager
        self.screen_manager.game_engine = self
        
    def restore_window(self):
        """恢复窗口到原始尺寸"""
        self.resize_window(self.original_width, self.original_height)
        
    def _on_window_resized(self, width, height):
        """
        窗口大小改变时的回调函数
        
        Args:
            width: 新的窗口宽度
            height: 新的窗口高度
        """
        # 添加窗口大小限制
        MIN_WIDTH = config.MIN_WINDOW_WIDTH
        MIN_HEIGHT = config.MIN_WINDOW_HEIGHT
        
        if width < MIN_WIDTH or height < MIN_HEIGHT:
            print(f"窗口大小不能小于 {MIN_WIDTH}x{MIN_HEIGHT}，忽略调整")
            return
        
        # 更新窗口相关属性
        self.screen_width = width
        self.screen_height = height
        self.screen = self.window_manager.game_surface
        
        # 更新中间渲染表面
        self.update_render_surface()
        
        # 通知ScreenManager窗口大小已改变
        if self.screen_manager:
            self.screen_manager.notify_window_resized(width, height)
            
        print(f"游戏引擎已响应窗口大小改变: {width}x{height} (游戏状态已保留)")
        
    def _setup_single_player_world(self, player_tank_id=1, map_name="default"):
        """初始化单机模式对象。"""
        self._movement_stack.clear()
        self.enemy_controllers.clear()  # 清除旧的控制器
        grid_size = config.GRID_SIZE
        
        # 重置游戏世界，清除旧的游戏对象
        self.game_world.reset()
        
        # 播放游戏开始音效
        from src.utils.resource_manager import resource_manager
        resource_manager.play_sound("start")
        
        # 锁定游戏难度（从context读取，游戏过程中不再改变）
        self.game_difficulty = getattr(self.screen_manager.context, 'enemy_difficulty', 'normal')
        print(f"[Game] 单人模式难度已锁定: {self.game_difficulty}")
        
        # Try to load custom map or generate level map
        map_data = None
        if map_name != "default":
            map_data = map_loader.load_map(map_name, config.GRID_SIZE)
            if map_data:
                print(f"加载自定义地图: {map_data.get('name', map_name)}")
        else:
            # 使用关卡地图生成器
            from src.utils.level_map_generator import generate_level_map
            map_data = generate_level_map(self.current_level, 
                                        self.game_world.width, 
                                        self.game_world.height)
            print(f"生成关卡地图: {map_data.get('name', '关卡地图')}")
        
        if map_data:
            # Load from map file or generated map
            # Calculate map offset to center the map in the game world
            map_width = map_data.get('width', 800)
            map_height = map_data.get('height', 600)
            
            # Calculate offset to center map in game world
            offset_x = (self.game_world.width - map_width) // 2
            offset_y = (self.game_world.height - map_height) // 2
            
            # Spawn points - Single player mode only uses first player spawn
            player_spawns = map_data.get('player_spawns', [[400, 550]])
            enemy_spawns = map_data.get('enemy_spawns', [[400, 50]])
            
            # Single player: only use first player spawn point
            player_spawn = tuple(player_spawns[0]) if player_spawns else (400, 550)
            enemy_spawn = tuple(enemy_spawns[0]) if enemy_spawns else (400, 50)
            
            # Apply offset to spawn points
            player_spawn = (player_spawn[0] + offset_x, player_spawn[1] + offset_y)
            enemy_spawn = (enemy_spawn[0] + offset_x, enemy_spawn[1] + offset_y)
            
            self.game_world.register_spawn_points("player", [player_spawn])
            self.game_world.register_spawn_points("enemy", [enemy_spawn])
            
            self.local_player_id = player_tank_id
            self.player_tank = self.game_world.spawn_tank("player", tank_id=player_tank_id, position=player_spawn, skin_id=player_tank_id)
            
            # 生成敌人 (使用动态ID)
            enemy_id = self.next_enemy_id
            self.next_enemy_id += 1
            self.game_world.spawn_tank("enemy", tank_id=enemy_id, position=enemy_spawn)
            self.enemy_controllers.append(EnemyAIController(enemy_id, self.game_world, difficulty=self.game_difficulty))
            
            # Load walls with offset
            walls = map_data.get('walls', [])
            for wall in walls:
                x = wall.get('x', 0) + offset_x
                y = wall.get('y', 0) + offset_y
                wall_type = wall.get('type', 0)
                self.game_world.spawn_wall(x, y, wall_type)
        else:
            # Use default map
            # 调整坦克出生点（适应30x30坦克）
            player_spawn = (self.screen_width // 2 - 15, self.screen_height - 100)
            enemy_spawn = (self.screen_width // 2 - 15, 50)

            self.game_world.register_spawn_points("player", [player_spawn])
            self.game_world.register_spawn_points("enemy", [enemy_spawn])

            self.local_player_id = player_tank_id
            self.player_tank = self.game_world.spawn_tank("player", tank_id=player_tank_id, position=player_spawn)
            
            # 生成敌人 (使用动态ID)
            enemy_id = self.next_enemy_id
            self.next_enemy_id += 1
            self.game_world.spawn_tank("enemy", tank_id=enemy_id, position=enemy_spawn)
            self.enemy_controllers.append(EnemyAIController(enemy_id, self.game_world, difficulty=self.game_difficulty))

            # 使用50x50网格创建地图布局
            # 中间一排砖墙（第6行，y=300）
            for col in range(4, 12):  # 列4-11
                x = col * grid_size
                y = 6 * grid_size
                self.game_world.spawn_wall(x, y, Wall.BRICK)
            
            # 左侧钢墙（列1）
            for row in range(2, 10):  # 衁2-9
                x = 1 * grid_size
                y = row * grid_size
                self.game_world.spawn_wall(x, y, Wall.STEEL)
            
            # 右侧钢墙（列14）
            for row in range(2, 10):  # 衁2-9
                x = 14 * grid_size
                y = row * grid_size
                self.game_world.spawn_wall(x, y, Wall.STEEL)
            
            # 添加一些草地（列7-8，衁4-5）
            for col in range(7, 9):
                for row in range(4, 6):
                    x = col * grid_size
                    y = row * grid_size
                    self.game_world.spawn_wall(x, y, Wall.GRASS)
            
            # 添加河流（列10，行3-8）
            for row in range(3, 9):
                x = 10 * grid_size
                y = row * grid_size
                self.game_world.spawn_wall(x, y, Wall.RIVER)
            
            # 添加基地（老鹰）在底部中央
            base_x = (self.screen_width // 2) - 25  # 居中
            base_y = self.screen_height - 100  # 底部
            self.game_world.spawn_wall(base_x, base_y, Wall.BASE)

    def setup_multiplayer_world(self, p1_tank_id, p2_tank_id, map_name="default"):
        """初始化联机模式对象"""
        self.game_world.reset()
        self._movement_stack.clear()
        self.enemy_controllers.clear()  # 清除旧的控制器
        grid_size = config.GRID_SIZE
        
        # 播放游戏开始音效
        from src.utils.resource_manager import resource_manager
        resource_manager.play_sound("start")
        
        # 锁定游戏难度（从context读取，游戏过程中不再改变）
        self.game_difficulty = getattr(self.screen_manager.context, 'enemy_difficulty', 'normal')
        print(f"[Game] 联机模式难度已锁定: {self.game_difficulty}")
        
        # Load Map
        map_data = None
        
        # Priority 1: Use received map data from host (for client)
        if hasattr(self.screen_manager.context, 'received_map_data') and self.screen_manager.context.received_map_data:
            map_data = self.screen_manager.context.received_map_data
            print(f"使用接收的地图数据: {map_data.get('name', map_name)}")
        # Priority 2: Load from local file
        elif map_name != "default":
            map_data = map_loader.load_map(map_name, config.GRID_SIZE)
            if map_data:
                print(f"加载联机地图: {map_data.get('name', map_name)}")
        
        # Default Spawns
        p1_spawn = (self.screen_width // 2 - 100, self.screen_height - 100)
        p2_spawn = (self.screen_width // 2 + 100, self.screen_height - 100)
        enemy_spawn = (self.screen_width // 2 - 15, 50)
        
        # Calculate map offset to center the map in the game world
        offset_x = 0
        offset_y = 0
        
        if map_data:
            # Calculate map dimensions from map data
            map_width = map_data.get('width', 800)
            map_height = map_data.get('height', 600)
            
            # Calculate offset to center map in game world
            offset_x = (self.game_world.width - map_width) // 2
            offset_y = (self.game_world.height - map_height) // 2
            
            # Use map spawns if available
            # Multiplayer mode: use both player spawn points (P1 and P2)
            player_spawns = map_data.get('player_spawns', [])
            if len(player_spawns) >= 2:
                p1_spawn = tuple(player_spawns[0])
                p2_spawn = tuple(player_spawns[1])
            elif len(player_spawns) == 1:
                # Fallback: if only one spawn, offset P2 from P1
                p1_spawn = tuple(player_spawns[0])
                p2_spawn = (p1_spawn[0] + 100, p1_spawn[1])
            
            enemy_spawns = map_data.get('enemy_spawns', [])
            if enemy_spawns:
                enemy_spawn = tuple(enemy_spawns[0])
            
            # Apply offset to spawn points
            p1_spawn = (p1_spawn[0] + offset_x, p1_spawn[1] + offset_y)
            p2_spawn = (p2_spawn[0] + offset_x, p2_spawn[1] + offset_y)
            enemy_spawn = (enemy_spawn[0] + offset_x, enemy_spawn[1] + offset_y)
                
        # Determine which tank is local player
        is_host = self.network_manager.stats.role == "host"
        
        # Spawn P1 (Host) - Logic ID 1
        p1 = self.game_world.spawn_tank("player", tank_id=1, position=p1_spawn, skin_id=p1_tank_id)
        
        # P2 Spawn (Client) - Logic ID 2
        p2 = self.game_world.spawn_tank("player", tank_id=2, position=p2_spawn, skin_id=p2_tank_id)
        
        if is_host:
            self.player_tank = p1
            self.local_player_id = 1
        else:
            self.player_tank = p2
            self.local_player_id = 2
        
        # Enemy Spawn
        enemy_id = self.next_enemy_id
        self.next_enemy_id += 1
        self.game_world.spawn_tank("enemy", tank_id=enemy_id, position=enemy_spawn)
        self.enemy_controllers.append(EnemyAIController(enemy_id, self.game_world, difficulty=self.game_difficulty))
        
        # Map Walls
        if map_data:
            walls = map_data.get('walls', [])
            for wall in walls:
                x = wall.get('x', 0) + offset_x
                y = wall.get('y', 0) + offset_y
                wall_type = wall.get('type', 0)
                self.game_world.spawn_wall(x, y, wall_type)
        else:
            # Default Map
            # 中间一排砖墙（第6行，y=300）
            for col in range(4, 12):  # 列4-11
                x = col * grid_size
                y = 6 * grid_size
                self.game_world.spawn_wall(x, y, Wall.BRICK)
            
            # 左侧钢墙（列1）
            for row in range(2, 10):  # 衁2-9
                x = 1 * grid_size
                y = row * grid_size
                self.game_world.spawn_wall(x, y, Wall.STEEL)
            
            # 右侧钢墙（列14）
            for row in range(2, 10):  # 衁2-9
                x = 14 * grid_size
                y = row * grid_size
                self.game_world.spawn_wall(x, y, Wall.STEEL)
            
            # 添加一些草地（列7-8，衁4-5）
            for col in range(7, 9):
                for row in range(4, 6):
                    x = col * grid_size
                    y = row * grid_size
                    self.game_world.spawn_wall(x, y, Wall.GRASS)
            
            # 添加河流（列10，行3-8）
            for row in range(3, 9):
                x = 10 * grid_size
                y = row * grid_size
                self.game_world.spawn_wall(x, y, Wall.RIVER)
            
            # 添加基地（老鹰）在底部中央
            base_x = (self.screen_width // 2) - 25  # 居中
            base_y = self.screen_height - 100  # 底部
            self.game_world.spawn_wall(base_x, base_y, Wall.BASE)

    def handle_event(self, event):
        """处理游戏事件"""
        self.screen_manager.handle_event(event)
        
        # 处理窗口大小变化事件
        if event.type == pygame.VIDEORESIZE:
            width, height = event.size
            # 限制最小窗口尺寸
            width = max(width, config.MIN_WINDOW_WIDTH)
            height = max(height, config.MIN_WINDOW_HEIGHT)
            self.resize_window(width, height)
            return

        if self.current_state != "game":
            return

        # ESC键暂停/恢复
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._toggle_pause()
            return
        
        # 如果暂停中，让暂停菜单处理事件
        if self.paused and self.pause_menu:
            action = self.pause_menu.handle_event(event)
            if action == 'continue':
                self._toggle_pause()
            elif action == 'restart':
                self._restart_game()
            elif action == 'exit':
                self._exit_to_menu()
            return  # 暂停时不处理游戏事件

        if event.type == pygame.KEYDOWN:
            # 调试功能：Ctrl+数字键生成道具
            if pygame.key.get_mods() & pygame.KMOD_CTRL:
                if event.key >= pygame.K_1 and event.key <= pygame.K_8:
                    prop_id = event.key - pygame.K_1 + 1  # K_1=49, 转换为1-8
                    self._spawn_cheat_prop(prop_id)
                    return
            
            if event.key in (pygame.K_w, pygame.K_UP):
                self._push_direction(Tank.UP)
            elif event.key in (pygame.K_d, pygame.K_RIGHT):
                self._push_direction(Tank.RIGHT)
            elif event.key in (pygame.K_s, pygame.K_DOWN):
                self._push_direction(Tank.DOWN)
            elif event.key in (pygame.K_a, pygame.K_LEFT):
                self._push_direction(Tank.LEFT)
            elif event.key == pygame.K_SPACE:
                self._player_shoot()
            elif event.key == pygame.K_F1:
                self.game_world.enable_debug_overlay(not self.game_world.debug_overlay)

        elif event.type == pygame.KEYUP:
            if event.key in (pygame.K_w, pygame.K_UP):
                self._release_direction(Tank.UP)
            elif event.key in (pygame.K_d, pygame.K_RIGHT):
                self._release_direction(Tank.RIGHT)
            elif event.key in (pygame.K_s, pygame.K_DOWN):
                self._release_direction(Tank.DOWN)
            elif event.key in (pygame.K_a, pygame.K_LEFT):
                self._release_direction(Tank.LEFT)

    def update(self):
        """更新游戏状态"""
        # 如果暂停，只更新UI管理器，跳过游戏逻辑
        if self.paused:
            # 更新UI管理器以处理暂停菜单
            time_delta = 1.0 / 60.0
            self.screen_manager.ui_manager.update(time_delta)
            return
        
        # Network Update
        if self.enable_network:
            self.network_manager.update()
            
            role = self.network_manager.stats.role
            
            if role == "client":
                # Client: Send Input -> Receive State -> Render
                # 1. Send Input
                # We need to capture current input state. 
                # Since handle_event updates _movement_stack, we can just send that?
                # Or better, send the raw key states or the resulting direction.
                # Let's send the current intended move direction and shoot status.
                input_data = {
                    "move": self._movement_stack[-1] if self._movement_stack else -1,
                    # "shoot": False # Don't send shoot here, it's an event handled by _player_shoot
                }
                self.network_manager.send_input(input_data)
                
                # 2. Client-Side Prediction: Update local player tank
                if self.player_tank and self.player_tank.active:
                    self.player_tank.update()  # Run local physics for immediate response
                
                # 2.5. Update bullets and explosions (for visual effects)
                # Bullets need to move and check collisions
                for bullet in self.game_world.bullets:
                    bullet.update()
                # Explosions need to animate
                for explosion in self.game_world.explosions:
                    explosion.update()
                
                # 3. Receive State and Reconcile
                remote_state = self.network_manager.get_latest_state()
                if remote_state:
                    # Server reconciliation: check if our prediction was correct
                    my_tank_data = remote_state.get('my_tank')
                    if my_tank_data and self.player_tank:
                        server_x = my_tank_data['x']
                        server_y = my_tank_data['y']
                        local_x = self.player_tank.x
                        local_y = self.player_tank.y
                        
                        # Calculate prediction error
                        error = ((server_x - local_x)**2 + (server_y - local_y)**2)**0.5
                        
                        if error > 5:  # Threshold for correction
                            # If error is HUGE, it's a teleport/respawn that state_manager missed (or lag)
                            # But state_manager should handle respawns now.
                            # Still, if error is very large, snap immediately.
                            if error > 50:
                                self.player_tank.x = server_x
                                self.player_tank.y = server_y
                                self.player_tank.rect.topleft = (server_x, server_y)
                            else:
                                # Smooth correction using lerp
                                alpha = 0.3  # Correction strength
                                self.player_tank.x = local_x + (server_x - local_x) * alpha
                                self.player_tank.y = local_y + (server_y - local_y) * alpha
                                self.player_tank.rect.topleft = (self.player_tank.x, self.player_tank.y)
                    
                    # Apply state for other entities (other players, bullets, etc.)
                    self.state_manager.decode_state(remote_state)
                
            elif role == "host":
                # Host: Receive Inputs -> Update Physics -> Send State
                # 1. Receive Inputs
                messages = self.network_manager.get_inputs()
                for msg in messages:
                    if msg.get("type") == "input":
                        inp = msg.get("payload")
                        if not inp:
                            continue
                        # Apply input to Player 2 (Client)
                        # Find client tank (P2 - Logic ID 2)
                        client_tank = next((t for t in self.game_world.tanks if t.tank_id == 2), None)
                        if client_tank:
                            move_dir = inp.get("move", -1)
                            # print(f"[Host] Processing input for P2: move={move_dir}")
                            if move_dir != -1:
                                client_tank.move(move_dir)
                            else:
                                client_tank.stop()
                            
                            # Process shoot input
                            if inp.get("shoot"):
                                self.game_world.spawn_bullet(client_tank)
                        else:
                            tank_ids = [t.tank_id for t in self.game_world.tanks if t.active]
                            print(f"[Host] Error: Client tank (ID 2) not found! Active tanks: {tank_ids}")
                            
                # 2. Update Physics - 只有在游戏未结束时才更新
                if self.current_state == "game" and not self.game_world.game_over:
                    self._update_enemy_ai()
                    self.game_world.update()
                    
                    # 检查游戏是否结束
                    if self._check_game_over():
                        # 游戏结束，停止所有音效
                        pygame.mixer.stop()
                        # 设置游戏结果并显示游戏结束屏幕
                        self.screen_manager.context.game_won = self.game_world.winner == "player"
                        # 通知屏幕管理器切换到游戏结束屏幕
                        self.screen_manager.set_state("game_over")
                        # 不要立即重置游戏世界，等回到主菜单时再重置
                    else:
                        # 3. Send State - 只有游戏未结束时才发送状态
                        state = self.state_manager.encode_state()
                        self.network_manager.send_state(state)
        
        else:
            # Single Player
            # 只有在游戏未结束时才更新游戏世界
            if self.current_state == "game" and not self.game_world.game_over:
                self._update_enemy_ai()
                self.game_world.update()
                
                # 检查游戏是否结束
                if self._check_game_over():
                    # 游戏结束，停止所有音效
                    pygame.mixer.stop()
                    # 设置游戏结果并显示游戏结束屏幕
                    self.screen_manager.context.game_won = self.game_world.winner == "player"
                    # 通知屏幕管理器切换到游戏结束屏幕
                    self.screen_manager.set_state("game_over")
                    # 不要立即重置游戏世界，等回到主菜单时再重置

        # UI Update
        self.screen_manager.update()
        
        # Sync State
        if self.screen_manager.current_state != self.current_state:
            self.current_state = self.screen_manager.current_state
            
            if self.current_state == "game":
                # Initialize Game World
                mode = self.screen_manager.context.game_mode
                if mode == "single":
                    self.enable_network = False
                    selected_map = getattr(self.screen_manager.context, 'selected_map', 'default')
                    self._setup_single_player_world(self.screen_manager.context.player_tank_id, selected_map)
                elif mode == "multi":
                    self.enable_network = True
                    # Determine P1/P2 IDs
                    # Determine P1/P2 IDs (Logic IDs)
                    # P1 is always 1, P2 is always 2
                    p1_logic_id = 1
                    p2_logic_id = 2
                    
                    # Skin IDs from context
                    p1_skin = self.screen_manager.context.player_tank_id if self.network_manager.stats.role == "host" else self.screen_manager.context.enemy_tank_id
                    p2_skin = self.screen_manager.context.enemy_tank_id if self.network_manager.stats.role == "host" else self.screen_manager.context.player_tank_id
                    
                    # Map Name from context
                    selected_map = getattr(self.screen_manager.context, 'selected_map', 'default')
                        
                    self.setup_multiplayer_world(p1_skin, p2_skin, selected_map)
                    
                    # Set player IDs for state manager
                    if self.network_manager.stats.role == "host":
                        self.state_manager.client_tank_id = p2_logic_id  # For encoding my_tank
                        self.state_manager.local_player_id = None  # Host doesn't skip
                    else:
                        self.state_manager.client_tank_id = None  # Client doesn't send my_tank
                        self.state_manager.local_player_id = p2_logic_id  # Skip this in decode
                elif mode == "level":
                    self.enable_network = False
                    # 设置当前关卡为选择的关卡
                    self.current_level = self.screen_manager.context.selected_level
                    selected_map = "default"  # 关卡模式使用生成的地图
                    player_skin = getattr(self.screen_manager.context, 'player_skin', 1)
                    self._setup_single_player_world(player_skin, selected_map)

        self.state_manager.update()

    def update_render_surface(self):
        """更新中间渲染表面尺寸"""
        # 游戏世界保持固定尺寸（28列*21行）
        grid_size = 50
        game_world_width = 28 * grid_size  # 28列
        game_world_height = 21 * grid_size  # 21行
        
        # 创建或更新中间渲染表面
        self.render_surface = pygame.Surface((game_world_width, game_world_height))
        
        # 更新游戏世界尺寸
        if self.game_world:
            self.game_world.width = game_world_width
            self.game_world.height = game_world_height
            self.game_world.bounds = pygame.Rect(0, 0, game_world_width, game_world_height)
    
    def render(self):
        """渲染游戏画面 - 实现宽高比适配"""
        # 1. 填充背景为黑色
        self.screen.fill((0, 0, 0))

        if self.current_state == "game":
            # 2. 确保中间渲染表面尺寸正确
            self.update_render_surface()
            
            # 3. 清空中间渲染表面
            self.render_surface.fill((0, 0, 0))
            
            # 4. 将游戏世界渲染到中间表面
            self.game_world.render(self.render_surface)
            
            # 5. 计算缩放比例和居中位置
            # 获取当前窗口的实际大小
            current_width, current_height = pygame.display.get_surface().get_size()
            
            # 计算游戏世界和窗口的宽高比
            game_world_aspect = self.render_surface.get_width() / self.render_surface.get_height()
            window_aspect = current_width / current_height
            
            # 根据宽高比决定缩放基准
            if window_aspect >= game_world_aspect:
                # 窗口更宽，以高度为基准缩放，保持游戏世界宽高比
                scale_factor = current_height / self.render_surface.get_height()
                scaled_width = int(self.render_surface.get_width() * scale_factor)
                scaled_height = current_height
            else:
                # 窗口更窄，以宽度为基准缩放，保持游戏世界宽高比
                scale_factor = current_width / self.render_surface.get_width()
                scaled_width = current_width
                scaled_height = int(self.render_surface.get_height() * scale_factor)
            
            # 计算居中位置
            x_offset = (current_width - scaled_width) // 2
            y_offset = (current_height - scaled_height) // 2
            
            # 6. 缩放并绘制游戏世界到主窗口
            scaled_surface = pygame.transform.scale(self.render_surface, (scaled_width, scaled_height))
            self.screen.blit(scaled_surface, (x_offset, y_offset))
            
            # 8. 绘制生命值显示（在非游戏区域）
            self._draw_lives_display(x_offset, y_offset, scaled_width, scaled_height)
            
            # 7. 渲染暂停菜单
            if self.paused and self.pause_menu:
                # 渲染半透明背景
                self.pause_menu.render()
                # 渲染UI元素（按钮和标签）
                self.screen_manager.ui_manager.draw_ui(self.screen)
        else:
            # 菜单界面直接渲染到主窗口
            self.screen_manager.render()

        pygame.display.flip()

    def _draw_lives_display(self, x_offset, y_offset, scaled_width, scaled_height):
        """在非游戏区域绘制玩家和敌人的生命值显示
        
        Args:
            x_offset: 游戏世界在屏幕上的x偏移量
            y_offset: 游戏世界在屏幕上的y偏移量
            scaled_width: 游戏世界的缩放后宽度
            scaled_height: 游戏世界的缩放后高度
        """
        # 初始化字体
        if not hasattr(self, 'lives_font'):
            self.lives_font = pygame.font.SysFont('SimHei', 24)
            self.lives_small_font = pygame.font.SysFont('SimHei', 18)
        
        # 计算生命值显示区域
        left_margin = x_offset // 2  # 左侧黑边的中间位置
        right_margin = x_offset + scaled_width + (x_offset // 2)  # 右侧黑边的中间位置
        
        # 玩家生命值信息
        player_lives = 0
        enemy_lives = 0
        
        # 统计玩家和敌人的剩余生命值
        for tank_id, lives in self.game_world.tank_lives.items():
            if tank_id in self.game_world.tank_info:
                tank_type = self.game_world.tank_info[tank_id].get('type', '')
                if tank_type == 'player':
                    player_lives += lives
                elif tank_type == 'enemy':
                    enemy_lives += lives
        
        # 绘制玩家生命值显示（左侧）
        player_text = f"玩家生命"
        player_lives_text = f"{player_lives}"
        
        # 绘制玩家标题
        player_title_surface = self.lives_font.render(player_text, True, (0, 255, 0))
        player_title_rect = player_title_surface.get_rect(
            center=(left_margin, scaled_height // 4)
        )
        self.screen.blit(player_title_surface, player_title_rect)
        
        # 绘制玩家生命值
        player_lives_surface = self.lives_font.render(player_lives_text, True, (255, 255, 0))
        player_lives_rect = player_lives_surface.get_rect(
            center=(left_margin, scaled_height // 4 + 30)
        )
        self.screen.blit(player_lives_surface, player_lives_rect)
        
        # 绘制敌人生命值显示（右侧）
        enemy_text = f"敌人生命"
        enemy_lives_text = f"{enemy_lives}"
        
        # 绘制敌人标题
        enemy_title_surface = self.lives_font.render(enemy_text, True, (255, 0, 0))
        enemy_title_rect = enemy_title_surface.get_rect(
            center=(right_margin, scaled_height // 4)
        )
        self.screen.blit(enemy_title_surface, enemy_title_rect)
        
        # 绘制敌人生命值
        enemy_lives_surface = self.lives_font.render(enemy_lives_text, True, (255, 255, 0))
        enemy_lives_rect = enemy_lives_surface.get_rect(
            center=(right_margin, scaled_height // 4 + 30)
        )
        self.screen.blit(enemy_lives_surface, enemy_lives_rect)
    
    def _check_game_over(self) -> bool:
        """检查游戏是否结束"""
        if self.game_world.game_over:
            if self.game_world.winner == "player":
                # 玩家获胜，解锁下一关卡
                from src.utils.level_progress import unlock_next_level
                unlock_next_level(self.current_level)
                
                # 玩家获胜，进入下一关卡
                if self.current_level < self.max_level:
                    # 准备进入下一关卡
                    print(f"[Game] 第 {self.current_level} 关完成！准备进入第 {self.current_level + 1} 关...")
                    self._prepare_next_level()
                    return False  # 游戏未结束，继续进行下一关卡
                else:
                    # 通关所有关卡
                    print(f"[Game] 恭喜！您已通关所有 {self.max_level} 关！")
                    self.game_won = True
                    return True
            else:
                # 玩家失败，游戏结束
                print(f"[Game] 第 {self.current_level} 关失败！游戏结束。")
                return True
        return False
    
    def _prepare_next_level(self):
        """准备进入下一关卡"""
        # 增加关卡数
        self.current_level += 1
        
        # 重置游戏世界
        self.game_world.reset()
        
        # 清除旧的敌人控制器
        self.enemy_controllers.clear()
        
        # 根据当前游戏模式重新设置游戏世界
        if hasattr(self.screen_manager.context, 'is_multiplayer') and self.screen_manager.context.is_multiplayer:
            # 联机模式
            p1_skin = getattr(self.screen_manager.context, 'p1_skin', 1)
            p2_skin = getattr(self.screen_manager.context, 'p2_skin', 2)
            selected_map = getattr(self.screen_manager.context, 'selected_map', 'default')
            self.setup_multiplayer_world(p1_skin, p2_skin, selected_map)
        else:
            # 单机模式
            player_skin = getattr(self.screen_manager.context, 'player_skin', 1)
            selected_map = getattr(self.screen_manager.context, 'selected_map', 'default')
            self._setup_single_player_world(player_skin, selected_map)
        
        print(f"[Game] 第 {self.current_level} 关已准备就绪！")

    # ------------------------------------------------------------------ #
    # 玩家控制
    # ------------------------------------------------------------------ #
    def _push_direction(self, direction: int):
        if direction in self._movement_stack:
            self._movement_stack.remove(direction)
        self._movement_stack.append(direction)
        self._apply_player_direction()

    def _release_direction(self, direction: int):
        if direction in self._movement_stack:
            self._movement_stack.remove(direction)
        self._apply_player_direction()

    def _apply_player_direction(self):
        # Client-Side Prediction: Both client and host move local player immediately
        
        # 重生检查：如果当前引用的坦克失效，尝试根据ID重新获取
        if (not self.player_tank or not self.player_tank.active) and self.local_player_id:
            # 尝试在活跃坦克列表中找到自己的坦克
            new_tank = next((t for t in self.game_world.tanks if t.tank_id == self.local_player_id and t.active), None)
            if new_tank:
                print(f"[Control] 重新获取玩家坦克引用 (ID: {self.local_player_id})")
                self.player_tank = new_tank

        if not self.player_tank or not self.player_tank.active:
            return
        if self._movement_stack:
            self.player_tank.move(self._movement_stack[-1])
        else:
            self.player_tank.stop()

    def _player_shoot(self):
        if self.enable_network and self.network_manager.stats.role == "client":
            # Client: Send shoot command
            self.network_manager.send_input({"move": self._movement_stack[-1] if self._movement_stack else -1, "shoot": True})
        else:
            # Host or Single: Shoot locally
            if self.player_tank and self.player_tank.active:
                self.game_world.spawn_bullet(self.player_tank)

    # ------------------------------------------------------------------ #
    # 敌人 AI
    # ------------------------------------------------------------------ #
    def _update_enemy_ai(self):
        """更新敌人AI"""
        # 检查是否有新生成的敌人需要分配AI控制器
        active_enemy_ids = {t.tank_id for t in self.game_world.tanks if t.active and t.tank_type == "enemy"}
        current_controller_ids = {c.tank_id for c in self.enemy_controllers}
        
        # 为新敌人创建控制器
        new_enemy_ids = active_enemy_ids - current_controller_ids
        for tank_id in new_enemy_ids:
            # 使用锁定的游戏难度，而不是从context读取（防止重生时难度改变）
            difficulty = self.game_difficulty if self.game_difficulty else 'normal'
            self.enemy_controllers.append(EnemyAIController(tank_id, self.game_world, difficulty))
            print(f"[AI] 为坦克 {tank_id} 创建AI控制器，难度: {difficulty}")
            
        # 移除已死亡敌人的控制器
        self.enemy_controllers = [c for c in self.enemy_controllers if c.tank_id in active_enemy_ids]
        
        # 更新所有控制器
        for controller in self.enemy_controllers:
            controller.update()
    
    def _toggle_pause(self):
        """切换暂停状态"""
        self.paused = not self.paused
        if self.paused:
            # 创建暂停菜单
            self.pause_menu = PauseMenuOverlay(self.screen, self.screen_manager.ui_manager.manager)
        else:
            # 销毁暂停菜单
            if self.pause_menu:
                self.pause_menu.cleanup()
                self.pause_menu = None

    def _restart_game(self):
        """重新开始游戏"""
        if self.pause_menu:
            self.pause_menu.cleanup()
            self.pause_menu = None
        self.paused = False
        
        # 重置关卡系统
        self.current_level = 1
        self.game_won = False
        
        # 重新初始化游戏世界
        self.game_world.reset()
        if hasattr(self.screen_manager.context, 'game_mode'):
            if self.screen_manager.context.game_mode == 'single':
                player_tank_id = getattr(self.screen_manager.context, 'player_tank_id', 1)
                map_name = getattr(self.screen_manager.context, 'selected_map', 'default')
                self._setup_single_player_world(player_tank_id, map_name)

    def _exit_to_menu(self):
        """退出到主菜单"""
        if self.pause_menu:
            self.pause_menu.cleanup()
            self.pause_menu = None
        self.paused = False
        
        # 停止所有音效
        pygame.mixer.stop()
        
        # 清理游戏状态
        self.game_world.reset()
        self.enemy_controllers.clear()
        self._movement_stack.clear()
        
        # 切换到菜单状态
        self.current_state = "menu"
        
        # 通知ScreenManager切换到菜单屏幕
        self.screen_manager.set_state("menu")
    
    def _spawn_cheat_prop(self, prop_id: int):
        """调试功能：在玩家坦克前方生成指定道具
        
        Args:
            prop_id: 道具ID (1-8)
        """
        if not self.player_tank or not self.player_tank.active:
            print(f"[Cheat] 无法生成道具：玩家坦克不存在或未激活")
            return
        
        # 获取玩家坦克位置和方向
        tank_x = self.player_tank.x
        tank_y = self.player_tank.y
        direction = self.player_tank.direction
        
        # 根据坦克方向计算道具生成位置（坦克前方50像素）
        offset = 50
        if direction == Tank.UP:
            prop_x = tank_x
            prop_y = tank_y - offset
        elif direction == Tank.RIGHT:
            prop_x = tank_x + offset
            prop_y = tank_y
        elif direction == Tank.DOWN:
            prop_x = tank_x
            prop_y = tank_y + offset
        elif direction == Tank.LEFT:
            prop_x = tank_x - offset
            prop_y = tank_y
        else:
            prop_x = tank_x
            prop_y = tank_y
        
        # 确保道具在地图范围内
        prop_x = max(0, min(prop_x, self.screen_width - 30))
        prop_y = max(0, min(prop_y, self.screen_height - 30))
        
        # 生成道具
        self.game_world.prop_manager.spawn_prop(prop_x, prop_y, prop_id)
        print(f"[Cheat] 生成道具 {prop_id} 于位置 ({prop_x}, {prop_y})")
