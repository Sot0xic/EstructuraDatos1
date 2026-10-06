"""
Pruebas de las estructuras de datos (Dia 5 - Semana 1).

Cobertura:
    - Inserciones (inicio/final, enqueue, push).
    - Eliminaciones (primero, ultimo, intermedio, unico elemento, vacia).
    - Busquedas y recorridos.
    - Orden FIFO de la cola.
    - Orden LIFO de la pila.
    - Integridad de las referencias prev/next.

Ejecutar desde la raiz del proyecto:

    python -m unittest discover -s tests -v
"""

import unittest

from Model.structures import DoublyLinkedList, Queue, Stack


class TestDoublyLinkedList(unittest.TestCase):
    """Pruebas de la lista doblemente enlazada."""

    def test_empty_list(self):
        lista = DoublyLinkedList()
        self.assertTrue(lista.is_empty())
        self.assertEqual(len(lista), 0)
        self.assertIsNone(lista.head)
        self.assertIsNone(lista.tail)
        self.assertIsNone(lista.search(1))
        self.assertFalse(lista.remove(1))

    def test_insert_first(self):
        lista = DoublyLinkedList()
        lista.insert_first(2)
        lista.insert_first(1)
        self.assertEqual(lista.to_list(), [1, 2])
        self.assertEqual(len(lista), 2)

    def test_insert_last(self):
        lista = DoublyLinkedList()
        lista.insert_last(1)
        lista.insert_last(2)
        lista.insert_last(3)
        self.assertEqual(lista.to_list(), [1, 2, 3])
        self.assertEqual(lista.tail.data, 3)

    def test_references_prev_next(self):
        lista = DoublyLinkedList()
        n1 = lista.insert_last(1)
        n2 = lista.insert_last(2)
        n3 = lista.insert_last(3)

        self.assertIsNone(n1.prev)
        self.assertIsNone(n3.next)
        self.assertIs(n1.next, n2)
        self.assertIs(n2.prev, n1)
        self.assertIs(n2.next, n3)
        self.assertIs(n3.prev, n2)
        self.assertIs(lista.head, n1)
        self.assertIs(lista.tail, n3)

    def test_search(self):
        lista = DoublyLinkedList()
        for value in (1, 2, 3):
            lista.insert_last(value)
        self.assertEqual(lista.search(2).data, 2)
        self.assertIsNone(lista.search(99))
        self.assertIn(3, lista)
        self.assertNotIn(99, lista)

    def test_remove_single_element(self):
        lista = DoublyLinkedList()
        lista.insert_last(1)
        self.assertTrue(lista.remove(1))
        self.assertTrue(lista.is_empty())
        self.assertIsNone(lista.head)
        self.assertIsNone(lista.tail)
        self.assertEqual(len(lista), 0)

    def test_remove_first_node(self):
        lista = DoublyLinkedList()
        for value in (1, 2, 3):
            lista.insert_last(value)
        self.assertTrue(lista.remove(1))
        self.assertEqual(lista.to_list(), [2, 3])
        self.assertIsNone(lista.head.prev)
        self.assertEqual(len(lista), 2)

    def test_remove_last_node(self):
        lista = DoublyLinkedList()
        for value in (1, 2, 3):
            lista.insert_last(value)
        self.assertTrue(lista.remove(3))
        self.assertEqual(lista.to_list(), [1, 2])
        self.assertIsNone(lista.tail.next)
        self.assertEqual(len(lista), 2)

    def test_remove_middle_node(self):
        lista = DoublyLinkedList()
        for value in (1, 2, 3):
            lista.insert_last(value)
        self.assertTrue(lista.remove(2))
        self.assertEqual(lista.to_list(), [1, 3])
        self.assertIsNone(lista.search(2))
        self.assertIs(lista.head.next, lista.tail)
        self.assertIs(lista.tail.prev, lista.head)
        self.assertEqual(len(lista), 2)

    def test_remove_nonexistent_element(self):
        lista = DoublyLinkedList()
        for value in (1, 2, 3):
            lista.insert_last(value)
        self.assertFalse(lista.remove(99))
        self.assertEqual(lista.to_list(), [1, 2, 3])
        self.assertEqual(len(lista), 3)

    def test_remove_all_elements(self):
        lista = DoublyLinkedList()
        for value in (1, 2, 3, 4):
            lista.insert_last(value)
        for value in (1, 2, 3, 4):
            self.assertTrue(lista.remove(value))
            self.assertEqual(len(lista), 4 - [1, 2, 3, 4].index(value) - 1)
        self.assertTrue(lista.is_empty())
        self.assertIsNone(lista.head)
        self.assertIsNone(lista.tail)

    def test_traverse_forward_and_backward(self):
        lista = DoublyLinkedList()
        for value in (1, 2, 3):
            lista.insert_last(value)
        self.assertEqual(list(lista.traverse(forward=True)), [1, 2, 3])
        self.assertEqual(list(lista.traverse(forward=False)), [3, 2, 1])
        self.assertEqual(list(lista), [1, 2, 3])

    def test_clear(self):
        lista = DoublyLinkedList()
        for value in (1, 2):
            lista.insert_last(value)
        lista.clear()
        self.assertTrue(lista.is_empty())
        self.assertEqual(len(lista), 0)


class TestQueue(unittest.TestCase):
    """Pruebas de la cola FIFO de enemigos en espera."""

    def test_empty_queue(self):
        cola = Queue()
        self.assertTrue(cola.is_empty())
        self.assertEqual(len(cola), 0)
        self.assertIsNone(cola.dequeue())
        self.assertIsNone(cola.peek())

    def test_fifo_order(self):
        cola = Queue()
        cola.enqueue("Enemy 1")
        cola.enqueue("Enemy 2")
        cola.enqueue("Enemy 3")
        cola.enqueue("Enemy 4")

        self.assertEqual(cola.peek(), "Enemy 1")
        self.assertEqual(cola.dequeue(), "Enemy 1")
        self.assertEqual(cola.dequeue(), "Enemy 2")
        self.assertEqual(cola.dequeue(), "Enemy 3")
        self.assertEqual(cola.dequeue(), "Enemy 4")
        self.assertTrue(cola.is_empty())

    def test_peek_does_not_remove(self):
        cola = Queue()
        cola.enqueue("Enemy 1")
        self.assertEqual(cola.peek(), "Enemy 1")
        self.assertEqual(len(cola), 1)
        self.assertEqual(cola.peek(), "Enemy 1")

    def test_dequeue_single_element(self):
        cola = Queue()
        cola.enqueue("Enemy 1")
        self.assertEqual(cola.dequeue(), "Enemy 1")
        self.assertTrue(cola.is_empty())
        self.assertIsNone(cola.dequeue())

    def test_interleaved_enqueue_dequeue(self):
        cola = Queue()
        cola.enqueue("A")
        cola.enqueue("B")
        self.assertEqual(cola.dequeue(), "A")
        cola.enqueue("C")
        self.assertEqual(cola.dequeue(), "B")
        self.assertEqual(cola.dequeue(), "C")
        self.assertTrue(cola.is_empty())

    def test_to_list_and_clear(self):
        cola = Queue()
        for name in ("A", "B", "C"):
            cola.enqueue(name)
        self.assertEqual(cola.to_list(), ["A", "B", "C"])
        cola.clear()
        self.assertTrue(cola.is_empty())
        self.assertEqual(cola.to_list(), [])


class TestStack(unittest.TestCase):
    """Pruebas de la pila LIFO del historial de acciones."""

    def test_empty_stack(self):
        pila = Stack()
        self.assertTrue(pila.is_empty())
        self.assertEqual(len(pila), 0)
        self.assertIsNone(pila.pop())
        self.assertIsNone(pila.peek())

    def test_lifo_order(self):
        pila = Stack()
        pila.push("Accion 1")
        pila.push("Accion 2")
        pila.push("Accion 3")

        self.assertEqual(pila.peek(), "Accion 3")
        self.assertEqual(pila.pop(), "Accion 3")
        self.assertEqual(pila.pop(), "Accion 2")
        self.assertEqual(pila.pop(), "Accion 1")
        self.assertTrue(pila.is_empty())

    def test_peek_does_not_remove(self):
        pila = Stack()
        pila.push("Accion 1")
        self.assertEqual(pila.peek(), "Accion 1")
        self.assertEqual(len(pila), 1)
        self.assertEqual(pila.peek(), "Accion 1")

    def test_pop_single_element(self):
        pila = Stack()
        pila.push("Accion 1")
        self.assertEqual(pila.pop(), "Accion 1")
        self.assertTrue(pila.is_empty())
        self.assertIsNone(pila.pop())

    def test_interleaved_push_pop(self):
        pila = Stack()
        pila.push("A")
        pila.push("B")
        self.assertEqual(pila.pop(), "B")
        pila.push("C")
        self.assertEqual(pila.pop(), "C")
        self.assertEqual(pila.pop(), "A")
        self.assertTrue(pila.is_empty())

    def test_to_list_and_clear(self):
        pila = Stack()
        for action in ("Accion 1", "Accion 2", "Accion 3"):
            pila.push(action)
        self.assertEqual(pila.to_list(), ["Accion 3", "Accion 2", "Accion 1"])
        pila.clear()
        self.assertTrue(pila.is_empty())
        self.assertEqual(pila.to_list(), [])


if __name__ == "__main__":
    unittest.main()
