#fixed: code
class Nodo:
    def __init__(self, valor):
        self.valor = valor
        self.siguiente = None # Este es nuestro 'puntero' al siguiente espacio en el Heap

# --- Prueba del Alumno ---
# El estudiante intenta crear una cadena: [Nodo 1] -> [Nodo 2]

contenedor = Nodo("Datos Importantes 1")

segundo = Nodo("Datos Importantes 2")

contenedor.siguiente = segundo  # para que el primer nodo apunte al segundo, se debe asignar el segundo nodo a la propiedad 'siguiente' del primer nodo

# Verificación
print(f"Contenido actual: {contenedor.valor}") #mostrará el valor del nodo 1
print(f"Contenido siguiente: {contenedor.siguiente.valor}") #mostrará el valor del siguiente nodo
if contenedor.siguiente is None:
    print("ERROR: Se ha perdido la referencia al primer nodo. ¡Memory Leak conceptual!")

