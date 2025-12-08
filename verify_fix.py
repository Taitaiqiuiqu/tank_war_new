#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
验证地图加载和游戏初始化修复的脚本
"""

import json
import os
from src.utils.map_loader import map_loader

# 测试地图加载
def test_map_loading():
    """测试地图加载功能"""
    print("=== 测试地图加载 ===")
    
    # 获取所有地图文件
    maps_dir = "maps"
    map_files = [f for f in os.listdir(maps_dir) if f.endswith('.json')]
    
    print(f"找到 {len(map_files)} 个地图文件")
    
    for map_file in map_files:
        map_name = map_file[:-5]  # 去除 .json 后缀
        print(f"\n测试加载地图: {map_name}")
        
        try:
            # 加载地图
            map_data = map_loader.load_map(map_name, 50)
            
            if map_data:
                print(f"  ✓ 地图加载成功")
                print(f"  - 地图名称: {map_data.get('name', map_name)}")
                print(f"  - 地图尺寸: {map_data.get('width', '未知')}x{map_data.get('height', '未知')}")
                
                # 检查玩家出生点
                player_spawns = map_data.get('player_spawns', [])
                if player_spawns:
                    print(f"  - 玩家出生点: {player_spawns}")
                else:
                    print(f"  - 玩家出生点: 未找到")
                
                # 检查敌人出生点
                enemy_spawns = map_data.get('enemy_spawns', [])
                if enemy_spawns:
                    print(f"  - 敌人出生点: {enemy_spawns}")
                else:
                    print(f"  - 敌人出生点: 未找到")
                
            else:
                print(f"  ✗ 地图加载失败")
                
        except Exception as e:
            print(f"  ✗ 地图加载出错: {e}")

# 测试特定地图
def test_specific_map(map_name):
    """测试特定地图的加载"""
    print(f"\n=== 测试特定地图: {map_name} ===")
    
    try:
        # 加载地图
        map_data = map_loader.load_map(map_name, 50)
        
        if map_data:
            print(f"✓ 地图加载成功")
            print(f"地图数据: {json.dumps(map_data, indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"✗ 地图加载失败")
            return False
            
    except Exception as e:
        print(f"✗ 地图加载出错: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # 运行所有测试
    test_map_loading()
    
    # 测试特定地图（可以替换为有问题的地图名称）
    test_specific_map("new_map")
