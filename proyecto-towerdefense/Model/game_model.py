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

# Alcance comun de todas las torres, en pixeles del mapa de Tiled
# (datos.md): misma dimension que Enemy.progress y Tower.position.
TOWER_RANGE = 210.0

# Registro centralizado de los 12 tipos de torre del catalogo
# (datos.md). Cada entrada define el nombre visible y las
# estadisticas de combate: damage por disparo, attack_interval en
# segundos (cooldown, que se descuenta con dt en Tower.refresh y
# por tanto no depende de los FPS) y range en pixeles de mapa,
# igual para las 12. El proyectil y los efectos visuales viven en
# View/tower_assets y View/tower_animations. Las tres primeras
# entradas son los tipos originales (teclas 1/2/3); torre_04..12
# son las nueve torres adicionales de la tienda, cuyo kind
# coincide con su variante de sprites.
TOWER_KINDS = {
    "basica": {
        "name": "Torre basica",
        "damage": 10,
        "attack_interval": 1.0,
        "range": TOWER_RANGE,
    },
    "fuego": {
        "name": "Torre de fuego",
        "damage": 14,
        "attack_interval": 0.9,
        "range": TOWER_RANGE,
    },
    "pesada": {
        "name": "Torre pesada",
        "damage": 22,
        "attack_interval": 1.1,
        "range": TOWER_RANGE,
    },
    "torre_04": {
        "name": "Torre de llamas",
        "damage": 12,
        "attack_interval": 0.5,
        "range": TOWER_RANGE,
    },
    "torre_05": {
        "name": "Torre gemela",
        "damage": 35,
        "attack_interval": 1.2,
        "range": TOWER_RANGE,
    },
    "torre_06": {
        "name": "Torre infernal",
        "damage": 20,
        "attack_interval": 0.6,
        "range": TOWER_RANGE,
    },
    "torre_07": {
        "name": "Lanzarrocas",
        "damage": 50,
        "attack_interval": 1.3,
        "range": TOWER_RANGE,
    },
    "torre_08": {
        "name": "Torre de piedra",
        "damage": 30,
        "attack_interval": 0.7,
        "range": TOWER_RANGE,
    },
    "torre_09": {
        "name": "Bastion de roca",
        "damage": 65,
        "attack_interval": 1.4,
        "range": TOWER_RANGE,
    },
    "torre_10": {
        "name": "Torre rocosa",
        "damage": 40,
        "attack_interval": 0.8,
        "range": TOWER_RANGE,
    },
    "torre_11": {
        "name": "Coloso de piedra",
        "damage": 80,
        "attack_interval": 1.5,
        "range": TOWER_RANGE,
    },
    "torre_12": {
        "name": "Guardian de piedra",
        "damage": 55,
        "attack_interval": 0.9,
        "range": TOWER_RANGE,
    },
}

# ---------------------------------------------------------------------------
# Economia (actualizacion.md): estrellas como moneda.
# ---------------------------------------------------------------------------
# Saldo inicial de estrellas con el que empieza el jugador.
STARTING_STARS = 500
# Recompensa en estrellas por cada enemigo eliminado por una torre. Se
# abona una sola vez por enemigo (Enemy.reward_claimed) para no duplicarla
# si mas de una torre lo alcanza o si el enemigo ya estaba muerto.
ENEMY_KILL_REWARD = 25

# Precio de cada variante de la tienda, en estrellas. Los valores viven
# SOLO aqui: la vista (ShopPanel) los consulta por variante y no debe
# duplicarlos. La variante 0 corresponde a la torre basica, la 1 a la
# de fuego, ..., la 11 a la ultima torre del catalogo (datos.md no
# altera estos precios).
SHOP_TOWER_PRICES = (
    100, 150, 200, 250, 300, 350,
    400, 450, 500, 550, 600, 650,
)
# Precio de cada torre jugable por tipo. Los 12 tipos de TOWER_KINDS
# estan mapeados a su variante de la tienda en el mismo orden, de modo
# que comprar cualquier kind cuesta exactamente lo que muestra su
# tarjeta (datos.md: la economia no cambia).
PLAYABLE_TOWER_PRICES = {
    "basica": SHOP_TOWER_PRICES[0],
    "fuego": SHOP_TOWER_PRICES[1],
    "pesada": SHOP_TOWER_PRICES[2],
    "torre_04": SHOP_TOWER_PRICES[3],
    "torre_05": SHOP_TOWER_PRICES[4],
    "torre_06": SHOP_TOWER_PRICES[5],
    "torre_07": SHOP_TOWER_PRICES[6],
    "torre_08": SHOP_TOWER_PRICES[7],
    "torre_09": SHOP_TOWER_PRICES[8],
    "torre_10": SHOP_TOWER_PRICES[9],
    "torre_11": SHOP_TOWER_PRICES[10],
    "torre_12": SHOP_TOWER_PRICES[11],
}


def tower_price(kind):
    """Precio en estrellas de una torre jugable por su tipo. O(1).

    Devuelve el precio registrado en PLAYABLE_TOWER_PRICES o 0 si el
    tipo no esta catalogado (por ejemplo, un tipo desbloqueado a mano
    en pruebas).
    """
    return PLAYABLE_TOWER_PRICES.get(kind, 0)


class Enemy:
    """Representacion basica de un enemigo del juego."""

    def __init__(self, enemy_id, name="Enemy", hp=100, speed=1.0, progress=0.0):
        self.enemy_id = enemy_id
        self.name = name
        self.max_hp = max(0, hp)
        self.hp = self.max_hp
        self.speed = speed
        self.progress = progress
        # La recompensa en estrellas (ENEMY_KILL_REWARD) se abona solo
        # la primera vez que el enemigo muere; ver GameModel._grant_kill.
        self.reward_claimed = False

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
    Si no se indica range se usa TOWER_RANGE (210 px, datos.md: el
    mismo alcance para las 12 torres).

    attack_interval (en segundos) es el tiempo minimo entre ataques
    (cooldown); cooldown indica los segundos que faltan para el
    siguiente disparo.

    kind identifica el tipo de torre (los registrados en
    TOWER_KINDS: basica, fuego, pesada, torre_04..torre_12) y
    determina que sprite y proyectil usara la vista.
    """

    def __init__(
        self, tower_id, name="Tower", damage=25, range=None, position=0.0,
        map_x=None, map_y=None, footprint=0.0, attack_interval=1.0,
        kind="basica",
    ):
        self.tower_id = tower_id
        self.name = name
        self.damage = damage
        self.range = TOWER_RANGE if range is None else range
        self.position = position
        self.map_x = map_x
        self.map_y = map_y
        self.footprint = footprint
        self.attack_interval = max(0.0, attack_interval)
        self.cooldown = 0.0
        self.kind = kind

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
        # Undo/Redo de colocaciones de torres (undoredo.md): dos pilas
        # propias (Stack) independientes del action_history de enemigos.
        # undo_stack guarda las colocaciones compradas que aun se pueden
        # deshacer; redo_stack las ya desechas y pendientes de restaurar.
        self.undo_stack = Stack()
        self.redo_stack = Stack()
        self.towers = []                    # torres colocadas en el mapa
        self.shots = []                     # eventos de disparo que la
                                            # vista consume al dibujar
        self.path_length = path_length      # largo total del camino
        # Economia: saldo actual en estrellas (actualizacion.md).
        self.stars = STARTING_STARS
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
            self._grant_kill_reward(enemy)
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
        self, kind="basica", name=None, damage=None, range=None,
        position=0.0, map_x=None, map_y=None, footprint=0.0,
        attack_interval=None,
    ):
        """Crea una torre del tipo indicado y la registra en el mapa. O(1).

        name, damage, attack_interval y range se toman del registro
        TOWER_KINDS del tipo (datos.md) salvo que se indiquen
        explicitamente; sin range indicado todas las torres quedan con
        el alcance comun TOWER_RANGE.
        """
        spec = TOWER_KINDS.get(kind, TOWER_KINDS["basica"])
        tower = Tower(
            self._next_tower_id,
            name=spec["name"] if name is None else name,
            damage=spec["damage"] if damage is None else damage,
            range=spec.get("range", TOWER_RANGE) if range is None else range,
            position=position,
            map_x=map_x,
            map_y=map_y,
            footprint=footprint,
            attack_interval=(
                spec["attack_interval"] if attack_interval is None
                else attack_interval
            ),
            kind=kind,
        )
        self._next_tower_id += 1
        self.towers.append(tower)
        self.action_history.push(("tower", tower))
        return tower

    def register_shot(self, tower, enemy):
        """Registra un disparo para que la vista lo anime. O(1).

        El danio se aplica una sola vez, en el momento del ataque
        (tower_attack); el disparo registrado aqui es solo un evento
        visual: la vista dibuja el proyectil y el impacto sin volver
        a tocar la vida del enemigo.
        """
        shot = {"kind": tower.kind, "tower": tower, "enemy": enemy}
        self.shots.append(shot)
        return shot

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
    # Economia (actualizacion.md): estrellas, precios y recompensas
    # ------------------------------------------------------------------
    def can_afford(self, kind):
        """True si el saldo alcanza para comprar una torre del tipo. O(1)."""
        return self.stars >= tower_price(kind)

    def spend_stars(self, amount):
        """Descuenta `amount` estrellas del saldo si hay fondos. O(1).

        Devuelve True si el descuento se aplico y False si `amount` es
        negativo o el saldo no alcanza (el saldo queda intacto).
        """
        if amount < 0 or self.stars < amount:
            return False
        self.stars -= amount
        return True

    def add_stars(self, amount):
        """Suma `amount` estrellas al saldo (recompensas, bonos). O(1).

        Devuelve el saldo resultante; un importe no positivo no cambia
        nada.
        """
        if amount > 0:
            self.stars += amount
        return self.stars

    def buy_tower(self, kind="basica", **tower_kwargs):
        """Compra una torre: valida saldo, la crea y descuenta su precio. O(1).

        Es la unica via de compra colocable: si el saldo no alcanza no
        se crea nada y se devuelve None. Si hay fondos se registra la
        torre (create_tower) y se descuenta su precio en el mismo paso,
        para que nunca se cobre sin colocar ni se coloque sin pagar.
        La colocacion queda registrada como accion deshacible (Undo) y
        invalida cualquier Redo pendiente (undoredo.md).
        Los kwarg extras (range, position, map_x, ...) se pasan a
        create_tower tal cual.
        """
        price = tower_price(kind)
        if self.stars < price:
            return None
        tower = self.create_tower(kind=kind, **tower_kwargs)
        self.stars -= price
        self._register_placement(tower, price)
        return tower

    def _grant_kill_reward(self, enemy):
        """Abona la recompensa por eliminar un enemigo, una sola vez. O(1).

        Se llama desde tower_attack al pasar el enemigo a is_alive.
        Usa enemy.reward_claimed para pagar solo la primera vez que
        muere, evitando recompensas duplicadas si otra torre lo remata
        o si el enemigo ya estaba fuera de la lista.
        """
        if enemy.reward_claimed:
            return 0
        enemy.reward_claimed = True
        self.add_stars(ENEMY_KILL_REWARD)
        return ENEMY_KILL_REWARD

    def reset_economy(self):
        """Reinicia la economia al estado inicial de partida. O(1).

        Vuelve el saldo a STARTING_STARS; las torres y el resto del
        modelo no se tocan (solo la moneda).
        """
        self.stars = STARTING_STARS
        return self.stars

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
    # Undo/Redo de colocaciones y venta (undoredo.md)
    # ------------------------------------------------------------------
    def _register_placement(self, tower, cost):
        """Registra una colocacion comprada como accion deshacible. O(1).

        Guarda los datos necesarios para deshacerla (devolver el 100%
        del costo pagado) y para restaurarla con Redo (tipo, alcance,
        posicion en el mapa, huella y costo). Una nueva colocacion
        invalida el Redo pendiente, como pide undoredo.md.
        """
        action = {
            "tower": tower,
            "kind": tower.kind,
            "range": tower.range,
            "position": tower.position,
            "map_x": tower.map_x,
            "map_y": tower.map_y,
            "footprint": tower.footprint,
            "cost": cost,
        }
        self.undo_stack.push(action)
        self.redo_stack.clear()
        return action

    def can_undo(self):
        """True si hay una colocacion valida pendiente de deshacer. O(1).

        Solo se permite deshacer UNA colocacion como maximo: tras un
        Undo exitoso la accion queda en redo_stack y el Undo se
        deshabilita hasta repetir la torre o colocar otra nueva.
        """
        return not self.undo_stack.is_empty() and self.redo_stack.is_empty()

    def can_redo(self):
        """True si hay una colocacion desecha pendiente de restaurar. O(1)."""
        return not self.redo_stack.is_empty()

    def undo_last_placement(self):
        """Deshace la ultima colocacion: quita la torre y devuelve el 100%. O(1).

        El costo pagado se reintegra completo con add_stars y la accion
        pasa a redo_stack para poder restaurarla. Si no hay colocacion
        deshacible no hace nada y devuelve None.
        """
        if not self.can_undo():
            return None
        action = self.undo_stack.pop()
        tower = action["tower"]
        if tower in self.towers:
            self.towers.remove(tower)
        self.add_stars(action["cost"])
        self.redo_stack.push(action)
        return action

    def redo_last_placement(self, tiled_map=None):
        """Restaura la torre eliminada por Undo cobrando su precio. O(z).

        Antes de restaurar comprueba que el saldo alcance y que la
        posicion siga disponible (misma coordenada libre y, si se pasa
        tiled_map, tambien valida contra zonas bloqueadas y limites). Si
        algo falta no realiza la operacion ni descarta la accion: el
        jugador puede reintentar. Tras un Redo exitoso la accion vuelve
        a undo_stack y redo_stack queda vacia (no se puede repetir).
        """
        if not self.can_redo():
            return None
        action = self.redo_stack.peek()
        if self.stars < action["cost"]:
            return None
        if self._placement_blocked(action, tiled_map):
            return None
        self.redo_stack.pop()
        tower = self.create_tower(
            kind=action["kind"],
            range=action["range"],
            position=action["position"],
            map_x=action["map_x"],
            map_y=action["map_y"],
            footprint=action["footprint"],
        )
        self.spend_stars(action["cost"])
        action["tower"] = tower
        self.undo_stack.push(action)
        return action

    def _placement_blocked(self, action, tiled_map):
        """True si la posicion de la accion ya no esta disponible. O(t).

        Sin mapa de Tiled solo se comprueba que no exista otra torre en
        las mismas coordenadas; con mapa se valida ademas contra zonas
        bloqueadas, limites y otras torres (can_place_tower_at).
        """
        map_x, map_y = action["map_x"], action["map_y"]
        for tower in self.towers:
            if tower.map_x is None or tower.map_y is None:
                continue
            if abs(tower.map_x - map_x) < 1e-6 and abs(tower.map_y - map_y) < 1e-6:
                return True
        if tiled_map is not None:
            valid, _ = self.can_place_tower_at(
                map_x, map_y, action["footprint"], tiled_map
            )
            return not valid
        return False

    def sell_tower(self, tower):
        """Vende una torre colocada: la elimina y reembolsa el 50%. O(t).

        Regla de redondeo documentada: el reembolso es entero con
        division por dos hacia abajo (tower_price // 2), de modo que un
        precio impar nunca deja decimales en el saldo. La venta es
        definitiva: no puede recuperarse con Undo/Redo; si la torre
        esta referenciada por alguna accion pendiente, esa accion se
        descarta para evitar restauraciones incorrectas. Devuelve las
        estrellas reembolsadas, o 0 si la torre no estaba en el mapa.
        """
        if tower not in self.towers:
            return 0
        self.towers.remove(tower)
        refund = tower_price(tower.kind) // 2
        self.add_stars(refund)
        self._drop_actions_for(tower)
        return refund

    def _drop_actions_for(self, tower):
        """Descarta de las pilas las acciones que referencian la torre. O(n).

        Reconstruye cada pila propia (Stack) conservando el orden de las
        acciones que no corresponden a la torre vendida.
        """
        self.undo_stack = self._filter_stack(self.undo_stack, tower)
        self.redo_stack = self._filter_stack(self.redo_stack, tower)

    @staticmethod
    def _filter_stack(stack, tower):
        """Devuelve una pila nueva (Stack) sin las acciones de la torre. O(n).

        to_list() recorre del tope a la base; reapilar en ese mismo
        orden conserva la disposicion original de la pila.
        """
        kept = Stack()
        for action in stack.to_list():
            if action["tower"] is not tower:
                kept.push(action)
        return kept

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
