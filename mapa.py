
# Clase Mapa y lógica de generación optimizada con conectividad garantizada
# y dificultad progresiva basada en el tamaño del mapa (relacionado con el nivel).
#
# Compatibilidad: mantiene la interfaz usada por juego.py
#   - Mapa(filas, columnas)
#   - generar_mapa()
#   - revelar_area(x, y, radio)
#   - atributos: base_matriz, revelado, jugador, enemigos, cofres, portal

import random
from collections import deque
from entidades import Personaje, Enemigo, Cofre
from config import VISIBLE_RADIUS

class Mapa:
    def __init__(self, filas, columnas, seed=None):
        self.filas = filas
        self.columnas = columnas
        self.base_matriz = [[' ' for _ in range(columnas)] for _ in range(filas)]
        self.revelado = [[False for _ in range(columnas)] for _ in range(filas)]
        self.jugador = None
        self.enemigos = []
        self.cofres = []
        self.portal = None
        if seed is not None:
            random.seed(seed)

    # ===================== API principal =====================
    def generar_mapa(self):
        """Genera un mapa aleatorio PERO garantizando que exista camino
        entre el jugador y el portal. Incluye dificultad progresiva.
        """
        # Estimamos el nivel a partir del tamaño del mapa que el Juego ya escala.
        # (El juego llama cambiar_mapa(15 + nivel, 15 + nivel))
        nivel_est = max(self.filas, self.columnas) - 15
        if nivel_est < 1:
            nivel_est = 1

        # Parámetros de dificultad progresiva
        # Menor probabilidad de suelo a mayor nivel => más obstáculos.
        prob_suelo = max(0.50, 0.72 - 0.02 * (nivel_est - 1))  # clamp [0.50, ~0.72]
        intentos_max = 8  # Intentos de regeneración antes de forzar camino
        min_dist_portal = min(8 + nivel_est, (self.filas + self.columnas) // 2)  # distancia mínima deseada

        cx, cy = self.filas // 2, self.columnas // 2  # centro para comenzar

        exito = False
        for _ in range(intentos_max):
            self._generar_terreno(prob_suelo)
            # Asegurar que el centro sea transitable
            self.base_matriz[cx][cy] = '.'
            self.jugador = Personaje(cx, cy)

            # Celdas alcanzables desde el jugador
            alcanzables, dist = self._alcanzables_desde((cx, cy))
            if not alcanzables:
                continue  # Terreno demasiado bloqueado, intentar de nuevo

            # Elegir portal: preferimos celdas muy lejanas y alcanzables
            portal = self._elegir_portal(alcanzables, dist, min_dist=min_dist_portal)
            if portal is None:
                # Tomar la celda más lejana alcanzable
                portal = max(alcanzables, key=lambda p: dist[p])

            px, py = portal
            self.base_matriz[px][py] = 'S'
            self.portal = (px, py)

            # Recalcular alcanzables incluyendo el portal (no necesario para camino, pero útil)
            alcanzables, dist = self._alcanzables_desde((cx, cy))
            if (px, py) not in alcanzables:
                # Algo falló (no hay camino), reintentar
                continue

            # Colocar entidades sólo en celdas alcanzables
            self._colocar_entidades(alcanzables, jugador=(cx, cy), portal=(px, py), nivel=nivel_est)

            # Revelar área inicial
            self.revelar_area(cx, cy, VISIBLE_RADIUS)
            exito = True
            break

        if not exito:
            # Último recurso: forzar un camino en forma de corredor L hacia una esquina lejana
            self._generar_terreno(prob_suelo)
            self.base_matriz[cx][cy] = '.'
            self.jugador = Personaje(cx, cy)
            esquina = self._esquina_mas_lejana(cx, cy)
            px, py = esquina
            self._carvar_camino((cx, cy), (px, py))
            self.base_matriz[px][py] = 'S'
            self.portal = (px, py)
            alcanzables, _ = self._alcanzables_desde((cx, cy))
            self._colocar_entidades(alcanzables, jugador=(cx, cy), portal=(px, py), nivel=nivel_est)
            self.revelar_area(cx, cy, VISIBLE_RADIUS)

    def revelar_area(self, x, y, radio):
        r2 = radio * radio
        for i in range(max(0, x - radio), min(self.filas, x + radio + 1)):
            for j in range(max(0, y - radio), min(self.columnas, y + radio + 1)):
                dx = x - i
                dy = y - j
                if dx * dx + dy * dy <= r2:
                    self.revelado[i][j] = True

    # ===================== Utilidades internas =====================
    def _generar_terreno(self, prob_suelo: float):
        """Rellena el mapa con suelo '.' según una probabilidad y el resto como muros ' '."""
        for i in range(self.filas):
            fila = self.base_matriz[i]
            for j in range(self.columnas):
                fila[j] = '.' if random.random() < prob_suelo else ' '

    def _alcanzables_desde(self, inicio):
        """BFS que devuelve el conjunto de celdas '.' alcanzables desde inicio
        y un diccionario con distancia en pasos.
        """
        si, sj = inicio
        if not self._es_transitable(si, sj):
            return set(), {}
        visitados = set()
        dist = {}
        q = deque([(si, sj)])
        visitados.add((si, sj))
        dist[(si, sj)] = 0
        while q:
            x, y = q.popleft()
            for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if self._en_limites(nx, ny) and self._es_transitable(nx, ny) and (nx, ny) not in visitados:
                    visitados.add((nx, ny))
                    dist[(nx, ny)] = dist[(x, y)] + 1
                    q.append((nx, ny))
        return visitados, dist

    def _elegir_portal(self, alcanzables, dist, min_dist=5):
        """Elige una celda alcanzable con distancia >= min_dist.
        Prioriza las más lejanas para aumentar el desafío.
        """
        candidatos = [p for p in alcanzables if dist.get(p, 0) >= min_dist]
        if not candidatos:
            return None
        # Seleccionar entre el 25% más lejano
        candidatos.sort(key=lambda p: dist[p], reverse=True)
        top = max(1, len(candidatos) // 4)
        return random.choice(candidatos[:top])

    def _colocar_entidades(self, alcanzables, jugador, portal, nivel):
        """Coloca enemigos y cofres en celdas alcanzables, evitando jugador y portal.
        Escala la cantidad y atributos con el nivel.
        """
        disponibles = set(alcanzables)
        disponibles.discard(jugador)
        disponibles.discard(portal)
        if not disponibles:
            return

        area = self.filas * self.columnas
        # Escalado: más enemigos con el nivel y el tamaño del mapa
        base_enemigos = 4
        enemigos_nivel = base_enemigos + nivel + max(0, area // 200)
        enemigos_max = max(5, area // 40)
        num_enemigos = min(enemigos_nivel, enemigos_max, len(disponibles))

        # Cofres: un poco menos agresivo, pero también escala
        base_cofres = 6
        cofres_nivel = base_cofres + max(0, nivel // 2) + max(0, area // 250)
        cofres_max = max(5, area // 45)
        num_cofres = min(cofres_nivel, cofres_max, max(0, len(disponibles) - num_enemigos))

        # Colocar enemigos
        for _ in range(num_enemigos):
            x, y = random.choice(tuple(disponibles))
            disponibles.remove((x, y))
            e = Enemigo(x, y)
            # Dificultad progresiva: aumentar visión con el nivel (tope 9)
            e.vision = min(9, 5 + nivel // 3)
            self.enemigos.append(e)

        # Colocar cofres
        for _ in range(num_cofres):
            x, y = random.choice(tuple(disponibles))
            disponibles.remove((x, y))
            self.cofres.append(Cofre(x, y))

    def _carvar_camino(self, origen, destino):
        """Abre un corredor en forma de L desde origen hasta destino garantizando conectividad."""
        ox, oy = origen
        dx, dy = destino
        # Carvar a lo largo del eje X
        step_x = 1 if dx > ox else -1
        for x in range(ox, dx + step_x, step_x):
            self.base_matriz[x][oy] = '.'
        # Luego a lo largo del eje Y
        step_y = 1 if dy > oy else -1
        for y in range(oy, dy + step_y, step_y):
            self.base_matriz[dx][y] = '.'

    def _esquina_mas_lejana(self, x, y):
        """Devuelve la esquina del mapa con mayor distancia Manhattan al punto dado."""
        esquinas = [(0, 0), (0, self.columnas - 1), (self.filas - 1, 0), (self.filas - 1, self.columnas - 1)]
        return max(esquinas, key=lambda p: abs(p[0] - x) + abs(p[1] - y))

    def _en_limites(self, x, y):
        return 0 <= x < self.filas and 0 <= y < self.columnas

    def _es_transitable(self, x, y):
        return self.base_matriz[x][y] == '.' or self.base_matriz[x][y] == 'S'

    # Método legado (para compatibilidad si fuera usado en otro lugar)
    def _posicion_aleatoria_valida(self, lejos_de=None, min_dist=0):
        """Selecciona una posición aleatoria en suelo '.' cumpliendo distancia mínima opcional."""
        intentos = 200
        while intentos > 0:
            intentos -= 1
            x = random.randint(0, self.filas - 1)
            y = random.randint(0, self.columnas - 1)
            if self.base_matriz[x][y] == '.':
                if lejos_de is None:
                    return x, y
                dx = lejos_de[0] - x
                dy = lejos_de[1] - y
                if dx * dx + dy * dy >= min_dist * min_dist:
                    return x, y
        # Fallback: devolver cualquier transitable
        for i in range(self.filas):
            for j in range(self.columnas):
                if self.base_matriz[i][j] == '.':
                    return i, j
        # Si nada transitable, centro
        return self.filas // 2, self.columnas // 2
