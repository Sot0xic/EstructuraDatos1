"""
Pruebas de los sprites animados de los enemigos (enemigos.md).

Comprueba que la representacion visual de los enemigos usa los PNG de
assets/enemigos sin tocar la logica del modelo ni del controlador:

    1. los cuatro tipos cargan sus sprites (walk/hurt/die, 20 frames)
    2. la animacion de caminar avanza con el tiempo y se repite
    3. los enemigos siguen el recorrido con su velocidad actual
    4. los fotogramas mantienen lienzo y ancla (sin saltos)
    5. hurt no interrumpe el movimiento ni el combate y vuelve a walk
    6. die se reproduce una sola vez y luego se elimina el visual
    7. los muertos no reciben dano ni bloquean el objetivo de torres
    8. la recompensa de 25 estrellas se paga una sola vez
    9. las animaciones se congelan con la tienda o la pausa abiertas
   10. se dibuja el sprite (no el circulo anterior)

Ejecutar desde la raiz del proyecto:

    py -m pytest tests/test_enemy_sprites.py -v
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import unittest

import pygame

from Controller.game_controller import GameController
from Model.game_model import ENEMY_KILL_REWARD, GameModel
from View.enemy_animations import ENEMY_HEIGHT_PX, EnemyAnimations
from View.game_window import GameWindow
from View.tiled_map import TiledMap

MAP_PATH = os.path.join("assets", "mapas", "mapa_principal.tmx")
ENEMY_TYPES = ("1", "2", "3", "4")
SENTINEL = (1, 2, 3)


class TestEnemySprites(unittest.TestCase):
    """Sprites animados de los enemigos (enemigos.md)."""

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
        self.model.undo_stack.clear()
        self.model.redo_stack.clear()
        self.model.towers.clear()
        self.model.shots.clear()
        self.model.reset_economy()
        self.model._next_enemy_id = 1
        self.model._next_tower_id = 1
        self.controller._spawn_timer = 0.0
        self.window._enemy_visuals.clear()
        self.window._dying_enemies.clear()
        self.window._dying_ids.clear()
        self.window.projectiles.clear()
        self.window.impacts.clear()
        self.window._fire_timers.clear()
        self.window._pending_click = None
        self.window._dt = 0.0
        self.window.pause_menu.close()
        self.window.shop.close()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _spawn_enemy(self, name="Goblin", hp=100, speed=1.0, progress=0.0):
        enemy = self.model.create_enemy(name=name, hp=hp, speed=speed)
        self.model.add_to_wave(enemy)
        self.model.spawn_next()
        enemy.progress = progress
        return enemy

    @staticmethod
    def _content_rect(surface):
        rects = pygame.mask.from_surface(surface, 8).get_bounding_rects()
        rect = rects[0].copy()
        for other in rects[1:]:
            rect = rect.union(other)
        return rect

    def _advance_window(self, dt):
        self.window._dt = dt
        self.window._advance_effects()

    # ------------------------------------------------------------------
    # 1. Los cuatro enemigos cargan sus sprites
    # ------------------------------------------------------------------
    def test_four_enemy_types_load_sprites(self):
        animations = EnemyAnimations(self.window.scale)

        for enemy_type in ENEMY_TYPES:
            self.assertTrue(animations.has(enemy_type))
            walk = animations.frames(enemy_type, "walk")
            hurt = animations.frames(enemy_type, "hurt")
            die = animations.frames(enemy_type, "die")
            self.assertEqual(len(walk), 20)
            self.assertEqual(len(hurt), 20)
            self.assertEqual(len(die), 20)
            self.assertEqual(
                {frame.get_size() for frame in walk}, {walk[0].get_size()}
            )
            self.assertGreater(animations.duration(enemy_type, "walk"), 0.0)
            self.assertGreater(animations.duration(enemy_type, "die"), 0.0)

            # ancla dentro del lienzo y alto del contenido igual a la
            # configuracion centralizada (ENEMY_HEIGHT_PX * escala)
            anchor = animations.anchor(enemy_type)
            width, height = animations.size(enemy_type)
            self.assertTrue(0 < anchor[0] < width)
            self.assertTrue(0 < anchor[1] <= height)
            target = ENEMY_HEIGHT_PX[enemy_type] * self.window.scale
            content = self._content_rect(walk[0])
            self.assertAlmostEqual(content.height, target, delta=3.0)

            # el volteo entrega el mismo contenido espejado
            flipped = animations.frames(enemy_type, "walk", flip=True)
            self.assertEqual(len(flipped), 20)
            self.assertEqual(
                animations.anchor(enemy_type, flip=True),
                (width - anchor[0], anchor[1]),
            )

    def test_wave_names_map_to_sprite_types(self):
        self.assertEqual(EnemyAnimations.type_for("Goblin"), "1")
        self.assertEqual(EnemyAnimations.type_for("Duende"), "2")
        self.assertEqual(EnemyAnimations.type_for("Orco"), "3")
        self.assertEqual(EnemyAnimations.type_for("Dragon"), "4")
        # nombre sin registrar: usa la carpeta por defecto
        self.assertEqual(EnemyAnimations.type_for("Enemigo raro"), "1")

    def test_enemy_names_get_their_sprite_type_in_window(self):
        for name, expected in (
            ("Goblin", "1"),
            ("Duende", "2"),
            ("Orco", "3"),
            ("Dragon", "4"),
        ):
            enemy = self._spawn_enemy(name=name)
            self.window._draw_enemies()
            state = self.window._enemy_visuals[enemy.enemy_id]
            self.assertEqual(state["type"], expected)
            self.assertIsNotNone(
                self.window.enemy_animations.frame(
                    state["type"], "walk", state["walk_time"]
                )
            )
            self.window._enemy_visuals.clear()
            self.model.active_enemies.clear()

    # ------------------------------------------------------------------
    # 2. La animacion de caminar avanza con el tiempo (independiente FPS)
    # ------------------------------------------------------------------
    def test_walk_animation_advances_in_time_and_loops(self):
        animations = EnemyAnimations(self.window.scale)
        step = 0.03  # paso de muestreo distinto de cualquier tasa de FPS

        for enemy_type in ENEMY_TYPES:
            walk = animations.frames(enemy_type, "walk")
            duration = animations.duration(enemy_type, "walk")

            # el fotograma depende solo del tiempo: misma hora, mismo
            # fotograma, sin importar cada cuantos frames se pinte
            self.assertIs(
                animations.frame(enemy_type, "walk", 0.25),
                animations.frame(enemy_type, "walk", 0.25),
            )

            seen = []
            moment = 0.0
            while moment < duration:
                seen.append(animations.frame(enemy_type, "walk", moment))
                moment += step

            # recorre los 20 fotogramas en orden y vuelve al primero
            self.assertEqual(len(set(map(id, seen))), 20)
            self.assertIs(seen[0], walk[0])
            wrap = duration + 0.01
            self.assertIs(
                animations.frame(enemy_type, "walk", wrap),
                animations.frame(enemy_type, "walk", wrap - duration),
            )

    # ------------------------------------------------------------------
    # 3. Siguen el recorrido sin cambiar la velocidad
    # ------------------------------------------------------------------
    def test_enemies_keep_speed_and_drawing_does_not_move_them(self):
        enemy = self._spawn_enemy(hp=1000, speed=2.5, progress=100.0)

        self.model.advance_enemies(0.5)
        self.assertAlmostEqual(enemy.progress, 100.0 + 0.5 * 2.5)

        # dibujar (y avanzar sus animaciones) no altera la posicion
        before = enemy.progress
        self.window._draw_enemies()
        self._advance_window(0.25)
        self.assertAlmostEqual(enemy.progress, before)

    # ------------------------------------------------------------------
    # 4. Los fotogramas no provocan saltos de posicion
    # ------------------------------------------------------------------
    def test_walk_frames_keep_canvas_and_head_stable(self):
        animations = EnemyAnimations(self.window.scale)

        for enemy_type in ENEMY_TYPES:
            walk = animations.frames(enemy_type, "walk")
            size = walk[0].get_size()
            tops = []
            for frame in walk:
                # lienzo constante: el sprite no se redimensiona
                self.assertEqual(frame.get_size(), size)
                tops.append(self._content_rect(frame).top)
            # la cabeza apenas se mueve entre fotogramas: el enemigo
            # camina sin desplazarse ni saltar de sitio
            self.assertLessEqual(max(tops) - min(tops), 6)

    # ------------------------------------------------------------------
    # 5. La animacion de dano funciona sin interrumpir el combate
    # ------------------------------------------------------------------
    def test_hurt_animation_does_not_interrupt_combat(self):
        tower = self.model.create_tower(kind="basica", position=0.0)
        enemy = self._spawn_enemy(hp=1000, speed=1.0, progress=0.0)
        self.window._draw_enemies()
        state = self.window._enemy_visuals[enemy.enemy_id]
        self.assertEqual(state["state"], "walk")

        killed, remaining = self.model.tower_attack(enemy, 10)
        self.assertFalse(killed)
        self.window._draw_enemies()
        self.assertEqual(state["state"], "hurt")
        self.assertEqual(state["state_time"], 0.0)

        # el movimiento continua igual mientras esta en hurt
        before = enemy.progress
        self.model.advance_enemies(0.4)
        self.assertAlmostEqual(enemy.progress, before + 0.4 * enemy.speed)

        # varios impactos seguidos no reinician la animacion
        self._advance_window(0.1)
        elapsed = state["state_time"]
        self.assertGreater(elapsed, 0.0)
        self.model.tower_attack(enemy, 10)
        self.window._draw_enemies()
        self.assertEqual(state["state"], "hurt")
        self.assertGreaterEqual(state["state_time"], elapsed)

        # la torre sigue atacando: el combate no se detiene
        self.controller.update(0.05)
        self.assertEqual(enemy.hp, 1000 - 10 - 10 - tower.damage)
        self.assertEqual(state["state"], "hurt")

        # al agotarse la animacion vuelve a walk
        for _ in range(30):
            self._advance_window(0.1)
            if state["state"] == "walk":
                break
        self.assertEqual(state["state"], "walk")
        self.assertEqual(state["state_time"], 0.0)

    # ------------------------------------------------------------------
    # 6. La animacion de muerte termina correctamente
    # ------------------------------------------------------------------
    def test_die_animation_plays_once_and_disappears(self):
        self.model.create_tower(kind="basica", position=0.0)
        enemy = self._spawn_enemy(hp=10, speed=1.0, progress=0.0)
        self.window._draw_enemies()  # crea su estado visual en vida

        self.controller.update(0.05)  # la torre lo mata
        self.assertFalse(enemy.is_alive)
        self.assertEqual(self.model.active_count, 0)

        self.window._consume_shots()  # la vista ve el disparo mortal
        self.assertEqual(len(self.window._dying_enemies), 1)
        self.assertEqual(self.window._dying_ids, {enemy.enemy_id})
        self.assertNotIn(enemy.enemy_id, self.window._enemy_visuals)
        state = self.window._dying_enemies[0]
        self.assertEqual(state["state"], "die")
        self.assertEqual(state["state_time"], 0.0)

        # dura lo que dura die y entonces se elimina el visual
        duration = self.window.enemy_animations.duration(
            state["type"], "die"
        )
        self.assertGreater(duration, 0.0)
        elapsed = 0.0
        while self.window._dying_enemies and elapsed < duration + 1.0:
            self._advance_window(0.1)
            elapsed += 0.1
        self.assertEqual(self.window._dying_enemies, [])
        self.assertEqual(self.window._dying_ids, set())

        # no reaparece al seguir avanzando ni entre los activos
        self._advance_window(0.5)
        self.assertEqual(self.window._dying_enemies, [])
        self.window._draw_enemies()
        self.assertEqual(self.window._enemy_visuals, {})

    # ------------------------------------------------------------------
    # 7. Los enemigos muertos no reciben dano ni bloquean objetivos
    # ------------------------------------------------------------------
    def test_dead_enemies_take_no_damage_and_do_not_block_targets(self):
        tower = self.model.create_tower(kind="basica", position=0.0)
        dead = self._spawn_enemy(hp=10, speed=1.0, progress=0.0)
        alive = self._spawn_enemy(
            name="Orco", hp=80, speed=1.0, progress=10.0
        )
        self.window._draw_enemies()

        self.controller.update(0.05)
        # eligio al de menor vida: el que ahora esta muerto
        self.assertFalse(dead.is_alive)
        self.assertTrue(alive.is_alive)

        result, hp = self.model.tower_attack(dead, 999)
        self.assertFalse(result)
        self.assertEqual(dead.hp, 0)

        # la torre sigue eligiendo al vivo (el muerto no lo bloquea)
        hp_before = alive.hp
        self.controller.update(1.1)  # supera el cooldown de 1.0 s
        self.assertLess(alive.hp, hp_before)
        self.assertEqual(dead.hp, 0)

    # ------------------------------------------------------------------
    # 8. Las recompensas no se duplican
    # ------------------------------------------------------------------
    def test_kill_reward_is_paid_only_once(self):
        self.model.create_tower(kind="basica", position=0.0)
        enemy = self._spawn_enemy(hp=10, speed=1.0, progress=0.0)
        stars_before = self.model.stars

        self.controller.update(0.05)
        self.assertFalse(enemy.is_alive)
        self.assertTrue(enemy.reward_claimed)
        self.assertEqual(
            self.model.stars, stars_before + ENEMY_KILL_REWARD
        )

        # ni otro ataque ni forzar el premio lo pagan de nuevo
        self.model.tower_attack(enemy, 999)
        self.model._grant_kill_reward(enemy)
        self.assertEqual(
            self.model.stars, stars_before + ENEMY_KILL_REWARD
        )

    # ------------------------------------------------------------------
    # 9. Las animaciones se congelan durante la pausa
    # ------------------------------------------------------------------
    def test_animations_freeze_while_paused(self):
        enemy = self._spawn_enemy(hp=1000, progress=0.0)
        self.window._draw_enemies()
        state = self.window._enemy_visuals[enemy.enemy_id]

        self._advance_window(0.5)
        self.assertAlmostEqual(state["walk_time"], 0.5)

        # deja una muerte en curso para congelarla tambien
        self.model.create_tower(kind="basica", position=0.0)
        victim = self._spawn_enemy(hp=10, progress=0.0)
        self.window._draw_enemies()
        self.controller.update(0.05)
        self.window._consume_shots()
        self.assertEqual(len(self.window._dying_enemies), 1)
        dying = self.window._dying_enemies[0]

        self.window.pause_menu.open()
        self.assertTrue(self.window.paused)
        walk_time = state["walk_time"]
        die_time = dying["state_time"]
        self._advance_window(5.0)
        self.assertEqual(state["walk_time"], walk_time)
        self.assertEqual(dying["state_time"], die_time)

        self.window.pause_menu.close()
        self.assertFalse(self.window.paused)
        self._advance_window(5.0)
        self.assertGreater(state["walk_time"], walk_time)
        self.assertGreater(dying["state_time"], die_time)

    # ------------------------------------------------------------------
    # 10. Se dibuja el sprite, no el circulo anterior
    # ------------------------------------------------------------------
    def test_enemy_is_drawn_as_sprite_not_circle(self):
        enemy = self._spawn_enemy(hp=1000, progress=100.0)

        self.window.screen.fill(SENTINEL)
        self.window._draw_enemies()
        state = self.window._enemy_visuals[enemy.enemy_id]
        self.assertEqual(state["state"], "walk")

        flip = state["facing"] < 0
        frame = self.window.enemy_animations.frame(
            state["type"], "walk", state["walk_time"], flip=flip
        )
        self.assertIsNotNone(frame)
        anchor = self.window.enemy_animations.anchor(
            state["type"], flip=flip
        )
        x, y = self.window._point_at(enemy.progress)
        x, y = int(x), int(y)

        # Por encima de la barra (y-20) y del circulo (radio 8) solo
        # puede haber pixeles del sprite: su cabeza ocupa la zona alta.
        found = False
        for py in range(y - anchor[1] + 2, y - 24):
            for px in range(x - anchor[0], x - anchor[0] + frame.get_width()):
                if self.window.screen.get_at((px, py))[:3] != SENTINEL:
                    found = True
                    break
            if found:
                break
        self.assertTrue(found, "No se dibujo el sprite del enemigo")


if __name__ == "__main__":
    unittest.main()
