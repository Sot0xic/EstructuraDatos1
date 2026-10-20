"""
Pruebas de las animaciones PNG de las torres (Semana 4).

Comprueba:

    - el catalogo TOWER_VARIANTS con las 12 variantes disponibles
    - que solo las tres primeras variantes estan cables a los tipos
      del juego (teclas 1/2/3); las otras nueve quedan como recursos
    - la carga perezosa y pre-escalada de reposo y frames de ataque
    - el recorte de la animacion en el frame de despegue, para no
      duplicar el proyectil visual del juego
    - que la ventana usa los frames PNG al dibujar torres y vuelve
      al reposo al terminar la animacion de disparo

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
from View.tower_animations import (
    KIND_VARIANTS,
    LAUNCH_END,
    TOWER_VARIANTS,
    TowerAnimations,
)
from View.tower_assets import TOWER_WIDTH_PX

MAP_PATH = os.path.join("assets", "mapas", "mapa_principal.tmx")


class TestTowerVariantCatalog(unittest.TestCase):
    """Pruebas del catalogo de las 12 variantes."""

    def test_catalog_has_twelve_variants(self):
        self.assertEqual(len(TOWER_VARIANTS), 12)
        esperadas = {f"torre_{index:02d}" for index in range(1, 13)}
        self.assertEqual(set(TOWER_VARIANTS), esperadas)

    def test_every_variant_declares_fifty_frames(self):
        for variant, spec in TOWER_VARIANTS.items():
            self.assertEqual(spec["frames"], 50, variant)
            self.assertGreater(spec["size"][0], 0, variant)
            self.assertGreater(spec["size"][1], 0, variant)

    def test_launch_end_cuts_before_the_projectile_flies_away(self):
        for variant, spec in TOWER_VARIANTS.items():
            self.assertGreaterEqual(spec["launch_end"], 2, variant)
            self.assertLess(spec["launch_end"], spec["frames"], variant)

    def test_launch_end_is_the_calibrated_constant(self):
        for spec in TOWER_VARIANTS.values():
            self.assertEqual(spec["launch_end"], LAUNCH_END)

    def test_all_twelve_variants_are_wired_to_kinds(self):
        esperado = {"basica": "torre_01", "fuego": "torre_02", "pesada": "torre_03"}
        esperado.update({f"torre_{i:02d}": f"torre_{i:02d}" for i in range(4, 13)})
        self.assertEqual(KIND_VARIANTS, esperado)
        self.assertEqual(set(KIND_VARIANTS.values()), set(TOWER_VARIANTS))


class TestTowerAnimationsLoading(unittest.TestCase):
    """Pruebas de la carga perezosa y el escalado de los frames."""

    def setUp(self):
        self.animations = TowerAnimations(scale=1.0)

    def test_has_is_true_only_for_wired_kinds(self):
        for kind in KIND_VARIANTS:
            self.assertTrue(self.animations.has(kind), kind)
        self.assertTrue(self.animations.has("torre_12"))
        self.assertFalse(self.animations.has("inventada"))

    def test_idle_and_attack_frames_load_for_the_twelve_kinds(self):
        for kind in KIND_VARIANTS:
            idle = self.animations.idle(kind)
            self.assertGreater(idle.get_width(), 0, kind)
            self.assertGreater(idle.get_height(), 0, kind)
            self.assertGreater(self.animations.frame_count(kind), 0, kind)
            self.assertNotEqual(
                pygame.image.tostring(idle, "RGBA"),
                pygame.image.tostring(self.animations.frame(kind, 1.0), "RGBA"),
                f"{kind}: el frame final del ataque es igual al reposo",
            )

    def test_frames_are_scaled_to_the_tower_width(self):
        for scale in (1.0, 0.5):
            animations = TowerAnimations(scale=scale)
            esperado = max(1, int(round(TOWER_WIDTH_PX * scale)))
            for kind in KIND_VARIANTS:
                self.assertEqual(
                    animations.idle(kind).get_width(), esperado, f"{kind} scale={scale}"
                )

    def test_anchor_points_to_the_base_of_the_frame(self):
        for kind in KIND_VARIANTS:
            idle = self.animations.idle(kind)
            anchor_x, anchor_y = self.animations.anchor(kind)
            self.assertTrue(0 <= anchor_x < idle.get_width(), kind)
            self.assertTrue(0 <= anchor_y < idle.get_height(), kind)
            self.assertEqual(anchor_y, idle.get_height() - 1, kind)

    def test_progress_zero_shows_idle_and_grows_through_the_attack(self):
        kind = "basica"
        idle = self.animations.idle(kind)
        self.assertEqual(self.animations.frame(kind, 0.0), idle)
        self.assertEqual(self.animations.frame(kind, -1.0), idle)
        self.assertNotEqual(self.animations.frame(kind, 0.5), idle)
        # progreso 1.0 queda en el ultimo frame de ataque (el despegue)
        self.assertEqual(
            self.animations.frame(kind, 1.0),
            self.animations.frame(kind, 9.9),
        )

    def test_duration_matches_the_number_of_attack_frames(self):
        for kind in KIND_VARIANTS:
            frames = self.animations.frame_count(kind)
            spec = TOWER_VARIANTS[KIND_VARIANTS[kind]]
            self.assertAlmostEqual(
                self.animations.duration(kind), frames * spec["frame_time"]
            )

    def test_unknown_kind_raises_key_error(self):
        with self.assertRaises(KeyError):
            self.animations.idle("inventada")
        with self.assertRaises(KeyError):
            self.animations.frame_count("inventada")

    def test_unused_variants_are_loaded_lazily(self):
        self.animations.idle("basica")

        self.assertEqual(set(self.animations._cache), {"torre_01"})


class TestWindowUsesAnimations(unittest.TestCase):
    """Pruebas de la ventana con las torres animadas."""

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
        self.model.shots.clear()
        self.model._next_enemy_id = 1
        self.model._next_tower_id = 1
        self.controller._spawn_timer = 0.0
        self.window._pending_click = None
        self.window.projectiles.clear()
        self.window.impacts.clear()
        self.window._dt = 0.0
        self.window._anim_time = 0.0
        self.window._fire_timers.clear()

    def _place_kind(self, kind, spot):
        map_x, map_y = spot
        progress = self.tiled_map.closest_progress_on_path(map_x, map_y)
        return self.model.create_tower(
            kind=kind,
            range=GameWindow.TOWER_RANGE_PX,
            position=progress,
            map_x=map_x,
            map_y=map_y,
            footprint=GameWindow.TOWER_FOOTPRINT,
        )

    def _valid_spot_near_path(self):
        radius = GameWindow.TOWER_FOOTPRINT
        offsets = [
            (0, 0), (radius * 3, 0), (-radius * 3, 0),
            (0, radius * 3), (0, -radius * 3),
        ]
        for px, py in self.tiled_map.path_points:
            for dx, dy in offsets:
                x, y = px + dx, py + dy
                valid, _ = self.tiled_map.can_place_tower(x, y, radius)
                if valid:
                    return x, y
        self.fail("No hay una posicion valida cerca del camino")

    def _spawn_enemy_on(self, tower, hp=100000):
        enemy = self.model.create_enemy(name="Goblin", hp=hp, speed=0.0)
        self.model.add_to_wave(enemy)
        self.model.spawn_next()
        enemy.progress = tower.position
        return enemy

    def test_window_exposes_animations_for_the_selected_kinds(self):
        for kind in GameWindow.TOWER_KIND_ORDER:
            self.assertTrue(self.window.animations.has(kind), kind)

    def test_idle_frame_is_drawn_on_the_tower_position(self):
        tower = self._place_kind("basica", self._valid_spot_near_path())
        self.window.draw()

        idle = self.window.animations.idle(tower.kind)
        anchor_x, anchor_y = self.window.animations.anchor(tower.kind)
        centro_x, centro_y = self.window.map_to_screen(tower.map_x, tower.map_y)

        # Se busca un pixel opaco del frame de reposo cerca del ancla
        # y se comprueba que la ventana lo pinto en esa posicion.
        offset = None
        for dy in range(-24, 24):
            for dx in range(-24, 24):
                sx, sy = anchor_x + dx, anchor_y + dy
                if not (0 <= sx < idle.get_width() and 0 <= sy < idle.get_height()):
                    continue
                # Los frames pre-escalados con smoothscale quedan con
                # alfa casi opaco (253); se busca un pixel solido.
                if idle.get_at((sx, sy)).a >= 200:
                    offset = (dx, dy)
                    break
            if offset is not None:
                break
        self.assertIsNotNone(offset, "El frame de reposo no tiene base opaca")
        esperado = idle.get_at((anchor_x + offset[0], anchor_y + offset[1]))
        pintado = self.window.screen.get_at(
            (int(centro_x) + offset[0], int(centro_y) + offset[1])
        )
        # El frame casi opaco (alfa 253) se funde un poco con el mapa
        # al dibujarse: se admite un desvio minimo por canal.
        for canal in range(4):
            self.assertLessEqual(
                abs(pintado[canal] - esperado[canal]),
                4,
                f"canal {canal}: pintado={tuple(pintado)} esperado={tuple(esperado)}",
            )

    def test_shot_plays_the_attack_animation_and_returns_to_idle(self):
        tower = self._place_kind("basica", self._valid_spot_near_path())
        self._spawn_enemy_on(tower)

        self.controller.update(0.05)
        self.window._dt = 0.05
        self.window.draw()

        self.assertGreater(self.window._tower_fire_progress(tower), 0.0)
        self.assertLessEqual(self.window._tower_fire_progress(tower), 1.0)
        self.assertNotEqual(
            self.window.animations.frame(
                tower.kind, self.window._tower_fire_progress(tower)
            ),
            self.window.animations.idle(tower.kind),
        )

        # Recorre la animacion completa sin updates: vuelve al reposo.
        self.window._dt = 0.05
        for _ in range(40):
            self.window.draw()
            if self.window._tower_fire_progress(tower) <= 0.0:
                break
        self.assertLessEqual(self.window._tower_fire_progress(tower), 0.0)
        self.window.draw()
        self.assertEqual(
            self.window.animations.frame(tower.kind, 0.0),
            self.window.animations.idle(tower.kind),
        )

    def test_animation_does_not_duplicate_damage(self):
        tower = self._place_kind("fuego", self._valid_spot_near_path())
        enemy = self._spawn_enemy_on(tower)

        self.controller.update(0.05)
        tras_disparo = enemy.hp
        self.assertEqual(tras_disparo, 100000 - tower.damage)

        self.window._dt = 0.05
        for _ in range(120):
            self.window.draw()
            if not self.window.projectiles and not self.window.impacts:
                break

        self.assertEqual(enemy.hp, tras_disparo)
        self.assertEqual(self.window.projectiles, [])
        self.assertEqual(self.window.impacts, [])


if __name__ == "__main__":
    unittest.main()
