"""
Pruebas del arranque sin torre seleccionada (torreta.md).

Comprueba que:

    - al iniciar una partida no hay ninguna torre seleccionada
    - un clic sobre el mapa sin seleccion no coloca nada ni cobra
    - no hay previsualizacion de colocacion sin seleccion
    - la tienda arma la colocacion al elegir una torre disponible
    - la torre elegida se coloca y se cobra su precio
    - ESC (y el clic derecho) vuelven al estado sin seleccion
    - una ventana de partida nueva tambien arranca sin seleccion

Ejecutar desde la raiz del proyecto:

    py -m pytest -v
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import unittest

import pygame

from Controller.game_controller import GameController
from Model.game_model import STARTING_STARS
from View.game_window import GameWindow
from View.tiled_map import TiledMap

MAP_PATH = os.path.join("assets", "mapas", "mapa_principal.tmx")


def _click_event(pos, button=1):
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos, button=button)


def _key_event(key):
    return pygame.event.Event(pygame.KEYDOWN, key=key)


class TestNewGameStartsWithoutSelection(unittest.TestCase):
    """Estado inicial de la partida: sin torre seleccionada."""

    def setUp(self):
        pygame.display.set_mode((GameWindow.WIDTH, GameWindow.HEIGHT))
        self.controller = GameController(view=None, spawn_interval=9999.0)
        self.tiled_map = TiledMap(MAP_PATH)
        self.controller.model.path_length = self.tiled_map.path_length()
        self.window = GameWindow(self.controller.model, self.tiled_map)

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

    def _open_shop_and_select(self, index=0):
        self.window.shop.open()
        center = self.window.shop.cards[index]["rect"].center
        pygame.event.clear()
        pygame.event.post(_click_event(center))
        self.assertTrue(self.window.process_events())

    def _click_map(self, screen_pos):
        pygame.event.clear()
        pygame.event.post(_click_event(screen_pos))
        self.assertTrue(self.window.process_events())
        self.window.draw()

    # 1. Inicio de partida sin ninguna torre seleccionada.
    def test_new_game_starts_with_no_tower_selected(self):
        self.assertIsNone(self.window.selected_kind)
        self.assertFalse(self.window.placing)

    # 2. El clic en el mapa sin seleccion no hace nada ni cobra.
    def test_map_click_without_selection_places_and_charges_nothing(self):
        spot = self._valid_spot()
        self._click_map(self.window.map_to_screen(*spot))
        self.assertEqual(len(self.controller.model.towers), 0)
        self.assertEqual(self.controller.model.stars, STARTING_STARS)

    def test_no_placement_preview_without_selection(self):
        # Sin seleccion no debe dibujarse nada siguiendo al cursor:
        # ni con el estado inicial (placing apagado) ni forzando el
        # estado inconsistente placing=True con selected_kind=None.
        screen = self.window.screen
        screen.fill((0, 0, 0))
        before = pygame.image.tostring(screen, "RGB")
        self.window._draw_placement_preview()
        self.assertEqual(pygame.image.tostring(screen, "RGB"), before)

        self.window.placing = True
        self.window._draw_placement_preview()
        self.assertEqual(pygame.image.tostring(screen, "RGB"), before)
        self.assertIsNone(self.window.selected_kind)

    # 3 y 4. La tienda arma la colocacion y la torre se coloca.
    def test_shop_selection_arms_the_placement_mode(self):
        self._open_shop_and_select(index=1)
        self.assertFalse(self.window.shop.is_open)
        self.assertEqual(self.window.selected_kind, "fuego")
        self.assertTrue(self.window.placing)

    def test_selected_tower_is_placed_and_charged(self):
        self._open_shop_and_select(index=0)
        spot = self._valid_spot()
        self._click_map(self.window.map_to_screen(*spot))
        self.assertEqual(len(self.controller.model.towers), 1)
        self.assertEqual(
            self.controller.model.stars, STARTING_STARS - 100
        )

    # 6. Cancelar con ESC vuelve al estado sin seleccion.
    def test_escape_cancels_back_to_no_selection(self):
        self._open_shop_and_select(index=0)
        pygame.event.clear()
        pygame.event.post(_key_event(pygame.K_ESCAPE))
        self.assertTrue(self.window.process_events())
        self.assertFalse(self.window.placing)
        self.assertIsNone(self.window.selected_kind)
        # Tras cancelar, un clic en el mapa ya no coloca nada.
        spot = self._valid_spot()
        self._click_map(self.window.map_to_screen(*spot))
        self.assertEqual(len(self.controller.model.towers), 0)
        self.assertEqual(self.controller.model.stars, STARTING_STARS)

    def test_right_click_cancels_back_to_no_selection(self):
        self._open_shop_and_select(index=0)
        self._click_map((10, 10))  # clic izq. inofensivo (zona invalida)
        pygame.event.clear()
        pygame.event.post(_click_event((10, 10), button=3))
        self.assertTrue(self.window.process_events())
        self.assertFalse(self.window.placing)
        self.assertIsNone(self.window.selected_kind)

    def test_clicking_the_map_without_selection_never_charges(self):
        # Fuerza el estado inconsistente placing=True sin seleccion:
        # la guarda de _try_place_tower debe impedir la colocacion.
        self.window.placing = True
        spot = self._valid_spot()
        self._click_map(self.window.map_to_screen(*spot))
        self.assertEqual(len(self.controller.model.towers), 0)
        self.assertEqual(self.controller.model.stars, STARTING_STARS)

    # 7. Reiniciar la partida (ventana nueva) restablece el estado.
    def test_a_restarted_game_starts_without_selection(self):
        self._open_shop_and_select(index=0)
        self.assertTrue(self.window.placing)
        self.window.close()

        pygame.display.set_mode((GameWindow.WIDTH, GameWindow.HEIGHT))
        restarted = GameWindow(self.controller.model, self.tiled_map)
        try:
            self.assertIsNone(restarted.selected_kind)
            self.assertFalse(restarted.placing)
        finally:
            restarted.close()


if __name__ == "__main__":
    unittest.main()
