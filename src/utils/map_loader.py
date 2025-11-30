"""
地图加载器 - 从JSON文件加载自定义地图
"""
import json
import os
from typing import Optional, List, Dict, Any


class MapLoader:
    """地图加载器类"""
    
    def __init__(self, maps_dir: str = "maps"):
        """初始化地图加载器
        
        Args:
            maps_dir: 地图文件目录
        """
        self.maps_dir = maps_dir
        self.base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.maps_path = os.path.join(self.base_path, maps_dir)
    
    def get_available_maps(self) -> List[str]:
        """获取所有可用的地图名称
        
        Returns:
            地图名称列表（不含.json扩展名）
        """
        if not os.path.exists(self.maps_path):
            return []
        
        maps = []
        for filename in os.listdir(self.maps_path):
            if filename.endswith('.json'):
                maps.append(filename[:-5])  # 移除.json扩展名
        return sorted(maps)
    
    def load_map(self, map_name: str) -> Optional[Dict[str, Any]]:
        """加载指定地图
        
        Args:
            map_name: 地图名称（不含扩展名）
        
        Returns:
            地图数据字典，如果加载失败返回None
        """
        map_file = os.path.join(self.maps_path, f"{map_name}.json")
        
        if not os.path.exists(map_file):
            print(f"地图文件不存在: {map_file}")
            return None
        
        try:
            with open(map_file, 'r', encoding='utf-8') as f:
                map_data = json.load(f)
            
            # 验证必需字段
            required_fields = ['name', 'walls', 'player_spawns', 'enemy_spawns']
            for field in required_fields:
                if field not in map_data:
                    print(f"地图数据缺少必需字段: {field}")
                    return None
            
            return map_data
        except Exception as e:
            print(f"加载地图失败: {e}")
            return None
    
    def get_map_display_name(self, map_name: str) -> str:
        """获取地图的显示名称
        
        Args:
            map_name: 地图文件名（不含扩展名）
        
        Returns:
            地图的显示名称
        """
        map_data = self.load_map(map_name)
        if map_data and 'name' in map_data:
            return map_data['name']
        return map_name


# 全局地图加载器实例
map_loader = MapLoader()
