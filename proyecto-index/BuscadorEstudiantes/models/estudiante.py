"""
Modelo del sistema: almacenamiento y búsqueda de estudiantes.

Responsabilidades:
- Representar cada estudiante (ID, nombre, carrera, edad).
- Generar registros automáticamente de forma reproducible.
- Implementar la búsqueda NO indexada (secuencial).
- Construir el índice (diccionario) y la búsqueda indexada.

Este módulo no conoce la vista ni el controlador.
"""

import random


# Listas predefinidas para generar los datos de los estudiantes.
NOMBRES = [
    "Ana", "Luis", "María", "Carlos", "Sofía", "Jorge", "Lucía", "Pedro",
    "Elena", "Miguel", "Valentina", "Diego", "Camila", "Andrés", "Rosa",
    "Juan", "Paula", "Mateo", "Isabel", "Ricardo",
]

CARRERAS = [
    "Ingeniería de Sistemas", "Medicina", "Derecho", "Administración",
    "Contabilidad", "Psicología", "Ingeniería Industrial", "Arquitectura",
    "Economía", "Educación",
]


class Estudiante:
    """Representa un registro de estudiante."""

    def __init__(self, id_estudiante, nombre, carrera, edad):
        self.id = id_estudiante
        self.nombre = nombre
        self.carrera = carrera
        self.edad = edad

    def __str__(self):
        return f"ID {self.id} | {self.nombre} | {self.carrera} | {self.edad} años"


class ModeloEstudiantes:
    """Almacena los estudiantes en memoria y ofrece los dos algoritmos de búsqueda."""

    def __init__(self):
        # Lista original: única fuente de datos para AMBOS algoritmos.
        self.estudiantes = []

        # Índice auxiliar: clave = ID, valor = posición en la lista.
        self.indice = {}

        # Indica si el índice ya fue construido.
        self.indice_construido = False

    # ------------------------------------------------------------------
    # Generación de datos
    # ------------------------------------------------------------------
    def generar_estudiantes(self, cantidad, semilla=42):
        """Crea `cantidad` estudiantes con IDs únicos.

        Se usa una semilla fija para que la generación sea reproducible:
        con la misma semilla siempre se obtienen los mismos datos.
        """
        random.seed(semilla)

        self.estudiantes = []
        for i in range(cantidad):
            id_estudiante = 1001 + i  # IDs únicos e incrementales
            nombre = random.choice(NOMBRES)
            carrera = random.choice(CARRERAS)
            edad = random.randint(18, 30)
            self.estudiantes.append(Estudiante(id_estudiante, nombre, carrera, edad))

        # Al generar datos nuevos, el índice anterior deja de ser válido.
        self.indice = {}
        self.indice_construido = False

        return self.estudiantes

    # ------------------------------------------------------------------
    # Búsqueda NO indexada (secuencial) - O(n)
    # ------------------------------------------------------------------
    def buscar_no_indexada(self, id_buscar):
        """Recorre la lista de principio a fin hasta encontrar el ID.

        Devuelve: (estudiante, posición, comparaciones)
        - estudiante: None si no se encontró.
        - posición: -1 si no se encontró.
        - comparaciones: cantidad de registros examinados.
        """
        comparaciones = 0

        # Se recorre la LISTA ORIGINAL elemento por elemento.
        for posicion in range(len(self.estudiantes)):
            comparaciones += 1
            if self.estudiantes[posicion].id == id_buscar:
                return self.estudiantes[posicion], posicion, comparaciones

        # Se recorrió toda la lista sin encontrar el ID.
        return None, -1, comparaciones

    # ------------------------------------------------------------------
    # Construcción del índice - O(n)
    # ------------------------------------------------------------------
    def construir_indice(self):
        """Crea el diccionario {ID: posición} a partir de la lista original.

        Se mide aparte del tiempo de búsqueda porque construir el índice
        también cuesta tiempo y memoria.
        """
        self.indice = {}

        # Se recorre la lista una sola vez para registrar cada posición.
        for posicion in range(len(self.estudiantes)):
            estudiante = self.estudiantes[posicion]
            self.indice[estudiante.id] = posicion

        self.indice_construido = True
        return self.indice

    # ------------------------------------------------------------------
    # Búsqueda indexada - O(1) promedio
    # ------------------------------------------------------------------
    def buscar_indexada(self, id_buscar):
        """Consulta el ID en el diccionario y accede a la lista por posición.

        Devuelve: (estudiante, posición, operaciones)
        - operaciones: 1 (la consulta al diccionario/hash), o 0 si el
          índice aún no se ha construido.
        """
        # Si el índice no existe, no se puede buscar de forma indexada.
        if not self.indice_construido:
            return None, -1, 0

        # El diccionario de Python usa una tabla hash: búsqueda O(1) promedio.
        posicion = self.indice.get(id_buscar)

        if posicion is None:
            # El ID no está en el índice (no existe).
            return None, -1, 1

        # Se accede al registro original usando la posición guardada.
        return self.estudiantes[posicion], posicion, 1
