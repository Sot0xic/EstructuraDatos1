"""
Pruebas de integracion del modelo con las estructuras (Dia 5 - Semana 1).

Comprueba el flujo conceptual:

    QUEUE (espera) -> dequeue() -> LISTA DOBLE (activos)
                                 -> torre elimina enemigo -> remove del nodo

    STACK -> historial de acciones (LIFO)

Ejecutar desde la raiz del proyecto:

    python -m unittest discover -s tests -v
"""

import unittest

from Model.game_model import Enemy, GameModel


class TestGameModel(unittest.TestCase):
    """Pruebas del modelo base del Tower Defense."""

    def setUp(self):
        self.model = GameModel()

    def _add_wave(self, count=3):
        enemies = []
        for _ in range(count):
            enemy = self.model.create_enemy()
            self.model.add_to_wave(enemy)
            enemies.append(enemy)
        return enemies

    def test_wave_is_queued_fifo(self):
        enemies = self._add_wave(3)
        self.assertEqual(self.model.pending_count, 3)
        self.assertEqual(self.model.pending_enemies.peek(), enemies[0])

    def test_spawn_moves_enemy_from_queue_to_list(self):
        enemies = self._add_wave(3)
        spawned = self.model.spawn_next()

        self.assertIs(spawned, enemies[0])
        self.assertEqual(self.model.pending_count, 2)
        self.assertEqual(self.model.active_count, 1)
        self.assertIn(enemies[0], self.model.active_enemies)

    def test_spawn_all(self):
        self._add_wave(4)
        spawned = self.model.spawn_all()
        self.assertEqual(len(spawned), 4)
        self.assertEqual(self.model.pending_count, 0)
        self.assertEqual(self.model.active_count, 4)

    def test_spawn_on_empty_queue(self):
        self.assertIsNone(self.model.spawn_next())

    def test_tower_kill_removes_node(self):
        enemies = self._add_wave(3)
        self.model.spawn_all()

        middle = enemies[1]
        killed, remaining = self.model.tower_attack(middle, damage=9999)

        self.assertTrue(killed)
        self.assertEqual(remaining, 0)
        self.assertEqual(self.model.active_count, 2)
        self.assertNotIn(middle, self.model.active_enemies)
        self.assertIn(enemies[0], self.model.active_enemies)
        self.assertIn(enemies[2], self.model.active_enemies)

        remaining_list = self.model.active_enemies.to_list()
        self.assertEqual(len(remaining_list), 2)
        self.assertIsNone(self.model.active_enemies.head.prev)
        self.assertIsNone(self.model.active_enemies.tail.next)

    def test_tower_attack_does_not_kill(self):
        enemy = self.model.create_enemy(hp=100)
        self.model.add_to_wave(enemy)
        self.model.spawn_next()

        killed, remaining = self.model.tower_attack(enemy, damage=30)

        self.assertFalse(killed)
        self.assertEqual(remaining, 70)
        self.assertEqual(self.model.active_count, 1)
        self.assertIn(enemy, self.model.active_enemies)

    def test_tower_attack_inactive_enemy(self):
        enemy = self.model.create_enemy()
        killed, remaining = self.model.tower_attack(enemy, damage=10)
        self.assertFalse(killed)
        self.assertEqual(remaining, enemy.hp)

    def test_remove_enemy(self):
        enemies = self._add_wave(2)
        self.model.spawn_all()
        self.assertTrue(self.model.remove_enemy(enemies[0]))
        self.assertEqual(self.model.active_count, 1)
        self.assertFalse(self.model.remove_enemy(enemies[0]))

    def test_history_is_lifo(self):
        enemy = self.model.create_enemy()
        self.model.add_to_wave(enemy)   # accion 1: enqueue
        self.model.spawn_next()         # accion 2: spawn

        self.assertEqual(self.model.history_count, 2)
        last = self.model.undo()        # LIFO: recupera la ultima
        self.assertEqual(last[0], "spawn")
        self.assertEqual(self.model.history_count, 1)

        previous = self.model.undo()
        self.assertEqual(previous[0], "enqueue")
        self.assertTrue(self.model.action_history.is_empty())
        self.assertIsNone(self.model.undo())

    def test_peek_last_action(self):
        self._add_wave(1)
        action = self.model.peek_last_action()
        self.assertEqual(action[0], "enqueue")
        self.assertEqual(self.model.history_count, 1)

    def test_enemy_damage(self):
        enemy = Enemy(1, hp=50)
        self.assertTrue(enemy.is_alive)
        enemy.take_damage(20)
        self.assertEqual(enemy.hp, 30)
        enemy.take_damage(100)
        self.assertEqual(enemy.hp, 0)
        self.assertFalse(enemy.is_alive)

    def test_get_state(self):
        self._add_wave(2)
        self.model.spawn_next()
        state = self.model.get_state()
        self.assertEqual(len(state["pending"]), 1)
        self.assertEqual(len(state["active"]), 1)
        self.assertEqual(len(state["history"]), 3)

    def test_advance_enemies_updates_progress(self):
        model = GameModel()
        enemy = model.create_enemy(
            name="Goblin",
            hp=60,
            speed=2.0,
        )

        model.add_to_wave(enemy)
        model.spawn_next()
        model.advance_enemies(3)

        self.assertEqual(enemy.progress, 6.0)

    def test_advance_enemies_respects_speed(self):
        model = GameModel()

        slow_enemy = model.create_enemy(
            name="Goblin",
            speed=1.0,
        )
        fast_enemy = model.create_enemy(
            name="Orco",
            speed=3.0,
        )

        model.add_to_wave(slow_enemy)
        model.add_to_wave(fast_enemy)
        model.spawn_all()
        model.advance_enemies(2)

        self.assertEqual(slow_enemy.progress, 2.0)
        self.assertEqual(fast_enemy.progress, 6.0)

    def test_pending_enemies_do_not_advance(self):
        model = GameModel()
        enemy = model.create_enemy(
            name="Dragon",
            speed=2.0,
        )

        model.add_to_wave(enemy)
        model.advance_enemies(5)

        self.assertEqual(enemy.progress, 0.0)
        self.assertEqual(model.pending_count, 1)
        self.assertEqual(model.active_count, 0)


class TestEnemy(unittest.TestCase):
    """Pruebas de la entidad Enemy (Dia 1 - Semana 2)."""

    def test_starts_with_max_health(self):
        enemy = Enemy(1, name="Goblin", hp=60)
        self.assertEqual(enemy.hp, enemy.max_hp)
        self.assertEqual(enemy.hp, 60)
        self.assertTrue(enemy.is_alive)
        self.assertFalse(enemy.is_defeated)

    def test_damage_reduces_health_and_never_goes_below_zero(self):
        enemy = Enemy(2, hp=50)
        self.assertEqual(enemy.take_damage(20), 30)
        self.assertEqual(enemy.take_damage(1000), 0)
        self.assertEqual(enemy.hp, 0)
        self.assertFalse(enemy.is_alive)
        self.assertTrue(enemy.is_defeated)

    def test_health_never_exceeds_max(self):
        enemy = Enemy(3, hp=40)
        enemy.take_damage(-100)
        self.assertEqual(enemy.hp, enemy.max_hp)
        self.assertEqual(enemy.hp, 40)

    def test_negative_initial_health_is_clamped(self):
        enemy = Enemy(4, hp=-30)
        self.assertEqual(enemy.max_hp, 0)
        self.assertEqual(enemy.hp, 0)
        self.assertTrue(enemy.is_defeated)

    def test_progress_represents_position(self):
        enemy = Enemy(5, speed=2.0, progress=10.0)
        enemy.advance(5)
        self.assertEqual(enemy.progress, 20.0)
        self.assertEqual(enemy.speed, 2.0)
        self.assertIn("progress", repr(enemy))


if __name__ == "__main__":
    unittest.main()
