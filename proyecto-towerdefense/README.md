# Propuesta de Proyecto Educativo: Tower Defense - Invasión de Enemigos

**Duración del proyecto:** 3 semanas  
**Lenguaje y tecnologías:** Python, Pygame  
**Patrón de diseño:** Modelo-Vista-Controlador (MVC)  
**Semana presentada:** Semana 1 - Implementación de estructuras de datos y modelo base

---

## 1. Resumen del Proyecto

El proyecto consiste en desarrollar un juego **Tower Defense**, donde los enemigos aparecen en oleadas, avanzan por un recorrido y deben ser eliminados antes de llegar a la base.

El objetivo principal del proyecto es aplicar de manera práctica los conceptos de **Estructuras de Datos y Algoritmos**, implementando manualmente las estructuras necesarias para administrar los enemigos y las acciones del juego.

A diferencia de intentar utilizar todas las estructuras disponibles, se utilizarán únicamente aquellas que tengan una función real dentro del juego.

Durante esta primera semana el proyecto se concentrará principalmente en la **implementación y prueba de las estructuras de datos**, dejando la interfaz gráfica y la integración completa del juego para las siguientes etapas.

---

## 2. Objetivos de la Semana 1

Durante la primera semana se busca:

- Implementar estructuras de datos manualmente.
- Comprender qué problema del juego resuelve cada estructura.
- Trabajar con nodos y referencias/punteros.
- Realizar operaciones básicas sobre las estructuras.
- Comprobar mediante pruebas que las estructuras funcionan correctamente.
- Analizar de forma básica la complejidad de las operaciones.
- Dejar preparado el modelo base para integrarlo posteriormente con el juego.

---

## 3. Aplicación de las Estructuras de Datos

| Estructura | Uso dentro del Tower Defense |
|---|---|
| **Cola (Queue)** | Mantener los enemigos que están esperando para aparecer en el mapa. |
| **Lista Doblemente Enlazada** | Mantener los enemigos que actualmente están activos en el mapa. |
| **Pila (Stack)** | Preparar un sistema de historial para posibles funciones de Deshacer/Rehacer. |

### 3.1 Cola (Queue)

Las oleadas de enemigos necesitan respetar un orden de entrada.

Los enemigos que llegan primero deben ser los primeros en aparecer en el mapa.

Esto corresponde al comportamiento:

**FIFO (First In, First Out)**

Ejemplo:

```text
Enemigo 1 → Enemigo 2 → Enemigo 3 → Enemigo 4
     ↓
Aparece primero el Enemigo 1
```

La cola permitirá almacenar los enemigos que todavía están esperando para entrar al campo de juego.

---

### 3.2 Lista Doblemente Enlazada

Los enemigos que ya están dentro del mapa serán almacenados en una **Lista Doblemente Enlazada**.

Cada nodo tendrá referencias hacia:

- El enemigo actual.
- El nodo anterior (`prev`).
- El nodo siguiente (`next`).

Representación:

```text
NULL ← [Enemigo 1] ⇄ [Enemigo 2] ⇄ [Enemigo 3] → NULL
```

Esta estructura resulta útil porque durante una partida los enemigos pueden ser eliminados en cualquier momento.

Por ejemplo, si una torre elimina al Enemigo 2:

```text
Antes:

[Enemigo 1] ⇄ [Enemigo 2] ⇄ [Enemigo 3]

Después:

[Enemigo 1] ⇄ [Enemigo 3]
```

La eliminación puede realizarse modificando las referencias de los nodos vecinos, sin tener que desplazar todos los elementos como ocurriría en una estructura basada directamente en un arreglo.

---

### 3.3 Pila (Stack)

La pila se implementará como una estructura **LIFO (Last In, First Out)**.

Durante esta primera semana se preparará como base para un posible sistema de historial de acciones.

Por ejemplo:

```text
Acción 3  ← última acción
Acción 2
Acción 1
```

La última acción almacenada sería la primera en recuperarse.

La implementación de Undo/Redo podrá ampliarse posteriormente mediante dos pilas, dependiendo de las indicaciones y necesidades del proyecto.

---

## 4. Arquitectura Inicial

El proyecto seguirá una organización compatible con el patrón **MVC**, pero durante la primera semana se priorizará el desarrollo del modelo y las estructuras de datos.

```text
Tower Defense
│
├── Model
│   ├── structures.py
│   └── game_model.py
│
├── View
│   └── game_view.py
│
├── Controller
│   └── game_controller.py
│
└── main.py
```

### Modelo

Contendrá las estructuras de datos y la lógica relacionada con los enemigos.

### Vista

Posteriormente será responsable de mostrar el juego utilizando Pygame.

### Controlador

Posteriormente conectará las acciones del usuario y del juego con el modelo.

> Durante la Semana 1, la prioridad será que el modelo funcione correctamente antes de desarrollar la interfaz gráfica.

---

## 5. Plan de Trabajo - Semana 1

### Día 1 - Preparación y diseño

- Configurar el proyecto en Python.
- Definir la organización inicial de carpetas.
- Identificar las estructuras necesarias.
- Definir los nodos que serán utilizados por las estructuras enlazadas.
- Establecer cómo se relacionarán las estructuras con los enemigos del juego.

**Resultado esperado:** estructura inicial del proyecto y diseño de las estructuras.

---

### Día 2 - Lista Doblemente Enlazada

Implementar la estructura `DoublyLinkedList`.

Operaciones iniciales:

- Insertar al inicio.
- Insertar al final.
- Buscar un elemento.
- Eliminar un elemento.
- Recorrer la lista.
- Mantener referencias `prev` y `next`.

También se deberán considerar casos como:

- Lista vacía.
- Lista con un solo nodo.
- Eliminación del primer nodo.
- Eliminación del último nodo.
- Eliminación de un nodo intermedio.

**Resultado esperado:** lista doblemente enlazada funcionando y probada.

---

### Día 3 - Cola de Enemigos

Implementar una estructura `Queue` utilizando nodos.

Operaciones principales:

- `enqueue()` para agregar enemigos.
- `dequeue()` para retirar el siguiente enemigo.
- `peek()` para consultar el siguiente enemigo.
- Comprobar si la cola está vacía.

Ejemplo:

```text
Enemigos esperando:

[Enemy 1] → [Enemy 2] → [Enemy 3] → [Enemy 4]

dequeue()

[Enemy 2] → [Enemy 3] → [Enemy 4]
```

**Resultado esperado:** cola FIFO funcionando correctamente.

---

### Día 4 - Pila

Implementar una estructura `Stack`.

Operaciones principales:

- `push()` para agregar una acción.
- `pop()` para retirar la última acción.
- `peek()` para consultar la última acción.
- Comprobar si la pila está vacía.

La estructura quedará preparada para posteriormente implementar un sistema de Undo/Redo si se considera necesario.

**Resultado esperado:** pila LIFO funcionando correctamente.

---

### Día 5 - Pruebas y documentación

Realizar pruebas de las estructuras implementadas.

Se comprobarán principalmente:

- Inserciones.
- Eliminaciones.
- Búsquedas.
- Recorridos.
- Lista vacía.
- Un solo elemento.
- Eliminación de elementos intermedios.
- Orden FIFO de la cola.
- Orden LIFO de la pila.

También se documentará de forma básica la complejidad temporal de las operaciones principales.

**Resultado esperado:** estructuras funcionando y documentadas, listas para integrarse posteriormente con el juego.

---

## 6. Complejidad Inicial

Se realizará un análisis de complejidad de las operaciones principales.

| Estructura | Operación | Complejidad esperada |
|---|---|---|
| Lista doblemente enlazada | Insertar al inicio | O(1) |
| Lista doblemente enlazada | Insertar al final | O(1) si se mantiene `tail` |
| Lista doblemente enlazada | Buscar | O(n) |
| Lista doblemente enlazada | Eliminar por valor | O(n) para encontrar el nodo |
| Cola | `enqueue()` | O(1) |
| Cola | `dequeue()` | O(1) |
| Pila | `push()` | O(1) |
| Pila | `pop()` | O(1) |

La complejidad podrá ajustarse posteriormente según la implementación final y las indicaciones del docente.

---

## 7. Resultado Esperado al Final de la Semana 1

Al terminar la primera semana se espera contar con:

- Proyecto Python organizado.
- Nodo base para estructuras enlazadas.
- Cola funcional para enemigos pendientes.
- Lista doblemente enlazada funcional para enemigos activos.
- Pila funcional para historial de acciones.
- Pruebas de las operaciones principales.
- Documentación básica de las estructuras.
- Primera relación entre las estructuras de datos y el funcionamiento del Tower Defense.

En esta etapa **todavía no es necesario tener el juego visual completo funcionando en Pygame**.

---

## 8. Flujo Conceptual del Juego

La relación entre las estructuras de datos durante esta primera etapa será:

```text
                 TOWER DEFENSE
                       │
             Oleada de enemigos
                       │
                       ▼
              ┌─────────────────┐
              │      QUEUE      │
              │ Enemigos en     │
              │ espera          │
              └────────┬────────┘
                       │ dequeue()
                       ▼
              ┌─────────────────┐
              │ DOUBLY LINKED   │
              │ LIST            │
              │ Enemigos activos│
              └────────┬────────┘
                       │
                Torre elimina
                    enemigo
                       │
                       ▼
              Se elimina el nodo
              correspondiente
```

La pila funcionará de manera independiente como base para el historial:

```text
       Acciones del juego
              │
              ▼
        ┌───────────┐
        │   STACK   │
        │ Acción 3  │
        │ Acción 2  │
        │ Acción 1  │
        └───────────┘
```

---

## 9. Alcance de la Primera Presentación

La primera presentación estará enfocada en demostrar que las estructuras seleccionadas tienen una razón de ser dentro del proyecto.

Se podrá explicar:

1. **Qué problema resuelve el Tower Defense.**
2. **Por qué se eligió una cola para los enemigos que esperan.**
3. **Por qué se eligió una lista doblemente enlazada para los enemigos activos.**
4. **Por qué se implementó una pila y cuál será su posible función.**
5. **Cómo funciona cada estructura internamente.**
6. **Qué operaciones fueron implementadas.**
7. **Qué pruebas se realizaron.**
8. **Cuál es la complejidad de las operaciones principales.**

La interfaz gráfica y la integración completa con Pygame quedarán para las siguientes etapas y podrán modificarse de acuerdo con las observaciones del ingeniero.

---

## 10. Evolución del Proyecto

El proyecto será desarrollado de manera incremental.

La Semana 1 funcionará como una **base inicial que podrá ser corregida o ampliada** después de la presentación.

Las siguientes etapas podrán incorporar, según las indicaciones del docente:

- Integración con Pygame.
- Movimiento de enemigos.
- Torres y ataques.
- Sistema de oleadas.
- Integración completa del modelo con MVC.
- Visualización de las estructuras de datos.
- Sistema de Undo/Redo.
- Nuevas estructuras solamente si existe una necesidad real dentro del juego.
- Pruebas adicionales y análisis de complejidad.

De esta manera, el proyecto puede evolucionar progresivamente sin implementar estructuras o funcionalidades que todavía no sean necesarias.

---

## Conclusión

La primera semana del proyecto se enfoca en construir una base sólida de **Estructuras de Datos aplicadas a un Tower Defense**.

La selección inicial de estructuras se limita a:

- **Queue:** enemigos esperando para entrar.
- **Doubly Linked List:** enemigos activos dentro del mapa.
- **Stack:** base para historial y posible Undo/Redo.

El objetivo de esta etapa no es terminar el juego, sino demostrar que las estructuras están correctamente implementadas, que tienen una aplicación concreta y que pueden ser integradas posteriormente al sistema completo.

## Semana 2: Integración gráfica y mecánicas básicas

### Objetivo de la semana

Integrar el modelo de enemigos con la interfaz gráfica del juego, implementar el movimiento de los enemigos y permitir que las torretas ataquen automáticamente. También se busca establecer un comportamiento consistente para seleccionar los objetivos de ataque.

### Plan de trabajo por días

#### Día 1: Modelo general de enemigos

Se implementó una clase general `Enemy` para representar a los diferentes enemigos del juego, evitando crear una clase independiente para cada tipo de enemigo.

La clase contempla los siguientes atributos y comportamientos:

- Identificador único del enemigo.
- Nombre del enemigo.
- Puntos de vida (`hp`).
- Velocidad de movimiento (`speed`).
- Progreso de desplazamiento (`progress`).
- Estado del enemigo: vivo o derrotado.
- Método `take_damage(damage)` para recibir daño y actualizar sus puntos de vida.

Se añadieron pruebas para comprobar el funcionamiento del modelo de enemigos.

#### Día 2: Integración del juego con la interfaz gráfica

Se avanzó en la integración del modelo y el controlador con la vista del juego, permitiendo representar gráficamente los elementos principales del Tower Defense.

Se mantuvo la organización del proyecto mediante el patrón MVC:

- **Model:** administra los datos y el estado de los enemigos.
- **Controller:** coordina la lógica del juego y el comportamiento de las torretas.
- **View:** muestra los elementos del juego y sus cambios en pantalla.

#### Día 3: Representación y movimiento de los enemigos

Se incorporaron los enemigos a la representación gráfica del juego y se implementó su desplazamiento en línea recta.

Los enemigos avanzan mientras se desarrolla la partida, permitiendo observar su progreso y comprobar cómo interactúan con las torretas.

#### Día 4: Ataque automático de las torretas

Se implementó el comportamiento de ataque de las tres torretas presentes en el juego.

Las torretas atacan a los enemigos y reducen sus puntos de vida. De esta manera, el sistema conecta el comportamiento ofensivo de las torretas con el estado de los enemigos definido en el modelo.

También se corrigió un problema de selección de objetivos: anteriormente, una torreta podía afectar a varios enemigos al mismo tiempo. Después del ajuste, cada torreta se concentra en un solo enemigo por ataque y prioriza al enemigo que tiene menos puntos de vida en ese momento.

#### Día 5: Integración y comprobación del funcionamiento

Se integraron los componentes desarrollados durante la semana y se realizaron ajustes para comprobar el comportamiento general de la partida.

Se verificó visualmente que:

- Los enemigos aparecen y avanzan por el escenario.
- Las tres torretas pueden atacar a los enemigos.
- Los puntos de vida de los enemigos disminuyen al recibir daño.
- Cada torreta selecciona un único objetivo por ataque.
- La selección del objetivo prioriza al enemigo con menor cantidad de vida.

### Resultado de la Semana 2

Al finalizar la segunda semana, el proyecto cuenta con una versión gráfica funcional de las mecánicas básicas del Tower Defense. Los enemigos pueden desplazarse por el escenario y las tres torretas los atacan automáticamente, reduciendo sus puntos de vida.

Además, se mejoró la selección de objetivos para evitar que una torreta ataque a varios enemigos simultáneamente y para priorizar al enemigo con menos vida.

Esta etapa permite pasar de un modelo centrado en las estructuras de datos a una versión interactiva del juego, sobre la cual se podrán incorporar nuevas mecánicas en las siguientes semanas.

### Alcance de la segunda presentación

Para la presentación de la Semana 2, se consideran los siguientes elementos:

- Modelo general de enemigos implementado.
- Integración del modelo con la interfaz gráfica.
- Tres torretas representadas en el escenario.
- Movimiento de los enemigos en línea recta.
- Ataque automático de las torretas.
- Reducción de los puntos de vida de los enemigos.
- Selección de un objetivo por ataque y priorización del enemigo con menos vida.

### Evolución del proyecto

La Semana 1 se centró en la implementación y comprobación de las estructuras de datos necesarias para organizar los elementos del juego.

Durante la Semana 2, estas bases se integraron con la representación gráfica y las mecánicas de movimiento y ataque.

Las siguientes etapas podrán centrarse en ampliar la lógica de la partida, incorporar recorridos más elaborados, gestionar oleadas de enemigos y definir las condiciones de victoria y derrota, siempre utilizando estructuras de datos cuando aporten una utilidad real al funcionamiento del juego.