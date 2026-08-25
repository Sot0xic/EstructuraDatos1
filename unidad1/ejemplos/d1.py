# fixed: code
original_data = [10, 20, 30]

# El estudiante intenta copiar los datos
copy_data = original_data.copy()  
# Usar copy() para crear una copia independiente

copy_data.append(40)

print(f"Original: {original_data}")
print(f"Copia: {copy_data}")

# El código tenía un error porque el estudiante intentaba modificar la lista original al agregar un elemento a la copia. Al usar copy(), se crea una copia independiente de la lista original, por lo que la lista original permanece sin cambios.