"""
Menu de pausa medieval (menu.md, arreglo.md).

Reutiliza los PNG extraidos de assets/ui/tienda (pack wooden_gui):

    tablero_madera_02.png -> marco de madera con pergamino (panel)
    cartel_pause.png      -> rotulo de titulo «PAUSE»
    boton_resume.png      -> boton «Resume» (reanudar la partida)
    boton_exit.png        -> boton «Exit» (cerrar el juego)

El marco se dibuja centrado sobre una capa oscura semitransparente
para que el mapa siga visible. Dentro del pergamino, y en este orden
vertical, van el rotulo PAUSE, el boton Resume y el boton Exit: el
titulo se situa en la parte superior del marco (panel_rect.top +
margen), nunca en su centro (arreglo.md). Solo existen Resume y
Exit: no hay Settings, Restart ni Main Menu.

El estado de pausa (opened) vive aqui; GameWindow lo consulta con
is_open y lo activa con open()/close()/toggle(). Los metodos
handle_click y hits_resume/hits_exit devuelven la accion del jugador
para que el controlador de la ventana la ejecute.
"""

import os

import pygame

TIENDA_DIR = os.path.join("assets", "ui", "tienda")

FRAME_FILE = "tablero_madera_02.png"
TITLE_FILE = "cartel_pause.png"
RESUME_FILE = "boton_resume.png"
EXIT_FILE = "boton_exit.png"

# Proporciones del pergamino interior dentro del PNG del marco
# (medidas sobre el archivo 1189x893): x0, y0, x1, y1 normalizados.
INTERIOR = (0.143, 0.2016, 0.8562, 0.7973)


class PauseMenu:
    """Menu de pausa centrado: estado, dibujo y clicks. O(1) por frame.

    El rotulo y los dos botones se cargan una sola vez en __init__ y
    sus rectangulos se calculan a partir del area interior del marco
    (interior_rect), no de coordenadas de pantalla: titulo en la
    parte superior, Resume debajo del titulo y Exit debajo de Resume,
    todos centrados en panel_rect.centerx (arreglo.md).
    """

    # Altura del marco escalado; el ancho sale de la proporcion del
    # PNG original 1189x893 y se conserva sin deformar.
    PANEL_H = 560
    # Posicion del titulo: parte superior del marco, no el centro.
    TITLE_TOP_RATIO = 0.29
    # Reparto vertical del pergamino entre los tres elementos.
    TITLE_H_RATIO = 0.32
    GAP1_RATIO = 0.07
    GAP2_RATIO = 0.055
    # Anchos de los botones respecto al pergamino (limitados en
    # altura para conservar su proporcion 676x125).
    RESUME_W_RATIO = 0.46
    RESUME_MAX_H_RATIO = 0.18
    EXIT_W_RATIO = 0.38
    EXIT_MAX_H_RATIO = 0.16

    COLOR_DIM = (10, 14, 10, 150)

    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.opened = False

        self._ensure_pygame()
        # Marco de madera escalado solo por altura (sin deformarlo).
        self.panel = self._fit_height(
            pygame.image.load(os.path.join(TIENDA_DIR, FRAME_FILE)).convert_alpha(),
            self.PANEL_H,
        )
        self.panel_rect = self.panel.get_rect(
            center=(screen_width // 2, screen_height // 2)
        )
        # Area interior (pergamino) donde deben caber los tres
        # elementos sin tocar el borde del marco.
        px0, py0, px1, py1 = INTERIOR
        self.interior_rect = pygame.Rect(
            self.panel_rect.x + int(self.panel_rect.w * px0),
            self.panel_rect.y + int(self.panel_rect.h * py0),
            int(self.panel_rect.w * (px1 - px0)),
            int(self.panel_rect.h * (py1 - py0)),
        )
        interior = self.interior_rect
        cx = self.panel_rect.centerx

        # Titulo PAUSE: relativo al borde superior del marco
        # (panel_rect.top + margen), centrado en panel_rect.centerx.
        self.title_image = self._fit_height(
            pygame.image.load(os.path.join(TIENDA_DIR, TITLE_FILE)).convert_alpha(),
            int(interior.h * self.TITLE_H_RATIO),
        )
        self.title_rect = self.title_image.get_rect(
            midtop=(
                cx,
                self.panel_rect.top
                + int(self.panel_rect.h * self.TITLE_TOP_RATIO),
            )
        )

        self.resume_button = self._fit(
            pygame.image.load(os.path.join(TIENDA_DIR, RESUME_FILE)).convert_alpha(),
            int(interior.w * self.RESUME_W_RATIO),
            int(interior.h * self.RESUME_MAX_H_RATIO),
        )
        self.resume_rect = self.resume_button.get_rect(
            midtop=(cx, self.title_rect.bottom + int(interior.h * self.GAP1_RATIO))
        )

        self.exit_button = self._fit(
            pygame.image.load(os.path.join(TIENDA_DIR, EXIT_FILE)).convert_alpha(),
            int(interior.w * self.EXIT_W_RATIO),
            int(interior.h * self.EXIT_MAX_H_RATIO),
        )
        self.exit_rect = self.exit_button.get_rect(
            midtop=(cx, self.resume_rect.bottom + int(interior.h * self.GAP2_RATIO))
        )

        self.dim_surface = pygame.Surface(
            (screen_width, screen_height), pygame.SRCALPHA
        )
        self.dim_surface.fill(self.COLOR_DIM)

    @staticmethod
    def _ensure_pygame():
        if not pygame.get_init():
            pygame.init()
        if not pygame.display.get_init():
            pygame.display.set_mode((1, 1))

    @staticmethod
    def _fit(image, max_w, max_h):
        """Escala image sin superar la caja (max_w, max_h). O(1)."""
        width, height = image.get_size()
        factor = min(max_w / max(1, width), max_h / max(1, height), 1.0)
        size = (
            max(1, int(round(width * factor))),
            max(1, int(round(height * factor))),
        )
        if (width, height) == size:
            return image
        return pygame.transform.smoothscale(image, size)

    @staticmethod
    def _fit_height(image, target_h):
        """Escala image a una altura concreta conservando la proporcion."""
        width, height = image.get_size()
        factor = target_h / max(1, height)
        size = (
            max(1, int(round(width * factor))),
            max(1, int(round(height * factor))),
        )
        if (width, height) == size:
            return image
        return pygame.transform.smoothscale(image, size)

    # ------------------------------------------------------------------
    # Estado
    # ------------------------------------------------------------------
    @property
    def is_open(self):
        """True mientras el menu de pausa este visible. O(1)."""
        return self.opened

    def open(self):
        """Abre el menu de pausa. O(1)."""
        self.opened = True

    def close(self):
        """Cierra el menu de pausa (equivalente a Resume). O(1)."""
        self.opened = False

    def toggle(self):
        """Abre si esta cerrado y cierra si esta abierto. O(1)."""
        self.opened = not self.opened

    # ------------------------------------------------------------------
    # Interaccion
    # ------------------------------------------------------------------
    def hits_resume(self, pos):
        """True si el click cae sobre el boton Resume. O(1)."""
        return self.resume_rect.collidepoint(pos)

    def hits_exit(self, pos):
        """True si el click cae sobre el boton Exit. O(1)."""
        return self.exit_rect.collidepoint(pos)

    def handle_click(self, pos):
        """Procesa un click con el menu abierto. O(1).

        Devuelve ("resume",) si cierra el menu, ("exit",) si el jugador
        quiere salir del juego o None si el click no hizo nada.
        """
        if not self.opened:
            return None
        if self.hits_resume(pos):
            self.close()
            return ("resume",)
        if self.hits_exit(pos):
            return ("exit",)
        return None

    # ------------------------------------------------------------------
    # Dibujo
    # ------------------------------------------------------------------
    def draw(self, surface):
        """Dibuja fondo oscuro, marco, rotulo y los dos botones. O(1)."""
        if not self.opened:
            return
        surface.blit(self.dim_surface, (0, 0))
        surface.blit(self.panel, self.panel_rect)
        surface.blit(self.title_image, self.title_rect)
        surface.blit(self.resume_button, self.resume_rect)
        surface.blit(self.exit_button, self.exit_rect)
