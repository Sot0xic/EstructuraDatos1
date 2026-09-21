import tkinter as tk
from tkinter import messagebox

class VistaTareas:
    def __init__(self, root, controlador):
        self.root = root
        self.controlador = controlador
        self.root.title("Gestor de Tareas - Listas Enlazadas")
        self.root.geometry("400x450")
        
        self.crear_widgets()

    def crear_widgets(self):
        # Entrada de texto
        frame_input = tk.Frame(self.root)
        frame_input.pack(pady=10)
        
        self.entry_tarea = tk.Entry(frame_input, width=30)
        self.entry_tarea.pack(side=tk.LEFT, padx=5)
        
        btn_agregar = tk.Button(frame_input, text="Agregar", command=self.controlador.agregar_tarea)
        btn_agregar.pack(side=tk.LEFT)

        # Lista de tareas
        self.listbox_tareas = tk.Listbox(self.root, width=45, height=15)
        self.listbox_tareas.pack(pady=10)

        # Botones de acción
        frame_botones = tk.Frame(self.root)
        frame_botones.pack(pady=5)
        
        btn_completar = tk.Button(frame_botones, text="Marcar Completada", command=self.controlador.completar_tarea)
        btn_completar.pack(side=tk.LEFT, padx=5)
        
        btn_eliminar = tk.Button(frame_botones, text="Eliminar Tarea", command=self.controlador.eliminar_tarea)
        btn_eliminar.pack(side=tk.LEFT, padx=5)

    def obtener_input(self):
        return self.entry_tarea.get()

    def limpiar_input(self):
        self.entry_tarea.delete(0, tk.END)

    def obtener_tarea_seleccionada(self):
        seleccion = self.listbox_tareas.curselection()
        if seleccion:
            texto_completo = self.listbox_tareas.get(seleccion[0])
            # Extraer solo el nombre de la tarea, quitando el estado " [pendiente]" o " [completada]"
            tarea = texto_completo.rsplit(' [', 1)[0]
            return tarea
        return None

    def actualizar_lista(self, tareas):
        self.listbox_tareas.delete(0, tk.END)
        for tarea in tareas:
            texto = f"{tarea['datos']} [{tarea['estado']}]"
            self.listbox_tareas.insert(tk.END, texto)
            
            # Colorear según el estado
            if tarea['estado'] == 'completada':
                self.listbox_tareas.itemconfig(tk.END, {'fg': 'green'})
            else:
                self.listbox_tareas.itemconfig(tk.END, {'fg': 'black'})

    def mostrar_mensaje(self, titulo, mensaje, tipo="info"):
        if tipo == "error":
            messagebox.showerror(titulo, mensaje)
        elif tipo == "advertencia":
            messagebox.showwarning(titulo, mensaje)
        else:
            messagebox.showinfo(titulo, mensaje)