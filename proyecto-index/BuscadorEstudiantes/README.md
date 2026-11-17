# Comparador de Búsquedas Indexadas y No Indexadas

Proyecto académico de la materia **Estructura de Datos I (ED1)**.

Una aplicación en Python que demuestra, comprende y compara el funcionamiento de la
**búsqueda no indexada** (secuencial) y la **búsqueda indexada** (con diccionario)
mediante un sistema de búsqueda de estudiantes.

---

## 1. Objetivo del proyecto

- Generar registros de estudiantes en memoria.
- Buscar un estudiante por ID de dos formas distintas.
- Medir tiempos reales de ejecución con `time.perf_counter()`.
- Contar las comparaciones que realiza cada algoritmo.
- Comparar el rendimiento de ambos métodos con diferentes cantidades de registros.

No se utilizan bases de datos externas: todos los datos viven en memoria.

---

## 2. ¿Qué es la búsqueda no indexada?

Es la **búsqueda secuencial**: se recorre la lista de estudiantes desde el
principio hasta el final, comparando el ID de cada registro con el ID buscado,
hasta encontrarlo (o hasta llegar al final de la lista).

```python
for posicion in range(len(self.estudiantes)):
    if self.estudiantes[posicion].id == id_buscar:
        return self.estudiantes[posicion]
```

**Características:**

- No requiere ninguna estructura auxiliar.
- Examina los registros uno por uno.
- Si el estudiante está al final (o no existe), examina todos los registros.

## 3. ¿Qué es la búsqueda indexada?

Es una búsqueda que se apoya en un **índice auxiliar**: un diccionario de Python
donde la **clave es el ID** del estudiante y el **valor es la posición** que ese
estudiante ocupa dentro de la lista original.

```python
indice = {
    1001: 0,
    1002: 1,
    1003: 2,
    1004: 3
}
```

Para buscar:

1. Se consulta el ID en el diccionario (operación de hash).
2. Se obtiene la posición guardada.
3. Se accede a la lista original con esa posición (`self.estudiantes[posicion]`).

```python
posicion = self.indice.get(id_buscar)
return self.estudiantes[posicion]
```

**Características:**

- Requiere construir el índice primero (tiempo y memoria adicionales).
- La búsqueda no recorre la lista: va directo al registro.
- El diccionario de Python está implementado con una **tabla hash**.

---

## 4. ¿Por qué se indexan los datos?

Porque **el costo de la búsqueda secuencial crece a medida que crecen los
datos**, mientras que el costo de la búsqueda con índice se mantiene casi
constante.

La contrapartida es que **construir y mantener el índice consume tiempo y
memoria adicionales**. El índice solo compensa si se realizarán muchas
búsquedas sobre los mismos datos.

---

## 5. Diferencias entre ambos métodos

| Aspecto | Búsqueda no indexada | Búsqueda indexada |
|---|---|---|
| Estructura usada | Solo la lista original | Lista original + diccionario |
| Recorrido | Recorre elemento por elemento | Acceso directo por posición |
| Preparación previa | Ninguna | Construir el índice |
| Costo en memoria | Ninguno adicional | Un diccionario con un registro por estudiante |
| Mejor caso | ID en la primera posición | Siempre el mismo |
| Peor caso | Último ID o ID inexistente | Siempre el mismo |
| Complejidad | O(n) | O(1) promedio |

> Nota: ambos algoritmos trabajan sobre la **misma lista original**, para que la
> comparación sea justa. La búsqueda no indexada nunca consulta el diccionario.

---

## 6. Complejidad temporal

- **Búsqueda secuencial: O(n)** — en el peor caso se examinan los `n` registros.
  Si hay 10.000 estudiantes y el ID está al final, se hacen 10.000 comparaciones.
- **Búsqueda indexada: O(1) promedio** — el diccionario de Python usa una tabla
  hash, por lo que la consulta del ID tarda un tiempo promedio constante,
  sin importar cuántos registros existan.
- **Construcción del índice: O(n)** — se recorre la lista una sola vez para
  registrar cada posición. Este tiempo se mide por separado del tiempo de
  búsqueda.

---

## 7. Arquitectura MVC

El proyecto separa las responsabilidades en tres componentes:

```text
Vista  ──(acciones del usuario)──►  Controlador  ──(peticiones)──►  Modelo
Vista  ◄──(resultados a mostrar)──  Controlador  ◄──(datos)──────  Modelo
```

| Componente | Archivo | Responsabilidad |
|---|---|---|
| **Modelo** | `models/estudiante.py` | Almacena y representa los estudiantes, los genera, implementa ambos algoritmos de búsqueda y construye el índice. No conoce a la vista ni al controlador. |
| **Controlador** | `controllers/estudiante_controller.py` | Recibe las acciones de la vista, pide operaciones al modelo, mide tiempos con `time.perf_counter()`, cuenta comparaciones, ejecuta las pruebas de rendimiento y entrega los resultados a la vista. |
| **Vista** | `views/estudiante_view.py` | Interfaz gráfica con Tkinter: botones, campos, tablas, área de resultados, comparación visual y gráfico. Solo muestra datos y captura acciones; no contiene lógica de búsqueda. |

---

## 8. Estructura de carpetas

```text
BuscadorEstudiantes/
│
├── models/
│   └── estudiante.py
│
├── controllers/
│   └── estudiante_controller.py
│
├── views/
│   └── estudiante_view.py
│
├── main.py
│
└── README.md
```

---

## 9. Cómo ejecutar el programa

Requisito: Python 3 con Tkinter (incluido en la instalación estándar de Python).

```bash
cd BuscadorEstudiantes
python main.py
```

Pasos de uso:

1. Selecciona la **cantidad de estudiantes** y pulsa **Generar registros**.
2. Pulsa **Construir índice**.
3. Escribe un **ID** (por ejemplo `1001`, `1500` o `5000`).
4. Pulsa **Buscar SIN índice** y luego **Buscar CON índice** para comparar.
5. Abre la pestaña **Pruebas de rendimiento** y pulsa
   **Ejecutar pruebas de rendimiento**.

---

## 10. Cómo interpretar los resultados

### Pestaña "Búsqueda"

- **Resultado**: si el estudiante fue encontrado o no, junto con sus datos.
- **Registros examinados (comparaciones)**: cuántos elementos recorrió la
  búsqueda secuencial. Crece según la posición del ID.
- **Operaciones sobre el índice**: siempre `1` (la consulta al diccionario),
  aunque el ID no exista.
- **Tiempo de ejecución**: medido con `time.perf_counter()` en milisegundos.
- **Comparación de tiempos**: dos barras proporcionales que muestran el tiempo
  de cada método.
- **Construcción del índice**: se muestra aparte, porque no forma parte de la
  búsqueda.

### Pestaña "Pruebas de rendimiento"

La tabla contiene una fila por cada combinación de *cantidad de registros* y
*caso de consulta*:

| Columna | Significado |
|---|---|
| Registros | Cantidad de estudiantes generados (10 a 10.000) |
| Caso | `primero`, `medio`, `final` o `inexistente` |
| Tiempo no indexado (ms) | Promedio de 30 repeticiones de la búsqueda secuencial |
| Tiempo indexado (ms) | Promedio de 30 repeticiones de la búsqueda con índice |
| Comparaciones | Registros examinados por la búsqueda secuencial |
| Construcción índice (ms) | Tiempo que tardó en crearse el diccionario |

Los cuatro casos se prueban con **las mismas consultas** para ambos algoritmos,
usando la misma lista de estudiantes y la misma semilla (`42`), de modo que la
comparación sea justa y reproducible.

El **gráfico de barras** muestra el tiempo promedio de búsqueda por cantidad de
registros: en rojo la búsqueda sin índice y en verde la búsqueda con índice.
Todos los valores son mediciones reales, no tiempos simulados.

### Ejemplo real (máquina de desarrollo)

Con 10.000 registros, búsqueda del último estudiante (promedio de 30
repeticiones):

| Método | Tiempo | Comparaciones |
|---|---|---|
| Sin índice | ≈ 1.68 ms | 10.000 |
| Con índice | ≈ 0.0006 ms | 1 |

Los tiempos exactos varían en cada equipo, pero la **proporción** se mantiene:
la búsqueda secuencial crece linealmente con la cantidad de registros, mientras
la búsqueda con índice permanece prácticamente constante.

---

## 11. Consideraciones académicas

- Los datos se generan con **semilla fija** (`random.seed(42)`), por lo que la
  generación es reproducible: la misma semilla produce los mismos estudiantes.
- Los IDs son únicos e incrementales a partir de `1001`.
- Los nombres y carreras provienen de listas predefinidas.
- No se usan bibliotecas externas: solo `tkinter`, `random` y `time`.
- Los tiempos provienen únicamente de ejecuciones reales.
