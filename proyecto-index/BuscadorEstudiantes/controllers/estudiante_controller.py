"""
Controlador del sistema: comunica el Modelo con la Vista.

Responsabilidades:
- Solicitar la generación de registros y la construcción del índice.
- Ejecutar las búsquedas (con y sin índice).
- Medir los tiempos con time.perf_counter_ns() en lotes.
- Contabilizar las comparaciones secuenciales y las operaciones indexadas.
- Ejecutar las pruebas de rendimiento y entregar los resultados a la Vista.
"""

import statistics
import time

from models.estudiante import ModeloEstudiantes


# Cantidades de registros que se prueban en el simulador.
CANTIDADES_PRUEBA = [10, 100, 500, 1000, 5000, 10000]

# Búsquedas de calentamiento previas a cada medición (no se registran).
WARMUP_BUSQUEDAS = 50

# Búsquedas consecutivas dentro de un mismo intervalo de medición.
# Reduce el impacto del costo de iniciar/detener el cronómetro.
BUSQUEDAS_POR_LOTE = 150

# Rondas de medición por escenario; se usa la mediana como resultado.
RONDAS_MEDICION = 5


class EstudianteController:
    """Intermediario entre el modelo de datos y la interfaz gráfica."""

    def __init__(self):
        self.modelo = ModeloEstudiantes()

    # ------------------------------------------------------------------
    # Operaciones básicas
    # ------------------------------------------------------------------
    def generar_estudiantes(self, cantidad, semilla=42):
        """Pide al modelo generar los registros y devuelve la cantidad creada."""
        estudiantes = self.modelo.generar_estudiantes(cantidad, semilla)
        return len(estudiantes)

    def construir_indice(self):
        """Pide al modelo construir el índice y mide su tiempo de construcción."""
        inicio = time.perf_counter_ns()
        indice = self.modelo.construir_indice()
        fin = time.perf_counter_ns()

        return {
            "cantidad_entradas": len(indice),
            # El tiempo de construcción se muestra aparte del tiempo de búsqueda.
            "tiempo_construccion_ms": (fin - inicio) / 1_000_000,
        }

    def hay_registros(self):
        return len(self.modelo.estudiantes) > 0

    def hay_indice(self):
        return self.modelo.indice_construido

    def cantidad_registros(self):
        return len(self.modelo.estudiantes)

    def obtener_estudiantes(self, limite=None):
        """Devuelve la lista de estudiantes para mostrarla en la tabla."""
        if limite is None:
            return list(self.modelo.estudiantes)
        return list(self.modelo.estudiantes[:limite])

    # ------------------------------------------------------------------
    # Búsquedas individuales (las usa la Vista)
    # ------------------------------------------------------------------
    def buscar_sin_indice(self, id_buscar):
        """Ejecuta la búsqueda secuencial y mide su tiempo."""
        inicio = time.perf_counter_ns()
        estudiante, posicion, comparaciones = self.modelo.buscar_no_indexada(id_buscar)
        fin = time.perf_counter_ns()

        return {
            "encontrado": estudiante is not None,
            "estudiante": estudiante,
            "posicion": posicion,
            "comparaciones": comparaciones,
            "tiempo_ms": (fin - inicio) / 1_000_000,
        }

    def buscar_con_indice(self, id_buscar):
        """Ejecuta la búsqueda por índice y mide su tiempo."""
        inicio = time.perf_counter_ns()
        estudiante, posicion, operaciones = self.modelo.buscar_indexada(id_buscar)
        fin = time.perf_counter_ns()

        return {
            "encontrado": estudiante is not None,
            "estudiante": estudiante,
            "posicion": posicion,
            "operaciones": operaciones,
            "tiempo_ms": (fin - inicio) / 1_000_000,
        }

    # ------------------------------------------------------------------
    # Medición de lotes (pruebas de rendimiento)
    # ------------------------------------------------------------------
    def _calentar(self, id_buscar):
        """Ejecuta búsquedas sin medir para estabilizar el sistema."""
        for _ in range(WARMUP_BUSQUEDAS):
            self.modelo.buscar_no_indexada(id_buscar)
            self.modelo.buscar_indexada(id_buscar)

    def _medir_lote_no_indexada(self, id_buscar, repeticiones):
        """Mide un lote de búsquedas secuenciales. Devuelve ns por búsqueda."""
        inicio = time.perf_counter_ns()
        for _ in range(repeticiones):
            self.modelo.buscar_no_indexada(id_buscar)
        fin = time.perf_counter_ns()
        return (fin - inicio) / repeticiones

    def _medir_lote_indexada(self, id_buscar, repeticiones):
        """Mide un lote de búsquedas indexadas. Devuelve ns por búsqueda."""
        inicio = time.perf_counter_ns()
        for _ in range(repeticiones):
            self.modelo.buscar_indexada(id_buscar)
        fin = time.perf_counter_ns()
        return (fin - inicio) / repeticiones

    def _medir_escenario(self, id_buscar):
        """Mide ambos algoritmos sobre el mismo ID con metodología estable.

        Pasos:
        1. Calentamiento (warm-up) sin registrar.
        2. Varias rondas de lotes con time.perf_counter_ns().
        3. Orden alternado entre rondas para no favorecer a un algoritmo.
        4. Mediana de las rondas como resultado representativo (ms).
        5. Comparaciones/operaciones se calculan una sola vez (son
           determinísticas para un mismo ID).
        """
        self._calentar(id_buscar)

        rondas_sin_ms = []
        rondas_con_ms = []

        for ronda in range(RONDAS_MEDICION):
            # Alternar el orden de medición entre rondas.
            if ronda % 2 == 0:
                ns_sin = self._medir_lote_no_indexada(id_buscar, BUSQUEDAS_POR_LOTE)
                ns_con = self._medir_lote_indexada(id_buscar, BUSQUEDAS_POR_LOTE)
            else:
                ns_con = self._medir_lote_indexada(id_buscar, BUSQUEDAS_POR_LOTE)
                ns_sin = self._medir_lote_no_indexada(id_buscar, BUSQUEDAS_POR_LOTE)

            rondas_sin_ms.append(ns_sin / 1_000_000)
            rondas_con_ms.append(ns_con / 1_000_000)

        mediana_sin_ms = statistics.median(rondas_sin_ms)
        mediana_con_ms = statistics.median(rondas_con_ms)

        # Conteos determinísticos: una sola ejecución basta.
        _, _, comparaciones = self.modelo.buscar_no_indexada(id_buscar)
        _, _, operaciones = self.modelo.buscar_indexada(id_buscar)

        return mediana_sin_ms, mediana_con_ms, comparaciones, operaciones

    # ------------------------------------------------------------------
    # Simulador de pruebas de rendimiento
    # ------------------------------------------------------------------
    def ejecutar_pruebas(self, progreso=None):
        """Ejecuta las pruebas automáticas con todas las cantidades de registros.

        Para cada cantidad:
        - Genera los estudiantes.
        - Construye el índice UNA sola vez (se mide su tiempo aparte).
        - Prueba 4 casos: primero, medio, final e inexistente.
        - Usa las MISMAS consultas para ambos algoritmos.
        - Mide con calentamiento, lotes, rondas y mediana.

        `progreso` es una función opcional para informar el avance a la Vista.
        """
        resultados = []
        total_pasos = len(CANTIDADES_PRUEBA) * 4
        paso = 0

        for cantidad in CANTIDADES_PRUEBA:
            # 1) Generar los registros con la misma semilla.
            self.modelo.generar_estudiantes(cantidad, semilla=42)

            # 2) Construir el índice UNA sola vez para esta cantidad.
            #    No se incluye en el tiempo de búsqueda.
            info_indice = self.construir_indice()
            tiempo_indice = info_indice["tiempo_construccion_ms"]

            # 3) Definir las 4 consultas de prueba sobre la misma lista.
            consultas = [
                ("primero", self.modelo.estudiantes[0].id),
                ("medio", self.modelo.estudiantes[cantidad // 2].id),
                ("final", self.modelo.estudiantes[-1].id),
                # ID inexistente: fuera del rango usado (1001 .. 1000+cantidad).
                ("inexistente", 1001 + cantidad + 500),
            ]

            for caso, id_consulta in consultas:
                # 4) Mismas consultas para ambos algoritmos, misma cantidad
                #    de repeticiones, datos sin modificar entre métodos.
                (tiempo_sin, tiempo_con,
                 comparaciones, operaciones) = self._medir_escenario(id_consulta)

                resultados.append({
                    "cantidad": cantidad,
                    "caso": caso,
                    "id_consulta": id_consulta,
                    "tiempo_no_indexado_ms": tiempo_sin,
                    "comparaciones": comparaciones,
                    "tiempo_indexado_ms": tiempo_con,
                    "operaciones": operaciones,
                    "tiempo_construccion_indice_ms": tiempo_indice,
                })

                paso += 1
                if progreso is not None:
                    progreso(paso, total_pasos, cantidad, caso)

        return resultados
