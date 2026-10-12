"""
Punto de entrada del Tower Defense (Semana 2).

Abre la ventana de Pygame, crea el controlador, carga una oleada
inicial con torres y ejecuta el ciclo del juego:

    eventos -> actualizacion del modelo -> dibujo de la vista

La demostracion de las estructuras de datos de la Semana 1 se
conserva en demo_estructuras.py.

Ejecutar desde la raiz del proyecto:

    python main.py
"""

from Controller.game_controller import GameController
from View.game_window import GameWindow


def create_controller():
    """Crea el controlador con una oleada y varias torres. O(k)."""
    controller = GameController(view=None, spawn_interval=1.0)

    controller.start_wave(
        [
            {"name": "Goblin", "hp": 60, "speed": 3.0},
            {"name": "Duende", "hp": 40, "speed": 4.0},
            {"name": "Orco", "hp": 120, "speed": 2.5},
            {"name": "Goblin", "hp": 60, "speed": 3.0},
            {"name": "Dragon", "hp": 200, "speed": 2.0},
            {"name": "Duende", "hp": 40, "speed": 4.0},
            {"name": "Orco", "hp": 120, "speed": 2.5},
            {"name": "Dragon", "hp": 200, "speed": 2.0},
        ]
    )

    controller.place_tower(name="Torre 1", damage=0.44, range=4.0, position=6.0)
    controller.place_tower(name="Torre 2", damage=0.52, range=4.0, position=20.0)
    controller.place_tower(name="Torre 3", damage=0.42, range=4.0, position=34.0)

    return controller


def main():
    controller = create_controller()
    window = GameWindow(controller.model)

    running = True
    while running:
        dt = window.tick()
        running = window.process_events()
        controller.update(dt)
        window.draw()

    window.close()


if __name__ == "__main__":
    main()
