#fixed: code
class Stack:
    def __init__(self):
        self.items = []

    def is_empty(self):
        # pregunta si la pila está vacía
        return len(self.items) == 0

    def push(self, item):
        # con append el usuario ya puede agregar elementos a la pila
        self.items.append(item)

    def pop(self):
        # se verifica si la pila no está vacía antes de intentar sacar un elemento
        if not self.is_empty():
            return self.items.pop()
        return None

# --- Prueba del Alumno ---
mi_pila = Stack()
mi_pila.push("A")
mi_pila.push("B")

print("¿Está vacía?", mi_pila.is_empty())
print("Elemento sacado:", mi_pila.pop())

