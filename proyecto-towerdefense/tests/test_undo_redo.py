"""
Pruebas de Undo, Redo y venta de torres (undoredo.md).

Comprueba que:

    - Undo elimina la ultima torre colocada y devuelve el 100% del costo
    - solo se puede deshacer UNA colocacion como maximo
    - Redo restaura la torre y descuenta su precio de nuevo
    - Redo falla de forma segura sin estrellas o con la posicion ocupada,
      sin perder la accion pendiente
    - colocar una nueva torre despues de Undo invalida el Redo
    - la venta reembolsa el 50% del precio (redondeo // 2)
    - una torre vendida no puede recuperarse con Undo ni con Redo
    - los botones de la ventana no duplican dinero ni torres
    - las pilas propias (Stack) siguen siendo las que sostienen el sistema

Ejecutar desde la raiz del proyecto:

    py -m pytest -v
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import unittest

import pygame

from Controller.game_controller import GameController
from Model.game_model import GameModel, tower_price
from Model.structures import Stack
from View.game_window import GameWindow
from View.tiled_map import TiledMap

MAP_PATH = os.path.join("assets", "mapas", "mapa_principal.tmx")


def _click_event(pos, button=1):
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos, button=button)


class TestUndoRedoModel(unittest.TestCase):
    """Undo/Redo de colocaciones directamente sobre el modelo."""

    def setUp(self):
        pygame.display.set_mode((1, 1))
        self.model = GameModel()
        self.tiled_map = TiledMap(MAP_PATH)

    def _valid_spot(self):
        radius = GameWindow.TOWER_FOOTPRINT
        for px, py in self.tiled_map.path_points:
            for dx, dy in ((0, radius * 3), (radius * 3, 0), (-radius * 3, 0)):
                x, y = px + dx, py + dy
                valid, _ = self.tiled_map.can_place_tower(x, y, radius)
                if valid:
                    return x, y
        self.fail("No hay una posicion valida cerca del camino")

    def _buy(self, kind="basica", spot=None):
        x, y = spot if spot is not None else self._valid_spot()
        tower = self.model.buy_tower(
            kind=kind,
            range=GameWindow.TOWER_RANGE_PX,
            position=0.0,
            map_x=x,
            map_y=y,
            footprint=GameWindow.TOWER_FOOTPRINT,
        )
        self.assertIsNotNone(tower)
        return tower

    def test_undo_removes_the_last_placed_tower(self):
        self._buy()
        self.assertEqual(len(self.model.towers), 1)
        action = self.model.undo_last_placement()
        self.assertIsNotNone(action)
        self.assertEqual(len(self.model.towers), 0)

    def test_undo_refunds_100_percent_of_the_cost(self):
        self._buy("fuego")
        self.assertEqual(self.model.stars, 500 - tower_price("fuego"))
        self.model.undo_last_placement()
        self.assertEqual(self.model.stars, 500)

    def test_undo_is_only_available_once(self):
        self._buy()
        self._buy()
        self.assertTrue(self.model.can_undo())
        self.model.undo_last_placement()
        # Una sola accion deshecha como maximo: hasta Redo o colocar otra.
        self.assertFalse(self.model.can_undo())
        self.assertIsNone(self.model.undo_last_placement())

    def test_redo_restores_the_tower(self):
        self._buy()
        self.model.undo_last_placement()
        action = self.model.redo_last_placement(self.tiled_map)
        self.assertIsNotNone(action)
        self.assertEqual(len(self.model.towers), 1)
        self.assertEqual(self.model.towers[0].kind, action["kind"])
        self.assertEqual(self.model.towers[0].map_x, action["map_x"])
        self.assertEqual(self.model.towers[0].map_y, action["map_y"])

    def test_redo_charges_the_price_again(self):
        self._buy("fuego")
        self.model.undo_last_placement()
        self.assertEqual(self.model.stars, 500)
        self.model.redo_last_placement(self.tiled_map)
        self.assertEqual(self.model.stars, 500 - tower_price("fuego"))

    def test_redo_cannot_be_repeated_immediately(self):
        self._buy()
        self.model.undo_last_placement()
        self.model.redo_last_placement(self.tiled_map)
        self.assertFalse(self.model.can_redo())
        self.assertIsNone(self.model.redo_last_placement(self.tiled_map))
        self.assertEqual(len(self.model.towers), 1)

    def test_redo_fails_safely_without_enough_stars(self):
        self._buy()
        self.model.undo_last_placement()
        self.model.stars = tower_price("basica") - 1
        stars = self.model.stars
        self.assertIsNone(self.model.redo_last_placement(self.tiled_map))
        self.assertEqual(len(self.model.towers), 0)
        self.assertEqual(self.model.stars, stars)
        # La accion pendiente se conserva para poder reintentar.
        self.assertTrue(self.model.can_redo())
        self.model.stars = 500
        self.assertIsNotNone(self.model.redo_last_placement(self.tiled_map))
        self.assertEqual(len(self.model.towers), 1)

    def test_redo_fails_safely_if_the_position_is_taken(self):
        spot = self._valid_spot()
        self._buy(spot=spot)
        self.model.undo_last_placement()
        # Otra torre ocupa la misma coordenada mientras tanto.
        self.model.create_tower(
            kind="basica",
            range=GameWindow.TOWER_RANGE_PX,
            position=0.0,
            map_x=spot[0],
            map_y=spot[1],
            footprint=GameWindow.TOWER_FOOTPRINT,
        )
        stars = self.model.stars
        self.assertIsNone(self.model.redo_last_placement(self.tiled_map))
        self.assertEqual(len(self.model.towers), 1)
        self.assertEqual(self.model.stars, stars)
        self.assertTrue(self.model.can_redo())

    def test_new_placement_after_undo_invalidates_redo(self):
        self._buy()
        self.model.undo_last_placement()
        self.assertTrue(self.model.can_redo())
        self._buy()
        self.assertFalse(self.model.can_redo())
        self.assertIsNone(self.model.redo_last_placement(self.tiled_map))
        self.assertEqual(len(self.model.towers), 1)
        self.assertEqual(self.model.stars, 500 - tower_price("basica"))

    def test_repeated_undo_redo_cycles_never_duplicate_money_or_towers(self):
        self._buy("pesada")
        for _ in range(5):
            self.model.undo_last_placement()
        self.assertEqual(self.model.stars, 500)
        self.assertEqual(len(self.model.towers), 0)
        for _ in range(5):
            self.model.redo_last_placement(self.tiled_map)
        self.assertEqual(self.model.stars, 500 - tower_price("pesada"))
        self.assertEqual(len(self.model.towers), 1)

    def test_the_stacks_are_the_own_stack_structure(self):
        self.assertIsInstance(self.model.undo_stack, Stack)
        self.assertIsInstance(self.model.redo_stack, Stack)
        self._buy()
        self.assertIsInstance(self.model.undo_stack.peek(), dict)

    def test_script_path_towers_are_not_registered_for_undo(self):
        self.model.create_tower(kind="basica", map_x=0.0, map_y=0.0)
        self.assertFalse(self.model.can_undo())
        self.assertIsNone(self.model.undo_last_placement())


class TestSellTowerModel(unittest.TestCase):
    """Venta de torres con el martillo sobre el modelo."""

    def setUp(self):
        pygame.display.set_mode((1, 1))
        self.model = GameModel()
        self.tiled_map = TiledMap(MAP_PATH)

    def _valid_spot(self):
        radius = GameWindow.TOWER_FOOTPRINT
        for px, py in self.tiled_map.path_points:
            for dx, dy in ((0, radius * 3), (radius * 3, 0), (-radius * 3, 0)):
                x, y = px + dx, py + dy
                valid, _ = self.tiled_map.can_place_tower(x, y, radius)
                if valid:
                    return x, y
        self.fail("No hay una posicion valida cerca del camino")

    def _buy(self, kind="basica"):
        x, y = self._valid_spot()
        tower = self.model.buy_tower(
            kind=kind,
            range=GameWindow.TOWER_RANGE_PX,
            position=0.0,
            map_x=x,
            map_y=y,
            footprint=GameWindow.TOWER_FOOTPRINT,
        )
        self.assertIsNotNone(tower)
        return tower

    def test_sell_refunds_50_percent_of_the_cost(self):
        tower = self._buy("pesada")
        paid = tower_price("pesada")
        refund = self.model.sell_tower(tower)
        self.assertEqual(refund, paid // 2)
        self.assertEqual(self.model.stars, 500 - paid + paid // 2)
        self.assertEqual(len(self.model.towers), 0)

    def test_sell_refund_uses_floor_division(self):
        # Regla documentada: reembolso entero con // 2 (hacia abajo).
        tower = self._buy("fuego")
        self.assertEqual(self.model.sell_tower(tower), tower_price("fuego") // 2)

    def test_a_tower_cannot_be_sold_twice(self):
        tower = self._buy()
        self.assertGreater(self.model.sell_tower(tower), 0)
        stars = self.model.stars
        self.assertEqual(self.model.sell_tower(tower), 0)
        self.assertEqual(self.model.stars, stars)

    def test_sold_tower_cannot_be_recovered_with_undo(self):
        self._buy()
        self.assertTrue(self.model.can_undo())
        tower = self.model.towers[0]
        self.model.sell_tower(tower)
        # La accion pendiente se descarto al vender la torre.
        self.assertFalse(self.model.can_undo())
        self.assertIsNone(self.model.undo_last_placement())
        self.assertEqual(len(self.model.towers), 0)

    def test_selling_invalidates_the_undone_redo_only_if_needed(self):
        first = self._buy()
        self._buy()
        self.model.undo_last_placement()
        # La primera torre sigue en el mapa y su accion esta en undo.
        stars = self.model.stars
        self.model.sell_tower(first)
        # Sin acciones de Undo que referencien la torre vendida.
        self.assertFalse(self.model.can_undo())
        # El Redo de la segunda torre sigue siendo valido.
        self.assertTrue(self.model.can_redo())
        self.assertIsNotNone(self.model.redo_last_placement(self.tiled_map))
        self.assertEqual(len(self.model.towers), 1)
        self.assertEqual(
            self.model.stars,
            stars - tower_price("basica") + tower_price("basica") // 2,
        )

    def test_selling_the_undone_tower_keeps_redo_safe(self):
        self._buy()
        self.model.undo_last_placement()
        # La torre desecha ya no esta en el mapa: vender otra no la toca.
        other = self.model.create_tower(
            kind="basica",
            range=GameWindow.TOWER_RANGE_PX,
            position=0.0,
            map_x=0.0,
            map_y=0.0,
            footprint=GameWindow.TOWER_FOOTPRINT,
        )
        self.model.undo_stack.push({"tower": other})
        self.model.sell_tower(other)
        self.assertFalse(self.model.can_undo())
        self.assertTrue(self.model.can_redo())


class TestUndoRedoAndSellThroughTheWindow(unittest.TestCase):
    """Flujo completo por la ventana: botones, martillo y Escape."""

    def setUp(self):
        pygame.display.set_mode((GameWindow.WIDTH, GameWindow.HEIGHT))
        self.controller = GameController(view=None, spawn_interval=9999.0)
        self.tiled_map = TiledMap(MAP_PATH)
        self.controller.model.path_length = self.tiled_map.path_length()
        self.window = GameWindow(self.controller.model, self.tiled_map)
        # La partida ya no inicia con torre seleccionada (torreta.md):
        # se arma la colocacion como si el jugador la hubiera elegido.
        self.window.selected_kind = "basica"
        self.window.placing = True

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

    def _place_tower(self):
        model = self.controller.model
        before = len(model.towers)
        self.window._pending_click = self.window.map_to_screen(*self._valid_spot())
        self.window.draw()
        self.assertEqual(len(model.towers), before + 1)
        return model.towers[-1]

    def _click(self, pos):
        pygame.event.clear()
        pygame.event.post(_click_event(pos))
        self.assertTrue(self.window.process_events())

    def test_undo_button_removes_the_tower_and_refunds(self):
        tower = self._place_tower()
        model = self.controller.model
        self.assertEqual(model.stars, 400)
        self._click(self.window.undo_button_rect.center)
        self.assertNotIn(tower, model.towers)
        self.assertEqual(model.stars, 500)

    def test_redo_button_restores_the_tower_and_charges(self):
        self._place_tower()
        model = self.controller.model
        self._click(self.window.undo_button_rect.center)
        self.assertEqual(model.stars, 500)
        self._click(self.window.redo_button_rect.center)
        self.assertEqual(len(model.towers), 1)
        self.assertEqual(model.stars, 400)

    def test_clicking_the_buttons_repeatedly_never_duplicates(self):
        model = self.controller.model
        self._place_tower()
        for _ in range(4):
            self._click(self.window.undo_button_rect.center)
        self.assertEqual(model.stars, 500)
        self.assertEqual(len(model.towers), 0)
        for _ in range(4):
            self._click(self.window.redo_button_rect.center)
        self.assertEqual(model.stars, 400)
        self.assertEqual(len(model.towers), 1)

    def test_hammer_click_activates_and_cancels_the_sell_mode(self):
        self.assertFalse(self.window.selling)
        self._click(self.window.hammer_button_rect.center)
        self.assertTrue(self.window.selling)
        self.assertFalse(self.window.placing)
        self._click(self.window.hammer_button_rect.center)
        self.assertFalse(self.window.selling)

    def test_escape_cancels_the_sell_mode(self):
        self._click(self.window.hammer_button_rect.center)
        self.assertTrue(self.window.selling)
        pygame.event.clear()
        pygame.event.post(
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
        )
        self.assertTrue(self.window.process_events())
        self.assertFalse(self.window.selling)

    def test_hammer_sells_the_clicked_tower_for_50_percent(self):
        tower = self._place_tower()
        model = self.controller.model
        self._click(self.window.hammer_button_rect.center)
        self._click(self.window.map_to_screen(tower.map_x, tower.map_y))
        self.assertNotIn(tower, model.towers)
        self.assertEqual(model.stars, 400 + tower_price(tower.kind) // 2)
        # El modo venta termina solo tras vender.
        self.assertFalse(self.window.selling)

    def test_clicking_empty_ground_in_sell_mode_sells_nothing(self):
        self._place_tower()
        model = self.controller.model
        self._click(self.window.hammer_button_rect.center)
        # Un punto del extremo opuesto del mapa, lejos de cualquier torre.
        self._click((GameWindow.WIDTH - 4, 4))
        self.assertEqual(len(model.towers), 1)
        self.assertEqual(model.stars, 400)
        self.assertTrue(self.window.selling)

    def test_selling_works_clicking_the_upper_part_of_the_sprite(self):
        tower = self._place_tower()
        model = self.controller.model
        self._click(self.window.hammer_button_rect.center)
        hitbox = self.window._tower_hitbox(tower)
        # La hitbox cubre la parte alta del sprite, por encima de la base.
        base_y = self.window.map_to_screen(tower.map_x, tower.map_y)[1]
        self.assertLess(hitbox.top, base_y)
        self._click((hitbox.centerx, hitbox.top + 4))
        self.assertNotIn(tower, model.towers)
        self.assertEqual(
            model.stars, 400 + tower_price(tower.kind) // 2
        )

    def test_clicking_just_above_the_sprite_does_not_sell(self):
        tower = self._place_tower()
        model = self.controller.model
        self._click(self.window.hammer_button_rect.center)
        hitbox = self.window._tower_hitbox(tower)
        self._click((hitbox.centerx, hitbox.top - 10))
        self.assertIn(tower, model.towers)
        self.assertEqual(model.stars, 400)
        self.assertTrue(self.window.selling)

    def test_sell_hitbox_clips_the_transparent_top_of_the_png(self):
        # El lienzo del frame tiene ~la mitad superior transparente
        # (fix.md): la hitbox debe recortarse al contenido visible y
        # terminar cerca de su parte superior, no al nivel del lienzo.
        tower = self._place_tower()
        frame = self.window.animations.idle(tower.kind)
        anchor = self.window.animations.anchor(tower.kind)
        base_x, base_y = self.window.map_to_screen(tower.map_x, tower.map_y)
        drawn_left = int(base_x) - anchor[0]
        drawn_top = int(base_y) - anchor[1]
        visible = frame.get_bounding_rect()
        hitbox = self.window._tower_hitbox(tower)
        # Arriba: apenas el margen de tolerancia sobre el contenido real.
        self.assertEqual(
            hitbox.top,
            drawn_top + visible.y - GameWindow.SELL_HITBOX_PAD_TOP,
        )
        # La hitbox sigue cubriendo la base (donde la torre toca el suelo).
        self.assertGreaterEqual(hitbox.bottom, int(base_y))
        # Izquierda: como maximo el margen estrecho fuera del contenido.
        self.assertEqual(
            hitbox.left,
            drawn_left + visible.x - GameWindow.SELL_HITBOX_PAD_LEFT,
        )

    def test_overlapping_hitboxes_prioritize_the_tower_in_front(self):
        model = self.controller.model
        x, y = self._valid_spot()
        # Dos torres casi superpuestas (solo para la hitbox de venta):
        # la segunda esta mas abajo, asi que se dibuja encima (Y-sorting).
        model.create_tower(
            kind="basica",
            range=GameWindow.TOWER_RANGE_PX,
            position=0.0,
            map_x=x,
            map_y=y,
            footprint=GameWindow.TOWER_FOOTPRINT,
        )
        front = model.create_tower(
            kind="basica",
            range=GameWindow.TOWER_RANGE_PX,
            position=0.0,
            map_x=x,
            map_y=y + 10,
            footprint=GameWindow.TOWER_FOOTPRINT,
        )
        back_hitbox = self.window._tower_hitbox(model.towers[0])
        front_hitbox = self.window._tower_hitbox(front)
        self.assertTrue(back_hitbox.colliderect(front_hitbox))
        overlap = back_hitbox.clip(front_hitbox).center
        self.assertIs(self.window._tower_at_screen(*overlap), front)

    def test_ui_clicks_do_not_sell_while_the_sell_mode_is_active(self):
        self._place_tower()
        model = self.controller.model
        self._click(self.window.hammer_button_rect.center)
        self.assertTrue(self.window.selling)
        # El martillo cancela el modo sin vender nada.
        self._click(self.window.hammer_button_rect.center)
        self.assertFalse(self.window.selling)
        self.assertEqual(len(model.towers), 1)
        self.assertEqual(model.stars, 400)
        # El boton Undo deshace (reembolso del 100%), nunca vende (50%).
        self._click(self.window.hammer_button_rect.center)
        self._click(self.window.undo_button_rect.center)
        self.assertEqual(len(model.towers), 0)
        self.assertEqual(model.stars, 500)
        self.assertTrue(self.window.selling)

    def test_sold_tower_is_not_recoverable_with_the_undo_button(self):
        self._place_tower()
        model = self.controller.model
        self._click(self.window.hammer_button_rect.center)
        screen_pos = self.window.map_to_screen(
            model.towers[0].map_x, model.towers[0].map_y
        )
        self._click(screen_pos)
        self.assertFalse(model.can_undo())
        self._click(self.window.undo_button_rect.center)
        self.assertEqual(len(model.towers), 0)
        self.assertEqual(
            model.stars,
            400 + tower_price("basica") // 2,
        )

    def test_placing_a_new_tower_after_undo_disables_the_redo_button(self):
        model = self.controller.model
        self._place_tower()
        self._click(self.window.undo_button_rect.center)
        self.assertTrue(model.can_redo())
        self._place_tower()
        self.assertFalse(model.can_redo())
        self.assertEqual(len(model.towers), 1)

    def test_button_clicks_do_not_place_towers_on_the_map(self):
        model = self.controller.model
        self.window.placing = True
        self._click(self.window.undo_button_rect.center)
        self._click(self.window.redo_button_rect.center)
        self.assertEqual(len(model.towers), 0)
        self.assertEqual(model.stars, 500)

    def test_controller_wrappers_coordinate_the_operations(self):
        model = self.controller.model
        x, y = self._valid_spot()
        tower = self.controller.buy_tower(
            kind="basica",
            range=GameWindow.TOWER_RANGE_PX,
            position=0.0,
            map_x=x,
            map_y=y,
            footprint=GameWindow.TOWER_FOOTPRINT,
        )
        self.assertIsNotNone(tower)
        self.assertEqual(model.stars, 400)
        self.assertIsNotNone(self.controller.undo_tower())
        self.assertEqual(model.stars, 500)
        self.assertIsNotNone(self.controller.redo_tower(self.tiled_map))
        self.assertEqual(model.stars, 400)
        refund = self.controller.sell_tower(model.towers[0])
        self.assertEqual(refund, tower_price("basica") // 2)
        self.assertEqual(model.towers, [])


if __name__ == "__main__":
    unittest.main()
