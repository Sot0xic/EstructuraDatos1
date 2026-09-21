# Proyecto de Gestor de Tareas con Listas Enlazadas

Este proyecto es una aplicación de escritorio desarrollada en Python con una interfaz gráfica en Tkinter. Su propósito es gestionar una lista de tareas (To-Do List) utilizando una **Lista Enlazada Simple** como estructura de datos principal, aplicando el patrón de arquitectura **MVC (Modelo-Vista-Controlador)**.

## 👥 Forma de Trabajo y Equipo

El desarrollo ha sido simulado mediante un entorno colaborativo de IA:
*   **MusePark 1.3**: Orquestador principal, toma de decisiones, QA y control de calidad.
*   **MusePark 1.2**: Responsable de la carpeta Views, encargado de la UI/UX con Tkinter.
*   **Big pickle**: Encargado de la lógica del proyecto, algoritmos de listas enlazadas (Models) y el puente de comunicación (Controllers).

## 🏗️ Estructura del Nodo (Lista Enlazada)
Cada nodo de la lista contiene:
*   `datos`: Cadena de texto con la descripción de la tarea.
*   `estado`: String que indica si está `'pendiente'` o `'completada'`.
*   `siguiente`: Puntero al siguiente nodo en la memoria.

## 📂 Arquitectura MVC
El proyecto está dividido en los siguientes módulos:
*   `models.py` (Model): Contiene la lógica pura de la estructura de datos (`Nodo` y `ListaEnlazada`).
*   `views.py` (View): Contiene la clase `VistaTareas` que renderiza la ventana, botones y listas de Tkinter.
*   `controllers.py` (Controller): Contiene `ControladorTareas`, que gestiona las acciones del usuario, actualiza el modelo y refresca la vista, manejando además las excepciones (ej. campos vacíos).
*   `main.py`: Punto de entrada que inicializa las tres partes y arranca la aplicación.


