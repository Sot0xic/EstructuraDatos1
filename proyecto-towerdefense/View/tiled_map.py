"""
Carga y representacion de mapas de Tiled (.tmx) en Pygame.

Soporta mapas ortogonales con tileset de imagenes individuales (.tsx)
y las capas de objetos usadas en el Tower Defense:

    Terreno, Camino, Decoracion        -> capas de tiles pre-renderizadas
    Decoraciones_libres                 -> objetos decorativos
    Decoraciones_superiores             -> objetos que van sobre enemigos
    Ruta_enemigos                       -> polilinea del camino
    Zonas_bloqueadas                    -> rectangulos y poligonos

La carga usa xml.etree.ElementTree (libreria estandar) y no depende
de librerias externas de Tiled.
"""

import os
import xml.etree.ElementTree as ET

import pygame

FLIPPED_HORIZONTALLY = 0x80000000
FLIPPED_VERTICALLY = 0x40000000
FLIPPED_DIAGONALLY = 0x20000000
GID_MASK = 0x1FFFFFFF


class TiledTileset:
    """Tileset cargado desde un archivo .tsx con imagenes individuales."""

    def __init__(self, path):
        self.path = path
        self.tiles = {}
        self._load(path)

    def _load(self, tsx_path):
        if not pygame.get_init():
            pygame.init()
        if not pygame.display.get_init():
            pygame.display.set_mode((1, 1))
        base_dir = os.path.dirname(tsx_path)
        tree = ET.parse(tsx_path)
        root = tree.getroot()

        for tile_el in root.findall("tile"):
            tile_id = int(tile_el.get("id"))
            image_el = tile_el.find("image")
            if image_el is None:
                continue
            source = image_el.get("source")
            image_path = os.path.normpath(os.path.join(base_dir, source))
            image = pygame.image.load(image_path).convert_alpha()
            self.tiles[tile_id] = image

    def get_tile(self, tile_id):
        """Devuelve la imagen del tile o None. O(1)."""
        return self.tiles.get(tile_id)


class TiledMap:
    """Mapa de Tiled (.tmx) cargado en memoria."""

    def __init__(self, tmx_path):
        self.tmx_path = tmx_path
        self.width = 0
        self.height = 0
        self.tile_width = 0
        self.tile_height = 0
        self.pixel_width = 0
        self.pixel_height = 0
        self.tileset = None
        self.layers = []
        self.object_groups = {}
        self.path_points = []
        self.blocked_zones = []
        self._load(tmx_path)

    def _load(self, tmx_path):
        tree = ET.parse(tmx_path)
        root = tree.getroot()

        self.width = int(root.get("width"))
        self.height = int(root.get("height"))
        self.tile_width = int(root.get("tilewidth"))
        self.tile_height = int(root.get("tileheight"))
        self.pixel_width = self.width * self.tile_width
        self.pixel_height = self.height * self.tile_height

        tsx_el = root.find("tileset")
        if tsx_el is not None:
            tsx_source = tsx_el.get("source")
            tsx_path = os.path.normpath(
                os.path.join(os.path.dirname(tmx_path), tsx_source)
            )
            self.tileset = TiledTileset(tsx_path)

        for layer_el in root.findall("layer"):
            name = layer_el.get("name")
            data_el = layer_el.find("data")
            csv_text = data_el.text.strip()
            gids = [int(v) for v in csv_text.replace("\n", "").split(",") if v.strip()]
            self.layers.append({"name": name, "gids": gids})

        for group_el in root.findall("objectgroup"):
            group_name = group_el.get("name")
            objects = []
            for obj_el in group_el.findall("object"):
                obj = self._parse_object(obj_el)
                objects.append(obj)
            self.object_groups[group_name] = objects

        self._extract_path()
        self._extract_blocked_zones()

    def _parse_object(self, obj_el):
        obj = {
            "id": int(obj_el.get("id")),
            "name": obj_el.get("name", ""),
            "x": float(obj_el.get("x", 0)),
            "y": float(obj_el.get("y", 0)),
            "width": float(obj_el.get("width", 0)),
            "height": float(obj_el.get("height", 0)),
            "gid": int(obj_el.get("gid", 0)) if obj_el.get("gid") else 0,
        }

        polyline_el = obj_el.find("polyline")
        if polyline_el is not None:
            obj["polyline"] = self._parse_points(polyline_el.get("points"))

        polygon_el = obj_el.find("polygon")
        if polygon_el is not None:
            obj["polygon"] = self._parse_points(polygon_el.get("points"))

        return obj

    @staticmethod
    def _parse_points(points_str):
        points = []
        for pair in points_str.split():
            xs, ys = pair.split(",")
            points.append((float(xs), float(ys)))
        return points

    def _extract_path(self):
        """Extrae la polilinea del camino de la capa Ruta_enemigos."""
        objects = self.object_groups.get("Ruta_enemigos", [])
        for obj in objects:
            if obj.get("polyline"):
                offset_x = obj["x"]
                offset_y = obj["y"]
                self.path_points = [
                    (offset_x + px, offset_y + py)
                    for px, py in obj["polyline"]
                ]
                return

    def _extract_blocked_zones(self):
        """Extrae las zonas bloqueadas de la capa Zonas_bloqueadas."""
        objects = self.object_groups.get("Zonas_bloqueadas", [])
        for obj in objects:
            if obj.get("polygon"):
                points = [
                    (obj["x"] + px, obj["y"] + py)
                    for px, py in obj["polygon"]
                ]
                self.blocked_zones.append({"type": "polygon", "points": points})
            elif obj["width"] > 0 and obj["height"] > 0:
                rect = pygame.Rect(
                    int(obj["x"]), int(obj["y"]),
                    int(obj["width"]), int(obj["height"]),
                )
                self.blocked_zones.append({"type": "rect", "rect": rect})

    def path_length(self):
        """Longitud total del camino de enemigos. O(p)."""
        if len(self.path_points) < 2:
            return 1.0
        total = 0.0
        for i in range(1, len(self.path_points)):
            x0, y0 = self.path_points[i - 1]
            x1, y1 = self.path_points[i]
            total += ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
        return total

    def point_at_fraction(self, fraction):
        """Punto en pixeles del mapa para una fraccion [0..1] del camino. O(p)."""
        target = fraction * self.path_length()
        accumulated = 0.0
        for i in range(1, len(self.path_points)):
            x0, y0 = self.path_points[i - 1]
            x1, y1 = self.path_points[i]
            seg = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
            if accumulated + seg >= target:
                t = (target - accumulated) / max(1e-9, seg)
                return (x0 + (x1 - x0) * t, y0 + (y1 - y0) * t)
            accumulated += seg
        return self.path_points[-1]

    # ------------------------------------------------------------------
    # Geometria de colocacion de torres
    # ------------------------------------------------------------------
    @staticmethod
    def point_in_rect(px, py, rect):
        """True si el punto (px, py) esta dentro del rectangulo. O(1)."""
        return (
            rect.left <= px <= rect.right
            and rect.top <= py <= rect.bottom
        )

    @staticmethod
    def point_in_polygon(px, py, points):
        """True si el punto esta dentro del poligono (ray casting). O(v)."""
        n = len(points)
        if n < 3:
            return False
        inside = False
        j = n - 1
        for i in range(n):
            xi, yi = points[i]
            xj, yj = points[j]
            if (yi > py) != (yj > py):
                x_intersect = (xj - xi) * (py - yi) / (yj - yi) + xi
                if px < x_intersect:
                    inside = not inside
            j = i
        return inside

    def can_place_tower(self, center_x, center_y, radius, existing_towers=None):
        """Comprueba si una torre de cierto radio puede colocarse. O(z + t).

        Comprueba toda la superficie circular de la torre (no solo el
        centro): borde superior, inferior, izquierdo, derecho y los
        cuatro puntos cardinales intermedios.

        Devuelve (True, "") si es valida, o (False, motivo).
        """
        if (
            center_x - radius < 0
            or center_y - radius < 0
            or center_x + radius > self.pixel_width
            or center_y + radius > self.pixel_height
        ):
            return False, "fuera del mapa"

        samples = self._tower_samples(center_x, center_y, radius)

        for zone in self.blocked_zones:
            if zone["type"] == "rect":
                rect = zone["rect"]
                for sx, sy in samples:
                    if self.point_in_rect(sx, sy, rect):
                        return False, "zona bloqueada"
            elif zone["type"] == "polygon":
                points = zone["points"]
                for sx, sy in samples:
                    if self.point_in_polygon(sx, sy, points):
                        return False, "zona bloqueada"

        if existing_towers:
            for tower in existing_towers:
                if not hasattr(tower, "map_x"):
                    continue
                dx = center_x - tower.map_x
                dy = center_y - tower.map_y
                if (dx * dx + dy * dy) ** 0.5 < radius * 2:
                    return False, "encima de otra torre"

        return True, ""

    @staticmethod
    def _tower_samples(cx, cy, r):
        """Puntos representativos de la superficie de una torre circular."""
        d = r * 0.7071
        return [
            (cx, cy),
            (cx + r, cy),
            (cx - r, cy),
            (cx, cy + r),
            (cx, cy - r),
            (cx + d, cy + d),
            (cx - d, cy + d),
            (cx + d, cy - d),
            (cx - d, cy - d),
        ]

    def closest_progress_on_path(self, px, py):
        """Progreso (distancia acumulada) del punto del camino mas cercano
        a (px, py). Util para asignarle a una torre su posicion de ataque.
        O(p)."""
        best_dist_sq = float("inf")
        best_progress = 0.0
        accumulated = 0.0
        for i in range(1, len(self.path_points)):
            x0, y0 = self.path_points[i - 1]
            x1, y1 = self.path_points[i]
            dx = x1 - x0
            dy = y1 - y0
            seg_len_sq = dx * dx + dy * dy
            seg_len = seg_len_sq ** 0.5
            if seg_len_sq > 0:
                t = ((px - x0) * dx + (py - y0) * dy) / seg_len_sq
                t = max(0.0, min(1.0, t))
            else:
                t = 0.0
            proj_x = x0 + t * dx
            proj_y = y0 + t * dy
            dist_sq = (px - proj_x) ** 2 + (py - proj_y) ** 2
            if dist_sq < best_dist_sq:
                best_dist_sq = dist_sq
                best_progress = accumulated + t * seg_len
            accumulated += seg_len
        return best_progress


class TiledMapRenderer:
    """Renderiza un TiledMap a superficies de Pygame."""

    LAYERS_BASE = ("Terreno", "Camino", "Decoracion")

    def __init__(self, tiled_map):
        self.map = tiled_map
        self.base_surface = self._build_base_surface()
        self.upper_surface = self._build_upper_surface()

    def _build_base_surface(self):
        """Pre-renderiza las capas de tiles y objetos decorativos. O(w*h)."""
        m = self.map
        surface = pygame.Surface((m.pixel_width, m.pixel_height), pygame.SRCALPHA)

        layer_lookup = {layer["name"]: layer for layer in m.layers}
        for name in self.LAYERS_BASE:
            layer = layer_lookup.get(name)
            if layer:
                self._draw_tile_layer(surface, layer)

        self._draw_objects(surface, m.object_groups.get("Decoraciones_libres", []))
        return surface

    def _build_upper_surface(self):
        """Pre-renderiza las capas que van por encima de enemigos. O(k)."""
        m = self.map
        surface = pygame.Surface((m.pixel_width, m.pixel_height), pygame.SRCALPHA)
        self._draw_objects(surface, m.object_groups.get("Decoraciones_superiores", []))
        return surface

    def _draw_tile_layer(self, surface, layer):
        m = self.map
        gids = layer["gids"]
        for row in range(m.height):
            for col in range(m.width):
                index = row * m.width + col
                if index >= len(gids):
                    continue
                gid = gids[index]
                if gid == 0:
                    continue
                tile_id = (gid & GID_MASK) - 1
                image = self.map.tileset.get_tile(tile_id)
                if image is None:
                    continue
                surface.blit(image, (col * m.tile_width, row * m.tile_height))

    def _draw_objects(self, surface, objects):
        for obj in objects:
            if obj["gid"] == 0:
                continue
            tile_id = (obj["gid"] & GID_MASK) - 1
            image = self.map.tileset.get_tile(tile_id)
            if image is None:
                continue
            w = int(obj["width"]) if obj["width"] > 0 else image.get_width()
            h = int(obj["height"]) if obj["height"] > 0 else image.get_height()
            if (w, h) != image.get_size():
                scaled = pygame.transform.smoothscale(image, (w, h))
            else:
                scaled = image
            x = int(obj["x"])
            y = int(obj["y"]) - h
            surface.blit(scaled, (x, y))
