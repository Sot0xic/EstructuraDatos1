"""
Punto de entrada del Tower Defense (Semanas 2 y 3).

    Abre la ventana de Pygame, carga el mapa de Tiled, crea el
    controlador, una oleada inicial con torres y ejecuta el ciclo
    del juego:

        eventos -> actualizacion del modelo -> dibujo de la vista

    Mientras la tienda emergente o el menu de pausa esten abiertos
    (window.paused) se omite la actualizacion del modelo: la
    simulacion queda en pausa hasta que el jugador los cierre.

    La demostracion de las estructuras de datos de la Semana 1 se
    conserva en demo_estructuras.py.

Ejecutar desde la raiz del proyecto:

    python main.py
"""

import os

from Controller.game_controller import GameController
from Model.game_model import GameModel
from View.game_window import GameWindow
from View.tiled_map import TiledMap

MAP_PATH = os.path.join("assets", "mapas", "mapa_principal.tmx")


def create_controller(tiled_map):
    """Crea el controlador con una oleada inicial. O(k)."""
    model = GameModel(path_length=tiled_map.path_length())
    controller = GameController(model=model, view=None, spawn_interval=1.0)

    controller.start_wave(
        [
            {"name": "Goblin", "hp": 60, "speed": 90},
            {"name": "Duende", "hp": 40, "speed": 130},
            {"name": "Orco", "hp": 120, "speed": 60},
            {"name": "Goblin", "hp": 60, "speed": 90},
            {"name": "Dragon", "hp": 200, "speed": 75},
            {"name": "Duende", "hp": 40, "speed": 130},
            {"name": "Orco", "hp": 120, "speed": 60},
            {"name": "Dragon", "hp": 200, "speed": 75},
        ]
    )

    return controller


def main():
    import pygame
    pygame.init()
    pygame.display.set_mode((1280, 720))
    tiled_map = TiledMap(MAP_PATH)
    controller = create_controller(tiled_map)
    window = GameWindow(controller.model, tiled_map)

    running = True
    while running:
        dt = window.tick()
        running = window.process_events()
        if not window.paused:
            controller.update(dt)
        window.draw()

    window.close()


if __name__ == "__main__":
    main()
