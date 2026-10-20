"""
Pruebas de la tienda emergente de torres (interfaz medieval).

Comprueba que la tienda:

    - se abre con el boton del HUD y pausa la simulacion (window.paused)
    - muestra las 12 torres en cuadricula 3x4, todas con tipo (datos.md)
    - al elegir una torre disponible cierra el panel y arma su
      colocacion (selected_kind + placing)
    - una tarjeta con saldo insuficiente no cierra ni selecciona
    - se cierra con ESC y con su boton, y con la tienda abierta no
      coloca torres ni deja salir con ESC

Ejecutar desde la raiz del proyecto:

    py -m pytest -v
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import unittest

import pygame

from Controller.game_controller import GameController
from View.game_window import GameWindow
from View.shop_panel import SHOP_TOWERS, ShopPanel
from View.tiled_map import TiledMap

MAP_PATH = os.path.join("assets", "mapas", "mapa_principal.tmx")


def _key_event(key):
    return pygame.event.Event(pygame.KEYDOWN, key=key)


def _click_event(pos, button=1):
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos, button=button)


class TestShopCatalog(unittest.TestCase):
    """Pruebas del catalogo y la disposicion de la tienda."""

    def setUp(self):
        pygame.display.set_mode((GameWindow.WIDTH, GameWindow.HEIGHT))
        self.shop = ShopPanel(GameWindow.WIDTH, GameWindow.HEIGHT)

    def tearDown(self):
        self.shop.close()

    def test_catalog_lists_twelve_towers_all_selectable(self):
        self.assertEqual(len(SHOP_TOWERS), 12)
        self.assertTrue(
            all(entry.get("kind") is not None for entry in SHOP_TOWERS)
        )
        self.assertEqual(
            [entry["kind"] for entry in SHOP_TOWERS],
            ["basica", "fuego", "pesada"]
            + [f"torre_{i:02d}" for i in range(4, 13)],
        )

    def test_grid_is_three_columns_by_four_rows(self):
        self.assertEqual(ShopPanel.COLS, 3)
        self.assertEqual(ShopPanel.ROWS, 4)
        self.assertEqual(len(self.shop.cards), 12)
        centros = [tuple(card["rect"].center) for card in self.shop.cards]
        self.assertEqual(len(set(centros)), 12)

    def test_no_catalog_tower_is_locked(self):
        for index in range(12):
            self.assertFalse(self.shop.tower_locked(index), index)

    def test_available_towers_take_names_from_the_model(self):
        self.assertEqual(self.shop.tower_name(0), "Torre basica")
        self.assertEqual(self.shop.tower_name(1), "Torre de fuego")
        self.assertEqual(self.shop.tower_name(2), "Torre pesada")
        for index in range(3, 12):
            self.assertTrue(self.shop.tower_name(index), index)

    def test_cards_fit_inside_the_screen(self):
        for card in self.shop.cards:
            rect = card["rect"]
            self.assertGreaterEqual(rect.x, 0)
            self.assertGreaterEqual(rect.y, 0)
            self.assertLessEqual(rect.right, GameWindow.WIDTH)
            self.assertLessEqual(rect.bottom, GameWindow.HEIGHT)


class TestShopInteraction(unittest.TestCase):
    """Pruebas de apertura, seleccion y cierre de la tienda."""

    def setUp(self):
        pygame.display.set_mode((GameWindow.WIDTH, GameWindow.HEIGHT))
        self.controller = GameController(view=None, spawn_interval=9999.0)
        self.tiled_map = TiledMap(MAP_PATH)
        self.controller.model.path_length = self.tiled_map.path_length()
        self.window = GameWindow(self.controller.model, self.tiled_map)

    def tearDown(self):
        self.window.close()

    def _open_shop(self):
        pygame.event.clear()
        pygame.event.post(_click_event(self.window.shop.opener_rect.center))
        self.assertTrue(self.window.process_events())
        self.assertTrue(self.window.shop.is_open)

    def _click_card(self, index):
        """Click de tarjeta atravesando process_events (como el jugador)."""
        self.window.shop.open()
        center = self.window.shop.cards[index]["rect"].center
        pygame.event.clear()
        pygame.event.post(_click_event(center))
        self.assertTrue(self.window.process_events())

    def test_opener_button_opens_the_shop_and_pauses(self):
        self.assertFalse(self.window.paused)
        self._open_shop()
        self.assertTrue(self.window.paused)

    def test_selecting_available_tower_arms_its_placement(self):
        self._open_shop()
        self.controller.model.stars = 100000
        for index, entry in enumerate(SHOP_TOWERS):
            self._click_card(index)
            self.assertFalse(self.window.shop.is_open)
            self.assertEqual(self.window.selected_kind, entry["kind"])
            self.assertTrue(self.window.placing)

    def test_unaffordable_card_does_not_close_nor_select(self):
        self._open_shop()
        self.window.placing = False
        self.controller.model.stars = 0
        center = self.window.shop.cards[5]["rect"].center
        self.assertEqual(
            self.window.shop.handle_click(center),
            ("insufficient", "torre_06"),
        )
        self.assertTrue(self.window.shop.is_open)
        self.assertFalse(self.window.placing)

    def test_escape_closes_the_shop(self):
        self._open_shop()
        pygame.event.clear()
        pygame.event.post(_key_event(pygame.K_ESCAPE))
        self.assertTrue(self.window.process_events())
        self.assertFalse(self.window.shop.is_open)
        self.assertFalse(self.window.paused)

    def test_close_button_closes_the_shop(self):
        self._open_shop()
        result = self.window.shop.handle_click(self.window.shop.close_rect.center)
        self.assertEqual(result, ("close",))
        self.assertFalse(self.window.shop.is_open)

    def test_map_click_is_ignored_while_the_shop_is_open(self):
        self._open_shop()
        antes = len(self.controller.model.towers)
        spot = self._valid_spot()
        screen_pos = self.window.map_to_screen(*spot)
        pygame.event.clear()
        pygame.event.post(_click_event(screen_pos))
        self.assertTrue(self.window.process_events())
        self.assertIsNone(self.window._pending_click)
        self.assertEqual(len(self.controller.model.towers), antes)

    def test_selected_tower_places_with_the_existing_system(self):
        self._open_shop()
        self._click_card(1)
        self.assertEqual(self.window.selected_kind, "fuego")

        spot = self._valid_spot()
        self.window._pending_click = self.window.map_to_screen(*spot)
        self.window.draw()

        towers = self.controller.model.towers
        self.assertEqual(len(towers), 1)
        self.assertEqual(towers[0].kind, "fuego")

    def test_escape_cancels_placement_before_opening_pause(self):
        # Se arma la colocacion eligiendo una torre en la tienda (la
        # partida ya no inicia con seleccion, torreta.md). El primer
        # ESC cancela la colocacion; el segundo abre el menu de pausa
        # en lugar de cerrar la app (menu.md).
        self._open_shop()
        self._click_card(0)
        self.assertTrue(self.window.placing)
        pygame.event.clear()
        pygame.event.post(_key_event(pygame.K_ESCAPE))
        self.assertTrue(self.window.process_events())
        self.assertFalse(self.window.placing)
        self.assertIsNone(self.window.selected_kind)

        pygame.event.clear()
        pygame.event.post(_key_event(pygame.K_ESCAPE))
        self.assertTrue(self.window.process_events())
        self.assertTrue(self.window.pause_menu.is_open)

    def _valid_spot(self):
        radius = GameWindow.TOWER_FOOTPRINT
        for px, py in self.tiled_map.path_points:
            for dx, dy in ((0, radius * 3), (radius * 3, 0), (-radius * 3, 0)):
                x, y = px + dx, py + dy
                valid, _ = self.tiled_map.can_place_tower(x, y, radius)
                if valid:
                    return x, y
        self.fail("No hay una posicion valida cerca del camino")


if __name__ == "__main__":
    unittest.main()
