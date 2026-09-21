class ControladorTareas:
    def __init__(self, modelo):
        self.modelo = modelo
        self.vista = None

    def set_vista(self, vista):
        self.vista = vista
        self.actualizar_vista()

    def agregar_tarea(self):
        datos = self.vista.obtener_input().strip()
        if datos:
            self.modelo.agregar_tarea(datos)
            self.vista.limpiar_input()
            self.actualizar_vista()
        else:
            self.vista.mostrar_mensaje("Error", "La descripción de la tarea no puede estar vacía.", "error")

    def completar_tarea(self):
        tarea_seleccionada = self.vista.obtener_tarea_seleccionada()
        if tarea_seleccionada:
            exito = self.modelo.marcar_completada(tarea_seleccionada)
            if exito:
                self.actualizar_vista()
            else:
                self.vista.mostrar_mensaje("Error", "No se pudo actualizar el estado de la tarea.", "error")
        else:
            self.vista.mostrar_mensaje("Advertencia", "Por favor, selecciona una tarea primero.", "advertencia")

    def eliminar_tarea(self):
        tarea_seleccionada = self.vista.obtener_tarea_seleccionada()
        if tarea_seleccionada:
            exito = self.modelo.eliminar_tarea(tarea_seleccionada)
            if exito:
                self.actualizar_vista()
            else:
                self.vista.mostrar_mensaje("Error", "No se pudo eliminar la tarea.", "error")
        else:
            self.vista.mostrar_mensaje("Advertencia", "Por favor, selecciona una tarea primero.", "advertencia")

    def actualizar_vista(self):
        tareas = self.modelo.obtener_tareas()
        self.vista.actualizar_lista(tareas)