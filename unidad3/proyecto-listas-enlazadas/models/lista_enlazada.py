class Nodo:
    def __init__(self, datos):
        self.datos = datos
        self.estado = 'pendiente'
        self.siguiente = None

class ListaEnlazada:
    def __init__(self):
        self.cabeza = None

    def agregar_tarea(self, datos):
        nuevo_nodo = Nodo(datos)
        if not self.cabeza:
            self.cabeza = nuevo_nodo
        else:
            actual = self.cabeza
            while actual.siguiente:
                actual = actual.siguiente
            actual.siguiente = nuevo_nodo

    def marcar_completada(self, datos):
        actual = self.cabeza
        while actual:
            if actual.datos == datos:
                actual.estado = 'completada'
                return True
            actual = actual.siguiente
        return False

    def eliminar_tarea(self, datos):
        actual = self.cabeza
        previo = None
        
        while actual:
            if actual.datos == datos:
                if previo:
                    previo.siguiente = actual.siguiente
                else:
                    self.cabeza = actual.siguiente
                return True
            previo = actual
            actual = actual.siguiente
        return False

    def obtener_tareas(self):
        tareas = []
        actual = self.cabeza
        while actual:
            tareas.append({'datos': actual.datos, 'estado': actual.estado})
            actual = actual.siguiente
        return tareas