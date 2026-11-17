"""
Punto de entrada del programa.

Crea las tres piezas de la arquitectura MVC y las une:
Vista  ->  Controlador  ->  Modelo

Ejecutar con:  python main.py
"""

import tkinter as tk

from controllers.estudiante_controller import EstudianteController
from views.estudiante_view import EstudianteView


def main():
    # Modelo: lo crea el controlador (no lo necesita la vista directamente).
    controlador = EstudianteController()

    # Vista: recibe el controlador para enviarle las acciones del usuario.
    root = tk.Tk()
    vista = EstudianteView(root, controlador)

    vista.ejecutar()


if __name__ == "__main__":
    main()
