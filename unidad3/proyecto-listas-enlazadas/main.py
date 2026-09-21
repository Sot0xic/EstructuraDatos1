import tkinter as tk

from models.lista_enlazada import ListaEnlazada
from views.vista_tareas import VistaTareas
from controllers.controlador_tareas import ControladorTareas


def main():
    # Inicializar la raíz de Tkinter
    root = tk.Tk()
    
    # Instanciar el Modelo (Big pickle)
    modelo = ListaEnlazada()
    
    # Instanciar el Controlador (Big pickle)
    controlador = ControladorTareas(modelo)
    
    # Instanciar la Vista (MusePark 1.2) y pasarle el controlador
    vista = VistaTareas(root, controlador)
    
    # Conectar la vista al controlador
    controlador.set_vista(vista)
    
    # Iniciar el bucle de la aplicación (Orquestado por MusePark 1.3)
    root.mainloop()

if __name__ == "__main__":
    main()