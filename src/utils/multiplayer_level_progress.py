"""
联机关卡进度管理器 - 确保联机模式的关卡状态与单机模式分离
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional

# 联机关卡进度文件路径
MULTIPLAYER_PROGRESS_FILE = "multiplayer_level_progress.json"

# 默认联机进度配置
DEFAULT_MULTIPLAYER_PROGRESS = {
    "unlocked_levels": [1],  # 默认只解锁第一关
    "max_level": 10,  # 最大关卡数
    "completed_levels": [],  # 已完成的关卡
    "best_scores": {}  # 各关卡最佳得分
}


def get_multiplayer_progress_file_path():
    """获取联机关卡进度文件的完整路径"""
    # 确保配置目录存在
    config_dir = Path(__file__).parent.parent / "config"
    config_dir.mkdir(exist_ok=True)
    return str(config_dir / MULTIPLAYER_PROGRESS_FILE)


def load_multiplayer_level_progress():
    """加载联机关卡进度"""
    file_path = get_multiplayer_progress_file_path()
    
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                progress = json.load(f)
                # 验证进度数据的完整性
                if "unlocked_levels" not in progress:
                    progress["unlocked_levels"] = DEFAULT_MULTIPLAYER_PROGRESS["unlocked_levels"]
                if "max_level" not in progress:
                    progress["max_level"] = DEFAULT_MULTIPLAYER_PROGRESS["max_level"]
                if "completed_levels" not in progress:
                    progress["completed_levels"] = DEFAULT_MULTIPLAYER_PROGRESS["completed_levels"]
                if "best_scores" not in progress:
                    progress["best_scores"] = DEFAULT_MULTIPLAYER_PROGRESS["best_scores"]
                return progress
        except (json.JSONDecodeError, IOError) as e:
            print(f"加载联机关卡进度失败: {e}")
    
    # 返回默认进度
    return DEFAULT_MULTIPLAYER_PROGRESS.copy()


def save_multiplayer_level_progress(progress):
    """保存联机关卡进度"""
    file_path = get_multiplayer_progress_file_path()
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(progress, f, ensure_ascii=False, indent=4)
        return True
    except IOError as e:
        print(f"保存联机关卡进度失败: {e}")
        return False


def unlock_next_multiplayer_level(current_level):
    """解锁下一关（联机模式）"""
    progress = load_multiplayer_level_progress()
    
    # 检查当前关卡是否已经完成
    if current_level in progress["unlocked_levels"]:
        next_level = current_level + 1
        if next_level <= progress["max_level"] and next_level not in progress["unlocked_levels"]:
            progress["unlocked_levels"].append(next_level)
            save_multiplayer_level_progress(progress)
            print(f"联机关卡 {next_level} 已解锁！")
            return True
    
    return False


def is_multiplayer_level_unlocked(level):
    """检查联机关卡是否已解锁"""
    progress = load_multiplayer_level_progress()
    return level in progress["unlocked_levels"]


def complete_multiplayer_level(level, score=None):
    """标记联机关卡已完成"""
    progress = load_multiplayer_level_progress()
    
    # 添加到已完成关卡列表
    if level not in progress["completed_levels"]:
        progress["completed_levels"].append(level)
    
    # 更新最佳得分
    if score is not None:
        if str(level) not in progress["best_scores"] or score > progress["best_scores"][str(level)]:
            progress["best_scores"][str(level)] = score
    
    # 保存进度
    save_multiplayer_level_progress(progress)
    
    # 解锁下一关
    unlock_next_multiplayer_level(level)
    
    return True


def get_multiplayer_level_best_score(level):
    """获取联机关卡的最佳得分"""
    progress = load_multiplayer_level_progress()
    return progress["best_scores"].get(str(level), 0)


def is_multiplayer_level_completed(level):
    """检查联机关卡是否已完成"""
    progress = load_multiplayer_level_progress()
    return level in progress["completed_levels"]


def reset_multiplayer_level_progress():
    """重置联机关卡进度"""
    return save_multiplayer_level_progress(DEFAULT_MULTIPLAYER_PROGRESS.copy())


def get_multiplayer_progress_summary():
    """获取联机关卡进度摘要"""
    progress = load_multiplayer_level_progress()
    
    total_levels = progress["max_level"]
    unlocked_levels = len(progress["unlocked_levels"])
    completed_levels = len(progress["completed_levels"])
    
    return {
        "total_levels": total_levels,
        "unlocked_levels": unlocked_levels,
        "completed_levels": completed_levels,
        "completion_percentage": (completed_levels / total_levels) * 100,
        "current_level": max(progress["unlocked_levels"]) if progress["unlocked_levels"] else 0,
        "next_level": min(max(progress["unlocked_levels"]) + 1, total_levels) if progress["unlocked_levels"] else 1
    }


def get_available_multiplayer_levels():
    """获取所有可用的联机关卡列表"""
    progress = load_multiplayer_level_progress()
    
    levels = []
    for level in range(1, progress["max_level"] + 1):
        level_info = {
            "level": level,
            "unlocked": is_multiplayer_level_unlocked(level),
            "completed": is_multiplayer_level_completed(level),
            "best_score": get_multiplayer_level_best_score(level)
        }
        levels.append(level_info)
    
    return levels


def get_next_unlockable_multiplayer_level():
    """获取下一个可解锁的联机关卡"""
    progress = load_multiplayer_level_progress()
    
    # 找到第一个未解锁的关卡
    for level in range(1, progress["max_level"] + 1):
        if level not in progress["unlocked_levels"]:
            return level
    
    # 所有关卡都已解锁
    return None


def get_multiplayer_level_config(level):
    """获取联机关卡配置
    
    Args:
        level: 关卡编号
        
    Returns:
        dict: 关卡配置，包含敌人数量、类型等信息
    """
    # 这里可以根据关卡编号返回不同的配置
    # 目前使用简单的递增难度配置
    
    if level <= 0:
        return None
    
    # 基础配置
    config = {
        "level": level,
        "enemy_count": min(1 + (level - 1) // 2, 5),  # 每2关增加一个敌人，最多5个
        "enemy_types": ["enemy"],  # 默认敌人类型
        "enemy_difficulty": "normal",  # 默认难度
        "has_base": True,  # 是否有基地
        "time_limit": None,  # 时间限制（秒）
        "score_target": None,  # 目标得分
    }
    
    # 根据关卡调整配置
    if level >= 3:
        config["enemy_types"] = ["enemy", "fast_enemy"]
    if level >= 5:
        config["enemy_types"] = ["enemy", "fast_enemy", "heavy_enemy"]
        config["enemy_difficulty"] = "hard"
    if level >= 7:
        config["enemy_types"] = ["enemy", "fast_enemy", "heavy_enemy", "smart_enemy"]
        config["enemy_difficulty"] = "hell"
    
    # 特殊关卡配置
    if level == 2:
        config["enemy_count"] = 2
        config["enemy_types"] = ["enemy", "enemy"]
        config["time_limit"] = 180  # 3分钟时间限制
    elif level == 4:
        config["enemy_count"] = 3
        config["enemy_types"] = ["enemy", "fast_enemy", "fast_enemy"]
        config["time_limit"] = 240  # 4分钟时间限制
    elif level == 6:
        config["enemy_count"] = 4
        config["enemy_types"] = ["enemy", "fast_enemy", "heavy_enemy", "heavy_enemy"]
        config["time_limit"] = 300  # 5分钟时间限制
        config["score_target"] = 500  # 目标得分500
    elif level == 8:
        config["enemy_count"] = 5
        config["enemy_types"] = ["enemy", "fast_enemy", "heavy_enemy", "smart_enemy", "smart_enemy"]
        config["time_limit"] = 360  # 6分钟时间限制
        config["score_target"] = 800  # 目标得分800
    elif level == 10:
        config["enemy_count"] = 5
        config["enemy_types"] = ["enemy", "fast_enemy", "heavy_enemy", "smart_enemy", "smart_enemy"]
        config["enemy_difficulty"] = "hell"
        config["time_limit"] = 420  # 7分钟时间限制
        config["score_target"] = 1000  # 目标得分1000
        # 最终关卡
        config["enemy_count"] = 5
        config["enemy_types"] = ["fast_enemy", "heavy_enemy", "smart_enemy", "smart_enemy", "smart_enemy"]
        config["enemy_difficulty"] = "hell"
        config["time_limit"] = 300  # 5分钟时间限制
    
    return config