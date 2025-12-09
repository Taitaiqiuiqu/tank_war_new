#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
坦克大战地图生成工具
根据地图生成规则自动生成10个不同风格的地图
"""

import json
import random
import os
from typing import List, Dict, Tuple

class MapGenerator:
    """地图生成器"""
    
    def __init__(self):
        self.grid_size = 50
        self.map_width = 800
        self.map_height = 600
        self.grid_width = self.map_width // self.grid_size  # 16
        self.grid_height = self.map_height // self.grid_size  # 12
        
        # 基地位置（底部中间）
        self.base_x = self.grid_width // 2  # 8
        self.base_y = self.grid_height - 1  # 11
        
        # 玩家出生点
        self.player1_spawn = [self.base_x - 2, self.base_y]  # [6, 11]
        self.player2_spawn = [self.base_x + 2, self.base_y]  # [10, 11]
        
        # 墙体类型
        self.WALL_TYPES = {
            'BRICK': 1,      # 砖墙（可破坏）
            'STEEL': 2,      # 钢墙（不可破坏）
            'GRASS': 3,      # 草地（可隐藏坦克）
            'RIVER': 4,      # 河流（不可穿越）
            'BASE': 5        # 基地
        }
    
    def generate_base_protection(self) -> List[Dict]:
        """生成基地保护墙"""
        walls = []
        
        # 基地本身
        walls.append({
            "grid_x": self.base_x,
            "grid_y": self.base_y,
            "type": self.WALL_TYPES['BASE']
        })
        
        # 基地周围的砖墙保护
        protection_positions = [
            (self.base_x - 1, self.base_y),     # 左
            (self.base_x + 1, self.base_y),     # 右
            (self.base_x, self.base_y - 1),     # 上
            (self.base_x - 1, self.base_y - 1), # 左上
            (self.base_x + 1, self.base_y - 1), # 右上
        ]
        
        for x, y in protection_positions:
            if 0 <= x < self.grid_width and 0 <= y < self.grid_height:
                walls.append({
                    "grid_x": x,
                    "grid_y": y,
                    "type": self.WALL_TYPES['BRICK']
                })
        
        return walls
    
    def generate_enemy_spawns(self) -> List[List[int]]:
        """生成敌人出生点"""
        spawns = []
        
        # 顶部均匀分布的3个出生点
        spawn_positions = [
            [2, 0],           # 左上
            [self.base_x, 0], # 中上
            [self.grid_width - 3, 0]  # 右上
        ]
        
        for pos in spawn_positions:
            if 0 <= pos[0] < self.grid_width:
                spawns.append(pos)
        
        return spawns
    
    def generate_simple_map(self) -> Dict:
        """生成简单地图"""
        walls = self.generate_base_protection()
        
        # 添加一些简单的砖墙
        for i in range(8):
            x = random.randint(1, self.grid_width - 2)
            y = random.randint(3, self.grid_height - 4)
            if not self.is_occupied(x, y, walls):
                walls.append({
                    "grid_x": x,
                    "grid_y": y,
                    "type": self.WALL_TYPES['BRICK']
                })
        
        return self.create_map_data("简单地图", walls)
    
    def generate_defense_map(self) -> Dict:
        """生成防御地图"""
        walls = self.generate_base_protection()
        
        # 在基地前方建立防御工事
        defense_line = self.base_y - 3
        for x in range(self.grid_width):
            if x % 2 == 0 and abs(x - self.base_x) > 2:
                walls.append({
                    "grid_x": x,
                    "grid_y": defense_line,
                    "type": random.choice([self.WALL_TYPES['BRICK'], self.WALL_TYPES['STEEL']])
                })
        
        # 添加侧翼防御
        for y in range(defense_line, self.base_y):
            walls.append({
                "grid_x": 2,
                "grid_y": y,
                "type": self.WALL_TYPES['STEEL']
            })
            walls.append({
                "grid_x": self.grid_width - 3,
                "grid_y": y,
                "type": self.WALL_TYPES['STEEL']
            })
        
        return self.create_map_data("防御地图", walls)
    
    def generate_maze_map(self) -> Dict:
        """生成迷宫地图"""
        walls = self.generate_base_protection()
        
        # 创建迷宫结构
        for y in range(2, self.grid_height - 2):
            for x in range(1, self.grid_width - 1):
                if y % 2 == 0 and x % 2 == 0:
                    # 迷宫支柱
                    walls.append({
                        "grid_x": x,
                        "grid_y": y,
                        "type": self.WALL_TYPES['BRICK']
                    })
                elif random.random() < 0.3:
                    # 随机墙壁
                    if not self.is_occupied(x, y, walls):
                        walls.append({
                            "grid_x": x,
                            "grid_y": y,
                            "type": random.choice([self.WALL_TYPES['BRICK'], self.WALL_TYPES['STEEL']])
                        })
        
        return self.create_map_data("迷宫地图", walls)
    
    def generate_river_map(self) -> Dict:
        """生成河流地图"""
        walls = self.generate_base_protection()
        
        # 创建横向河流
        river_y = self.grid_height // 2
        for x in range(self.grid_width):
            if abs(x - self.base_x) > 1:  # 避开基地
                walls.append({
                    "grid_x": x,
                    "grid_y": river_y,
                    "type": self.WALL_TYPES['RIVER']
                })
        
        # 创建纵向河流
        river_x = self.grid_width // 3
        for y in range(1, river_y):
            walls.append({
                "grid_x": river_x,
                "grid_y": y,
                "type": self.WALL_TYPES['RIVER']
            })
        
        river_x2 = 2 * self.grid_width // 3
        for y in range(river_y + 1, self.grid_height - 1):
            walls.append({
                "grid_x": river_x2,
                "grid_y": y,
                "type": self.WALL_TYPES['RIVER']
            })
        
        return self.create_map_data("河流地图", walls)
    
    def generate_fortress_map(self) -> Dict:
        """生成堡垒地图"""
        walls = self.generate_base_protection()
        
        # 中心堡垒
        fortress_size = 2
        for dx in range(-fortress_size, fortress_size + 1):
            for dy in range(-fortress_size, fortress_size + 1):
                x = self.base_x + dx
                y = self.base_y - 4 + dy
                if 0 <= x < self.grid_width and 0 <= y < self.grid_height:
                    if dx == 0 and dy == 0:
                        continue  # 中心留空
                    walls.append({
                        "grid_x": x,
                        "grid_y": y,
                        "type": self.WALL_TYPES['STEEL']
                    })
        
        # 角落堡垒
        corners = [(2, 2), (self.grid_width - 3, 2), (2, self.grid_height - 4), (self.grid_width - 3, self.grid_height - 4)]
        for cx, cy in corners:
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    if dx == 0 and dy == 0:
                        continue
                    walls.append({
                        "grid_x": cx + dx,
                        "grid_y": cy + dy,
                        "type": self.WALL_TYPES['STEEL']
                    })
        
        return self.create_map_data("堡垒地图", walls)
    
    def generate_open_map(self) -> Dict:
        """生成开放地图"""
        walls = self.generate_base_protection()
        
        # 只在边缘添加少量掩体
        edge_positions = [
            (1, 3), (self.grid_width - 2, 3),
            (1, self.grid_height - 4), (self.grid_width - 2, self.grid_height - 4),
            (self.grid_width // 4, 2), (3 * self.grid_width // 4, 2)
        ]
        
        for x, y in edge_positions:
            walls.append({
                "grid_x": x,
                "grid_y": y,
                "type": self.WALL_TYPES['BRICK']
            })
        
        return self.create_map_data("开放地图", walls)
    
    def generate_symmetric_map(self) -> Dict:
        """生成对称地图"""
        walls = self.generate_base_protection()
        
        # 生成左半边，然后镜像到右半边
        for y in range(2, self.grid_height - 2):
            for x in range(1, self.base_x):
                if random.random() < 0.4:
                    if not self.is_occupied(x, y, walls):
                        wall_type = random.choice([self.WALL_TYPES['BRICK'], self.WALL_TYPES['STEEL'], self.WALL_TYPES['GRASS']])
                        walls.append({
                            "grid_x": x,
                            "grid_y": y,
                            "type": wall_type
                        })
                        
                        # 镜像到右半边
                        mirror_x = self.grid_width - 1 - x
                        if not self.is_occupied(mirror_x, y, walls):
                            walls.append({
                                "grid_x": mirror_x,
                                "grid_y": y,
                                "type": wall_type
                            })
        
        return self.create_map_data("对称地图", walls)
    
    def generate_island_map(self) -> Dict:
        """生成多岛地图"""
        walls = self.generate_base_protection()
        
        # 创建多个岛屿
        islands = [
            (3, 3, 2),  # (center_x, center_y, radius)
            (self.grid_width - 4, 3, 2),
            (3, self.grid_height - 4, 2),
            (self.grid_width - 4, self.grid_height - 4, 2),
            (self.base_x, self.grid_height // 2, 1)
        ]
        
        for cx, cy, radius in islands:
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    if abs(dx) + abs(dy) <= radius:
                        x = cx + dx
                        y = cy + dy
                        if 0 <= x < self.grid_width and 0 <= y < self.grid_height:
                            if not self.is_occupied(x, y, walls):
                                walls.append({
                                    "grid_x": x,
                                    "grid_y": y,
                                    "type": random.choice([self.WALL_TYPES['BRICK'], self.WALL_TYPES['GRASS']])
                                })
        
        return self.create_map_data("多岛地图", walls)
    
    def generate_challenge_map(self) -> Dict:
        """生成挑战地图"""
        walls = self.generate_base_protection()
        
        # 密集的钢墙防御
        for y in range(1, self.grid_height - 1):
            for x in range(1, self.grid_width - 1):
                if random.random() < 0.2:
                    if not self.is_occupied(x, y, walls):
                        # 70%概率钢墙，30%概率砖墙
                        wall_type = self.WALL_TYPES['STEEL'] if random.random() < 0.7 else self.WALL_TYPES['BRICK']
                        walls.append({
                            "grid_x": x,
                            "grid_y": y,
                            "type": wall_type
                        })
        
        # 添加草地作为战术掩体
        for _ in range(10):
            x = random.randint(1, self.grid_width - 2)
            y = random.randint(2, self.grid_height - 3)
            if not self.is_occupied(x, y, walls):
                walls.append({
                    "grid_x": x,
                    "grid_y": y,
                    "type": self.WALL_TYPES['GRASS']
                })
        
        return self.create_map_data("挑战地图", walls)
    
    def is_occupied(self, x: int, y: int, walls: List[Dict]) -> bool:
        """检查位置是否被占用"""
        for wall in walls:
            if wall["grid_x"] == x and wall["grid_y"] == y:
                return True
        
        # 检查是否与出生点冲突
        if [x, y] == self.player1_spawn or [x, y] == self.player2_spawn:
            return True
        
        enemy_spawns = self.generate_enemy_spawns()
        for spawn in enemy_spawns:
            if [x, y] == spawn:
                return True
        
        return False
    
    def create_map_data(self, name: str, walls: List[Dict]) -> Dict:
        """创建地图数据"""
        return {
            "name": name,
            "original_width": 1400,
            "original_height": 1050,
            "aspect_ratio": 1.3333333333333333,
            "grid_size": self.grid_size,
            "wall_grid_data": walls,
            "player_spawns_grid": [self.player1_spawn, self.player2_spawn],
            "enemy_spawns_grid": self.generate_enemy_spawns()
        }
    
    def generate_all_maps(self) -> List[Dict]:
        """生成所有地图"""
        maps = []
        
        # 生成10个不同风格的地图
        map_generators = [
            self.generate_simple_map,
            self.generate_defense_map,
            self.generate_maze_map,
            self.generate_river_map,
            self.generate_fortress_map,
            self.generate_open_map,
            self.generate_symmetric_map,
            self.generate_island_map,
            self.generate_challenge_map,
            self.generate_simple_map  # 再生成一个简单地图作为第10个
        ]
        
        for generator in map_generators:
            try:
                map_data = generator()
                maps.append(map_data)
                print(f"成功生成地图: {map_data['name']}")
            except Exception as e:
                print(f"生成地图失败: {e}")
        
        return maps
    
    def save_maps(self, maps: List[Dict], output_dir: str = "maps"):
        """保存地图到文件"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        for i, map_data in enumerate(maps):
            filename = f"generated_map_{i+1}.json"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(map_data, f, ensure_ascii=False, indent=2)
            
            print(f"地图已保存: {filepath}")

def main():
    """主函数"""
    print("开始生成坦克大战地图...")
    
    generator = MapGenerator()
    maps = generator.generate_all_maps()
    
    # 保存到maps目录
    output_dir = "d:\\1tank_war_my\\maps"
    generator.save_maps(maps, output_dir)
    
    print(f"\n地图生成完成！共生成 {len(maps)} 个地图")
    print("地图文件已保存到 maps 目录下")
    
    # 显示生成的地图信息
    print("\n生成的地图列表:")
    for i, map_data in enumerate(maps):
        wall_count = len(map_data["wall_grid_data"])
        print(f"{i+1}. {map_data['name']} - {wall_count} 个障碍物")

if __name__ == "__main__":
    main()