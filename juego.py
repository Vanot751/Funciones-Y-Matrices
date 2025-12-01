# Clase Juego (lógica principal y bucle)

# Clase Juego (lógica principal y bucle)
import pygame
import sys
import math
import random
from config import SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE, VISIBLE_RADIUS, FPS
from config import BLACK, WHITE, GRAY, DARK_GRAY, GREEN, BROWN, RED, BLUE, YELLOW, PURPLE
from mapa import Mapa

class Juego:
    def __init__(self):
        self.mapa_actual = None
        self.nivel = 1
        self.screen = None
        self.clock = pygame.time.Clock()
        self.font = None
        self.mensaje = ""
        self.mensaje_tiempo = 0
        self.pista_portal = ""   # <- pista persistente por nivel

    def iniciar_pygame(self):
        pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN])
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Aventura optimizada (estética original)")
        self.font = pygame.font.SysFont(None, 24)

    def cambiar_mapa(self, filas, columnas):
        self.mapa_actual = Mapa(filas, columnas)
        self.mapa_actual.generar_mapa()
        self.mostrar_mensaje(f"--- Nivel {self.nivel} ---")

        # Generar pista estática para este nivel (una sola vez)
        px, py = self.mapa_actual.portal
        if random.choice([True, False]):
            self.pista_portal = f"({px}, ?)"
        else:
            self.pista_portal = f"(?, {py})"

    def iniciar(self):
        self.iniciar_pygame()
        self.cambiar_mapa(15, 15)
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        running = False

                    # Movimiento del jugador (WASD)
                    dx, dy = 0, 0
                    if event.key == pygame.K_w: dx = -1
                    elif event.key == pygame.K_s: dx = 1
                    elif event.key == pygame.K_a: dy = -1
                    elif event.key == pygame.K_d: dy = 1

                    if dx != 0 or dy != 0:
                        if self.mapa_actual.jugador.mover(dx, dy, self.mapa_actual.base_matriz):
                            # Revelado alrededor del jugador
                            self.mapa_actual.revelar_area(self.mapa_actual.jugador.x,
                                                          self.mapa_actual.jugador.y,
                                                          VISIBLE_RADIUS)
                            # Movimiento de enemigos
                            for enemigo in self.mapa_actual.enemigos:
                                enemigo.mover_hacia_jugador(self.mapa_actual.jugador,
                                                            self.mapa_actual.base_matriz,
                                                            self.mapa_actual.jugador.movimientos)

                            # Colisiones y eventos
                            if self.verificar_colision_enemigo():
                                self.mostrar_mensaje("¡Has sido atrapado por un enemigo!")
                                running = False
                            if self.verificar_cofre():
                                pass
                            if self.verificar_portal():
                                self.mostrar_mensaje("¡Portal encontrado! Pasando al siguiente nivel...")
                                self.nivel += 1
                                self.cambiar_mapa(15 + self.nivel, 15 + self.nivel)

            # Expirar mensajes después de 3s
            if pygame.time.get_ticks() - self.mensaje_tiempo > 3000:
                self.mensaje = ""

            # Render
            self.dibujar()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()

    # ---------------- Lógica ----------------
    def mostrar_mensaje(self, texto):
        self.mensaje = texto
        self.mensaje_tiempo = pygame.time.get_ticks()

    def verificar_colision_enemigo(self):
        j = self.mapa_actual.jugador
        return any(j.x == e.x and j.y == e.y for e in self.mapa_actual.enemigos)

    def verificar_cofre(self):
        j = self.mapa_actual.jugador
        for c in self.mapa_actual.cofres:
            if not c.abierto and j.x == c.x and j.y == c.y:
                c.abierto = True
                self.mostrar_mensaje(f"¡Cofre abierto! Contenía: {c.contenido}")
                return True
        return False

    def verificar_portal(self):
        j = self.mapa_actual.jugador
        px, py = self.mapa_actual.portal
        return j.x == px and j.y == py

    # ---------------- Render ----------------
    def dibujar(self):
        self.screen.fill(BLACK)

        # Cámara centrada en el jugador (fila -> y, columna -> x)
        offset_x = (SCREEN_WIDTH // 2) - (self.mapa_actual.jugador.y * TILE_SIZE)
        offset_y = (SCREEN_HEIGHT // 2) - (self.mapa_actual.jugador.x * TILE_SIZE)

        # Rango visible de tiles (culling)
        start_i = max(0, math.floor((-offset_y) / TILE_SIZE))
        end_i   = min(self.mapa_actual.filas, math.ceil((SCREEN_HEIGHT - offset_y) / TILE_SIZE))
        start_j = max(0, math.floor((-offset_x) / TILE_SIZE))
        end_j   = min(self.mapa_actual.columnas, math.ceil((SCREEN_WIDTH - offset_x) / TILE_SIZE))

        # Base estática dentro del viewport y si está revelado
        for i in range(start_i, end_i):
            for j in range(start_j, end_j):
                if not self.mapa_actual.revelado[i][j]:
                    continue
                x = j * TILE_SIZE + offset_x
                y = i * TILE_SIZE + offset_y
                celda = self.mapa_actual.base_matriz[i][j]
                if celda == '.':
                    pygame.draw.rect(self.screen, GREEN, (x, y, TILE_SIZE, TILE_SIZE))
                elif celda == 'S':
                    pygame.draw.rect(self.screen, PURPLE, (x, y, TILE_SIZE, TILE_SIZE))
                    pygame.draw.circle(self.screen, WHITE,
                                       (x + TILE_SIZE // 2, y + TILE_SIZE // 2),
                                       TILE_SIZE // 4)
                else:
                    pygame.draw.rect(self.screen, DARK_GRAY, (x, y, TILE_SIZE, TILE_SIZE))
                pygame.draw.rect(self.screen, GRAY, (x, y, TILE_SIZE, TILE_SIZE), 1)

        # Auxiliar viewport
        def dentro_view(i, j):
            return start_i <= i < end_i and start_j <= j < end_j

        # Cofres
        for c in self.mapa_actual.cofres:
            if not c.abierto and self.mapa_actual.revelado[c.x][c.y] and dentro_view(c.x, c.y):
                cx = c.y * TILE_SIZE + offset_x
                cy = c.x * TILE_SIZE + offset_y
                pygame.draw.rect(self.screen, BROWN, (cx, cy, TILE_SIZE, TILE_SIZE))
                pygame.draw.rect(self.screen, YELLOW, (cx + 10, cy + 10, TILE_SIZE - 20, TILE_SIZE - 20))
                pygame.draw.rect(self.screen, GRAY, (cx, cy, TILE_SIZE, TILE_SIZE), 1)

        # Enemigos
        for e in self.mapa_actual.enemigos:
            if self.mapa_actual.revelado[e.x][e.y] and dentro_view(e.x, e.y):
                ex = e.y * TILE_SIZE + offset_x
                ey = e.x * TILE_SIZE + offset_y
                pygame.draw.rect(self.screen, RED, (ex, ey, TILE_SIZE, TILE_SIZE))
                pygame.draw.polygon(self.screen, BLACK, [
                    (ex + TILE_SIZE // 2, ey + 5),
                    (ex + 5, ey + TILE_SIZE - 5),
                    (ex + TILE_SIZE - 5, ey + TILE_SIZE - 5)
                ])
                pygame.draw.rect(self.screen, GRAY, (ex, ey, TILE_SIZE, TILE_SIZE), 1)

        # Jugador
        px = self.mapa_actual.jugador.y * TILE_SIZE + offset_x
        py = self.mapa_actual.jugador.x * TILE_SIZE + offset_y
        pygame.draw.rect(self.screen, BLUE, (px, py, TILE_SIZE, TILE_SIZE))
        pygame.draw.circle(self.screen, WHITE, (px + TILE_SIZE // 2, py + TILE_SIZE // 2), TILE_SIZE // 3)
        pygame.draw.rect(self.screen, GRAY, (px, py, TILE_SIZE, TILE_SIZE), 1)

        # HUD
        self.dibujar_hud()
        pygame.display.flip()

    def dibujar_hud(self):
        nivel_texto  = self.font.render(f"Nivel: {self.nivel}", True, WHITE)
        vida_texto   = self.font.render(f"Vida: {self.mapa_actual.jugador.vida}", True, WHITE)
        movs_texto   = self.font.render(f"Movimientos: {self.mapa_actual.jugador.movimientos}", True, WHITE)
        coords_texto = self.font.render(f"Posición: ({self.mapa_actual.jugador.x}, {self.mapa_actual.jugador.y})", True, WHITE)
        mapa_texto   = self.font.render(f"Mapa: {self.mapa_actual.filas}x{self.mapa_actual.columnas}", True, WHITE)

        # Pista portal (ESTÁTICA: se generó en cambiar_mapa)
        pista_texto  = self.font.render(f"Pista portal: {self.pista_portal}", True, YELLOW)

        # Dibujar en pantalla
        self.screen.blit(nivel_texto,  (10, 10))
        self.screen.blit(vida_texto,   (10, 40))
        self.screen.blit(movs_texto,   (10, 70))
        self.screen.blit(coords_texto, (10, 100))
        self.screen.blit(mapa_texto,   (10, 130))
        self.screen.blit(pista_texto,  (10, 160))

        if self.mensaje:
            msg_surface = self.font.render(self.mensaje, True, YELLOW)
            msg_rect = msg_surface.get_rect(center=(SCREEN_WIDTH // 2, 30))
            self.screen.blit(msg_surface, msg_rect)
