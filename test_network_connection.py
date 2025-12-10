#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单的网络连接测试脚本
用于验证修复后的网络管理器是否能正常工作
"""

import sys
import os
import time
import threading

# 添加项目根目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from src.network.network_manager import NetworkManager

def test_host_client():
    """测试主机-客户端连接"""
    print("=== 开始网络连接测试 ===")
    
    # 创建主机
    host = NetworkManager()
    host.start_host()
    print("主机已启动")
    
    # 等待主机完全启动
    time.sleep(1)
    
    # 创建客户端
    client = NetworkManager()
    client.start_client()
    print("客户端已启动")
    
    # 客户端发送广播
    client.broadcast_discovery()
    print("客户端发送广播")
    
    # 等待响应
    time.sleep(1)
    
    # 检查是否发现主机
    if client.found_servers:
        print(f"发现服务器: {client.found_servers}")
        server_ip = client.found_servers[0][0]
        
        # 尝试连接
        print(f"尝试连接到 {server_ip}")
        if client.connect_to_server(server_ip):
            print("连接成功!")
            
            # 等待一会儿让连接稳定
            time.sleep(1)
            
            # 检查连接状态
            print(f"主机连接状态: {host.stats.connected}")
            print(f"客户端连接状态: {client.stats.connected}")
            
            # 测试消息发送
            test_msg = {"type": "test", "data": "Hello from client"}
            client.send_input(test_msg)
            print("发送测试消息")
            
            time.sleep(0.5)
            
            # 关闭连接
            client.stop()
            host.stop()
            print("连接已关闭")
            return True
        else:
            print("连接失败!")
            client.stop()
            host.stop()
            return False
    else:
        print("未发现服务器")
        client.stop()
        host.stop()
        return False

if __name__ == "__main__":
    success = test_host_client()
    if success:
        print("\n=== 测试通过 ===")
    else:
        print("\n=== 测试失败 ===")
    sys.exit(0 if success else 1)