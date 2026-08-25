# 📚 Enunciados — Unidad 1

## Desafío 1 — El misterio de las referencias

### 🧠 Gestión de Memoria

**Problema:**

Un estudiante intenta duplicar una lista de valores, pero al modificar la **copia**, la lista original también cambia.

**Objetivo:**

Determinar:

* Por qué la modificación de la copia afecta a la lista original.
* Qué sucede con las referencias a los objetos en memoria.
* Cómo realizar una copia que permita modificar la nueva lista sin afectar a la original.

---

## Desafío 2 — Implementación de TDA Pila (Stack)

### 📚 Tipo de Dato Abstracto

**Problema:**

La siguiente clase `Stack` presenta varios errores críticos en su implementación:

* La función `pop` no valida si la pila está vacía.
* La lógica de `is_empty` está implementada de manera inversa.
* El método `push` no está almacenando los elementos correctamente.

**Objetivo:**

Analizar el código proporcionado, identificar los errores y corregir la implementación para que la clase `Stack` funcione correctamente.

La implementación deberá respetar el comportamiento esperado de una **pila (LIFO — Last In, First Out)**.

---

## Desafío 3 — Gestión de Memoria en el Heap

### 🔗 Nodos Dinámicos

**Contexto:**

En lenguajes de bajo nivel, la memoria del **Heap** requiere una gestión manual. En Python, la gestión de memoria se realiza automáticamente, pero el concepto de las referencias sigue siendo fundamental para comprender el funcionamiento de las estructuras dinámicas.

Si se pierde la referencia al punto inicial de una estructura, se pierde el acceso directo a los datos que forman parte de ella.

**Problema:**

El siguiente código intenta crear una secuencia formada por **dos nodos en el Heap**. Sin embargo, debido a una mala asignación, el segundo nodo reemplaza al primero en la variable utilizada para controlar la estructura.

Como consecuencia, se pierde la referencia al inicio de la estructura.

**Objetivo:**

Analizar el problema de referencias y corregir la implementación para mantener correctamente el acceso a los dos nodos.

---

## Desafío 4 — TDA Punto y Circunferencia

### 📍 Paso por Referencia vs. Valor

**Contexto:**

Se ha definido un `Punto` y una `Circunferencia` que utiliza un objeto `Punto` como su centro.

En Python, las variables que contienen objetos almacenan **referencias** a dichos objetos. Esto puede producir comportamientos inesperados cuando un mismo objeto mutable es utilizado desde diferentes partes del programa.

**Problema:**

Un estudiante crea una `Circunferencia` utilizando como centro un objeto `Punto`.

Posteriormente, modifica directamente las coordenadas del `Punto` original, esperando que la `Circunferencia` conserve el centro que tenía originalmente.

Sin embargo, debido a que la `Circunferencia` mantiene una referencia al mismo objeto `Punto`, la modificación de las coordenadas también afecta al centro de la `Circunferencia`.

**Objetivo:**

Analizar el problema y determinar cómo evitar que las modificaciones realizadas sobre el `Punto` original afecten al centro de la `Circunferencia`.

---

## Desafío 5 — TDA Automóvil y Garaje

### 🚗 Gestión de Objetos en Colecciones

**Contexto:**

Se está modelando un `Automovil` y un `Garaje` que almacena una colección de automóviles.

Al trabajar con listas de objetos, es importante comprender cómo Python maneja las **referencias a objetos** en memoria.

**Problema:**

Un estudiante intenta añadir varios automóviles a un garaje. Sin embargo, debido a una reutilización incorrecta de una variable que contiene un objeto `Automovil`, termina con un garaje que parece contener el **mismo automóvil repetido varias veces**, en lugar de automóviles independientes.

**Objetivo:**

Analizar el manejo de referencias de objetos dentro de una colección y corregir la implementación para que cada automóvil almacenado en el garaje sea un objeto independiente.

---

## Desafío 6 — TDA Línea

### 📏 Inmutabilidad Conceptual con Objetos Mutables

**Contexto:**

Una `Línea` se define mediante dos objetos `Punto`:

* Un punto de inicio.
* Un punto final.

Conceptualmente, una vez definida la línea, sus puntos extremos no deberían cambiar cuando se modifican los objetos `Punto` originales utilizados durante su creación, a menos que dicho comportamiento sea explícitamente deseado.

**Problema:**

Al igual que ocurre con el desafío de la `Circunferencia`, si la clase `Línea` almacena referencias directas a los objetos `Punto` mutables recibidos durante su inicialización, cualquier modificación externa realizada sobre dichos puntos también afectará a la `Línea`.

El estudiante espera que la línea permanezca **estática después de su creación**, pero las referencias compartidas provocan que sus puntos extremos cambien.

**Objetivo:**

Analizar el problema producido por las referencias compartidas y determinar cómo conseguir que la `Línea` conserve sus puntos originales independientemente de las modificaciones realizadas posteriormente sobre los objetos `Punto` externos.
