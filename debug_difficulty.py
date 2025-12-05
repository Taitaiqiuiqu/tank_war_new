import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.game_engine.ai_config import DIFFICULTY_CONFIGS, get_difficulty_key_by_name, get_difficulty_names

print("=== Difficulty Config Debug ===")
print(f"Configs: {DIFFICULTY_CONFIGS.keys()}")
print(f"Names: {get_difficulty_names()}")

test_names = ["简单", "普通", "困难", "地狱", "NonExistent"]
for name in test_names:
    key = get_difficulty_key_by_name(name)
    print(f"Testing '{name}': -> '{key}'")
    if name != "NonExistent" and key == "normal" and name != "普通":
        print(f"  [WARNING] '{name}' mapped to default 'normal'!")

print("=== End Debug ===")
