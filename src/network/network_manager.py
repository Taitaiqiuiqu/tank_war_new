from __future__ import annotations

import json
import queue
import socket
import threading
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class NetworkStats:
    last_heartbeat: float = 0.0
    last_ping_ms: float = 0.0
    packets_sent: int = 0
    packets_received: int = 0
    connected: bool = False
    role: str = "standalone"  # "host" 或 "client"


class NetworkManager:
    """局域网通信占位实现，提供可扩展的线程框架。"""

    BROADCAST_PORT = 8888
    CONTROL_PORT = 8889
    BUFFER_SIZE = 4096

    def __init__(self):
        self.stats = NetworkStats()
        self._udp_socket: Optional[socket.socket] = None
        self._tcp_socket: Optional[socket.socket] = None
        self._conn: Optional[socket.socket] = None  # For Host: client connection; For Client: server connection
        self._threads: list[threading.Thread] = []
        self._running = False
        self._incoming_state = queue.Queue() # Queue for game state (from Host)
        self._incoming_input = queue.Queue() # Queue for input (from Client)
        self._event_queue = queue.Queue() # Queue for non-state events (for Client)
        self.found_servers = [] # List of (ip, room_name)

    # ------------------------------------------------------------------ #
    # 生命周期
    # ------------------------------------------------------------------ #
    def start_host(self):
        """启动主机模式：TCP监听 + UDP广播响应"""
        if self._running: return
        self.stats.role = "host"
        self._running = True
        
        # TCP Server
        self._tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._tcp_socket.bind(('0.0.0.0', self.CONTROL_PORT))
        self._tcp_socket.listen(1)
        self._tcp_socket.settimeout(0.2)
        
        # UDP Listener (for discovery)
        self._udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self._udp_socket.bind(('0.0.0.0', self.BROADCAST_PORT))
        
        # Threads
        t_tcp = threading.Thread(target=self._host_tcp_accept_loop, daemon=True)
        t_udp = threading.Thread(target=self._host_udp_respond_loop, daemon=True)
        self._threads = [t_tcp, t_udp]
        for t in self._threads: t.start()
        print("[Network] Host started")

    def start_client(self):
        """启动客户端模式：TCP连接 + UDP发现"""
        if self._running: return
        self.stats.role = "client"
        self._running = True
        
        # UDP Socket (for discovery)
        self._udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self._udp_socket.bind(('0.0.0.0', 0)) # Random port
        
        # Start discovery thread
        t_udp = threading.Thread(target=self._client_udp_listen_loop, daemon=True)
        self._threads = [t_udp]
        t_udp.start()
        print("[Network] Client started")

    def connect_to_server(self, server_ip: str) -> bool:
        """客户端连接到主机"""
        try:
            self._tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._tcp_socket.connect((server_ip, self.CONTROL_PORT))
            self._conn = self._tcp_socket
            self.stats.connected = True
            
            # Start receiving loop
            t_recv = threading.Thread(target=self._tcp_recv_loop, args=(self._conn, self._incoming_state), daemon=True)
            t_recv.start()
            self._threads.append(t_recv)
            print(f"[Network] Connected to {server_ip}")
            return True
        except Exception as e:
            print(f"[Network] Connection failed: {e}")
            return False

    def stop(self):
        self._running = False
        if self._conn:
            try: self._conn.close()
            except: pass
        if self._tcp_socket:
            try: self._tcp_socket.close()
            except: pass
        if self._udp_socket:
            try: self._udp_socket.close()
            except: pass
        self._conn = None
        self._tcp_socket = None
        self._udp_socket = None
        print("[Network] Stopped")

    # ------------------------------------------------------------------ #
    # API 给游戏层调用
    # ------------------------------------------------------------------ #
    def update(self):
        """在游戏循环中调用"""
        pass # 实际逻辑在线程中处理

    def send_state(self, payload: dict):
        """主机发送状态给客户端"""
        if self.stats.role == "host" and self.stats.connected and self._conn:
            self._send_json(self._conn, {"type": "state", "payload": payload})

    def send_input(self, input_data: dict):
        """客户端发送输入给主机"""
        if self.stats.role == "client" and self.stats.connected and self._conn:
            self._send_json(self._conn, {"type": "input", "payload": input_data})

    def send_lobby_update(self, tank_id: int):
        """客户端发送大厅更新（如坦克选择）"""
        if self.stats.role == "client" and self.stats.connected and self._conn:
            self._send_json(self._conn, {"type": "lobby_update", "payload": {"tank_id": tank_id}})

    def send_game_start(self, p1_tank_id: int, p2_tank_id: int):
        """主机发送游戏开始信号"""
        if self.stats.role == "host" and self.stats.connected and self._conn:
            self._send_json(self._conn, {
                "type": "game_start", 
                "payload": {
                    "p1_tank_id": p1_tank_id,
                    "p2_tank_id": p2_tank_id
                }
            })

    def get_latest_state(self) -> Optional[dict]:
        """客户端获取最新状态 (只取最新的，丢弃旧的，非状态消息移入事件队列)"""
        latest = None
        try:
            while True:
                msg = self._incoming_state.get_nowait()
                if msg.get("type") == "state":
                    latest = msg
                else:
                    self._event_queue.put(msg)
        except queue.Empty:
            pass
        return latest.get("payload") if latest else None

    def get_events(self) -> list[dict]:
        """客户端获取事件消息"""
        events = []
        try:
            while True:
                msg = self._event_queue.get_nowait()
                if msg:
                    events.append(msg)
        except queue.Empty:
            pass
        return events

    def get_inputs(self) -> list[dict]:
        """主机获取所有积压的消息 (Input + LobbyUpdate)"""
        messages = []
        try:
            while True:
                msg = self._incoming_input.get_nowait()
                if msg:
                    messages.append(msg)
        except queue.Empty:
            pass
        return messages

    def broadcast_discovery(self):
        """客户端发送发现广播"""
        if self._udp_socket:
            msg = json.dumps({"type": "scan"}).encode('utf-8')
            self._udp_socket.sendto(msg, ('<broadcast>', self.BROADCAST_PORT))

    # ------------------------------------------------------------------ #
    # 内部线程循环
    # ------------------------------------------------------------------ #
    def _host_tcp_accept_loop(self):
        print("[Network] Waiting for TCP connection...")
        while self._running:
            try:
                conn, addr = self._tcp_socket.accept()
                print(f"[Network] Accepted connection from {addr}")
                self._conn = conn
                self.stats.connected = True
                # Start receiving inputs from this client
                t_recv = threading.Thread(target=self._tcp_recv_loop, args=(conn, self._incoming_input), daemon=True)
                t_recv.start()
                self._threads.append(t_recv)
                break # Only support 1 client for now
            except socket.timeout:
                continue
            except Exception as e:
                if self._running: print(f"[Network] Accept error: {e}")
                break

    def _host_udp_respond_loop(self):
        while self._running:
            try:
                data, addr = self._udp_socket.recvfrom(1024)
                msg = json.loads(data.decode('utf-8'))
                if msg.get("type") == "scan":
                    response = json.dumps({
                        "type": "scan_response",
                        "room_name": f"Room {socket.gethostname()}",
                        "timestamp": time.time()
                    }).encode('utf-8')
                    self._udp_socket.sendto(response, addr)
            except Exception:
                pass

    def _client_udp_listen_loop(self):
        while self._running:
            try:
                data, addr = self._udp_socket.recvfrom(1024)
                msg = json.loads(data.decode('utf-8'))
                if msg.get("type") == "scan_response":
                    server_info = (addr[0], msg.get("room_name", "Unknown"))
                    if server_info not in self.found_servers:
                        self.found_servers.append(server_info)
            except Exception:
                pass

    def _tcp_recv_loop(self, sock: socket.socket, out_queue: queue.Queue):
        """通用TCP接收循环 (Line-delimited JSON)"""
        buffer = ""
        while self._running:
            try:
                data = sock.recv(4096)
                if not data:
                    print("[Network] Connection closed")
                    self.stats.connected = False
                    break
                
                buffer += data.decode('utf-8')
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if line.strip():
                        try:
                            msg = json.loads(line)
                            out_queue.put(msg)
                        except json.JSONDecodeError:
                            pass
            except Exception as e:
                if self._running: print(f"[Network] Recv error: {e}")
                self.stats.connected = False
                break

    def _send_json(self, sock: socket.socket, data: dict):
        try:
            msg = json.dumps(data) + '\n'
            sock.sendall(msg.encode('utf-8'))
        except Exception as e:
            print(f"[Network] Send error: {e}")
            self.stats.connected = False

