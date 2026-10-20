"""
Render de numeros e iconos con sprites del PNG (fuente de madera).

Reutiliza los recortes de assets/ui/wood_fonts/extraidos, generados a
partir del spritesheet UI_Font_A.png sin modificar el archivo fuente:

    - los digitos 0..9 (View/sprite_font.py) para dibujar cantidades
    - la estrella dorada (SpriteFont.STAR_GOLD) como icono de moneda

Los recortes conservan la transparencia RGBA original y se escalan en
pantalla con smoothscale sobre copias cacheadas: el spritesheet de
origen nunca se reescribe.

La distribucion real del spritesheet se verifico antes de recortar
(no hay celdas de tamano uniforme): los digitos ocupan la fila 0 y la
estrella dorada la fila 14, columna 15. Cada recorte se limito a su
bounding box real de contenido, por lo que no incluye fragmentos de
iconos vecinos.
"""

import os

import pygame

EXTRACT_DIR = os.path.join("assets", "ui", "wood_fonts", "extraidos")

# Digito -> nombre del PNG recortado.
DIGIT_FILES = {d: f"digito_{d}.png" for d in range(10)}


class SpriteFont:
    """Sprites de digitos e iconos, escalables y cacheados.

    Los PNG se cargan una sola vez en tamano nativo y cada tamano
    pedido se cachea como copia escalada; dos instancias pueden pedir
    alturas distintas sin interferirse y sin tocar el archivo fuente.
    """

    STAR_GOLD = "estrella_dorada.png"

    def __init__(self):
        self._native = {}
        self._scaled = {}

    @staticmethod
    def _ensure_display():
        if not pygame.get_init():
            pygame.init()
        if not pygame.display.get_init():
            pygame.display.set_mode((1, 1))

    def _load_native(self, filename):
        """Carga el PNG en tamano nativo, la primera vez. O(1) tras cachear."""
        if filename not in self._native:
            self._ensure_display()
            path = os.path.join(EXTRACT_DIR, filename)
            self._native[filename] = pygame.image.load(path).convert_alpha()
        return self._native[filename]

    def glyph(self, filename, height=None):
        """Sprite escalado a `height` px de alto (nativo si es None).

        Devuelve una superficie cacheada; el llamante no debe mutarla.
        O(1) tras la primera carga de ese tamano.
        """
        native = self._load_native(filename)
        if height is None:
            return native
        key = (filename, int(height))
        if key not in self._scaled:
            factor = height / native.get_height()
            size = (
                max(1, round(native.get_width() * factor)),
                max(1, round(native.get_height() * factor)),
            )
            self._scaled[key] = pygame.transform.smoothscale(native, size)
        return self._scaled[key]

    def digit(self, value, height=None):
        """Sprite del digito `value` (0..9) escalado. O(1)."""
        return self.glyph(DIGIT_FILES[int(value) % 10], height)

    def star(self, height=None):
        """Icono de estrella dorada (moneda) escalado. O(1)."""
        return self.glyph(self.STAR_GOLD, height)

    def measure(self, text, height=None, spacing=1):
        """Ancho total y alto maximo de los digitos de `text`. O(d).

        `spacing` son los pixeles horizontales entre glifos. Los
        caracteres que no son digitos se ignoran.
        """
        width = 0
        max_h = 0
        count = 0
        for char in text:
            glyph = self._glyph_for_char(char, height)
            if glyph is None:
                continue
            width += glyph.get_width()
            max_h = max(max_h, glyph.get_height())
            count += 1
        if count > 1:
            width += spacing * (count - 1)
        return width, max_h

    def _glyph_for_char(self, char, height):
        """Sprite para un caracter de texto, o None si no hay glifo. O(1).

        El spritesheet no incluye glifos de puntuacion, asi que solo
        los digitos se renderizan; coma y punto se ignoran.
        """
        if char.isdigit():
            return self.digit(char, height)
        return None

    def render(self, surface, text, pos, height=None, spacing=1,
               align="left"):
        """Dibuja los digitos de `text` con sprites y devuelve su rect. O(d).

        Solo se renderizan digitos; coma, punto y demas caracteres se
        ignoran (el spritesheet no trae esos glifos). `align` puede ser
        "left" o "right": con "right" el ultimo digito termina en `pos`
        en vez de empezar en el.
        """
        glyphs = []
        for char in text:
            glyph = self._glyph_for_char(char, height)
            if glyph is not None:
                glyphs.append(glyph)

        total_w = sum(g.get_width() for g in glyphs)
        if len(glyphs) > 1:
            total_w += spacing * (len(glyphs) - 1)
        total_h = max((g.get_height() for g in glyphs), default=0)

        x, y = pos
        if align == "right":
            x -= total_w

        cursor = x
        for glyph in glyphs:
            surface.blit(glyph, (cursor, y))
            cursor += glyph.get_width() + spacing

        return pygame.Rect(x, y, total_w, total_h)
