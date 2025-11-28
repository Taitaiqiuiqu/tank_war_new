import pygame
import pygame_gui
from pygame_gui.elements import UIButton, UILabel, UITextEntryLine, UISelectionList
from pygame_gui.windows import UIMessageWindow

from src.ui.screen_manager import BaseScreen, ScreenContext
from src.ui.ui_components import UIManagerWrapper


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
        
        UILabel(
            relative_rect=pygame.Rect((center_x - 100, 100), (200, 50)),
            text="选择你的坦克",
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

    def handle_event(self, event: pygame.event.Event):
        super().handle_event(event)
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.btn_start:
                self.context.next_state = "game"
                # 设置单机模式标志
                # self.context.game_mode = "single" 
            elif event.ui_element == self.btn_back:
                self.context.next_state = "menu"

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

    def update(self, time_delta: float):
        super().update(time_delta)
        # Check connection status
        if hasattr(self, 'network_manager'):
            if self.network_manager.stats.connected:
                self.player_list.set_item_list(["Player1 (Host)", "Player2 (Client)"])
            else:
                self.player_list.set_item_list(["Player1 (Host)"])
                
            # Client: Check if game started (received state)
            if not self.context.is_host:
                state = self.network_manager.get_latest_state()
                if state:
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
                self.context.next_state = "game"
            elif event.ui_element == self.btn_ready:
                pass

    def render(self):
        self.surface.fill((50, 30, 30))
