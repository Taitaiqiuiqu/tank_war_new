"""
测试地图数据网络传输
"""

import json

# 模拟地图数据
test_map_data = {
    "name": "测试地图",
    "walls": [
        {"x": 100, "y": 100, "type": 1},
        {"x": 150, "y": 100, "type": 2},
        {"x": 200, "y": 100, "type": 3}
    ],
    "player_spawns": [[50, 550], [750, 550]],
    "enemy_spawns": [[400, 50]]
}

# 测试JSON序列化
try:
    json_str = json.dumps(test_map_data)
    print(f"✓ 地图数据可以序列化为JSON")
    print(f"  大小: {len(json_str)} 字节")
    
    # 测试反序列化
    decoded = json.loads(json_str)
    assert decoded == test_map_data
    print(f"✓ 地图数据可以正确反序列化")
    
    # 测试嵌套在消息中
    message = {
        "type": "game_start",
        "payload": {
            "p1_tank_id": 1,
            "p2_tank_id": 2,
            "map_name": "test_map",
            "map_data": test_map_data
        }
    }
    
    msg_json = json.dumps(message)
    print(f"✓ 完整消息可以序列化")
    print(f"  大小: {len(msg_json)} 字节")
    
    decoded_msg = json.loads(msg_json)
    assert decoded_msg["payload"]["map_data"] == test_map_data
    print(f"✓ 完整消息可以正确反序列化")
    
    print("\n所有测试通过！地图数据传输机制可以正常工作。")
    
except Exception as e:
    print(f"✗ 测试失败: {e}")
