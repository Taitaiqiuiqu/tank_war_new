"""
关卡地图生成器 - 根据关卡规则自动生成地图数据
"""
import random
from typing import Dict, List, Tuple

from src.game_engine.wall import Wall


def generate_level_map(level: int, map_width: int = 800, map_height: int = 600) -> Dict[str, any]:
    """
    根据关卡生成地图数据
    
    Args:
        level: 当前关卡
        map_width: 地图宽度（像素）
        map_height: 地图高度（像素）
        
    Returns:
        地图数据字典
    """
    grid_size = 50  # 每个格子的大小
    cols = map_width // grid_size
    rows = map_height // grid_size
    
    walls = []
    
    # 计算基地位置（最底下一行中间）
    base_col = cols // 2
    base_row = rows - 1  # 最底下一行
    base_x = base_col * grid_size
    base_y = base_row * grid_size
    
    # 放置基地
    walls.append({
        "x": base_x,
        "y": base_y,
        "type": Wall.BASE
    })
    
    # 基地周围用砖墙包围（一圈）
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            if dx == 0 and dy == 0:
                continue  # 跳过基地位置
            
            col = base_col + dx
            row = base_row + dy
            
            # 确保在地图范围内
            if 0 <= col < cols and 0 <= row < rows:
                walls.append({
                    "x": col * grid_size,
                    "y": row * grid_size,
                    "type": Wall.BRICK
                })
    
    # 玩家出生点（基地左边两格和右边两格）
    player_spawns = [
        [base_x - 2 * grid_size, base_y],  # 左边两格
        [base_x + 2 * grid_size, base_y]   # 右边两格
    ]
    
    # 敌人出生点（最上面一行的随机位置）
    enemy_spawns = []
    for i in range(3):  # 生成3个敌人出生点
        col = random.randint(1, cols - 2)  # 避免太靠边
        enemy_spawns.append([col * grid_size, grid_size])  # 最上面一行
    
    # 根据关卡增加墙体数量和难度
    wall_count = min(30 + level * 5, 80)  # 随着关卡增加墙体数量，最多80个
    
    # 随机生成砖墙和钢墙
    placed_walls = 0
    max_attempts = 500  # 防止无限循环
    attempts = 0
    
    while placed_walls < wall_count and attempts < max_attempts:
        attempts += 1
        
        col = random.randint(0, cols - 1)
        row = random.randint(1, rows - 2)  # 避免最上面一行（敌人出生区域）和最下面两行（基地区域）
        
        # 跳过玩家和敌人出生点附近
        too_close = False
        for spawn in player_spawns + enemy_spawns:
            spawn_col = spawn[0] // grid_size
            spawn_row = spawn[1] // grid_size
            if abs(col - spawn_col) < 2 and abs(row - spawn_row) < 2:
                too_close = True
                break
        
        if too_close:
            continue
            
        # 跳过基地区域
        if abs(col - base_col) < 3 and abs(row - base_row) < 3:
            continue
        
        # 检查是否已经有墙体
        x = col * grid_size
        y = row * grid_size
        if any(w["x"] == x and w["y"] == y for w in walls):
            continue
        
        # 随机选择墙体类型（钢墙概率随关卡增加而增加）
        steel_probability = min(0.1 + level * 0.02, 0.3)  # 从10%到30%
        wall_type = Wall.STEEL if random.random() < steel_probability else Wall.BRICK
        
        walls.append({
            "x": x,
            "y": y,
            "type": wall_type
        })
        
        placed_walls += 1
    
    # 随机添加一些草地和河流
    # 草地概率较低
    grass_count = random.randint(3, 8)
    for _ in range(grass_count):
        col = random.randint(0, cols - 1)
        row = random.randint(1, rows - 2)
        
        x = col * grid_size
        y = row * grid_size
        if any(w["x"] == x and w["y"] == y for w in walls):
            continue
        
        walls.append({
            "x": x,
            "y": y,
            "type": Wall.GRASS
        })
    
    # 河流概率较低
    river_count = random.randint(1, 3)
    for _ in range(river_count):
        col = random.randint(0, cols - 1)
        row = random.randint(1, rows - 2)
        
        x = col * grid_size
        y = row * grid_size
        if any(w["x"] == x and w["y"] == y for w in walls):
            continue
        
        walls.append({
            "x": x,
            "y": y,
            "type": Wall.RIVER
        })
    
    # 生成地图数据
    map_data = {
        "name": f"关卡 {level}",
        "width": map_width,
        "height": map_height,
        "walls": walls,
        "player_spawns": player_spawns,
        "enemy_spawns": enemy_spawns
    }
    
    return map_data
