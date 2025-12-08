#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地图优化脚本 - 检查并优化所有地图文件，确保符合地图生成规则
"""

import json
import os
import sys

def analyze_map(map_file):
    """分析单个地图文件"""
    print(f"\n=== 分析地图: {map_file} ===")
    
    try:
        with open(map_file, 'r', encoding='utf-8') as f:
            map_data = json.load(f)
    except Exception as e:
        print(f"  错误: 无法加载地图文件 - {e}")
        return None
    
    # 检查基本字段
    required_fields = ['name', 'walls', 'player_spawns', 'enemy_spawns']
    for field in required_fields:
        if field not in map_data:
            print(f"  错误: 缺少必需字段 {field}")
            return None
    
    # 检查基地
    base_walls = [w for w in map_data['walls'] if w['type'] == 5]
    if len(base_walls) != 1:
        print(f"  错误: 基地数量不正确，应该有1个，实际有{len(base_walls)}个")
        return None
    
    base = base_walls[0]
    base_x, base_y = base['x'], base['y']
    print(f"  基地位置: ({base_x}, {base_y})")
    
    # 检查基地是否在最底下一行（假设墙高50）
    if 'height' in map_data:
        expected_base_y = map_data['height'] - 100  # 考虑到出生点在550，墙高50
        if abs(base_y - expected_base_y) > 10:
            print(f"  警告: 基地位置可能不在最底下一行，期望Y坐标: {expected_base_y}, 实际Y坐标: {base_y}")
    
    # 检查基地周围是否有砖墙（类型2）
    base_surroundings = [
        (base_x - 50, base_y),    # 左
        (base_x + 50, base_y),    # 右
        (base_x, base_y - 50),    # 上
        (base_x - 50, base_y - 50),  # 左上
        (base_x + 50, base_y - 50)   # 右上
    ]
    
    for (x, y) in base_surroundings:
        wall = next((w for w in map_data['walls'] if w['x'] == x and w['y'] == y and w['type'] == 2), None)
        if not wall:
            print(f"  警告: 基地周围缺少砖墙保护，位置: ({x}, {y})")
    
    # 检查玩家出生点
    player_spawns = map_data['player_spawns']
    if len(player_spawns) < 2:
        print(f"  警告: 玩家出生点数量不足，应该至少有2个，实际有{len(player_spawns)}个")
    
    # 检查第一个玩家出生点是否在基地左边两格
    expected_p1_x = base_x - 100
    expected_p1_y = base_y + 50
    if player_spawns and (abs(player_spawns[0][0] - expected_p1_x) > 10 or abs(player_spawns[0][1] - expected_p1_y) > 10):
        print(f"  警告: 第一个玩家出生点位置可能不正确，期望: ({expected_p1_x}, {expected_p1_y}), 实际: ({player_spawns[0][0]}, {player_spawns[0][1]})")
    
    # 检查第二个玩家出生点是否在基地右边两格
    expected_p2_x = base_x + 100
    expected_p2_y = base_y + 50
    if len(player_spawns) > 1 and (abs(player_spawns[1][0] - expected_p2_x) > 10 or abs(player_spawns[1][1] - expected_p2_y) > 10):
        print(f"  警告: 第二个玩家出生点位置可能不正确，期望: ({expected_p2_x}, {expected_p2_y}), 实际: ({player_spawns[1][0]}, {player_spawns[1][1]})")
    
    # 检查敌人出生点
    enemy_spawns = map_data['enemy_spawns']
    if len(enemy_spawns) < 3:
        print(f"  警告: 敌人出生点数量不足，应该至少有3个，实际有{len(enemy_spawns)}个")
    
    for i, (x, y) in enumerate(enemy_spawns):
        if y > 100:  # 假设敌人出生点应该在最上面一行（Y坐标在50左右）
            print(f"  警告: 敌人出生点 {i+1} 位置可能不在最上面一行，Y坐标: {y}")
    
    # 检查是否有重复的墙
    wall_positions = set()
    for wall in map_data['walls']:
        pos = (wall['x'], wall['y'])
        if pos in wall_positions:
            print(f"  警告: 墙位置重复: {pos}")
        wall_positions.add(pos)
    
    return map_data

def optimize_map(map_data):
    """优化地图数据"""
    if not map_data:
        return None
    
    print(f"\n=== 优化地图: {map_data['name']} ===")
    
    # 获取基地位置
    base = next(w for w in map_data['walls'] if w['type'] == 5)
    base_x, base_y = base['x'], base['y']
    
    # 确保基地周围有砖墙
    base_surroundings = [
        (base_x - 50, base_y, 2),    # 左
        (base_x + 50, base_y, 2),    # 右
        (base_x, base_y - 50, 2),    # 上
        (base_x - 50, base_y - 50, 2),  # 左上
        (base_x + 50, base_y - 50, 2)   # 右上
    ]
    
    # 创建现有墙位置的集合
    existing_walls = set((w['x'], w['y']) for w in map_data['walls'])
    
    # 添加缺失的砖墙
    for (x, y, wall_type) in base_surroundings:
        if (x, y) not in existing_walls:
            new_wall = {'x': x, 'y': y, 'type': wall_type}
            map_data['walls'].append(new_wall)
            existing_walls.add((x, y))
            print(f"  添加了砖墙保护: ({x}, {y})")
    
    # 确保玩家出生点正确
    if 'height' in map_data:
        spawn_y = map_data['height'] - 50  # 玩家出生点应该在地图最底部
    else:
        spawn_y = 550  # 默认值
    
    expected_p1 = [base_x - 100, spawn_y]
    expected_p2 = [base_x + 100, spawn_y]
    
    # 更新或添加玩家出生点
    if len(map_data['player_spawns']) < 2:
        map_data['player_spawns'] = [expected_p1, expected_p2]
        print(f"  设置了玩家出生点: {expected_p1}, {expected_p2}")
    else:
        map_data['player_spawns'][0] = expected_p1
        map_data['player_spawns'][1] = expected_p2
        print(f"  更新了玩家出生点: {expected_p1}, {expected_p2}")
    
    # 确保敌人出生点在最上面一行
    if 'height' in map_data:
        spawn_y = 50  # 敌人出生点应该在地图最顶部
    else:
        spawn_y = 50  # 默认值
    
    # 如果没有敌人出生点，添加3个
    if len(map_data['enemy_spawns']) == 0:
        if 'width' in map_data:
            map_data['enemy_spawns'] = [
                [100, spawn_y],
                [map_data['width'] // 2, spawn_y],
                [map_data['width'] - 100, spawn_y]
            ]
        else:
            map_data['enemy_spawns'] = [
                [100, spawn_y],
                [400, spawn_y],
                [700, spawn_y]
            ]
        print(f"  添加了敌人出生点: {map_data['enemy_spawns']}")
    else:
        # 更新所有敌人出生点的Y坐标
        for i, spawn in enumerate(map_data['enemy_spawns']):
            map_data['enemy_spawns'][i][1] = spawn_y
        print(f"  更新了敌人出生点的Y坐标为: {spawn_y}")
    
    # 确保地图尺寸正确
    if 'width' not in map_data:
        map_data['width'] = 800
    if 'height' not in map_data:
        map_data['height'] = 600
    
    # 移除重复的墙
    unique_walls = []
    seen_positions = set()
    for wall in map_data['walls']:
        pos = (wall['x'], wall['y'])
        if pos not in seen_positions:
            unique_walls.append(wall)
            seen_positions.add(pos)
    
    if len(unique_walls) < len(map_data['walls']):
        removed = len(map_data['walls']) - len(unique_walls)
        map_data['walls'] = unique_walls
        print(f"  移除了 {removed} 个重复的墙")
    
    return map_data

def main():
    """主函数"""
    maps_dir = "maps"
    
    if not os.path.exists(maps_dir):
        print(f"错误: 地图目录 {maps_dir} 不存在")
        sys.exit(1)
    
    # 获取所有地图文件
    map_files = [f for f in os.listdir(maps_dir) if f.endswith('.json')]
    
    if not map_files:
        print("没有找到地图文件")
        sys.exit(1)
    
    print(f"找到 {len(map_files)} 个地图文件")
    
    for map_file in map_files:
        map_path = os.path.join(maps_dir, map_file)
        
        # 分析地图
        map_data = analyze_map(map_path)
        
        if map_data:
            # 优化地图
            optimized_data = optimize_map(map_data)
            
            if optimized_data:
                # 保存优化后的地图
                with open(map_path, 'w', encoding='utf-8') as f:
                    json.dump(optimized_data, f, ensure_ascii=False, indent=4)
                print(f"  地图已优化并保存: {map_file}")
    
    print("\n=== 所有地图优化完成 ===")

if __name__ == "__main__":
    main()