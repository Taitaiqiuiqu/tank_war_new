"""
深度调试脚本 - 追踪下拉菜单的完整事件流程
"""
import src.ui.init_i18n
import pygame
import pygame_gui

pygame.init()
window = pygame.display.set_mode((800, 600))
manager = pygame_gui.UIManager((800, 600), "d:/1tank_war_my/src/ui/theme.json")

# 手动添加字体路径
manager.add_font_paths("chinese", "C:/Windows/Fonts/msyh.ttc")

# 创建下拉菜单
dropdown = pygame_gui.elements.UIDropDownMenu(
    options_list=['简单', '普通', '困难', '地狱'],
    starting_option='普通',
    relative_rect=pygame.Rect((350, 275), (100, 30)),
    manager=manager
)

print(f"Dropdown created: {dropdown}")
print(f"Initial selected_option: {dropdown.selected_option}")
print(f"Options list: {dropdown.options_list}")

# 尝试手动调用内部方法
print(f"\nDropdown internal state:")
print(f"  current_state: {dropdown.current_state}")
print(f"  selected_option: {dropdown.selected_option}")

clock = pygame.time.Clock()
running = True
event_count = 0

while running:
    time_delta = clock.tick(60)/1000.0
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        # 在 process_events 之前检查事件
        if event.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
            event_count += 1
            print(f"\n=== Event #{event_count} ===")
            print(f"Event type: {event.type}")
            print(f"Event dict: {event.__dict__}")
            print(f"Dropdown.selected_option BEFORE: {dropdown.selected_option}")
        
        manager.process_events(event)
        
        # 在 process_events 之后再次检查
        if event.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
            print(f"Dropdown.selected_option AFTER: {dropdown.selected_option}")
            
            # 尝试直接访问内部状态
            if hasattr(dropdown, 'current_state'):
                print(f"Current state type: {type(dropdown.current_state)}")
                if hasattr(dropdown.current_state, 'selected_option'):
                    print(f"State.selected_option: {dropdown.current_state.selected_option}")
    
    manager.update(time_delta)
    window.fill((0, 0, 0))
    manager.draw_ui(window)
    pygame.display.update()

pygame.quit()
