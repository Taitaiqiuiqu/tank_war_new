import sys
sys.path.append('d:\\1tank_war_my')
import pygame
import ctypes
from src.game_engine.game import GameEngine

try:
    print("Initializing GameEngine...")
    pygame.init()
    # Mocking pygame.display.set_mode to avoid opening actual window if possible, 
    # but we want to test the init logic which calls set_mode.
    # We'll just run it and close it quickly.
    
    game = GameEngine()
    print("GameEngine initialized successfully.")
    
    # Check awareness
    try:
        shcore = ctypes.windll.shcore
        awareness = ctypes.c_int()
        shcore.GetProcessDpiAwareness(0, ctypes.byref(awareness))
        print(f"Current Process DPI Awareness: {awareness.value}")
        if awareness.value == 1:
            print("SUCCESS: DPI Awareness is set to System DPI Aware.")
        else:
            print(f"WARNING: DPI Awareness is {awareness.value} (Expected 1)")
    except Exception as e:
        print(f"Could not check awareness: {e}")
        
    pygame.quit()
    
except Exception as e:
    print(f"An error occurred: {e}")
    import traceback
    traceback.print_exc()
