# 道具8（船）测试说明

## 道具效果

**道具8 - 船**：
1. 允许坦克通过河流（type=4的墙体）
2. 在河上时显示河流护盾图片
3. 可以抵挡一次攻击（之后船消失）

## 测试步骤

### 方法1：使用现有地图
1. 选择有河流的地图（如 `river_crossing`）
2. 开始游戏
3. 按 `Ctrl+8` 生成船道具
4. 拾取道具
5. 尝试穿过河流 → 应该能通过
6. 在河上时应该看到河流护盾图片

### 方法2：创建测试地图
1. 进入地图编辑器
2. 按 `4` 键选择河流工具
3. 在地图上画一条河流
4. 保存地图
5. 开始游戏并选择该地图
6. 按 `Ctrl+8` 生成船道具测试

## 验证效果

### 没有船时
- ❌ 无法穿过河流（会被阻挡）
- ❌ 没有河流护盾显示

### 有船时
- ✅ 可以穿过河流
- ✅ 在河上时显示河流护盾图片（`river_shield.png`）
- ✅ 被攻击一次后船消失，恢复正常状态

## 代码逻辑

### 拾取道具
```python
# game_world.py:591-593
elif prop_type == 8: # 船 (水上行走)
    # 可过河，抵挡一次攻击
    player.enable_boat()
```

### 启用船
```python
# tank.py:314-317
def enable_boat(self):
    """启用船道具"""
    self.has_boat = True
    self.boat_shield_active = True
```

### 河流碰撞检测
```python
# wall.py:127-129
if self.wall_type == self.RIVER and getattr(other, 'has_boat', False):
    pass # 可以通过
```

### 渲染河流护盾
```python
# tank.py:176-179
if self.has_boat and self.is_on_river:
    river_shield_img = resource_manager.get_river_shield_image()
    if river_shield_img:
        screen.blit(river_shield_img, (self.x, self.y))
```

## 注意事项

1. **必须有河流**：地图中必须有 type=4 的墙体（河流）才能看到效果
2. **河流护盾只在河上显示**：离开河流后护盾图片消失，但 `has_boat` 仍然为 `True`
3. **抵挡攻击**：被攻击一次后，`has_boat` 和 `boat_shield_active` 都会变为 `False`

## 推荐测试地图

使用以下地图测试船道具：
- `river_crossing` - 专门设计的渡河地图
- 或自己在地图编辑器中创建包含河流的地图
