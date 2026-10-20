"""
Balance de las 12 torres (datos.md).

Comprueba la configuracion centralizada TOWER_KINDS:

    - la tabla exacta de danio e intervalo de las 12 torres
    - el alcance unico de 210 px (TOWER_RANGE) en todos los tipos
    - los precios de la tienda sin alterar (SHOP_TOWER_PRICES)
    - que las 12 estan integradas en combate (tienda, animaciones,
      danio aplicado y cadencia de ataque)
    - que la cadencia se mide con dt y no depende de los FPS
    - la prioridad de atacar al enemigo con menor vida en su alcance

Ejecutar desde la raiz del proyecto:

    py -m pytest -v
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import unittest

from Controller.game_controller import GameController
from Model.game_model import (
    GameModel,
    PLAYABLE_TOWER_PRICES,
    SHOP_TOWER_PRICES,
    TOWER_KINDS,
    TOWER_RANGE,
)
from View.game_window import GameWindow
from View.shop_panel import SHOP_TOWERS
from View.tower_animations import KIND_VARIANTS

# Tabla de datos.md en orden (torre 01..12): kind, danio, intervalo.
BALANCE = (
    ("basica", 10, 1.0),
    ("fuego", 14, 0.9),
    ("pesada", 22, 1.1),
    ("torre_04", 12, 0.5),
    ("torre_05", 35, 1.2),
    ("torre_06", 20, 0.6),
    ("torre_07", 50, 1.3),
    ("torre_08", 30, 0.7),
    ("torre_09", 65, 1.4),
    ("torre_10", 40, 0.8),
    ("torre_11", 80, 1.5),
    ("torre_12", 55, 0.9),
)

EXPECTED_PRICES = (100, 150, 200, 250, 300, 350, 400, 450, 500, 550, 600, 650)


class TestBalanceTable(unittest.TestCase):
    """La tabla de datos.md vive centralizada en TOWER_KINDS."""

    def test_damage_and_interval_match_the_table_for_twelve_kinds(self):
        self.assertEqual(len(TOWER_KINDS), 12)
        for kind, damage, interval in BALANCE:
            spec = TOWER_KINDS[kind]
            self.assertEqual(spec["damage"], damage, kind)
            self.assertEqual(spec["attack_interval"], interval, kind)

    def test_every_kind_uses_the_common_range_of_210_pixels(self):
        self.assertEqual(TOWER_RANGE, 210.0)
        self.assertEqual(GameWindow.TOWER_RANGE_PX, TOWER_RANGE)
        for kind, _, _ in BALANCE:
            self.assertEqual(TOWER_KINDS[kind]["range"], TOWER_RANGE, kind)

    def test_prices_are_untouched_and_mapped_to_every_kind(self):
        self.assertEqual(SHOP_TOWER_PRICES, EXPECTED_PRICES)
        for index, (kind, _, _) in enumerate(BALANCE):
            self.assertEqual(
                PLAYABLE_TOWER_PRICES[kind], EXPECTED_PRICES[index], kind
            )

    def test_created_towers_take_the_table_stats_by_default(self):
        model = GameModel()
        for kind, damage, interval in BALANCE:
            tower = model.create_tower(kind=kind)
            self.assertEqual(tower.damage, damage, kind)
            self.assertEqual(tower.attack_interval, interval, kind)
            self.assertEqual(tower.range, TOWER_RANGE, kind)


class TestTwelveTowersIntegrated(unittest.TestCase):
    """Las 12 torres estan cables a tienda, animaciones y combate."""

    def test_shop_cards_and_animations_cover_every_kind(self):
        for index, (kind, _, _) in enumerate(BALANCE):
            entry = SHOP_TOWERS[index]
            self.assertEqual(entry["kind"], kind, index)
            self.assertEqual(KIND_VARIANTS[kind], entry["variant"], kind)
            self.assertEqual(PLAYABLE_TOWER_PRICES[kind], entry["price"])

    def test_buying_any_kind_charges_its_catalog_price(self):
        model = GameModel()
        for index, (kind, _, _) in enumerate(BALANCE):
            model.stars = 100000
            tower = model.buy_tower(kind=kind)
            self.assertIsNotNone(tower, kind)
            self.assertEqual(model.stars, 100000 - EXPECTED_PRICES[index], kind)

    def test_controller_place_tower_defaults_to_kind_stats(self):
        controller = GameController(view=None, spawn_interval=9999.0)
        for kind, damage, interval in BALANCE:
            tower = controller.place_tower(kind=kind, position=0.0)
            self.assertEqual(tower.kind, kind)
            self.assertEqual(tower.damage, damage, kind)
            self.assertEqual(tower.attack_interval, interval, kind)
            self.assertEqual(tower.range, TOWER_RANGE, kind)


class TestCombatPerKind(unittest.TestCase):
    """Danio, alcance y cadencia de cada tipo en el combate real."""

    def _new_game(self):
        controller = GameController(view=None, spawn_interval=9999.0)
        return controller, controller.model

    @staticmethod
    def _spawn_still_enemy(model, hp, progress=0.0):
        enemy = model.create_enemy(hp=hp, speed=0.0)
        model.add_to_wave(enemy)
        enemy = model.spawn_next()
        enemy.progress = progress
        return enemy

    def test_each_kind_applies_its_damage_inside_its_range(self):
        for kind, damage, _ in BALANCE:
            controller, model = self._new_game()
            controller.place_tower(kind=kind, position=0.0)
            enemy = self._spawn_still_enemy(model, hp=1000, progress=TOWER_RANGE)

            controller.update(0.05)

            self.assertEqual(enemy.hp, 1000 - damage, kind)
            self.assertEqual(len(model.shots), 1, kind)

    def test_enemy_out_of_the_common_range_is_not_hit(self):
        for kind, _, _ in BALANCE:
            controller, model = self._new_game()
            controller.place_tower(kind=kind, position=0.0)
            enemy = self._spawn_still_enemy(
                model, hp=1000, progress=TOWER_RANGE + 1.0
            )

            controller.update(0.05)

            self.assertEqual(enemy.hp, 1000, kind)
            self.assertEqual(len(model.shots), 0, kind)

    def test_attack_interval_does_not_depend_on_the_frame_rate(self):
        def shots_over(total_time, step):
            controller, model = self._new_game()
            controller.place_tower(kind="basica", position=0.0)
            enemy = self._spawn_still_enemy(model, hp=100000)
            shots = 0
            for _ in range(int(round(total_time / step))):
                controller.update(step)
                shots += len(model.shots)
            return shots, enemy

        # basica: intervalo 1.0 s; el primer disparo sale en el primer
        # update y despues uno por cada segundo completo de cooldown.
        coarse, enemy_a = shots_over(2.0, 0.1)
        fine, enemy_b = shots_over(2.0, 0.05)
        self.assertEqual(coarse, 2)
        self.assertEqual(fine, 2)
        self.assertEqual(enemy_a.hp, 100000 - 2 * 10)
        self.assertEqual(enemy_b.hp, 100000 - 2 * 10)

        # A mitad de intervalo (0.5 s) solo ha disparado una vez.
        half, _ = shots_over(0.5, 0.1)
        self.assertEqual(half, 1)

    def test_lowest_hp_enemy_is_attacked_first(self):
        controller, model = self._new_game()
        tower = controller.place_tower(kind="basica", position=0.0)
        weak = self._spawn_still_enemy(model, hp=50)
        strong = self._spawn_still_enemy(model, hp=80)

        controller.update(0.05)

        self.assertEqual(len(model.shots), 1)
        self.assertIs(model.shots[0]["enemy"], weak)
        self.assertEqual(weak.hp, 50 - tower.damage)
        self.assertEqual(strong.hp, 80)


if __name__ == "__main__":
    unittest.main()
