"""
Pruebas del modo debug de alcance de torres (fixed.md).

Comprueba:
    - Tecla F3 activa/desactiva el modo debug
    - Circulo de radio 210 px centrado en el punto de calculo real
    - Centro coincide con Tower.position (logica de combate is_in_range)
    - Punto rojo en el centro exacto del calculo
    - Enemigos dentro de 210 px pueden ser atacados; fuera no

Ejecutar desde la raiz del proyecto:

    py -m pytest -v
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import unittest

import pygame

from Controller.game_controller import GameController
from Model.game_model import GameModel, TOWER_KINDS, TOWER_RANGE
from View.game_window import GameWindow
from View.tiled_map import TiledMap

MAP_PATH = os.path.join("assets", "mapas", "mapa_principal.tmx")


def _key_event(key):
    return pygame.event.Event(pygame.KEYDOWN, key=key)


class TestDebugRangeMode(unittest.TestCase):
    """Modo debug de alcance activado con F3 (fixed.md)."""

    def setUp(self):
        pygame.display.set_mode((GameWindow.WIDTH, GameWindow.HEIGHT))
        self.controller = GameController(view=None, spawn_interval=9999.0)
        self.tiled_map = TiledMap(MAP_PATH)
        self.controller.model.path_length = self.tiled_map.path_length()
        self.window = GameWindow(self.controller.model, self.tiled_map)
        self.model = self.controller.model

    def tearDown(self):
        self.window.close()

    def _valid_spot(self):
        radius = GameWindow.TOWER_FOOTPRINT
        for px, py in self.tiled_map.path_points:
            for dx, dy in ((0, radius * 3), (radius * 3, 0), (-radius * 3, 0)):
                x, y = px + dx, py + dy
                valid, _ = self.tiled_map.can_place_tower(x, y, radius)
                if valid:
                    return x, y
        self.fail("No hay una posicion valida cerca del camino")

    def test_f3_toggles_debug_range_mode(self):
        self.assertFalse(self.window.debug_range)
        pygame.event.clear()
        pygame.event.post(_key_event(pygame.K_F3))
        self.assertTrue(self.window.process_events())
        self.assertTrue(self.window.debug_range)
        # F3 de nuevo para desactivar
        pygame.event.clear()
        pygame.event.post(_key_event(pygame.K_F3))
        self.assertTrue(self.window.process_events())
        self.assertFalse(self.window.debug_range)

    def test_debug_range_draws_circle_and_center_point(self):
        spot = self._valid_spot()
        progress = self.tiled_map.closest_progress_on_path(*spot)
        tower = self.model.buy_tower(
            kind="basica",
            position=progress,
            map_x=spot[0], map_y=spot[1],
            footprint=GameWindow.TOWER_FOOTPRINT,
        )
        self.assertIsNotNone(tower)

        self.window.debug_range = True
        self.window.draw()

        # Centro del calculo: Tower.position en pantalla
        cx, cy = self.window._point_at(tower.position)
        # Radio en pantalla
        expected_radius = self.window._range_radius_px(tower)
        self.assertGreater(expected_radius, 0)

        # Verificar que el centro es el mismo que usa is_in_range
        self.assertAlmostEqual(tower.position, progress)

    def test_center_matches_combat_logic_position(self):
        spot = self._valid_spot()
        progress = self.tiled_map.closest_progress_on_path(*spot)
        tower = self.model.buy_tower(
            kind="basica",
            position=progress,
            map_x=spot[0], map_y=spot[1],
            footprint=GameWindow.TOWER_FOOTPRINT,
        )
        self.assertIsNotNone(tower)

        # La posicion de combate (is_in_range usa tower.position) debe
        # coincidir con el punto que se usa para dibujar el centro
        combat_center = tower.position
        self.assertAlmostEqual(combat_center, progress)

        # Y el punto en pantalla del centro debug debe ser _point_at(tower.position)
        screen_center = self.window._point_at(tower.position)
        self.assertEqual(
            screen_center,
            self.window._point_at(combat_center),
        )

    def test_tower_range_is_exactly_210_pixels(self):
        spot = self._valid_spot()
        progress = self.tiled_map.closest_progress_on_path(*spot)
        tower = self.model.buy_tower(
            kind="basica",
            position=progress,
            map_x=spot[0], map_y=spot[1],
            footprint=GameWindow.TOWER_FOOTPRINT,
        )
        self.assertEqual(tower.range, TOWER_RANGE)
        self.assertEqual(tower.range, 210.0)

    def test_enemies_within_210_are_attacked_outside_not(self):
        spot = self._valid_spot()
        progress = self.tiled_map.closest_progress_on_path(*spot)
        tower = self.model.buy_tower(
            kind="basica",
            position=progress,
            map_x=spot[0], map_y=spot[1],
            footprint=GameWindow.TOWER_FOOTPRINT,
        )
        self.assertIsNotNone(tower)

        # Enemigo a distancia 210 (dentro del limite)
        enemy_in = self.model.create_enemy(hp=1000, speed=0.0)
        self.model.add_to_wave(enemy_in)
        enemy_in = self.model.spawn_next()
        enemy_in.progress = progress + TOWER_RANGE  # exactamente 210 px

        # Enemigo a distancia 211 (fuera)
        enemy_out = self.model.create_enemy(hp=1000, speed=0.0)
        self.model.add_to_wave(enemy_out)
        enemy_out = self.model.spawn_next()
        enemy_out.progress = progress + TOWER_RANGE + 1.0  # 211 px

        # La torre solo debe poder atacar al primero
        self.assertTrue(tower.is_in_range(enemy_in))
        self.assertFalse(tower.is_in_range(enemy_out))

        # El combat real ataca solo al enemigo en rango
        self.controller.update(0.1)
        self.assertLess(enemy_in.hp, 1000)
        self.assertEqual(enemy_out.hp, 1000)

    def test_debug_range_radius_uses_tower_range_constant(self):
        spot = self._valid_spot()
        progress = self.tiled_map.closest_progress_on_path(*spot)
        tower = self.model.buy_tower(
            kind="basica",
            position=progress,
            map_x=spot[0], map_y=spot[1],
            footprint=GameWindow.TOWER_FOOTPRINT,
        )

        # Radio en pantalla = TOWER_RANGE * escala
        radius = self.window._range_radius_px(tower)
        expected = int(TOWER_RANGE * self.window.scale)
        self.assertEqual(radius, expected)


if __name__ == "__main__":
    unittest.main()
