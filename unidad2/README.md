# Proyecto: Calculadora y Comparador de Fracciones

## Descripción

Este proyecto consiste en un programa desarrollado en **Python** que permite trabajar con fracciones mediante una interfaz de consola.

El programa permite realizar operaciones aritméticas entre dos fracciones, además de ingresar múltiples fracciones para compararlas y ordenarlas.

## Funcionalidades

### Calculadora de fracciones

Permite trabajar con dos fracciones y realizar las siguientes operaciones:

* Suma
* Resta
* Multiplicación
* División

Las fracciones se simplifican automáticamente utilizando el **máximo común divisor (MCD)**.

### Comparador de fracciones

Permite ingresar varias fracciones y ordenarlas:

* De menor a mayor
* De mayor a menor

Para realizar la comparación, cada fracción se convierte temporalmente a su valor decimal.

## Validaciones

El programa incluye diferentes validaciones para evitar errores:

* No permite denominadores iguales a cero.
* No permite dividir entre una fracción cuyo numerador sea cero.
* Verifica que las fracciones sean ingresadas utilizando el formato `numerador/denominador`.
* Verifica que la cantidad de fracciones a comparar sea de al menos 2.
* Controla las opciones inválidas del menú.

## Estructura principal

El programa está organizado mediante una clase principal y varias funciones:

### Clase `Fraccion`

Representa una fracción y contiene los métodos necesarios para trabajar con ella.

Entre sus principales métodos se encuentran:

* `simplificar()` → Reduce la fracción utilizando el MCD.
* `sumar()` → Suma dos fracciones.
* `restar()` → Resta dos fracciones.
* `multiplicar()` → Multiplica dos fracciones.
* `dividir()` → Divide dos fracciones.
* `valor()` → Obtiene el valor decimal.
* `__str__()` → Representa la fracción como texto.

### Funciones principales

* `ingresar_fraccion()` → Permite ingresar una fracción por teclado.
* `calculadora()` → Ejecuta las operaciones entre dos fracciones.
* `comparar_fracciones()` → Permite ingresar y ordenar múltiples fracciones.
* `mostrar_menu()` → Muestra el menú principal del programa.

## Requisitos

Para ejecutar el programa se necesita:

* Python 3.x
* Módulo `math` incluido en Python.

No es necesario instalar librerías externas.

## Ejecución

Desde la terminal, ubicarse en la carpeta donde se encuentra el archivo y ejecutar:

```bash
python nombre_del_archivo.py
```

En Windows también puede utilizarse:

```bash
py nombre_del_archivo.py
```

## Ejemplo de uso

Al ejecutar el programa se muestra el menú principal:

```text
==============================
   PROYECTO: FRACCIONES
==============================
1. Calculadora de fracciones
2. Comparar y ordenar fracciones
3. Salir
```

Por ejemplo, si se ingresan:

```text
1/2
3/4
```

y se selecciona la opción de sumar, el programa mostrará:

```text
Resultado: 1/2 + 3/4 = 5/4
```

## Conceptos utilizados

En este proyecto se aplican conceptos fundamentales de programación en Python:

* Programación orientada a objetos.
* Clases y objetos.
* Métodos.
* Listas.
* Funciones.
* Estructuras condicionales.
* Bucles `while` y `for`.
* Manejo de excepciones.
* Validación de datos.
* Uso de `lambda`.
* Ordenamiento mediante `sorted()`.
* Máximo común divisor mediante `math.gcd`.

## Autor

Proyecto académico desarrollado en Python.
