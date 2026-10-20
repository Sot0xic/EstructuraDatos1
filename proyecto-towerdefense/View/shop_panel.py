"""
Tienda emergente de torres (interfaz medieval de madera y pergamino).

Muestra las 12 torres del catalogo View.tower_animations.TOWER_VARIANTS
en una cuadricula de 3 columnas y 4 filas dentro del tablero de madera
con pergamino. Las 12 entradas tienen tipo (kind) en
Model.game_model.TOWER_KINDS (datos.md: basica, fuego, pesada y
torre_04..torre_12) y por tanto son seleccionables; el mecanismo de
candado se reserva para cualquier tarjeta que en el futuro se publique
sin kind asociado.

Reutiliza los PNG extraidos en la fase anterior de assets/ui/tienda:

    tablero_madera_01.png -> panel de la tienda (marco de madera y
                             pergamino interior como fondo)
    boton_atras.png       -> boton de cierre de la tienda
    boton_menu.png        -> boton «Tienda» del HUD en la pantalla
                             principal
    <variante>/frame_001.png de assets/torres/animaciones/torres
                          -> imagen real de cada torre en su reposo

Los marcos de las tarjetas, el candado de las torres sin kind y todos
los textos se dibujan con Pygame, porque el pack de GUI no tiene marcos
genericos limpios para tarjetas (los botones llevan texto o numeros
pegados).

Economia (actualizacion.md): cada tarjeta muestra su precio en
estrellas debajo de la imagen de la torre, renderizado con la fuente
de sprites de View.sprite_font (estrella dorada + digitos del
spritesheet de madera). Los precios vienen centralizados en
Model.game_model.SHOP_TOWER_PRICES (unica fuente); aqui solo se
asocian a la tarjeta. Una torre jugable con saldo insuficiente se
distingue con un velo rojo y su click no inicia la compra (devuelve
("insufficient", kind) sin cerrar el panel).
"""

import os

import pygame

from Model.game_model import SHOP_TOWER_PRICES, TOWER_KINDS
from View.sprite_font import SpriteFont

TIENDA_DIR = os.path.join("assets", "ui", "tienda")
ANIM_DIR = os.path.join("assets", "torres", "animaciones", "torres")

PANEL_FILE = "tablero_madera_01.png"
CLOSE_FILE = "boton_atras.png"
OPENER_FILE = "boton_menu.png"

# Proporciones del pergamino interior dentro del PNG del tablero
# (medidas sobre el archivo 1190x893): x0, y0, x1, y1 normalizados.
PERGAMINO = (0.1445, 0.206, 0.8538, 0.7973)

# Catalogo de la tienda: las 12 entradas asocian su variante de
# sprites con el kind del modelo (datos.md), lo que las hace
# seleccionables y fija sus estadisticas de combate en TOWER_KINDS.
# El precio de cada variante viene del modelo (SHOP_TOWER_PRICES, la
# unica fuente de precios): aqui solo se asocia a la tarjeta para
# dibujarlo bajo la imagen de la torre. Los nombres visibles salen
# de TOWER_KINDS[kind]["name"] (tower_name).
SHOP_TOWERS = (
    {"variant": "torre_01", "kind": "basica", "price": SHOP_TOWER_PRICES[0]},
    {"variant": "torre_02", "kind": "fuego", "price": SHOP_TOWER_PRICES[1]},
    {"variant": "torre_03", "kind": "pesada", "price": SHOP_TOWER_PRICES[2]},
    {"variant": "torre_04", "kind": "torre_04", "price": SHOP_TOWER_PRICES[3]},
    {"variant": "torre_05", "kind": "torre_05", "price": SHOP_TOWER_PRICES[4]},
    {"variant": "torre_06", "kind": "torre_06", "price": SHOP_TOWER_PRICES[5]},
    {"variant": "torre_07", "kind": "torre_07", "price": SHOP_TOWER_PRICES[6]},
    {"variant": "torre_08", "kind": "torre_08", "price": SHOP_TOWER_PRICES[7]},
    {"variant": "torre_09", "kind": "torre_09", "price": SHOP_TOWER_PRICES[8]},
    {"variant": "torre_10", "kind": "torre_10", "price": SHOP_TOWER_PRICES[9]},
    {"variant": "torre_11", "kind": "torre_11", "price": SHOP_TOWER_PRICES[10]},
    {"variant": "torre_12", "kind": "torre_12", "price": SHOP_TOWER_PRICES[11]},
)


class ShopPanel:
    """Tienda emergente: estado, disposicion, dibujo y clicks. O(1) por frame.

    La cuadrifica 3x4 se calcula una sola vez contra la region de
    pergamino del tablero escalado; las imagenes de las torres se
    cargan de forma perezosa por variante y se cachean ya ajustadas al
    tamano de la tarjeta.
    """

    COLS = 3
    ROWS = 4

    # Altura del panel escalado (el ancho sale de la proporcion del PNG).
    PANEL_H = 710

    CARD_W = 212
    CARD_H = 98
    GAP_X = 12
    GAP_Y = 8
    SPRITE_MAX_W = 88
    # El sprite deja una franja inferior para el precio en estrellas
    # (star + digitos de View.sprite_font) bajo la imagen de la torre.
    SPRITE_MAX_H = 70

    CLOSE_W = 74
    CLOSE_H = 41
    OPENER_W = 150
    OPENER_H = 83

    COLOR_CARD = (236, 223, 186)
    COLOR_CARD_EDGE = (140, 110, 70)
    COLOR_CARD_BORDER = (86, 58, 28)
    COLOR_HOVER = (198, 150, 58)
    COLOR_NAME = (58, 38, 16)
    COLOR_TITLE = (240, 225, 190)
    COLOR_TITLE_SHADOW = (40, 25, 10)
    COLOR_DIM = (10, 14, 10, 110)
    COLOR_LOCKED_OVERLAY = (18, 12, 8, 145)
    COLOR_LOCKED_TEXT = (216, 172, 150)
    COLOR_PADLOCK = (232, 214, 168)
    COLOR_HINT = (226, 210, 170)
    # Velo y borde de las torres jugables que no se pueden pagar aun.
    COLOR_UNAFFORD_OVERLAY = (120, 22, 18, 110)
    COLOR_UNAFFORD_BORDER = (168, 52, 40)

    NAME_SIZES = (24, 22, 20, 18, 16)

    # Precio en estrellas: estrella dorada + digitos del spritesheet.
    PRICE_GLYPH_H = 16
    PRICE_SPACING = 1
    PRICE_GAP = 2

    def __init__(self, screen_width, screen_height, model=None):
        self.screen_width = screen_width
        self.screen_height = screen_height
        # Modelo opcional: aporta el saldo para distinguir las torres
        # pagables de las que aun no se pueden comprar. Sin modelo (por
        # ejemplo en pruebas del catalogo) todo se considera pagable.
        self.model = model
        self.opened = False

        self._sprite_cache = {}
        self._name_cache = {}
        self._ensure_pygame()
        self.sprite_font = SpriteFont()

        self.panel = self._fit_height(
            pygame.image.load(os.path.join(TIENDA_DIR, PANEL_FILE)).convert_alpha(),
            self.PANEL_H,
        )
        self.panel_rect = self.panel.get_rect(
            center=(screen_width // 2, screen_height // 2)
        )
        self.close_button = self._fit(
            pygame.image.load(os.path.join(TIENDA_DIR, CLOSE_FILE)).convert_alpha(),
            self.CLOSE_W,
            self.CLOSE_H,
        )
        self.close_rect = self.close_button.get_rect(
            topleft=(self.panel_rect.right - 122, self.panel_rect.top + 28)
        )
        self.opener = self._fit(
            pygame.image.load(os.path.join(TIENDA_DIR, OPENER_FILE)).convert_alpha(),
            self.OPENER_W,
            self.OPENER_H,
        )
        # Colocado por encima del HUD (56 px) en la esquina inferior
        # derecha, para no quedar tapado por la barra de estado.
        self.opener_rect = self.opener.get_rect(
            topright=(screen_width - 14, screen_height - self.OPENER_H - 14)
        )

        self.dim_surface = pygame.Surface(
            (screen_width, screen_height), pygame.SRCALPHA
        )
        self.dim_surface.fill(self.COLOR_DIM)

        self.font_title = pygame.font.Font(None, 44)
        self.font_name = pygame.font.Font(None, 24)
        self.font_small = pygame.font.Font(None, 20)
        self.font_button = pygame.font.Font(None, 28)
        self.font_hint = pygame.font.Font(None, 22)

        self.cards = self._build_layout()

    # ------------------------------------------------------------------
    # Utilidades de imagen
    # ------------------------------------------------------------------
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

    def _fit_height(self, image, target_h):
        """Escala image a una altura concreta conservando la proporcion."""
        width, height = image.get_size()
        factor = target_h / max(1, height)
        size = (max(1, int(round(width * factor))), max(1, int(round(height * factor))))
        if (width, height) == size:
            return image
        return pygame.transform.smoothscale(image, size)

    # ------------------------------------------------------------------
    # Disposicion
    # ------------------------------------------------------------------
    def _build_layout(self):
        """Rectangulos de las 12 tarjetas dentro del pergamino. O(1)."""
        px0, py0, px1, py1 = PERGAMINO
        inner = pygame.Rect(
            self.panel_rect.x + int(self.panel_rect.w * px0),
            self.panel_rect.y + int(self.panel_rect.h * py0),
            int(self.panel_rect.w * (px1 - px0)),
            int(self.panel_rect.h * (py1 - py0)),
        )
        total_w = self.COLS * self.CARD_W + (self.COLS - 1) * self.GAP_X
        total_h = self.ROWS * self.CARD_H + (self.ROWS - 1) * self.GAP_Y
        start_x = inner.x + (inner.w - total_w) // 2
        start_y = inner.y + (inner.h - total_h) // 2

        cards = []
        for index, entry in enumerate(SHOP_TOWERS):
            row, col = divmod(index, self.COLS)
            rect = pygame.Rect(
                start_x + col * (self.CARD_W + self.GAP_X),
                start_y + row * (self.CARD_H + self.GAP_Y),
                self.CARD_W,
                self.CARD_H,
            )
            cards.append({"entry": entry, "rect": rect})
        return cards

    @staticmethod
    def tower_name(index):
        """Nombre visible de la tarjeta index. O(1)."""
        entry = SHOP_TOWERS[index]
        kind = entry.get("kind")
        if kind is not None:
            return TOWER_KINDS[kind]["name"]
        return entry["name"]

    @staticmethod
    def tower_locked(index):
        """True si la torre de la tarjeta index esta bloqueada. O(1)."""
        return SHOP_TOWERS[index].get("kind") is None

    @staticmethod
    def tower_price(index):
        """Precio en estrellas de la tarjeta index (SHOP_TOWER_PRICES). O(1)."""
        return SHOP_TOWERS[index]["price"]

    def tower_affordable(self, index):
        """True si el saldo alcanza para pagar la torre de la tarjeta. O(1).

        Sin modelo asociado (pruebas del catalogo) se considera pagable.
        Las torres bloqueadas no son pagables (no se pueden comprar).
        """
        if self.tower_locked(index):
            return False
        if self.model is None:
            return True
        return self.model.stars >= self.tower_price(index)

    # ------------------------------------------------------------------
    # Estado
    # ------------------------------------------------------------------
    @property
    def is_open(self):
        """True mientras la tienda este visible. O(1)."""
        return self.opened

    def open(self):
        """Abre la tienda. O(1)."""
        self.opened = True

    def close(self):
        """Cierra la tienda. O(1)."""
        self.opened = False

    # ------------------------------------------------------------------
    # Interaccion
    # ------------------------------------------------------------------
    def hits_opener(self, pos):
        """True si el click cae sobre el boton «Tienda». O(1)."""
        return self.opener_rect.collidepoint(pos)

    def handle_click(self, pos):
        """Procesa un click con la tienda abierta. O(1).

        Devuelve ("close",) si cierra, ("select", kind) si el jugador
        elige una torre disponible y asequible (entonces cierra el
        panel para armar su colocacion), ("insufficient", kind) si la
        torre es jugable pero el saldo no alcanza (el panel queda
        abierto y no se inicia la compra) o None si el click no hizo
        nada (fuera del panel, tarjeta bloqueada, etc.).
        """
        if not self.opened:
            return None
        if self.close_rect.collidepoint(pos):
            self.close()
            return ("close",)
        for index, card in enumerate(self.cards):
            if not card["rect"].collidepoint(pos):
                continue
            kind = card["entry"].get("kind")
            if kind is None:
                return None
            if not self.tower_affordable(index):
                return ("insufficient", kind)
            self.close()
            return ("select", kind)
        return None

    # ------------------------------------------------------------------
    # Dibujo
    # ------------------------------------------------------------------
    def _sprite(self, variant):
        """Frame de reposo de la variante ajustado a la tarjeta. O(1)."""
        if variant not in self._sprite_cache:
            path = os.path.join(ANIM_DIR, variant, "frame_001.png")
            image = pygame.image.load(path).convert_alpha()
            self._sprite_cache[variant] = self._fit(
                image, self.SPRITE_MAX_W, self.SPRITE_MAX_H
            )
        return self._sprite_cache[variant]

    def _name_image(self, text):
        """Texto del nombre reducido hasta caber en la tarjeta. O(t)."""
        if text in self._name_cache:
            return self._name_cache[text]
        max_w = self.CARD_W - 108
        image = None
        for size in self.NAME_SIZES:
            font = pygame.font.Font(None, size)
            image = font.render(text, True, self.COLOR_NAME)
            if image.get_width() <= max_w:
                break
        self._name_cache[text] = image
        return image

    def _draw_padlock(self, surface, center):
        """Candado dibujado con primitivas sobre una tarjeta. O(1)."""
        cx, cy = center
        body = pygame.Rect(0, 0, 28, 21)
        body.center = (cx, cy + 5)
        pygame.draw.rect(surface, self.COLOR_PADLOCK, body, border_radius=4)
        shackle = pygame.Rect(0, 0, 18, 20)
        shackle.center = (cx, cy - 8)
        pygame.draw.arc(surface, self.COLOR_PADLOCK, shackle, 3.14159, 6.28318, 4)
        pygame.draw.circle(surface, self.COLOR_NAME, (cx, cy + 14), 3)

    def _draw_price(self, surface, index, center_x, y):
        """Precio en estrellas bajo la imagen de la torre. O(d).

        Dibuja la estrella dorada del spritesheet (SpriteFont.star)
        seguida del precio en digitos de la misma fuente. Se usa en
        todas las tarjetas, tambien en las bloqueadas, para que el
        jugador conozca su coste aun sin poder comprarla.
        """
        price = self.tower_price(index)
        star = self.sprite_font.star(self.PRICE_GLYPH_H)
        digits = str(price)
        text_w, _ = self.sprite_font.measure(
            digits, self.PRICE_GLYPH_H, self.PRICE_SPACING
        )
        total_w = star.get_width() + self.PRICE_GAP + text_w
        x = center_x - total_w // 2
        surface.blit(star, (x, y))
        self.sprite_font.render(
            surface,
            digits,
            (x + star.get_width() + self.PRICE_GAP, y),
            self.PRICE_GLYPH_H,
            self.PRICE_SPACING,
        )

    def _draw_card(self, surface, index, mouse_pos):
        """Dibuja una tarjeta del catalogo. O(1)."""
        card = self.cards[index]
        rect = card["rect"]
        locked = self.tower_locked(index)
        affordable = self.tower_affordable(index)
        # Solo las torres jugables y pagables se resaltan al pasar el
        # raton: las bloqueadas y las que no se pueden pagar aun no
        # deben invitar a hacer click.
        hovered = (not locked) and affordable and rect.collidepoint(mouse_pos)

        pygame.draw.rect(surface, self.COLOR_CARD, rect, border_radius=8)
        pygame.draw.rect(
            surface, self.COLOR_CARD_EDGE, rect, width=1, border_radius=8
        )
        border = 3 if hovered else 2
        if not locked and not affordable:
            border_color = self.COLOR_UNAFFORD_BORDER
        elif hovered:
            border_color = self.COLOR_HOVER
        else:
            border_color = self.COLOR_CARD_BORDER
        pygame.draw.rect(
            surface, border_color, rect, width=border, border_radius=8
        )

        sprite = self._sprite(card["entry"]["variant"])
        sprite_rect = sprite.get_rect(
            midbottom=(rect.x + 8 + self.SPRITE_MAX_W // 2, rect.bottom - 24)
        )
        surface.blit(sprite, sprite_rect)

        name = self._name_image(self.tower_name(index))
        column = pygame.Rect(rect.x + 100, rect.y, rect.w - 108, rect.h)
        if locked:
            name_rect = name.get_rect(center=(column.centerx, column.centery - 10))
            surface.blit(name, name_rect)
            lock_text = self.font_small.render("Bloqueada", True, self.COLOR_LOCKED_TEXT)
            surface.blit(
                lock_text,
                lock_text.get_rect(center=(column.centerx, column.centery + 18)),
            )
            overlay = pygame.Surface(rect.size, pygame.SRCALPHA)
            overlay.fill(self.COLOR_LOCKED_OVERLAY)
            surface.blit(overlay, rect.topleft)
            # Candado en la esquina superior izquierda para no tapar la
            # silueta de la torre.
            self._draw_padlock(surface, (rect.x + 22, rect.y + 20))
        else:
            surface.blit(name, name.get_rect(center=column.center))
            if not affordable:
                # Velo rojizo: la torre existe y se puede elegir en el
                # futuro, pero el saldo actual no llega a su precio.
                overlay = pygame.Surface(rect.size, pygame.SRCALPHA)
                overlay.fill(self.COLOR_UNAFFORD_OVERLAY)
                surface.blit(overlay, rect.topleft)

        # Precio bajo la imagen de la torre, por encima de los velos
        # para que siga legible en tarjetas bloqueadas o no pagables.
        self._draw_price(
            surface, index, rect.x + 8 + self.SPRITE_MAX_W // 2, rect.bottom - 20
        )

    def draw(self, surface):
        """Dibuja el fondo oscurecido, el panel y las tarjetas. O(n)."""
        if not self.opened:
            return
        surface.blit(self.dim_surface, (0, 0))
        surface.blit(self.panel, self.panel_rect)

        title = self.font_title.render("TIENDA DE TORRES", True, self.COLOR_TITLE)
        shadow = self.font_title.render("TIENDA DE TORRES", True, self.COLOR_TITLE_SHADOW)
        title_rect = title.get_rect(
            center=(self.panel_rect.centerx, self.panel_rect.y + 44)
        )
        surface.blit(shadow, (title_rect.x + 2, title_rect.y + 2))
        surface.blit(title, title_rect)

        hint = self.font_hint.render("ESC: cerrar", True, self.COLOR_HINT)
        surface.blit(
            hint,
            hint.get_rect(
                center=(self.panel_rect.centerx, self.panel_rect.bottom - 34)
            ),
        )

        mouse_pos = pygame.mouse.get_pos()
        for index in range(len(self.cards)):
            self._draw_card(surface, index, mouse_pos)

        surface.blit(self.close_button, self.close_rect)

    def draw_opener(self, surface):
        """Dibuja el boton «Tienda» de la pantalla principal. O(1)."""
        surface.blit(self.opener, self.opener_rect)
        # Rotulo centrado bajo el icono, con contorno oscuro para que se
        # lea sobre la madera sin depender del color del texto.
        label = self.font_button.render("Tienda", True, self.COLOR_TITLE)
        center = (self.opener_rect.centerx, self.opener_rect.bottom - 18)
        label_rect = label.get_rect(center=center)
        pygame.draw.rect(
            surface,
            (30, 18, 8),
            label_rect.inflate(10, 6),
            border_radius=5,
        )
        surface.blit(label, label_rect)
