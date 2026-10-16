"""
Modelo base del Tower Defense (Semanas 1 y 2).

Relaciona las estructuras de datos con el funcionamiento del juego:

    Queue          -> enemigos esperando para entrar al mapa.
    DoublyLinkedList -> enemigos activos dentro del mapa.
    Stack          -> historial de acciones (base Undo/Redo).
    Tower          -> torres que atacan a los enemigos en su alcance.

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
        self.max_hp = max(0, hp)
        self.hp = self.max_hp
        self.speed = speed
        self.progress = progress

    @property
    def is_alive(self):
        """True mientras tenga puntos de vida."""
        return self.hp > 0

    @property
    def is_defeated(self):
        """True cuando la vida llego a cero o menos."""
        return self.hp <= 0

    def take_damage(self, damage):
        """Aplica danio y devuelve los puntos de vida restantes. O(1).

        La vida nunca baja de cero ni supera la vida maxima; un valor
        de danio no positivo no modifica al enemigo.
        """
        if damage <= 0:
            return self.hp
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


class Tower:
    """Torre basica del juego (Semana 2).

    Cada torre tiene identificador, nombre, daño por ataque, alcance
    y una posicion sobre el recorrido (misma dimension que Enemy.progress).

    Ademas almacena su posicion en el mapa (map_x, map_y en pixeles
    del mapa de Tiled) y su radio de ocupacion (footprint) para la
    validacion de colocacion.

    El alcance es la distancia maxima, en unidades de progreso, a la que
    la torre puede alcanzar a un enemigo. position, range y
    Enemy.progress usan la misma dimension: con el mapa de Tiled son
    pixeles del mapa (Enemy.progress avanza en pixeles por segundo).

    attack_interval (en segundos) es el tiempo minimo entre ataques
    (cooldown); cooldown indica los segundos que faltan para el
    siguiente disparo.
    """

    def __init__(
        self, tower_id, name="Tower", damage=25, range=3.0, position=0.0,
        map_x=None, map_y=None, footprint=0.0, attack_interval=1.0,
    ):
        self.tower_id = tower_id
        self.name = name
        self.damage = damage
        self.range = range
        self.position = position
        self.map_x = map_x
        self.map_y = map_y
        self.footprint = footprint
        self.attack_interval = max(0.0, attack_interval)
        self.cooldown = 0.0

    @property
    def is_ready(self):
        """True cuando la torre ya puede volver a atacar. O(1)."""
        return self.cooldown <= 0.0

    def refresh(self, dt):
        """Descuenta el tiempo transcurrido del cooldown. O(1)."""
        if dt > 0.0:
            self.cooldown = max(0.0, self.cooldown - dt)

    def start_cooldown(self):
        """Reinicia el cooldown tras un ataque. O(1)."""
        self.cooldown = self.attack_interval

    def is_in_range(self, enemy):
        """True si el enemigo esta dentro del alcance. O(1)."""
        return abs(enemy.progress - self.position) <= self.range

    def attack(self, model, enemy):
        """Ataca al enemigo usando el combate del modelo. O(1) + O(n).

        Si el enemigo esta fuera del alcance no aplica danio. Si el
        enemigo ya fue eliminado, model.tower_attack tampoco lo modifica.
        """
        if not self.is_in_range(enemy):
            return False, enemy.hp
        return model.tower_attack(enemy, self.damage)

    def __repr__(self):
        return (
            f"Tower(id={self.tower_id}, {self.name}, "
            f"damage={self.damage}, range={self.range}, "
            f"position={self.position})"
        )


class GameModel:
    """Modelo base: administra enemigos con las estructuras de la Semana 1."""

    def __init__(self, path_length=40.0):
        self.pending_enemies = Queue()      # enemigos en espera (oleada)
        self.active_enemies = DoublyLinkedList()  # enemigos en el mapa
        self.action_history = Stack()       # historial (base Undo/Redo)
        self.towers = []                    # torres colocadas en el mapa
        self.path_length = path_length      # largo total del camino
        self._next_enemy_id = 1
        self._next_tower_id = 1

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
    # Torres (Semana 2)
    # ------------------------------------------------------------------
    def create_tower(
        self, name="Tower", damage=25, range=3.0, position=0.0,
        map_x=None, map_y=None, footprint=0.0, attack_interval=1.0,
    ):
        """Crea una torre y la registra en el mapa. O(1)."""
        tower = Tower(
            self._next_tower_id,
            name=name,
            damage=damage,
            range=range,
            position=position,
            map_x=map_x,
            map_y=map_y,
            footprint=footprint,
            attack_interval=attack_interval,
        )
        self._next_tower_id += 1
        self.towers.append(tower)
        self.action_history.push(("tower", tower))
        return tower

    def can_place_tower_at(self, map_x, map_y, footprint, tiled_map):
        """Comprueba si se puede colocar una torre en (map_x, map_y).

        Usa tiled_map.can_place_tower para validar contra zonas
        bloqueadas, limites del mapa y otras torres ya colocadas.
        Devuelve (True, "") si es valida, o (False, motivo).
        """
        return tiled_map.can_place_tower(
            map_x, map_y, footprint, existing_towers=self.towers
        )

    # ------------------------------------------------------------------
    # Movimiento (Dia 2 - Semana 2)
    # ------------------------------------------------------------------
    def advance_enemies(self, distance):
        """Avanza a todos los enemigos activos. O(n)."""
        enemies = self.active_enemies.to_list()

        for enemy in enemies:
            enemy.advance(distance)

    def remove_escaped(self):
        """Retira a los enemigos que llegaron al final del camino. O(n).

        Recorre la lista de activos y elimina con remove_node() en O(1)
        cada nodo cuyo enemigo alcanzo o supero path_length.
        Devuelve la lista de enemigos retirados.
        """
        removed = []
        node = self.active_enemies.head
        while node is not None:
            next_node = node.next
            enemy = node.data
            if enemy.progress >= self.path_length:
                self.active_enemies.remove_node(node)
                self.action_history.push(("escape", enemy))
                removed.append(enemy)
            node = next_node
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
