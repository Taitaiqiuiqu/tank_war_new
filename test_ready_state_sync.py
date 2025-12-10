#!/usr/bin/env python3
"""
测试准备状态同步功能
"""

import sys
import os
import time
import threading

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from src.network.network_manager import NetworkManager

def test_ready_state_sync():
    """测试准备状态同步"""
    print("测试准备状态同步功能...")
    
    # 创建两个网络管理器，一个主机，一个客户端
    host_nm = NetworkManager()
    client_nm = NetworkManager()
    
    # 启动主机
    print("启动主机...")
    host_nm.start_host()
    time.sleep(0.5)
    
    # 客户端连接
    print("客户端连接...")
    client_nm.start_client()
    # 获取主机IP
    host_ip = "127.0.0.1"  # 本地测试
    client_nm.connect_to_server(host_ip)
    time.sleep(1.0)
    
    # 测试准备状态同步
    print("测试准备状态同步...")
    
    # 初始化标志
    client_received_ready = False
    host_received_ready = False
    
    # 主机发送准备状态
    print("主机发送准备状态: True")
    host_nm.send_ready_state(True)
    time.sleep(0.5)
    
    # 客户端检查消息
    events = client_nm.get_events()
    print(f"客户端收到的事件数量: {len(events)}")
    for event in events:
        print(f"客户端收到事件: {event}")
        if event.get("type") == "ready_state":
            print(f"客户端收到准备状态: {event.get('payload')}")
            client_received_ready = True
    
    if not client_received_ready:
        print("错误: 客户端未收到准备状态消息")
    
    # 客户端发送准备状态
    print("客户端发送准备状态: True")
    client_nm.send_ready_state(True)
    time.sleep(1.0)  # 增加等待时间
    
    # 主机检查消息
    msgs = host_nm.get_inputs()
    print(f"主机收到的消息数量: {len(msgs)}")
    for msg in msgs:
        print(f"主机收到消息: {msg}")
        if msg.get("type") == "ready_state":
            print(f"主机收到准备状态: {msg.get('payload')}")
            host_received_ready = True
    
    if not host_received_ready:
        print("错误: 主机未收到准备状态消息")
    
    # 等待一段时间再清理
    time.sleep(0.5)
    
    # 清理
    host_nm.stop()
    client_nm.stop()
    
    print("测试完成")

if __name__ == "__main__":
    test_ready_state_sync()