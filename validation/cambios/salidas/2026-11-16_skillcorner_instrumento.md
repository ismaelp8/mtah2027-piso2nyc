# El detector de cambios de posesión en SkillCorner frente a `main`

- código: 50b7135 · SkillCorner, mitad de entrenamiento (10 partidos) · bootstrap: 1000
- detector: ninguno (`p` a cero: comprobación del instrumento)
- combinación: w 25 · γ 8 · W 50 · contra el otro equipo
- `main`: B5, `dead_state` y `temporal.decode` (coste 25), sin «cortas a `D`»

## `spellF1` frente a `main`

| `D` | condición | `main` | candidato | diferencia [5–95 %] | gana en | posesiones predichas (`main` / candidato) / reales |
|---|---|---|---|---|---|---|
| de las etiquetas | detectado | 0.519 | 0.519 | +0.000 [+0.000 a +0.000] | 0 de 10 | 2270 / 2270 / 3228 |
| de las etiquetas | detectado, suavizado | 0.514 | 0.514 | +0.000 [+0.000 a +0.000] | 0 de 10 | 2284 / 2284 / 3228 |
| propio | detectado | 0.382 | 0.382 | +0.000 [+0.000 a +0.000] | 0 de 10 | 2342 / 2342 / 3228 |
| propio | detectado, suavizado | 0.378 | 0.378 | +0.000 [+0.000 a +0.000] | 0 de 10 | 2345 / 2345 / 3228 |

## Comprobación del instrumento

- El candidato sin detector sale igual que `main` en todos los frames en 40 de 40 salidas (partido × condición × `D`).
- `main` partido a partido, para compararlo con `validation/skillcorner/medir.py` del 15/11 en estos partidos:

| `D` | condición | `main` | por partido, mín–máx | posesiones predichas / reales |
|---|---|---|---|---|
| de las etiquetas | detectado | 0.519 | 0.451–0.574 | 2270 / 3228 |
| de las etiquetas | detectado, suavizado | 0.514 | 0.444–0.566 | 2284 / 3228 |
| propio | detectado | 0.382 | 0.346–0.432 | 2342 / 3228 |
| propio | detectado, suavizado | 0.378 | 0.345–0.427 | 2345 / 3228 |
