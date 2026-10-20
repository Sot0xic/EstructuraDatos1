"""
Sprites de torres, proyectiles e impactos (Semana 3).

Integra el pack stone-tower-game-assets guardado en
assets/torres/PNG. Cada tipo de torre (Model.game_model.TOWER_KINDS)
tiene asociados en TOWER_ASSETS:

    body          -> imagen del cuerpo de la torre en reposo
    body_firing   -> variante del cuerpo durante el disparo
                     (brillo en basica, llama alta en fuego);
                     None si el tipo no tiene variante
    shadow        -> sombra compuesta debajo del cuerpo
    projectile    -> proyectil visible disparado por la torre
    impact        -> frames del efecto de impacto, en orden
    hover         -> munición flotante sobre la torre en reposo
                     (mismo pack, estilo de los GIFs de ejemplo)
    hover_height  -> altura de ese flote en pixeles de mapa
                     sobre la base de la torre

Las tres torres de prueba (basica, fuego y pesada) lanzan rocas: las
animaciones PNG de View.tower_animations las muestran como catapultas,
asi que sus proyectiles e impactos usan las rocas del pack. El sprite
de proyectil de fuego se conserva en LEGACY_FIRE_PROJECTILE para una
torre de fuego futura.

Los tamanos se expresan en pixeles del mapa de Tiled (misma unidad
que Tower.map_x/map_y y Enemy.progress) y se pre-escalan con la
escala de la ventana; la velocidad del proyectil va en pixeles de
mapa por segundo.

El daño NO se aplica aqui: los proyectiles y los impactos son
puramente visuales; la logica de combate sigue en el modelo.
"""

import os

import pygame

ASSET_DIR = os.path.join("assets", "torres", "PNG")

# Factor de tamano visual de las torres. 1.0 = tamano inicial de la
# Semana 3 (130 px de ancho en el mapa -> cuerpo visible de ~52x56 px
# en la ventana de 1280x720). Con 1.35 el cuerpo visible mide ~70x76
# px, proporcional a todos los frames de animacion y al sprite de
# fallback. Ajustar unicamente este numero cambia el tamano de las
# torres sin tocar los PNG ni la logica del juego.
TOWER_SIZE_FACTOR = 1.35

# Ancho compuesto (sombra + cuerpo) de una torre en pixeles de mapa.
TOWER_WIDTH_PX = 130.0 * TOWER_SIZE_FACTOR

# Proyectil de cada variante de torre (las 12 del catalogo de
# View.tower_animations), con el modo de rotacion del sprite en vuelo:
#
#   None   -> roca simple, el sprite vuela sin rotar (torres 01-03)
#   "fall" -> 35.png esta dibujado en orientacion de caida (la llama
#             apunta hacia abajo): se orienta hacia la direccion real
#             del movimiento y va girando hacia abajo durante el
#             vuelo para representar la caida (torres 04-06)
#   "spin" -> gira sobre si mismo mientras vuela (torres 10-12)
#
# Distribucion exacta segun torres.md:
#   torre_01-03 -> 40.png (roca, conservado de la Semana 3)
#   torre_04-06 -> 35.png (llama en caida)
#   torre_07-09 -> 29.png (proyectil pesado)
#   torre_10-12 -> 45.png (proyectil orbitando)
VARIANT_PROJECTILES = {
    "torre_01": {"file": "40.png", "rotate": None},
    "torre_02": {"file": "40.png", "rotate": None},
    "torre_03": {"file": "40.png", "rotate": None},
    "torre_04": {"file": "35.png", "rotate": "fall"},
    "torre_05": {"file": "35.png", "rotate": "fall"},
    "torre_06": {"file": "35.png", "rotate": "fall"},
    "torre_07": {"file": "29.png", "rotate": None},
    "torre_08": {"file": "29.png", "rotate": None},
    "torre_09": {"file": "29.png", "rotate": None},
    "torre_10": {"file": "45.png", "rotate": "spin"},
    "torre_11": {"file": "45.png", "rotate": "spin"},
    "torre_12": {"file": "45.png", "rotate": "spin"},
}

TOWER_ASSETS = {
    # Las tres torres de prueba lanzan la roca 40.png de la tabla
    # VARIANT_PROJECTILES (catapultas de las variantes torre_01-03).
    "basica": {
        "body": "3.png",
        "body_firing": "7.png",
        "shadow": "8.png",
        "projectile": VARIANT_PROJECTILES["torre_01"]["file"],
        "impact": ["41.png", "42.png", "43.png", "44.png"],
        "hover": VARIANT_PROJECTILES["torre_01"]["file"],
        "hover_height": 170.0,
        "projectile_size": 38.0,
        "hover_size": 30.0,
        "impact_size": 85.0,
        "projectile_speed": 620.0,
        "impact_frame_time": 0.08,
        "rotate": VARIANT_PROJECTILES["torre_01"]["rotate"],
    },
    # La torre "fuego" es la catapulta de la variante torre_02: lanza
    # rocas, no llamas. Conserva su danio, cadencia y velocidad de
    # proyectil.
    "fuego": {
        "body": "13.png",
        "body_firing": "14.png",
        "shadow": "10.png",
        "projectile": VARIANT_PROJECTILES["torre_02"]["file"],
        "impact": ["41.png", "42.png", "43.png", "44.png"],
        "hover": VARIANT_PROJECTILES["torre_02"]["file"],
        "hover_height": 180.0,
        "projectile_size": 38.0,
        "hover_size": 30.0,
        "impact_size": 85.0,
        "projectile_speed": 520.0,
        "impact_frame_time": 0.06,
        "rotate": VARIANT_PROJECTILES["torre_02"]["rotate"],
    },
    "pesada": {
        "body": "25.png",
        "body_firing": None,
        "shadow": "8.png",
        "projectile": VARIANT_PROJECTILES["torre_03"]["file"],
        "impact": ["30.png", "31.png", "32.png", "33.png", "34.png"],
        "hover": VARIANT_PROJECTILES["torre_03"]["file"],
        "hover_height": 155.0,
        "projectile_size": 38.0,
        "hover_size": 30.0,
        "impact_size": 110.0,
        "projectile_speed": 430.0,
        "impact_frame_time": 0.07,
        "rotate": VARIANT_PROJECTILES["torre_03"]["rotate"],
    },
    # Las nueve torres adicionales (torre_04..torre_12) estan cables
    # a los proyectiles de VARIANT_PROJECTILES segun torres.md: el
    # cuerpo y la sombra se dibujan con los frames de animacion de
    # View.tower_animations (KIND_VARIANTS), por lo que aqui solo se
    # configuran los efectos de vuelo e impacto.
    "torre_04": {
        "body": "35.png",
        "body_firing": None,
        "shadow": "8.png",
        "projectile": VARIANT_PROJECTILES["torre_04"]["file"],
        "impact": ["54.png", "55.png", "56.png", "57.png", "58.png", "59.png", "60.png", "61.png"],
        "hover": VARIANT_PROJECTILES["torre_04"]["file"],
        "hover_height": 160.0,
        "projectile_size": 54.0,
        "hover_size": 40.0,
        "impact_size": 145.0,
        "projectile_speed": 580.0,
        "impact_frame_time": 0.06,
        "rotate": VARIANT_PROJECTILES["torre_04"]["rotate"],
    },
    "torre_05": {
        "body": "35.png",
        "body_firing": None,
        "shadow": "8.png",
        "projectile": VARIANT_PROJECTILES["torre_05"]["file"],
        "impact": ["54.png", "55.png", "56.png", "57.png", "58.png", "59.png", "60.png", "61.png"],
        "hover": VARIANT_PROJECTILES["torre_05"]["file"],
        "hover_height": 160.0,
        "projectile_size": 54.0,
        "hover_size": 40.0,
        "impact_size": 145.0,
        "projectile_speed": 580.0,
        "impact_frame_time": 0.06,
        "rotate": VARIANT_PROJECTILES["torre_05"]["rotate"],
    },
    "torre_06": {
        "body": "35.png",
        "body_firing": None,
        "shadow": "8.png",
        "projectile": VARIANT_PROJECTILES["torre_06"]["file"],
        "impact": ["54.png", "55.png", "56.png", "57.png", "58.png", "59.png", "60.png", "61.png"],
        "hover": VARIANT_PROJECTILES["torre_06"]["file"],
        "hover_height": 160.0,
        "projectile_size": 54.0,
        "hover_size": 40.0,
        "impact_size": 145.0,
        "projectile_speed": 580.0,
        "impact_frame_time": 0.06,
        "rotate": VARIANT_PROJECTILES["torre_06"]["rotate"],
    },
    "torre_07": {
        "body": "29.png",
        "body_firing": None,
        "shadow": "8.png",
        "projectile": VARIANT_PROJECTILES["torre_07"]["file"],
        "impact": ["30.png", "31.png", "32.png", "33.png", "34.png"],
        "hover": VARIANT_PROJECTILES["torre_07"]["file"],
        "hover_height": 150.0,
        "projectile_size": 42.0,
        "hover_size": 32.0,
        "impact_size": 110.0,
        "projectile_speed": 500.0,
        "impact_frame_time": 0.07,
        "rotate": VARIANT_PROJECTILES["torre_07"]["rotate"],
    },
    "torre_08": {
        "body": "29.png",
        "body_firing": None,
        "shadow": "8.png",
        "projectile": VARIANT_PROJECTILES["torre_08"]["file"],
        "impact": ["30.png", "31.png", "32.png", "33.png", "34.png"],
        "hover": VARIANT_PROJECTILES["torre_08"]["file"],
        "hover_height": 150.0,
        "projectile_size": 42.0,
        "hover_size": 32.0,
        "impact_size": 110.0,
        "projectile_speed": 500.0,
        "impact_frame_time": 0.07,
        "rotate": VARIANT_PROJECTILES["torre_08"]["rotate"],
    },
    "torre_09": {
        "body": "29.png",
        "body_firing": None,
        "shadow": "8.png",
        "projectile": VARIANT_PROJECTILES["torre_09"]["file"],
        "impact": ["30.png", "31.png", "32.png", "33.png", "34.png"],
        "hover": VARIANT_PROJECTILES["torre_09"]["file"],
        "hover_height": 150.0,
        "projectile_size": 42.0,
        "hover_size": 32.0,
        "impact_size": 110.0,
        "projectile_speed": 500.0,
        "impact_frame_time": 0.07,
        "rotate": VARIANT_PROJECTILES["torre_09"]["rotate"],
    },
    "torre_10": {
        "body": "45.png",
        "body_firing": None,
        "shadow": "8.png",
        "projectile": VARIANT_PROJECTILES["torre_10"]["file"],
        "impact": ["46.png", "47.png", "48.png", "49.png", "50.png"],
        "hover": VARIANT_PROJECTILES["torre_10"]["file"],
        "hover_height": 155.0,
        "projectile_size": 40.0,
        "hover_size": 30.0,
        "impact_size": 105.0,
        "projectile_speed": 480.0,
        "impact_frame_time": 0.08,
        "rotate": VARIANT_PROJECTILES["torre_10"]["rotate"],
    },
    "torre_11": {
        "body": "45.png",
        "body_firing": None,
        "shadow": "8.png",
        "projectile": VARIANT_PROJECTILES["torre_11"]["file"],
        "impact": ["46.png", "47.png", "48.png", "49.png", "50.png"],
        "hover": VARIANT_PROJECTILES["torre_11"]["file"],
        "hover_height": 155.0,
        "projectile_size": 40.0,
        "hover_size": 30.0,
        "impact_size": 105.0,
        "projectile_speed": 480.0,
        "impact_frame_time": 0.08,
        "rotate": VARIANT_PROJECTILES["torre_11"]["rotate"],
    },
    "torre_12": {
        "body": "45.png",
        "body_firing": None,
        "shadow": "8.png",
        "projectile": VARIANT_PROJECTILES["torre_12"]["file"],
        "impact": ["46.png", "47.png", "48.png", "49.png", "50.png"],
        "hover": VARIANT_PROJECTILES["torre_12"]["file"],
        "hover_height": 155.0,
        "projectile_size": 40.0,
        "hover_size": 30.0,
        "impact_size": 105.0,
        "projectile_speed": 480.0,
        "impact_frame_time": 0.08,
        "rotate": VARIANT_PROJECTILES["torre_12"]["rotate"],
    },
}


# Apariencia de proyectil de fuego de la Semana 3, conservada para
# reutilizarla en una torre que realmente lance fuego (por ejemplo,
# las variantes torre_04-06, que ya la tienen asignada en
# VARIANT_PROJECTILES). La torre "fuego" actual es una catapulta que
# lanza rocas (variante torre_02), por eso su spec usa la roca del
# pack y no esta llama. 35.png se dibuja en orientacion de caida, de
# ahi el modo de rotacion "fall".
LEGACY_FIRE_PROJECTILE = {
    "projectile": "35.png",
    "impact": [
        "54.png", "55.png", "56.png", "57.png",
        "58.png", "59.png", "60.png", "61.png",
    ],
    "hover": "35.png",
    "projectile_size": 54.0,
    "hover_size": 40.0,
    "impact_size": 145.0,
    "impact_frame_time": 0.06,
    "rotate": "fall",
}


def asset_path(filename):
    """Ruta completa de un PNG del pack. O(1)."""
    return os.path.join(ASSET_DIR, filename)


class TowerAssets:
    """Sprites precargados y pre-escalados de torres y efectos.

    Compone cada torre como sombra + cuerpo (en reposo o en la
    variante de disparo) en una sola superficie y cachea el
    proyectil, la munición flotante y los frames de impacto ya
    escalados al tamano final de pantalla. O(1) por tipo tras la
    primera carga.
    """

    def __init__(self, scale=1.0):
        self.scale = max(1e-6, float(scale))
        self._tower_cache = {}
        self._tower_anchor = {}
        self._projectile_cache = {}
        self._hover_cache = {}
        self._impact_cache = {}

    def spec(self, kind):
        """Configuracion visual de un tipo de torre. O(1)."""
        return TOWER_ASSETS.get(kind, TOWER_ASSETS["basica"])

    @staticmethod
    def _ensure_pygame():
        if not pygame.get_init():
            pygame.init()
        if not pygame.display.get_init():
            pygame.display.set_mode((1, 1))

    def _load(self, filename):
        self._ensure_pygame()
        return pygame.image.load(asset_path(filename)).convert_alpha()

    def _fit(self, image, target_size):
        """Escala image para que su lado mayor mida target_size*scale px."""
        width, height = image.get_size()
        target = max(1, int(round(target_size * self.scale)))
        factor = target / max(width, height)
        size = (
            max(1, int(round(width * factor))),
            max(1, int(round(height * factor))),
        )
        if (width, height) == size:
            return image
        return pygame.transform.smoothscale(image, size)

    def tower(self, kind, firing=False):
        """Superficie compuesta (sombra + cuerpo) de la torre. O(1).

        Con firing=True usa la variante body_firing si existe
        (brillo de basica, llama alta de fuego); si no, la normal.
        El lienzo y el ancla son siempre los del par de cuerpos
        para que ambas variantes se dibujen en el mismo sitio.
        """
        cache_key = (kind, bool(firing))
        if cache_key in self._tower_cache:
            return self._tower_cache[cache_key]
        spec = self.spec(kind)
        idle_body = self._fit(self._load(spec["body"]), TOWER_WIDTH_PX)
        shadow = self._fit(self._load(spec["shadow"]), TOWER_WIDTH_PX * 0.85)

        firing_body = None
        if spec.get("body_firing"):
            firing_body = self._fit(self._load(spec["body_firing"]), TOWER_WIDTH_PX)

        body = firing_body if (firing and firing_body) else idle_body
        body_w, body_h = body.get_size()
        idle_w, idle_h = idle_body.get_size()
        shadow_w, shadow_h = shadow.get_size()

        bottoms = [idle_h]
        if firing_body is not None:
            bottoms.append(firing_body.get_height())
        body_bottom = max(bottoms)
        width = max(idle_w, body_w, shadow_w)
        height = body_bottom + shadow_h // 2

        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        surface.blit(shadow, ((width - shadow_w) // 2, height - shadow_h))
        surface.blit(body, ((width - body_w) // 2, body_bottom - body_h))

        self._tower_cache[cache_key] = surface
        self._tower_anchor[kind] = (width // 2, body_bottom)
        return surface

    def tower_anchor(self, kind):
        """Punto de la superficie que se alinea con la torre en el mapa.

        Es la base del cuerpo (donde la torre toca el suelo), para que
        la plataforma quede sobre el punto colocado y la sombra debajo.
        O(1).
        """
        self.tower(kind)
        return self._tower_anchor[kind]

    def projectile(self, kind):
        """Sprite del proyectil del tipo, escalado. O(1)."""
        if kind in self._projectile_cache:
            return self._projectile_cache[kind]
        spec = self.spec(kind)
        image = self._fit(self._load(spec["projectile"]), spec["projectile_size"])
        self._projectile_cache[kind] = image
        return image

    def hover(self, kind):
        """Sprite de la munición flotante en reposo, escalado. O(1)."""
        if kind in self._hover_cache:
            return self._hover_cache[kind]
        spec = self.spec(kind)
        image = self._fit(self._load(spec["hover"]), spec["hover_size"])
        self._hover_cache[kind] = image
        return image

    def hover_height(self, kind):
        """Altura del flote sobre la base de la torre, en pixeles de
        mapa ya escalados a pantalla. O(1)."""
        return self.spec(kind)["hover_height"] * self.scale

    def impact_frames(self, kind):
        """Frames del impacto del tipo, en orden y escalados. O(k)."""
        if kind in self._impact_cache:
            return self._impact_cache[kind]
        spec = self.spec(kind)
        frames = [
            self._fit(self._load(filename), spec["impact_size"])
            for filename in spec["impact"]
        ]
        self._impact_cache[kind] = frames
        return frames
