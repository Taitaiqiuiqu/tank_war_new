# 地图数据网络传输功能

## 功能说明

实现了通过网络传输地图数据的功能，使得客户端不需要本地拥有地图文件也能正常游戏。

## 工作原理

### 1. 主机端（Host）

当主机点击"开始游戏"时：

1. 加载选择的地图文件（如果不是默认地图）
2. 将完整的地图数据（墙体、生成点等）包含在 `game_start` 消息中
3. 通过TCP连接发送给客户端

```python
# 在 RoomScreen.handle_event 中
map_data = map_loader.load_map(self.selected_map)
self.network_manager.send_game_start(
    self.local_tank_id, 
    self.remote_tank_id, 
    self.selected_map, 
    map_data  # 完整的地图数据
)
```

### 2. 客户端（Client）

当客户端接收到 `game_start` 消息时：

1. 提取消息中的 `map_data` 字段
2. 将其保存到 `context.received_map_data`
3. 在初始化游戏世界时优先使用接收到的地图数据

```python
# 在 RoomScreen.update 中（客户端）
if "map_data" in payload:
    self.context.received_map_data = payload["map_data"]
    print(f"[Client] 接收到地图数据: {self.context.selected_map}")
```

### 3. 游戏世界初始化

`setup_multiplayer_world` 方法现在有两种加载地图的方式：

```python
# Priority 1: 使用从主机接收的地图数据（客户端）
if hasattr(self.screen_manager.context, 'received_map_data') and self.screen_manager.context.received_map_data:
    map_data = self.screen_manager.context.received_map_data
    
# Priority 2: 从本地文件加载（主机或本地有文件的客户端）
elif map_name != "default":
    map_data = map_loader.load_map(map_name)
```

## 消息格式

### game_start 消息

```json
{
  "type": "game_start",
  "payload": {
    "p1_tank_id": 1,
    "p2_tank_id": 2,
    "map_name": "test4",
    "map_data": {
      "name": "测试地图4",
      "walls": [
        {"x": 100, "y": 100, "type": 1},
        {"x": 150, "y": 100, "type": 2}
      ],
      "player_spawns": [[50, 550], [750, 550]],
      "enemy_spawns": [[400, 50]]
    }
  }
}
```

## 优势

1. **无需同步地图文件**：客户端不需要手动下载或复制地图文件
2. **即时游戏**：主机选择任何地图，客户端都能立即开始游戏
3. **版本一致性**：确保双方使用完全相同的地图数据，避免版本不一致问题
4. **简化部署**：新地图只需要在主机端添加，客户端自动获取

## 使用场景

### 场景1：客户端没有地图文件

- 主机选择 `test4` 地图
- 客户端本地没有 `test4.json` 文件
- 主机发送完整地图数据
- 客户端使用接收到的数据初始化游戏 ✓

### 场景2：客户端有地图文件

- 主机选择 `test4` 地图
- 客户端本地有 `test4.json` 文件
- 主机仍然发送地图数据
- 客户端优先使用接收到的数据（确保版本一致）✓

### 场景3：默认地图

- 主机选择默认地图
- 不发送 `map_data`（节省带宽）
- 双方使用硬编码的默认地图 ✓

## 性能考虑

- **数据大小**：典型地图数据约 500-2000 字节
- **传输时间**：在局域网中几乎瞬时完成
- **内存占用**：地图数据在 `context` 中临时存储，游戏开始后可以清理

## 测试

运行 `test_map_transmission.py` 验证JSON序列化和反序列化功能。

## 未来改进

1. 可以添加地图数据压缩（如果地图很大）
2. 可以添加地图数据校验和，确保传输完整性
3. 可以支持地图预览图片的传输
