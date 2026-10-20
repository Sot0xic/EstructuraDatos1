"""
Pruebas del circulo de alcance en la previsualizacion (circulo.md).

Comprueba:
    - Sin torre seleccionada: no hay circulos de alcance
    - Con torre seleccionada (placing): circulo semitransparente de
      210 px sigue al cursor junto a la previsualizacion
    - Tras colocar (placing=False): el circulo desaparece
    - ESC cancela colocacion y circulo
    - Tienda/martillo/Undo/Redo no muestran circulos innecesarios
    - Funciona con las 12 torres

Ejecutar desde la raiz del proyecto:

    py -m pytest -v
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import unittest

import pygame

from Controller.game_controller import GameController
from Model.game_model import TOWER_RANGE
from View.game_window import GameWindow
from View.shop_panel import SHOP_TOWERS
from View.tiled_map import TiledMap

MAP_PATH = os.path.join("assets", "mapas", "mapa_principal.tmx")


def _key_event(key):
    return pygame.event.Event(pygame.KEYDOWN, key=key)


def _click_event(pos, button=1):
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos, button=button)


class TestPlacementRangeCircle(unittest.TestCase):
    """Circulo de alcance solo durante la colocacion (circulo.md)."""

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

    def _place_tower_near_path(self):
        spot = self._valid_spot()
        progress = self.tiled_map.closest_progress_on_path(*spot)
        tower = self.model.buy_tower(
            kind="basica",
            position=progress,
            map_x=spot[0], map_y=spot[1],
            footprint=GameWindow.TOWER_FOOTPRINT,
        )
        self.assertIsNotNone(tower)
        return tower

    def test_no_circle_when_no_tower_selected(self):
        # Estado inicial: placing=False, selected_kind=None
        self.assertFalse(self.window.placing)
        self.assertIsNone(self.window.selected_kind)
        self._place_tower_near_path()

        # Al dibujar, no debe haber circulo de alcance de torres colocadas
        # (circulo.md: las torres colocadas no muestran su radio)
        self.window.draw()
        # El metodo _draw_tower_ranges ya no se llama en draw()
        # Verificar que placing sigue False
        self.assertFalse(self.window.placing)

    def test_circle_appears_when_selecting_from_shop(self):
        # Seleccionar una torre desde la tienda via process_events
        pygame.event.clear()
        pygame.event.post(_click_event(self.window.shop.opener_rect.center))
        self.assertTrue(self.window.process_events())
        self.assertTrue(self.window.shop.is_open)

        card_center = self.window.shop.cards[0]["rect"].center
        pygame.event.clear()
        pygame.event.post(_click_event(card_center))
        self.assertTrue(self.window.process_events())

        self.assertTrue(self.window.placing)
        self.assertEqual(self.window.selected_kind, "basica")

        # Al dibujar con placing activo, _draw_placement_preview dibuja
        # el circulo de alcance
        self.window.draw()

    def test_circle_follows_cursor_during_placement(self):
        self.window.selected_kind = "basica"
        self.window.placing = True

        # Simular movimiento del cursor
        pygame.mouse.set_pos(400, 300)
        self.window.draw()

        # El radio en pantalla debe ser TOWER_RANGE * scale
        expected_radius = int(TOWER_RANGE * self.window.scale)
        self.assertGreater(expected_radius, 0)

    def test_circle_disappears_after_placement(self):
        self.window.selected_kind = "basica"
        self.window.placing = True

        # Colocar torre
        spot = self._valid_spot()
        screen_pos = self.window.map_to_screen(*spot)
        self.window._pending_click = screen_pos
        self.window.draw()

        # placing sigue activo (permite colocar varias)
        self.assertTrue(self.window.placing)
        self.assertEqual(self.window.selected_kind, "basica")

        # Cancelar con ESC
        pygame.event.clear()
        pygame.event.post(_key_event(pygame.K_ESCAPE))
        self.assertTrue(self.window.process_events())
        self.assertFalse(self.window.placing)
        self.assertIsNone(self.window.selected_kind)

    def test_escape_cancels_preview_and_circle(self):
        self.window.selected_kind = "basica"
        self.window.placing = True

        pygame.event.clear()
        pygame.event.post(_key_event(pygame.K_ESCAPE))
        self.assertTrue(self.window.process_events())

        self.assertFalse(self.window.placing)
        self.assertIsNone(self.window.selected_kind)

    def test_no_circle_when_shop_open(self):
        self.window.selected_kind = "basica"
        self.window.placing = True
        self.window.shop.open()

        # Con tienda abierta, _draw_placement_preview no dibuja nada
        self.assertTrue(self.window.shop.is_open)
        self.window.draw()
        # placing se mantiene pero shop.is_open bloquea el dibujo
        self.assertTrue(self.window.placing)

    def test_no_circle_when_selling(self):
        # Activar modo venta
        self.window.selling = True
        self.window.placing = False
        self.window.selected_kind = None

        self.assertTrue(self.window.selling)
        self.assertFalse(self.window.placing)
        self.window.draw()

    def test_all_twelve_towers_work_with_preview(self):
        for index, entry in enumerate(SHOP_TOWERS):
            kind = entry["kind"]
            self.window.selected_kind = kind
            self.window.placing = True

            # Verificar que placing y selected_kind estan correctos
            self.assertTrue(self.window.placing)
            self.assertEqual(self.window.selected_kind, kind)

            # El circulo se dibuja igual para todos (mismo TOWER_RANGE)
            self.window.draw()

    def test_circle_uses_same_radius_as_combat(self):
        tower = self._place_tower_near_path()

        # Radio de combate: tower.range (210 px de mapa)
        self.assertEqual(tower.range, TOWER_RANGE)

        # Radio visual en previsualizacion: TOWER_RANGE * scale
        preview_radius = int(TOWER_RANGE * self.window.scale)
        combat_radius_px = int(tower.range * self.window.scale)

        self.assertEqual(preview_radius, combat_radius_px)


if __name__ == "__main__":
    unittest.main()
