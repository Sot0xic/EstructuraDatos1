Necesito corregir únicamente la posición del título "PAUSE" dentro del menú de pausa de mi Tower Defense.

**Problema actual:**

El texto "PAUSE" aparece en el centro del marco de madera, en lugar de aparecer encima del botón RESUME.

Los botones RESUME y EXIT ya funcionan correctamente. No quiero modificar su funcionalidad.

## Distribución exacta que quiero

Dentro del mismo marco de madera, los elementos deben aparecer verticalmente en este orden:

PAUSE

RESUME

EXIT

Todos deben estar centrados horizontalmente respecto al marco, con separación suficiente para que no se superpongan.

## Indicaciones técnicas

1. Revisa cómo se calcula actualmente la posición del texto PAUSE.
2. No utilices `panel_rect.center` para posicionar el título, porque eso lo coloca en el centro vertical del panel.
3. Utiliza una posición relativa a la parte superior del marco, por ejemplo `panel_rect.top + margen_superior`.
4. Centra horizontalmente el título utilizando `panel_rect.centerx`.
5. Coloca RESUME debajo del título y EXIT debajo de RESUME, dejando márgenes consistentes.
6. Calcula las posiciones en función de las dimensiones reales del panel, los botones y el texto.
7. Verifica que los tres elementos queden completamente dentro del área interior del marco, sin tocar sus bordes.
8. Si hace falta, ajusta ligeramente el tamaño del marco, pero evita deformar sus elementos decorativos.
9. Mantén las hitboxes de RESUME y EXIT alineadas con sus posiciones visuales.

## Importante

- No modifiques la lógica de pausa.
- No cambies el comportamiento de Escape.
- No alteres los temporizadores ni la lógica del juego.
- No cambies los recursos gráficos de `wooden_gui`.
- No agregues nuevos botones.
- Realiza únicamente los ajustes visuales necesarios.

Al terminar, explícame qué coordenada provocaba que PAUSE apareciera en el centro y cómo corregiste su posición.