class Punto:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __str__(self):
        return f"({self.x}, {self.y})"


class Circunferencia:
    def __init__(self, centro, radio):
        # Creamos una copia independiente del punto original
        self.centro = Punto(centro.x, centro.y)
        self.radio = radio

    def __str__(self):
        return (
            f"Circunferencia con centro en {self.centro} "
            f"y radio {self.radio}"
        )


# Prueba del alumno
mi_punto_original = Punto(1, 2)
mi_circunferencia = Circunferencia(mi_punto_original, 5)

print(f"Circunferencia inicial: {mi_circunferencia}")

# El alumno modifica el punto original
mi_punto_original.x = 10
mi_punto_original.y = 20

print(
    "Circunferencia después de modificar el punto original: "
    f"{mi_circunferencia}"
)
