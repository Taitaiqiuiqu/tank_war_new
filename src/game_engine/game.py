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


class EnemyAIController:
    """极简敌人 AI：随机改变方向并偶尔射击。"""

    def __init__(self, tank: Tank, world: GameWorld):
        self.tank = tank
        self.world = world
        self.direction_timer = 0
        self.shoot_timer = 0

    def update(self):
        if not self.tank.active:
            return
        self.direction_timer -= 1
        self.shoot_timer -= 1
        if self.direction_timer <= 0:
            self.tank.move(random.choice([Tank.UP, Tank.RIGHT, Tank.DOWN, Tank.LEFT]))
            self.direction_timer = random.randint(30, 120)
        if self.shoot_timer <= 0:
            self.world.spawn_bullet(self.tank)
            self.shoot_timer = random.randint(90, 180)


class GameEngine:
    """游戏引擎核心类，负责协调各个模块的工作"""

    def __init__(self, enable_network: bool = False):
        """初始化游戏引擎"""
        # 设置游戏窗口
        self.screen_width = 800
        self.screen_height = 600
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("坦克大战 - 单机试玩")

        # 核心模块
        # 核心模块
        self.network_manager = NetworkManager()
        self.screen_manager = ScreenManager(self.screen, self.network_manager)
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

        self._setup_single_player_world()
        
        # 播放游戏开始音效
        resource_manager.play_sound("start")

    def _setup_single_player_world(self):
        """初始化单机模式对象。"""
        # 使用50x50网格系统，避免墙体重叠
        # 地图：800x600，可以放置 16列 x 12行
        grid_size = 50
        
        # 调整坦克出生点（适应30x30坦克）
        player_spawn = (self.screen_width // 2 - 15, self.screen_height - 100)
        enemy_spawn = (self.screen_width // 2 - 15, 50)

        self.game_world.register_spawn_points("player", [player_spawn])
        self.game_world.register_spawn_points("enemy", [enemy_spawn])

        self.player_tank = self.game_world.spawn_tank("player", tank_id=1, position=player_spawn)
        enemy_tank = self.game_world.spawn_tank("enemy", tank_id=1, position=enemy_spawn)
        self.enemy_controllers.append(EnemyAIController(enemy_tank, self.game_world))

        # 使用50x50网格创建地图布局
        # 中间一排砖墙（第6行，y=300）
        for col in range(4, 12):  # 列4-11
            x = col * grid_size
            y = 6 * grid_size
            self.game_world.spawn_wall(x, y, Wall.BRICK)
        
        # 左侧钢墙（列1）
        for row in range(2, 10):  # 行2-9
            x = 1 * grid_size
            y = row * grid_size
            self.game_world.spawn_wall(x, y, Wall.STEEL)
        
        # 右侧钢墙（列14）
        for row in range(2, 10):  # 行2-9
            x = 14 * grid_size
            y = row * grid_size
            self.game_world.spawn_wall(x, y, Wall.STEEL)
        
        # 添加一些草地（列7-8，行4-5）
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

    def setup_multiplayer_world(self):
        """初始化联机模式对象"""
        self.game_world.reset()
        grid_size = 50
        
        # P1 Spawn
        p1_spawn = (self.screen_width // 2 - 100, self.screen_height - 100)
        self.player_tank = self.game_world.spawn_tank("player", tank_id=1, position=p1_spawn)
        
        # P2 Spawn
        p2_spawn = (self.screen_width // 2 + 100, self.screen_height - 100)
        self.game_world.spawn_tank("player", tank_id=2, position=p2_spawn)
        
        # Enemy Spawn
        enemy_spawn = (self.screen_width // 2 - 15, 50)
        enemy_tank = self.game_world.spawn_tank("enemy", tank_id=3, position=enemy_spawn)
        self.enemy_controllers.append(EnemyAIController(enemy_tank, self.game_world))
        
        # Map (Same as single player for now)
        # 中间一排砖墙（第6行，y=300）
        for col in range(4, 12):  # 列4-11
            x = col * grid_size
            y = 6 * grid_size
            self.game_world.spawn_wall(x, y, Wall.BRICK)

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
                    "shoot": False # TODO: Capture shoot event? 
                    # Shooting is an event, not a state. 
                    # We handled shooting in handle_event by calling _player_shoot.
                    # For client, _player_shoot should SEND a shoot command instead of spawning bullet.
                }
                self.network_manager.send_input(input_data)
                
                # 2. Receive State
                remote_state = self.network_manager.get_latest_state()
                if remote_state:
                    self.state_manager.decode_state(remote_state)
                    
                # 3. Skip local physics update
                # self.game_world.update() # Client does NOT update physics
                
            elif role == "host":
                # Host: Receive Inputs -> Update Physics -> Send State
                # 1. Receive Inputs
                inputs = self.network_manager.get_inputs()
                for inp in inputs:
                    # Apply input to Player 2 (Client)
                    # We need a reference to Player 2 tank.
                    # For now, let's assume tank_id=2 is client.
                    client_tank = next((t for t in self.game_world.tanks if t.tank_id == 2), None)
                    if client_tank:
                        move_dir = inp.get("move", -1)
                        if move_dir != -1:
                            client_tank.move(move_dir)
                        else:
                            client_tank.stop()
                        
                        if inp.get("shoot"):
                            self.game_world.spawn_bullet(client_tank)
                            
                # 2. Update Physics
                if self.current_state == "game":
                    self._update_enemy_ai()
                    self.game_world.update()
                    
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

        self.state_manager.update()

    def render(self):
        """渲染游戏画面"""
        self.screen.fill((0, 0, 0))

        if self.current_state == "game":
            self.game_world.render(self.screen)
        else:
            self.screen_manager.render()

        pygame.display.flip()

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
        # If Client, we don't move locally immediately (or we do for prediction?)
        # For "Dumb Terminal", we don't move locally. We send input.
        # But to feel responsive, we might want to move locally?
        # Let's stick to "Dumb Terminal" for now to avoid sync issues.
        # Wait, if we don't move locally, the player sees lag.
        # But handle_event calls this.
        
        if self.enable_network and self.network_manager.stats.role == "client":
            # Client: Do nothing here, input is sent in update()
            pass
        else:
            # Host or Single: Move local player (Tank 1)
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
