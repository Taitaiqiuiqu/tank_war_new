"""
联机模式地图生成工具 - 支持不同游戏模式的地图需求
"""
import json
import os
import random
from typing import Dict, List, Tuple, Optional
from src.utils.map_loader import MapLoader
from src.config.game_config import config


class MultiplayerMapGenerator:
    """联机模式地图生成器类"""
    
    def __init__(self, maps_dir="maps"):
        """初始化地图生成器"""
        self.maps_dir = maps_dir
        self.map_loader = MapLoader(maps_dir)
        self.grid_size = config.GRID_SIZE
        
        # 确保地图目录存在
        if not os.path.exists(self.maps_dir):
            os.makedirs(self.maps_dir)
        
        # 创建联机模式专用子目录
        self.multiplayer_dir = os.path.join(self.maps_dir, "multiplayer")
        if not os.path.exists(self.multiplayer_dir):
            os.makedirs(self.multiplayer_dir)
    
    def generate_pvp_map(self, map_name: str, width: int = 800, height: int = 600) -> Dict:
        """生成对战模式地图
        
        Args:
            map_name: 地图名称
            width: 地图宽度
            height: 地图高度
            
        Returns:
            dict: 生成的地图数据
        """
        # 计算网格尺寸
        grid_width = width // self.grid_size
        grid_height = height // self.grid_size
        
        # 初始化地图数据
        map_data = {
            "name": map_name,
            "original_width": width,
            "original_height": height,
            "aspect_ratio": width / height,
            "grid_size": self.grid_size,
            "wall_grid_data": [],
            "player_spawns_grid": [],
            "enemy_spawns_grid": [],  # 对战模式不需要敌人
            "base_grid": []  # 对战模式不需要基地
        }
        
        # 生成边界墙
        self._generate_border_walls(map_data, grid_width, grid_height)
        
        # 生成随机障碍物
        self._generate_random_obstacles(map_data, grid_width, grid_height, density=0.15)
        
        # 生成玩家出生点（对称分布）
        self._generate_pvp_spawns(map_data, grid_width, grid_height)
        
        # 保存地图
        self._save_multiplayer_map(map_data, "pvp")
        
        return map_data
    
    def generate_coop_map(self, map_name: str, width: int = 800, height: int = 600, 
                          difficulty: str = "normal") -> Dict:
        """生成合作模式地图
        
        Args:
            map_name: 地图名称
            width: 地图宽度
            height: 地图高度
            difficulty: 难度等级 (easy, normal, hard)
            
        Returns:
            dict: 生成的地图数据
        """
        # 计算网格尺寸
        grid_width = width // self.grid_size
        grid_height = height // self.grid_size
        
        # 根据难度调整参数
        difficulty_params = {
            "easy": {"obstacle_density": 0.1, "base_protection": 0.8},
            "normal": {"obstacle_density": 0.15, "base_protection": 0.6},
            "hard": {"obstacle_density": 0.2, "base_protection": 0.4}
        }
        
        params = difficulty_params.get(difficulty, difficulty_params["normal"])
        
        # 初始化地图数据
        map_data = {
            "name": map_name,
            "original_width": width,
            "original_height": height,
            "aspect_ratio": width / height,
            "grid_size": self.grid_size,
            "wall_grid_data": [],
            "player_spawns_grid": [],
            "enemy_spawns_grid": [],
            "base_grid": []
        }
        
        # 生成边界墙
        self._generate_border_walls(map_data, grid_width, grid_height)
        
        # 生成基地
        base_x, base_y = grid_width // 2, grid_height - 3
        map_data["base_grid"] = [base_x, base_y]
        map_data["wall_grid_data"].append({
            "grid_x": base_x,
            "grid_y": base_y,
            "type": "BASE"
        })
        
        # 生成基地保护墙
        self._generate_base_protection(map_data, base_x, base_y, params["base_protection"])
        
        # 生成随机障碍物
        self._generate_random_obstacles(map_data, grid_width, grid_height, 
                                       density=params["obstacle_density"],
                                       avoid_area=[(base_x, base_y, 3)])
        
        # 生成玩家出生点（靠近基地）
        map_data["player_spawns_grid"] = [
            [base_x - 2, base_y + 1],
            [base_x + 2, base_y + 1]
        ]
        
        # 生成敌人出生点（顶部区域）
        self._generate_enemy_spawns(map_data, grid_width, grid_height, count=3)
        
        # 保存地图
        self._save_multiplayer_map(map_data, "coop")
        
        return map_data
    
    def generate_mixed_map(self, map_name: str, width: int = 800, height: int = 600,
                         difficulty: str = "normal") -> Dict:
        """生成混战模式地图（PvP + AI敌人）
        
        Args:
            map_name: 地图名称
            width: 地图宽度
            height: 地图高度
            difficulty: 难度等级 (easy, normal, hard)
            
        Returns:
            dict: 生成的地图数据
        """
        # 计算网格尺寸
        grid_width = width // self.grid_size
        grid_height = height // self.grid_size
        
        # 根据难度调整参数
        difficulty_params = {
            "easy": {"obstacle_density": 0.12, "enemy_count": 2},
            "normal": {"obstacle_density": 0.15, "enemy_count": 3},
            "hard": {"obstacle_density": 0.18, "enemy_count": 4}
        }
        
        params = difficulty_params.get(difficulty, difficulty_params["normal"])
        
        # 初始化地图数据
        map_data = {
            "name": map_name,
            "original_width": width,
            "original_height": height,
            "aspect_ratio": width / height,
            "grid_size": self.grid_size,
            "wall_grid_data": [],
            "player_spawns_grid": [],
            "enemy_spawns_grid": [],
            "base_grid": []  # 混战模式通常不包含基地
        }
        
        # 生成边界墙
        self._generate_border_walls(map_data, grid_width, grid_height)
        
        # 生成随机障碍物
        self._generate_random_obstacles(map_data, grid_width, grid_height, 
                                       density=params["obstacle_density"])
        
        # 生成玩家出生点（对称分布）
        self._generate_pvp_spawns(map_data, grid_width, grid_height)
        
        # 生成敌人出生点（中部区域，避免靠近玩家出生点）
        self._generate_mixed_enemy_spawns(map_data, grid_width, grid_height, 
                                         count=params["enemy_count"])
        
        # 保存地图
        self._save_multiplayer_map(map_data, "mixed")
        
        return map_data
    
    def generate_level_map(self, level_number: int, width: int = 800, height: int = 600) -> Dict:
        """生成联机关卡模式地图
        
        Args:
            level_number: 关卡编号
            width: 地图宽度
            height: 地图高度
            
        Returns:
            dict: 生成的地图数据
        """
        # 计算网格尺寸
        grid_width = width // self.grid_size
        grid_height = height // self.grid_size
        
        # 根据关卡编号调整难度
        difficulty = min(1 + (level_number - 1) * 0.1, 2.0)  # 难度递增，最高2倍
        
        # 初始化地图数据
        map_data = {
            "name": f"联机关卡 {level_number}",
            "original_width": width,
            "original_height": height,
            "aspect_ratio": width / height,
            "grid_size": self.grid_size,
            "wall_grid_data": [],
            "player_spawns_grid": [],
            "enemy_spawns_grid": [],
            "base_grid": [],
            "level_number": level_number,
            "difficulty": difficulty
        }
        
        # 生成边界墙
        self._generate_border_walls(map_data, grid_width, grid_height)
        
        # 生成基地
        base_x, base_y = grid_width // 2, grid_height - 3
        map_data["base_grid"] = [base_x, base_y]
        map_data["wall_grid_data"].append({
            "grid_x": base_x,
            "grid_y": base_y,
            "type": "BASE"
        })
        
        # 生成基地保护墙
        protection_level = max(0.8 - (level_number - 1) * 0.05, 0.3)  # 随关卡减少保护
        self._generate_base_protection(map_data, base_x, base_y, protection_level)
        
        # 生成预设障碍物模式
        self._generate_level_obstacles(map_data, grid_width, grid_height, level_number)
        
        # 生成玩家出生点（靠近基地）
        map_data["player_spawns_grid"] = [
            [base_x - 2, base_y + 1],
            [base_x + 2, base_y + 1]
        ]
        
        # 生成敌人出生点（根据关卡增加数量）
        enemy_count = min(2 + (level_number - 1) // 2, 6)  # 每2关增加1个敌人，最多6个
        self._generate_enemy_spawns(map_data, grid_width, grid_height, count=enemy_count)
        
        # 保存地图
        self._save_multiplayer_map(map_data, "level")
        
        return map_data
    
    def _generate_border_walls(self, map_data: Dict, grid_width: int, grid_height: int):
        """生成边界墙"""
        wall_type = "STEEL"  # 使用钢墙作为边界
        
        # 上下边界
        for x in range(grid_width):
            map_data["wall_grid_data"].append({
                "grid_x": x,
                "grid_y": 0,
                "type": wall_type
            })
            map_data["wall_grid_data"].append({
                "grid_x": x,
                "grid_y": grid_height - 1,
                "type": wall_type
            })
        
        # 左右边界
        for y in range(1, grid_height - 1):
            map_data["wall_grid_data"].append({
                "grid_x": 0,
                "grid_y": y,
                "type": wall_type
            })
            map_data["wall_grid_data"].append({
                "grid_x": grid_width - 1,
                "grid_y": y,
                "type": wall_type
            })
    
    def _generate_random_obstacles(self, map_data: Dict, grid_width: int, grid_height: int,
                                  density: float = 0.15, avoid_area: List[Tuple] = None):
        """生成随机障碍物"""
        wall_types = ["BRICK", "STEEL"]
        avoid_area = avoid_area or []
        
        # 计算障碍物数量
        total_cells = (grid_width - 2) * (grid_height - 2)  # 减去边界
        obstacle_count = int(total_cells * density)
        
        # 生成随机位置
        positions = []
        for _ in range(obstacle_count):
            attempts = 0
            while attempts < 50:  # 最多尝试50次
                x = random.randint(1, grid_width - 2)
                y = random.randint(1, grid_height - 2)
                
                # 检查是否与现有障碍物重叠
                if (x, y) in positions:
                    attempts += 1
                    continue
                
                # 检查是否在避让区域内
                in_avoid_area = False
                for ax, ay, radius in avoid_area:
                    if abs(x - ax) <= radius and abs(y - ay) <= radius:
                        in_avoid_area = True
                        break
                
                if in_avoid_area:
                    attempts += 1
                    continue
                
                positions.append((x, y))
                break
        
        # 添加障碍物到地图数据
        for x, y in positions:
            wall_type = random.choice(wall_types)
            map_data["wall_grid_data"].append({
                "grid_x": x,
                "grid_y": y,
                "type": wall_type
            })
    
    def _generate_base_protection(self, map_data: Dict, base_x: int, base_y: int, 
                                 protection_level: float):
        """生成基地保护墙"""
        # 根据保护级别决定保护墙的完整性
        if protection_level >= 0.8:
            # 完全保护
            protection_positions = [
                (base_x - 1, base_y), (base_x + 1, base_y),
                (base_x, base_y - 1), (base_x - 1, base_y - 1), (base_x + 1, base_y - 1)
            ]
        elif protection_level >= 0.6:
            # 部分保护
            protection_positions = [
                (base_x - 1, base_y), (base_x + 1, base_y),
                (base_x, base_y - 1)
            ]
        elif protection_level >= 0.4:
            # 最小保护
            protection_positions = [
                (base_x - 1, base_y), (base_x + 1, base_y)
            ]
        else:
            # 无保护
            protection_positions = []
        
        # 添加保护墙
        for x, y in protection_positions:
            map_data["wall_grid_data"].append({
                "grid_x": x,
                "grid_y": y,
                "type": "BRICK"
            })
    
    def _generate_pvp_spawns(self, map_data: Dict, grid_width: int, grid_height: int):
        """生成对战模式玩家出生点"""
        # 左下角和右下角，对称分布
        margin = 2
        map_data["player_spawns_grid"] = [
            [margin, grid_height - margin - 1],
            [grid_width - margin - 1, grid_height - margin - 1]
        ]
    
    def _generate_enemy_spawns(self, map_data: Dict, grid_width: int, grid_height: int, 
                              count: int = 3):
        """生成敌人出生点"""
        # 在顶部区域均匀分布
        margin = 2
        spacing = (grid_width - 2 * margin) // (count + 1)
        
        for i in range(count):
            x = margin + spacing * (i + 1)
            y = margin
            map_data["enemy_spawns_grid"].append([x, y])
    
    def _generate_mixed_enemy_spawns(self, map_data: Dict, grid_width: int, grid_height: int,
                                    count: int = 3):
        """生成混战模式敌人出生点（避免靠近玩家出生点）"""
        # 在中部区域随机分布，但避开玩家出生区域
        player_spawn_areas = [
            (2, grid_height - 3, 3),  # 左下角玩家区域
            (grid_width - 5, grid_height - 3, 3)  # 右下角玩家区域
        ]
        
        positions = []
        for _ in range(count):
            attempts = 0
            while attempts < 50:
                x = random.randint(grid_width // 4, 3 * grid_width // 4)
                y = random.randint(grid_height // 4, 3 * grid_height // 4)
                
                # 检查是否与现有出生点重叠
                if (x, y) in positions:
                    attempts += 1
                    continue
                
                # 检查是否在玩家出生区域内
                in_player_area = False
                for px, py, radius in player_spawn_areas:
                    if abs(x - px) <= radius and abs(y - py) <= radius:
                        in_player_area = True
                        break
                
                if in_player_area:
                    attempts += 1
                    continue
                
                positions.append((x, y))
                break
        
        for x, y in positions:
            map_data["enemy_spawns_grid"].append([x, y])
    
    def _generate_level_obstacles(self, map_data: Dict, grid_width: int, grid_height: int,
                                 level_number: int):
        """生成关卡模式障碍物（根据关卡有不同的预设模式）"""
        # 根据关卡编号选择不同的预设模式
        pattern = (level_number - 1) % 5  # 5种基本模式循环
        
        if pattern == 0:
            # 模式1: 中心堡垒
            center_x, center_y = grid_width // 2, grid_height // 2
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    if abs(dx) == 2 or abs(dy) == 2:  # 只生成外围
                        map_data["wall_grid_data"].append({
                            "grid_x": center_x + dx,
                            "grid_y": center_y + dy,
                            "type": "STEEL" if (dx, dy) in [(0, -2), (0, 2), (-2, 0), (2, 0)] else "BRICK"
                        })
        
        elif pattern == 1:
            # 模式2: 对称迷宫
            for y in range(3, grid_height - 3, 2):
                for x in range(3, grid_width - 3):
                    if x % 4 == 0 or x % 4 == 1:
                        map_data["wall_grid_data"].append({
                            "grid_x": x,
                            "grid_y": y,
                            "type": "BRICK"
                        })
        
        elif pattern == 3:
            # 模式3: 之字形路径
            for y in range(3, grid_height - 3, 3):
                start_x = 3 if (y // 3) % 2 == 0 else grid_width - 4
                direction = 1 if (y // 3) % 2 == 0 else -1
                for x in range(0, grid_width - 6):
                    map_data["wall_grid_data"].append({
                        "grid_x": start_x + direction * x,
                        "grid_y": y,
                        "type": "BRICK"
                    })
        
        elif pattern == 4:
            # 模式4: 随机散布的钢墙
            steel_count = min(5 + level_number, 15)
            for _ in range(steel_count):
                x = random.randint(3, grid_width - 4)
                y = random.randint(3, grid_height - 4)
                map_data["wall_grid_data"].append({
                    "grid_x": x,
                    "grid_y": y,
                    "type": "STEEL"
                })
        
        # 默认模式2: 随机障碍物
        else:
            self._generate_random_obstacles(map_data, grid_width, grid_height, 
                                          density=0.1 + level_number * 0.02)
    
    def _save_multiplayer_map(self, map_data: Dict, game_mode: str):
        """保存联机模式地图"""
        # 创建模式特定的子目录
        mode_dir = os.path.join(self.multiplayer_dir, game_mode)
        if not os.path.exists(mode_dir):
            os.makedirs(mode_dir)
        
        # 生成文件名
        filename = f"{map_data['name']}.json"
        filepath = os.path.join(mode_dir, filename)
        
        # 保存地图
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(map_data, f, indent=2, ensure_ascii=False)
        
        print(f"已保存{game_mode}模式地图: {filepath}")
    
    def get_multiplayer_maps(self, game_mode: str) -> List[Dict]:
        """获取指定游戏模式的联机地图列表
        
        Args:
            game_mode: 游戏模式 (pvp, coop, mixed, level)
            
        Returns:
            list: 地图信息列表
        """
        mode_dir = os.path.join(self.multiplayer_dir, game_mode)
        if not os.path.exists(mode_dir):
            return []
        
        maps = []
        try:
            for filename in os.listdir(mode_dir):
                if filename.endswith(".json"):
                    filepath = os.path.join(mode_dir, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            map_data = json.load(f)
                        
                        map_info = {
                            "name": map_data.get("name", filename.replace(".json", "")),
                            "filename": filename,
                            "filepath": filepath,
                            "game_mode": game_mode,
                            "level_number": map_data.get("level_number"),
                            "difficulty": map_data.get("difficulty", "normal")
                        }
                        maps.append(map_info)
                    except Exception as e:
                        print(f"加载{game_mode}模式地图文件 {filename} 时出错: {e}")
        except Exception as e:
            print(f"获取{game_mode}模式地图列表时出错: {e}")
        
        return maps
    
    def load_multiplayer_map(self, game_mode: str, map_name: str) -> Optional[Dict]:
        """加载指定游戏模式的地图
        
        Args:
            game_mode: 游戏模式 (pvp, coop, mixed, level)
            map_name: 地图名称或文件名
            
        Returns:
            dict: 地图数据，如果加载失败则返回None
        """
        mode_dir = os.path.join(self.multiplayer_dir, game_mode)
        if not os.path.exists(mode_dir):
            return None
        
        # 查找地图文件
        map_filepath = None
        for filename in os.listdir(mode_dir):
            if filename.endswith(".json"):
                if filename == map_name or filename == f"{map_name}.json":
                    map_filepath = os.path.join(mode_dir, filename)
                    break
        
        if not map_filepath:
            return None
        
        try:
            with open(map_filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载{game_mode}模式地图 {map_name} 时出错: {e}")
            return None


# 创建全局联机地图生成器实例
multiplayer_map_generator = MultiplayerMapGenerator()