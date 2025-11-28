import pygame
import pygame_gui
from pygame_gui.elements import UIButton, UILabel, UITextEntryLine, UISelectionList, UIImage
from pygame_gui.windows import UIMessageWindow

from src.ui.screen_manager import BaseScreen, ScreenContext
from src.ui.ui_components import UIManagerWrapper
from src.utils.resource_manager import resource_manager


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
            relative_rect=pygame.Rect((center_x - btn_width // 2, center_y - 100 + btn_height + spacing), (btn_width, btn_height)),
            text='联机模式',
            manager=self.manager
        )
        
        self.btn_settings = UIButton(
            relative_rect=pygame.Rect((center_x - btn_width // 2, center_y - 100 + (btn_height + spacing) * 2), (btn_width, btn_height)),
            text='设置',
            manager=self.manager
        )
        
        self.btn_exit = UIButton(
            relative_rect=pygame.Rect((center_x - btn_width // 2, center_y - 100 + (btn_height + spacing) * 3), (btn_width, btn_height)),
            text='退出游戏',
            manager=self.manager
        )

    def handle_event(self, event: pygame.event.Event):
        super().handle_event(event)
        
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.btn_single:
                # 进入单机设置
                # TODO: 暂时直接开始游戏，后续跳转到 SinglePlayerSetupScreen
                # self.screen_manager.set_state("single_setup") 
                # 这里需要一种方式通知 ScreenManager 切换状态，或者通过 context 回调
                # 目前 BaseScreen 没有直接引用 ScreenManager，可以通过 context 传递回调或者事件
                # 简单起见，我们在 ScreenManager 中轮询 context 的状态请求，或者让 handle_event 返回新状态
                # 但为了保持架构简单，我们可以约定 context 中有一个 next_state 字段
                self.context.next_state = "single_setup"
                
            elif event.ui_element == self.btn_multi:
                self.context.next_state = "lobby"
                
            elif event.ui_element == self.btn_settings:
                self.context.next_state = "settings"
                
            elif event.ui_element == self.btn_exit:
                pygame.event.post(pygame.event.Event(pygame.QUIT))

    def render(self):
        self.surface.fill((30, 30, 30))
        # 绘制标题
        title_surf = self.font.render("坦克大战", True, (255, 215, 0))
        self.surface.blit(title_surf, title_surf.get_rect(center=(self.surface.get_width() // 2, 100)))


class SinglePlayerSetupScreen(BaseScreen):
    """单机模式设置屏幕"""
    
    def on_enter(self):
        super().on_enter()
        
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
        super().handle_event(event)
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.btn_start:
                self.context.next_state = "game"
                self.context.game_mode = "single"
            elif event.ui_element == self.btn_back:
                self.context.next_state = "menu"
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


class LobbyScreen(BaseScreen):
    """联机大厅屏幕"""
    
    def on_enter(self):
        super().on_enter()
        
        self.surface_width = self.surface.get_width()
        
        # 用户名输入
        UILabel(
            relative_rect=pygame.Rect((50, 50), (100, 30)),
            text="用户名:",
            manager=self.manager
        )
        self.username_entry = UITextEntryLine(
            relative_rect=pygame.Rect((160, 50), (200, 30)),
            manager=self.manager
        )
        self.username_entry.set_text("Player1")
        
        # 房间列表
        UILabel(
            relative_rect=pygame.Rect((50, 100), (200, 30)),
            text="房间列表:",
            manager=self.manager
        )
        self.room_list = UISelectionList(
            relative_rect=pygame.Rect((50, 140), (500, 300)),
            item_list=[], 
            manager=self.manager
        )
        
        # 按钮
        self.btn_create = UIButton(
            relative_rect=pygame.Rect((600, 140), (150, 50)),
            text='创建房间',
            manager=self.manager
        )
        
        self.btn_join = UIButton(
            relative_rect=pygame.Rect((600, 210), (150, 50)),
            text='加入房间',
            manager=self.manager
        )
        
        self.btn_refresh = UIButton(
            relative_rect=pygame.Rect((600, 280), (150, 50)),
            text='刷新列表',
            manager=self.manager
        )
        
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
        pass

    def update(self, time_delta: float):
        super().update(time_delta)
        # Refresh room list from NetworkManager
        # Assuming we have access...
        # For now, let's implement the UI logic assuming `self.network_manager` exists.
        # I will update ScreenManager next.
        if hasattr(self, 'network_manager'):
            # Update room list
            rooms = [f"{r[1]} ({r[0]})" for r in self.network_manager.found_servers]
            # Only update if changed to avoid flickering
            # self.room_list.set_item_list(rooms) 
            pass

    def handle_event(self, event: pygame.event.Event):
        super().handle_event(event)
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.btn_create:
                # Start Host
                if hasattr(self, 'network_manager'):
                    self.network_manager.start_host()
                self.context.next_state = "room"
                self.context.is_host = True
                self.context.game_mode = "multi"
                
            elif event.ui_element == self.btn_join:
                # Join selected
                selected = self.room_list.get_single_selection()
                if selected:
                    # Parse IP from string "RoomName (IP)"
                    ip = selected.split('(')[-1].strip(')')
                    if hasattr(self, 'network_manager'):
                        self.network_manager.start_client()
                        if self.network_manager.connect_to_server(ip):
                            self.context.next_state = "room"
                            self.context.is_host = False
                            self.context.game_mode = "multi"
                else:
                    # If no selection, just start client discovery for now
                    if hasattr(self, 'network_manager'):
                        self.network_manager.start_client()
                        self.network_manager.broadcast_discovery()
                        
            elif event.ui_element == self.btn_refresh:
                if hasattr(self, 'network_manager'):
                    self.network_manager.start_client()
                    self.network_manager.broadcast_discovery()
                    # Update list
                    rooms = [f"{r[1]} ({r[0]})" for r in self.network_manager.found_servers]
                    self.room_list.set_item_list(rooms)

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
            relative_rect=pygame.Rect((50, 100), (300, 300)),
            item_list=["Player1 (Host)"], 
            manager=self.manager
        )
        
        # Tank Selection UI
        self.local_tank_id = 1
        self.remote_tank_id = 1
        self.context.player_tank_id = 1
        self.context.enemy_tank_id = 1
        
        # Local Tank (Left side)
        UILabel(relative_rect=pygame.Rect((50, 150), (100, 30)), text="你的坦克", manager=self.manager)
        self.local_image_rect = pygame.Rect((50, 190), (100, 100))
        self.local_image_elem = None
        
        self.btn_prev = UIButton(relative_rect=pygame.Rect((50, 300), (45, 30)), text='<', manager=self.manager)
        self.btn_next = UIButton(relative_rect=pygame.Rect((105, 300), (45, 30)), text='>', manager=self.manager)
        
        # Remote Tank (Right side) - Display Only
        UILabel(relative_rect=pygame.Rect((200, 150), (100, 30)), text="对手坦克", manager=self.manager)
        self.remote_image_rect = pygame.Rect((200, 190), (100, 100))
        self.remote_image_elem = None
        
        self._update_images()

        self.btn_ready = UIButton(
            relative_rect=pygame.Rect((400, 100), (150, 50)),
            text='准备',
            manager=self.manager
        )
        
        # 仅房主可见
        self.btn_start = UIButton(
            relative_rect=pygame.Rect((400, 170), (150, 50)),
            text='开始游戏',
            manager=self.manager
        )
        if not getattr(self.context, 'is_host', False):
            self.btn_start.hide()
            
        self.btn_leave = UIButton(
            relative_rect=pygame.Rect((50, 450), (150, 50)),
            text='离开房间',
            manager=self.manager
        )

    def _update_images(self):
        # Local
        if self.local_image_elem: self.local_image_elem.kill()
        images = resource_manager.load_tank_images('player', self.local_tank_id, 0)
        surf = pygame.transform.scale(images[0][0], (100, 100)) if images and images.get(0) else pygame.Surface((100, 100))
        self.local_image_elem = UIImage(relative_rect=self.local_image_rect, image_surface=surf, manager=self.manager)
        
        # Remote
        if self.remote_image_elem: self.remote_image_elem.kill()
        # For remote, we might want to show a different color or just the tank they picked
        # Assuming they pick from same pool 'player'
        images = resource_manager.load_tank_images('player', self.remote_tank_id, 0)
        surf = pygame.transform.scale(images[0][0], (100, 100)) if images and images.get(0) else pygame.Surface((100, 100))
        self.remote_image_elem = UIImage(relative_rect=self.remote_image_rect, image_surface=surf, manager=self.manager)

    def update(self, time_delta: float):
        super().update(time_delta)
        # Check connection status
        if hasattr(self, 'network_manager'):
            if self.network_manager.stats.connected:
                self.player_list.set_item_list(["Player1 (Host)", "Player2 (Client)"])
            else:
                self.player_list.set_item_list(["Player1 (Host)"])
                
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
            else:
                # Client: Check for game start
                # Flush state queue to populate event queue (and get latest state if needed)
                self.network_manager.get_latest_state()
                
                # Check events
                events = self.network_manager.get_events()
                for event in events:
                    if event.get("type") == "game_start":
                        payload = event.get("payload")
                        if payload:
                            # Game Start!
                            self.context.enemy_tank_id = payload["p1_tank_id"] # Host is enemy for client
                            self.context.player_tank_id = payload["p2_tank_id"] # Client is p2
                            # Update local selection to match what Host assigned
                            self.local_tank_id = self.context.player_tank_id
                            
                            self.context.next_state = "game"

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
                    # Send Game Start with tank IDs
                    # Host is p1, Client is p2
                    self.network_manager.send_game_start(self.local_tank_id, self.remote_tank_id)
                
                self.context.player_tank_id = self.local_tank_id
                self.context.enemy_tank_id = self.remote_tank_id
                self.context.next_state = "game"
                
            elif event.ui_element == self.btn_prev:
                self.local_tank_id -= 1
                if self.local_tank_id < 1: self.local_tank_id = 4
                self._update_images()
                if not self.context.is_host and hasattr(self, 'network_manager'):
                    self.network_manager.send_lobby_update(self.local_tank_id)
                    
            elif event.ui_element == self.btn_next:
                self.local_tank_id += 1
                if self.local_tank_id > 4: self.local_tank_id = 1
                self._update_images()
                if not self.context.is_host and hasattr(self, 'network_manager'):
                    self.network_manager.send_lobby_update(self.local_tank_id)

            elif event.ui_element == self.btn_ready:
                pass

    def render(self):
        self.surface.fill((50, 30, 30))
