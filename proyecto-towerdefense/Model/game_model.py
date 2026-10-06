"""
Modelo base del Tower Defense (Semana 1).

Relaciona las estructuras de datos con el funcionamiento del juego:

    Queue          -> enemigos esperando para entrar al mapa.
    DoublyLinkedList -> enemigos activos dentro del mapa.
    Stack          -> historial de acciones (base Undo/Redo).

Flujo conceptual:

    Oleada -> QUEUE (espera) -> dequeue() -> LISTA DOBLE (activos)
                                            -> torre elimina enemigo
                                            -> remove_node()
"""

from Model.structures import DoublyLinkedList, Queue, Stack


class Enemy:
    """Representacion basica de un enemigo del juego."""

    def __init__(self, enemy_id, name="Enemy", hp=100, speed=1.0, progress=0.0):
        self.enemy_id = enemy_id
        self.name = name
        self.hp = hp
        self.max_hp = hp
        self.speed = speed
        self.progress = progress

    @property
    def is_alive(self):
        """True mientras tenga puntos de vida."""
        return self.hp > 0

    def take_damage(self, damage):
        """Aplica danio y devuelve los puntos de vida restantes. O(1)."""
        self.hp = max(0, self.hp - damage)
        return self.hp

    def advance(self, distance):
        """Avanza por el recorrido. O(1)."""
        self.progress += distance * self.speed

    def __repr__(self):
        return (
            f"Enemy(id={self.enemy_id}, {self.name}, "
            f"hp={self.hp}/{self.max_hp}, progress={self.progress:.1f})"
        )


class GameModel:
    """Modelo base: administra enemigos con las estructuras de la Semana 1."""

    def __init__(self):
        self.pending_enemies = Queue()      # enemigos en espera (oleada)
        self.active_enemies = DoublyLinkedList()  # enemigos en el mapa
        self.action_history = Stack()       # historial (base Undo/Redo)
        self._next_enemy_id = 1

    # ------------------------------------------------------------------
    # Oleadas (Queue)
    # ------------------------------------------------------------------
    def create_enemy(self, name="Enemy", hp=100, speed=1.0):
        """Crea un enemigo con id correlativo. O(1)."""
        enemy = Enemy(self._next_enemy_id, name=name, hp=hp, speed=speed)
        self._next_enemy_id += 1
        return enemy

    def add_to_wave(self, enemy):
        """Agrega un enemigo a la cola de espera. O(1)."""
        self.pending_enemies.enqueue(enemy)
        self.action_history.push(("enqueue", enemy))
        return enemy

    def spawn_next(self):
        """Pasa el siguiente enemigo de la cola al mapa. O(1).

        dequeue() de la Queue + insert_last() de la lista doblemente enlazada.
        Devuelve None si no hay enemigos esperando.
        """
        enemy = self.pending_enemies.dequeue()
        if enemy is None:
            return None
        self.active_enemies.insert_last(enemy)
        self.action_history.push(("spawn", enemy))
        return enemy

    def spawn_all(self):
        """Pasa todos los enemigos pendientes al mapa. O(k) con k = pendientes."""
        spawned = []
        while not self.pending_enemies.is_empty():
            enemy = self.spawn_next()
            if enemy is not None:
                spawned.append(enemy)
        return spawned

    # ------------------------------------------------------------------
    # Combate (DoublyLinkedList)
    # ------------------------------------------------------------------
    def tower_attack(self, enemy, damage):
        """La torre ataca a un enemigo activo. O(n) para localizarlo si solo
        se conoce por valor; O(1) si se pasa el objeto/nodo directamente.

        Si el enemigo muere, su nodo se elimina de la lista en O(1).
        """
        if enemy not in self.active_enemies:
            return False, enemy.hp

        remaining_hp = enemy.take_damage(damage)
        if not enemy.is_alive:
            self.active_enemies.remove(enemy)
            self.action_history.push(("kill", enemy))
            return True, remaining_hp
        return False, remaining_hp

    def remove_enemy(self, enemy):
        """Elimina un enemigo activo sin comprobar vida. O(n) buscar + O(1) reenlazar."""
        removed = self.active_enemies.remove(enemy)
        if removed:
            self.action_history.push(("remove", enemy))
        return removed

    # ------------------------------------------------------------------
    # Historial (Stack) - base para Undo/Redo
    # ------------------------------------------------------------------
    def undo(self):
        """Recupera (y descarta) la ultima accion registrada. O(1).

        Base del sistema Undo/Redo; la implementacion completa podra
        ampliarse con una segunda pila (Redo) en etapas posteriores.
        """
        return self.action_history.pop()

    def peek_last_action(self):
        """Consulta la ultima accion sin retirarla. O(1)."""
        return self.action_history.peek()

    # ------------------------------------------------------------------
    # Estado (para la Vista)
    # ------------------------------------------------------------------
    @property
    def pending_count(self):
        return len(self.pending_enemies)

    @property
    def active_count(self):
        return len(self.active_enemies)

    @property
    def history_count(self):
        return len(self.action_history)

    def get_state(self):
        """Devuelve un diccionario con el estado completo del modelo. O(n)."""
        return {
            "pending": self.pending_enemies.to_list(),
            "active": self.active_enemies.to_list(),
            "history": self.action_history.to_list(),
        }

    def __repr__(self):
        return (
            f"GameModel(pendientes={self.pending_count}, "
            f"activos={self.active_count}, acciones={self.history_count})"
        )
