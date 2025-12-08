import pygame
import ctypes
import sys

def check_resolution():
    pygame.init()
    
    print("--- Pygame Info ---")
    info = pygame.display.Info()
    print(f"Pygame Display Info: {info.current_w}x{info.current_h}")
    
    print("\n--- Ctypes Info (Physical) ---")
    try:
        user32 = ctypes.windll.user32
        # Method 1: GetSystemMetrics
        w = user32.GetSystemMetrics(0)
        h = user32.GetSystemMetrics(1)
        print(f"GetSystemMetrics(0,1): {w}x{h}")
        
        # Method 2: EnumDisplaySettings
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
        
        devmode = DEVMODE()
        devmode.dmSize = ctypes.sizeof(DEVMODE)
        if user32.EnumDisplaySettingsW(None, -1, ctypes.byref(devmode)):
            print(f"EnumDisplaySettings: {devmode.dmPelsWidth}x{devmode.dmPelsHeight}")
            
    except Exception as e:
        print(f"Error accessing ctypes: {e}")

    print("\n--- DPI Awareness Check ---")
    try:
        shcore = ctypes.windll.shcore
        awareness = ctypes.c_int()
        shcore.GetProcessDpiAwareness(0, ctypes.byref(awareness))
        print(f"GetProcessDpiAwareness: {awareness.value} (0=Unaware, 1=System, 2=PerMonitor)")
    except Exception as e:
        print(f"Could not check DPI awareness: {e}")

    pygame.quit()

if __name__ == "__main__":
    check_resolution()
