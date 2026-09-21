from math import gcd


class Fraccion:
    """Representa una fracción con numerador y denominador."""

    def __init__(self, numerador, denominador):
        if denominador == 0:
            raise ValueError("El denominador no puede ser cero.")

        self.numerador = numerador
        self.denominador = denominador
        self.simplificar()

    def simplificar(self):
        """Simplifica la fracción usando el máximo común divisor."""
        divisor = gcd(self.numerador, self.denominador)

        self.numerador //= divisor
        self.denominador //= divisor

        if self.denominador < 0:
            self.numerador *= -1
            self.denominador *= -1

    def sumar(self, otra):
        """Suma esta fracción con otra."""
        numerador = (
            self.numerador * otra.denominador
            + otra.numerador * self.denominador
        )
        denominador = self.denominador * otra.denominador

        return Fraccion(numerador, denominador)

    def restar(self, otra):
        """Resta otra fracción de esta fracción."""
        numerador = (
            self.numerador * otra.denominador
            - otra.numerador * self.denominador
        )
        denominador = self.denominador * otra.denominador

        return Fraccion(numerador, denominador)

    def multiplicar(self, otra):
        """Multiplica esta fracción por otra."""
        numerador = self.numerador * otra.numerador
        denominador = self.denominador * otra.denominador

        return Fraccion(numerador, denominador)

    def dividir(self, otra):
        """Divide esta fracción entre otra."""
        if otra.numerador == 0:
            raise ZeroDivisionError(
                "No se puede dividir entre una fracción igual a cero."
            )

        numerador = self.numerador * otra.denominador
        denominador = self.denominador * otra.numerador

        return Fraccion(numerador, denominador)

    def valor(self):
        """Devuelve el valor decimal de la fracción."""
        return self.numerador / self.denominador

    def __str__(self):
        """Devuelve la fracción en formato numerador/denominador."""
        return f"{self.numerador}/{self.denominador}"


def ingresar_fraccion():
    """Solicita al usuario una fracción en formato numerador/denominador."""
    while True:
        entrada = input(
            "Ingrese una fracción (numerador/denominador): "
        ).strip()

        try:
            partes = entrada.split("/")

            if len(partes) != 2:
                raise ValueError

            numerador = int(partes[0].strip())
            denominador = int(partes[1].strip())

            return Fraccion(numerador, denominador)

        except ValueError:
            print(
                "Entrada inválida. Use el formato numerador/denominador."
            )


def calculadora():
    """Realiza operaciones aritméticas entre dos fracciones."""
    print("\n===== CALCULADORA DE FRACCIONES =====")

    fraccion_1 = ingresar_fraccion()
    fraccion_2 = ingresar_fraccion()

    print("\nFracción 1:", fraccion_1)
    print("Fracción 2:", fraccion_2)

    while True:
        print("\n----- OPERACIONES -----")
        print("1. Sumar")
        print("2. Restar")
        print("3. Multiplicar")
        print("4. Dividir")
        print("5. Volver al menú principal")

        opcion = input("Seleccione una opción: ").strip()

        try:
            if opcion == "1":
                resultado = fraccion_1.sumar(fraccion_2)
                print(f"\nResultado: {fraccion_1} + {fraccion_2}"
                      f" = {resultado}")

            elif opcion == "2":
                resultado = fraccion_1.restar(fraccion_2)
                print(f"\nResultado: {fraccion_1} - {fraccion_2}"
                      f" = {resultado}")

            elif opcion == "3":
                resultado = fraccion_1.multiplicar(fraccion_2)
                print(f"\nResultado: {fraccion_1} * {fraccion_2}"
                      f" = {resultado}")

            elif opcion == "4":
                resultado = fraccion_1.dividir(fraccion_2)
                print(f"\nResultado: {fraccion_1} / {fraccion_2}"
                      f" = {resultado}")

            elif opcion == "5":
                break

            else:
                print("Opción inválida.")

        except ZeroDivisionError as error:
            print(f"\nError: {error}")


def comparar_fracciones():
    """Permite ingresar y ordenar múltiples fracciones."""
    print("\n===== COMPARADOR DE FRACCIONES =====")

    while True:
        try:
            cantidad = int(
                input("¿Cuántas fracciones desea ingresar?: ")
            )

            if cantidad < 2:
                print("Debe ingresar al menos 2 fracciones.")
                continue

            break

        except ValueError:
            print("Ingrese un número entero válido.")

    fracciones = []

    for numero in range(1, cantidad + 1):
        print(f"\nFracción {numero}:")
        fracciones.append(ingresar_fraccion())

    print("\nFracciones ingresadas:")

    for fraccion in fracciones:
        print(fraccion)

    while True:
        print("\n----- ORDENAR FRACCIONES -----")
        print("1. De menor a mayor")
        print("2. De mayor a menor")
        print("3. Volver al menú principal")

        opcion = input("Seleccione una opción: ").strip()

        if opcion == "1":
            ordenadas = sorted(fracciones, key=lambda fraccion: fraccion.valor())

            print("\nDe menor a mayor:")
            for fraccion in ordenadas:
                print(fraccion)

        elif opcion == "2":
            ordenadas = sorted(
                fracciones,
                key=lambda fraccion: fraccion.valor(),
                reverse=True
            )

            print("\nDe mayor a menor:")
            for fraccion in ordenadas:
                print(fraccion)

        elif opcion == "3":
            break

        else:
            print("Opción inválida.")


def mostrar_menu():
    """Muestra el menú principal."""
    while True:
        print("\n==============================")
        print("   PROYECTO: FRACCIONES")
        print("==============================")
        print("1. Calculadora de fracciones")
        print("2. Comparar y ordenar fracciones")
        print("3. Salir")

        opcion = input("Seleccione una opción: ").strip()

        if opcion == "1":
            calculadora()

        elif opcion == "2":
            comparar_fracciones()

        elif opcion == "3":
            print("\nPrograma finalizado.")
            break

        else:
            print("\nOpción inválida. Intente nuevamente.")


if __name__ == "__main__":
    mostrar_menu()