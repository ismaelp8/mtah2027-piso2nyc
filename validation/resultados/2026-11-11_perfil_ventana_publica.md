# Perfil de la GT pública (5 minutos)

- **Fecha:** 2026-11-11 · **Quién:** Claude, en la sesión de Ismael.
- **Datos:** `evaluation/gt/BAR-ATH_possession_gt_public.csv`, la GT pública que viene en el repo.
- **Comando:** `python validation/scripts/perfil_etiquetas.py evaluation/gt/BAR-ATH_possession_gt_public.csv`
- **Para qué:** comprobar la métrica y entender qué significan las etiquetas. **No es un prior ni
  sirve para elegir parámetros:** son 17 posesiones y las reglas lo prohíben.

**Lectura:**

- La GT tiene posesiones de 19 y 33 frames. Encaja con que "nada se suaviza".
- Su huella de retrasos (1,00 / 0,95 / 0,78 con 3 / 8 / 25 frames) sale más alta que la tabla oficial
  (0,98 / 0,89 / 0,65). Si esa tabla es la del partido completo (duda D1), en el partido completo hay más
  posesiones cortas que en estos 5 minutos.
- Solo el 19,6 % de los frames es `D`, frente al ~40 % que cabe esperar en un partido entero (el tiempo
  efectivo de LaLiga ronda el 59 % según CIES, con datos de 2019 a 2021). Tampoco en esto es representativa.

## Salida

```text
fichero: BAR-ATH_possession_gt_public.csv
frames: 199319  evaluados (no X): 7500  tramos evaluados: 1
reparto de frames evaluados: H 46.1%  A 34.4%  D 19.6%

posesiones (rachas de H o de A): 17  |  4.23 por minuto de balón vivo
  duración (s): p10 2.2 | p25 3.5 | mediana 7.6 | p75 20.0 | p90 38.1 | media 14.2
  más cortas que: 0.5 s 0%  1 s 6%  2 s 12%  3 s 18%  5 s 35%
  las tres más cortas (frames): [19, 33, 71]

paradas (rachas de D): 4
  duración (s): p10 8.2 | p25 12.2 | mediana 16.4 | p75 18.9 | p90 19.8 | media 14.7

transiciones por tipo: A>D 3  A>H 6  D>A 2  D>H 2  H>A 6  H>D 1

huella de retrasos (spellF1 de la secuencia contra sí misma retrasada d frames)
   retraso       esta    oficial  diferencia
         1     1.0000     1.0000     +0.0000
         3     1.0000     0.9818     +0.0182
         8     0.9529     0.8933     +0.0596
        25     0.7765     0.6539     +0.1226
  (oficial = tabla de EVALUATION.md; solo informativa, no decide nada: dudas D1 y D21)
```
