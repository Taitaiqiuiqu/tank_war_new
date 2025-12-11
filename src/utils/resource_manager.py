"""
资源管理器 - 统一管理游戏中的所有图片和音频资源
"""
import os
import pygame
from typing import Dict, List, Optional


class ResourceManager:
    """资源管理器单例类"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        
        # 图片缓存
        self.images: Dict[str, pygame.Surface] = {}
        self.tank_images: Dict[str, Dict[int, List[pygame.Surface]]] = {}
        self.explosion_frames: List[pygame.Surface] = []
        self.shield_frames: List[pygame.Surface] = []
        self.river_shield_image: Optional[pygame.Surface] = None
        self.star_frames: List[pygame.Surface] = []
        
        # 音频缓存
        self.sounds: Dict[str, pygame.mixer.Sound] = {}
        
        # 资源是否已加载
        self._resources_loaded = False
        self._preload_progress = 0.0  # 预加载进度 (0.0 - 1.0)
        self._preload_status = ""  # 预加载状态文本
        self._preload_total_steps = 7  # 总加载步骤数
        self._preload_current_step = 0  # 当前加载步骤
    
    def _ensure_resources_loaded(self):
        """确保资源已加载（延迟加载）"""
        if not self._resources_loaded:
            self._load_all_resources()
            self._resources_loaded = True
    
    def _load_all_resources(self):
        """加载所有游戏资源"""
        try:
            self._preload_current_step = 0
            self._preload_progress = 0.0
            self._preload_status = "加载墙体图片..."
            self._load_wall_images()
            self._preload_current_step = 1
            self._preload_progress = 1.0 / self._preload_total_steps
            
            self._preload_status = "加载子弹图片..."
            self._load_bullet_image()
            self._preload_current_step = 2
            self._preload_progress = 2.0 / self._preload_total_steps
            
            self._preload_status = "加载爆炸动画..."
            self._load_explosion_frames()
            self._preload_current_step = 3
            self._preload_progress = 3.0 / self._preload_total_steps
            
            self._preload_status = "加载护盾动画..."
            self._load_shield_frames()
            self._preload_current_step = 4
            self._preload_progress = 4.0 / self._preload_total_steps
            
            self._preload_status = "加载河流护盾..."
            self._load_river_shield_image()
            self._preload_current_step = 5
            self._preload_progress = 5.0 / self._preload_total_steps
            
            self._preload_status = "加载星星动画..."
            self._load_star_frames()
            self._preload_current_step = 6
            self._preload_progress = 6.0 / self._preload_total_steps
            
            self._preload_status = "加载音频文件..."
            self._load_sounds()
            self._preload_current_step = 7
            self._preload_progress = 1.0
            self._preload_status = "资源加载完成"
            print("✓ 游戏资源加载完成")
        except Exception as e:
            print(f"⚠ 加载资源时出错: {e}")
            self._preload_status = f"加载出错: {e}"
    
    def preload_all(self):
        """预加载所有资源（同步）"""
        if not self._resources_loaded:
            self._load_all_resources()
            self._resources_loaded = True
    
    def get_preload_progress(self) -> float:
        """获取预加载进度 (0.0 - 1.0)"""
        return self._preload_progress
    
    def get_preload_status(self) -> str:
        """获取预加载状态文本"""
        return self._preload_status
    
    def is_preload_complete(self) -> bool:
        """检查预加载是否完成"""
        return self._resources_loaded and self._preload_progress >= 1.0
    
    def _load_wall_images(self):
        """加载墙体图片"""
        walls_path = os.path.join(self.base_path, "images", "walls")
        for i in range(6):
            img_path = os.path.join(walls_path, f"{i}.png")
            if os.path.exists(img_path):
                img = pygame.image.load(img_path).convert_alpha()
                # 缩放到50x50
                self.images[f"wall_{i}"] = pygame.transform.scale(img, (50, 50))
    
    def _load_bullet_image(self):
        """加载子弹图片"""
        bullet_path = os.path.join(self.base_path, "images", "bullet", "bullet.png")
        if os.path.exists(bullet_path):
            self.images["bullet"] = pygame.image.load(bullet_path).convert_alpha()
    
    def _load_explosion_frames(self):
        """加载爆炸动画帧"""
        boom_path = os.path.join(self.base_path, "images", "boom")
        for i in range(1, 9):
            img_path = os.path.join(boom_path, f"blast{i}.gif")
            if os.path.exists(img_path):
                self.explosion_frames.append(pygame.image.load(img_path).convert_alpha())
    
    def _load_shield_frames(self):
        """加载护盾动画帧"""
        shield_path = os.path.join(self.base_path, "images", "born_shield")
        for i in range(2):
            img_path = os.path.join(shield_path, f"bornShield{i}.png")
            if os.path.exists(img_path):
                img = pygame.image.load(img_path).convert_alpha()
                # 缩放到30x30以匹配坦克大小
                img = pygame.transform.scale(img, (30, 30))
                self.shield_frames.append(img)
    
    def _load_river_shield_image(self):
        """加载河流护盾图片"""
        img_path = os.path.join(self.base_path, "images", "river_shield", "river_shield.png")
        if os.path.exists(img_path):
            img = pygame.image.load(img_path).convert_alpha()
            # 缩放到30x30以匹配坦克大小
            self.river_shield_image = pygame.transform.scale(img, (30, 30))

    def _load_star_frames(self):
        """加载星星动画帧（敌人生成特效）"""
        star_path = os.path.join(self.base_path, "images", "star")
        for i in range(4):
            img_path = os.path.join(star_path, f"star{i}.png")
            if os.path.exists(img_path):
                self.star_frames.append(pygame.image.load(img_path).convert_alpha())
    
    def _load_sounds(self):
        """加载音频文件"""
        musics_path = os.path.join(self.base_path, "musics")
        sound_files = {
            "boom": "boom.wav",
            # "bullet_destroy": "bullet.destroy.wav",  # 格式不兼容，已移除
            "enemy_move": "enemy.move.wav",
            "fire": "fire.wav",
            "player_move": "player.move.wav",
            "player_idle": "玩家原地待机音效.mp3",
            "start": "start.wav",
            "brick_destroy": "砖块消除.wav",
        }
        
        for key, filename in sound_files.items():
            sound_path = os.path.join(musics_path, filename)
            if os.path.exists(sound_path):
                try:
                    self.sounds[key] = pygame.mixer.Sound(sound_path)
                except Exception as e:
                    print(f"无法加载音频 {filename}: {e}")
    
    def load_tank_images(self, tank_type: str, tank_id: int, level: int = 0) -> Dict[int, List[pygame.Surface]]:
        """
        加载坦克图片（4个方向，每个方向2帧动画）
        
        Args:
            tank_type: 'player' 或 'enemy'
            tank_id: 坦克ID (1-4)
            level: 坦克等级 (0-3)
        
        Returns:
            字典 {方向: [帧1, 帧2, 帧3, 帧4]}，方向: 0=上, 1=右, 2=下, 3=左
        """
        self._ensure_resources_loaded()
        cache_key = f"{tank_type}_{tank_id}_{level}"
        if cache_key in self.tank_images:
            return self.tank_images[cache_key]
        
        images = {0: [], 1: [], 2: [], 3: []}  # 4个方向
        
        # 修正拼写错误：palyer -> player
        folder_name = "palyer" if tank_type == "player" else "enemy"
        prefix = f"p{tank_id}" if tank_type == "player" else f"e{tank_id}"
        
        tank_base_path = os.path.join(
            self.base_path, 
            "tank_images", 
            folder_name,
            prefix,
            f"{prefix}_{level}"
        )
        
        # 加载每个方向的图片
        for frame in range(2):  # 2帧动画
            img_path = os.path.join(tank_base_path, f"{prefix}_{level}_{frame}.png")
            if os.path.exists(img_path):
                original = pygame.image.load(img_path).convert_alpha()
                # 缩放到30x30
                original = pygame.transform.scale(original, (30, 30))
                
                # 为4个方向创建旋转版本
                # 原始图片是向上的
                images[0].append(original)  # 上
                images[1].append(pygame.transform.rotate(original, -90))  # 右
                images[2].append(pygame.transform.rotate(original, 180))  # 下
                images[3].append(pygame.transform.rotate(original, 90))  # 左
        
        self.tank_images[cache_key] = images
        return images
    
    def get_wall_image(self, wall_type: int) -> Optional[pygame.Surface]:
        """获取墙体图片"""
        self._ensure_resources_loaded()
        return self.images.get(f"wall_{wall_type}")
    
    def get_bullet_image(self) -> Optional[pygame.Surface]:
        """获取子弹图片"""
        self._ensure_resources_loaded()
        return self.images.get("bullet")
    
    def get_explosion_frames(self) -> List[pygame.Surface]:
        """获取爆炸动画帧"""
        self._ensure_resources_loaded()
        return self.explosion_frames
    
    def get_shield_frames(self) -> List[pygame.Surface]:
        """获取护盾动画帧"""
        self._ensure_resources_loaded()
        return self.shield_frames
    
    def get_river_shield_image(self) -> Optional[pygame.Surface]:
        """获取河流护盾图片"""
        self._ensure_resources_loaded()
        return self.river_shield_image

    def get_star_frames(self) -> List[pygame.Surface]:
        """获取星星动画帧"""
        return self.star_frames
    
    def play_sound(self, sound_name: str, loops: int = 0):
        """
        播放音效
        
        Args:
            sound_name: 音效名称
            loops: 循环次数，0表示播放一次，-1表示无限循环
        """
        self._ensure_resources_loaded()
        if sound_name in self.sounds:
            try:
                self.sounds[sound_name].play(loops=loops)
            except Exception as e:
                print(f"播放音效失败 {sound_name}: {e}")
    
    def stop_sound(self, sound_name: str):
        """停止播放音效"""
        if sound_name in self.sounds:
            try:
                self.sounds[sound_name].stop()
            except Exception as e:
                print(f"停止音效失败 {sound_name}: {e}")
    
    def set_sound_volume(self, sound_name: str, volume: float):
        """
        设置音效音量
        
        Args:
            sound_name: 音效名称
            volume: 音量 (0.0 - 1.0)
        """
        if sound_name in self.sounds:
            self.sounds[sound_name].set_volume(volume)


# 全局资源管理器实例
resource_manager = ResourceManager()
