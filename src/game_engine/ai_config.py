"""
敌人AI难度配置系统
定义了4个难度等级的AI参数
"""

DIFFICULTY_CONFIGS = {
    "easy": {
        "name": "简单",
        "speed": 1.2,  # 降低速度，减少漂移
        "direction_interval": (30, 40),  # 0.5-0.67秒决策间隔 (30-40帧)
        "shoot_interval": (45, 60),     # 0.75-1秒射击间隔
        "tracking": False,
        "prediction": False,
        "dodge": False
    },
    "normal": {
        "name": "普通",
        "speed": 1.5,  # 降低速度
        "direction_interval": (25, 35),  # 0.42-0.58秒决策间隔
        "shoot_interval": (35, 50),     # 0.58-0.83秒射击间隔
        "tracking": True,
        "tracking_prob": 0.7,
        "prediction": True,
        "prediction_frames": 10,
        "dodge": True,
        "dodge_prob": 0.3
    },
    "hard": {
        "name": "困难",
        "speed": 1.8,  # 降低速度
        "direction_interval": (20, 30),  # 0.33-0.5秒决策间隔
        "shoot_interval": (25, 40),     # 0.42-0.67秒射击间隔
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
        "speed": 2.0,  # 降低速度
        "direction_interval": (15, 25),  # 0.25-0.42秒决策间隔
        "shoot_interval": (20, 30),     # 0.33-0.5秒射击间隔
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
