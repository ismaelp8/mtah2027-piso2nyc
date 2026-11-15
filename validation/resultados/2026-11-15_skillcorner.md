# ¿Aguanta B5 con un tracking automático? 20 partidos de SkillCorner · 2026-11-15 · Claude (sesión de Ismael)

- **Fecha y quién:** 15/11/2026. Lo pidió Ismael tras la revisión externa («empieza por SkillCorner como
  validación»). Lo escribió y lo ejecutó Claude.
- **Datos:** los 20 partidos abiertos de SkillCorner de la A-League 2024/25
  (https://github.com/SkillCorner/opendata, commit `4340d2745728`, licencia MIT), con el sha256 de cada
  tracking comprobado contra su puntero LFS. Tracking **automático** de la retransmisión, a 10 fps. Nada del
  partido del reto.
- **Código:** `validation/skillcorner/` (`descargar.py`, `lector.py`, `prueba_lector.py` y `medir.py`) sobre
  `main` en `05b6d98`, sin tocar `possession/`. B5 y `dead_state` van con los coeficientes de la entrega
  (los 7 partidos de la DFL): **nunca han visto estos partidos**.
- **Comandos:**
  - `python validation/skillcorner/descargar.py` (unos 1,8 GB, 3 minutos);
  - `python validation/skillcorner/prueba_lector.py` (`TODO BIEN`);
  - `python validation/skillcorner/medir.py --bootstrap 1000` (unos 7 minutos).
- **Para qué:** el harness de la DFL usa tracking limpio y revisado. El partido es tracking automático.
  Faltaba saber si la ventaja de B5 aguanta con un tracking automático.
- **Regla de lectura:** `validation/skillcorner/BITACORA.md` §6, escrita antes de puntuar ningún método.
  Antes solo se miraron recuentos de un partido para fijar las etiquetas (§2). Esta revisión no subió la
  regla a git antes de medir: el historial no lo demuestra.

**Lectura en tres líneas:**

1. **B5 aguanta con tracking automático** [medido, con la regla]. Con el `D` oráculo, `main` gana al
   baseline por +0,131 y +0,135 en 20 de 20 partidos, y a N1 por +0,059 y +0,065 en 19 de 20, en las dos
   condiciones que votan. N1 también gana al baseline (+0,07).
2. **La ventaja de B5 sobre N1 depende de ver a todos los jugadores** [medido, sin voto]. Con solo los
   jugadores que la retransmisión detecta (15 de mediana, frente a 22), baja a +0,028 en 17 de 20. El ATD ve
   20,5 objetos de media: está más cerca de «todos».
3. **Dos cosas descriptivas, bajo D21** (comparan con cifras oficiales):
   - con el `D` propio, el baseline saca aquí 0,249 y 0,248, muy cerca del 0,2433 del partido; `main` saca
     0,381 y 0,377;
   - la huella de retrasos de las etiquetas de SkillCorner a 25 frames es 0,678, la más cercana a la
     oficial (0,654) de todas las que se han medido (DFL: 0,552 con el flag y 0,808 con control).

## Lo que dice y lo que no

- **[medido] La regla se cumple** en los dos puntos. B5 se puede entregar con más confianza que ayer: su
  ventaja ya no sale solo de la DFL.
- **[medido, sin voto] Suavizar el balón casi no cambia nada** (0,514 → 0,509 para `main`). Con el balón
  estimado de SkillCorner, B5 sube algo frente a N1 (+0,077).
- **[medido] El balón se ve en el 92,8 % de los frames de juego y en el 20,8 % de los `D`** con la
  condición «detectado». En la ventana pública del ATD se ve el 93,5 % del juego (experimento 2).
- **[inferencia] Sobre el nivel en el partido.** Con el `D` propio, el baseline saca aquí casi lo mismo que
  en el partido (0,249 frente a 0,2433). Si SkillCorner con el `D` propio se parece al partido en dificultad,
  `main` estaría en torno a 0,38. Coincide con el centro del rango de 0,30 a 0,50 de la revisión externa
  (§3.2). No es una medida del partido: otra liga, otras etiquetas, otro tracking y otro `D`.
  - Cuidado con el `D` propio de aquí: el balón no se tapa en los `D` (se ve en el 20,8 %), los `D` largos
    suelen ser repeticiones sin tracking, y no hay Smart Tagging, así que `dead_ball` no entra.
- **[inferencia] Sobre la convención.** Las etiquetas de SkillCorner (su posesión exige control) tienen
  6,05 posesiones por minuto vivo, entre el control (4,71) y el flag (8,30) de la DFL. Su huella cae cerca de
  la oficial. Es coherente con lo que decía la revisión externa (§3.2, punto 8): la GT del reto estaría
  entre las dos convenciones de la DFL. Descriptivo: no elige nada.
- **Lo que no dice:**
  - nada del partido del reto: no se ha tocado;
  - nada del `D` de verdad con el balón ni del Smart Tagging;
  - si la ventaja de B5 aguantaría con el ATD exactamente: el ATD es una cámara táctica que ve todo el campo,
    y SkillCorner es retransmisión, con jugadores fuera de plano estimados.

## Discrepancia apuntada

`BITACORA.md` §6 pide ganar en «17 de 20 o más». `medir.py` aplicó en esta ejecución 18 de 20 (la proporción
de 6 de 7 redondeada hacia arriba), que es más estricto. Los resultados (20 de 20 y 19 de 20) pasan con los
dos, así que el veredicto no cambia. Se corrigió `medir.py` después para que aplique el 17 escrito; la salida
de abajo es la de la ejecución original.

## Salida, tal cual

`python validation/skillcorner/medir.py --bootstrap 1000` (las líneas de progreso, que van a stderr, no se
copian):

```text
partidos: 20 · bootstrap: 1000 · código: pipeline de main, B5 y dead_state con los coeficientes de la entrega

### Las etiquetas (convención de SkillCorner)

- posesiones: 6380 · 6.05 por minuto vivo · frames `D`: 46.5 % · frames de las partes sin etiqueta: 0.03 %
- huella de retrasos 1 / 3 / 8 / 25 frames: 0.9969 / 0.9770 / 0.8938 / 0.6782
  (DFL flag 0,5522 · oficial 0,6539 · DFL control 0,8082 a 25 frames; descriptivo)

| condición | ¿vota? | balón visible en los frames vivos | balón visible en los `D` |
|---|---|---|---|
| detectado | sí | 92.8 % | 20.8 % |
| detectado, suavizado | sí | 92.8 % | 20.8 % |
| con el estimado | no | 98.3 % | 46.5 % |
| solo jugadores detectados | no | 92.8 % | 20.8 % |

### `D` oraculo (decide)

| balón y jugadores | versión | spellF1, 20 partidos | por partido, mín–máx | frente al control [5–95 %] · gana en | frente a N1 [5–95 %] · gana en | posesiones predichas / reales |
|---|---|---|---|---|---|---|
| detectado | control: voto ±50 | 0.383 | 0.320–0.470 | – | -0.073 [-0.078 a -0.067] · 0 de 20 | 7943 / 6380 |
| detectado | N1, coste 25 | 0.455 | 0.401–0.506 | +0.073 [+0.067 a +0.078] · 20 de 20 | – | 5041 / 6380 |
| detectado | main (B5, coste 25) | 0.514 | 0.444–0.574 | +0.131 [+0.123 a +0.139] · 20 de 20 | +0.059 [+0.051 a +0.067] · 19 de 20 | 4553 / 6380 |
| detectado, suavizado | control: voto ±50 | 0.374 | 0.311–0.450 | – | -0.070 [-0.075 a -0.065] · 0 de 20 | 8284 / 6380 |
| detectado, suavizado | N1, coste 25 | 0.444 | 0.388–0.504 | +0.070 [+0.065 a +0.075] · 20 de 20 | – | 5246 / 6380 |
| detectado, suavizado | main (B5, coste 25) | 0.509 | 0.434–0.566 | +0.135 [+0.127 a +0.142] · 20 de 20 | +0.065 [+0.057 a +0.073] · 19 de 20 | 4615 / 6380 |
| con el estimado (sin voto) | control: voto ±50 | 0.389 | 0.326–0.465 | – | -0.052 [-0.057 a -0.047] · 0 de 20 | 7755 / 6380 |
| con el estimado (sin voto) | N1, coste 25 | 0.441 | 0.397–0.501 | +0.052 [+0.047 a +0.057] · 20 de 20 | – | 5320 / 6380 |
| con el estimado (sin voto) | main (B5, coste 25) | 0.518 | 0.455–0.583 | +0.129 [+0.121 a +0.136] · 20 de 20 | +0.077 [+0.069 a +0.085] · 20 de 20 | 4565 / 6380 |
| solo jugadores detectados (sin voto) | control: voto ±50 | 0.383 | 0.324–0.464 | – | -0.073 [-0.078 a -0.067] · 0 de 20 | 8078 / 6380 |
| solo jugadores detectados (sin voto) | N1, coste 25 | 0.456 | 0.394–0.510 | +0.073 [+0.067 a +0.078] · 20 de 20 | – | 5104 / 6380 |
| solo jugadores detectados (sin voto) | main (B5, coste 25) | 0.484 | 0.419–0.541 | +0.101 [+0.094 a +0.107] · 20 de 20 | +0.028 [+0.020 a +0.036] · 17 de 20 | 5216 / 6380 |

### `D` propio (descriptivo)

| balón y jugadores | versión | spellF1, 20 partidos | por partido, mín–máx | frente al control [5–95 %] · gana en | frente a N1 [5–95 %] · gana en | posesiones predichas / reales |
|---|---|---|---|---|---|---|
| detectado | control: voto ±50 | 0.249 | 0.187–0.327 | – | -0.083 [-0.089 a -0.078] · 0 de 20 | 9951 / 6380 |
| detectado | N1, coste 25 | 0.332 | 0.274–0.380 | +0.083 [+0.078 a +0.089] · 20 de 20 | – | 5326 / 6380 |
| detectado | main (B5, coste 25) | 0.381 | 0.330–0.432 | +0.132 [+0.124 a +0.139] · 20 de 20 | +0.048 [+0.042 a +0.054] · 20 de 20 | 4610 / 6380 |
| detectado, suavizado | control: voto ±50 | 0.248 | 0.183–0.317 | – | -0.078 [-0.084 a -0.073] · 0 de 20 | 10056 / 6380 |
| detectado, suavizado | N1, coste 25 | 0.326 | 0.265–0.380 | +0.078 [+0.073 a +0.084] · 20 de 20 | – | 5486 / 6380 |
| detectado, suavizado | main (B5, coste 25) | 0.377 | 0.334–0.427 | +0.129 [+0.121 a +0.136] · 20 de 20 | +0.051 [+0.045 a +0.057] · 19 de 20 | 4652 / 6380 |
| con el estimado (sin voto) | control: voto ±50 | 0.246 | 0.181–0.322 | – | -0.075 [-0.081 a -0.069] · 0 de 20 | 8729 / 6380 |
| con el estimado (sin voto) | N1, coste 25 | 0.321 | 0.275–0.370 | +0.075 [+0.069 a +0.081] · 20 de 20 | – | 5673 / 6380 |
| con el estimado (sin voto) | main (B5, coste 25) | 0.378 | 0.339–0.432 | +0.132 [+0.125 a +0.139] · 20 de 20 | +0.058 [+0.051 a +0.063] · 20 de 20 | 4663 / 6380 |
| solo jugadores detectados (sin voto) | control: voto ±50 | 0.248 | 0.184–0.327 | – | -0.061 [-0.066 a -0.055] · 0 de 20 | 10247 / 6380 |
| solo jugadores detectados (sin voto) | N1, coste 25 | 0.309 | 0.266–0.359 | +0.061 [+0.055 a +0.066] · 20 de 20 | – | 5207 / 6380 |
| solo jugadores detectados (sin voto) | main (B5, coste 25) | 0.343 | 0.301–0.398 | +0.095 [+0.088 a +0.101] · 20 de 20 | +0.034 [+0.028 a +0.041] · 18 de 20 | 5308 / 6380 |

### Regla de BITACORA.md §6 (`D` oráculo, condiciones que votan: detectado, detectado, suavizado)

- «B5 aguanta con tracking automático» (main frente al control): **sí**
- «La ventaja de B5 sobre N1 aguanta» (main frente a N1): **sí**
- (descriptivo) N1 frente al control: **sí**
  Gana: +0.03 o más con los partidos juntos, en 18 de 20 o más y con el intervalo por encima de cero, en las dos condiciones que votan.
```
