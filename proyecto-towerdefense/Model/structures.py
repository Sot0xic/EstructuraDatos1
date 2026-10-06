"""
Estructuras de datos implementadas manualmente para el Tower Defense.

Semana 1 - Implementacion de estructuras de datos y modelo base.

Estructuras incluidas:
    - Node: nodo base para las estructuras enlazadas.
    - DoublyLinkedList: enemigos activos dentro del mapa.
    - Queue: enemigos esperando para aparecer en el mapa (FIFO).
    - Stack: historial de acciones, base para Undo/Redo (LIFO).

Cada operacion documenta su complejidad temporal en el docstring.
El analisis completo se encuentra en docs/COMPLEJIDAD.md.
"""


class Node:
    """Nodo base para las estructuras enlazadas del juego.

    Atributos:
        data: dato almacenado (por ejemplo, un objeto Enemy).
        prev: referencia al nodo anterior (None si no aplica).
        next: referencia al nodo siguiente (None si no aplica).
    """

    def __init__(self, data):
        self.data = data
        self.prev = None
        self.next = None

    def __repr__(self):
        return f"Node({self.data!r})"


class DoublyLinkedList:
    """Lista doblemente enlazada con referencias head y tail.

    Uso en el juego: mantiene los enemigos que estan activos en el mapa.
    Permite eliminar un enemigo en cualquier posicion reenlazando solo
    los nodos vecinos, sin desplazar el resto de los elementos.

    Invariante:
        - Si la lista no esta vacia, head.prev es None y tail.next es None.
        - Los enlaces next/prev son consistentes entre nodos vecinos.
        - len(lista) coincide con el numero de nodos recorridos.
    """

    def __init__(self):
        self.head = None
        self.tail = None
        self._size = 0

    def __len__(self):
        """Numero de elementos. Complejidad: O(1)."""
        return self._size

    def __contains__(self, data):
        """Busqueda por valor. Complejidad: O(n)."""
        return self.search(data) is not None

    def __iter__(self):
        """Recorrido de inicio a fin. Complejidad: O(n) sobre todo el recorrido."""
        current = self.head
        while current is not None:
            yield current.data
            current = current.next

    def is_empty(self):
        """Comprueba si la lista esta vacia. Complejidad: O(1)."""
        return self._size == 0

    def insert_first(self, data):
        """Inserta un elemento al inicio de la lista. Complejidad: O(1).

        Casos: lista vacia y lista con elementos.
        """
        new_node = Node(data)
        if self.is_empty():
            self.head = new_node
            self.tail = new_node
        else:
            new_node.next = self.head
            self.head.prev = new_node
            self.head = new_node
        self._size += 1
        return new_node

    def insert_last(self, data):
        """Inserta un elemento al final de la lista. Complejidad: O(1).

        Requiere mantener la referencia tail. Casos: lista vacia y con elementos.
        """
        new_node = Node(data)
        if self.is_empty():
            self.head = new_node
            self.tail = new_node
        else:
            new_node.prev = self.tail
            self.tail.next = new_node
            self.tail = new_node
        self._size += 1
        return new_node

    def search(self, data):
        """Busca un elemento por valor y devuelve su nodo o None. Complejidad: O(n)."""
        current = self.head
        while current is not None:
            if current.data == data:
                return current
            current = current.next
        return None

    def remove(self, data):
        """Elimina la primera aparicion de un elemento. Complejidad: O(n).

        O(n) porque primero hay que encontrar el nodo; la reconfiguracion
        de enlaces de los vecinos es O(1).

        Casos cubiertos:
            - Lista vacia.
            - Un solo nodo.
            - Eliminacion del primer nodo.
            - Eliminacion del ultimo nodo.
            - Eliminacion de un nodo intermedio.
            - Elemento inexistente.
        """
        node = self.search(data)
        if node is None:
            return False
        self.remove_node(node)
        return True

    def remove_node(self, node):
        """Elimina un nodo ya identificado. Complejidad: O(1).

        Operacion usada por las torres cuando ya tienen referencia
        al enemigo (nodo) que eliminaron.
        """
        if node is None:
            return False

        if node.prev is not None:
            node.prev.next = node.next
        else:
            self.head = node.next

        if node.next is not None:
            node.next.prev = node.prev
        else:
            self.tail = node.prev

        node.prev = None
        node.next = None
        self._size -= 1
        return True

    def traverse(self, forward=True):
        """Recorre la lista y genera sus elementos. Complejidad: O(n).

        forward=True recorre de inicio a fin; forward=False de fin a inicio.
        """
        if forward:
            current = self.head
            while current is not None:
                yield current.data
                current = current.next
        else:
            current = self.tail
            while current is not None:
                yield current.data
                current = current.prev

    def to_list(self):
        """Devuelve la lista como un arreglo de Python (para impresion). O(n)."""
        return list(self.traverse(forward=True))

    def clear(self):
        """Vacia la lista. Complejidad: O(1) (se descartan las referencias)."""
        self.head = None
        self.tail = None
        self._size = 0

    def __repr__(self):
        content = " <-> ".join(repr(item) for item in self.traverse())
        return f"DoublyLinkedList([{content}])"


class Queue:
    """Cola FIFO implementada con nodos (head y tail).

    Uso en el juego: mantiene los enemigos que esperan para aparecer
    en el mapa, respetando el orden de la oleada.

    Ejemplo:
        enqueue(1), enqueue(2), enqueue(3)
        dequeue() -> 1   (FIFO: primero entra, primero sale)
    """

    def __init__(self):
        self._head = None
        self._tail = None
        self._size = 0

    def __len__(self):
        """Numero de elementos. Complejidad: O(1)."""
        return self._size

    def is_empty(self):
        """Comprueba si la cola esta vacia. Complejidad: O(1)."""
        return self._size == 0

    def enqueue(self, data):
        """Agrega un elemento al final de la cola. Complejidad: O(1)."""
        new_node = Node(data)
        if self.is_empty():
            self._head = new_node
            self._tail = new_node
        else:
            self._tail.next = new_node
            self._tail = new_node
        self._size += 1
        return new_node

    def dequeue(self):
        """Retira y devuelve el primer elemento. Complejidad: O(1).

        Devuelve None si la cola esta vacia.
        """
        if self.is_empty():
            return None
        data = self._head.data
        self._head = self._head.next
        if self._head is None:
            self._tail = None
        self._size -= 1
        return data

    def peek(self):
        """Consulta el primer elemento sin retirarlo. Complejidad: O(1).

        Devuelve None si la cola esta vacia.
        """
        if self.is_empty():
            return None
        return self._head.data

    def to_list(self):
        """Devuelve los elementos en orden FIFO (para impresion). O(n)."""
        elements = []
        current = self._head
        while current is not None:
            elements.append(current.data)
            current = current.next
        return elements

    def clear(self):
        """Vacia la cola. Complejidad: O(1)."""
        self._head = None
        self._tail = None
        self._size = 0

    def __repr__(self):
        content = " -> ".join(repr(item) for item in self.to_list())
        return f"Queue([{content}])"


class Stack:
    """Pila LIFO implementada con nodos.

    Uso en el juego: base del historial de acciones para un posible
    sistema de Undo/Redo. La ultima accion almacenada es la primera
    en recuperarse.

    Ejemplo:
        push(Accion 1), push(Accion 2), push(Accion 3)
        pop() -> Accion 3   (LIFO: ultimo entra, primero sale)
    """

    def __init__(self):
        self._top = None
        self._size = 0

    def __len__(self):
        """Numero de elementos. Complejidad: O(1)."""
        return self._size

    def is_empty(self):
        """Comprueba si la pila esta vacia. Complejidad: O(1)."""
        return self._size == 0

    def push(self, data):
        """Agrega una accion al tope de la pila. Complejidad: O(1)."""
        new_node = Node(data)
        new_node.next = self._top
        self._top = new_node
        self._size += 1
        return new_node

    def pop(self):
        """Retira y devuelve la ultima accion agregada. Complejidad: O(1).

        Devuelve None si la pila esta vacia.
        """
        if self.is_empty():
            return None
        data = self._top.data
        self._top = self._top.next
        self._size -= 1
        return data

    def peek(self):
        """Consulta la ultima accion sin retirarla. Complejidad: O(1).

        Devuelve None si la pila esta vacia.
        """
        if self.is_empty():
            return None
        return self._top.data

    def to_list(self):
        """Devuelve los elementos desde el tope hasta la base (para impresion). O(n)."""
        elements = []
        current = self._top
        while current is not None:
            elements.append(current.data)
            current = current.next
        return elements

    def clear(self):
        """Vacia la pila. Complejidad: O(1)."""
        self._top = None
        self._size = 0

    def __repr__(self):
        content = ", ".join(repr(item) for item in self.to_list())
        return f"Stack([{content}])"
