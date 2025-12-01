
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
        self.pista_portal = ""

    def iniciar_pygame(self):
        pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN])
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Aventura optimizada (corazones y puntuación)")
        self.font = pygame.font.SysFont(None, 24)

    def cambiar_mapa(self, filas, columnas):
        # Si es el primer mapa, crear jugador normal
        if self.mapa_actual is None:
            self.mapa_actual = Mapa(filas, columnas)
            self.mapa_actual.generar_mapa()
        else:
            # Guardar estado del jugador
            j_prev = self.mapa_actual.jugador
            self.mapa_actual = Mapa(filas, columnas)
            self.mapa_actual.generar_mapa()
            # Transferir stats
            j = self.mapa_actual.jugador
            j.corazones_totales = j_prev.corazones_totales
            j.corazones_llenos = j_prev.corazones_llenos
            j.armaduras = j_prev.armaduras
            j.espadas = j_prev.espadas
            j.puntuacion = j_prev.puntuacion

        self.mostrar_mensaje(f"--- Nivel {self.nivel} ---")

        # Generar pista estática del portal
        px, py = self.mapa_actual.portal
        self.pista_portal = f"({px}, ?)" if random.choice([True, False]) else f"(?, {py})"

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

                    dx, dy = 0, 0
                    if event.key == pygame.K_w: dx = -1
                    elif event.key == pygame.K_s: dx = 1
                    elif event.key == pygame.K_a: dy = -1
                    elif event.key == pygame.K_d: dy = 1

                    if dx != 0 or dy != 0:
                        if self.mapa_actual.jugador.mover(dx, dy, self.mapa_actual.base_matriz):
                            self.mapa_actual.revelar_area(self.mapa_actual.jugador.x,
                                                          self.mapa_actual.jugador.y,
                                                          VISIBLE_RADIUS)
                            for enemigo in self.mapa_actual.enemigos:
                                enemigo.mover_hacia_jugador(self.mapa_actual.jugador,
                                                            self.mapa_actual.base_matriz,
                                                            self.mapa_actual.jugador.movimientos)

                            self.verificar_cofre()

                            if self.resolver_colisiones_enemigos():
                                running = False

                            if self.verificar_portal():
                                self.mostrar_mensaje("¡Portal encontrado! Pasando al siguiente nivel...")
                                self.nivel += 1
                                j = self.mapa_actual.jugador
                                j.corazones_totales += 1  # Añadir corazón vacío
                                self.recargar_corazones(j)  # Intentar recargar usando puntuación
                                self.cambiar_mapa(15 + self.nivel, 15 + self.nivel)

            if pygame.time.get_ticks() - self.mensaje_tiempo > 3000:
                self.mensaje = ""

            self.dibujar()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()

    # ---------------- Lógica ----------------
    def mostrar_mensaje(self, texto):
        self.mensaje = texto
        self.mensaje_tiempo = pygame.time.get_ticks()

    def resolver_colisiones_enemigos(self):
        j = self.mapa_actual.jugador
        colisionados = [e for e in self.mapa_actual.enemigos if j.x == e.x and j.y == e.y]
        if not colisionados:
            return False

        for e in colisionados:
            if j.espadas > 0:
                j.espadas -= 1
                self.mapa_actual.enemigos.remove(e)
                self.mostrar_mensaje("Usaste una ESPADA: enemigo eliminado!")
                continue

            if j.armaduras > 0:
                j.armaduras -= 1
                if self.empujar_enemigo(e, pasos=2):
                    self.mostrar_mensaje("Usaste ARMADURA: enemigo empujado!")
                else:
                    j.perder_corazon()
                    self.mostrar_mensaje(f"No se pudo empujar: perdiste un corazón ({j.corazones_llenos}/{j.corazones_totales})")
                    if j.corazones_llenos == 0:
                        self.mostrar_mensaje("¡Has sido derrotado!")
                        return True
                continue

            # Sin items: perder corazón
            j.perder_corazon()
            self.mostrar_mensaje(f"¡Perdiste un corazón! ({j.corazones_llenos}/{j.corazones_totales})")
            if j.corazones_llenos == 0:
                self.mostrar_mensaje("¡Has sido derrotado!")
                return True

        return False

    def empujar_enemigo(self, enemigo, pasos=2):
        dx = enemigo.ultimo_dx
        dy = enemigo.ultimo_dy
        if dx == 0 and dy == 0:
            j = self.mapa_actual.jugador
            dx = 1 if enemigo.x > j.x else -1 if enemigo.x < j.x else 0
            dy = 1 if enemigo.y > j.y else -1 if enemigo.y < j.y else 0
        dx *= -1
        dy *= -1
        final_x, final_y = enemigo.x, enemigo.y
        for step in range(1, pasos + 1):
            nx = enemigo.x + dx * step
            ny = enemigo.y + dy * step
            if 0 <= nx < self.mapa_actual.filas and 0 <= ny < self.mapa_actual.columnas:
                if self.mapa_actual.base_matriz[nx][ny] in ('.', 'S'):
                    final_x, final_y = nx, ny
                else:
                    break
            else:
                break
        if (final_x, final_y) != (enemigo.x, enemigo.y):
            enemigo.x, enemigo.y = final_x, final_y
            return True
        return False

    def verificar_cofre(self):
        j = self.mapa_actual.jugador
        for c in self.mapa_actual.cofres:
            if not c.abierto and j.x == c.x and j.y == c.y:
                c.abierto = True
                if c.contenido == 'armadura':
                    j.armaduras += 1
                    self.mostrar_mensaje("¡Cofre abierto! ARMADURA obtenida.")
                elif c.contenido == 'espada':
                    j.espadas += 1
                    self.mostrar_mensaje("¡Cofre abierto! ESPADA obtenida.")
                elif c.contenido == 'dinero':
                    j.puntuacion += c.valor
                    self.mostrar_mensaje(f"¡Cofre abierto! Dinero +{c.valor}. Puntos: {j.puntuacion}")
                return True
        return False

    def verificar_portal(self):
        j = self.mapa_actual.jugador
        px, py = self.mapa_actual.portal
        return j.x == px and j.y == py

    def recargar_corazones(self, jugador, costo_por_corazon=100):
        while jugador.corazones_llenos < jugador.corazones_totales and jugador.puntuacion >= costo_por_corazon:
            jugador.puntuacion -= costo_por_corazon
            jugador.corazones_llenos += 1

    # ---------------- Render ----------------
    def dibujar(self):
        self.screen.fill(BLACK)
        offset_x = (SCREEN_WIDTH // 2) - (self.mapa_actual.jugador.y * TILE_SIZE)
        offset_y = (SCREEN_HEIGHT // 2) - (self.mapa_actual.jugador.x * TILE_SIZE)
        start_i = max(0, math.floor((-offset_y) / TILE_SIZE))
        end_i = min(self.mapa_actual.filas, math.ceil((SCREEN_HEIGHT - offset_y) / TILE_SIZE))
        start_j = max(0, math.floor((-offset_x) / TILE_SIZE))
        end_j = min(self.mapa_actual.columnas, math.ceil((SCREEN_WIDTH - offset_x) / TILE_SIZE))

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
                    pygame.draw.circle(self.screen, WHITE, (x + TILE_SIZE // 2, y + TILE_SIZE // 2), TILE_SIZE // 4)
                else:
                    pygame.draw.rect(self.screen, DARK_GRAY, (x, y, TILE_SIZE, TILE_SIZE))
                pygame.draw.rect(self.screen, GRAY, (x, y, TILE_SIZE, TILE_SIZE), 1)

        def dentro_view(i, j):
            return start_i <= i < end_i and start_j <= j < end_j

        for c in self.mapa_actual.cofres:
            if not c.abierto and self.mapa_actual.revelado[c.x][c.y] and dentro_view(c.x, c.y):
                cx = c.y * TILE_SIZE + offset_x
                cy = c.x * TILE_SIZE + offset_y
                pygame.draw.rect(self.screen, BROWN, (cx, cy, TILE_SIZE, TILE_SIZE))
                pygame.draw.rect(self.screen, YELLOW, (cx + 10, cy + 10, TILE_SIZE - 20, TILE_SIZE - 20))
                pygame.draw.rect(self.screen, GRAY, (cx, cy, TILE_SIZE, TILE_SIZE), 1)

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

        px = self.mapa_actual.jugador.y * TILE_SIZE + offset_x
        py = self.mapa_actual.jugador.x * TILE_SIZE + offset_y
        pygame.draw.rect(self.screen, BLUE, (px, py, TILE_SIZE, TILE_SIZE))
        pygame.draw.circle(self.screen, WHITE, (px + TILE_SIZE // 2, py + TILE_SIZE // 2), TILE_SIZE // 3)
        pygame.draw.rect(self.screen, GRAY, (px, py, TILE_SIZE, TILE_SIZE), 1)

        self.dibujar_hud()
        pygame.display.flip()

    def dibujar_hud(self):
        j = self.mapa_actual.jugador
        nivel_texto = self.font.render(f"Nivel: {self.nivel}", True, WHITE)
        corazones_texto = self.font.render(f"Corazones: {j.corazones_llenos}/{j.corazones_totales}", True, WHITE)
        movs_texto = self.font.render(f"Movimientos: {j.movimientos}", True, WHITE)
        coords_texto = self.font.render(f"Posición: ({j.x}, {j.y})", True, WHITE)
        mapa_texto = self.font.render(f"Mapa: {self.mapa_actual.filas}x{self.mapa_actual.columnas}", True, WHITE)
        pista_texto = self.font.render(f"Pista portal: {self.pista_portal}", True, YELLOW)
        inv_armadura = self.font.render(f"Armaduras: {j.armaduras}", True, WHITE)
        inv_espada = self.font.render(f"Espadas: {j.espadas}", True, WHITE)
        puntaje_texto = self.font.render(f"Puntuación: {j.puntuacion}", True, WHITE)

        self.screen.blit(nivel_texto, (10, 10))
        self.screen.blit(corazones_texto, (10, 40))
        self.screen.blit(movs_texto, (10, 70))
        self.screen.blit(coords_texto, (10, 100))
        self.screen.blit(mapa_texto, (10, 130))
        self.screen.blit(pista_texto, (10, 160))
        self.screen.blit(inv_armadura, (10, 190))
        self.screen.blit(inv_espada, (10, 220))
        self.screen.blit(puntaje_texto, (10, 250))

        if self.mensaje:
            msg_surface = self.font.render(self.mensaje, True, YELLOW)
            msg_rect = msg_surface.get_rect(center=(SCREEN_WIDTH // 2, 30))
            self.screen.blit(msg_surface, msg_rect)
