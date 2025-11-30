"""
调试脚本：打印客户端坦克的速度和动画状态
在 game.py 的客户端更新逻辑中添加调试输出
"""

# 在 src/game_engine/game.py 的第360行之后添加：
# if self.player_tank:
#     print(f"[Client] Tank vx={self.player_tank.velocity_x}, vy={self.player_tank.velocity_y}, is_moving={self.player_tank.is_moving}, frame={self.player_tank.animation_frame}")

# 这个脚本用于记录需要添加的调试代码
print("请在 src/game_engine/game.py 的第360行之后添加以下代码：")
print("""
                # Debug: Print tank state
                if self.player_tank:
                    print(f"[Client] vx={self.player_tank.velocity_x}, vy={self.player_tank.velocity_y}, moving={self.player_tank.is_moving}, frame={self.player_tank.animation_frame}")
""")
