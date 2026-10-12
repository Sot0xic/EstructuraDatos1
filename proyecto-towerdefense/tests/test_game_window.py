"""
Smoke test de la ventana de Pygame (Semana 2).

Comprueba que la ventana se puede abrir, dibujar y cerrar sin errores.
Usa el controlador de video "dummy" para no abrir una ventana real.

Ejecutar desde la raiz del proyecto:

    py -m pytest -v
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import unittest

import pygame

from Controller.game_controller import GameController
from View.game_window import GameWindow


class TestGameWindow(unittest.TestCase):
    """Pruebas basicas de la vista grafica."""

    def setUp(self):
        self.controller = GameController(view=None, spawn_interval=1.5)
        self.controller.start_wave([{"name": "Goblin", "hp": 60, "speed": 2.0}])
        self.controller.spawn_all()
        self.controller.place_tower(damage=5, range=4.0, position=6.0)
        self.window = GameWindow(self.controller.model)

    def tearDown(self):
        self.window.close()

    def test_window_opens(self):
        self.assertIsNotNone(pygame.display.get_surface())
        self.assertEqual(pygame.display.get_caption()[0], "Tower Defense - Semana 2")

    def test_draw_without_errors(self):
        self.controller.update(0.1)
        self.window.draw()

    def test_process_events_returns_running(self):
        self.assertTrue(self.window.process_events())

    def test_tick_limits_frame_time(self):
        dt = self.window.tick()
        self.assertGreaterEqual(dt, 0.0)
        self.assertLessEqual(dt, GameWindow.MAX_FRAME_TIME)

    def test_close_quits_pygame(self):
        self.window.close()
        self.assertFalse(pygame.display.get_init())


if __name__ == "__main__":
    unittest.main()
