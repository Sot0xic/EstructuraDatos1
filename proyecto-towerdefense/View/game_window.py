"""
Vista grafica del Tower Defense con Pygame (Semana 2).

Dibuja el estado del modelo en una ventana:

    - fondo y camino horizontal
    - torres con su alcance (circulo translucido)
    - enemigos con barra de vida
    - resumen del estado (HUD)

La ventana solo dibuja el modelo; no lo modifica. El ciclo del juego
(eventos, actualizacion y dibujo) se ejecuta en main.py.
"""

import pygame


class GameWindow:
    """Ventana de Pygame que dibuja el estado del modelo."""

    WIDTH = 900
    HEIGHT = 420
    FPS = 60
    MAX_FRAME_TIME = 0.1

    PATH_Y = 250
    PATH_MARGIN = 60
    PATH_THICKNESS = 36
    ENEMY_RADIUS = 10
    TOWER_SIZE = 26
    TOWER_OFFSET = 64

    BACKGROUND = (24, 32, 26)
    PATH_COLOR = (94, 78, 54)
    START_COLOR = (70, 160, 90)
    BASE_COLOR = (170, 60, 60)
    TOWER_COLOR = (80, 140, 225)
    TOWER_BORDER = (25, 50, 95)
    RANGE_FILL = (90, 150, 255, 45)
    ENEMY_COLOR = (205, 70, 70)
    ENEMY_BORDER = (95, 25, 25)
    HP_BG = (70, 70, 70)
    HP_FILL = (90, 205, 90)
    TEXT_COLOR = (230, 230, 230)
    TEXT_DIM = (170, 170, 170)

    def __init__(self, model):
        self.model = model
        pygame.init()
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("Tower Defense - Semana 2")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 26)
        self.path_x1 = float(self.PATH_MARGIN)
        self.path_x2 = float(self.WIDTH - self.PATH_MARGIN)
        self.px_per_unit = (self.path_x2 - self.path_x1) / max(1.0, model.path_length)

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
        return True

    def close(self):
        """Cierra la ventana y finaliza Pygame. O(1)."""
        pygame.quit()

    # ------------------------------------------------------------------
    # Dibujo
    # ------------------------------------------------------------------
    def draw(self):
        """Dibuja el estado completo del modelo. O(n)."""
        self.screen.fill(self.BACKGROUND)
        self._draw_path()
        self._draw_towers()
        self._draw_enemies()
        self._draw_hud()
        pygame.display.flip()

    def _progress_to_x(self, progress):
        """Convierte el progreso del modelo en una coordenada x. O(1)."""
        if progress <= 0.0:
            return self.path_x1
        if progress >= self.model.path_length:
            return self.path_x2
        return self.path_x1 + progress * self.px_per_unit

    def _draw_path(self):
        """Dibuja el camino, el punto de entrada y la base final."""
        path = pygame.Rect(
            int(self.path_x1),
            self.PATH_Y - self.PATH_THICKNESS // 2,
            int(self.path_x2 - self.path_x1),
            self.PATH_THICKNESS,
        )
        pygame.draw.rect(self.screen, self.PATH_COLOR, path, border_radius=8)

        start = pygame.Rect(int(self.path_x1) - 4, self.PATH_Y - 26, 10, 52)
        pygame.draw.rect(self.screen, self.START_COLOR, start, border_radius=3)

        base = pygame.Rect(int(self.path_x2) - 8, self.PATH_Y - 34, 18, 68)
        pygame.draw.rect(self.screen, self.BASE_COLOR, base, border_radius=3)

    def _draw_towers(self):
        """Dibuja cada torre con el circulo de su alcance sobre el camino."""
        for tower in self.model.towers:
            x = int(self._progress_to_x(tower.position))

            radius = int(tower.range * self.px_per_unit)
            if radius > 0:
                range_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(
                    range_surface, self.RANGE_FILL, (radius, radius), radius
                )
                self.screen.blit(range_surface, (x - radius, self.PATH_Y - radius))

            body = pygame.Rect(0, 0, self.TOWER_SIZE, self.TOWER_SIZE)
            body.center = (x, self.PATH_Y - self.TOWER_OFFSET)
            pygame.draw.rect(
                self.screen, self.TOWER_COLOR, body, border_radius=4
            )
            pygame.draw.rect(
                self.screen, self.TOWER_BORDER, body, 2, border_radius=4
            )

    def _draw_enemies(self):
        """Dibuja los enemigos activos como circulos con barra de vida."""
        for enemy in self.model.active_enemies:
            x = int(self._progress_to_x(enemy.progress))
            center = (x, self.PATH_Y)

            pygame.draw.circle(self.screen, self.ENEMY_COLOR, center, self.ENEMY_RADIUS)
            pygame.draw.circle(
                self.screen, self.ENEMY_BORDER, center, self.ENEMY_RADIUS, 2
            )

            bar_width = 26
            ratio = 0.0
            if enemy.max_hp > 0:
                ratio = max(0.0, min(1.0, enemy.hp / enemy.max_hp))
            bar = pygame.Rect(
                x - bar_width // 2, self.PATH_Y - 24, bar_width, 5
            )
            pygame.draw.rect(self.screen, self.HP_BG, bar)
            fill = bar.copy()
            fill.width = int(bar_width * ratio)
            if fill.width > 0:
                pygame.draw.rect(self.screen, self.HP_FILL, fill)

    def _draw_hud(self):
        """Dibuja el resumen del estado y la ayuda de controles."""
        state_text = (
            f"Pendientes: {self.model.pending_count}   "
            f"Activos: {self.model.active_count}   "
            f"Torres: {len(self.model.towers)}   "
            f"Historial: {self.model.history_count}"
        )
        self.screen.blit(
            self.font.render(state_text, True, self.TEXT_COLOR), (12, 10)
        )
        self.screen.blit(
            self.font.render("ESC para salir", True, self.TEXT_DIM), (12, 34)
        )
