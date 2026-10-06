"""
Controlador del Tower Defense (Semana 1).

Conecta las acciones del juego con el modelo y la vista.
En etapas posteriores manejara la entrada del usuario con Pygame
(raton y teclado); por ahora expone los comandos basicos usados
por la simulacion de main.py.
"""

from Model.game_model import GameModel
from View.game_view import GameView


class GameController:
    """Coordina el modelo (estructuras) y la vista (impresion)."""

    def __init__(self, model=None, view=None):
        self.model = model if model is not None else GameModel()
        self.view = view if view is not None else GameView()

    def start_wave(self, enemies):
        """Registra una oleada completa en la cola de espera. O(k)."""
        for specs in enemies:
            if hasattr(specs, "get"):
                enemy = self.model.create_enemy(**specs)
            else:
                enemy = self.model.create_enemy(*specs)
            self.model.add_to_wave(enemy)
        self.render()

    def spawn_next(self):
        """Hace aparecer al siguiente enemigo de la cola. O(1)."""
        enemy = self.model.spawn_next()
        self.render()
        return enemy

    def spawn_all(self):
        """Hace aparecer a todos los enemigos pendientes. O(k)."""
        spawned = self.model.spawn_all()
        self.render()
        return spawned

    def attack(self, enemy, damage):
        """Ataca con una torre a un enemigo activo. O(n) + O(1)."""
        result = self.model.tower_attack(enemy, damage)
        self.render()
        return result

    def undo(self):
        """Recupera la ultima accion del historial. O(1)."""
        action = self.model.undo()
        self.render()
        return action

    def render(self):
        """Dibuja el estado actual en la vista."""
        self.view.render(self.model)
