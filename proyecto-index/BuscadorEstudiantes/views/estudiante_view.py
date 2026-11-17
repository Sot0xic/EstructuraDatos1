"""
Vista del sistema: interfaz gráfica construida con Tkinter.

Solo muestra datos y captura las acciones del usuario.
Toda la lógica de búsqueda, medición y pruebas vive en el Controlador.
"""

import math
import tkinter as tk
from tkinter import ttk, messagebox


# Cantidades disponibles para generar registros.
CANTIDADES = ["10", "100", "500", "1000", "5000", "10000"]

# Escenarios de búsqueda que se prueban en el simulador.
ESCENARIOS = ["primero", "medio", "final", "inexistente"]

# Límite de filas que se cargan en la tabla de estudiantes (para no
# ralentizar la interfaz con 10.000 registros).
MAX_FILAS_TABLA = 500


class EstudianteView:
    """Ventana principal de la aplicación."""

    def __init__(self, root, controlador):
        self.root = root
        self.controlador = controlador
        self._resultados_pruebas = []

        self.root.title("Comparador de Búsquedas Indexadas y No Indexadas")
        self.root.geometry("1080x720")

        self._crear_widgets()
        self._actualizar_estado()

    # ------------------------------------------------------------------
    # Construcción de la interfaz
    # ------------------------------------------------------------------
    def _crear_widgets(self):
        # Barra de estado inferior.
        self.lbl_estado = ttk.Label(self.root, anchor="w", relief="sunken")
        self.lbl_estado.pack(side="bottom", fill="x")

        # Pestañas: una para buscar, otra para las pruebas de rendimiento.
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=8, pady=8)

        self.pestana_busqueda = ttk.Frame(notebook)
        self.pestana_pruebas = ttk.Frame(notebook)
        notebook.add(self.pestana_busqueda, text=" Búsqueda ")
        notebook.add(self.pestana_pruebas, text=" Pruebas de rendimiento ")

        # El gráfico solo puede dibujarse cuando su pestaña está visible.
        notebook.bind("<<NotebookTabChanged>>", self._al_cambiar_pestana)

        self._crear_pestana_busqueda()
        self._crear_pestana_pruebas()

    def _crear_pestana_busqueda(self):
        marco = self.pestana_busqueda

        # --- 1) Generación de registros e índice ---
        frame_generacion = ttk.LabelFrame(marco, text="1. Datos e índice")
        frame_generacion.pack(fill="x", padx=6, pady=(6, 4))

        ttk.Label(frame_generacion, text="Cantidad de estudiantes:").pack(
            side="left", padx=(8, 4), pady=8
        )

        self.combo_cantidad = ttk.Combobox(
            frame_generacion, values=CANTIDADES, width=8, state="readonly"
        )
        self.combo_cantidad.set("1000")
        self.combo_cantidad.pack(side="left", pady=8)

        ttk.Button(
            frame_generacion, text="Generar registros", command=self._generar_registros
        ).pack(side="left", padx=8, pady=8)

        ttk.Button(
            frame_generacion, text="Construir índice", command=self._construir_indice
        ).pack(side="left", pady=8)

        self.lbl_indice = ttk.Label(frame_generacion, text="Índice: no construido")
        self.lbl_indice.pack(side="left", padx=16, pady=8)

        # --- 2) Búsqueda ---
        frame_busqueda = ttk.LabelFrame(marco, text="2. Búsqueda por ID")
        frame_busqueda.pack(fill="x", padx=6, pady=4)

        ttk.Label(frame_busqueda, text="ID del estudiante:").pack(
            side="left", padx=(8, 4), pady=8
        )

        self.entry_id = ttk.Entry(frame_busqueda, width=12)
        self.entry_id.pack(side="left", pady=8)
        self.entry_id.bind("<Return>", lambda evento: self._buscar_sin_indice())

        ttk.Button(
            frame_busqueda, text="Buscar SIN índice", command=self._buscar_sin_indice
        ).pack(side="left", padx=8, pady=8)

        ttk.Button(
            frame_busqueda, text="Buscar CON índice", command=self._buscar_con_indice
        ).pack(side="left", pady=8)

        # --- Comparación visual de los tiempos (ancho completo) ---
        # Fuera de frame_contenido para disponer de todo el ancho disponible
        # y que los valores nunca queden cortados.
        frame_comparacion = ttk.LabelFrame(
            marco, text="Comparación de tiempos (ms)"
        )
        frame_comparacion.pack(fill="x", padx=6, pady=4)

        self.canvas_comparacion = tk.Canvas(
            frame_comparacion, height=110, background="white",
            highlightthickness=0,
        )
        self.canvas_comparacion.pack(fill="x", padx=4, pady=4)
        # Se redibuja al cambiar el tamaño para adaptarse a la ventana.
        self.canvas_comparacion.bind(
            "<Configure>", lambda evento: self._redibujar_comparacion_si_hay_datos()
        )

        # --- 3) Contenido: tabla de estudiantes + resultados ---
        frame_contenido = ttk.Frame(marco)
        frame_contenido.pack(fill="both", expand=True, padx=6, pady=(4, 6))

        # Tabla con los registros.
        frame_tabla = ttk.LabelFrame(frame_contenido, text="Estudiantes")
        frame_tabla.pack(side="left", fill="both", expand=True, padx=(0, 4))

        columnas = ("id", "nombre", "carrera", "edad")
        self.tabla_estudiantes = ttk.Treeview(
            frame_tabla, columns=columnas, show="headings", height=14
        )
        self.tabla_estudiantes.heading("id", text="ID")
        self.tabla_estudiantes.heading("nombre", text="Nombre")
        self.tabla_estudiantes.heading("carrera", text="Carrera")
        self.tabla_estudiantes.heading("edad", text="Edad")
        self.tabla_estudiantes.column("id", width=70, anchor="center")
        self.tabla_estudiantes.column("nombre", width=110)
        self.tabla_estudiantes.column("carrera", width=190)
        self.tabla_estudiantes.column("edad", width=55, anchor="center")

        scroll_tabla = ttk.Scrollbar(
            frame_tabla, orient="vertical", command=self.tabla_estudiantes.yview
        )
        self.tabla_estudiantes.configure(yscrollcommand=scroll_tabla.set)
        self.tabla_estudiantes.pack(side="left", fill="both", expand=True)
        scroll_tabla.pack(side="right", fill="y")

        self.lbl_tabla = ttk.Label(frame_tabla, text="", anchor="w")
        self.lbl_tabla.pack(side="bottom", fill="x", padx=4, pady=2)

        # Resultados de la última búsqueda.
        frame_resultados = ttk.LabelFrame(frame_contenido, text="Resultados")
        frame_resultados.pack(side="right", fill="both", padx=(4, 0), ipadx=4)

        self.area_resultados = tk.Text(
            frame_resultados, width=46, height=16, wrap="word", state="disabled"
        )
        self.area_resultados.pack(fill="both", expand=True, padx=4, pady=4)

    def _crear_pestana_pruebas(self):
        marco = self.pestana_pruebas

        # --- Control de las pruebas ---
        frame_control = ttk.Frame(marco)
        frame_control.pack(fill="x", padx=6, pady=(6, 4))

        ttk.Button(
            frame_control, text="Ejecutar pruebas de rendimiento",
            command=self._ejecutar_pruebas,
        ).pack(side="left", padx=(0, 10), pady=6)

        self.barra_progreso = ttk.Progressbar(
            frame_control, orient="horizontal", length=320, mode="determinate"
        )
        self.barra_progreso.pack(side="left", pady=6)

        self.lbl_progreso = ttk.Label(frame_control, text="Listo")
        self.lbl_progreso.pack(side="left", padx=10, pady=6)

        # --- Tabla comparativa ---
        frame_tabla_pruebas = ttk.LabelFrame(marco, text="Tabla comparativa")
        frame_tabla_pruebas.pack(fill="x", padx=6, pady=4)

        columnas = ("registros", "caso", "no_indexado", "indexado",
                    "comparaciones", "operaciones", "construccion")
        self.tabla_pruebas = ttk.Treeview(
            frame_tabla_pruebas, columns=columnas, show="headings", height=8
        )
        self.tabla_pruebas.heading("registros", text="Cantidad de estudiantes")
        self.tabla_pruebas.heading("caso", text="Escenario de búsqueda")
        self.tabla_pruebas.heading("no_indexado", text="Tiempo sin índice (ms)")
        self.tabla_pruebas.heading("indexado", text="Tiempo con índice (ms)")
        self.tabla_pruebas.heading("comparaciones", text="Comparaciones secuenciales")
        self.tabla_pruebas.heading("operaciones", text="Operaciones indexadas")
        self.tabla_pruebas.heading("construccion", text="Construcción índice (ms)")
        self.tabla_pruebas.column("registros", width=110, anchor="center")
        self.tabla_pruebas.column("caso", width=110, anchor="center")
        self.tabla_pruebas.column("no_indexado", width=130, anchor="e")
        self.tabla_pruebas.column("indexado", width=130, anchor="e")
        self.tabla_pruebas.column("comparaciones", width=130, anchor="center")
        self.tabla_pruebas.column("operaciones", width=120, anchor="center")
        self.tabla_pruebas.column("construccion", width=140, anchor="e")

        scroll_pruebas = ttk.Scrollbar(
            frame_tabla_pruebas, orient="vertical",
            command=self.tabla_pruebas.yview,
        )
        self.tabla_pruebas.configure(yscrollcommand=scroll_pruebas.set)
        self.tabla_pruebas.pack(side="left", fill="x", expand=True)
        scroll_pruebas.pack(side="right", fill="y")

        # --- Selector de escenario + Gráfico ---
        frame_grafico = ttk.LabelFrame(
            marco, text="Gráfico: tiempo de búsqueda por cantidad de registros"
        )
        frame_grafico.pack(fill="both", expand=True, padx=6, pady=(4, 4))

        frame_selector = ttk.Frame(frame_grafico)
        frame_selector.pack(fill="x", padx=4, pady=(4, 0))

        ttk.Label(frame_selector, text="Escenario:").pack(side="left", padx=(0, 4))
        self.combo_escenario = ttk.Combobox(
            frame_selector, values=ESCENARIOS, width=14, state="readonly"
        )
        self.combo_escenario.set("primero")
        self.combo_escenario.pack(side="left")
        self.combo_escenario.bind(
            "<<ComboboxSelected>>", lambda evento: self._dibujar_grafico()
        )

        ttk.Label(
            frame_selector,
            text="Escala vertical logarítmica (ms) — barras muy pequeñas son visibles",
        ).pack(side="left", padx=12)

        self.canvas_grafico = tk.Canvas(
            frame_grafico, background="white", height=240
        )
        self.canvas_grafico.pack(fill="both", expand=True, padx=4, pady=4)
        # Se redibuja cuando el canvas cambia de tamaño.
        self.canvas_grafico.bind("<Configure>", lambda e: self._dibujar_grafico())

        # --- Conclusión automática ---
        frame_conclusion = ttk.LabelFrame(marco, text="Conclusión automática (resultados reales)")
        frame_conclusion.pack(fill="x", padx=6, pady=(0, 6))

        self.area_conclusion = tk.Text(
            frame_conclusion, height=5, wrap="word", state="disabled"
        )
        self.area_conclusion.pack(fill="x", padx=4, pady=4)

    # ------------------------------------------------------------------
    # Acciones de la pestaña de búsqueda
    # ------------------------------------------------------------------
    def _al_cambiar_pestana(self, evento):
        """Redibuja el gráfico cuando se abre la pestaña de pruebas."""
        # evento.widget es el Notebook; select() devuelve la pestaña activa.
        if evento.widget.select() == str(self.pestana_pruebas):
            self.canvas_grafico.after(50, self._dibujar_grafico)

    def _generar_registros(self):
        cantidad = int(self.combo_cantidad.get())
        creados = self.controlador.generar_estudiantes(cantidad)
        self._actualizar_tabla_estudiantes()
        self._actualizar_estado(
            f"Generados {creados} registros. El índice anterior quedó obsoleto."
        )
        self.lbl_indice.config(text="Índice: no construido")
        self._limpiar_resultados()

    def _construir_indice(self):
        if not self.controlador.hay_registros():
            messagebox.showwarning("Aviso", "Primero genera los registros.")
            return

        info = self.controlador.construir_indice()
        self.lbl_indice.config(
            text=f"Índice: {info['cantidad_entradas']} entradas "
                 f"({info['tiempo_construccion_ms']:.4f} ms)"
        )
        self._actualizar_estado(
            f"Índice construido con {info['cantidad_entradas']} entradas."
        )

    def _leer_id(self):
        """Lee el ID escrito por el usuario. Devuelve None si no es válido."""
        texto = self.entry_id.get().strip()
        if not texto.isdigit():
            messagebox.showerror("Error", "Escribe un ID numérico, por ejemplo 1001.")
            return None
        return int(texto)

    def _buscar_sin_indice(self):
        if not self.controlador.hay_registros():
            messagebox.showwarning("Aviso", "Primero genera los registros.")
            return

        id_buscar = self._leer_id()
        if id_buscar is None:
            return

        resultado = self.controlador.buscar_sin_indice(id_buscar)
        self._mostrar_resultado(resultado, "Búsqueda SIN índice (secuencial)")
        # Se compara con el último tiempo indexado si ya existe.
        self._dibujar_comparacion(
            resultado["tiempo_ms"], getattr(self, "_ultimo_tiempo_indexado", None)
        )

    def _buscar_con_indice(self):
        if not self.controlador.hay_registros():
            messagebox.showwarning("Aviso", "Primero genera los registros.")
            return

        if not self.controlador.hay_indice():
            messagebox.showwarning(
                "Aviso", "Primero construye el índice con el botón correspondiente."
            )
            return

        id_buscar = self._leer_id()
        if id_buscar is None:
            return

        resultado = self.controlador.buscar_con_indice(id_buscar)
        self._mostrar_resultado(resultado, "Búsqueda CON índice (diccionario)")
        self._ultimo_tiempo_indexado = resultado["tiempo_ms"]
        self._dibujar_comparacion(getattr(self, "_ultimo_tiempo_sin_indice", None),
                                  resultado["tiempo_ms"])

    def _mostrar_resultado(self, resultado, titulo):
        if "comparaciones" in resultado:
            self._ultimo_tiempo_sin_indice = resultado["tiempo_ms"]
        else:
            self._ultimo_tiempo_indexado = resultado["tiempo_ms"]

        lineas = [titulo, "=" * len(titulo)]

        if resultado["encontrado"]:
            estudiante = resultado["estudiante"]
            lineas.append("Resultado: ENCONTRADO")
            lineas.append(f"Datos: {estudiante}")
            lineas.append(f"Posición en la lista: {resultado['posicion']}")
        else:
            lineas.append("Resultado: NO ENCONTRADO")

        if "comparaciones" in resultado:
            lineas.append(
                f"Registros examinados (comparaciones): {resultado['comparaciones']}"
            )
        else:
            lineas.append(
                f"Operaciones sobre el índice: {resultado['operaciones']}"
            )

        lineas.append(f"Tiempo de ejecución: {resultado['tiempo_ms']:.6f} ms")

        self.area_resultados.config(state="normal")
        self.area_resultados.delete("1.0", "end")
        self.area_resultados.insert("1.0", "\n".join(lineas))
        self.area_resultados.config(state="disabled")

        self._actualizar_estado(f"{titulo} completada.")

    def _limpiar_resultados(self):
        self.area_resultados.config(state="normal")
        self.area_resultados.delete("1.0", "end")
        self.area_resultados.config(state="disabled")
        self.canvas_comparacion.delete("all")
        self._ultimo_tiempo_sin_indice = None
        self._ultimo_tiempo_indexado = None

    # ------------------------------------------------------------------
    # Tablas
    # ------------------------------------------------------------------
    def _actualizar_tabla_estudiantes(self):
        self.tabla_estudiantes.delete(*self.tabla_estudiantes.get_children())

        estudiantes = self.controlador.obtener_estudiantes(MAX_FILAS_TABLA)
        for estudiante in estudiantes:
            self.tabla_estudiantes.insert(
                "", "end",
                values=(estudiante.id, estudiante.nombre,
                        estudiante.carrera, estudiante.edad),
            )

        total = self.controlador.cantidad_registros()
        if total > MAX_FILAS_TABLA:
            self.lbl_tabla.config(
                text=f"Mostrando los primeros {MAX_FILAS_TABLA} de {total} registros."
            )
        else:
            self.lbl_tabla.config(text=f"{total} registros.")

    # ------------------------------------------------------------------
    # Comparación visual de tiempos
    # ------------------------------------------------------------------
    def _redibujar_comparacion_si_hay_datos(self):
        """Vuelve a dibujar la comparación tras redimensionar (si hay datos)."""
        tiempo_sin = getattr(self, "_ultimo_tiempo_sin_indice", None)
        tiempo_con = getattr(self, "_ultimo_tiempo_indexado", None)
        if tiempo_sin is None and tiempo_con is None:
            return
        self._dibujar_comparacion(tiempo_sin, tiempo_con)

    def _dibujar_comparacion(self, tiempo_sin, tiempo_con):
        """Dibuja dos barras horizontales con los valores siempre visibles.

        Los valores numéricos se colocan en una columna fija a la derecha,
        por lo que nunca quedan ocultos aunque una barra sea muy larga.
        """
        canvas = self.canvas_comparacion
        canvas.delete("all")

        if tiempo_sin is None and tiempo_con is None:
            return

        maximo = max(tiempo_sin or 0, tiempo_con or 0)
        if maximo == 0:
            maximo = 1

        ancho = canvas.winfo_width()
        alto = canvas.winfo_height()
        if ancho < 80 or alto < 40:
            return

        # Columna fija a la derecha para los valores (garantiza visibilidad).
        ancho_valores = 115
        margen_izq = 10
        x_valor = ancho - ancho_valores
        # Ancho máximo de barra disponible antes de la columna de valores.
        ancho_barra_max = max(30, x_valor - margen_izq - 8)

        datos = [
            ("Sin índice", tiempo_sin, "#e74c3c"),
            ("Con índice", tiempo_con, "#27ae60"),
        ]

        # Distribución vertical: etiqueta arriba, barra y valor debajo.
        alto_bloque = max(48, (alto - 12) // 2)
        y = 8

        for etiqueta, tiempo, color in datos:
            # Etiqueta sobre la barra.
            canvas.create_text(
                margen_izq, y, anchor="nw", text=etiqueta, font=("Arial", 9)
            )

            y_barra = y + 18
            longitud = 0 if tiempo is None else (tiempo / maximo) * ancho_barra_max
            # Mínimo visible para que la barra exista aunque el tiempo sea casi 0.
            if tiempo is not None and longitud < 2:
                longitud = 2

            canvas.create_rectangle(
                margen_izq, y_barra - 9,
                margen_izq + longitud, y_barra + 9,
                fill=color, outline="",
            )

            # Valor SIEMPRE en la columna fija de la derecha.
            texto = "—" if tiempo is None else f"{tiempo:.6f} ms"
            canvas.create_text(
                x_valor, y_barra, anchor="w", text=texto, font=("Arial", 9)
            )

            y += alto_bloque

    # ------------------------------------------------------------------
    # Pruebas de rendimiento
    # ------------------------------------------------------------------
    def _ejecutar_pruebas(self):
        # Se informa el progreso en cada paso y se refresca la interfaz
        # para que la barra no se quede congelada.
        def progreso(paso, total, cantidad, caso):
            self.barra_progreso["maximum"] = total
            self.barra_progreso["value"] = paso
            self.lbl_progreso.config(
                text=f"Paso {paso}/{total}: {cantidad} registros, caso {caso}"
            )
            self.root.update()

        self.lbl_progreso.config(text="Ejecutando pruebas...")
        self.root.update()

        self._resultados_pruebas = self.controlador.ejecutar_pruebas(progreso)

        self._actualizar_tabla_pruebas()
        self._dibujar_grafico()
        self._actualizar_conclusion()
        self.lbl_progreso.config(
            text=f"Listo: {len(self._resultados_pruebas)} mediciones reales."
        )
        self.barra_progreso["value"] = 0
        self._actualizar_estado("Pruebas de rendimiento finalizadas.")

    def _actualizar_tabla_pruebas(self):
        self.tabla_pruebas.delete(*self.tabla_pruebas.get_children())

        for fila in self._resultados_pruebas:
            self.tabla_pruebas.insert(
                "", "end",
                values=(
                    fila["cantidad"],
                    fila["caso"],
                    f"{fila['tiempo_no_indexado_ms']:.6f}",
                    f"{fila['tiempo_indexado_ms']:.6f}",
                    fila["comparaciones"],
                    fila["operaciones"],
                    f"{fila['tiempo_construccion_indice_ms']:.4f}",
                ),
            )

    # ------------------------------------------------------------------
    # Conclusión automática (calculada desde las mediciones reales)
    # ------------------------------------------------------------------
    def _actualizar_conclusion(self):
        texto = self._generar_conclusion()
        self.area_conclusion.config(state="normal")
        self.area_conclusion.delete("1.0", "end")
        self.area_conclusion.insert("1.0", texto)
        self.area_conclusion.config(state="disabled")

    def _generar_conclusion(self):
        """Calcula una conclusión a partir de los resultados medidos.

        No usa valores predeterminados: todos los números salen de
        las mediciones reales de la última ejecución.
        """
        resultados = self._resultados_pruebas
        if not resultados:
            return "Aún no hay mediciones. Ejecuta las pruebas de rendimiento."

        # Promedio general de cada método sobre TODOS los escenarios.
        prom_sin = sum(r["tiempo_no_indexado_ms"] for r in resultados) / len(resultados)
        prom_con = sum(r["tiempo_indexado_ms"] for r in resultados) / len(resultados)

        lineas = []

        # 1) ¿Qué método fue más rápido en promedio?
        if prom_con < prom_sin:
            if prom_con > 0:
                factor = prom_sin / prom_con
                lineas.append(
                    f"• La búsqueda CON índice fue más rápida en promedio: "
                    f"{prom_con:.6f} ms vs {prom_sin:.6f} ms sin índice "
                    f"(≈ {factor:.1f}× más rápida)."
                )
            else:
                lineas.append(
                    "• La búsqueda CON índice fue más rápida en promedio "
                    "(tiempo medido ≈ 0 ms)."
                )
        else:
            lineas.append(
                f"• En estas mediciones la búsqueda SIN índice promedió "
                f"{prom_sin:.6f} ms vs {prom_con:.6f} ms con índice."
            )

        # 2) ¿Cómo cambia al aumentar los registros? (solo búsqueda sin índice)
        cantidades = sorted({r["cantidad"] for r in resultados})
        if len(cantidades) >= 2:
            menor, mayor = cantidades[0], cantidades[-1]

            def _promedio_sin(cant):
                filas = [r for r in resultados if r["cantidad"] == cant]
                return sum(r["tiempo_no_indexado_ms"] for r in filas) / len(filas)

            def _promedio_con(cant):
                filas = [r for r in resultados if r["cantidad"] == cant]
                return sum(r["tiempo_indexado_ms"] for r in filas) / len(filas)

            t_sin_menor = _promedio_sin(menor)
            t_sin_mayor = _promedio_sin(mayor)
            t_con_menor = _promedio_con(menor)
            t_con_mayor = _promedio_con(mayor)

            if t_sin_menor > 0:
                factor_crecimiento = t_sin_mayor / t_sin_menor
                lineas.append(
                    f"• Al pasar de {menor} a {mayor} registros, la búsqueda "
                    f"SIN índice pasó de {t_sin_menor:.6f} a {t_sin_mayor:.6f} ms "
                    f"(×{factor_crecimiento:.1f}): crece con n [O(n)]."
                )

            if t_con_menor > 0 and t_con_mayor > 0:
                factor_con = t_con_mayor / t_con_menor
                lineas.append(
                    f"• La búsqueda CON índice pasó de {t_con_menor:.6f} a "
                    f"{t_con_mayor:.6f} ms (×{factor_con:.1f}): se mantiene "
                    f"casi plana [O(1) promedio]."
                )

        # 3) Costo de construcción del índice (una vez por conjunto de datos).
        constr_por_cantidad = {}
        for r in resultados:
            constr_por_cantidad[r["cantidad"]] = r["tiempo_construccion_indice_ms"]
        prom_constr = sum(constr_por_cantidad.values()) / len(constr_por_cantidad)
        max_constr = max(constr_por_cantidad.values())
        lineas.append(
            f"• Construcción del índice (una sola vez por conjunto): "
            f"promedio {prom_constr:.4f} ms, máximo {max_constr:.4f} ms. "
            f"Se reutiliza en todas las búsquedas posteriores."
        )

        # 4) Cuándo conviene indexar.
        if prom_con < prom_sin and cantidades:
            lineas.append(
                "• Conviene construir el índice cuando se realizarán varias "
                "búsquedas sobre los mismos datos: el costo de construcción "
                "se amortiza rápidamente."
            )

        return "\n".join(lineas)

    # ------------------------------------------------------------------
    # Gráfico de barras con escala logarítmica (sin bibliotecas externas)
    # ------------------------------------------------------------------
    @staticmethod
    def _formato_ms(valor):
        """Formatea un tiempo en ms con suficiente precisión."""
        if valor >= 1:
            return f"{valor:.4f}"
        if valor >= 0.001:
            return f"{valor:.6f}"
        if valor >= 0.000001:
            return f"{valor:.9f}"
        if valor > 0:
            return f"{valor:.3e}"
        return "0"

    @staticmethod
    def _altura_log(valor, valor_min, valor_max, alto_util):
        """Convierte un tiempo (ms) a píxeles usando escala log10.

        Maneja valores cero o no positivos asignándoles la altura mínima
        visible para que no desaparezcan en la escala logarítmica.
        """
        min_px = 3  # altura mínima visible de una barra

        if valor_max <= valor_min:
            return max(alto_util / 2, min_px)

        # Valores no positivos → altura mínima (no se pueden tomar log).
        if valor <= 0:
            return min_px

        log_v = math.log10(valor)
        log_min = math.log10(valor_min)
        log_max = math.log10(valor_max)

        if log_max <= log_min:
            return max(alto_util / 2, min_px)

        fraccion = (log_v - log_min) / (log_max - log_min)
        altura = fraccion * alto_util
        return max(altura, min_px)

    def _dibujar_grafico(self):
        canvas = self.canvas_grafico
        canvas.delete("all")

        if not self._resultados_pruebas:
            return

        ancho = canvas.winfo_width()
        alto = canvas.winfo_height()
        if ancho < 50 or alto < 50:
            return

        escenario = self.combo_escenario.get()

        # Filas del escenario seleccionado (uno por cantidad de registros).
        filas = [
            r for r in self._resultados_pruebas if r["caso"] == escenario
        ]
        if not filas:
            return

        # Ordenar por cantidad de registros.
        filas.sort(key=lambda r: r["cantidad"])

        grupos = [
            (r["cantidad"], r["tiempo_no_indexado_ms"], r["tiempo_indexado_ms"])
            for r in filas
        ]

        # Rango de valores positivos para la escala logarítmica.
        valores = []
        for _, t_sin, t_con in grupos:
            if t_sin > 0:
                valores.append(t_sin)
            if t_con > 0:
                valores.append(t_con)

        if not valores:
            canvas.create_text(
                ancho // 2, alto // 2,
                text="No hay valores positivos para graficar en este escenario.",
            )
            return

        valor_min = min(valores)
        valor_max = max(valores)
        # Evitar rango degenerado (todos iguales o casi iguales).
        if valor_max <= valor_min:
            valor_max = valor_min * 10
        # Tope suave para que una sola barra gigante no aplaste el resto.
        if valor_max / valor_min > 1e9:
            valor_min = valor_max / 1e9

        margen_izquierdo = 85
        margen_derecho = 20
        margen_superior = 30
        margen_inferior = 45
        ancho_util = ancho - margen_izquierdo - margen_derecho
        alto_util = alto - margen_superior - margen_inferior

        # Eje vertical y horizontal.
        canvas.create_line(
            margen_izquierdo, margen_superior,
            margen_izquierdo, alto - margen_inferior,
        )
        canvas.create_line(
            margen_izquierdo, alto - margen_inferior,
            ancho - margen_derecho, alto - margen_inferior,
        )

        # Marcas del eje Y en potencias de 10 (escala logarítmica).
        exp_min = math.floor(math.log10(valor_min))
        exp_max = math.ceil(math.log10(valor_max))
        # Limitar la cantidad de marcas para no saturar el eje.
        exponentes = list(range(exp_min, exp_max + 1))
        while len(exponentes) > 8:
            exponentes = exponentes[::2]

        for exp in exponentes:
            valor_marca = 10 ** exp
            if valor_marca < valor_min * 0.999 or valor_marca > valor_max * 1.001:
                continue
            y = (alto - margen_inferior
                 - self._altura_log(valor_marca, valor_min, valor_max, alto_util))
            canvas.create_line(
                margen_izquierdo - 4, y, margen_izquierdo, y,
                fill="#bbbbbb",
            )
            canvas.create_text(
                margen_izquierdo - 8, y, anchor="e",
                text=self._formato_ms(valor_marca),
                fill="#666666", font=("Arial", 7),
            )

        ancho_grupo = ancho_util / len(grupos)
        ancho_barra = min(ancho_grupo * 0.32, 40)

        for indice, (cantidad, tiempo_sin, tiempo_con) in enumerate(grupos):
            centro = margen_izquierdo + ancho_grupo * indice + ancho_grupo / 2

            base = alto - margen_inferior

            # Barra roja: búsqueda sin índice.
            alto_sin = self._altura_log(
                tiempo_sin, valor_min, valor_max, alto_util
            )
            x1 = centro - ancho_barra - 2
            canvas.create_rectangle(
                x1, base - alto_sin,
                x1 + ancho_barra, base,
                fill="#e74c3c", outline="",
            )

            # Barra verde: búsqueda con índice.
            alto_con = self._altura_log(
                tiempo_con, valor_min, valor_max, alto_util
            )
            x2 = centro + 2
            canvas.create_rectangle(
                x2, base - alto_con,
                x2 + ancho_barra, base,
                fill="#27ae60", outline="",
            )

            # Etiqueta de la cantidad en el eje X.
            canvas.create_text(
                centro, base + 16,
                text=f"{cantidad}", fill="black",
            )

            # Valor encima de cada barra (precisión suficiente).
            canvas.create_text(
                x1 + ancho_barra / 2, base - alto_sin - 8,
                text=self._formato_ms(tiempo_sin),
                fill="#c0392b", font=("Arial", 7),
            )
            canvas.create_text(
                x2 + ancho_barra / 2, base - alto_con - 8,
                text=self._formato_ms(tiempo_con),
                fill="#1e8449", font=("Arial", 7),
            )

        # Leyenda.
        canvas.create_rectangle(ancho - 190, 8, ancho - 176, 22,
                                fill="#e74c3c", outline="")
        canvas.create_text(ancho - 170, 15, anchor="w", text="Sin índice")
        canvas.create_rectangle(ancho - 100, 8, ancho - 86, 22,
                                fill="#27ae60", outline="")
        canvas.create_text(ancho - 80, 15, anchor="w", text="Con índice")

        canvas.create_text(
            margen_izquierdo, 12, anchor="w",
            text=(
                f"Escenario «{escenario}» — tiempo de búsqueda en milisegundos "
                f"(ms), escala logarítmica vertical"
            ),
        )

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------
    def _actualizar_estado(self, mensaje=None):
        if mensaje is None:
            mensaje = (
                f"Registros: {self.controlador.cantidad_registros()} | "
                f"Índice: "
                + ("construido" if self.controlador.hay_indice() else "no construido")
            )
        self.lbl_estado.config(text=mensaje)

    def ejecutar(self):
        """Inicia el bucle principal de la interfaz."""
        self.root.mainloop()
