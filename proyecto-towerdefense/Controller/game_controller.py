"""
Controlador del Tower Defense (Semanas 1 y 2).

Conecta las acciones del juego con el modelo y la vista.
Ademas de los comandos basicos de la Semana 1 (start_wave, spawn_next,
spawn_all, attack, undo y render), expone update(dt) para integrar
aparicion, movimiento y combate de torres dentro del ciclo de Pygame.
"""

from Model.game_model import GameModel


class GameController:
    """Coordina el modelo (estructuras) y la vista (impresion)."""

    def __init__(self, model=None, view=None, spawn_interval=1.5):
        self.model = model if model is not None else GameModel()
        self.view = view
        self.spawn_interval = spawn_interval
        self._spawn_timer = 0.0

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

    def place_tower(
        self, name="Tower", damage=25, range=3.0, position=0.0,
        map_x=None, map_y=None, footprint=0.0, attack_interval=1.0,
    ):
        """Crea una torre y la registra en el mapa. O(1)."""
        tower = self.model.create_tower(
            name=name, damage=damage, range=range, position=position,
            map_x=map_x, map_y=map_y, footprint=footprint,
            attack_interval=attack_interval,
        )
        self.render()
        return tower

    def attack(self, enemy, damage):
        """Ataca con una torre a un enemigo activo. O(n) + O(1)."""
        result = self.model.tower_attack(enemy, damage)
        self.render()
        return result

    def update(self, dt=1.0):
        """Actualiza el juego: aparicion, movimiento y combate. O(n*m).

        1. Hace aparecer enemigos de la cola cada spawn_interval segundos.
        2. Avanza solo a los enemigos activos (los pendientes no avanzan).
        3. Cada torre ataca a un solo enemigo, el que tiene menos vida
           dentro de su alcance, y solo cuando termino su cooldown
           (attack_interval segundos desde el ataque anterior).
        4. Retira a los enemigos derrotados o que llegaron al final.
        """
        self._spawn_timer += dt
        while self.spawn_interval > 0 and self._spawn_timer >= self.spawn_interval:
            self._spawn_timer -= self.spawn_interval
            if self.model.pending_count == 0:
                self._spawn_timer = 0.0
                break
            self.model.spawn_next()

        self.model.advance_enemies(dt)

        for tower in self.model.towers:
            tower.refresh(dt)
            if not tower.is_ready:
                continue
            target = None
            for enemy in self.model.active_enemies.to_list():
                if not tower.is_in_range(enemy):
                    continue
                if target is None or enemy.hp < target.hp:
                    target = enemy
            if target is not None:
                tower.attack(self.model, target)
                tower.start_cooldown()

        self.model.remove_escaped()

    def undo(self):
        """Recupera la ultima accion del historial. O(1)."""
        action = self.model.undo()
        self.render()
        return action

    def render(self):
        """Dibuja el estado actual en la vista (si hay vista configurada)."""
        if self.view is not None:
            self.view.render(self.model)
