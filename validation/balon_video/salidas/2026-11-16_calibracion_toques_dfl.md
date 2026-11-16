# Suelo de ruido del detector de toques en la DFL (puerta 1b, condición 4) · 2026-11-16 · Claude (sesión de Ismael)

- **Para qué:** la cifra que pedía la condición 4 de la puerta 1b (`validation/balon_video/BITACORA.md`) antes de
  ejecutar la 1b: el suelo de ruido por minuto con el balón limpio de la DFL y su doble. Y cómo crecen toques y ruido
  con temblor gaussiano en la posición del balón y con el balón «como el ATD». **Desde la corrección de la puerta 1b
  (16/11, 15:50) la condición 4 es descriptiva:** el doble (4,2) ya no es un umbral que decida.
- **Datos:** los 7 partidos abiertos de la Bundesliga (Bassek et al., 2025, CC BY 4.0), caché del experimento 0
  (`validation/experimento0/dfl_lector.py`), con `validation/harness/dfl.py` (condiciones `limpio` y «como el ATD»).
  Nada del partido.
- **Comando:** `python validation/balon_video/calibrar_toques_dfl.py` (Python 3.14.7, numpy 2.5.4, pandas 3.1.1;
  repo en `48f29cf` con `validation/balon_video/toques.py` sin commitear, sha256 `52a11063…4afd9e`, y el script
  con sha256 `820156ae…66d521`). Dos ejecuciones dan la misma salida. Las tablas son idénticas a las de la primera
  versión del script (sha256 `dfaad901…921cf842`); esta solo añade el desglose por distancia al `D`.
- **Lectura en cuatro líneas** [medido]:
  1. Suelo de ruido con el balón limpio, los 7 juntos: **2,1 por minuto** (de 1,14 a 3,92 por partido). Su doble,
     4,2, era el umbral de la condición 4; ya no decide.
  2. Cordura: limpio da 38,4 toques/min (experimento 2: 37,9) y «como el ATD» 3,6 (experimento 2, media móvil de 25
     frames: 3,5; ATD en la ventana pública: 2,2).
  3. Con temblor el ruido crece deprisa: σ = 0,03 m da 3,4 de ruido por minuto y σ = 0,05 m da 8,7.
  4. Buena parte del 4,1 de ruido por minuto del balón «como el ATD» es un artefacto del harness, no del suavizado: 564
     de sus 1.324 eventos de ruido caen justo a 18 frames de un `D` (con el balón limpio, 8). 18 = `BORDE` 5 + media
     ventana 12 + 1, el primer frame en que la media móvil deja de usar un solo lado, porque `dfl.degradar_con` tapa
     el `D`±5 antes de suavizar. Lejos de los `D` (a 50 frames o más), «como el ATD» da 2,44 por minuto y el limpio
     1,72; sin los eventos a 18 frames o menos de un `D`, «como el ATD» da 2,33. Lo llevan también las dos condiciones
     que votan en el harness (las dos llevan `suavizado` = 25 en `dfl.PARAMETROS_DE`; su efecto en la otra no está
     medido aquí).

Salida tal cual:

```text
# Toques y suelo de ruido del detector de toques en la DFL (7 partidos)

Detector: `validation/balon_video/toques.py` (umbral 3.0 m/s, toque con jugador a 1.5 m o menos, ruido sin nadie a 3.0 m o menos, tramos de 10 frames o más), parte a parte.
Por minuto de frames de juego (`H` o `A` en el flag) con el balón de esa versión visible.

## Los 7 juntos

| versión del balón | min de juego con balón | toques | ruido | toques/min | ruido/min | eventos/min | ruido/toques |
|---|---|---|---|---|---|---|---|
| limpio | 364.1 | 13962 | 764 | 38.35 | 2.1 | 41.46 | 0.055 |
| limpio + 0.03 m | 364.1 | 14352 | 1243 | 39.42 | 3.41 | 44.08 | 0.087 |
| limpio + 0.05 m | 364.1 | 15157 | 3183 | 41.63 | 8.74 | 52.96 | 0.21 |
| limpio + 0.10 m | 364.1 | 24758 | 12217 | 68.01 | 33.56 | 118.73 | 0.493 |
| limpio + 0.20 m | 364.1 | 27984 | 13561 | 76.87 | 37.25 | 137.2 | 0.485 |
| como el ATD | 321.9 | 1173 | 1324 | 3.64 | 4.11 | 9.77 | 1.129 |

**Suelo de ruido con el balón limpio (7 juntos): 2.1 por minuto** (por partido, de 1.14 a 3.92).
El doble, 4.2 por minuto, era el umbral de la condición 4 antes de la corrección de la puerta 1b; desde entonces la condición 4 es descriptiva y esta cifra no decide nada.

## Ruido por distancia al D más cercano (los 7 juntos; descriptivo)

| versión del balón | ruido | ruido a 18 frames de un D | ruido a 18 o menos | ruido/min sin los de 18 o menos | ruido/min a 50 frames o más de un D (min) |
|---|---|---|---|---|---|
| limpio | 764 | 8 | 93 | 1.84 | 1.72 (323.8) |
| como el ATD | 1324 | 564 | 574 | 2.33 | 2.44 (285.9) |

## Por partido

| J03WMX | min de juego con balón | toques | ruido | toques/min | ruido/min | eventos/min | ruido/toques |
|---|---|---|---|---|---|---|---|
| limpio | 56.2 | 2589 | 164 | 46.04 | 2.92 | 50.61 | 0.063 |
| limpio + 0.03 m | 56.2 | 2652 | 242 | 47.16 | 4.3 | 53.47 | 0.091 |
| limpio + 0.05 m | 56.2 | 2751 | 541 | 48.92 | 9.62 | 62.01 | 0.197 |
| limpio + 0.10 m | 56.2 | 3916 | 1823 | 69.64 | 32.42 | 118.49 | 0.466 |
| limpio + 0.20 m | 56.2 | 4373 | 2033 | 77.77 | 36.15 | 136.01 | 0.465 |
| como el ATD | 49.8 | 223 | 217 | 4.48 | 4.36 | 10.99 | 0.973 |

| J03WN1 | min de juego con balón | toques | ruido | toques/min | ruido/min | eventos/min | ruido/toques |
|---|---|---|---|---|---|---|---|
| limpio | 44.9 | 1839 | 176 | 40.96 | 3.92 | 47.07 | 0.096 |
| limpio + 0.03 m | 44.9 | 1893 | 247 | 42.17 | 5.5 | 50.27 | 0.13 |
| limpio + 0.05 m | 44.9 | 1997 | 435 | 44.48 | 9.69 | 58.41 | 0.218 |
| limpio + 0.10 m | 44.9 | 2995 | 1407 | 66.71 | 31.34 | 118.39 | 0.47 |
| limpio + 0.20 m | 44.9 | 3343 | 1575 | 74.47 | 35.08 | 136.08 | 0.471 |
| como el ATD | 39.7 | 136 | 193 | 3.42 | 4.86 | 11.08 | 1.419 |

| J03WOH | min de juego con balón | toques | ruido | toques/min | ruido/min | eventos/min | ruido/toques |
|---|---|---|---|---|---|---|---|
| limpio | 47.3 | 1659 | 103 | 35.08 | 2.18 | 38.1 | 0.062 |
| limpio + 0.03 m | 47.3 | 1717 | 154 | 36.31 | 3.26 | 40.58 | 0.09 |
| limpio + 0.05 m | 47.3 | 1816 | 411 | 38.4 | 8.69 | 49.46 | 0.226 |
| limpio + 0.10 m | 47.3 | 3131 | 1689 | 66.2 | 35.71 | 119.17 | 0.539 |
| limpio + 0.20 m | 47.3 | 3542 | 1863 | 74.89 | 39.39 | 138.05 | 0.526 |
| como el ATD | 41.8 | 161 | 175 | 3.85 | 4.19 | 9.77 | 1.087 |

| J03WOY | min de juego con balón | toques | ruido | toques/min | ruido/min | eventos/min | ruido/toques |
|---|---|---|---|---|---|---|---|
| limpio | 50.1 | 1798 | 81 | 35.88 | 1.62 | 38.39 | 0.045 |
| limpio + 0.03 m | 50.1 | 1843 | 147 | 36.78 | 2.93 | 40.79 | 0.08 |
| limpio + 0.05 m | 50.1 | 1967 | 400 | 39.25 | 7.98 | 49.65 | 0.203 |
| limpio + 0.10 m | 50.1 | 3264 | 1719 | 65.13 | 34.3 | 118.01 | 0.527 |
| limpio + 0.20 m | 50.1 | 3706 | 1944 | 73.95 | 38.79 | 137.11 | 0.525 |
| como el ATD | 44.2 | 137 | 198 | 3.1 | 4.47 | 9.67 | 1.445 |

| J03WPY | min de juego con balón | toques | ruido | toques/min | ruido/min | eventos/min | ruido/toques |
|---|---|---|---|---|---|---|---|
| limpio | 53.7 | 2006 | 61 | 37.38 | 1.14 | 38.93 | 0.03 |
| limpio + 0.03 m | 53.7 | 2061 | 145 | 38.4 | 2.7 | 41.68 | 0.07 |
| limpio + 0.05 m | 53.7 | 2188 | 474 | 40.77 | 8.83 | 51.63 | 0.217 |
| limpio + 0.10 m | 53.7 | 3666 | 1894 | 68.31 | 35.29 | 119.39 | 0.517 |
| limpio + 0.20 m | 53.7 | 4162 | 2097 | 77.55 | 39.07 | 138.58 | 0.504 |
| como el ATD | 47.4 | 180 | 187 | 3.8 | 3.95 | 9.68 | 1.039 |

| J03WQQ | min de juego con balón | toques | ruido | toques/min | ruido/min | eventos/min | ruido/toques |
|---|---|---|---|---|---|---|---|
| limpio | 55.6 | 2099 | 103 | 37.76 | 1.85 | 40.14 | 0.049 |
| limpio + 0.03 m | 55.6 | 2163 | 180 | 38.92 | 3.24 | 42.86 | 0.083 |
| limpio + 0.05 m | 55.6 | 2283 | 509 | 41.07 | 9.16 | 52.09 | 0.223 |
| limpio + 0.10 m | 55.6 | 3856 | 1890 | 69.38 | 34.0 | 119.77 | 0.49 |
| limpio + 0.20 m | 55.6 | 4368 | 2059 | 78.59 | 37.04 | 137.4 | 0.471 |
| como el ATD | 49.1 | 194 | 199 | 3.95 | 4.05 | 9.79 | 1.026 |

| J03WR9 | min de juego con balón | toques | ruido | toques/min | ruido/min | eventos/min | ruido/toques |
|---|---|---|---|---|---|---|---|
| limpio | 56.3 | 1972 | 76 | 35.04 | 1.35 | 37.11 | 0.039 |
| limpio + 0.03 m | 56.3 | 2023 | 128 | 35.95 | 2.27 | 39.1 | 0.063 |
| limpio + 0.05 m | 56.3 | 2155 | 413 | 38.3 | 7.34 | 47.57 | 0.192 |
| limpio + 0.10 m | 56.3 | 3930 | 1795 | 69.84 | 31.9 | 117.88 | 0.457 |
| limpio + 0.20 m | 56.3 | 4490 | 1990 | 79.79 | 35.36 | 137.16 | 0.443 |
| como el ATD | 49.9 | 142 | 155 | 2.85 | 3.11 | 7.68 | 1.092 |

Tiempo: 8 s.
```
