"""
Pruebas de la clase Tower (Dia 2 - Semana 2).

Comprueba el combate con torres:

    - alcance (dentro y fuera)
    - danio aplicado y vida que nunca baja de cero
    - enemigo derrotado fuera de la lista activa
    - la torre no ataca enemigos ya eliminados

Ejecutar desde la raiz del proyecto:

    py -m pytest -v
"""

import unittest

from Model.game_model import GameModel, Tower


class TestTower(unittest.TestCase):
    """Pruebas de la logica de combate de las torres."""

    def setUp(self):
        self.model = GameModel()

    def _active_enemy(self, hp=100, progress=0.0):
        enemy = self.model.create_enemy(hp=hp)
        self.model.add_to_wave(enemy)
        self.model.spawn_next()
        enemy.progress = progress
        return enemy

    def test_tower_has_required_attributes(self):
        tower = self.model.create_tower(
            name="Torre 1", damage=30, range=4.0, position=10.0
        )

        self.assertIsInstance(tower, Tower)
        self.assertEqual(tower.name, "Torre 1")
        self.assertEqual(tower.damage, 30)
        self.assertEqual(tower.range, 4.0)
        self.assertEqual(tower.position, 10.0)
        self.assertGreater(tower.tower_id, 0)
        self.assertIn(tower, self.model.towers)

    def test_towers_have_unique_ids(self):
        first = self.model.create_tower()
        second = self.model.create_tower()
        self.assertNotEqual(first.tower_id, second.tower_id)

    def test_is_in_range(self):
        tower = self.model.create_tower(range=5.0, position=10.0)
        enemy_in = self.model.create_enemy()
        enemy_in.progress = 8.0
        enemy_out = self.model.create_enemy()
        enemy_out.progress = 16.0

        self.assertTrue(tower.is_in_range(enemy_in))
        self.assertFalse(tower.is_in_range(enemy_out))

    def test_is_in_range_boundary(self):
        tower = self.model.create_tower(range=5.0, position=10.0)
        edge = self.model.create_enemy()
        edge.progress = 15.0
        beyond = self.model.create_enemy()
        beyond.progress = 15.1

        self.assertTrue(tower.is_in_range(edge))
        self.assertFalse(tower.is_in_range(beyond))

    def test_enemy_in_range_receives_damage(self):
        enemy = self._active_enemy(hp=100, progress=3.0)
        tower = self.model.create_tower(damage=30, range=5.0, position=0.0)

        killed, remaining = tower.attack(self.model, enemy)

        self.assertFalse(killed)
        self.assertEqual(remaining, 70)
        self.assertEqual(enemy.hp, 70)
        self.assertEqual(self.model.active_count, 1)

    def test_enemy_out_of_range_receives_no_damage(self):
        enemy = self._active_enemy(hp=100, progress=0.0)
        tower = self.model.create_tower(damage=30, range=3.0, position=20.0)

        killed, remaining = tower.attack(self.model, enemy)

        self.assertFalse(killed)
        self.assertEqual(remaining, 100)
        self.assertEqual(enemy.hp, 100)

    def test_hp_never_goes_below_zero(self):
        enemy = self._active_enemy(hp=50)
        tower = self.model.create_tower(damage=9999, range=10.0, position=0.0)

        killed, remaining = tower.attack(self.model, enemy)

        self.assertTrue(killed)
        self.assertEqual(remaining, 0)
        self.assertEqual(enemy.hp, 0)

    def test_defeated_enemy_leaves_active_list(self):
        enemy = self._active_enemy(hp=50)
        tower = self.model.create_tower(damage=9999, range=10.0, position=0.0)

        tower.attack(self.model, enemy)

        self.assertEqual(self.model.active_count, 0)
        self.assertNotIn(enemy, self.model.active_enemies)
        self.assertTrue(enemy.is_defeated)

    def test_tower_does_not_attack_removed_enemy(self):
        enemy = self._active_enemy(hp=50)
        tower = self.model.create_tower(damage=9999, range=10.0, position=0.0)
        tower.attack(self.model, enemy)
        history_before = self.model.history_count

        killed, remaining = tower.attack(self.model, enemy)

        self.assertFalse(killed)
        self.assertEqual(remaining, 0)
        self.assertEqual(enemy.hp, 0)
        self.assertEqual(self.model.history_count, history_before)

    def test_tower_does_not_attack_pending_enemy(self):
        enemy = self.model.create_enemy(hp=100)
        self.model.add_to_wave(enemy)
        tower = self.model.create_tower(damage=30, range=10.0, position=0.0)

        killed, remaining = tower.attack(self.model, enemy)

        self.assertFalse(killed)
        self.assertEqual(remaining, 100)
        self.assertEqual(enemy.hp, 100)
        self.assertEqual(self.model.pending_count, 1)

    def test_remove_escaped_enemy(self):
        enemy = self._active_enemy(hp=100)
        enemy.progress = self.model.path_length

        removed = self.model.remove_escaped()

        self.assertEqual(removed, [enemy])
        self.assertEqual(self.model.active_count, 0)
        self.assertNotIn(enemy, self.model.active_enemies)

    def test_remove_escaped_keeps_enemies_on_path(self):
        enemy = self._active_enemy(hp=100)
        enemy.progress = 1.0

        removed = self.model.remove_escaped()

        self.assertEqual(removed, [])
        self.assertEqual(self.model.active_count, 1)


if __name__ == "__main__":
    unittest.main()
