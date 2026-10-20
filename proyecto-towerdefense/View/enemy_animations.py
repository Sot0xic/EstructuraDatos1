"""
Sprites animados de los enemigos (enemigos.md).

Reemplaza unicamente la representacion visual de los enemigos (el
circulo de GameWindow) por los PNG de assets/enemigos, sin tocar la
logica de modelo ni de controlador: vida, velocidad, movimiento por el
recorrido, oleadas, combate, recompensa de 25 estrellas y prioridad de
objetivo (menor vida) quedan exactamente igual.

Recursos inspeccionados en assets/enemigos/{1,2,3,4}/: cada carpeta
tiene 7 animaciones (attack, die, hurt, idle, jump, run, walk) con 20
fotogramas PNG, llamadas {tipo}_enemies_1_{anim}_{idx:03d}.png. Todos
los fotogramas de un tipo comparten el mismo lienzo (1: 294x275,
2: 343x348, 3: 349x291, 4: 254x205) y el contenido etiquetado varia
pocos pixeles dentro de walk, de modo que el enemigo no salta entre
fotogramas.

Sistema unico y reutilizable (enemigos.md §9): una sola clase recibe
el tipo de enemigo. Las oleadas existentes (Goblin, Duende, Orco,
Dragon) se cables a las carpetas 1..4 en ENEMY_TYPES; cualquier nombre
desconocido usa DEFAULT_TYPE, y para anyadir el enemigo 5 basta con
crear assets/enemigos/5 y registrar su nombre en ENEMY_TYPES.

Los PNG tienen espacios transparentes alrededor del personaje y este
esta dibujado mirando a la derecha, por lo que:

  - el ancla es el centro-inferior del contenido (no del lienzo) de
    walk_000: los pies caen sobre el punto logico del camino y el
    relleno transparente no desplaza al enemigo. La misma ancla se usa
    en todas las animaciones del tipo para que nada se mueva al pasar
    de walk a hurt o a die;
  - al desplazarse hacia la izquierda se entrega la version volteada
    horizontalmente del fotograma (frames flip).

La reproduccion (tiempos, estados walk/hurt/die y congelado en
pausa) vive en View.game_window._advance_effects; aqui solo se carga,
escala y entrega fotogramas, de forma perezosa por (tipo, animacion).
No se importa nada del modelo: la vista sigue sin invertir
dependencias en la capa de datos (MVC).
"""

import os

import pygame

ANIM_DIR = os.path.join("assets", "enemigos")

# Animaciones disponibles en las carpetas (inspeccionado, §1).
ANIMS = ("walk", "idle", "hurt", "die", "attack", "run", "jump")

# Nombre de oleada (main.py) -> carpeta de sprites. Para agregar el
# enemigo 5: crear assets/enemigos/5 con sus PNG y anadir aqui el
# nombre con el que la oleada lo invoca.
ENEMY_TYPES = {
    "Goblin": "1",
    "Duende": "2",
    "Orco": "3",
    "Dragon": "4",
}
# Carpeta usada para nombres sin mapear (pruebas, oleadas nuevas).
DEFAULT_TYPE = "1"

# Altura objetivo del CONTENIDO (sin relleno transparente) de cada
# tipo, en pixeles de mapa: es el unico sitio donde ajustar el tamano
# visual de cada enemigo (enemigos.md §6 y §11). Se multiplica por la
# escala de la ventana igual que TOWER_WIDTH_PX en las torres.
ENEMY_HEIGHT_PX = {
    "1": 140.0,
    "2": 180.0,
    "3": 155.0,
    "4": 110.0,
}

# Segundos por fotograma. walk se repite en bucle; hurt y die se
# reproducen una sola vez (la ventana los corta al completarlos).
FRAME_TIMES = {
    "walk": 1.0 / 12.0,
    "hurt": 1.0 / 20.0,
    "die": 1.0 / 15.0,
}
DEFAULT_FRAME_TIME = FRAME_TIMES["walk"]


class EnemyAnimations:
    """Fotogramas de los enemigos, precargados y pre-escalados.

    Carga perezosa por (tipo, animacion): al pedir walk, hurt o die
    por primera vez se leen del disco solo los 20 PNG de esa
    animacion, se escalan una vez al alto objetivo del tipo y se
    guardan tambien volteados horizontalmente. O(1) por consulta tras
    la primera carga.
    """

    def __init__(self, scale=1.0):
        self.scale = max(1e-6, float(scale))
        # tipo -> datos fijos del tipo (anclas y factor de escala).
        self._types = {}
        # (tipo, anim) -> {"frames": [...], "flip": [...]}.
        self._anims = {}

    # ------------------------------------------------------------------
    # Tipos
    # ------------------------------------------------------------------
    @staticmethod
    def type_for(name):
        """Carpeta de sprites asignada a un nombre de oleada. O(1)."""
        return ENEMY_TYPES.get(name, DEFAULT_TYPE)

    @staticmethod
    def available_types():
        """Carpetas de enemigos existentes en assets/enemigos. O(d)."""
        if not os.path.isdir(ANIM_DIR):
            return tuple()
        return tuple(
            entry
            for entry in sorted(os.listdir(ANIM_DIR))
            if os.path.isdir(os.path.join(ANIM_DIR, entry))
        )

    def has(self, enemy_type):
        """True si el tipo tiene carpeta de sprites. O(1)."""
        return os.path.isdir(os.path.join(ANIM_DIR, enemy_type))

    # ------------------------------------------------------------------
    # Carga y escala
    # ------------------------------------------------------------------
    @staticmethod
    def _ensure_pygame():
        if not pygame.get_init():
            pygame.init()
        if not pygame.display.get_init():
            pygame.display.set_mode((1, 1))

    @staticmethod
    def _content_rect(surface):
        """Rectangulo del contenido con alfa visible, sin relleno. O(w*h).

        Los PNG traen espacios transparentes distintos entre tipos y
        animaciones; medir el contenido (no el lienzo) es lo que
        permite anclar los pies de cualquier animacion en el mismo
        punto sin desplazamientos visuales.
        """
        rects = pygame.mask.from_surface(surface, 8).get_bounding_rects()
        if not rects:
            return pygame.Rect(0, 0, 0, 0)
        rect = rects[0].copy()
        for other in rects[1:]:
            rect = rect.union(other)
        return rect

    @staticmethod
    def _frame_indices(enemy_type, anim):
        """Indices de PNG disponibles para una animacion. O(f) de disco."""
        folder = os.path.join(ANIM_DIR, enemy_type)
        if not os.path.isdir(folder):
            return tuple()
        prefix = f"{enemy_type}_enemies_1_{anim}_"
        indices = []
        for filename in os.listdir(folder):
            if filename.startswith(prefix) and filename.endswith(".png"):
                suffix = filename[len(prefix):-4]
                if suffix.isdigit():
                    indices.append(int(suffix))
        return tuple(sorted(indices))

    def _load_frame(self, enemy_type, anim, index):
        """Carga y escala un fotograma PNG. O(1) de CPU + disco."""
        self._ensure_pygame()
        filename = f"{enemy_type}_enemies_1_{anim}_{index:03d}.png"
        path = os.path.join(ANIM_DIR, enemy_type, filename)
        image = pygame.image.load(path).convert_alpha()
        factor = self._types[enemy_type]["factor"]
        width, height = image.get_size()
        size = (
            max(1, int(round(width * factor))),
            max(1, int(round(height * factor))),
        )
        if (width, height) == size:
            return image
        return pygame.transform.smoothscale(image, size)

    def _ensure_type(self, enemy_type):
        """Ancla y escala fijas del tipo, calculadas con walk_000. O(w*h)."""
        cached = self._types.get(enemy_type)
        if cached is not None:
            return cached
        if not self.has(enemy_type):
            raise KeyError(f"Tipo de enemigo sin sprites: {enemy_type}")
        walk = self._frame_indices(enemy_type, "walk")
        if not walk:
            raise KeyError(f"Tipo de enemigo sin frames walk: {enemy_type}")
        native = self._load_frame_raw(enemy_type, "walk", walk[0])
        content = self._content_rect(native)
        target = ENEMY_HEIGHT_PX.get(
            enemy_type, ENEMY_HEIGHT_PX[DEFAULT_TYPE]
        )
        factor = (target * self.scale) / max(1.0, content.height)
        entry = {"factor": factor}
        self._types[enemy_type] = entry

        scaled = self._load_frame(enemy_type, "walk", walk[0])
        rect = self._content_rect(scaled)
        width = scaled.get_width()
        entry["size"] = scaled.get_size()
        entry["anchor"] = (rect.centerx, rect.bottom)
        entry["anchor_flip"] = (width - rect.centerx, rect.bottom)
        return entry

    @staticmethod
    def _load_frame_raw(enemy_type, anim, index):
        """Carga un PNG sin escalar. O(1) de disco."""
        EnemyAnimations._ensure_pygame()
        filename = f"{enemy_type}_enemies_1_{anim}_{index:03d}.png"
        path = os.path.join(ANIM_DIR, enemy_type, filename)
        return pygame.image.load(path).convert_alpha()

    def _ensure_anim(self, enemy_type, anim):
        """Carga y cachea todos los fotogramas (y sus volteos). O(20)."""
        key = (enemy_type, anim)
        cached = self._anims.get(key)
        if cached is not None:
            return cached
        self._ensure_type(enemy_type)
        frames = []
        flip = []
        for index in self._frame_indices(enemy_type, anim):
            image = self._load_frame(enemy_type, anim, index)
            frames.append(image)
            flip.append(pygame.transform.flip(image, True, False))
        entry = {"frames": frames, "flip": flip}
        self._anims[key] = entry
        return entry

    # ------------------------------------------------------------------
    # Consultas (las que usa GameWindow al dibujar)
    # ------------------------------------------------------------------
    def frames(self, enemy_type, anim, flip=False):
        """Fotogramas escalados de una animacion, o [] si no existe. O(1)."""
        if anim not in ANIMS or not self.has(enemy_type):
            return []
        entry = self._ensure_anim(enemy_type, anim)
        return entry["flip"] if flip else entry["frames"]

    def frame(self, enemy_type, anim, time, flip=False, loop=True):
        """Fotograma para `time` segundos, o None si no hay recursos. O(1).

        loop=True recorre la animacion en bucle (walk); loop=False se
        queda en el ultimo fotograma (hurt y die, que la ventana corta
        al completar su duracion).
        """
        frames = self.frames(enemy_type, anim, flip=flip)
        if not frames:
            return None
        frame_time = FRAME_TIMES.get(anim, DEFAULT_FRAME_TIME)
        index = int(max(0.0, float(time)) / max(1e-9, frame_time))
        if loop:
            index %= len(frames)
        else:
            index = min(index, len(frames) - 1)
        return frames[index]

    def anchor(self, enemy_type, flip=False):
        """Punto del fotograma que se alinea con el enemigo. O(1).

        Centro-inferior del contenido de walk_000 en pantalla; con
        flip se devuelve la referencia espejada del mismo punto.
        """
        entry = self._ensure_type(enemy_type)
        return entry["anchor_flip" if flip else "anchor"]

    def size(self, enemy_type):
        """Tamano del lienzo escalado de un tipo, o None. O(1)."""
        return self._types.get(enemy_type, {}).get("size")

    def duration(self, enemy_type, anim):
        """Segundos que dura la animacion completa (una pasada). O(1)."""
        frames = self.frames(enemy_type, anim)
        if not frames:
            return 0.0
        return len(frames) * FRAME_TIMES.get(anim, DEFAULT_FRAME_TIME)
