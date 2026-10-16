"""
Pruebas de la carga, representacion y colocacion de torres.

Comprueba que:

    - el mapa .tmx se carga con dimensiones correctas
    - el tileset .tsx carga los tiles
    - la polilinea del camino se extrae y tiene longitud valida
    - las zonas bloqueadas se extraen
    - las capas del mapa se renderizan a una superficie
    - la validacion de colocacion de torres funciona correctamente

Ejecutar desde la raiz del proyecto:

    py -m pytest -v
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import unittest

import pygame

from Model.game_model import GameModel
from View.tiled_map import TiledMap, TiledMapRenderer

MAP_PATH = os.path.join("assets", "mapas", "mapa_principal.tmx")


class TestTiledMap(unittest.TestCase):
    """Pruebas de la carga del mapa de Tiled."""

    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))
        cls.tiled_map = TiledMap(MAP_PATH)

    def test_map_dimensions(self):
        self.assertEqual(self.tiled_map.width, 12)
        self.assertEqual(self.tiled_map.height, 7)
        self.assertEqual(self.tiled_map.tile_width, 256)
        self.assertEqual(self.tiled_map.tile_height, 256)
        self.assertEqual(self.tiled_map.pixel_width, 3072)
        self.assertEqual(self.tiled_map.pixel_height, 1792)

    def test_tileset_loaded(self):
        self.assertIsNotNone(self.tiled_map.tileset)
        self.assertGreater(len(self.tiled_map.tileset.tiles), 0)

    def test_layers_present(self):
        names = [layer["name"] for layer in self.tiled_map.layers]
        self.assertIn("Terreno", names)
        self.assertIn("Camino", names)
        self.assertIn("Decoracion", names)

    def test_path_extracted(self):
        self.assertGreater(len(self.tiled_map.path_points), 1)
        self.assertGreater(self.tiled_map.path_length(), 0)

    def test_blocked_zones_extracted(self):
        self.assertGreater(len(self.tiled_map.blocked_zones), 0)

    def test_object_groups_present(self):
        self.assertIn("Decoraciones_libres", self.tiled_map.object_groups)
        self.assertIn("Decoraciones_superiores", self.tiled_map.object_groups)
        self.assertIn("Ruta_enemigos", self.tiled_map.object_groups)
        self.assertIn("Zonas_bloqueadas", self.tiled_map.object_groups)

    def test_point_at_fraction_endpoints(self):
        start = self.tiled_map.point_at_fraction(0.0)
        end = self.tiled_map.point_at_fraction(1.0)
        self.assertEqual(
            (int(start[0]), int(start[1])),
            (int(self.tiled_map.path_points[0][0]),
             int(self.tiled_map.path_points[0][1])),
        )
        self.assertEqual(
            (int(end[0]), int(end[1])),
            (int(self.tiled_map.path_points[-1][0]),
             int(self.tiled_map.path_points[-1][1])),
        )


class TestTiledMapRenderer(unittest.TestCase):
    """Pruebas de la renderizacion del mapa."""

    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))
        cls.tiled_map = TiledMap(MAP_PATH)
        cls.renderer = TiledMapRenderer(cls.tiled_map)

    def test_base_surface_size(self):
        self.assertEqual(
            self.renderer.base_surface.get_size(),
            (self.tiled_map.pixel_width, self.tiled_map.pixel_height),
        )

    def test_upper_surface_size(self):
        self.assertEqual(
            self.renderer.upper_surface.get_size(),
            (self.tiled_map.pixel_width, self.tiled_map.pixel_height),
        )

    def test_base_surface_not_empty(self):
        rect = self.renderer.base_surface.get_bounding_rect()
        self.assertGreater(rect.width, 0)
        self.assertGreater(rect.height, 0)


class TestGeometryHelpers(unittest.TestCase):
    """Pruebas de los helpers geometricos de TiledMap."""

    def test_point_in_rect_inside(self):
        rect = pygame.Rect(10, 10, 100, 100)
        self.assertTrue(TiledMap.point_in_rect(50, 50, rect))
        self.assertTrue(TiledMap.point_in_rect(10, 10, rect))
        self.assertTrue(TiledMap.point_in_rect(110, 110, rect))

    def test_point_in_rect_outside(self):
        rect = pygame.Rect(10, 10, 100, 100)
        self.assertFalse(TiledMap.point_in_rect(5, 5, rect))
        self.assertFalse(TiledMap.point_in_rect(200, 50, rect))
        self.assertFalse(TiledMap.point_in_rect(50, 200, rect))

    def test_point_in_polygon_triangle_inside(self):
        tri = [(0, 0), (100, 0), (50, 100)]
        self.assertTrue(TiledMap.point_in_polygon(50, 30, tri))

    def test_point_in_polygon_triangle_outside(self):
        tri = [(0, 0), (100, 0), (50, 100)]
        self.assertFalse(TiledMap.point_in_polygon(10, 90, tri))
        self.assertFalse(TiledMap.point_in_polygon(150, 50, tri))

    def test_point_in_polygon_square(self):
        sq = [(0, 0), (100, 0), (100, 100), (0, 100)]
        self.assertTrue(TiledMap.point_in_polygon(50, 50, sq))
        self.assertFalse(TiledMap.point_in_polygon(150, 50, sq))

    def test_closest_progress_on_path_start(self):
        m = TiledMap.__new__(TiledMap)
        m.path_points = [(0, 0), (100, 0), (100, 100)]
        self.assertAlmostEqual(m.closest_progress_on_path(0, 0), 0.0)
        self.assertAlmostEqual(m.closest_progress_on_path(100, 0), 100.0)
        self.assertAlmostEqual(m.closest_progress_on_path(100, 100), 200.0)
        self.assertAlmostEqual(m.closest_progress_on_path(50, 0), 50.0)


class TestTowerPlacement(unittest.TestCase):
    """Pruebas de la validacion de colocacion de torres."""

    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))
        cls.tiled_map = TiledMap(MAP_PATH)

    def test_valid_position_accepted(self):
        valid, reason = self.tiled_map.can_place_tower(1680, 80, 40)
        self.assertTrue(valid, f"Se esperaba valida, motivo: {reason}")
        self.assertEqual(reason, "")

    def test_outside_map_rejected_left(self):
        valid, reason = self.tiled_map.can_place_tower(-10, 500, 40)
        self.assertFalse(valid)
        self.assertEqual(reason, "fuera del mapa")

    def test_outside_map_rejected_right(self):
        valid, reason = self.tiled_map.can_place_tower(3100, 500, 40)
        self.assertFalse(valid)
        self.assertEqual(reason, "fuera del mapa")

    def test_outside_map_rejected_top(self):
        valid, reason = self.tiled_map.can_place_tower(1500, -10, 40)
        self.assertFalse(valid)
        self.assertEqual(reason, "fuera del mapa")

    def test_outside_map_rejected_bottom(self):
        valid, reason = self.tiled_map.can_place_tower(1500, 1800, 40)
        self.assertFalse(valid)
        self.assertEqual(reason, "fuera del mapa")

    def test_blocked_zone_rejected(self):
        valid, reason = self.tiled_map.can_place_tower(300, 100, 20)
        self.assertFalse(valid)
        self.assertEqual(reason, "zona bloqueada")

    def test_edge_of_blocked_zone_rejected(self):
        rect_zone = None
        for zone in self.tiled_map.blocked_zones:
            if zone["type"] == "rect":
                rect_zone = zone["rect"]
                break
        self.assertIsNotNone(rect_zone)
        edge_x = rect_zone.left + 2
        edge_y = rect_zone.centery
        valid, reason = self.tiled_map.can_place_tower(edge_x, edge_y, 20)
        self.assertFalse(valid)

    def test_near_blocked_zone_but_outside_accepted(self):
        rect_zone = None
        for zone in self.tiled_map.blocked_zones:
            if zone["type"] == "rect" and zone["rect"].left > 100:
                rect_zone = zone["rect"]
                break
        self.assertIsNotNone(rect_zone)
        safe_x = rect_zone.right + 50
        safe_y = rect_zone.centery
        valid, reason = self.tiled_map.can_place_tower(safe_x, safe_y, 20)
        self.assertTrue(valid, f"Se esperaba valida, motivo: {reason}")

    def test_on_top_of_tower_rejected(self):
        class FakeTower:
            map_x = 1680.0
            map_y = 80.0

        valid, reason = self.tiled_map.can_place_tower(
            1690, 80, 40, existing_towers=[FakeTower()]
        )
        self.assertFalse(valid)
        self.assertEqual(reason, "encima de otra torre")

    def test_far_from_tower_accepted(self):
        class FakeTower:
            map_x = 1680.0
            map_y = 80.0

        valid, reason = self.tiled_map.can_place_tower(
            2000, 80, 40, existing_towers=[FakeTower()]
        )
        self.assertTrue(valid, f"Se esperaba valida, motivo: {reason}")

    def test_model_can_place_tower_at(self):
        model = GameModel(path_length=self.tiled_map.path_length())
        valid, reason = model.can_place_tower_at(
            1680, 80, 40, self.tiled_map
        )
        self.assertTrue(valid, f"Se esperaba valida, motivo: {reason}")

        model.create_tower(map_x=1680, map_y=80, footprint=40)
        valid, reason = model.can_place_tower_at(
            1685, 85, 40, self.tiled_map
        )
        self.assertFalse(valid)
        self.assertEqual(reason, "encima de otra torre")

    def test_create_tower_stores_map_coordinates(self):
        model = GameModel(path_length=self.tiled_map.path_length())
        progress = self.tiled_map.closest_progress_on_path(1680, 80)
        tower = model.create_tower(
            map_x=1680, map_y=80, footprint=40, position=progress
        )
        self.assertEqual(tower.map_x, 1680)
        self.assertEqual(tower.map_y, 80)
        self.assertEqual(tower.footprint, 40)
        self.assertAlmostEqual(tower.position, progress)

    def test_no_towers_created_on_startup(self):
        model = GameModel(path_length=self.tiled_map.path_length())
        self.assertEqual(len(model.towers), 0)


if __name__ == "__main__":
    unittest.main()
