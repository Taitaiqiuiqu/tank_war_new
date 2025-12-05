import pygame
import pygame_gui
import os

# Monkey patch pygame_gui's translate function (SAME AS ui_components.py)
try:
    from pygame_gui.core import utility
    original_translate = utility.translate
    
    def patched_translate(text, **kwargs):
        """Bypass i18n translation to prevent errors"""
        if text is None:
            return ""
        return str(text)
    
    utility.translate = patched_translate
    print("Monkey patch applied.")
except Exception as e:
    print(f"Warning: Could not patch pygame_gui translate: {e}")

# Initialize Pygame
pygame.init()

# Set up display
pygame.display.set_caption('Dropdown Patch Test')
window_surface = pygame.display.set_mode((800, 600))
background = pygame.Surface((800, 600))
background.fill(pygame.Color('#000000'))

# Initialize UI Manager
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

clock = pygame.time.Clock()
is_running = True

print("Test started. Please select options.")

while is_running:
    time_delta = clock.tick(60)/1000.0
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            is_running = False

        if event.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
            print(f"Event: {event}")
            print(f"Event Text: {event.text}")
            print(f"Dropdown Selected: {dropdown_cn.selected_option}")

        manager.process_events(event)

    manager.update(time_delta)

    window_surface.blit(background, (0, 0))
    manager.draw_ui(window_surface)

    pygame.display.update()
