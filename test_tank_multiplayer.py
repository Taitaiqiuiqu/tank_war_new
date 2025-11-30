"""
简单测试脚本：验证联机模式下坦克ID和动画
"""

import pygame
from src.game_engine.game_world import GameWorld
from src.game_engine.tank import Tank

# 初始化pygame
pygame.init()
pygame.display.set_mode((100, 100))

# 创建游戏世界
world = GameWorld(800, 600)

# 模拟联机模式：生成两个玩家坦克
p1 = world.spawn_tank("player", tank_id=1, position=(100, 100), skin_id=1)
p2 = world.spawn_tank("player", tank_id=2, position=(200, 200), skin_id=2)

print(f"P1 - Logic ID: {p1.tank_id}, Skin ID: {p1.skin_id}")
print(f"P2 - Logic ID: {p2.tank_id}, Skin ID: {p2.skin_id}")

# 验证可以通过逻辑ID找到坦克
found_p1 = next((t for t in world.tanks if t.tank_id == 1), None)
found_p2 = next((t for t in world.tanks if t.tank_id == 2), None)

assert found_p1 is not None, "P1 not found by logic ID!"
assert found_p2 is not None, "P2 not found by logic ID!"
assert found_p1.skin_id == 1, f"P1 skin_id mismatch: {found_p1.skin_id}"
assert found_p2.skin_id == 2, f"P2 skin_id mismatch: {found_p2.skin_id}"

print("✓ Tank ID and skin_id separation working correctly")

# 测试移动和动画
p2.move(Tank.UP)
p2.update()

print(f"P2 velocity after move: vx={p2.velocity_x}, vy={p2.velocity_y}")
print(f"P2 animation frame: {p2.animation_frame}")

assert p2.velocity_y != 0, "P2 should be moving!"

print("✓ Tank movement working")

pygame.quit()
print("\n所有测试通过！")
