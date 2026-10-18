"""
Pruebas de los tres tipos de torre, sus sprites y proyectiles
(Semana 3 - pack stone-tower-game-assets).

Comprueba:

    - el registro TOWER_KINDS (basica, fuego, pesada) y sus roles
    - la creacion de torres tomando nombre/danio/cadencia del tipo
    - la seleccion de tipo con las teclas 1/2/3 y la colocacion
    - que los sprites de cada tipo existen y se componen
    - que el danio se aplica una sola vez por disparo: el proyectil
      y el impacto son puramente visuales y no lo duplican
    - que los proyectiles vuelan hasta el enemigo y generan impactos
      que se animan por frames y terminan desapareciendo

Ejecutar desde la raiz del proyecto:

    py -m pytest -v
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import unittest

import pygame

from Controller.game_controller import GameController
from Model.game_model import GameModel, TOWER_KINDS
from View.game_window import GameWindow
from View.tiled_map import TiledMap
from View.tower_assets import (
    LEGACY_FIRE_PROJECTILE,
    TOWER_ASSETS,
    VARIANT_PROJECTILES,
    TowerAssets,
    asset_path,
)

MAP_PATH = os.path.join("assets", "mapas", "mapa_principal.tmx")


class TestTowerKinds(unittest.TestCase):
    """Pruebas del registro de tipos y de creacion de torres."""

    def test_registry_has_the_three_kinds(self):
        self.assertEqual(set(TOWER_KINDS), {"basica", "fuego", "pesada"})

    def test_kind_stats_match_their_roles(self):
        basica = TOWER_KINDS["basica"]
        fuego = TOWER_KINDS["fuego"]
        pesada = TOWER_KINDS["pesada"]

        for spec in (basica, fuego, pesada):
            self.assertGreater(spec["damage"], 0)
            self.assertGreater(spec["attack_interval"], 0.0)
            self.assertTrue(spec["name"])

        # fuego ataca mas rapido; pesada ataca mas lento y mas fuerte
        self.assertLess(fuego["attack_interval"], basica["attack_interval"])
        self.assertGreater(pesada["attack_interval"], basica["attack_interval"])
        self.assertGreater(pesada["damage"], basica["damage"])
        self.assertGreater(basica["damage"], fuego["damage"])

    def test_create_tower_uses_kind_stats(self):
        model = GameModel()

        for kind, spec in TOWER_KINDS.items():
            tower = model.create_tower(kind=kind, range=5.0, position=0.0)

            self.assertEqual(tower.kind, kind)
            self.assertEqual(tower.name, spec["name"])
            self.assertEqual(tower.damage, spec["damage"])
            self.assertEqual(tower.attack_interval, spec["attack_interval"])
            self.assertGreater(tower.tower_id, 0)
            self.assertIn(tower, model.towers)

    def test_default_kind_is_basica(self):
        model = GameModel()

        tower = model.create_tower()

        self.assertEqual(tower.kind, "basica")
        self.assertEqual(tower.damage, TOWER_KINDS["basica"]["damage"])

    def test_create_tower_allows_explicit_overrides(self):
        model = GameModel()

        tower = model.create_tower(
            kind="fuego", damage=42, name="Personalizada", attack_interval=2.5
        )

        self.assertEqual(tower.kind, "fuego")
        self.assertEqual(tower.damage, 42)
        self.assertEqual(tower.name, "Personalizada")
        self.assertEqual(tower.attack_interval, 2.5)

    def test_unknown_kind_falls_back_to_basica_stats(self):
        model = GameModel()

        tower = model.create_tower(kind="inventada", range=5.0, position=0.0)

        self.assertEqual(tower.damage, TOWER_KINDS["basica"]["damage"])
        self.assertEqual(
            tower.attack_interval, TOWER_KINDS["basica"]["attack_interval"]
        )


class TestTowerAssets(unittest.TestCase):
    """Pruebas de los sprites del pack stone-tower-game-assets."""

    def test_asset_files_exist(self):
        for kind, spec in TOWER_ASSETS.items():
            filenames = [spec["body"], spec["shadow"], spec["projectile"]]
            filenames.extend(spec["impact"])
            if spec.get("body_firing"):
                filenames.append(spec["body_firing"])
            if spec.get("hover"):
                filenames.append(spec["hover"])
            self.assertTrue(spec["impact"], f"{kind} sin frames de impacto")
            for filename in filenames:
                path = asset_path(filename)
                self.assertTrue(
                    os.path.isfile(path), f"Falta el sprite {path}"
                )

    def test_firing_variant_differs_from_idle_when_available(self):
        assets = TowerAssets(scale=1.0)

        for kind, spec in TOWER_ASSETS.items():
            idle = assets.tower(kind, firing=False)
            firing = assets.tower(kind, firing=True)
            self.assertEqual(idle.get_size(), firing.get_size())
            if spec.get("body_firing"):
                self.assertNotEqual(
                    pygame.image.tostring(idle, "RGBA"),
                    pygame.image.tostring(firing, "RGBA"),
                    f"{kind}: body_firing igual al cuerpo en reposo",
                )
                opacos_firing = pygame.mask.from_surface(firing).count()
                self.assertGreater(opacos_firing, 100, f"{kind}: firing vacio")

    def test_test_towers_fire_rocks_not_fire(self):
        fuego = TOWER_ASSETS["fuego"]
        basica = TOWER_ASSETS["basica"]

        # Las tres torres de prueba son catapultas: lanzan rocas.
        self.assertEqual(fuego["projectile"], basica["projectile"])
        self.assertEqual(fuego["impact"], basica["impact"])
        self.assertEqual(fuego["hover"], basica["hover"])

        # El proyectil de fuego original queda reutilizable.
        self.assertEqual(LEGACY_FIRE_PROJECTILE["projectile"], "35.png")
        self.assertTrue(LEGACY_FIRE_PROJECTILE["impact"])

    def test_variant_projectile_table_covers_all_twelve_variants(self):
        esperado = {
            "torre_01": ("40.png", None),
            "torre_02": ("40.png", None),
            "torre_03": ("40.png", None),
            "torre_04": ("35.png", "fall"),
            "torre_05": ("35.png", "fall"),
            "torre_06": ("35.png", "fall"),
            "torre_07": ("29.png", None),
            "torre_08": ("29.png", None),
            "torre_09": ("29.png", None),
            "torre_10": ("50.png", "spin"),
            "torre_11": ("50.png", "spin"),
            "torre_12": ("50.png", "spin"),
        }

        self.assertEqual(set(VARIANT_PROJECTILES), set(esperado))
        for variante, (archivo, rotacion) in esperado.items():
            entrada = VARIANT_PROJECTILES[variante]
            self.assertEqual(entrada["file"], archivo)
            self.assertEqual(entrada["rotate"], rotacion)
            self.assertTrue(
                os.path.isfile(asset_path(archivo)),
                f"Falta el sprite {archivo} de {variante}",
            )

    def test_wired_kinds_use_their_variant_projectile(self):
        pares = (
            ("basica", "torre_01"),
            ("fuego", "torre_02"),
            ("pesada", "torre_03"),
        )

        for kind, variante in pares:
            spec = TOWER_ASSETS[kind]
            entrada = VARIANT_PROJECTILES[variante]
            self.assertEqual(spec["projectile"], entrada["file"])
            self.assertEqual(spec["hover"], entrada["file"])
            self.assertEqual(spec["rotate"], entrada["rotate"])

    def test_hover_sprite_loaded(self):
        assets = TowerAssets(scale=1.0)

        for kind, spec in TOWER_ASSETS.items():
            hover = assets.hover(kind)
            self.assertGreater(hover.get_width(), 0)
            self.assertGreater(hover.get_height(), 0)
            self.assertGreater(assets.hover_height(kind), 0.0)
            self.assertGreater(spec["hover_height"], 0.0)

    def test_composed_tower_surface_has_content(self):
        assets = TowerAssets(scale=1.0)

        for kind in TOWER_ASSETS:
            sprite = assets.tower(kind)

            self.assertGreater(sprite.get_width(), 0)
            self.assertGreater(sprite.get_height(), 0)
            # la mayoria de la superficie debe ser opaca (cuerpo + sombra)
            opacos = pygame.mask.from_surface(sprite).count()
            self.assertGreater(opacos, 100, f"{kind}: sprite casi vacio")

            # el anclaje (base del cuerpo) cae dentro de la superficie
            anchor_x, anchor_y = assets.tower_anchor(kind)
            self.assertTrue(0 <= anchor_x < sprite.get_width())
            self.assertTrue(0 <= anchor_y < sprite.get_height())

    def test_projectile_and_impact_frames_loaded(self):
        assets = TowerAssets(scale=1.0)

        for kind, spec in TOWER_ASSETS.items():
            projectile = assets.projectile(kind)
            self.assertGreater(projectile.get_width(), 0)
            self.assertGreater(projectile.get_height(), 0)

            frames = assets.impact_frames(kind)
            self.assertEqual(len(frames), len(spec["impact"]))
            for frame in frames:
                self.assertGreater(frame.get_width(), 0)

    def test_scale_reduces_sprite_size(self):
        grande = TowerAssets(scale=1.0).tower("basica")
        pequena = TowerAssets(scale=0.5).tower("basica")

        self.assertLess(pequena.get_width(), grande.get_width())


class TestTowerPlacementAndProjectiles(unittest.TestCase):
    """Pruebas de colocacion, disparos, proyectiles e impactos."""

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
        self.window.selected_kind = "basica"
        self.window._dt = 0.0
        self.window._anim_time = 0.0
        self.window._fire_timers.clear()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _valid_spots(self, count, min_distance=None):
        """Busca posiciones validas cerca del camino. O(p * o)."""
        radius = GameWindow.TOWER_FOOTPRINT
        if min_distance is None:
            min_distance = radius * 2.5
        offsets = [
            (0, 0), (radius * 3, 0), (-radius * 3, 0),
            (0, radius * 3), (0, -radius * 3),
            (radius * 3, radius * 3), (-radius * 3, radius * 3),
            (radius * 3, -radius * 3), (-radius * 3, -radius * 3),
        ]
        spots = []
        for px, py in self.tiled_map.path_points:
            for dx, dy in offsets:
                x, y = px + dx, py + dy
                rx, ry = self.window.screen_to_map(
                    *self.window.map_to_screen(x, y)
                )
                valid, _ = self.tiled_map.can_place_tower(rx, ry, radius)
                if not valid:
                    continue
                separada = all(
                    (x - sx) ** 2 + (y - sy) ** 2 >= min_distance ** 2
                    for sx, sy in spots
                )
                if not separada:
                    continue
                spots.append((x, y))
                if len(spots) >= count:
                    return spots
        self.fail(f"No hay {count} posiciones validas cerca del camino")

    def _place_kind(self, kind, spot):
        """Coloca una torre del tipo indicado en una posicion de mapa."""
        map_x, map_y = spot
        progress = self.tiled_map.closest_progress_on_path(map_x, map_y)
        return self.model.create_tower(
            kind=kind,
            range=GameWindow.TOWER_RANGE_PX,
            position=progress,
            map_x=map_x, map_y=map_y,
            footprint=GameWindow.TOWER_FOOTPRINT,
        )

    def _spawn_enemy(self, hp=100, speed=1.0, progress=None):
        enemy = self.model.create_enemy(name="Goblin", hp=hp, speed=speed)
        self.model.add_to_wave(enemy)
        self.model.spawn_next()
        if progress is not None:
            enemy.progress = progress
        return enemy

    def _run_draws(self, max_frames, dt=0.05):
        """Ejecuta draws con un dt fijo hasta que no quede nada animando."""
        self.window._dt = dt
        for _ in range(max_frames):
            self.window.draw()
            if not self.window.projectiles and not self.window.impacts:
                break

    def _run_until_projectiles_land(self, max_frames=80, dt=0.05):
        """Ejecuta draws hasta que todos los proyectiles lleguen."""
        self.window._dt = dt
        for _ in range(max_frames):
            self.window.draw()
            if not self.window.projectiles:
                break

    # ------------------------------------------------------------------
    # 1. Seleccion y colocacion del tipo de torre
    # ------------------------------------------------------------------
    def test_keys_select_tower_kind(self):
        pares = ((pygame.K_2, "fuego"), (pygame.K_3, "pesada"), (pygame.K_1, "basica"))

        for key, kind in pares:
            pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key))
            self.assertTrue(self.window.process_events())
            self.assertEqual(self.window.selected_kind, kind)

    def test_window_places_selected_kind_with_its_stats(self):
        self.window.selected_kind = "fuego"
        spot = self._valid_spots(1)[0]
        spec = TOWER_KINDS["fuego"]

        self.window._try_place_tower(*self.window.map_to_screen(*spot))

        self.assertEqual(len(self.model.towers), 1)
        tower = self.model.towers[0]
        self.assertEqual(tower.kind, "fuego")
        self.assertEqual(tower.name, spec["name"])
        self.assertEqual(tower.damage, spec["damage"])
        self.assertEqual(tower.attack_interval, spec["attack_interval"])
        self.assertEqual(tower.range, GameWindow.TOWER_RANGE_PX)
        self.assertEqual(tower.footprint, GameWindow.TOWER_FOOTPRINT)

    # ------------------------------------------------------------------
    # 2. Disparo: danio una sola vez + evento visual
    # ------------------------------------------------------------------
    def test_attack_registers_shot_and_applies_damage_once(self):
        tower = self._place_kind("basica", self._valid_spots(1)[0])
        enemy = self._spawn_enemy(hp=1000, progress=tower.position)

        self.controller.update(0.05)

        self.assertEqual(enemy.hp, 1000 - tower.damage)
        self.assertEqual(len(self.model.shots), 1)
        shot = self.model.shots[0]
        self.assertEqual(shot["kind"], "basica")
        self.assertIs(shot["tower"], tower)
        self.assertIs(shot["enemy"], enemy)

    def test_shots_consumed_by_view_create_projectiles(self):
        tower = self._place_kind("basica", self._valid_spots(1)[0])
        self._spawn_enemy(hp=1000, progress=tower.position)
        self.controller.update(0.05)

        self.window.draw()

        self.assertEqual(self.model.shots, [])
        self.assertEqual(len(self.window.projectiles), 1)
        self.assertEqual(self.window.projectiles[0]["kind"], "basica")

    def test_stale_shots_are_dropped_on_next_update(self):
        tower = self._place_kind("basica", self._valid_spots(1)[0])
        self._spawn_enemy(hp=100000, progress=tower.position)

        self.controller.update(0.05)
        self.assertEqual(len(self.model.shots), 1)

        # sin vista que los consuma, el siguiente update los descarta
        self.controller.update(0.05)
        self.assertEqual(self.model.shots, [])

    # ------------------------------------------------------------------
    # 3. Proyectil -> impacto (solo visual, sin danio extra)
    # ------------------------------------------------------------------
    def test_projectile_arrives_and_spawns_impact(self):
        tower = self._place_kind("basica", self._valid_spots(1)[0])
        enemy = self._spawn_enemy(hp=1000, progress=tower.position)
        self.controller.update(0.05)
        self.assertEqual(len(self.window.projectiles), 0)
        self.window.draw()
        self.assertEqual(len(self.window.projectiles), 1)

        self._run_until_projectiles_land()

        self.assertEqual(self.window.projectiles, [])
        self.assertEqual(len(self.window.impacts), 1)
        self.assertEqual(self.window.impacts[0]["kind"], "basica")
        self.assertEqual(enemy.hp, 1000 - tower.damage)

    def test_projectile_starts_at_tower_map_position(self):
        tower = self._place_kind("basica", self._valid_spots(1)[0])
        self._spawn_enemy(hp=1000, progress=tower.position)
        self.controller.update(0.05)

        self.window.draw()

        proyectil = self.window.projectiles[0]
        self.assertAlmostEqual(proyectil["x"], tower.map_x)
        self.assertAlmostEqual(proyectil["y"], tower.map_y)

    def test_fall_rotation_orients_along_movement_and_pitches_down(self):
        """35.png (dibujado cayendo) se orienta al moverse y gira a 0."""
        spec = {"rotate": "fall"}
        window = self.window

        # Derecha: se orienta a 90 grados y va girando hacia 0.
        projectile = {"angle": 0.0, "age": 0.0}
        window._update_projectile_rotation(projectile, spec, 10.0, 0.0, 10.0, 0.0)
        self.assertAlmostEqual(projectile["angle"], 90.0)

        window._update_projectile_rotation(projectile, spec, 10.0, 0.0, 10.0, 0.05)
        self.assertAlmostEqual(projectile["angle"], 82.5)

        for _ in range(40):
            window._update_projectile_rotation(projectile, spec, 10.0, 0.0, 10.0, 0.05)
        self.assertAlmostEqual(projectile["angle"] % 360.0, 0.0)

        # Abajo: ya es caida, no rota.
        projectile = {"angle": 0.0, "age": 0.0}
        window._update_projectile_rotation(projectile, spec, 0.0, 5.0, 5.0, 0.0)
        self.assertAlmostEqual(projectile["angle"], 0.0)
        window._update_projectile_rotation(projectile, spec, 0.0, 5.0, 5.0, 0.1)
        self.assertAlmostEqual(projectile["angle"] % 360.0, 0.0)

        # Arriba: 180 grados y converge a 0 (caida).
        projectile = {"angle": 0.0, "age": 0.0}
        window._update_projectile_rotation(projectile, spec, 0.0, -10.0, 10.0, 0.0)
        self.assertAlmostEqual(projectile["angle"], 180.0)
        for _ in range(20):
            window._update_projectile_rotation(projectile, spec, 0.0, -10.0, 10.0, 0.1)
        self.assertAlmostEqual(projectile["angle"] % 360.0, 0.0)

        # Izquierda: 270 grados y converge a 0 por el camino corto.
        projectile = {"angle": 0.0, "age": 0.0}
        window._update_projectile_rotation(projectile, spec, -10.0, 0.0, 10.0, 0.0)
        self.assertAlmostEqual(projectile["angle"], 270.0)
        for _ in range(15):
            window._update_projectile_rotation(projectile, spec, -10.0, 0.0, 10.0, 0.1)
        self.assertAlmostEqual(projectile["angle"] % 360.0, 0.0)

    def test_impact_appears_at_enemy_map_position(self):
        tower = self._place_kind("basica", self._valid_spots(1)[0])
        enemy = self._spawn_enemy(hp=1000, progress=tower.position)
        self.controller.update(0.05)
        self.window.draw()

        self._run_until_projectiles_land()

        fraccion = enemy.progress / self.model.path_length
        map_x, map_y = self.tiled_map.point_at_fraction(fraccion)
        impacto = self.window.impacts[0]
        self.assertAlmostEqual(impacto["x"], map_x, delta=1.0)
        self.assertAlmostEqual(impacto["y"], map_y, delta=1.0)

    def test_impact_expires_after_its_frames(self):
        tower = self._place_kind("basica", self._valid_spots(1)[0])
        self._spawn_enemy(hp=1000, progress=tower.position)
        self.controller.update(0.05)
        self.window.draw()

        self._run_draws(80)

        self.assertEqual(self.window.impacts, [])
        self.assertEqual(self.window.projectiles, [])

    def test_animation_does_not_duplicate_damage(self):
        tower = self._place_kind("fuego", self._valid_spots(1)[0])
        enemy = self._spawn_enemy(hp=10000, progress=tower.position)

        self.controller.update(0.05)
        tras_disparo = enemy.hp
        self.assertEqual(tras_disparo, 10000 - tower.damage)

        # proyectil completo + impacto completo, sin nuevos updates
        self._run_draws(120)

        self.assertEqual(enemy.hp, tras_disparo)
        self.assertEqual(self.window.projectiles, [])
        self.assertEqual(self.window.impacts, [])

    def test_cooldown_prevents_extra_damage_without_new_shot(self):
        tower = self._place_kind("pesada", self._valid_spots(1)[0])
        enemy = self._spawn_enemy(hp=100000, progress=tower.position)

        self.controller.update(0.05)
        self.assertEqual(enemy.hp, 100000 - tower.damage)
        self.assertEqual(len(self.model.shots), 1)

        self.controller.update(0.05)
        self.assertEqual(enemy.hp, 100000 - tower.damage)
        self.assertEqual(self.model.shots, [])

    def test_fire_progress_active_right_after_shot(self):
        tower = self._place_kind("basica", self._valid_spots(1)[0])
        self._spawn_enemy(hp=100000, progress=tower.position)

        self.controller.update(0.05)
        self.window.draw()

        # recien disparada: cooldown lleno -> progreso 0; un frame
        # despues con dt mayor que cero ya hay animacion de disparo
        self.window._dt = 0.05
        self.window.draw()
        progreso = self.window._tower_fire_progress(tower)
        self.assertGreater(progreso, 0.0)
        self.assertLessEqual(progreso, 1.0)

    def test_hover_hidden_while_projectile_in_flight(self):
        tower = self._place_kind("basica", self._valid_spots(1)[0])
        self._spawn_enemy(hp=100000, progress=tower.position)
        self.controller.update(0.05)
        self.window.draw()

        self.assertTrue(self.window.projectiles)
        self.assertIsNone(self.window._tower_hover_position(tower, 0.0))

        self._run_until_projectiles_land()
        # sin proyectil en vuelo vuelve el flote (si la torre no
        # esta justo en la ventana de animacion de disparo)
        self.window._fire_timers.clear()
        self.assertIsNotNone(self.window._tower_hover_position(tower, 0.0))

    # ------------------------------------------------------------------
    # 4. Los tres tipos en pantalla
    # ------------------------------------------------------------------
    def test_three_kinds_fly_and_impact(self):
        kinds = ("basica", "fuego", "pesada")
        spots = self._valid_spots(3, min_distance=GameWindow.TOWER_RANGE_PX * 2.2)
        towers = [
            self._place_kind(kind, spot) for kind, spot in zip(kinds, spots)
        ]
        enemies = [
            self._spawn_enemy(hp=100000, progress=tower.position)
            for tower in towers
        ]

        self.controller.update(0.05)
        self.assertEqual(
            sorted(shot["kind"] for shot in self.model.shots), sorted(kinds)
        )

        self.window.draw()
        self.assertEqual(len(self.window.projectiles), 3)
        self.assertEqual(
            sorted(p["kind"] for p in self.window.projectiles), sorted(kinds)
        )

        vistos = set()
        self.window._dt = 0.05
        for _ in range(80):
            self.window.draw()
            for projectile in self.window.projectiles:
                vistos.add(projectile["kind"])
            for impact in self.window.impacts:
                vistos.add(impact["kind"])
            if not self.window.projectiles and not self.window.impacts:
                break

        self.assertEqual(vistos, set(kinds))
        self.assertEqual(self.window.projectiles, [])
        self.assertEqual(self.window.impacts, [])
        for tower, enemy in zip(towers, enemies):
            self.assertEqual(enemy.hp, 100000 - tower.damage)

    def test_each_kind_draws_sprite_projectile_and_impact(self):
        kinds = ("basica", "fuego", "pesada")
        spots = self._valid_spots(3, min_distance=GameWindow.TOWER_RANGE_PX * 2.2)
        for kind, spot in zip(kinds, spots):
            tower = self._place_kind(kind, spot)
            self._spawn_enemy(hp=100000, progress=tower.position)

        self.controller.update(0.05)
        self.window.draw()

        self.assertEqual(len(self.window.projectiles), 3)
        for kind in kinds:
            sprite = self.window.assets.tower(kind)
            self.assertGreater(sprite.get_width(), 0)
            self.assertGreater(len(self.window.assets.impact_frames(kind)), 0)

        self._run_draws(120)


if __name__ == "__main__":
    unittest.main()
