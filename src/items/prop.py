import pygame
import random
import time
import os
from src.config.game_config import config

class Prop(pygame.sprite.Sprite):
    def __init__(self, x, y, prop_type):
        super().__init__()
        self.type = prop_type  # 1-8
        # Use absolute path for image loading
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        image_path = os.path.join(base_path, "images", "props", f"prop{prop_type}.png")
        loaded_image = pygame.image.load(image_path).convert_alpha()
        # 缩放到配置的尺寸
        self.image = pygame.transform.scale(loaded_image, (config.PROP_WIDTH, config.PROP_HEIGHT))
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.creation_time = time.time()
        self.flash_interval = 0.2
        self.visible = True
        self.last_flash_time = 0

    def update(self):
        # Flash effect before disappearing (optional, or just static)
        # For now, let's keep it simple: static until picked up or level ends
        pass

class PropManager:
    def __init__(self):
        self.props = pygame.sprite.Group()
        
    def spawn_prop(self, x, y, prop_type=None):
        # Randomly select a prop type (1-8) if not specified
        if prop_type is None:
            prop_type = random.randint(1, 8)
        prop = Prop(x, y, prop_type)
        self.props.add(prop)
        return prop

    def update(self):
        self.props.update()

    def draw(self, screen):
        self.props.draw(screen)

    def check_collision(self, player_rect):
        # Returns a list of props collided with
        hit_props = []
        for prop in self.props:
            if player_rect.colliderect(prop.rect):
                hit_props.append(prop)
                prop.kill()
        return hit_props
