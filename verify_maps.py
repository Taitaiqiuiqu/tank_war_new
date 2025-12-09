import os
import json

# 检查单个地图是否存在重叠问题
def check_map_overlaps(map_file):
    print(f"\n检查地图: {map_file}")
    
    with open(map_file, 'r', encoding='utf-8') as f:
        map_data = json.load(f)
    
    # 提取地图数据
    wall_grid_data = map_data.get('wall_grid_data', [])
    player_spawns_grid = map_data.get('player_spawns_grid', [])
    enemy_spawns_grid = map_data.get('enemy_spawns_grid', [])
    
    # 检查墙体是否有重复
    wall_positions = set()
    duplicate_walls = 0
    for wall in wall_grid_data:
        pos = (wall['grid_x'], wall['grid_y'])
        if pos in wall_positions:
            duplicate_walls += 1
        else:
            wall_positions.add(pos)
    
    if duplicate_walls > 0:
        print(f"  警告: 发现 {duplicate_walls} 个重复墙体")
    else:
        print(f"  墙体无重复")
    
    # 检查玩家出生点是否与墙体重叠
    player_overlaps = 0
    for x, y in player_spawns_grid:
        pos = (x, y)
        if pos in wall_positions:
            player_overlaps += 1
            print(f"  警告: 玩家出生点 ({x}, {y}) 与墙体重叠")
    
    if player_overlaps == 0:
        print(f"  玩家出生点无重叠")
    
    # 检查敌人出生点是否与墙体重叠
    enemy_overlaps = 0
    for x, y in enemy_spawns_grid:
        pos = (x, y)
        if pos in wall_positions:
            enemy_overlaps += 1
            print(f"  警告: 敌人出生点 ({x}, {y}) 与墙体重叠")
    
    if enemy_overlaps == 0:
        print(f"  敌人出生点无重叠")
    
    # 检查玩家出生点之间是否重叠
    player_positions = set()
    player_self_overlaps = 0
    for x, y in player_spawns_grid:
        pos = (x, y)
        if pos in player_positions:
            player_self_overlaps += 1
            print(f"  警告: 玩家出生点 ({x}, {y}) 之间重叠")
        else:
            player_positions.add(pos)
    
    if player_self_overlaps == 0:
        print(f"  玩家出生点之间无重叠")
    
    # 检查敌人出生点之间是否重叠
    enemy_positions = set()
    enemy_self_overlaps = 0
    for x, y in enemy_spawns_grid:
        pos = (x, y)
        if pos in enemy_positions:
            enemy_self_overlaps += 1
            print(f"  警告: 敌人出生点 ({x}, {y}) 之间重叠")
        else:
            enemy_positions.add(pos)
    
    if enemy_self_overlaps == 0:
        print(f"  敌人出生点之间无重叠")
    
    # 检查玩家出生点和敌人出生点之间是否重叠
    player_enemy_overlaps = 0
    for x, y in player_spawns_grid:
        pos = (x, y)
        if pos in enemy_positions:
            player_enemy_overlaps += 1
            print(f"  警告: 玩家出生点 ({x}, {y}) 与敌人出生点重叠")
    
    if player_enemy_overlaps == 0:
        print(f"  玩家出生点与敌人出生点之间无重叠")
    
    # 检查基地是否存在
    has_base = False
    base_positions = []
    for wall in wall_grid_data:
        if wall['type'] == 5:  # BASE类型
            has_base = True
            base_positions.append((wall['grid_x'], wall['grid_y']))
    
    if has_base:
        print(f"  基地存在，位于位置: {base_positions}")
    else:
        print(f"  警告: 未找到基地")
    
    # 检查敌人出生点数量是否至少为3个
    if len(enemy_spawns_grid) < 3:
        print(f"  警告: 敌人出生点数量不足3个")
    else:
        print(f"  敌人出生点数量: {len(enemy_spawns_grid)} (符合要求)")
    
    # 返回是否有任何问题
    has_issues = duplicate_walls > 0 or player_overlaps > 0 or enemy_overlaps > 0 or \
                player_self_overlaps > 0 or enemy_self_overlaps > 0 or player_enemy_overlaps > 0 or \
                not has_base or len(enemy_spawns_grid) < 3
    
    return has_issues

# 检查所有地图
def check_all_maps():
    maps_dir = 'maps'
    
    if not os.path.exists(maps_dir):
        print(f"错误: 地图目录 {maps_dir} 不存在")
        return
    
    # 获取所有JSON地图文件
    map_files = [os.path.join(maps_dir, f) for f in os.listdir(maps_dir) if f.endswith('.json')]
    
    if not map_files:
        print(f"错误: 地图目录 {maps_dir} 中没有JSON文件")
        return
    
    print(f"共找到 {len(map_files)} 个地图文件")
    
    # 检查每个地图
    total_issues = 0
    for map_file in map_files:
        if check_map_overlaps(map_file):
            total_issues += 1
    
    print(f"\n{'='*50}")
    print(f"检查完成: {len(map_files)} 个地图，其中 {total_issues} 个存在问题")
    
    if total_issues == 0:
        print("所有地图均无重叠问题！")
    else:
        print("存在问题的地图需要进一步检查和修复。")

if __name__ == "__main__":
    check_all_maps()
