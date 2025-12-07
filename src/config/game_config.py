"""
游戏配置文件
集中管理所有游戏参数，避免魔法数字
"""


class GameConfig:
    """游戏配置类 - 高优先级参数"""
    
    # ========== 游戏对象尺寸 ==========
    
    # 坦克尺寸（像素）
    TANK_WIDTH = 30
    TANK_HEIGHT = 30
    
    # 墙体尺寸（像素）
    WALL_WIDTH = 50
    WALL_HEIGHT = 50
    
    # 子弹尺寸（像素）
    BULLET_WIDTH = 4
    BULLET_HEIGHT = 4
    
    # 地图网格尺寸（像素）
    GRID_SIZE = 50
    
    # ========== 速度参数 ==========
    
    # 坦克基础移动速度（像素/帧）
    TANK_BASE_SPEED = 2
    
    # 坦克升级后移动速度（像素/帧）
    TANK_UPGRADED_SPEED = 3
    
    # 子弹移动速度（像素/帧）
    BULLET_SPEED = 5
    
    # ========== 伤害和生命值 ==========
    
    # 子弹伤害值
    BULLET_DAMAGE = 50
    
    # 游戏对象默认生命值
    DEFAULT_HEALTH = 100
    
    # 墙体生命值
    WALL_HEALTH = 100
    
    # 坦克默认生命数
    TANK_DEFAULT_LIVES = 3
    
    # 手榴弹道具伤害（秒杀）
    GRENADE_DAMAGE = 1000
    
    # ========== 时间参数（帧数，60fps） ==========
    
    # 射击冷却时间（帧）
    SHOOT_COOLDOWN_BASE = 20
    
    # 升级后射击冷却时间（帧）
    SHOOT_COOLDOWN_UPGRADED = 15
    
    # 护盾持续时间（帧，10秒）
    SHIELD_DURATION = 600
    
    # 坦克重生倒计时（帧，3秒）
    RESPAWN_TIME = 90
    
    # 子弹生命周期（帧）
    BULLET_LIFETIME = 60
    
    # 冻结敌人道具持续时间（帧，10秒）
    FREEZE_ENEMIES_DURATION = 600
    
    # 基地强化道具持续时间（帧，20秒）
    FORTIFY_BASE_DURATION = 1200
    
    # 星星特效持续时间（帧）
    STAR_EFFECT_DURATION = 90
    
    # ========== 等级系统 ==========
    
    # 初始等级
    INITIAL_LEVEL = 0
    
    # 最大等级
    MAX_LEVEL = 3
    
    # 等级1阈值
    LEVEL_1_THRESHOLD = 1
    
    # 等级2阈值
    LEVEL_2_THRESHOLD = 2
    
    # 等级3阈值
    LEVEL_3_THRESHOLD = 3
    
    # ========== 道具系统 ==========
    
    # 敌人死亡掉落道具概率
    ENEMY_DROP_RATE = 1
    
    # 墙体破坏掉落道具概率
    WALL_DROP_RATE = 1
    
    # 道具类型最小值
    PROP_TYPE_MIN = 1
    
    # 道具类型最大值
    PROP_TYPE_MAX = 8
    
    # 道具尺寸（像素）
    PROP_WIDTH = 30
    PROP_HEIGHT = 30
    
    # ========== 窗口参数 ==========
    
    # 默认窗口宽度（像素） - 16:9比例
    DEFAULT_WINDOW_WIDTH = 1920
    
    # 默认窗口高度（像素） - 16:9比例
    DEFAULT_WINDOW_HEIGHT = 1080
    
    # 最小窗口宽度（像素） - 16:9比例
    MIN_WINDOW_WIDTH = 1280
    
    # 最小窗口高度（像素） - 16:9比例
    MIN_WINDOW_HEIGHT = 720
    
    # ========== 特效参数 ==========
    
    # 爆炸默认半径（像素）
    EXPLOSION_DEFAULT_RADIUS = 16
    
    # 爆炸默认持续时间（帧）
    EXPLOSION_DEFAULT_DURATION = 18
    
    # 坦克爆炸半径（像素）
    TANK_EXPLOSION_RADIUS = 28
    
    # 坦克爆炸持续时间（帧）
    TANK_EXPLOSION_DURATION = 24
    
    # 子弹爆炸半径（像素）
    BULLET_EXPLOSION_RADIUS = 12
    
    # 子弹爆炸持续时间（帧）
    BULLET_EXPLOSION_DURATION = 10
    
    # ========== 动画参数 ==========
    
    # 坦克动画切换速度（帧）
    TANK_ANIMATION_SPEED = 5
    
    # 护盾动画帧间隔（毫秒）
    SHIELD_ANIMATION_INTERVAL = 100
    
    # 星星动画帧间隔（帧）
    STAR_ANIMATION_INTERVAL = 5
    
    # ========== 子弹位置偏移 ==========
    
    # 子弹生成位置偏移（像素）
    BULLET_SPAWN_OFFSET = 2


# 创建全局配置实例（方便导入使用）
config = GameConfig()
