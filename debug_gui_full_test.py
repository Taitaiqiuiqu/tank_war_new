import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Mimic src/ui/ui_components.py structure
print("Importing init_i18n...")
import src.ui.init_i18n

print("Importing pygame/pygame_gui...")
import pygame
import pygame_gui

print("Applying monkey patch...")
try:
    from pygame_gui.core import utility
    original_translate = utility.translate
    
    def patched_translate(text, **kwargs):
        """Bypass i18n translation to prevent errors"""
        # print(f"Translating: {text}") # Uncomment to debug translation calls
        if text is None:
            return ""
        return str(text)
    
    utility.translate = patched_translate
    print("Monkey patch applied.")
except Exception as e:
    print(f"Warning: Could not patch pygame_gui translate: {e}")

# Initialize Pygame
pygame.init()
pygame.display.set_caption('Full Stack Test')
window_surface = pygame.display.set_mode((800, 600))
background = pygame.Surface((800, 600))
background.fill(pygame.Color('#000000'))

# Initialize UI Manager
theme_path = "d:/1tank_war_my/src/ui/theme.json"
manager = pygame_gui.UIManager((800, 600), theme_path)

# Manually add font paths like UIManagerWrapper does
# We use the path we know exists
font_path = "C:/Windows/Fonts/msyh.ttc"
manager.add_font_paths("chinese", font_path)
print(f"Added font path: {font_path}")

# Create Dropdown
dropdown = pygame_gui.elements.UIDropDownMenu(
    options_list=['简单', '普通', '困难', '地狱'],
    starting_option='普通',
    relative_rect=pygame.Rect((350, 275), (100, 30)),
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
            print(f"Event Dict: {event.__dict__}")
            print(f"Dropdown Selected: {dropdown.selected_option}")

        manager.process_events(event)

    manager.update(time_delta)

    window_surface.blit(background, (0, 0))
    manager.draw_ui(window_surface)

    pygame.display.update()
