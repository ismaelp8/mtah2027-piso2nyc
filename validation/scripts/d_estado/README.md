# Estado de balón muerto (`D`) con jugadores: entrenamiento y medida

Los scripts del modelo de `possession/dead_state.py`. Ninguno lee datos del partido: solo los 7 partidos
abiertos de la Bundesliga (Bassek et al., 2025, CC BY 4.0). Los puede ejecutar cualquiera, Claude
incluido, y solo imprimen agregados y coeficientes.

- Qué se compara y con qué regla se lee: `docs/decisiones.md`, entrada del 14/11 «estado con jugadores:
  candidatos y regla de lectura, escritos antes de medir».
- Resultado: `validation/resultados/2026-11-14_d_estado.md`.

| script | qué hace |
|---|---|
| `entrenar.py` | ajusta la regresión logística (`D` frente a juego) con los rasgos de `dead_state.features` e imprime el `MODEL` que va escrito en el módulo. Con `--comprobar` dice si el `MODEL` del módulo es el que sale de aquí. Es el único sitio donde se usa `scikit-learn` |
| `medir.py` | mide los tres candidatos (E1, E2 y E3) dejando un partido fuera: AUC por frame, el criterio del 13/11 por parada, el `spellF1` oficial con el equipo oráculo frente al control, el placebo y la sensibilidad |
| `prueba_d_estado.py` | prueba la pieza con un partido inventado, sin cargar ninguno de verdad: que no mira fuera de los tramos evaluados (lo que haya fuera no cambia la puntuación de dentro, y donde fuera no hay datos, como en la DFL, el resultado es el de siempre, bit a bit) y que la opción de escala hace lo que dice. No necesita la caché ni `scikit-learn` |
| `referencia_agregado4.py` | cómo se mueven los jugadores en la DFL, tal cual y con un temblor añadido, en las mismas dos líneas que imprime `validation/partido/agregados_jugadores.py` en su punto 4. Es con lo que se compara la salida del partido para saber si el modelo se traslada al ATD |
| `retraso_transicion.py` | con cuánto retraso pasa el modelo E2 de parado a juego al acabar una parada, por tipo de reinicio de los eventos de la DFL, dejando un partido fuera. Es la medida de los retrasos que se restan al ancla del instante del reinicio (`DFL_DELAY` de `validation/partido/agregados_instante_reinicio.py`): los tipos con 50 paradas o más con transición y la mediana positiva |
| `traslado_atd.py` | la referencia de la DFL **partido a partido** para leer los puntos 4 y 6 de `validation/partido/agregados_jugadores.py` (velocidades, jugadores fuera del campo y slots vistos), y qué hace la pieza si faltan jugadores a ratos. Con ella se fijaron los umbrales de `validation/resultados/2026-11-14_agregados_jugadores_atd.md` |

## Cómo se ejecutan

Hace falta la caché de los 7 partidos de la DFL (`validation/harness/README.md`) y, además de lo del
pipeline, `lxml` para crear la caché y `scikit-learn` para entrenar y medir. Ninguno de los dos está en
`requirements.txt`: el pipeline no los usa.

El `MODEL` del módulo se entrenó el 14/11 con `scikit-learn` 1.7.2, `numpy` 2.2.4, `scipy` 1.15.3 y Python
3.10.12. `entrenar.py` imprime las versiones que usa cada vez.

```bash
python validation/scripts/d_estado/medir.py
```

```bash
python validation/scripts/d_estado/entrenar.py
```

```bash
python validation/scripts/d_estado/entrenar.py --comprobar
```

```bash
python validation/scripts/d_estado/prueba_d_estado.py
```

```bash
python validation/scripts/d_estado/referencia_agregado4.py
```

```bash
python validation/scripts/d_estado/traslado_atd.py
```

```bash
python validation/scripts/d_estado/retraso_transicion.py
```

`medir.py` tarda unos minutos con los 7 partidos. Con `--sin-sensibilidad` hace solo la medida principal.

## Cómo se cambia el modelo

1. Escribe antes en `docs/decisiones.md` qué candidato nuevo vas a comparar y con qué regla.
2. Añade sus rasgos a `FEATURES` en `possession/dead_state.py` y el candidato a `CANDIDATOS` en
   `entrenar.py` y a `ORDEN` en `medir.py`.
3. Ejecuta `medir.py`. Si gana, pon su nombre en `ELEGIDO` (`entrenar.py`), ejecuta `entrenar.py` y copia
   el `MODEL` que imprime a `possession/dead_state.py`.
4. Ejecuta `entrenar.py --comprobar`, `prueba_d_estado.py` y `python validation/scripts/prueba_pipeline.py`.
