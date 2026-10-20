"""
Pruebas de la economia en estrellas (actualizacion.md).

Comprueba que:

    - el saldo inicial es 500 estrellas
    - los precios de las 12 variantes estan centralizados en el modelo
      y son los pedidos (100..650 en pasos de 50)
    - una compra valida crea la torre y descuenta su precio
    - una compra sin fondos no crea nada ni cobra
    - cancelar la colocacion no descuenta nada
    - una colocacion en posicion invalida no descuenta nada
    - cada enemigo eliminado por torres abona 25 estrellas, una sola vez
    - un enemigo que llega al final del camino no da estrellas
    - reset_economy vuelve el saldo a 500
    - la tienda muestra precios, marca lo no pagable y no inicia la
      compra sin fondos

Ejecutar desde la raiz del proyecto:

    py -m pytest -v
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import unittest

import pygame

from Controller.game_controller import GameController
from Model.game_model import (
    ENEMY_KILL_REWARD,
    SHOP_TOWER_PRICES,
    STARTING_STARS,
    GameModel,
    tower_price,
)
from View.game_window import GameWindow
from View.shop_panel import SHOP_TOWERS, ShopPanel
from View.tiled_map import TiledMap

MAP_PATH = os.path.join("assets", "mapas", "mapa_principal.tmx")


def _click_event(pos, button=1):
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos, button=button)


class TestPrices(unittest.TestCase):
    """Precios centralizados en una unica configuracion del modelo."""

    def test_prices_are_the_requested_ones(self):
        self.assertEqual(
            SHOP_TOWER_PRICES,
            (100, 150, 200, 250, 300, 350, 400, 450, 500, 550, 600, 650),
        )

    def test_every_shop_card_price_comes_from_the_model_config(self):
        for index, entry in enumerate(SHOP_TOWERS):
            self.assertEqual(entry["price"], SHOP_TOWER_PRICES[index], index)

    def test_playable_kinds_map_to_the_first_three_prices(self):
        self.assertEqual(tower_price("basica"), 100)
        self.assertEqual(tower_price("fuego"), 150)
        self.assertEqual(tower_price("pesada"), 200)

    def test_unknown_kind_costs_zero(self):
        self.assertEqual(tower_price("inexistente"), 0)


class TestBalance(unittest.TestCase):
    """Saldo inicial, compras y reinicio de la economia."""

    def setUp(self):
        self.model = GameModel()

    def test_initial_balance_is_500(self):
        self.assertEqual(self.model.stars, STARTING_STARS)
        self.assertEqual(self.model.stars, 500)

    def test_successful_purchase_creates_tower_and_discounts(self):
        tower = self.model.buy_tower(kind="basica")
        self.assertIsNotNone(tower)
        self.assertEqual(tower.kind, "basica")
        self.assertEqual(len(self.model.towers), 1)
        self.assertEqual(self.model.stars, 500 - 100)

    def test_purchase_without_enough_stars_creates_nothing_and_charges_nothing(self):
        self.model.stars = 99
        tower = self.model.buy_tower(kind="basica")
        self.assertIsNone(tower)
        self.assertEqual(len(self.model.towers), 0)
        self.assertEqual(self.model.stars, 99)

    def test_exact_balance_is_enough(self):
        self.model.stars = 100
        tower = self.model.buy_tower(kind="basica")
        self.assertIsNotNone(tower)
        self.assertEqual(self.model.stars, 0)

    def test_can_afford_reflects_the_balance(self):
        self.assertTrue(self.model.can_afford("basica"))
        self.model.stars = 100
        self.assertTrue(self.model.can_afford("basica"))
        self.assertFalse(self.model.can_afford("fuego"))

    def test_reset_economy_restores_the_initial_balance(self):
        self.model.buy_tower(kind="basica")
        self.assertEqual(self.model.stars, 400)
        self.model.reset_economy()
        self.assertEqual(self.model.stars, STARTING_STARS)


class TestKillReward(unittest.TestCase):
    """Recompensa de estrellas por enemigo eliminado por torres."""

    def setUp(self):
        self.model = GameModel()

    def _active_enemy(self, hp=10):
        enemy = self.model.create_enemy(hp=hp)
        self.model.add_to_wave(enemy)
        self.model.spawn_next()
        return enemy

    def test_kill_grants_25_stars_once(self):
        enemy = self._active_enemy(hp=10)
        killed, _ = self.model.tower_attack(enemy, damage=10)
        self.assertTrue(killed)
        self.assertEqual(self.model.stars, 500 + ENEMY_KILL_REWARD)
        self.assertEqual(self.model.stars, 525)

    def test_surviving_enemy_grants_nothing(self):
        enemy = self._active_enemy(hp=100)
        killed, _ = self.model.tower_attack(enemy, damage=10)
        self.assertFalse(killed)
        self.assertEqual(self.model.stars, 500)

    def test_reward_is_not_duplicated_on_a_second_lethal_hit(self):
        enemy = self._active_enemy(hp=10)
        self.model.tower_attack(enemy, damage=10)
        # El enemigo ya no esta activo: otro ataque no vuelve a pagar.
        killed, _ = self.model.tower_attack(enemy, damage=10)
        self.assertFalse(killed)
        self.assertEqual(self.model.stars, 525)

    def test_enemy_reaching_the_end_grants_nothing(self):
        enemy = self._active_enemy(hp=100)
        enemy.progress = self.model.path_length
        removed = self.model.remove_escaped()
        self.assertEqual(removed, [enemy])
        self.assertEqual(self.model.stars, 500)


class TestPurchaseFlowThroughTheWindow(unittest.TestCase):
    """Flujo de compra del jugador: tienda, colocacion y cancelacion."""

    def setUp(self):
        pygame.display.set_mode((GameWindow.WIDTH, GameWindow.HEIGHT))
        self.controller = GameController(view=None, spawn_interval=9999.0)
        self.tiled_map = TiledMap(MAP_PATH)
        self.controller.model.path_length = self.tiled_map.path_length()
        self.window = GameWindow(self.controller.model, self.tiled_map)

    def tearDown(self):
        self.window.close()

    def _open_shop(self):
        self.window.shop.open()

    def _click_card(self, index):
        self.window.shop.open()
        center = self.window.shop.cards[index]["rect"].center
        pygame.event.clear()
        pygame.event.post(_click_event(center))
        self.assertTrue(self.window.process_events())

    def _valid_spot(self):
        radius = GameWindow.TOWER_FOOTPRINT
        for px, py in self.tiled_map.path_points:
            for dx, dy in ((0, radius * 3), (radius * 3, 0), (-radius * 3, 0)):
                x, y = px + dx, py + dy
                valid, _ = self.tiled_map.can_place_tower(x, y, radius)
                if valid:
                    return x, y
        self.fail("No hay una posicion valida cerca del camino")

    def test_selecting_and_placing_a_tower_charges_its_price(self):
        self._click_card(0)
        self.assertTrue(self.window.placing)
        self.window._pending_click = self.window.map_to_screen(*self._valid_spot())
        self.window.draw()
        self.assertEqual(len(self.controller.model.towers), 1)
        self.assertEqual(self.controller.model.stars, 400)

    def test_selecting_without_funds_does_not_start_the_purchase(self):
        self.controller.model.stars = 50
        self.window.placing = False
        self._open_shop()
        center = self.window.shop.cards[0]["rect"].center
        result = self.window.shop.handle_click(center)
        self.assertEqual(result, ("insufficient", "basica"))
        self.assertTrue(self.window.shop.is_open)
        self.assertFalse(self.window.placing)

    def test_placement_without_funds_creates_nothing_and_charges_nothing(self):
        # Saldo suficiente para abrir la compra, agotado antes de colocar.
        self._click_card(0)
        self.controller.model.stars = 0
        spot = self._valid_spot()
        self.window._pending_click = self.window.map_to_screen(*spot)
        self.window.draw()
        self.assertEqual(len(self.controller.model.towers), 0)
        self.assertEqual(self.controller.model.stars, 0)

    def test_cancelling_placement_charges_nothing(self):
        self._click_card(0)
        self.assertTrue(self.window.placing)
        self.window.placing = False
        self.assertEqual(len(self.controller.model.towers), 0)
        self.assertEqual(self.controller.model.stars, 500)

    def test_invalid_placement_charges_nothing(self):
        self._click_card(0)
        antes = self.controller.model.stars
        # Click en una posicion bloqueada (el propio camino).
        px, py = self.tiled_map.path_points[0]
        self.window._pending_click = self.window.map_to_screen(px, py)
        self.window.draw()
        self.assertEqual(len(self.controller.model.towers), 0)
        self.assertEqual(self.controller.model.stars, antes)

    def test_controller_buy_tower_wrapper_charges(self):
        tower = self.controller.buy_tower(kind="fuego", position=0.0)
        self.assertIsNotNone(tower)
        self.assertEqual(self.controller.model.stars, 350)

    def test_coin_counter_reads_the_model_balance(self):
        self.controller.model.stars = 123
        self.window.draw()
        self.assertEqual(self.controller.model.stars, 123)


class TestShopAffordability(unittest.TestCase):
    """La tienda refleja el saldo: precios visibles y no pagables."""

    def setUp(self):
        pygame.display.set_mode((GameWindow.WIDTH, GameWindow.HEIGHT))
        self.model = GameModel()
        self.shop = ShopPanel(GameWindow.WIDTH, GameWindow.HEIGHT, self.model)

    def tearDown(self):
        self.shop.close()

    def test_all_twelve_cards_expose_a_price(self):
        for index in range(12):
            self.assertEqual(self.shop.tower_price(index), SHOP_TOWER_PRICES[index])

    def test_all_catalog_towers_follow_their_prices(self):
        for index in range(12):
            price = SHOP_TOWER_PRICES[index]
            self.model.stars = price - 1
            self.assertFalse(self.shop.tower_affordable(index), index)
            self.model.stars = price
            self.assertTrue(self.shop.tower_affordable(index), index)

    def test_playable_towers_follow_the_balance(self):
        self.assertTrue(all(self.shop.tower_affordable(i) for i in range(3)))
        self.model.stars = 120
        self.assertTrue(self.shop.tower_affordable(0))
        self.assertFalse(self.shop.tower_affordable(1))
        self.assertFalse(self.shop.tower_affordable(2))

    def test_draw_with_the_shop_open_renders_all_prices(self):
        self.model.stars = 50
        self.shop.open()
        surface = pygame.Surface((GameWindow.WIDTH, GameWindow.HEIGHT))
        self.shop.draw(surface)


if __name__ == "__main__":
    unittest.main()
