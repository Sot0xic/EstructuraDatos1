"""
Pruebas de torres colocadas manualmente en el mapa (Semana 3).

Comprueba que una torre colocada con el raton sobre el mapa de Tiled:

    - se registra en el modelo y participa en update()
    - almacena su alcance en pixeles del mapa (misma unidad que
      Enemy.progress), teniendo en cuenta el escalado de la ventana
    - respeta el cooldown (attack_interval) entre ataques
    - aplica el danio a la vida del enemigo
    - refleja el danio en la barra de vida
    - elimina al enemigo cuando su vida llega a cero

Ejecutar desde la raiz del proyecto:

    py -m pytest -v
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import unittest

import pygame

from Controller.game_controller import GameController
from Model.game_model import GameModel
from View.game_window import GameWindow
from View.tiled_map import TiledMap

MAP_PATH = os.path.join("assets", "mapas", "mapa_principal.tmx")


class TestManualTower(unittest.TestCase):
    """Pruebas de la torre colocada a traves de la ventana."""

    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1))
        cls.tiled_map = TiledMap(MAP_PATH)
        cls.model = GameModel(path_length=cls.tiled_map.path_length())
        cls.controller = GameController(
            model=cls.model, view=None, spawn_interval=9999.0
        )
        cls.window = GameWindow(cls.model, cls.tiled_map)

    def setUp(self):
        self.model.pending_enemies.clear()
        self.model.active_enemies.clear()
        self.model.action_history.clear()
        self.model.towers.clear()
        self.model._next_enemy_id = 1
        self.model._next_tower_id = 1
        self.controller._spawn_timer = 0.0
        self.window._pending_click = None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _valid_spot_near_path(self):
        """Busca una posicion valida cerca del camino. O(p).

        Valida tambien el recorrido pantalla -> mapa -> pantalla para
        que el click simulado coloque la torre en la misma posicion.
        """
        radius = GameWindow.TOWER_FOOTPRINT
        offsets = [
            (0, 0), (radius * 3, 0), (-radius * 3, 0),
            (0, radius * 3), (0, -radius * 3),
            (radius * 3, radius * 3), (-radius * 3, radius * 3),
            (radius * 3, -radius * 3), (-radius * 3, -radius * 3),
        ]
        for px, py in self.tiled_map.path_points:
            for dx, dy in offsets:
                x, y = px + dx, py + dy
                rx, ry = self.window.screen_to_map(
                    *self.window.map_to_screen(x, y)
                )
                valid, _ = self.tiled_map.can_place_tower(rx, ry, radius)
                if valid:
                    return x, y
        self.fail("No hay una posicion valida cerca del camino")

    def _place_tower_near_path(self, via_draw=False):
        """Coloca una torre con el mismo flujo que un click del jugador."""
        map_x, map_y = self._valid_spot_near_path()
        screen_pos = self.window.map_to_screen(map_x, map_y)

        if via_draw:
            self.window._pending_click = screen_pos
            self.window.draw()
        else:
            self.window._try_place_tower(*screen_pos)

        self.assertEqual(len(self.model.towers), 1, "La torre no se registro")
        return self.model.towers[0]

    def _spawn_enemy(self, hp=100, speed=1.0, progress=None):
        enemy = self.model.create_enemy(name="Goblin", hp=hp, speed=speed)
        self.model.add_to_wave(enemy)
        self.model.spawn_next()
        if progress is not None:
            enemy.progress = progress
        return enemy

    # ------------------------------------------------------------------
    # 1. Registro en el modelo y participacion en el update
    # ------------------------------------------------------------------
    def test_placed_tower_is_registered_in_model(self):
        tower = self._place_tower_near_path(via_draw=True)

        self.assertIn(tower, self.model.towers)
        self.assertIsNotNone(tower.map_x)
        self.assertIsNotNone(tower.map_y)
        self.assertEqual(tower.footprint, GameWindow.TOWER_FOOTPRINT)
        self.assertAlmostEqual(
            tower.position,
            self.tiled_map.closest_progress_on_path(tower.map_x, tower.map_y),
        )

    def test_full_draw_with_tower_and_enemy(self):
        tower = self._place_tower_near_path(via_draw=True)
        self._spawn_enemy(hp=100, progress=tower.position)

        self.controller.update(0.05)
        self.window.draw()

        centro = self.window.map_to_screen(tower.map_x, tower.map_y)
        self.assertEqual(
            self.window.screen.get_at((int(centro[0]), int(centro[1])))[:3],
            GameWindow.TOWER_COLOR,
        )
        self.assertEqual(
            self.window.screen.get_size(),
            (GameWindow.WIDTH, GameWindow.HEIGHT),
        )

    def test_placed_tower_participates_in_update(self):
        tower = self._place_tower_near_path()
        enemy = self._spawn_enemy(hp=100, progress=tower.position)

        self.controller.update(0.05)

        self.assertGreater(tower.damage, 0)
        self.assertEqual(enemy.hp, 100 - tower.damage)
        self.assertIn(enemy, self.model.active_enemies)

    # ------------------------------------------------------------------
    # 2. Deteccion con el mismo sistema de coordenadas (pixeles del mapa)
    # ------------------------------------------------------------------
    def test_placed_tower_range_is_in_map_pixels(self):
        tower = self._place_tower_near_path()

        self.assertEqual(tower.range, GameWindow.TOWER_RANGE_PX)

    def test_placed_tower_detects_enemy_inside_map_pixel_range(self):
        tower = self._place_tower_near_path()
        al_limite = self._spawn_enemy(
            progress=tower.position + GameWindow.TOWER_RANGE_PX - 1
        )
        fuera = self._spawn_enemy(
            progress=tower.position + GameWindow.TOWER_RANGE_PX + 1
        )

        self.assertTrue(tower.is_in_range(al_limite))
        self.assertFalse(tower.is_in_range(fuera))

    def test_placed_tower_ignores_enemy_out_of_range(self):
        tower = self._place_tower_near_path()
        enemy = self._spawn_enemy(
            hp=100, progress=tower.position + GameWindow.TOWER_RANGE_PX + 100
        )

        self.controller.update(0.05)

        self.assertEqual(enemy.hp, 100)
        self.assertEqual(tower.cooldown, 0.0)

    # ------------------------------------------------------------------
    # 3. Cooldown entre ataques
    # ------------------------------------------------------------------
    def test_placed_tower_respects_attack_cooldown(self):
        tower = self._place_tower_near_path()
        enemy = self._spawn_enemy(hp=1000, progress=tower.position)

        self.controller.update(0.05)
        self.assertEqual(enemy.hp, 1000 - tower.damage)

        self.controller.update(0.05)
        self.assertEqual(enemy.hp, 1000 - tower.damage,
                         "Ataco antes de terminar el cooldown")

        self.controller.update(tower.attack_interval)
        self.assertEqual(enemy.hp, 1000 - 2 * tower.damage,
                         "No ataco al terminar el cooldown")

    def test_tower_starts_ready_to_attack(self):
        tower = self._place_tower_near_path()

        self.assertTrue(tower.is_ready)
        self.assertEqual(tower.cooldown, 0.0)
        self.assertEqual(tower.attack_interval, GameWindow.TOWER_ATTACK_INTERVAL)
        self.assertGreater(tower.attack_interval, 0.0)

    # ------------------------------------------------------------------
    # 4 y 6. Danio aplicado y eliminacion del enemigo
    # ------------------------------------------------------------------
    def test_placed_tower_kills_and_removes_enemy(self):
        tower = self._place_tower_near_path()
        enemy = self._spawn_enemy(hp=tower.damage, progress=tower.position)
        historia = self.model.history_count

        self.controller.update(0.05)

        self.assertEqual(enemy.hp, 0)
        self.assertTrue(enemy.is_defeated)
        self.assertEqual(self.model.active_count, 0)
        self.assertNotIn(enemy, self.model.active_enemies)
        self.assertIsNone(self.model.active_enemies.head)
        self.assertIsNone(self.model.active_enemies.tail)
        ultima = self.model.peek_last_action()
        self.assertEqual(ultima[0], "kill")
        self.assertIs(ultima[1], enemy)
        self.assertEqual(self.model.history_count, historia + 1)

    def test_placed_tower_targets_lowest_hp_enemy(self):
        tower = self._place_tower_near_path()
        hp_baja = tower.damage + 25
        hp_alta = tower.damage + 100
        con_mas_vida = self._spawn_enemy(
            hp=hp_alta, progress=tower.position - 100
        )
        con_menos_vida = self._spawn_enemy(
            hp=hp_baja, progress=tower.position + 100
        )

        self.controller.update(0.05)

        self.assertEqual(con_menos_vida.hp, hp_baja - tower.damage)
        self.assertEqual(con_mas_vida.hp, hp_alta)
        self.assertEqual(self.model.active_count, 2)

    def test_placed_tower_kills_enemy_crossing_its_range(self):
        tower = self._place_tower_near_path()
        enemy = self._spawn_enemy(
            hp=tower.damage * 2, speed=100.0, progress=tower.position - 400
        )

        for _ in range(400):
            self.controller.update(0.05)
            if not enemy.is_alive:
                break

        self.assertFalse(enemy.is_alive)
        self.assertEqual(enemy.hp, 0)
        self.assertEqual(self.model.active_count, 0)
        self.assertNotIn(enemy, self.model.active_enemies)

    # ------------------------------------------------------------------
    # 5. Barra de vida refleja el dano
    # ------------------------------------------------------------------
    def test_hp_bar_reflects_damage(self):
        tower = self._place_tower_near_path()
        enemy = self._spawn_enemy(hp=1000, progress=tower.position)
        bar_width = 22

        x, y = self.window._point_at(enemy.progress)
        x, y = int(x), int(y)
        izq = x - bar_width // 2
        borde_derecho = (izq + bar_width - 1, y - 19)

        self.window.screen.fill(GameWindow.BACKGROUND)
        self.window._draw_enemies()
        self.assertEqual(
            self.window.screen.get_at(borde_derecho)[:3], GameWindow.HP_FILL
        )

        self.controller.update(0.05)

        self.assertEqual(enemy.hp, 1000 - tower.damage)
        relleno = int(bar_width * enemy.hp / enemy.max_hp)
        self.assertLess(relleno, bar_width)

        self.window.screen.fill(GameWindow.BACKGROUND)
        self.window._draw_enemies()
        self.assertEqual(
            self.window.screen.get_at((izq + relleno - 1, y - 19))[:3],
            GameWindow.HP_FILL,
        )
        self.assertEqual(
            self.window.screen.get_at((izq + relleno, y - 19))[:3],
            GameWindow.HP_BG,
        )

    # ------------------------------------------------------------------
    # Circulo dibujado coherente con el alcance y el escalado
    # ------------------------------------------------------------------
    def test_drawn_range_circle_matches_range_and_scale(self):
        tower = self._place_tower_near_path()

        radio = self.window._range_radius_px(tower)

        self.assertEqual(radio, int(tower.range * self.window.scale))
        self.assertGreater(radio, 0)


if __name__ == "__main__":
    unittest.main()
