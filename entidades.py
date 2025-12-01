# Clases: Personaje, Enemigo, Cofre


import random
from config import MONEY_MIN, MONEY_MAX



class Personaje:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.movimientos = 0

        # Corazones (vida escalable)
        self.corazones_totales = 2   # Comienza con 2 corazones
        self.corazones_llenos = 2    # Ambos llenos al inicio

        # Inventario
        self.armaduras = 0           # Cada una permite empujar enemigo
        self.espadas = 0             # Cada una elimina enemigo al contacto

        # Puntuación acumulada (para recargar corazones)
        self.puntuacion = 0

    def mover(self, dx, dy, base_matriz):
        """Mueve al jugador si la celda es transitable."""
        nuevo_x = self.x + dx
        nuevo_y = self.y + dy
        filas = len(base_matriz)
        columnas = len(base_matriz[0])
        if not (0 <= nuevo_x < filas and 0 <= nuevo_y < columnas):
            return False
        if base_matriz[nuevo_x][nuevo_y] in ('.', 'S'):
            self.x = nuevo_x
            self.y = nuevo_y
            self.movimientos += 1
            return True
        return False

    def perder_corazon(self):
        """Pierde un corazón lleno si hay disponible."""
        if self.corazones_llenos > 0:
            self.corazones_llenos -= 1

    def agregar_corazon(self):
        """Añade un corazón vacío (por pasar de nivel)."""
        self.corazones_totales += 1

    def recargar_corazones(self, costo_por_corazon=100):
        """Recarga corazones vacíos usando puntuación acumulada."""
        while self.corazones_llenos < self.corazones_totales and self.puntuacion >= costo_por_corazon:
            self.puntuacion -= costo_por_corazon
            self.corazones_llenos += 1


class Enemigo:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vida = 50
        self.vision = 5
        self.ultimo_movimiento = 0
        # Dirección del último paso (para poder empujar en sentido contrario)
        self.ultimo_dx = 0
        self.ultimo_dy = 0

    def mover_hacia_jugador(self, jugador, base_matriz, movimiento_actual):
        # Se mueve cada 2 movimientos del jugador
        if movimiento_actual - self.ultimo_movimiento < 2:
            return False
        dist_x = jugador.x - self.x
        dist_y = jugador.y - self.y
        if abs(dist_x) <= self.vision and abs(dist_y) <= self.vision:
            dx, dy = 0, 0
            if abs(dist_x) > abs(dist_y):
                dx = 1 if dist_x > 0 else -1
            else:
                dy = 1 if dist_y > 0 else -1
            nuevo_x = self.x + dx
            nuevo_y = self.y + dy
            filas = len(base_matriz)
            columnas = len(base_matriz[0])
            if 0 <= nuevo_x < filas and 0 <= nuevo_y < columnas:
                if base_matriz[nuevo_x][nuevo_y] in ('.', 'S'):
                    self.x = nuevo_x
                    self.y = nuevo_y
                    self.ultimo_movimiento = movimiento_actual
                    self.ultimo_dx = dx
                    self.ultimo_dy = dy
                    return True
        return False

class Cofre:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        # Armadura / Espada / Dinero
        self.contenido = random.choice(['armadura', 'espada', 'dinero'])
        # Valor solo aplica para dinero
        self.valor = random.randint(MONEY_MIN, MONEY_MAX) if self.contenido == 'dinero' else 0
        self.abierto = False
