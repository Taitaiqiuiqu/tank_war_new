import random
from typing import List, Optional

import pygame

from src.game_engine.game_world import GameWorld
from src.game_engine.tank import Tank
from src.game_engine.wall import Wall
from src.network.network_manager import NetworkManager
from src.state_sync.state_manager import StateManager
from src.ui.screen_manager import ScreenManager
from src.utils.resource_manager import resource_manager
from src.utils.map_loader import map_loader
from src.game_engine.window_manager import WindowManager


class EnemyAIController:
    """极简敌人 AI：随机改变方向并偶尔射击。"""

    def __init__(self, tank_id: int, world: GameWorld):
        self.tank_id = tank_id
        self.world = world
        self.direction_timer = 0
        self.shoot_timer = 0

    def update(self):
        # 动态查找坦克实例
        tank = next((t for t in self.world.tanks if t.tank_id == self.tank_id and t.active), None)
        if not tank:
            return

        self.direction_timer -= 1
        self.shoot_timer -= 1
        if self.direction_timer <= 0:
            tank.move(random.choice([Tank.UP, Tank.RIGHT, Tank.DOWN, Tank.LEFT]))
            self.direction_timer = random.randint(30, 120)
        if self.shoot_timer <= 0:
            self.world.spawn_bullet(tank)
            self.shoot_timer = random.randint(90, 180)


class GameEngine:
    """游戏引擎核心类，负责协调各个模块的工作"""

    def __init__(self, enable_network: bool = False):
        """初始化游戏引擎"""
        # 设置游戏窗口
        self.screen = pygame.display.set_mode((800, 600))
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
        self.game_world = GameWorld(self.screen_width, self.screen_height)
        self.state_manager.attach_world(self.game_world)

        # 游戏状态
        self.is_running = True
        self.current_state = "menu"  # menu, lobby, game, settings
        self.enable_network = enable_network
        self.player_tank: Optional[Tank] = None
        self.enemy_controllers: List[EnemyAIController] = []
        self._movement_stack: List[int] = []
        
        # 播放游戏开始音效
        resource_manager.play_sound("start")

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
        # 重新创建游戏世界以适应新的尺寸
        self.game_world = GameWorld(width, height)
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
        # 更新窗口相关属性
        self.screen_width = width
        self.screen_height = height
        self.screen = self.window_manager.game_surface
        
        # 重新创建游戏世界以适应新的尺寸
        self.game_world = GameWorld(width, height)
        self.state_manager.attach_world(self.game_world)
        
        # 通知ScreenManager窗口大小已改变
        if self.screen_manager:
            self.screen_manager.notify_window_resized(width, height)
            self.screen_manager.game_engine = self  # 确保引用正确
            
        print(f"游戏引擎已响应窗口大小改变: {width}x{height}")
        
    def _setup_single_player_world(self, player_tank_id=1, map_name="default"):
        """初始化单机模式对象。"""
        self._movement_stack.clear()
        self.enemy_controllers.clear()  # 清除旧的控制器
        grid_size = 50
        
        # Try to load custom map
        map_data = None
        if map_name != "default":
            map_data = map_loader.load_map(map_name)
            if map_data:
                print(f"加载自定义地图: {map_data.get('name', map_name)}")
        
        if map_data:
            # Load from map file
            # Spawn points - Single player mode only uses first player spawn
            player_spawns = map_data.get('player_spawns', [[400, 550]])
            enemy_spawns = map_data.get('enemy_spawns', [[400, 50]])
            
            # Single player: only use first player spawn point
            player_spawn = tuple(player_spawns[0]) if player_spawns else (400, 550)
            enemy_spawn = tuple(enemy_spawns[0]) if enemy_spawns else (400, 50)
            
            self.game_world.register_spawn_points("player", [player_spawn])
            self.game_world.register_spawn_points("enemy", [enemy_spawn])
            
            self.player_tank = self.game_world.spawn_tank("player", tank_id=player_tank_id, position=player_spawn, skin_id=player_tank_id)
            self.game_world.spawn_tank("enemy", tank_id=1, position=enemy_spawn)
            self.enemy_controllers.append(EnemyAIController(1, self.game_world))
            
            # Load walls
            walls = map_data.get('walls', [])
            for wall in walls:
                x = wall.get('x', 0)
                y = wall.get('y', 0)
                wall_type = wall.get('type', 0)
                self.game_world.spawn_wall(x, y, wall_type)
        else:
            # Use default map
            # 调整坦克出生点（适应30x30坦克）
            player_spawn = (self.screen_width // 2 - 15, self.screen_height - 100)
            enemy_spawn = (self.screen_width // 2 - 15, 50)

            self.game_world.register_spawn_points("player", [player_spawn])
            self.game_world.register_spawn_points("enemy", [enemy_spawn])

            self.player_tank = self.game_world.spawn_tank("player", tank_id=player_tank_id, position=player_spawn)
            self.game_world.spawn_tank("enemy", tank_id=1, position=enemy_spawn)
            self.enemy_controllers.append(EnemyAIController(1, self.game_world))

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
        grid_size = 50
        
        # Load Map
        map_data = None
        
        # Priority 1: Use received map data from host (for client)
        if hasattr(self.screen_manager.context, 'received_map_data') and self.screen_manager.context.received_map_data:
            map_data = self.screen_manager.context.received_map_data
            print(f"使用接收的地图数据: {map_data.get('name', map_name)}")
        # Priority 2: Load from local file
        elif map_name != "default":
            map_data = map_loader.load_map(map_name)
            if map_data:
                print(f"加载联机地图: {map_data.get('name', map_name)}")
        
        # Default Spawns
        p1_spawn = (self.screen_width // 2 - 100, self.screen_height - 100)
        p2_spawn = (self.screen_width // 2 + 100, self.screen_height - 100)
        enemy_spawn = (self.screen_width // 2 - 15, 50)
        
        if map_data:
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
                
        # Determine which tank is local player
        is_host = self.network_manager.stats.role == "host"
        
        # Spawn P1 (Host) - Logic ID 1
        p1 = self.game_world.spawn_tank("player", tank_id=1, position=p1_spawn, skin_id=p1_tank_id)
        
        # P2 Spawn (Client) - Logic ID 2
        p2 = self.game_world.spawn_tank("player", tank_id=2, position=p2_spawn, skin_id=p2_tank_id)
        
        if is_host:
            self.player_tank = p1
        else:
            self.player_tank = p2
        
        # Enemy Spawn
        self.game_world.spawn_tank("enemy", tank_id=3, position=enemy_spawn)
        self.enemy_controllers.append(EnemyAIController(3, self.game_world))
        
        # Map Walls
        if map_data:
            walls = map_data.get('walls', [])
            for wall in walls:
                x = wall.get('x', 0)
                y = wall.get('y', 0)
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

        if self.current_state != "game":
            return

        if event.type == pygame.KEYDOWN:
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
            elif event.key == pygame.K_ESCAPE:
                self.is_running = False

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
                            
                # 2. Update Physics
                if self.current_state == "game":
                    self._update_enemy_ai()
                    self.game_world.update()
                    
                    # 检查游戏是否结束
                    if self._check_game_over():
                        # 游戏结束，返回主菜单
                        self.current_state = "menu"
                        self.game_world.reset()
                    
                # 3. Send State
                state = self.state_manager.encode_state()
                self.network_manager.send_state(state)
        
        else:
            # Single Player
            if self.current_state == "game":
                self._update_enemy_ai()
                self.game_world.update()

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

        self.state_manager.update()

    def render(self):
        """渲染游戏画面"""
        self.screen.fill((0, 0, 0))

        if self.current_state == "game":
            self.game_world.render(self.screen)
        else:
            self.screen_manager.render()

        pygame.display.flip()

    def _check_game_over(self) -> bool:
        """检查游戏是否结束"""
        return self.game_world.game_over

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
        for controller in self.enemy_controllers:
            controller.update()
