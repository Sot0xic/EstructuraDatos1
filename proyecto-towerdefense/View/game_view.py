"""
Vista del Tower Defense (Semana 1).

Durante la primera semana la prioridad es el modelo y las estructuras
de datos; la interfaz grafica con Pygame se integrara en etapas
posteriores. Por ahora se proporciona una vista de texto que muestra
el estado de las estructuras (cola, lista doble y pila).
"""


class GameView:
    """Vista basica en consola del estado del modelo."""

    def __init__(self, output=print):
        self._output = output

    def render(self, model):
        """Muestra el estado completo del modelo. O(n) por la impresion."""
        state = model.get_state()

        self._output("=" * 50)
        self._output(" TOWER DEFENSE - Estado de estructuras (Semana 1)")
        self._output("=" * 50)

        self._output("\n[QUEUE] Enemigos esperando (FIFO):")
        if state["pending"]:
            for i, enemy in enumerate(state["pending"], start=1):
                self._output(f"   {i}. {enemy}")
        else:
            self._output("   (vacia)")

        self._output("\n[DOUBLY LINKED LIST] Enemigos activos en el mapa:")
        if state["active"]:
            for enemy in state["active"]:
                self._output(f"   - {enemy}")
        else:
            self._output("   (vacia)")

        self._output("\n[STACK] Historial de acciones (LIFO):")
        if state["history"]:
            for action in state["history"]:
                self._output(f"   - {action[0]}: {action[1]}")
        else:
            self._output("   (vacia)")

        self._output(
            f"\nResumen -> pendientes: {model.pending_count} | "
            f"activos: {model.active_count} | "
            f"acciones: {model.history_count}"
        )
        self._output("-" * 50)
