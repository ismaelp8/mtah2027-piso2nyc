# Costes del `D` con el `D` propio · 2026-11-15 · David, con Claude

- **Fecha y quién:** 15/11/2026. Tarea 2 de David (`docs/PLAN_ENTREGA.md` §3). Lo escribió y lo ejecutó
  Claude en la sesión de David.
- **Datos:** los 7 partidos de la Bundesliga (Bassek et al., 2025, CC BY 4.0). Nada del partido.
- **Código:** la rama `exp/costes-d-propio`, que sale de `main` en `bb4f2ef`. El fichero de versiones
  (`validation/harness/versiones/costes_d_propio_2026-11-15.json`) tiene su propio commit, `2563c4d`, hecho
  antes de medir.
- **Versiones:** `to_dead` × `from_dead` en 12, 25 y 50, y `switch` a 25. La de `main` es 25 / 25.
- **Comandos:**
  - `python validation/harness/puntuar.py --versiones validation/harness/versiones/costes_d_propio_2026-11-15.json --d propio`
    (unos 8 minutos);
  - `python validation/apuesta_b/d_propio.py --versiones validation/harness/versiones/costes_d_propio_2026-11-15.json`.
- **Es descriptivo.** Un número con el `D` propio no decide (§4 del plan). La regla escrita en el plan
  antes de medir: si algo gana a `main` en los dos modos (el balón tapado y el balón a la vista en los `D`)
  y con las dos convenciones, se le pasa a Ismael, que decide.

## Lectura

1. **Ninguna versión gana a `main`** [medido]. Frente a `main`, la regla de §5.8 da «empate o no concluye»
   en las 8. Todas las diferencias con `main` caen entre −0,008 y +0,004, frente al umbral de 0,03. Ninguna
   gana en más de 4 de los 7 partidos en las condiciones que votan. **No hay nada que pasarle a Ismael.**
   Se quedan los 25 / 25 de `main`.
2. **Lo único que se mueve, y muy poco, es la suma `to_dead + from_dead`** [medido]. Las versiones con la
   misma suma dan exactamente lo mismo: 12 + 50 y 50 + 12, 12 + 25 y 25 + 12, 25 + 50 y 50 + 25.
   [inferencia] Cada parada dentro de un tramo se paga entrando y saliendo, así que, salvo en el borde
   del tramo, el decodificador solo ve la suma. En la práctica es un solo parámetro.
3. **El sentido depende de la convención** [medido], aunque las dos diferencias son ruido:
   - con control, la suma más baja (24) es la peor: −0,006 [−0,010 a −0,002], 1 de 7;
   - con el flag, nada se mueve más de ±0,002.
4. **Las paradas vistas apenas cambian** [medido]. Con el balón tapado, la suma 24 ve 636 de 713 frente a
   629 de `main`; la suma 100 ve 619. Con el balón a la vista: 547, 545 y 534. La precisión del `D` está
   entre el 93 y el 95 % en todas.
5. **Lo que queda para cuando Ana añada la escala del `D` a 0,5:** basta repetirlo con tres sumas (24, 50
   y 100) en vez de nueve combinaciones.

## Salida resumida

`puntuar.py --d propio`, spellF1 de los 7 partidos juntos, en las condiciones que votan:

| versión (`to_dead` / `from_dead`) | flag, como el ATD | flag, sin bloques | control, como el ATD | control, sin bloques |
|---|---|---|---|---|
| control: voto ±50 | 0,310 | 0,346 | 0,353 | 0,397 |
| **main (25 / 25)** | **0,416** | **0,433** | **0,616** | **0,642** |
| 12 / 12 | 0,417 | 0,433 | 0,610 | 0,636 |
| 12 / 25 y 25 / 12 | 0,417 | 0,433 | 0,615 | 0,641 |
| 12 / 50 y 50 / 12 | 0,417 | 0,433 | 0,620 | 0,644 |
| 25 / 50 y 50 / 25 | 0,415 | 0,431 | 0,617 | 0,642 |
| 50 / 50 | 0,415 | 0,432 | 0,618 | 0,643 |

Frente al control, todas ganan con §5.8 (de +0,085 a +0,107 con el flag, 7 de 7).

Frente a `main`: la diferencia más grande, en cualquiera de las cuatro condiciones de arriba, es −0,006
[−0,010 a −0,002], la de 12 / 12 con control. La positiva más grande es +0,004 [+0,001 a +0,006], la de
12 / 50 y 50 / 12 con control y el balón como el ATD, en 4 de 7.

`d_propio.py`, balón «como el ATD»:

| versión | paradas vistas, balón tapado | paradas vistas, balón a la vista | spellF1 flag / control, balón a la vista |
|---|---|---|---|
| main (25 / 25) | 629 de 713 (88,2 %) | 545 de 713 (76,4 %) | 0,391 / 0,569 |
| 12 / 12 | 636 (89,2 %) | 547 (76,7 %) | 0,390 / 0,562 |
| 12 / 50 y 50 / 12 | 627 (87,9 %) | 543 (76,2 %) | 0,392 / 0,572 |
| 50 / 50 | 619 (86,8 %) | 534 (74,9 %) | 0,390 / 0,573 |

La salida completa de los dos comandos se puede repetir con los comandos de arriba. El harness es
determinista.
