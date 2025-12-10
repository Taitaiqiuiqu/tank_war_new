"""
地图加载器 - 支持16:9屏幕比例和动态分辨率
"""
import os
import json
import pygame
from src.game_engine.wall import Wall
from src.config.game_config import config


class MapLoader:
    """地图加载器类 - 支持16:9屏幕比例和动态分辨率"""
    
    def __init__(self, maps_dir="maps"):
        """初始化地图加载器"""
        self.maps_dir = maps_dir
        self.maps = []
        
        # 确保地图目录存在
        if not os.path.exists(self.maps_dir):
            os.makedirs(self.maps_dir)
        
        # 获取可用地图列表
        self._load_maps_list()
    
    def _load_maps_list(self):
        """加载可用地图列表"""
        self.maps = []
        try:
            for filename in os.listdir(self.maps_dir):
                if filename.endswith(".json"):
                    filepath = os.path.join(self.maps_dir, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            map_data = json.load(f)
                        
                        # 获取地图基本信息
                        map_info = {
                            "name": map_data.get("name", filename.replace(".json", "")),
                            "filename": filename,
                            "filepath": filepath,
                            "original_width": map_data.get("original_width", 800),
                            "original_height": map_data.get("original_height", 600),
                            "aspect_ratio": map_data.get("aspect_ratio", 4/3),
                            "grid_size": map_data.get("grid_size", config.GRID_SIZE)
                        }
                        self.maps.append(map_info)
                        print(f"加载地图信息: {map_info['name']} ({map_info['original_width']}x{map_info['original_height']})")
                    except Exception as e:
                        print(f"加载地图文件 {filename} 时出错: {e}")
        except Exception as e:
            print(f"获取地图列表时出错: {e}")
    
    def get_available_maps(self):
        """获取所有可用地图的列表
        
        Returns:
            list: 包含地图信息的字典列表
        """
        # 重新加载地图列表以确保最新
        self._load_maps_list()
        return self.maps
    
    def load_map(self, map_name, target_grid_size=None):
        """加载指定名称的地图，并根据当前游戏尺寸进行适配
        
        Args:
            map_name: 地图名称或文件名
            target_grid_size: 目标网格大小（如果为None，则使用配置中的网格大小）
        
        Returns:
            dict: 包含地图数据的字典，支持16:9比例和自适应游戏窗口尺寸
        """
        if target_grid_size is None:
            target_grid_size = config.GRID_SIZE
        
        # 查找地图文件
        map_filepath = None
        for map_info in self.maps:
            if map_info["name"] == map_name or map_info["filename"] == map_name:
                map_filepath = map_info["filepath"]
                break
        
        # 如果没有找到，尝试直接构建文件路径
        if map_filepath is None:
            if not map_name.endswith(".json"):
                map_name += ".json"
            map_filepath = os.path.join(self.maps_dir, map_name)
        
        if not os.path.exists(map_filepath):
            print(f"地图文件不存在: {map_filepath}")
            
            # 如果是默认地图，返回硬编码的默认地图数据
            if map_name == "default" or map_filepath.endswith("default.json"):
                return self._get_default_map(target_grid_size)
            
            return None
        
        try:
            with open(map_filepath, 'r', encoding='utf-8') as f:
                map_data = json.load(f)
        except Exception as e:
            print(f"加载地图 {map_name} 时出错: {e}")
            return None
        
        # 只支持新格式（使用网格坐标）
        return self._load_new_format_map(map_data, target_grid_size)
    
    def _load_new_format_map(self, map_data, target_grid_size):
        """加载新格式地图（使用网格坐标）"""
        original_grid_size = map_data.get('grid_size', config.GRID_SIZE)
        original_width = map_data.get('original_width', 800)
        original_height = map_data.get('original_height', 600)
        
        # 确保原始尺寸至少为800x600
        if original_width < 800:
            original_width = 800
        if original_height < 600:
            original_height = 600
        
        # 墙体类型映射（字符串到数字）
        wall_type_map = {
            'background': 0,
            'brick': 1,
            'steel': 2,
            'grass': 3,
            'river': 4,
            'base': 5,
            # 大写版本支持
            'BACKGROUND': 0,
            'BRICK': 1,
            'STEEL': 2,
            'GRASS': 3,
            'RIVER': 4,
            'BASE': 5
        }
        
        # 转换墙体数据
        walls = []
        bases = []  # 基地列表
        if 'wall_grid_data' in map_data:
            for wall_grid in map_data['wall_grid_data']:
                # 直接使用目标网格大小转换为像素坐标
                x = wall_grid['grid_x'] * target_grid_size
                y = wall_grid['grid_y'] * target_grid_size
                wall_type_str = wall_grid['type']
                
                # 检查墙体类型是否已经是数字类型
                if isinstance(wall_type_str, (int, float)):
                    wall_type = int(wall_type_str)
                else:
                    # 将字符串类型转换为数字类型
                    wall_type = wall_type_map.get(wall_type_str, 1)  # 默认值为1（砖块）
                
                walls.append({
                    'x': x,
                    'y': y,
                    'type': wall_type
                })
                
                # 如果是基地，单独记录
                if wall_type == 5:  # 基地的数字类型是5
                    bases.append([x, y])
        
        # 转换玩家出生点
        player_spawns = []
        
        if 'player_spawns_grid' in map_data:
            for spawn_grid in map_data['player_spawns_grid']:
                x = spawn_grid[0] * target_grid_size
                y = spawn_grid[1] * target_grid_size
                player_spawns.append([x, y])
            print(f"[MapLoader] 从player_spawns_grid转换玩家出生点: {player_spawns}")
        else:
            # 默认出生点
            player_spawns = [[400, 550]]
            print(f"[MapLoader] 使用默认玩家出生点: {player_spawns}")
        
        # 转换敌人出生点
        enemy_spawns = []
        
        if 'enemy_spawns_grid' in map_data:
            for spawn_grid in map_data['enemy_spawns_grid']:
                x = spawn_grid[0] * target_grid_size
                y = spawn_grid[1] * target_grid_size
                enemy_spawns.append([x, y])
            print(f"[MapLoader] 从enemy_spawns_grid转换敌人出生点: {enemy_spawns}")
        else:
            # 默认出生点
            enemy_spawns = [[400, 50]]
            print(f"[MapLoader] 使用默认敌人出生点: {enemy_spawns}")
        
        # 处理基地
        if not bases and 'base_grid' in map_data:
            # 如果有单独的基地网格数据
            base_grid = map_data['base_grid']
            base_x = base_grid[0] * target_grid_size
            base_y = base_grid[1] * target_grid_size
            bases.append([base_x, base_y])
            # 将基地添加到墙体列表中
            walls.append({
                'x': base_x,
                'y': base_y,
                'type': 5
            })
        
        print(f"[MapLoader] 找到基地数量: {len(bases)}")
        
        # 原始尺寸（从文件加载）
        map_width = original_width
        map_height = original_height
        
        # 确保尺寸是网格大小的整数倍
        map_width = (map_width // target_grid_size) * target_grid_size
        map_height = (map_height // target_grid_size) * target_grid_size
        
        # 确保最小尺寸
        map_width = max(map_width, target_grid_size * 16)  # 最小16列
        map_height = max(map_height, target_grid_size * 12)  # 最小12行
        
        # 确保所有出生点都在地图范围内
        for spawn in player_spawns + enemy_spawns:
            if spawn[0] >= map_width:
                map_width = (spawn[0] // target_grid_size + 1) * target_grid_size
            if spawn[1] >= map_height:
                map_height = (spawn[1] // target_grid_size + 1) * target_grid_size
        
        # 创建最终的地图数据
        loaded_map = {
            "name": map_data.get("name", "unknown"),
            "width": map_width,
            "height": map_height,
            "original_width": original_width,
            "original_height": original_height,
            "aspect_ratio": original_width / original_height,
            "grid_size": target_grid_size,
            "walls": walls,
            "player_spawns": player_spawns,
            "enemy_spawns": enemy_spawns,
            "bases": bases,
            "wall_grid_data": map_data.get("wall_grid_data", []),
            "player_spawns_grid": map_data.get("player_spawns_grid", []),
            "enemy_spawns_grid": map_data.get("enemy_spawns_grid", []),
            "base_grid": map_data.get("base_grid", [])
        }
        
        print(f"成功加载地图 {loaded_map['name']}")
        print(f"地图尺寸: {loaded_map['width']}x{loaded_map['height']}, 网格大小: {loaded_map['grid_size']}px")
        print(f"墙体数量: {len(loaded_map['walls'])}, 玩家出生点: {len(loaded_map['player_spawns'])}, 敌人出生点: {len(loaded_map['enemy_spawns'])}, 基地数量: {len(loaded_map['bases'])}")
        
        return loaded_map
    
    def _get_default_map(self, target_grid_size):
        """返回默认的硬编码地图数据"""
        default_map = {
            "name": "默认地图",
            "walls": [],
            "player_spawns": [[400, 550]],
            "enemy_spawns": [[400, 50]],
            "grid_size": target_grid_size,
            "aspect_ratio": 16/9
        }
        
        # 添加一些基本墙体
        wall_positions = [
            # 中心区域
            (300, 200), (350, 200), (400, 200), (450, 200),
            (300, 250),                          (450, 250),
            (300, 300),                          (450, 300),
            (300, 350), (350, 350), (400, 350), (450, 350),
            
            # 周围墙体
            (100, 100), (150, 100), (200, 100), (250, 100),
            (100, 150),                                      (250, 150),
            (100, 200),                                      (250, 200),
            (100, 250),                                      (250, 250),
            (100, 300),                                      (250, 300),
            (100, 350), (150, 350), (200, 350), (250, 350),
            
            (600, 100), (650, 100), (700, 100), (750, 100),
            (600, 150),                                      (750, 150),
            (600, 200),                                      (750, 200),
            (600, 250),                                      (750, 250),
            (600, 300),                                      (750, 300),
            (600, 350), (650, 350), (700, 350), (750, 350),
            
            (100, 400), (150, 400), (200, 400), (250, 400),
            (100, 450),                                      (250, 450),
            (100, 500),                                      (250, 500),
            (100, 550), (150, 550), (200, 550), (250, 550),
            
            (600, 400), (650, 400), (700, 400), (750, 400),
            (600, 450),                                      (750, 450),
            (600, 500),                                      (750, 500),
            (600, 550), (650, 550), (700, 550), (750, 550)
        ]
        
        # 转换为目标网格大小
        scaled_walls = []
        for x, y in wall_positions:
            # 计算新的墙体位置，保持相对位置不变
            scaled_x = int(x * (target_grid_size / 50))
            scaled_y = int(y * (target_grid_size / 50))
            scaled_walls.append({"x": scaled_x, "y": scaled_y, "type": 1})
        
        default_map["walls"] = scaled_walls
        return default_map
    
    def get_map_display_name(self, filename):
        """获取地图的显示名称
        
        Args:
            filename: 地图文件名
        
        Returns:
            str: 地图的显示名称
        """
        try:
            filepath = os.path.join(self.maps_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                map_data = json.load(f)
                return map_data.get("name", filename.replace(".json", ""))
        except Exception as e:
            print(f"获取地图显示名称时出错: {e}")
            return filename.replace(".json", "")
    
    def add_map(self, map_data, filename=None):
        """添加新地图
        
        Args:
            map_data: 地图数据
            filename: 地图文件名（可选）
        
        Returns:
            bool: 是否添加成功
        """
        try:
            if filename is None:
                filename = f"{map_data.get('name', 'new_map')}.json"
            
            if not filename.endswith(".json"):
                filename += ".json"
            
            filepath = os.path.join(self.maps_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(map_data, f, indent=2, ensure_ascii=False)
            
            print(f"成功添加地图: {filename}")
            
            # 重新加载地图列表
            self._load_maps_list()
            
            return True
        except Exception as e:
            print(f"添加地图时出错: {e}")
            return False
    
    def delete_map(self, map_name):
        """删除指定名称的地图
        
        Args:
            map_name: 地图名称或文件名
        
        Returns:
            bool: 是否删除成功
        """
        try:
            # 查找地图文件
            map_filepath = None
            for map_info in self.maps:
                if map_info["name"] == map_name or map_info["filename"] == map_name:
                    map_filepath = map_info["filepath"]
                    break
            
            if not map_filepath:
                print(f"找不到地图: {map_name}")
                return False
            
            # 删除地图文件
            os.remove(map_filepath)
            print(f"成功删除地图: {map_name}")
            
            # 重新加载地图列表
            self._load_maps_list()
            
            return True
        except Exception as e:
            print(f"删除地图时出错: {e}")
            return False


# 创建全局地图加载器实例
map_loader = MapLoader()