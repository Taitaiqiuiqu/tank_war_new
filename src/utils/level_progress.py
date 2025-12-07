import json
import os
from pathlib import Path

# 关卡进度文件路径
PROGRESS_FILE = "level_progress.json"

# 默认进度配置
DEFAULT_PROGRESS = {
    "unlocked_levels": [1],  # 默认只解锁第一关
    "max_level": 10  # 最大关卡数
}


def get_progress_file_path():
    """获取进度文件的完整路径"""
    # 确保配置目录存在
    config_dir = Path(__file__).parent.parent / "config"
    config_dir.mkdir(exist_ok=True)
    return str(config_dir / PROGRESS_FILE)


def load_level_progress():
    """加载关卡进度"""
    file_path = get_progress_file_path()
    
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                progress = json.load(f)
                # 验证进度数据的完整性
                if "unlocked_levels" not in progress:
                    progress["unlocked_levels"] = DEFAULT_PROGRESS["unlocked_levels"]
                if "max_level" not in progress:
                    progress["max_level"] = DEFAULT_PROGRESS["max_level"]
                return progress
        except (json.JSONDecodeError, IOError) as e:
            print(f"加载关卡进度失败: {e}")
    
    # 返回默认进度
    return DEFAULT_PROGRESS.copy()


def save_level_progress(progress):
    """保存关卡进度"""
    file_path = get_progress_file_path()
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(progress, f, ensure_ascii=False, indent=4)
        return True
    except IOError as e:
        print(f"保存关卡进度失败: {e}")
        return False


def unlock_next_level(current_level):
    """解锁下一关"""
    progress = load_level_progress()
    
    # 检查当前关卡是否已经完成
    if current_level in progress["unlocked_levels"]:
        next_level = current_level + 1
        if next_level <= progress["max_level"] and next_level not in progress["unlocked_levels"]:
            progress["unlocked_levels"].append(next_level)
            save_level_progress(progress)
            print(f"关卡 {next_level} 已解锁！")
            return True
    
    return False


def is_level_unlocked(level):
    """检查关卡是否已解锁"""
    progress = load_level_progress()
    return level in progress["unlocked_levels"]


def reset_level_progress():
    """重置关卡进度"""
    return save_level_progress(DEFAULT_PROGRESS.copy())
