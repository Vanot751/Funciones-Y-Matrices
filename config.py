# Constantes y configuración global

import pygame

pygame.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
TILE_SIZE = 40
VISIBLE_RADIUS = 3
FPS = 60

# Colores
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)
DARK_GRAY = (50, 50, 50)
GREEN = (0, 150, 0)
BROWN = (139, 69, 19)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)

# --- Nuevas constantes de gameplay ---
ENEMY_DAMAGE = 25           # Daño al jugador por colisión si no usa item
MONEY_MIN = 10              # Valor mínimo de dinero en un cofre
MONEY_MAX = 50              # Valor máximo de dinero en un cofre
