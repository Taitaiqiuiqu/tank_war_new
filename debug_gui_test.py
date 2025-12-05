import pygame
import pygame_gui
import os

# Initialize Pygame
pygame.init()

# Set up display
pygame.display.set_caption('Dropdown Test')
window_surface = pygame.display.set_mode((800, 600))
background = pygame.Surface((800, 600))
background.fill(pygame.Color('#000000'))

# Initialize UI Manager
# Ensure we use the same theme file if possible, otherwise default
theme_path = "d:/1tank_war_my/src/ui/theme.json"
if os.path.exists(theme_path):
    manager = pygame_gui.UIManager((800, 600), theme_path)
else:
    manager = pygame_gui.UIManager((800, 600))

# Create Dropdown with Chinese
dropdown_cn = pygame_gui.elements.UIDropDownMenu(
    options_list=['简单', '普通', '困难', '地狱'],
    starting_option='普通',
    relative_rect=pygame.Rect((100, 100), (200, 30)),
    manager=manager
)

# Create Dropdown with English
dropdown_en = pygame_gui.elements.UIDropDownMenu(
    options_list=['Easy', 'Normal', 'Hard', 'Hell'],
    starting_option='Normal',
    relative_rect=pygame.Rect((400, 100), (200, 30)),
    manager=manager
)

clock = pygame.time.Clock()
is_running = True

print("Test started. Please select options from both dropdowns.")

while is_running:
    time_delta = clock.tick(60)/1000.0
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            is_running = False

        if event.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
            print(f"Event: {event}")
            print(f"Event Text: {event.text}")
            if event.ui_element == dropdown_cn:
                print(f"CN Dropdown Selected: {dropdown_cn.selected_option}")
            elif event.ui_element == dropdown_en:
                print(f"EN Dropdown Selected: {dropdown_en.selected_option}")

        manager.process_events(event)

    manager.update(time_delta)

    window_surface.blit(background, (0, 0))
    manager.draw_ui(window_surface)

    pygame.display.update()
