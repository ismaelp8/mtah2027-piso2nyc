# Temblor del balón en la DFL según σ (condición 5 de la puerta 1b) · 2026-11-16 · Claude (sesión de Ismael)

- **Para qué:** la calibración que pide la condición 5 de la puerta 1b (`validation/balon_video/BITACORA.md`,
  «Corrección de la puerta 1b»): para elegir la σ de la celda que se lee, «el menor de la rejilla cuyo temblor en la DFL
  (calibrado con la misma función) es igual o mayor que el que mide la 1b». Da el temblor de la DFL para cada σ con la
  misma función que usa el sondeo, `validation/experimento2/instrumento.py: temblor`.
- **Datos:** los 7 partidos abiertos de la Bundesliga (Bassek et al., 2025, CC BY 4.0), caché del experimento 0, con
  `validation/harness/dfl.py` (balón `limpio` y, como referencia, «como el ATD»). Nada del partido.
- **Comando:** `python validation/balon_video/calibrar_temblor_dfl.py --json validation/balon_video/salidas/2026-11-16_calibracion_temblor_dfl.json`
  (Python 3.14.7, numpy 2.5.4; repo en `48f29cf`, script sin commitear con sha256 `872d6ab6…aa112be1f`). Dos
  ejecuciones dan la misma salida (salvo la línea del tiempo). Rehecha el 16/11 tras una revisión: σ = 0 ya no cuenta
  como σ de la rejilla (la emulación no tiene celdas con σ = 0); ningún temblor cambia, solo la columna «en la rejilla»
  de la fila «limpio» y `sigmas_rejilla` del JSON, que ahora es [0,03, 0,06, 0,12, 0,25]. La tabla de los 7 juntos va también en
  `2026-11-16_calibracion_temblor_dfl.json`, para que el sondeo no tenga que leer este markdown.
- **Cómo:** frames de juego (`H` o `A` en el flag), cada parte por separado; la mediana de los 7 juntos es la de todos
  los valores |b[t+1] − 2·b[t] + b[t−1]| (no la media de las medianas), y el script comprueba que parte a parte da
  exactamente `instrumento.temblor`. Ruido N(0, σ²) por eje y frame, una tirada por partido escalada por σ.
- **Lectura** [medido]:
  - el balón limpio de la DFL tiembla 0,022 m (está redondeado al centímetro: √(0,01² + 0,02²) = 0,0224 es el valor
    típico de un paso de redondeo, y por eso cinco partidos dan exactamente lo mismo);
  - con ruido, el temblor es unas 2,9–3,2 veces σ (para ruido puro sería √6·√(2 ln 2) ≈ 2,88): σ = 0,03 → 0,095 m;
    0,06 → 0,181; 0,12 → 0,353; 0,25 → 0,725;
  - el balón «como el ATD» del harness (suavizado 25 frames) tiembla 0,009 m, menos que el limpio.
  - Para leer la celda: si la 1b mide 0,0947 m o menos (también 0,0224 m o menos, lo que tiembla el balón limpio), σ
    es 0,03, la menor de la rejilla: σ = 0 no es una celda. Si mide más de 0,725 m, ninguna σ de la rejilla llega y la
    regla no tiene celda.

Salida tal cual:

```text
# Temblor del balón en la DFL según σ (7 partidos)

Función: `validation/experimento2/instrumento.py: temblor`, parte a parte, en los frames de juego (`H` o `A` en el flag). Semilla 20261116; ruido N(0, σ²) por eje y frame sobre el balón `limpio` del harness.

## σ → temblor (m), los 7 juntos

Mediana de todos los valores |b[t+1] − 2·b[t] + b[t−1]| de las dos partes de todos los partidos.

| balón | σ (m) | en la rejilla | temblor (m) | temblor / σ | valores |
|---|---|---|---|---|---|
| limpio | 0 | no (referencia: limpio) | 0,0224 | – | 544662 |
| limpio + 0,02 m | 0,02 | no (interpolar) | 0,0667 | 3,34 | 544662 |
| limpio + 0,03 m | 0,03 | sí | 0,0947 | 3,16 | 544662 |
| limpio + 0,045 m | 0,045 | no (interpolar) | 0,1375 | 3,06 | 544662 |
| limpio + 0,06 m | 0,06 | sí | 0,1805 | 3,01 | 544662 |
| limpio + 0,09 m | 0,09 | no (interpolar) | 0,2665 | 2,96 | 544662 |
| limpio + 0,12 m | 0,12 | sí | 0,3525 | 2,94 | 544662 |
| limpio + 0,18 m | 0,18 | no (interpolar) | 0,5244 | 2,91 | 544662 |
| limpio + 0,25 m | 0,25 | sí | 0,7248 | 2,90 | 544662 |
| como el ATD (referencia, sin voto) | – | – | 0,0092 | – | 480938 |

## Por partido (m)

| σ (m) | J03WMX | J03WN1 | J03WOH | J03WOY | J03WPY | J03WQQ | J03WR9 |
|---|---|---|---|---|---|---|---|
| limpio | 0,0316 | 0,0283 | 0,0224 | 0,0224 | 0,0224 | 0,0224 | 0,0224 |
| limpio + 0,02 m | 0,0732 | 0,0713 | 0,0647 | 0,0651 | 0,0648 | 0,0648 | 0,0647 |
| limpio + 0,03 m | 0,1014 | 0,0995 | 0,0925 | 0,0928 | 0,0928 | 0,0928 | 0,0927 |
| limpio + 0,045 m | 0,1443 | 0,1425 | 0,1346 | 0,1353 | 0,1354 | 0,1357 | 0,1354 |
| limpio + 0,06 m | 0,1878 | 0,1858 | 0,1773 | 0,1781 | 0,1782 | 0,1787 | 0,1782 |
| limpio + 0,09 m | 0,2745 | 0,2721 | 0,2628 | 0,2636 | 0,2640 | 0,2648 | 0,2643 |
| limpio + 0,12 m | 0,3613 | 0,3579 | 0,3484 | 0,3492 | 0,3501 | 0,3506 | 0,3507 |
| limpio + 0,18 m | 0,5328 | 0,5298 | 0,5192 | 0,5203 | 0,5223 | 0,5226 | 0,5231 |
| limpio + 0,25 m | 0,7325 | 0,7303 | 0,7194 | 0,7204 | 0,7229 | 0,7241 | 0,7241 |
| como el ATD | 0,0108 | 0,0089 | 0,0088 | 0,0087 | 0,0094 | 0,0096 | 0,0084 |

Frames de juego con el balón limpio visible: J03WMX 84349, J03WN1 67340, J03WOH 70940, J03WOY 75171, J03WPY 80500, J03WQQ 83372, J03WR9 84406.

Tiempo: 24 s.
```
