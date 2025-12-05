"""
敌人AI难度配置系统
定义了4个难度等级的AI参数
"""

DIFFICULTY_CONFIGS = {
    "easy": {
        "name": "简单",
        "speed": 1.5,
        "direction_interval": (60, 150),  # 帧
        "shoot_interval": (120, 240),
        "tracking": False,
        "prediction": False,
        "dodge": False
    },
    "normal": {
        "name": "普通",
        "speed": 2.0,
        "direction_interval": (40, 100),
        "shoot_interval": (80, 160),
        "tracking": True,
        "tracking_prob": 0.7,
        "prediction": True,
        "prediction_frames": 10,
        "dodge": True,
        "dodge_prob": 0.3
    },
    "hard": {
        "name": "困难",
        "speed": 2.5,
        "direction_interval": (30, 70),
        "shoot_interval": (50, 100),
        "tracking": True,
        "tracking_prob": 0.9,
        "prediction": True,
        "prediction_frames": 20,
        "dodge": True,
        "dodge_prob": 0.7,
        "safe_distance": 100
    },
    "hell": {
        "name": "地狱",
        "speed": 3.0,
        "direction_interval": (20, 50),
        "shoot_interval": (30, 60),
        "tracking": True,
        "tracking_prob": 1.0,
        "prediction": True,
        "prediction_frames": 30,
        "dodge": True,
        "dodge_prob": 0.9,
        "safe_distance": 150,
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
