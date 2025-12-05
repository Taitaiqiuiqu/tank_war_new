"""
修复地图文件中不对齐50px网格的坐标
"""
import json
import os
import glob

def fix_coordinate(coord):
    """将坐标对齐到50的倍数"""
    return (coord // 50) * 50

def fix_map_file(filepath):
    """修复单个地图文件"""
    print(f"\n检查文件: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    fixed = False
    
    # 修复墙体坐标
    if 'walls' in data:
        for wall in data['walls']:
            old_x, old_y = wall['x'], wall['y']
            new_x = fix_coordinate(old_x)
            new_y = fix_coordinate(old_y)
            
            if old_x != new_x or old_y != new_y:
                print(f"  修复墙体坐标: ({old_x}, {old_y}) -> ({new_x}, {new_y}), type={wall['type']}")
                wall['x'] = new_x
                wall['y'] = new_y
                fixed = True
    
    # 修复玩家出生点
    if 'player_spawns' in data:
        for i, spawn in enumerate(data['player_spawns']):
            old_x, old_y = spawn[0], spawn[1]
            new_x = fix_coordinate(old_x)
            new_y = fix_coordinate(old_y)
            
            if old_x != new_x or old_y != new_y:
                print(f"  修复玩家出生点 {i}: ({old_x}, {old_y}) -> ({new_x}, {new_y})")
                spawn[0] = new_x
                spawn[1] = new_y
                fixed = True
    
    # 修复敌人出生点
    if 'enemy_spawns' in data:
        for i, spawn in enumerate(data['enemy_spawns']):
            old_x, old_y = spawn[0], spawn[1]
            new_x = fix_coordinate(old_x)
            new_y = fix_coordinate(old_y)
            
            if old_x != new_x or old_y != new_y:
                print(f"  修复敌人出生点 {i}: ({old_x}, {old_y}) -> ({new_x}, {new_y})")
                spawn[0] = new_x
                spawn[1] = new_y
                fixed = True
    
    # 如果有修改，保存文件
    if fixed:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"  ✓ 已保存修复后的文件")
    else:
        print(f"  ✓ 文件坐标已对齐，无需修复")
    
    return fixed

def main():
    """修复所有地图文件"""
    maps_dir = "maps"
    map_files = glob.glob(os.path.join(maps_dir, "*.json"))
    
    print(f"找到 {len(map_files)} 个地图文件")
    
    fixed_count = 0
    for filepath in map_files:
        if fix_map_file(filepath):
            fixed_count += 1
    
    print(f"\n总计修复了 {fixed_count} 个文件")

if __name__ == "__main__":
    main()
