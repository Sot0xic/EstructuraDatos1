"""
Punto de entrada del proyecto Tower Defense - Semana 1.

Demuestra el flujo conceptual del juego con las estructuras de datos:

    Oleada -> QUEUE (en espera) -> dequeue() -> LISTA DOBLE (activos)
                                              -> torre elimina enemigo
                                              -> remove del nodo

    STACK -> historial de acciones (base Undo/Redo)

Ejecutar desde la raiz del proyecto:

    python main.py
"""

from Controller.game_controller import GameController


def main():
    controller = GameController()

    print("\n>>> PASO 1: Llega una oleada de enemigos (se encolan en la QUEUE)")
    controller.start_wave(
        [
            {"name": "Goblin", "hp": 60, "speed": 1.2},
            {"name": "Orco", "hp": 120, "speed": 0.8},
            {"name": "Duende", "hp": 40, "speed": 1.5},
            {"name": "Dragon", "hp": 200, "speed": 0.6},
        ]
    )

    print("\n>>> PASO 2: Los enemigos entran al mapa (dequeue -> lista doble)")
    controller.spawn_next()
    controller.spawn_next()

    print("\n>>> PASO 3: Una torre ataca al segundo enemigo activo")
    active = controller.model.active_enemies.to_list()
    target = active[1]
    killed, remaining = controller.attack(target, damage=120)
    print(f"    Resultado del ataque -> eliminado: {killed} | vida restante: {remaining}")

    print("\n>>> PASO 4: Los enemigos restantes de la oleada entran al mapa")
    controller.spawn_all()

    print("\n>>> PASO 5: Historial de acciones (STACK, LIFO)")
    print(f"    Ultima accion registrada: {controller.model.peek_last_action()}")
    last = controller.undo()
    print(f"    undo() recupero: {last}")

    print("\n>>> Estado final del modelo")
    controller.render()


if __name__ == "__main__":
    main()
