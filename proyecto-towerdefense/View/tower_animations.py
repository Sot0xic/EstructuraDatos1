"""
Animaciones PNG de las torres (Semana 4 - 12 variantes).

Integra el pack de animaciones guardado en
assets/torres/animaciones/torres. Hay 12 variantes (torre_01 ...
torre_12), cada una con 50 fotogramas PNG y un metadata.json con el
tamano original, el crop de origen y el tamano final de cada frame.

Todas las variantes comparten la misma estructura temporal, verificada
frame a frame en las 12 carpetas:

    frame 001           -> reposo (la municion asienta en la torre)
    frames 002..015     -> ataque: la torre se tensa y lanza
    frames 016..050     -> el proyectil sale del encuadre y la torre
                           vuelve al reposo (identicos entre si)

La animacion se recorta en el frame de despegue (LAUNCH_END = 15):
a partir del frame 016 el proyectil de los PNG vuela por el aire y
duplicaria al proyectil visual del juego (View.tower_assets), que si
se dirige al enemigo real. Recortada asi, la animacion muestra el
lanzamiento y el proyectil del juego continua el vuelo sin que se
vean dos proyectiles a la vez.

Solo las tres primeras variantes estan cables a los tipos actuales
del juego (KIND_VARIANTS, teclas 1/2/3); las otras nueve quedan
registradas en TOWER_VARIANTS como recursos listos para la futura
tienda, sin leerse del disco hasta que se pidan (carga perezosa).

La logica de combate no cambia: estas imagenes son puramente
visuales, igual que los proyectiles y los impactos de la Semana 3.
"""

import json
import os

import pygame

from View.tower_assets import TOWER_WIDTH_PX

ANIM_DIR = os.path.join("assets", "torres", "animaciones", "torres")
METADATA_PATH = os.path.join(ANIM_DIR, "metadata.json")

# Ultimo frame de la animacion de ataque que se reproduce: el frame
# en el que el proyectil todavía asienta en la torre / acaba de
# despegar. Calibrado visualmente igual para las 12 variantes.
LAUNCH_END = 15

# Segundos por frame de la animacion de ataque. 14 frames (002..015)
# suman ~0.56 s, coherente con el attack_interval de las torres.
FRAME_TIME = 0.04

# Variantes cables a los tipos del modelo (Model.game_model.TOWER_KINDS)
# en el orden de las teclas 1, 2 y 3. Las nueve restantes solo existen
# en TOWER_VARIANTS a la espera de la tienda.
KIND_VARIANTS = {
    "basica": "torre_01",
    "fuego": "torre_02",
    "pesada": "torre_03",
}


def _load_metadata():
    """Lee metadata.json y anade el recorte de ataque. O(v)."""
    with open(METADATA_PATH, "r", encoding="utf-8") as file:
        raw = json.load(file)
    catalog = {}
    for variant, info in raw.items():
        catalog[variant] = {
            "frames": int(info.get("frames", 50)),
            "size": tuple(info.get("size", (0, 0))),
            "launch_end": LAUNCH_END,
            "frame_time": FRAME_TIME,
        }
    return catalog


# Catálogo completo de las 12 variantes (recursos disponibles).
TOWER_VARIANTS = _load_metadata()


class TowerAnimations:
    """Frames de animacion de las torres, precargados y pre-escalados.

    Carga perezosa por variante: por cada torre solo se leen del disco
    el frame de reposo (001) y los frames de ataque hasta el despegue
    (002..LAUNCH_END). Todos se pre-escalan al ancho del cuerpo de una
    torre en pixeles de mapa (TOWER_WIDTH_PX, el mismo tamano que el
    sprite compuesto de la Semana 3) multiplicado por la escala de la
    ventana. O(1) por consulta tras la primera carga de la variante.
    """

    def __init__(self, scale=1.0):
        self.scale = max(1e-6, float(scale))
        self._cache = {}

    def spec(self, variant):
        """Configuracion de una variante del catalogo. O(1)."""
        if variant not in TOWER_VARIANTS:
            raise KeyError(f"Variante de torre desconocida: {variant}")
        return TOWER_VARIANTS[variant]

    def has(self, kind):
        """True si el tipo de torre tiene animacion cables. O(1)."""
        return kind in KIND_VARIANTS

    def _variant_for(self, kind):
        """Variante asignada a un tipo, o KeyError si no tiene. O(1)."""
        if not self.has(kind):
            raise KeyError(f"El tipo de torre '{kind}' no tiene animacion")
        return KIND_VARIANTS[kind]

    @staticmethod
    def _ensure_pygame():
        if not pygame.get_init():
            pygame.init()
        if not pygame.display.get_init():
            pygame.display.set_mode((1, 1))

    def _load_frame(self, variant, index):
        """Carga un fotograma PNG de la variante. O(1) de CPU + disco."""
        self._ensure_pygame()
        filename = f"frame_{index:03d}.png"
        path = os.path.join(ANIM_DIR, variant, filename)
        return pygame.image.load(path).convert_alpha()

    def _fit_width(self, image):
        """Escala image para que su ancho mida TOWER_WIDTH_PX*scale px.

        El cuerpo de los PNG (~165 px de ancho) es el mismo tamano
        relativo que el sprite anterior, por lo que el factor sirve
        tambien para colocarlos sobre el mapa de Tiled.
        """
        width, height = image.get_size()
        target = max(1, int(round(TOWER_WIDTH_PX * self.scale)))
        factor = target / max(1, width)
        size = (
            target,
            max(1, int(round(height * factor))),
        )
        if (width, height) == size:
            return image
        return pygame.transform.smoothscale(image, size)

    def _ensure_loaded(self, variant):
        """Carga y cachea reposo + frames de ataque de la variante. O(f)."""
        if variant in self._cache:
            return self._cache[variant]
        spec = self.spec(variant)
        launch_end = min(spec["launch_end"], spec["frames"])

        idle = self._fit_width(self._load_frame(variant, 1))
        attack = [
            self._fit_width(self._load_frame(variant, index))
            for index in range(2, launch_end + 1)
        ]

        # Ancla = base del cuerpo (la torre toca el punto colocado).
        anchor = (idle.get_width() // 2, idle.get_height() - 1)
        entry = {
            "idle": idle,
            "attack": attack,
            "anchor": anchor,
            "duration": max(1, launch_end - 1) * spec["frame_time"],
        }
        self._cache[variant] = entry
        return entry

    def idle(self, kind):
        """Frame de reposo del tipo, escalado. O(1) tras la carga."""
        entry = self._ensure_loaded(self._variant_for(kind))
        return entry["idle"]

    def anchor(self, kind):
        """Punto del frame alineado con la posicion de la torre. O(1)."""
        entry = self._ensure_loaded(self._variant_for(kind))
        return entry["anchor"]

    def frame_count(self, kind):
        """Numero de frames de la animacion de ataque recortada. O(1)."""
        entry = self._ensure_loaded(self._variant_for(kind))
        return len(entry["attack"])

    def duration(self, kind):
        """Segundos que dura la animacion de ataque completa. O(1)."""
        entry = self._ensure_loaded(self._variant_for(kind))
        return entry["duration"]

    def frame(self, kind, progress):
        """Frame a dibujar para un progreso 0..1 de la animacion. O(1).

        progress <= 0 devuelve el reposo; 0 < progress <= 1 recorre
        los frames de ataque; valores mayores se quedan en el ultimo.
        """
        entry = self._ensure_loaded(self._variant_for(kind))
        attack = entry["attack"]
        if progress <= 0.0 or not attack:
            return entry["idle"]
        index = int(progress * len(attack))
        return attack[min(index, len(attack) - 1)]
