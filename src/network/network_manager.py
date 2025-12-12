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
        self._client_buffer = ""  # Buffer for client TCP data
        self.found_servers = [] # List of (ip, room_name)

    # ------------------------------------------------------------------ #
    # 生命周期
    # ------------------------------------------------------------------ #
    def start_host(self):
        """启动主机模式：TCP监听 + UDP广播响应"""
        if self._running: 
            print("[Network] Host already running")
            return
        self.stats.role = "host"
        self._running = True
        
        # TCP Server
        self._tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Allow address reuse
        self._tcp_socket.bind(('0.0.0.0', self.CONTROL_PORT))
        self._tcp_socket.listen(1)
        self._tcp_socket.settimeout(0.2)
        print(f"[Network] TCP server listening on port {self.CONTROL_PORT}")
        
        # UDP Listener (for discovery)
        self._udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self._udp_socket.bind(('0.0.0.0', self.BROADCAST_PORT))
        self._udp_socket.settimeout(0.5)  # Prevent blocking
        print(f"[Network] UDP listener bound on port {self.BROADCAST_PORT}")
        
        # Threads
        t_tcp = threading.Thread(target=self._host_tcp_accept_loop, daemon=True)
        t_udp = threading.Thread(target=self._host_udp_respond_loop, daemon=True)
        self._threads = [t_tcp, t_udp]
        for t in self._threads: t.start()
        print("[Network] Host started successfully")

    def start_client(self):
        """启动客户端模式：TCP连接 + UDP发现"""
        if self._running: return
        self.stats.role = "client"
        self._running = True
        
        # UDP Socket (for discovery)
        self._udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self._udp_socket.bind(('0.0.0.0', 0)) # Random port
        self._udp_socket.settimeout(0.5)  # Prevent blocking
        
        # Start discovery thread
        t_udp = threading.Thread(target=self._client_udp_listen_loop, daemon=True)
        self._threads = [t_udp]
        t_udp.start()
        print("[Network] Client started")

    def connect_to_server(self, server_ip: str) -> bool:
        """客户端连接到主机"""
        try:
            # Store host IP for potential reconnection
            self._last_host_ip = server_ip
            
            print(f"[Network] Attempting to connect to {server_ip}:{self.CONTROL_PORT}")
            
            # Create a new socket each time to avoid reusing closed sockets
            self._tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._tcp_socket.settimeout(5.0)  # Add timeout to prevent hanging
            
            self._tcp_socket.connect((server_ip, self.CONTROL_PORT))
            self._conn = self._tcp_socket
            self.stats.connected = True
            
            # Initialize last state time
            self._last_state_time = time.time()
            
            # Start receiving loop
            t_recv = threading.Thread(target=self._client_receiver_loop, daemon=True)
            t_recv.start()
            self._threads.append(t_recv)
            print(f"[Network] Successfully connected to {server_ip}")
            return True
        except socket.timeout:
            print(f"[Network] Connection timeout to {server_ip}:{self.CONTROL_PORT}")
            return False
        except ConnectionRefusedError:
            print(f"[Network] Connection refused by {server_ip}:{self.CONTROL_PORT}")
            return False
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
        
        # Reset state
        self.stats.role = "standalone"
        self.stats.connected = False
        self.found_servers.clear()
        
        # Clear queues
        while not self._incoming_state.empty():
            try: self._incoming_state.get_nowait()
            except: pass
        while not self._incoming_input.empty():
            try: self._incoming_input.get_nowait()
            except: pass
        while not self._event_queue.empty():
            try: self._event_queue.get_nowait()
            except: pass
            
        print("[Network] Stopped")

    # ------------------------------------------------------------------ #
    # API 给游戏层调用
    # ------------------------------------------------------------------ #
    def update(self):
        """在游戏循环中调用"""
        # Check for connection timeouts and attempt reconnection
        if self.stats.connected and self._conn:
            # Check if connection is still alive
            if self.stats.role == "client":
                # Client: Check if we're still receiving data from host
                current_time = time.time()
                if hasattr(self, '_last_state_time'):
                    # If no state received for more than 10 seconds, consider disconnected (increased from 5 to 10)
                    # This gives more tolerance for network delays
                    if current_time - self._last_state_time > 10.0:
                        print("[Network] Connection timeout - no data received from host")
                        self._handle_disconnect()
                else:
                    # Initialize timestamp
                    self._last_state_time = current_time
            elif self.stats.role == "host":
                # Host: Check if client is still responsive
                current_time = time.time()
                if hasattr(self, '_last_input_time'):
                    # If no input received for more than 10 seconds, consider disconnected (increased from 5 to 10)
                    # This gives more tolerance for network delays
                    # Note: Client may not send input every frame if not moving, so we also check for any activity
                    if current_time - self._last_input_time > 10.0:
                        print("[Network] Connection timeout - no input received from client")
                        self._handle_disconnect()
                else:
                    # Initialize timestamp
                    self._last_input_time = current_time
        
        # Attempt reconnection if disconnected
        if not self.stats.connected and hasattr(self, '_reconnect_attempt') and self._reconnect_attempt is not None:
            current_time = time.time()
            # Try to reconnect every 3 seconds
            if current_time - self._last_reconnect_time > 3.0:
                if self._reconnect_attempt < 5:  # Max 5 attempts
                    print(f"[Network] Attempting reconnection ({self._reconnect_attempt + 1}/5)")
                    self._attempt_reconnect()
                    self._reconnect_attempt += 1
                    self._last_reconnect_time = current_time
                else:
                    print("[Network] Max reconnection attempts reached")
                    self._reconnect_attempt = None
    
    def _handle_disconnect(self):
        """Handle disconnection without losing role/state for the game loop"""
        previous_role = self.stats.role  # Preserve role so host/client logic keeps running
        
        if self._conn:
            try:
                self._conn.close()
            except:
                pass
            self._conn = None
        
        self.stats.connected = False
        # Keep host/client role; avoid resetting to an invalid state that stops the game loop
        if previous_role in ("host", "client"):
            self.stats.role = previous_role
        
        # Only clients should attempt reconnection; hosts keep listening normally
        if previous_role == "client" and hasattr(self, "_last_host_ip"):
            self._reconnect_attempt = 0
            self._last_reconnect_time = time.time()
        else:
            # Remove reconnection state to avoid spurious attempts for host
            if hasattr(self, "_reconnect_attempt"):
                delattr(self, "_reconnect_attempt")
            if hasattr(self, "_last_reconnect_time"):
                delattr(self, "_last_reconnect_time")
        
        # Clear queues
        self._incoming_state.queue.clear()
        self._incoming_input.queue.clear()
        self._event_queue.queue.clear()
    
    def _attempt_reconnect(self):
        """Attempt to reconnect to the last host"""
        if hasattr(self, '_last_host_ip') and self._last_host_ip:
            try:
                # Create new TCP socket
                self._conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._conn.settimeout(3.0)  # 3 second timeout
                self._conn.connect((self._last_host_ip, self.CONTROL_PORT))
                
                # Start receiver thread
                self._receiver_thread = threading.Thread(target=self._client_receiver_loop, daemon=True)
                self._receiver_thread.start()
                
                self.stats.connected = True
                self.stats.role = "client"
                
                print(f"[Network] Successfully reconnected to host at {self._last_host_ip}")
                
                # Clear reconnection state
                self._reconnect_attempt = None
                
                # Add reconnection event to queue
                self._event_queue.put({"type": "reconnected", "payload": {}})
            except Exception as e:
                print(f"[Network] Reconnection failed: {e}")
                if self._conn:
                    try:
                        self._conn.close()
                    except:
                        pass
                    self._conn = None

    def send_state(self, payload: dict):
        """主机发送状态给客户端"""
        if self.stats.role == "host" and self.stats.connected and self._conn:
            self._send_json(self._conn, {"type": "state", "payload": payload})

    def send_input(self, input_data: dict):
        """客户端发送输入给主机"""
        if self.stats.role == "client" and self.stats.connected and self._conn:
            self._send_json(self._conn, {"type": "input", "payload": input_data})

    def send_lobby_update(self, tank_id: int):
        """发送大厅更新（如坦克选择）"""
        if self.stats.connected and self._conn:
            role = "Host" if self.stats.role == "host" else "Client"
            print(f"[Network] {role} 发送坦克选择更新: tank_id={tank_id}")
            self._send_json(self._conn, {"type": "lobby_update", "payload": {"tank_id": tank_id}})
        else:
            role = "Host" if self.stats.role == "host" else "Client"
            print(f"[Network] {role} 无法发送坦克选择更新: connected={self.stats.connected}, conn={self._conn is not None}")

    def send_map_selection(self, map_name: str):
        """发送地图选择更新"""
        if self.stats.connected and self._conn:
            self._send_json(self._conn, {"type": "map_selection", "payload": {"map_name": map_name}})

    def send_ready_state(self, is_ready: bool):
        """发送准备状态"""
        if self.stats.connected and self._conn:
            self._send_json(self._conn, {"type": "ready_state", "payload": {"is_ready": is_ready}})

    def send_game_start(self, p1_tank_id: int, p2_tank_id: int, map_name: str = "default", 
                        map_data: dict = None, game_mode: str = "coop", level_number: int = None):
        """主机发送游戏开始信号（包含完整地图数据、游戏模式和关卡编号）"""
        if self.stats.role == "host" and self.stats.connected and self._conn:
            payload = {
                "p1_tank_id": p1_tank_id,
                "p2_tank_id": p2_tank_id,
                "map_name": map_name,
                "game_mode": game_mode
            }
            
            # Include map data if provided
            if map_data:
                payload["map_data"] = map_data
            
            # Include level number if provided
            if level_number is not None:
                payload["level_number"] = level_number
            
            self._send_json(self._conn, {
                "type": "game_start", 
                "payload": payload
            })

    def send_event(self, event_type: str, payload: dict):
        """通用事件发送方法"""
        if self.stats.connected and self._conn:
            self._send_json(self._conn, {
                "type": event_type, 
                "payload": payload
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
        if self.stats.role == "client" and self._udp_socket:
            msg = json.dumps({"type": "scan"}).encode('utf-8')
            # Try multiple broadcast addresses including common network configurations
            targets = ['<broadcast>', '255.255.255.255', '127.0.0.1']
            
            # Add local network broadcast addresses
            try:
                import socket
                # Get local IP addresses and their broadcast addresses
                hostname = socket.gethostname()
                local_ips = socket.gethostbyname_ex(hostname)[2]
                for ip in local_ips:
                    if ip.startswith('192.168.'):
                        # Class C private network
                        broadcast_ip = ip.rsplit('.', 1)[0] + '.255'
                        targets.append(broadcast_ip)
                    elif ip.startswith('10.'):
                        # Class A private network - simplified
                        broadcast_ip = '10.255.255.255'
                        targets.append(broadcast_ip)
                    elif ip.startswith('172.'):
                        # Class B private network - simplified
                        broadcast_ip = '172.31.255.255'
                        targets.append(broadcast_ip)
            except Exception as e:
                print(f"[Network] Error getting local IPs: {e}")
            
            # Remove duplicates while preserving order
            seen = set()
            unique_targets = [t for t in targets if not (t in seen or seen.add(t))]
            
            # Send to all targets with error handling
            success_count = 0
            for target in unique_targets:
                try:
                    self._udp_socket.sendto(msg, (target, self.BROADCAST_PORT))
                    success_count += 1
                except Exception as e:
                    # Only log for non-common errors to reduce spam
                    if "Network is unreachable" not in str(e) and "Permission denied" not in str(e):
                        print(f"[Network] Broadcast to {target} failed: {e}")
            
            # If all broadcasts failed, try to recreate socket
            if success_count == 0 and self._running:
                print("[Network] All broadcasts failed, attempting to recreate UDP socket")
                try:
                    if self._udp_socket:
                        self._udp_socket.close()
                    self._udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    self._udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                    self._udp_socket.bind(('0.0.0.0', 0))  # Random port
                    self._udp_socket.settimeout(0.5)
                    print("[Network] UDP socket recreated successfully")
                except Exception as e:
                    print(f"[Network] Failed to recreate UDP socket: {e}")

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
        """主机UDP广播响应线程"""
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
                    print(f"[Network] Responded to scan from {addr[0]}:{addr[1]}")
            except socket.timeout:
                pass
            except Exception as e:
                if self._running and getattr(e, 'winerror', 0) != 10054:
                    print(f"[Network] UDP Respond Error: {e}")

    def _client_udp_listen_loop(self):
        while self._running:
            try:
                data, addr = self._udp_socket.recvfrom(1024)
                msg = json.loads(data.decode('utf-8'))
                if msg.get("type") == "scan_response":
                    server_info = (addr[0], msg.get("room_name", "Unknown"))
                    if server_info not in self.found_servers:
                        self.found_servers.append(server_info)
            except socket.timeout:
                pass
            except Exception as e:
                if self._running and getattr(e, 'winerror', 0) != 10054:
                    print(f"[Network] UDP Listen Error: {e}")

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
                
                # Host: any incoming data counts as activity for timeout detection
                if self.stats.role == "host":
                    self._last_input_time = time.time()

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

    def _client_receiver_loop(self):
        """客户端接收消息线程"""
        while self._running and self._conn:
            try:
                data = self._conn.recv(4096)
                if not data:
                    print("[Network] Connection closed by host")
                    self._handle_disconnect()
                    break
                    
                buffer = data.decode('utf-8')
                self._client_buffer += buffer
                
                while '\n' in self._client_buffer:
                    line, self._client_buffer = self._client_buffer.split('\n', 1)
                    if not line:
                        continue
                        
                    try:
                        msg = json.loads(line)
                        msg_type = msg.get("type")
                        
                        # Update last state time for timeout detection (any message indicates connection is alive)
                        # This prevents false disconnections when host sends non-state messages
                        if hasattr(self, '_last_state_time'):
                            self._last_state_time = time.time()
                        else:
                            self._last_state_time = time.time()
                        
                        if msg_type == "state":
                            self._incoming_state.put(msg)
                        else:
                            # 所有非状态消息统一放入事件队列，避免大厅更新等被丢弃
                            self._event_queue.put(msg)
                    except json.JSONDecodeError:
                        continue
                        
            except socket.timeout:
                continue
            except Exception as e:
                if self._running:
                    print(f"[Network] Client receiver error: {e}")
                    self._handle_disconnect()
                break

    def _host_receiver_loop(self, conn: socket.socket):
        """主机接收消息线程"""
        while self._running and conn:
            try:
                data = conn.recv(4096)
                if not data:
                    print("[Network] Client disconnected")
                    self._handle_disconnect()
                    break
                    
                buffer = data.decode('utf-8')
                self._host_buffer += buffer
                
                while '\n' in self._host_buffer:
                    line, self._host_buffer = self._host_buffer.split('\n', 1)
                    if not line:
                        continue
                        
                    try:
                        msg = json.loads(line)
                        msg_type = msg.get("type")
                        
                        # Update last input time for timeout detection (any message indicates connection is alive)
                        # This prevents false disconnections when client sends non-input messages
                        if hasattr(self, '_last_input_time'):
                            self._last_input_time = time.time()
                        else:
                            self._last_input_time = time.time()
                        
                        if msg_type == "input":
                            self._incoming_input.put(msg)
                        elif msg_type in ("lobby_update", "map_selection", "ready_state"):
                            self._incoming_input.put(msg)
                    except json.JSONDecodeError:
                        continue
                        
            except socket.timeout:
                continue
            except Exception as e:
                if self._running:
                    print(f"[Network] Host receiver error: {e}")
                    self._handle_disconnect()
                break

    def _send_json(self, sock: socket.socket, data: dict):
        try:
            msg = json.dumps(data) + '\n'
            sock.sendall(msg.encode('utf-8'))
        except Exception as e:
            print(f"[Network] Send error: {e}")
            self.stats.connected = False


