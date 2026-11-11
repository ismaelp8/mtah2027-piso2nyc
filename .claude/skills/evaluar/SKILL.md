---
name: evaluar
description: Valida y puntúa una entrega (CSV frame,label) con el validador y el scorer oficiales, enseñando solo agregados. Úsala con "/evaluar", "¿cuánto saca esto?", "valida la entrega" o antes de entregar.
argument-hint: "[ruta del csv]"
---

# Evaluar una entrega

Entrega: $ARGUMENTS (si viene vacía, pregunta qué fichero; normalmente
`evaluation/results/<nombre>.csv`).

**No leas el CSV ni los informes de `evaluation/reports/`.** Son etiquetas del partido frame a frame
(regla nº 1 de `CLAUDE.md`). Solo ejecutas estos dos scripts oficiales, que imprimen agregados.

1. **El fichero existe** (comprobación sin leerlo):
   ```
   python -c "import os,sys; print(os.path.getsize(sys.argv[1]), 'bytes')" <csv>
   ```
   Si no existe, la entrega la genera la persona en su máquina con nuestro pipeline o con
   `starter/baseline.py`. Tú no ejecutas código que lea `MTAH_DATA_DIR`.
2. **Validar:** `python evaluation/validate_submission.py <csv>`. Explica en dos líneas:
   - **Si sale `FAIL`,** qué falla.
   - **Si sale `OK`,** los recuentos de etiquetas, cuántas posesiones dice y su duración media.
     - Sirve para detectar fragmentación: posesiones de muy pocos segundos de media, o muchas más de las
       que salían en la versión anterior, indican que algo las está partiendo.
     - Como orden de magnitud, la ventana pública tiene 17 posesiones en 5 minutos. Esa ventana no es
       representativa del partido completo, así que no es un objetivo ni se extrapola.
     - El recuento de `X` incluye los frames de fuera de los tramos evaluados, donde la `X` es lo
       normal. Por sí solo no indica nada.
3. **Puntuar en la ventana pública:** `python evaluation/run_evaluation.py`. Puntúa todos los CSV de
   `evaluation/results/`, así que la entrega tiene que estar ahí. Si hay que decidir si una diferencia es
   real, añade `--bootstrap 1000`.
4. **Explicar el resultado.** Enseña solo la fila de esta entrega y la de `baseline_smooth50`, y
   recuerda siempre que:
   - la ventana pública (5 minutos, 17 posesiones) **solo comprueba que el pipeline es correcto**:
     alineación, formato y significado de las etiquetas;
   - **no sirve para elegir entre versiones.** En la ventana gana `smooth125` y en el partido completo
     gana `smooth50`. Para elegir está la validación externa;
   - diferencias de spellF1 de menos de ~0,04 son ruido;
   - en el detalle del scorer, la línea `abstained` cuenta las `X` sobre frames evaluados de la ventana
     pública. Si no es 0, avisa: la `X` solo va fuera de los tramos evaluados.
5. **Si es la entrega final:**
   - el fichero se llama exactamente `<NOMBRE_EQUIPO>.csv`;
   - tiene 199.319 filas;
   - `validate_submission.py` sale en verde **sobre ese mismo fichero**;
   - el repo lo regenera byte a byte con un solo comando: compara el hash de dos ejecuciones con
     `python -c "import hashlib,sys; print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" <csv>`.

   Repasa la checklist de entrega de `CLAUDE.md`.
