#!/usr/bin/env python3
"""
全面测试在线模式数据传输功能
测试所有数据传输类型：游戏状态、输入、大厅更新、地图选择、准备状态、游戏开始信号
"""

import sys
import os
import time
import threading

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from src.network.network_manager import NetworkManager

def test_comprehensive_network_transmission():
    """全面测试在线模式数据传输功能"""
    print("=" * 60)
    print("全面测试在线模式数据传输功能")
    print("=" * 60)
    
    # 创建两个网络管理器，一个主机，一个客户端
    host_nm = NetworkManager()
    client_nm = NetworkManager()
    
    # 测试结果记录
    test_results = {
        "host_start": False,
        "client_start": False,
        "connection": False,
        "game_state_transmission": False,
        "input_transmission": False,
        "lobby_update_transmission": False,
        "map_selection_transmission": False,
        "ready_state_transmission": False,
        "game_start_transmission": False
    }
    
    try:
        # 启动主机
        print("\n1. 启动主机...")
        host_nm.start_host()
        time.sleep(0.5)
        test_results["host_start"] = True
        print("✓ 主机启动成功")
        
        # 客户端连接
        print("\n2. 启动客户端并连接...")
        client_nm.start_client()
        time.sleep(0.5)
        test_results["client_start"] = True
        
        # 连接到主机
        host_ip = "127.0.0.1"  # 本地测试
        connected = client_nm.connect_to_server(host_ip)
        time.sleep(1.0)
        
        if connected and client_nm.stats.connected:
            test_results["connection"] = True
            print("✓ 客户端连接成功")
        else:
            print("✗ 客户端连接失败")
            return test_results
        
        # 测试准备状态同步
        print("\n3. 测试准备状态同步...")
        
        # 主机发送准备状态
        host_nm.send_ready_state(True)
        time.sleep(0.5)
        
        # 客户端检查消息
        events = client_nm.get_events()
        ready_received = False
        for event in events:
            if event.get("type") == "ready_state":
                print(f"✓ 客户端收到准备状态: {event.get('payload')}")
                ready_received = True
                break
        
        if not ready_received:
            print("✗ 客户端未收到准备状态消息")
        
        # 客户端发送准备状态
        client_nm.send_ready_state(True)
        time.sleep(0.5)
        
        # 主机检查消息
        msgs = host_nm.get_inputs()
        ready_received_host = False
        for msg in msgs:
            if msg.get("type") == "ready_state":
                print(f"✓ 主机收到准备状态: {msg.get('payload')}")
                ready_received_host = True
                break
        
        if not ready_received_host:
            print("✗ 主机未收到准备状态消息")
        
        if ready_received and ready_received_host:
            test_results["ready_state_transmission"] = True
        
        # 测试大厅更新
        print("\n4. 测试大厅更新同步...")
        
        # 主机发送大厅更新
        host_nm.send_lobby_update(1)
        time.sleep(0.5)
        
        # 客户端检查消息
        events = client_nm.get_events()
        lobby_received = False
        for event in events:
            if event.get("type") == "lobby_update":
                print(f"✓ 客户端收到大厅更新: {event.get('payload')}")
                lobby_received = True
                break
        
        if not lobby_received:
            print("✗ 客户端未收到大厅更新消息")
        
        # 客户端发送大厅更新
        client_nm.send_lobby_update(2)
        time.sleep(0.5)
        
        # 主机检查消息
        msgs = host_nm.get_inputs()
        lobby_received_host = False
        for msg in msgs:
            if msg.get("type") == "lobby_update":
                print(f"✓ 主机收到大厅更新: {msg.get('payload')}")
                lobby_received_host = True
                break
        
        if not lobby_received_host:
            print("✗ 主机未收到大厅更新消息")
        
        if lobby_received and lobby_received_host:
            test_results["lobby_update_transmission"] = True
        
        # 测试地图选择
        print("\n5. 测试地图选择同步...")
        
        # 主机发送地图选择
        host_nm.send_map_selection("desert")
        time.sleep(0.5)
        
        # 客户端检查消息
        events = client_nm.get_events()
        map_received = False
        for event in events:
            if event.get("type") == "map_selection":
                print(f"✓ 客户端收到地图选择: {event.get('payload')}")
                map_received = True
                break
        
        if not map_received:
            print("✗ 客户端未收到地图选择消息")
        
        # 客户端发送地图选择
        client_nm.send_map_selection("forest")
        time.sleep(0.5)
        
        # 主机检查消息
        msgs = host_nm.get_inputs()
        map_received_host = False
        for msg in msgs:
            if msg.get("type") == "map_selection":
                print(f"✓ 主机收到地图选择: {msg.get('payload')}")
                map_received_host = True
                break
        
        if not map_received_host:
            print("✗ 主机未收到地图选择消息")
        
        if map_received and map_received_host:
            test_results["map_selection_transmission"] = True
        
        # 测试游戏状态传输
        print("\n6. 测试游戏状态传输...")
        
        # 主机发送游戏状态
        test_state = {
            "players": {
                "1": {"x": 100, "y": 100, "direction": "up", "health": 100},
                "2": {"x": 500, "y": 500, "direction": "down", "health": 100}
            },
            "enemies": [],
            "bullets": [],
            "time": 123.45,
            "score": 1000
        }
        
        host_nm.send_state(test_state)
        time.sleep(0.5)
        
        # 客户端检查游戏状态
        latest_state = client_nm.get_latest_state()
        if latest_state:
            print(f"✓ 客户端收到游戏状态: {list(latest_state.keys())}")
            if "players" in latest_state and "time" in latest_state and "score" in latest_state:
                test_results["game_state_transmission"] = True
                print("  ✓ 游戏状态包含所有必要字段")
        else:
            print("✗ 客户端未收到游戏状态")
        
        # 测试输入传输
        print("\n7. 测试输入传输...")
        
        # 客户端发送输入
        test_input = {
            "player_id": 2,
            "keys": {"up": True, "fire": True},
            "timestamp": time.time()
        }
        
        client_nm.send_input(test_input)
        time.sleep(0.5)
        
        # 主机检查输入
        inputs = host_nm.get_inputs()
        input_received = False
        for msg in inputs:
            if msg.get("type") == "input":
                print(f"✓ 主机收到输入: {msg.get('payload')}")
                input_received = True
                test_results["input_transmission"] = True
                break
        
        if not input_received:
            print("✗ 主机未收到输入")
        
        # 测试游戏开始信号
        print("\n8. 测试游戏开始信号...")
        
        # 主机发送游戏开始信号
        host_nm.send_game_start(
            p1_tank_id=1,
            p2_tank_id=2,
            map_name="desert",
            map_data={"width": 800, "height": 600, "walls": []},
            game_mode="coop",
            level_number=1
        )
        time.sleep(0.5)
        
        # 客户端检查游戏开始信号
        events = client_nm.get_events()
        game_start_received = False
        for event in events:
            if event.get("type") == "game_start":
                payload = event.get("payload")
                print(f"✓ 客户端收到游戏开始信号: {payload}")
                if all(key in payload for key in ["p1_tank_id", "p2_tank_id", "map_name", "game_mode"]):
                    test_results["game_start_transmission"] = True
                    print("  ✓ 游戏开始信号包含所有必要字段")
                game_start_received = True
                break
        
        if not game_start_received:
            print("✗ 客户端未收到游戏开始信号")
            
    except Exception as e:
        print(f"\n✗ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理资源
        print("\n9. 清理资源...")
        host_nm.stop()
        client_nm.stop()
        time.sleep(0.5)
        
        # 打印测试结果汇总
        print("\n" + "=" * 60)
        print("测试结果汇总")
        print("=" * 60)
        
        all_passed = True
        for test_name, passed in test_results.items():
            status = "✓" if passed else "✗"
            print(f"{status} {test_name.replace('_', ' ').title()}: {'通过' if passed else '失败'}")
            if not passed:
                all_passed = False
        
        print("\n" + "=" * 60)
        if all_passed:
            print("🎉 所有测试通过！在线模式数据传输功能正常工作")
        else:
            print("❌ 部分测试失败，请检查网络传输功能")
        print("=" * 60)
        
        return test_results

if __name__ == "__main__":
    test_comprehensive_network_transmission()
