"""
敌人AI难度配置系统
定义了4个难度等级的AI参数
"""

DIFFICULTY_CONFIGS = {
    "easy": {
        "name": "简单",
        "speed": 1.2,  # 降低速度，减少漂移
        "direction_interval": (28, 36),  # 略提速
        "shoot_interval": (40, 55),
        "tracking": False,
        "prediction": False,
        "dodge": False
    },
    "normal": {
        "name": "普通",
        "speed": 1.5,  # 降低速度
        "direction_interval": (22, 30),  # 决策更快
        "shoot_interval": (30, 45),
        "tracking": True,
        "tracking_prob": 0.7,
        "prediction": True,
        "prediction_frames": 10,
        "dodge": True,
        "dodge_prob": 0.45
    },
    "hard": {
        "name": "困难",
        "speed": 1.8,  # 降低速度
        "direction_interval": (16, 24),  # 更快决策
        "shoot_interval": (20, 32),     # 更快射击
        "tracking": True,
        "tracking_prob": 0.9,
        "prediction": True,
        "prediction_frames": 20,
        "dodge": True,
        "dodge_prob": 0.85,
        "safe_distance": 100
    },
    "hell": {
        "name": "地狱",
        "speed": 2.0,  # 降低速度
        "direction_interval": (10, 18),  # 极快决策
        "shoot_interval": (14, 24),     # 极快射击
        "tracking": True,
        "tracking_prob": 1.0,
        "prediction": True,
        "prediction_frames": 30,
        "dodge": True,
        "dodge_prob": 0.95,
        "safe_distance": 140,
        "team_coordination": True
    }
}

# 默认难度
DEFAULT_DIFFICULTY = "normal"

def get_difficulty_config(difficulty: str) -> dict:
    """获取难度配置"""
    return DIFFICULTY_CONFIGS.get(difficulty, DIFFICULTY_CONFIGS[DEFAULT_DIFFICULTY])

def get_difficulty_names() -> list:
    """获取所有难度名称（用于UI）"""
    return [config["name"] for config in DIFFICULTY_CONFIGS.values()]

def get_difficulty_key_by_name(name: str) -> str:
    """根据中文名称获取难度key"""
    for key, config in DIFFICULTY_CONFIGS.items():
        if config["name"] == name:
            return key
    return DEFAULT_DIFFICULTY
