# ¿Llega el balón del ATD con retraso respecto a los jugadores? (15/11/2026)

- **Quién:** Antonio Azuero, con Claude. Antonio ejecutó en local el script del partido; Claude, la
  calibración en la DFL y el harness.
- **Para qué:** la tarea 1 de Antonio en `docs/PLAN_ENTREGA.md` §3 (P1 de la revisión externa). El harness
  da por hecho que el balón del ATD, suavizado unos 25 frames, llega a su hora. Si el suavizado fuera hacia
  atrás, llegaría unos 12 frames tarde.
- **Datos:**
  - **DFL:** 7 partidos abiertos (Bassek et al., 2025, CC BY 4.0), con el tracking del harness.
  - **Partido:** el ATD, solo agregados.
- **Reglas y detalle:** `validation/retraso_balon/BITACORA.md`. Decisión en `docs/decisiones.md` (15/11).
- **Comandos:**

  ```bash
  python validation/retraso_balon/calibrar_dfl.py       # v1: no pasa (bitácora §7)
  python validation/retraso_balon/calibrar_dfl_v2.py    # v2: pasa (§9)
  python validation/partido/retraso_balon.py --data-dir <datos>   # el partido, lo ejecuta una persona (§10)
  python validation/harness/puntuar.py --versiones validation/harness/versiones/retraso_balon_2026-11-15.json
  python validation/retraso_balon/calibrar_dfl_v2.py --anchos 13 37 49   # sensibilidad al ancho (§11)
  ```

**Lectura en tres líneas:**

1. **El balón del ATD llega unos 4 frames tarde** respecto a los jugadores [medido]: `d̂` = +4, del 5 al 95 %
   de +2 a +5, con +3 y +4 en las dos partes. Un suavizado centrado de otro ancho, de 13 a 49 frames, no lo
   explica: en la DFL da como mucho +2 (bitácora §11).
2. **En la DFL, ese retraso cuesta entre −0,007 y +0,002 de `spellF1` frente a `main`:** es un empate. La
   variante `ball.advance_ball` queda escrita y apagada, y la propuesta es no encenderla.
3. **El riesgo de la revisión externa,** unos 12 frames, **queda descartado respecto a los jugadores.**

## Calibración de la v2 en la DFL (salida tal cual, sin las líneas de progreso)

```
Retraso del balón, versión 2: calibración en la DFL (bitácora §8.3). d̂ > 0: el balón llega tarde.
Cada partido, con la familia de los otros 6. [p5, p95] es el bootstrap por rachas.

centrado −9  (se espera -9 ± 2)
   J03WMX  d̂   -9  [-10.0,  -8.0]  residuo  0.003  partes -10/-8   L̂ v1  -13  rachas  222  ok
   J03WN1  d̂   -7  [ -8.0,  -6.0]  residuo  0.006  partes -8/-6    L̂ v1  -13  rachas  169  ok
   J03WOH  d̂   -9  [-10.0,  -7.0]  residuo  0.001  partes -8/-9    L̂ v1  -14  rachas  158  ok
   J03WOY  d̂  -10  [-11.0,  -8.0]  residuo  0.001  partes -9/-10   L̂ v1  -16  rachas  142  ok
   J03WPY  d̂   -9  [-11.0,  -8.0]  residuo  0.005  partes -10/-9   L̂ v1  -14  rachas  170  ok
   J03WQQ  d̂  -10  [-12.0,  -8.0]  residuo  0.005  partes -9/-12   L̂ v1  -14  rachas  211  ok
   J03WR9  d̂  -10  [-11.0,  -9.0]  residuo  0.001  partes -10/-10  L̂ v1  -16  rachas  205  ok
   → 7 de 7 partidos en la banda (hacen falta 6): pasa

centrado −6  (se espera -6 ± 2)
   J03WMX  d̂   -5  [ -6.0,  -4.0]  residuo  0.004  partes -5/-5    L̂ v1   -9  rachas  296  ok
   J03WN1  d̂   -5  [ -6.0,  -4.0]  residuo  0.003  partes -6/-4    L̂ v1  -10  rachas  227  ok
   J03WOH  d̂   -6  [ -7.0,  -5.0]  residuo  0.003  partes -5/-7    L̂ v1  -10  rachas  216  ok
   J03WOY  d̂   -6  [ -6.0,  -5.0]  residuo  0.004  partes -6/-5    L̂ v1  -10  rachas  197  ok
   J03WPY  d̂   -7  [ -7.0,  -6.0]  residuo  0.004  partes -7/-6    L̂ v1  -11  rachas  217  ok
   J03WQQ  d̂   -6  [ -7.0,  -5.0]  residuo  0.007  partes -5/-7    L̂ v1  -11  rachas  275  ok
   J03WR9  d̂   -7  [ -8.0,  -6.0]  residuo  0.002  partes -7/-7    L̂ v1  -12  rachas  268  ok
   → 7 de 7 partidos en la banda (hacen falta 6): pasa

centrado −3  (se espera -3 ± 2)
   J03WMX  d̂   -1  [ -3.0,  +0.0]  residuo  0.002  partes -1/-1    L̂ v1   -7  rachas  421  ok
   J03WN1  d̂   -3  [ -4.0,  -1.0]  residuo  0.001  partes -4/-1    L̂ v1   -8  rachas  299  ok
   J03WOH  d̂   -3  [ -4.0,  -2.0]  residuo  0.001  partes -4/-3    L̂ v1   -8  rachas  313  ok
   J03WOY  d̂   -2  [ -3.0,  -1.0]  residuo  0.000  partes -2/-2    L̂ v1   -8  rachas  287  ok
   J03WPY  d̂   -4  [ -5.0,  -3.0]  residuo  0.001  partes -4/-4    L̂ v1   -9  rachas  332  ok
   J03WQQ  d̂   -3  [ -4.0,  -2.0]  residuo  0.003  partes -4/-2    L̂ v1   -8  rachas  365  ok
   J03WR9  d̂   -4  [ -5.0,  -3.0]  residuo  0.002  partes -4/-4    L̂ v1   -9  rachas  368  ok
   → 7 de 7 partidos en la banda (hacen falta 6): pasa

centrado 0  (se espera +0 ± 2)
   J03WMX  d̂   +2  [ +1.0,  +3.0]  residuo  0.001  partes +2/+2    L̂ v1   -6  rachas  522  ok
   J03WN1  d̂   +1  [ -1.0,  +2.0]  residuo  0.001  partes +0/+1    L̂ v1   -7  rachas  356  ok
   J03WOH  d̂   -1  [ -2.0,  +1.0]  residuo  0.002  partes -1/+0    L̂ v1   -7  rachas  383  ok
   J03WOY  d̂   +1  [ +0.0,  +1.0]  residuo  0.001  partes +0/+1    L̂ v1   -7  rachas  368  ok
   J03WPY  d̂   +0  [ -2.0,  +1.0]  residuo  0.002  partes -1/+1    L̂ v1   -7  rachas  435  ok
   J03WQQ  d̂   -1  [ -2.0,  +1.0]  residuo  0.002  partes -1/+0    L̂ v1   -7  rachas  488  ok
   J03WR9  d̂   -2  [ -3.0,  -1.0]  residuo  0.001  partes -2/-2    L̂ v1   -8  rachas  467  ok
   → 7 de 7 partidos en la banda (hacen falta 6): pasa

centrado +3  (se espera +3 ± 2)
   J03WMX  d̂   +5  [ +4.0,  +5.0]  residuo  0.008  partes +5/+5    L̂ v1   -6  rachas  568  ok
   J03WN1  d̂   +3  [ +2.0,  +4.0]  residuo  0.000  partes +3/+3    L̂ v1   -6  rachas  374  ok
   J03WOH  d̂   +3  [ +2.0,  +4.0]  residuo  0.001  partes +3/+3    L̂ v1   -6  rachas  424  ok
   J03WOY  d̂   +3  [ +3.0,  +4.0]  residuo  0.006  partes +3/+4    L̂ v1   -6  rachas  418  ok
   J03WPY  d̂   +3  [ +2.0,  +4.0]  residuo  0.000  partes +2/+4    L̂ v1   -6  rachas  476  ok
   J03WQQ  d̂   +2  [ +1.0,  +4.0]  residuo  0.003  partes +2/+3    L̂ v1   -7  rachas  519  ok
   J03WR9  d̂   +2  [ +1.0,  +3.0]  residuo  0.004  partes +1/+2    L̂ v1   -7  rachas  495  ok
   → 7 de 7 partidos en la banda (hacen falta 6): pasa

centrado +6  (se espera +6 ± 2)
   J03WMX  d̂   +7  [ +7.0,  +8.0]  residuo  0.009  partes +7/+7    L̂ v1   +7  rachas  592  ok
   J03WN1  d̂   +6  [ +5.0,  +7.0]  residuo  0.003  partes +6/+6    L̂ v1   +6  rachas  408  ok
   J03WOH  d̂   +6  [ +5.0,  +7.0]  residuo  0.001  partes +6/+6    L̂ v1   +6  rachas  444  ok
   J03WOY  d̂   +6  [ +5.0,  +6.0]  residuo  0.003  partes +6/+6    L̂ v1   +6  rachas  453  ok
   J03WPY  d̂   +6  [ +5.0,  +7.0]  residuo  0.001  partes +6/+7    L̂ v1   +6  rachas  504  ok
   J03WQQ  d̂   +6  [ +5.0,  +7.0]  residuo  0.001  partes +6/+6    L̂ v1   +6  rachas  541  ok
   J03WR9  d̂   +5  [ +4.0,  +5.0]  residuo  0.009  partes +5/+5    L̂ v1   -7  rachas  518  ok
   → 7 de 7 partidos en la banda (hacen falta 6): pasa

centrado +9  (se espera +9 ± 2)
   J03WMX  d̂  +10  [+10.0, +11.0]  residuo  0.011  partes +11/+10  L̂ v1   +9  rachas  572  ok
   J03WN1  d̂   +8  [ +8.0,  +9.0]  residuo  0.010  partes +8/+9    L̂ v1   +8  rachas  392  ok
   J03WOH  d̂   +9  [ +8.0, +10.0]  residuo  0.001  partes +9/+9    L̂ v1   +9  rachas  430  ok
   J03WOY  d̂   +8  [ +8.0,  +9.0]  residuo  0.010  partes +8/+9    L̂ v1   +9  rachas  450  ok
   J03WPY  d̂   +9  [ +9.0, +10.0]  residuo  0.008  partes +9/+9    L̂ v1  +10  rachas  504  ok
   J03WQQ  d̂   +9  [ +9.0, +10.0]  residuo  0.007  partes +10/+9   L̂ v1   +9  rachas  512  ok
   J03WR9  d̂   +8  [ +7.0,  +8.0]  residuo  0.012  partes +8/+8    L̂ v1   +9  rachas  515  ok
   → 7 de 7 partidos en la banda (hacen falta 6): pasa

hacia atrás  (se espera +12 ± 2)
   J03WMX  d̂  +13  [+12.0, +14.0]  residuo  0.007  partes +14/+11  L̂ v1  +12  rachas  464  ok
   J03WN1  d̂  +11  [+10.0, +12.0]  residuo  0.018  partes +11/+12  L̂ v1  +12  rachas  352  ok
   J03WOH  d̂  +14  [+12.0, +15.0]  residuo  0.027  partes +13/+14  L̂ v1  +13  rachas  367  ok
   J03WOY  d̂  +11  [+11.0, +13.0]  residuo  0.008  partes +11/+11  L̂ v1  +12  rachas  409  ok
   J03WPY  d̂  +12  [+11.0, +14.0]  residuo  0.005  partes +12/+12  L̂ v1  +13  rachas  419  ok
   J03WQQ  d̂  +12  [+11.0, +13.0]  residuo  0.001  partes +12/+12  L̂ v1  +12  rachas  461  ok
   J03WR9  d̂  +11  [+10.0, +12.0]  residuo  0.009  partes +11/+10  L̂ v1  +12  rachas  465  ok
   → 7 de 7 partidos en la banda (hacen falta 6): pasa

exponencial hacia atrás, α = 1/9 (descriptiva: retraso medio +8; no está en la familia)
   J03WMX  d̂   +7  [ +6.0,  +7.0]  residuo  0.138  partes +6/+7    L̂ v1   -7  rachas  585
   J03WN1  d̂   +6  [ +5.0,  +6.0]  residuo  0.082  partes +5/+6    L̂ v1   -7  rachas  390
   J03WOH  d̂   +5  [ +4.0,  +6.0]  residuo  0.108  partes +5/+5    L̂ v1   -7  rachas  430
   J03WOY  d̂   +5  [ +4.0,  +6.0]  residuo  0.090  partes +5/+5    L̂ v1   -7  rachas  464
   J03WPY  d̂   +4  [ +3.0,  +6.0]  residuo  0.205  partes +4/+5    L̂ v1   -7  rachas  502
   J03WQQ  d̂   +5  [ +4.0,  +6.0]  residuo  0.176  partes +4/+6    L̂ v1   -7  rachas  518
   J03WR9  d̂   +3  [ +1.0,  +4.0]  residuo  0.154  partes +3/+2    L̂ v1   -7  rachas  515

Residuo de referencia (el mayor de las 8 pruebas): 0.027

Calibración v2: PASA, la medida se puede ejecutar en el partido
tiempo 41 s
```

## El partido (salida entera, tal cual la pegó Antonio)

Ejecutado el 15/11 hacia las 16:50, con la rama en `b143176`, antes del cambio de Ismael del lado negativo
(bitácora §11). Ese cambio no altera esta lectura: el desfase es positivo.

```
Retraso del balón del ATD, versión 2 (validation/retraso_balon/BITACORA.md §8): frames evaluados, las dos partes juntas

0. Controles (el perfil del ATD dice 158857 y 94214; la familia, 7 partidos de la DFL)
   frames evaluados: 158857
   frames evaluados con balón: 94214
   partidos de la DFL en la familia: 7
   ¿cuadran los tres? sí

1. Rachas de conducción (mismo slot a 1.5 m o menos, 25 frames o más)
   rachas: 572   frames en rachas: 29183
   rachas por parte: 290, 282

2. Desfase d̂ (d̂ > 0: el balón llega tarde)
   d̂ = +4 frames   intervalo del 5 al 95 %: [2,0, 5,0]
   d̂ por parte: +3, +4
   residuo: 0,018   de referencia (DFL): 0,027   (no concluye si pasa de 2 veces)

3. Descriptivo, no decide
   L̂ de la versión 1 (máximo de la curva): +5   por parte: +5, -6   con el módulo: +6
   correlación por desfase:
      -24: 0,287  -18: 0,388  -12: 0,458  -6: 0,486  -3: 0,476  +0: 0,454  +3: 0,481  +6: 0,485  +9: 0,465  +12: 0,427  +15: 0,377  +18: 0,324  +24: 0,206

4. Lectura (bitácora §8.5): candidato 2
   |desfase| = 4 ≥ 4: variante en possession/ball.py que adelanta el balón 4 frames

   tiempo 45 s
```

## Lo que costaría ese retraso: el harness (descriptivo, no decide)

El balón de la DFL retrasado 4 frames (`ball.advance_ball` con `frames = −4`) frente a `main`, con el
control al lado. `spellF1` de los 7 partidos juntos:

| etiquetas | balón | control (voto ±50) | `main` | balón 4 frames tarde | tarde frente a `main` [5–95 %] |
|---|---|---|---|---|---|
| flag | como el ATD | 0,406 | 0,498 | 0,500 | +0,001 [−0,003 a +0,006] |
| flag | como el ATD, sin bloques | 0,435 | 0,512 | 0,514 | +0,002 [−0,002 a +0,007] |
| control | como el ATD | 0,464 | 0,728 | 0,721 | −0,007 [−0,012 a −0,002] |
| control | como el ATD, sin bloques | 0,494 | 0,748 | 0,742 | −0,006 [−0,011 a −0,001] |

Frente a `main`, con §5.8: **empate o no concluye.**

## Sensibilidad al ancho del suavizado (DFL, descriptivo, hecho después de medir el partido)

Es el balón centrado sin retraso con otros anchos, medido dejando un partido fuera con la familia de caja de
25, con `python validation/retraso_balon/calibrar_dfl_v2.py --anchos 13 37 49` (bitácora §11). Lo correcto sería 0. Con la lectura
cambiada por Ismael, los tres de 49 frames en −4 o menos salen «negativo, se apunta».

| ancho | `d̂` en los 7 partidos | residuo |
|---|---|---|
| 13 | de −1 a +2 | de 0,002 a 0,006 |
| 37 | de −3 a +1 | de 0,002 a 0,006 |
| 49 | de −6 a −1 (3 de 7 en −4 o menos) | de 0,011 a 0,037 |
