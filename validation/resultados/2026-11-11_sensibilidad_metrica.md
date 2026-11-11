# Sensibilidad de spellF1 a cada tipo de error (GT sintética)

- **Fecha:** 2026-11-11 · **Quién:** Claude, en la sesión de Ismael.
- **Datos:** ninguno del partido. Solo la tabla oficial de retrasos de `EVALUATION.md` y el scorer
  oficial.
- **Comando:** `python validation/scripts/sensibilidad_metrica.py` (determinista, unos segundos).
- **Para qué:** ordenar los errores por lo que cuestan. No predice nuestra nota. Como la GT sintética
  se calibra con la tabla oficial, es lectura de la métrica y no base para fijar parámetros (duda D21
  de `validation/PASOS.md`).

**Lectura** (detalle en las secciones 1.2, 1.3 y 7.2 de `docs/investigacion_metodos.md`):

- La tabla oficial se reproduce con posesiones de mediana ≈ 5,3 s: en torno a un tercio dura menos de
  3 s y una de cada diez, menos de 1 s.
- **Inventar cambios de posesión es el error más caro:** uno por minuto de balón vivo cuesta 0,16.
- **No ver las posesiones cortas es el segundo:** perder todas las de menos de 3 s cuesta 0,26.
- **Desfasar las fronteras cuesta menos, pero no es gratis:** con σ = 12 frames cuesta 0,12.
- **No detectar ninguna parada cuesta 0,37.**
- El escenario B (0,69) ya exige un sistema muy bueno; el D (0,39) sigue estando por encima del baseline
  (0,24).

## Salida

```text
lognormal ajustada: mediana 132 frames (5.3 s), sigma 1.26, media 291 frames (11.6 s)
tabla reproducida por el ajuste: {3: 0.9773, 8: 0.896, 25: 0.6544}  objetivo: {3: 0.9818, 8: 0.8933, 25: 0.6539}
  posesiones de menos de   12 frames ( 0.5 s): 2.9 %
  posesiones de menos de   18 frames ( 0.7 s): 5.7 %
  posesiones de menos de   25 frames ( 1.0 s): 9.4 %
  posesiones de menos de   50 frames ( 2.0 s): 22.1 %
  posesiones de menos de   75 frames ( 3.0 s): 32.8 %
  posesiones de menos de  125 frames ( 5.0 s): 48.4 %
  posesiones de menos de  250 frames (10.0 s): 69.5 %
  posesiones de menos de  500 frames (20.0 s): 85.5 %

parte sintética: 142942 frames, 332 posesiones, media 10.9 s, balón vivo 0.63

-- comprobación: retraso uniforme sobre la GT sintética (debe parecerse a la oficial) --
retraso uniforme de 3 frames                                       spellF1 0.979  macroF1 0.990  posesiones pred/real 1.00
retraso uniforme de 8 frames                                       spellF1 0.898  macroF1 0.973  posesiones pred/real 1.00
retraso uniforme de 25 frames                                      spellF1 0.651  macroF1 0.919  posesiones pred/real 1.00

-- fronteras desplazadas N(0, sd) --
sd 3 frames, todas las fronteras                                   spellF1 0.981  macroF1 0.992  posesiones pred/real 1.00
sd 6 frames, todas las fronteras                                   spellF1 0.947  macroF1 0.984  posesiones pred/real 0.99
sd 12 frames, todas las fronteras                                  spellF1 0.878  macroF1 0.968  posesiones pred/real 0.97
sd 25 frames, todas las fronteras                                  spellF1 0.749  macroF1 0.936  posesiones pred/real 0.92
sd 12 frames, solo las fronteras con D                             spellF1 0.958  macroF1 0.981  posesiones pred/real 0.99
sd 25 frames, solo las fronteras con D                             spellF1 0.904  macroF1 0.962  posesiones pred/real 0.97
sd 50 frames, solo las fronteras con D                             spellF1 0.830  macroF1 0.928  posesiones pred/real 0.93
sd 12 frames, solo los cambios H<->A                               spellF1 0.928  macroF1 0.986  posesiones pred/real 0.98
sd 25 frames, solo los cambios H<->A                               spellF1 0.846  macroF1 0.972  posesiones pred/real 0.94

-- posesiones cortas no detectadas (heredan la etiqueta anterior) --
se pierden todas las de menos de 12 frames (0.5 s)                 spellF1 0.982  macroF1 1.000  posesiones pred/real 0.97
se pierden todas las de menos de 18 frames (0.7 s)                 spellF1 0.960  macroF1 0.999  posesiones pred/real 0.93
se pierden todas las de menos de 25 frames (1.0 s)                 spellF1 0.933  macroF1 0.997  posesiones pred/real 0.88
se pierden todas las de menos de 50 frames (2.0 s)                 spellF1 0.830  macroF1 0.986  posesiones pred/real 0.73
se pierden todas las de menos de 75 frames (3.0 s)                 spellF1 0.742  macroF1 0.971  posesiones pred/real 0.62
se pierden todas las de menos de 125 frames (5.0 s)                spellF1 0.611  macroF1 0.939  posesiones pred/real 0.47

-- cambios de posesión inventados dentro de posesiones reales (10-40 frames) --
0.25 cambios falsos por minuto de balón vivo                       spellF1 0.956  macroF1 0.998  posesiones pred/real 1.08
0.50 cambios falsos por minuto de balón vivo                       spellF1 0.912  macroF1 0.995  posesiones pred/real 1.16
1.00 cambios falsos por minuto de balón vivo                       spellF1 0.838  macroF1 0.990  posesiones pred/real 1.32
2.00 cambios falsos por minuto de balón vivo                       spellF1 0.711  macroF1 0.980  posesiones pred/real 1.63
4.00 cambios falsos por minuto de balón vivo                       spellF1 0.540  macroF1 0.960  posesiones pred/real 2.24
8.00 cambios falsos por minuto de balón vivo                       spellF1 0.354  macroF1 0.923  posesiones pred/real 3.34

-- errores de balón muerto --
10 % de las paradas no detectadas (D -> equipo anterior)           spellF1 0.971  macroF1 0.971  posesiones pred/real 0.99
25 % de las paradas no detectadas (D -> equipo anterior)           spellF1 0.910  macroF1 0.917  posesiones pred/real 0.96
50 % de las paradas no detectadas (D -> equipo anterior)           spellF1 0.821  macroF1 0.818  posesiones pred/real 0.90
100 % de las paradas no detectadas (D -> equipo anterior)          spellF1 0.633  macroF1 0.532  posesiones pred/real 0.80
0.25 tramos D falsos (1-4 s) por minuto de balón vivo              spellF1 0.970  macroF1 0.993  posesiones pred/real 1.03
0.50 tramos D falsos (1-4 s) por minuto de balón vivo              spellF1 0.941  macroF1 0.987  posesiones pred/real 1.07
1.00 tramos D falsos (1-4 s) por minuto de balón vivo              spellF1 0.888  macroF1 0.975  posesiones pred/real 1.14
2.00 tramos D falsos (1-4 s) por minuto de balón vivo              spellF1 0.792  macroF1 0.951  posesiones pred/real 1.27

-- escenarios combinados (sección 7.2 del informe) --
A: sd 6 + pierde <18 + 0,25 falsos/min + 5 % paradas               spellF1 0.872  macroF1 0.957  posesiones pred/real 1.01
B: sd 12 + pierde <25 y la mitad de 25-75 + 0,5 falsos/min + 10 %  spellF1 0.691  macroF1 0.926  posesiones pred/real 0.89
C: sd 12 + pierde <50 y la mitad de 50-125 + 1 falso/min + 20 %    spellF1 0.517  macroF1 0.865  posesiones pred/real 0.90
D: sd 25 + pierde <75 + 2 falsos/min + 30 % + 0,5 D falsos/min     spellF1 0.390  macroF1 0.810  posesiones pred/real 1.34
```
