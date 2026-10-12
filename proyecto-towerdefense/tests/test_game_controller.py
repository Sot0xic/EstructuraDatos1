"""
Pruebas del controlador: movimiento y combate en update() (Semana 2).

Comprueba que:

    - los enemigos activos avanzan con el tiempo
    - los enemigos pendientes no avanzan
    - la cola va soltando enemigos poco a poco
    - las torres atacan a los enemigos en su alcance
    - los enemigos derrotados desaparecen de la lista activa

Ejecutar desde la raiz del proyecto:

    py -m pytest -v
"""

import unittest

from Controller.game_controller import GameController


class TestGameController(unittest.TestCase):
    """Pruebas de integracion movimiento + combate."""

    def setUp(self):
        self.controller = GameController(view=None, spawn_interval=1.5)
        self.model = self.controller.model

    def test_controller_keeps_basic_commands(self):
        for name in (
            "start_wave",
            "spawn_next",
            "spawn_all",
            "attack",
            "undo",
            "render",
            "update",
        ):
            self.assertTrue(callable(getattr(self.controller, name)))

    def test_render_without_view_does_not_fail(self):
        self.controller.start_wave([{"hp": 100, "speed": 1.0}])
        self.controller.render()
        self.assertEqual(self.model.pending_count, 1)

    def test_update_advances_active_enemies(self):
        self.controller.start_wave([{"hp": 100, "speed": 2.0}])
        self.controller.spawn_all()
        enemy = self.model.active_enemies.to_list()[0]

        self.controller.update(3.0)

        self.assertEqual(enemy.progress, 6.0)

    def test_update_does_not_advance_pending_enemies(self):
        controller = GameController(view=None, spawn_interval=9999.0)
        controller.start_wave(
            [
                {"hp": 100, "speed": 2.0},
                {"hp": 100, "speed": 2.0},
            ]
        )

        controller.update(10.0)

        self.assertEqual(controller.model.pending_count, 2)
        self.assertEqual(controller.model.active_count, 0)
        for enemy in controller.model.pending_enemies.to_list():
            self.assertEqual(enemy.progress, 0.0)

    def test_update_spawns_enemies_over_time(self):
        self.controller.start_wave(
            [
                {"hp": 100, "speed": 2.0},
                {"hp": 100, "speed": 2.0},
            ]
        )

        self.controller.update(1.5)
        self.assertEqual(self.model.active_count, 1)
        self.assertEqual(self.model.pending_count, 1)

        self.controller.update(1.5)
        self.assertEqual(self.model.active_count, 2)
        self.assertEqual(self.model.pending_count, 0)

    def test_update_tower_attacks_enemy_in_range(self):
        self.controller.start_wave([{"hp": 100, "speed": 1.0}])
        self.controller.spawn_all()
        self.controller.place_tower(damage=30, range=5.0, position=0.0)
        enemy = self.model.active_enemies.to_list()[0]

        self.controller.update(0.1)

        self.assertEqual(enemy.hp, 70)
        self.assertEqual(self.model.active_count, 1)

    def test_update_tower_ignores_enemy_out_of_range(self):
        self.controller.start_wave([{"hp": 100, "speed": 1.0}])
        self.controller.spawn_all()
        self.controller.place_tower(damage=30, range=3.0, position=30.0)
        enemy = self.model.active_enemies.to_list()[0]

        self.controller.update(1.0)

        self.assertEqual(enemy.hp, 100)
        self.assertEqual(self.model.active_count, 1)

    def test_update_removes_defeated_enemy(self):
        self.controller.start_wave([{"hp": 50, "speed": 1.0}])
        self.controller.spawn_all()
        self.controller.place_tower(damage=9999, range=10.0, position=0.0)

        self.controller.update(0.1)

        self.assertEqual(self.model.active_count, 0)
        self.assertEqual(len(self.model.active_enemies.to_list()), 0)

    def test_update_tower_attacks_only_one_enemy(self):
        self.controller.start_wave(
            [
                {"hp": 100, "speed": 1.0},
                {"hp": 40, "speed": 1.0},
            ]
        )
        self.controller.spawn_all()
        enemies = self.model.active_enemies.to_list()
        enemies[0].progress = 5.0  # el mas avanzado, pero con mas vida
        enemies[1].progress = 1.0  # el menos avanzado, pero con menos vida
        self.controller.place_tower(damage=30, range=10.0, position=0.0)

        self.controller.update(0.1)

        # la torre prioriza al enemigo con menos vida
        self.assertEqual(enemies[1].hp, 10)
        self.assertEqual(enemies[0].hp, 100)

    def test_update_removes_enemies_that_reach_the_end(self):
        self.controller.start_wave([{"hp": 100, "speed": 50.0}])
        self.controller.spawn_all()

        self.controller.update(1.0)

        self.assertEqual(self.model.active_count, 0)


if __name__ == "__main__":
    unittest.main()
