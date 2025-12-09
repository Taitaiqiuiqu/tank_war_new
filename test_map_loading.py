import json
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath('.'))

from src.utils.map_loader import MapLoader

def test_map_loading():
    """测试新格式地图加载功能"""
    print("开始测试新格式地图加载功能...")
    
    # 创建MapLoader实例
    map_loader = MapLoader()
    
    # 获取maps目录下的所有地图文件
    maps_dir = "maps"
    if not os.path.exists(maps_dir):
        print("错误: maps目录不存在")
        return False
    
    map_files = [f for f in os.listdir(maps_dir) if f.endswith('.json')]
    if not map_files:
        print("错误: maps目录下没有地图文件")
        return False
    
    print(f"找到{len(map_files)}个地图文件，开始逐个加载测试...")
    
    success_count = 0
    failed_count = 0
    
    for map_file in map_files:
        # 直接使用文件名，因为MapLoader内部已经处理了maps目录
        print(f"\n测试加载地图: {map_file}")
        
        try:
            # 加载地图
            map_data = map_loader.load_map(map_file)
            
            # 验证加载结果
            if map_data:
                print(f"✓ 地图加载成功")
                print(f"  - 地图名称: {map_data.get('name', '未知')}")
                print(f"  - 墙体数量: {len(map_data.get('walls', []))}")
                print(f"  - 玩家出生点数量: {len(map_data.get('player_spawns', []))}")
                print(f"  - 敌人出生点数量: {len(map_data.get('enemy_spawns', []))}")
                success_count += 1
            else:
                print(f"✗ 地图加载失败: 返回None")
                failed_count += 1
                
        except Exception as e:
            print(f"✗ 地图加载出错: {str(e)}")
            failed_count += 1
    
    print(f"\n{'-'*50}")
    print(f"测试结果: 成功 {success_count} 个, 失败 {failed_count} 个")
    
    if failed_count == 0:
        print("🎉 所有地图加载测试通过！")
        return True
    else:
        print("❌ 部分地图加载失败")
        return False

if __name__ == "__main__":
    test_map_loading()
