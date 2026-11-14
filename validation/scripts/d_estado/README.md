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
| `referencia_agregado4.py` | cómo se mueven los jugadores en la DFL, tal cual y con un temblor añadido, en las mismas dos líneas que imprime `validation/partido/agregados_jugadores.py` en su punto 4. Es con lo que se compara la salida del partido para saber si el modelo se traslada al ATD |
| `traslado_atd.py` | la referencia de la DFL **partido a partido** para leer los puntos 4 y 6 de `validation/partido/agregados_jugadores.py` (velocidades, jugadores fuera del campo y slots vistos), y qué hace la pieza si faltan jugadores a ratos. Con ella se fijaron los umbrales de `validation/resultados/2026-11-14_agregados_jugadores_atd.md` |

## Cómo se ejecutan

Hace falta la caché de los 7 partidos de la DFL (`validation/harness/README.md`) y, además de lo del
pipeline, `lxml` para crear la caché y `scikit-learn` para entrenar y medir. Ninguno de los dos está en
`requirements.txt`: el pipeline no los usa.

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
python validation/scripts/d_estado/referencia_agregado4.py
```

```bash
python validation/scripts/d_estado/traslado_atd.py
```

`medir.py` tarda unos minutos con los 7 partidos. Con `--sin-sensibilidad` hace solo la medida principal.

## Cómo se cambia el modelo

1. Escribe antes en `docs/decisiones.md` qué candidato nuevo vas a comparar y con qué regla.
2. Añade sus rasgos a `FEATURES` en `possession/dead_state.py` y el candidato a `CANDIDATOS` en
   `entrenar.py` y a `ORDEN` en `medir.py`.
3. Ejecuta `medir.py`. Si gana, pon su nombre en `ELEGIDO` (`entrenar.py`), ejecuta `entrenar.py` y copia
   el `MODEL` que imprime a `possession/dead_state.py`.
4. Ejecuta `entrenar.py --comprobar` y `python validation/scripts/prueba_pipeline.py`.
