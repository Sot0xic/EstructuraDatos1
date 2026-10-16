"""
Vista grafica del Tower Defense con Pygame (Semanas 2 y 3).

Dibuja el estado del modelo sobre el mapa de Tiled:

    - capas del mapa (Terreno, Camino, Decoracion) pre-renderizadas
    - torres colocadas por el jugador con su alcance (circulo translucido)
    - enemigos con barra de vida
    - Decoraciones_superiores por encima de enemigos y torres
    - resumen del estado (HUD)

Permite colocar torres haciendo click izquierdo en el mapa, validando
que la posicion no este en zona bloqueada, fuera del mapa ni encima de
otra torre. Las torres se dibujan en su posicion del mapa y su alcance
se calcula sobre el camino (progreso mas cercano).

La ventana solo dibuja el modelo; el ciclo del juego se ejecuta en
main.py.
"""

import pygame

from View.tiled_map import TiledMapRenderer


class GameWindow:
    """Ventana de Pygame que dibuja el estado del modelo sobre el mapa."""

    FPS = 60
    MAX_FRAME_TIME = 0.1

    WIDTH = 1280
    HEIGHT = 720

    ENEMY_RADIUS = 8
    TOWER_FOOTPRINT = 40.0
    # Alcance y huella en pixeles del mapa de Tiled (misma unidad que
    # Enemy.progress y Tower.position); el dibujo aplica el escalado.
    # El combate mide la distancia sobre el camino (progress), no en
    # linea recta: la torre llega un poco mas alla del circulo dibujado,
    # por lo que este valor va algo por debajo del radio visual para
    # que ambas cosas coincidan en pantalla.
    TOWER_RANGE_PX = 210.0
    # Segundos entre ataques de las torres colocadas por el jugador.
    TOWER_ATTACK_INTERVAL = 0.6

    RANGE_FILL = (90, 150, 255, 45)
    TOWER_COLOR = (180, 140, 80)
    TOWER_BORDER = (100, 80, 40)
    TOWER_INVALID = (200, 60, 60)
    ENEMY_COLOR = (205, 70, 70)
    ENEMY_BORDER = (95, 25, 25)
    HP_BG = (70, 70, 70)
    HP_FILL = (90, 205, 90)
    TEXT_COLOR = (240, 240, 240)
    TEXT_DIM = (200, 200, 200)
    HUD_BG = (12, 18, 14, 170)
    BACKGROUND = (34, 60, 30)

    def __init__(self, model, tiled_map=None):
        self.model = model
        self.tiled_map = tiled_map
        pygame.init()
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("Tower Defense - Semana 2")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 26)

        self.renderer = None
        self.scale = 1.0
        self.offset_x = 0
        self.offset_y = 0

        if tiled_map is not None:
            self.renderer = TiledMapRenderer(tiled_map)
            map_w = tiled_map.pixel_width
            map_h = tiled_map.pixel_height
            self.scale = min(self.WIDTH / map_w, self.HEIGHT / map_h)
            scaled_w = int(map_w * self.scale)
            scaled_h = int(map_h * self.scale)
            self.offset_x = (self.WIDTH - scaled_w) // 2
            self.offset_y = (self.HEIGHT - scaled_h) // 2

        self.hud_background = self._build_hud_background()
        self._pending_click = None

    # ------------------------------------------------------------------
    # Ciclo (usado por main.py)
    # ------------------------------------------------------------------
    def tick(self):
        """Limita la velocidad del ciclo y devuelve el tiempo del frame. O(1)."""
        return min(self.clock.tick(self.FPS) / 1000.0, self.MAX_FRAME_TIME)

    def process_events(self):
        """Procesa eventos de Pygame. Devuelve False si hay que salir. O(e)."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN and event.key in (
                pygame.K_ESCAPE,
                pygame.K_q,
            ):
                return False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._pending_click = event.pos
        return True

    def close(self):
        """Cierra la ventana y finaliza Pygame. O(1)."""
        pygame.quit()

    # ------------------------------------------------------------------
    # Conversion de coordenadas
    # ------------------------------------------------------------------
    def screen_to_map(self, screen_x, screen_y):
        """Convierte coordenadas de ventana a pixeles del mapa Tiled. O(1)."""
        if self.scale <= 0:
            return 0.0, 0.0
        mx = (screen_x - self.offset_x) / self.scale
        my = (screen_y - self.offset_y) / self.scale
        return mx, my

    def map_to_screen(self, map_x, map_y):
        """Convierte pixeles del mapa Tiled a coordenadas de ventana. O(1)."""
        return (
            self.offset_x + map_x * self.scale,
            self.offset_y + map_y * self.scale,
        )

    def _point_at(self, progress):
        """Punto en pantalla para un progreso del modelo. O(p)."""
        if self.tiled_map is None:
            path_length = max(1e-9, self.model.path_length)
            fraction = min(1.0, max(0.0, progress / path_length))
            x = 40 + fraction * (self.WIDTH - 80)
            return x, self.HEIGHT // 2
        path_length = max(1e-9, self.model.path_length)
        fraction = min(1.0, max(0.0, progress / path_length))
        mx, my = self.tiled_map.point_at_fraction(fraction)
        return self.map_to_screen(mx, my)

    # ------------------------------------------------------------------
    # Colocacion de torres
    # ------------------------------------------------------------------
    def _try_place_tower(self, screen_x, screen_y):
        """Valida y coloca una torre en la posicion del click. O(z + t)."""
        if self.tiled_map is None:
            return
        map_x, map_y = self.screen_to_map(screen_x, screen_y)
        valid, _ = self.model.can_place_tower_at(
            map_x, map_y, self.TOWER_FOOTPRINT, self.tiled_map
        )
        if not valid:
            return
        progress = self.tiled_map.closest_progress_on_path(map_x, map_y)
        self.model.create_tower(
            name="Torre", damage=15, range=self.TOWER_RANGE_PX,
            position=progress,
            map_x=map_x, map_y=map_y,
            footprint=self.TOWER_FOOTPRINT,
            attack_interval=self.TOWER_ATTACK_INTERVAL,
        )

    # ------------------------------------------------------------------
    # Dibujo
    # ------------------------------------------------------------------
    def draw(self):
        """Dibuja el estado completo del modelo. O(n)."""
        if self._pending_click is not None:
            self._try_place_tower(*self._pending_click)
            self._pending_click = None

        self.screen.fill(self.BACKGROUND)

        if self.renderer is not None:
            scaled = pygame.transform.smoothscale(
                self.renderer.base_surface,
                (
                    int(self.tiled_map.pixel_width * self.scale),
                    int(self.tiled_map.pixel_height * self.scale),
                ),
            )
            self.screen.blit(scaled, (self.offset_x, self.offset_y))

        self._draw_towers()
        self._draw_enemies()

        if self.renderer is not None:
            scaled_upper = pygame.transform.smoothscale(
                self.renderer.upper_surface,
                (
                    int(self.tiled_map.pixel_width * self.scale),
                    int(self.tiled_map.pixel_height * self.scale),
                ),
            )
            self.screen.blit(scaled_upper, (self.offset_x, self.offset_y))

        self._draw_hud()
        pygame.display.flip()

    def _build_hud_background(self):
        """Panel semitransparento detras del HUD. O(1)."""
        surface = pygame.Surface((self.WIDTH, 56), pygame.SRCALPHA)
        pygame.draw.rect(surface, self.HUD_BG, surface.get_rect(), border_radius=6)
        return surface

    def _range_radius_px(self, tower):
        """Radio del circulo de alcance en pixeles de pantalla. O(1).

        tower.range esta expresado en pixeles del mapa (misma unidad que
        Enemy.progress), por lo que el radio en pantalla se calcula
        aplicando el escalado del mapa de Tiled. Sin mapa, el progreso
        se dibuja de forma lineal sobre la ventana.
        """
        if self.tiled_map is not None:
            return int(tower.range * self.scale)
        path_length = max(1e-9, self.model.path_length)
        return int(tower.range / path_length * (self.WIDTH - 80))

    def _draw_towers(self):
        """Dibuja cada torre en su posicion del mapa con su alcance."""
        for tower in self.model.towers:
            if tower.map_x is not None and tower.map_y is not None:
                x, y = self.map_to_screen(tower.map_x, tower.map_y)
            else:
                x, y = self._point_at(tower.position)

            radius_px = self._range_radius_px(tower)
            if radius_px > 0:
                range_surface = pygame.Surface(
                    (radius_px * 2, radius_px * 2), pygame.SRCALPHA
                )
                pygame.draw.circle(
                    range_surface, self.RANGE_FILL, (radius_px, radius_px), radius_px
                )
                self.screen.blit(
                    range_surface, (int(x) - radius_px, int(y) - radius_px)
                )

            footprint_px = max(4, int(tower.footprint * self.scale)) \
                if tower.footprint else self.TOWER_FOOTPRINT
            center = (int(x), int(y))
            pygame.draw.circle(self.screen, self.TOWER_COLOR, center, footprint_px)
            pygame.draw.circle(
                self.screen, self.TOWER_BORDER, center, footprint_px, 2
            )

    def _draw_enemies(self):
        """Dibuja los enemigos activos con barra de vida."""
        for enemy in self.model.active_enemies:
            x, y = self._point_at(enemy.progress)
            x, y = int(x), int(y)
            center = (x, y)

            pygame.draw.circle(self.screen, self.ENEMY_COLOR, center, self.ENEMY_RADIUS)
            pygame.draw.circle(
                self.screen, self.ENEMY_BORDER, center, self.ENEMY_RADIUS, 2
            )

            bar_width = 22
            ratio = 0.0
            if enemy.max_hp > 0:
                ratio = max(0.0, min(1.0, enemy.hp / enemy.max_hp))
            bar = pygame.Rect(x - bar_width // 2, y - 20, bar_width, 4)
            pygame.draw.rect(self.screen, self.HP_BG, bar)
            fill = bar.copy()
            fill.width = int(bar_width * ratio)
            if fill.width > 0:
                pygame.draw.rect(self.screen, self.HP_FILL, fill)

    def _draw_hud(self):
        """Dibuja el resumen del estado y la ayuda de controles."""
        self.screen.blit(self.hud_background, (6, 6))
        state_text = (
            f"Pendientes: {self.model.pending_count}   "
            f"Activos: {self.model.active_count}   "
            f"Torres: {len(self.model.towers)}   "
            f"Historial: {self.model.history_count}"
        )
        self.screen.blit(
            self.font.render(state_text, True, self.TEXT_COLOR), (14, 12)
        )
        self.screen.blit(
            self.font.render("Click izq: colocar torre   ESC: salir",
                             True, self.TEXT_DIM), (14, 32)
        )
