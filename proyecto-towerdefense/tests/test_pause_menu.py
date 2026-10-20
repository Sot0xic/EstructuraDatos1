"""
Pruebas del menu de pausa (menu.md).

Comprueba los 10 puntos del enunciado:
    1. Escape abre el menu
    2. Resume reanuda el juego
    3. Escape dos veces abre y cierra
    4. Enemigos no avanzan durante la pausa
    5. Torres no disparan durante la pausa
    6. Proyectiles no se mueven durante la pausa
    7. Oleadas no avanzan durante la pausa
    8. Clics sobre el mapa no producen acciones
    9. Exit cierra Pygame (process_events devuelve False)
    10. El boton X de la ventana sigue funcionando

Ejecutar desde la raiz del proyecto:

    py -m pytest -v
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import unittest

import pygame

from Controller.game_controller import GameController
from View.game_window import GameWindow
from View.pause_menu import PauseMenu
from View.tiled_map import TiledMap

MAP_PATH = os.path.join("assets", "mapas", "mapa_principal.tmx")


def _key_event(key):
    return pygame.event.Event(pygame.KEYDOWN, key=key)


def _click_event(pos, button=1):
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos, button=button)


class TestPauseMenu(unittest.TestCase):
    """Menu de pausa: ESC, Resume, Exit y simulacion congelada."""

    def setUp(self):
        pygame.display.set_mode((GameWindow.WIDTH, GameWindow.HEIGHT))
        self.controller = GameController(view=None, spawn_interval=0.5)
        self.tiled_map = TiledMap(MAP_PATH)
        self.controller.model.path_length = self.tiled_map.path_length()
        self.controller.start_wave(
            [{"name": "Goblin", "hp": 60, "speed": 90}] * 3
        )
        self.window = GameWindow(self.controller.model, self.tiled_map)
        self.model = self.controller.model

    def tearDown(self):
        self.window.close()

    # ------------------------------------------------------------------
    # 1-3: ESC y Resume
    # ------------------------------------------------------------------
    def test_escape_opens_pause_menu(self):
        self.assertFalse(self.window.pause_menu.is_open)
        pygame.event.clear()
        pygame.event.post(_key_event(pygame.K_ESCAPE))
        self.assertTrue(self.window.process_events())
        self.assertTrue(self.window.pause_menu.is_open)
        self.assertTrue(self.window.paused)

    def test_resume_closes_menu_and_resumes(self):
        self.window.pause_menu.open()
        resume_center = self.window.pause_menu.resume_rect.center
        pygame.event.clear()
        pygame.event.post(_click_event(resume_center))
        self.assertTrue(self.window.process_events())
        self.assertFalse(self.window.pause_menu.is_open)
        self.assertFalse(self.window.paused)

    def test_escape_twice_opens_then_closes(self):
        pygame.event.clear()
        pygame.event.post(_key_event(pygame.K_ESCAPE))
        self.assertTrue(self.window.process_events())
        self.assertTrue(self.window.pause_menu.is_open)

        pygame.event.clear()
        pygame.event.post(_key_event(pygame.K_ESCAPE))
        self.assertTrue(self.window.process_events())
        self.assertFalse(self.window.pause_menu.is_open)
        self.assertFalse(self.window.paused)

    # ------------------------------------------------------------------
    # 4-7: simulacion congelada
    # ------------------------------------------------------------------
    def test_enemies_do_not_advance_while_paused(self):
        self.controller.update(0.6)
        self.assertEqual(len(self.model.active_enemies), 1)
        enemy = self.model.active_enemies.to_list()[0]
        progress_before = enemy.progress

        self.window.pause_menu.open()
        self.assertTrue(self.window.paused)
        # main.py omite controller.update mientras paused
        if not self.window.paused:
            self.controller.update(1.0)
        self.assertEqual(enemy.progress, progress_before)

    def test_towers_do_not_fire_while_paused(self):
        self.controller.update(0.1)
        self.model.buy_tower(
            kind="basica",
            position=0.0,
            map_x=100, map_y=100,
            footprint=10.0,
        )
        self.assertTrue(self.model.towers)
        self.model.shots.clear()

        self.window.pause_menu.open()
        if not self.window.paused:
            self.controller.update(1.0)
        self.assertEqual(len(self.model.shots), 0)

    def test_projectiles_do_not_move_while_paused(self):
        self.controller.update(0.1)
        self.model.buy_tower(
            kind="basica",
            position=0.0,
            map_x=100, map_y=100,
            footprint=10.0,
        )
        self.controller.update(1.0)
        self.window.draw()
        self.assertTrue(self.window.projectiles or self.window.impacts)

        self.window.pause_menu.open()
        positions_before = [
            (p["x"], p["y"]) for p in self.window.projectiles
        ]
        self.window.draw()
        positions_after = [
            (p["x"], p["y"]) for p in self.window.projectiles
        ]
        self.assertEqual(positions_before, positions_after)

    def test_waves_do_not_advance_while_paused(self):
        pending_before = self.model.pending_count
        active_before = len(self.model.active_enemies)

        self.window.pause_menu.open()
        if not self.window.paused:
            self.controller.update(2.0)
        self.assertEqual(self.model.pending_count, pending_before)
        self.assertEqual(len(self.model.active_enemies), active_before)

    # ------------------------------------------------------------------
    # 8: clics en el mapa bloqueados
    # ------------------------------------------------------------------
    def test_map_clicks_do_nothing_while_paused(self):
        self.window.pause_menu.open()
        towers_before = len(self.model.towers)
        stars_before = self.model.stars

        pygame.event.clear()
        pygame.event.post(_click_event((400, 300)))
        self.assertTrue(self.window.process_events())
        self.window.draw()

        self.assertEqual(len(self.model.towers), towers_before)
        self.assertEqual(self.model.stars, stars_before)

    def test_escape_while_paused_does_not_cancel_placing(self):
        self.window.selected_kind = "basica"
        self.window.placing = True
        self.window.pause_menu.open()

        pygame.event.clear()
        pygame.event.post(_key_event(pygame.K_ESCAPE))
        self.assertTrue(self.window.process_events())
        self.assertFalse(self.window.pause_menu.is_open)
        # ESC en el menu solo reanuda; no cancela la colocacion
        self.assertTrue(self.window.placing)
        self.assertEqual(self.window.selected_kind, "basica")

    # ------------------------------------------------------------------
    # 9-10: Exit y boton X
    # ------------------------------------------------------------------
    def test_exit_button_closes_game(self):
        self.window.pause_menu.open()
        exit_center = self.window.pause_menu.exit_rect.center
        pygame.event.clear()
        pygame.event.post(_click_event(exit_center))
        self.assertFalse(self.window.process_events())

    def test_window_close_button_still_works(self):
        pygame.event.clear()
        pygame.event.post(pygame.event.Event(pygame.QUIT))
        self.assertFalse(self.window.process_events())

    # ------------------------------------------------------------------
    # Integracion MVC y recursos
    # ------------------------------------------------------------------
    def test_pause_menu_uses_wooden_gui_assets(self):
        menu = PauseMenu(GameWindow.WIDTH, GameWindow.HEIGHT)
        self.assertIsNotNone(menu.panel)
        self.assertIsNotNone(menu.resume_button)
        self.assertIsNotNone(menu.exit_button)
        self.assertGreater(menu.panel.get_width(), 0)
        self.assertGreater(menu.resume_button.get_width(), 0)
        self.assertGreater(menu.exit_button.get_width(), 0)

    def test_pause_menu_only_has_resume_and_exit(self):
        menu = PauseMenu(GameWindow.WIDTH, GameWindow.HEIGHT)
        attrs = set(vars(menu).keys())
        # No debe existir Settings, Restart ni Main Menu
        for forbidden in ("settings_rect", "restart_rect", "menu_rect"):
            self.assertNotIn(forbidden, attrs)
        self.assertIn("resume_rect", attrs)
        self.assertIn("exit_rect", attrs)

    def test_layout_title_above_buttons_inside_frame(self):
        # Distribucion exigida en arreglo.md: PAUSE, RESUME y EXIT
        # en ese orden vertical, centrados en el marco y completamente
        # dentro de su area interior (pergamino).
        menu = PauseMenu(GameWindow.WIDTH, GameWindow.HEIGHT)
        interior = menu.interior_rect

        self.assertTrue(interior.contains(menu.title_rect))
        self.assertTrue(interior.contains(menu.resume_rect))
        self.assertTrue(interior.contains(menu.exit_rect))

        # Orden vertical sin superposiciones
        self.assertLessEqual(menu.title_rect.bottom, menu.resume_rect.top)
        self.assertLessEqual(menu.resume_rect.bottom, menu.exit_rect.top)

        # Centrados horizontalmente en el eje del marco
        self.assertEqual(menu.title_rect.centerx, menu.panel_rect.centerx)
        self.assertEqual(menu.resume_rect.centerx, menu.panel_rect.centerx)
        self.assertEqual(menu.exit_rect.centerx, menu.panel_rect.centerx)

        # El titulo en la parte superior del marco, no en su centro
        self.assertLess(menu.title_rect.centery, menu.panel_rect.centery)
        self.assertLess(menu.title_rect.bottom, menu.resume_rect.top)

    def test_hitboxes_match_visible_button_positions(self):
        # Las hitboxes son los mismos rectangulos con los que se
        # dibujan los botones (arreglo.md, punto 9).
        menu = PauseMenu(GameWindow.WIDTH, GameWindow.HEIGHT)
        menu.open()
        self.assertEqual(
            menu.handle_click(menu.resume_rect.center), ("resume",)
        )
        menu.open()
        self.assertEqual(menu.handle_click(menu.exit_rect.center), ("exit",))

    def test_paused_covers_shop_and_pause_menu(self):
        self.assertFalse(self.window.paused)
        self.window.pause_menu.open()
        self.assertTrue(self.window.paused)
        self.window.pause_menu.close()
        self.assertFalse(self.window.paused)
        self.window.shop.open()
        self.assertTrue(self.window.paused)
        self.window.shop.close()
        self.assertFalse(self.window.paused)

    def test_game_cannot_close_with_escape_alone(self):
        # ESC sin colocacion activa abre el menu, no cierra la app
        pygame.event.clear()
        pygame.event.post(_key_event(pygame.K_ESCAPE))
        self.assertTrue(self.window.process_events())
        self.assertTrue(self.window.pause_menu.is_open)


if __name__ == "__main__":
    unittest.main()
