# K2 y `main` con los slots y el balón como los del partido (DFL, 7 partidos; descriptivo)

Código: 8c46846 · bootstrap pareado de 1000 · cada partido, con el pliegue que no lo vio.

## K2 frente a `main`, con la misma degradación los dos

| degradación | `D` | condición | etiquetas | main | K2 | diferencia [5–95 %] | gana en |
|---|---|---|---|---|---|---|---|
| sin degradar | etiquetas | como el ATD | control | 0.728 | 0.780 | +0.051 [+0.040 a +0.064] | 7 de 7 |
| sin degradar | etiquetas | como el ATD | flag | 0.498 | 0.542 | +0.044 [+0.034 a +0.054] | 7 de 7 |
| sin degradar | etiquetas | como el ATD, sin bloques | control | 0.748 | 0.794 | +0.046 [+0.035 a +0.057] | 6 de 7 |
| sin degradar | etiquetas | como el ATD, sin bloques | flag | 0.512 | 0.549 | +0.037 [+0.027 a +0.046] | 7 de 7 |
| sin degradar | propio | como el ATD | control | 0.623 | 0.668 | +0.045 [+0.035 a +0.057] | 6 de 7 |
| sin degradar | propio | como el ATD | flag | 0.414 | 0.457 | +0.043 [+0.034 a +0.052] | 7 de 7 |
| sin degradar | propio | como el ATD, sin bloques | control | 0.651 | 0.686 | +0.036 [+0.024 a +0.047] | 6 de 7 |
| sin degradar | propio | como el ATD, sin bloques | flag | 0.431 | 0.464 | +0.033 [+0.024 a +0.042] | 7 de 7 |
| slots como los del partido | etiquetas | como el ATD | control | 0.721 | 0.784 | +0.063 [+0.051 a +0.076] | 7 de 7 |
| slots como los del partido | etiquetas | como el ATD | flag | 0.497 | 0.543 | +0.046 [+0.036 a +0.056] | 7 de 7 |
| slots como los del partido | etiquetas | como el ATD, sin bloques | control | 0.743 | 0.797 | +0.053 [+0.042 a +0.065] | 6 de 7 |
| slots como los del partido | etiquetas | como el ATD, sin bloques | flag | 0.511 | 0.551 | +0.040 [+0.030 a +0.049] | 7 de 7 |
| slots como los del partido | propio | como el ATD | control | 0.619 | 0.672 | +0.053 [+0.042 a +0.065] | 7 de 7 |
| slots como los del partido | propio | como el ATD | flag | 0.415 | 0.458 | +0.043 [+0.034 a +0.053] | 7 de 7 |
| slots como los del partido | propio | como el ATD, sin bloques | control | 0.649 | 0.688 | +0.039 [+0.028 a +0.050] | 6 de 7 |
| slots como los del partido | propio | como el ATD, sin bloques | flag | 0.432 | 0.466 | +0.034 [+0.025 a +0.044] | 7 de 7 |
| balón 4 frames tarde | etiquetas | como el ATD | control | 0.721 | 0.784 | +0.063 [+0.052 a +0.075] | 7 de 7 |
| balón 4 frames tarde | etiquetas | como el ATD | flag | 0.500 | 0.552 | +0.052 [+0.043 a +0.062] | 7 de 7 |
| balón 4 frames tarde | etiquetas | como el ATD, sin bloques | control | 0.742 | 0.794 | +0.052 [+0.042 a +0.064] | 6 de 7 |
| balón 4 frames tarde | etiquetas | como el ATD, sin bloques | flag | 0.514 | 0.559 | +0.045 [+0.035 a +0.054] | 7 de 7 |
| balón 4 frames tarde | propio | como el ATD | control | 0.621 | 0.671 | +0.050 [+0.039 a +0.062] | 7 de 7 |
| balón 4 frames tarde | propio | como el ATD | flag | 0.417 | 0.464 | +0.047 [+0.039 a +0.056] | 7 de 7 |
| balón 4 frames tarde | propio | como el ATD, sin bloques | control | 0.649 | 0.689 | +0.039 [+0.028 a +0.050] | 6 de 7 |
| balón 4 frames tarde | propio | como el ATD, sin bloques | flag | 0.434 | 0.475 | +0.042 [+0.033 a +0.050] | 7 de 7 |
| las dos juntas | etiquetas | como el ATD | control | 0.715 | 0.783 | +0.068 [+0.058 a +0.080] | 7 de 7 |
| las dos juntas | etiquetas | como el ATD | flag | 0.499 | 0.551 | +0.052 [+0.042 a +0.063] | 7 de 7 |
| las dos juntas | etiquetas | como el ATD, sin bloques | control | 0.738 | 0.792 | +0.055 [+0.043 a +0.066] | 6 de 7 |
| las dos juntas | etiquetas | como el ATD, sin bloques | flag | 0.513 | 0.558 | +0.044 [+0.035 a +0.054] | 7 de 7 |
| las dos juntas | propio | como el ATD | control | 0.618 | 0.672 | +0.054 [+0.044 a +0.065] | 7 de 7 |
| las dos juntas | propio | como el ATD | flag | 0.416 | 0.464 | +0.048 [+0.039 a +0.057] | 7 de 7 |
| las dos juntas | propio | como el ATD, sin bloques | control | 0.648 | 0.688 | +0.040 [+0.029 a +0.051] | 6 de 7 |
| las dos juntas | propio | como el ATD, sin bloques | flag | 0.434 | 0.476 | +0.042 [+0.033 a +0.051] | 7 de 7 |

Lectura (docs/decisiones.md, 17/11): con cada degradación, ¿sigue K2 ganando a `main` por +0.005 o más con control en las cuatro celdas, sin perder con el flag?

- sin degradar: **sí**
- slots como los del partido: **sí**
- balón 4 frames tarde: **sí**
- las dos juntas: **sí**

## Lo que cuesta cada degradación a cada versión (frente a sí misma sin degradar)

| versión | degradación | control, como el ATD, `D` etiquetas | flag, como el ATD, `D` etiquetas | control, como el ATD, sin bloques, `D` etiquetas | flag, como el ATD, sin bloques, `D` etiquetas | control, como el ATD, `D` propio | flag, como el ATD, `D` propio | control, como el ATD, sin bloques, `D` propio | flag, como el ATD, sin bloques, `D` propio |
|---|---|---|---|---|---|---|---|---|---|
| main | slots como los del partido | -0.008 | -0.002 | -0.004 | -0.001 | -0.004 | +0.001 | -0.001 | +0.001 |
| main | balón 4 frames tarde | -0.007 | +0.001 | -0.006 | +0.002 | -0.002 | +0.003 | -0.001 | +0.003 |
| main | las dos juntas | -0.013 | +0.000 | -0.010 | +0.001 | -0.005 | +0.002 | -0.003 | +0.003 |
| K2 | slots como los del partido | +0.004 | +0.001 | +0.003 | +0.002 | +0.003 | +0.001 | +0.002 | +0.002 |
| K2 | balón 4 frames tarde | +0.004 | +0.009 | +0.001 | +0.010 | +0.003 | +0.008 | +0.002 | +0.012 |
| K2 | las dos juntas | +0.004 | +0.009 | -0.002 | +0.009 | +0.004 | +0.008 | +0.002 | +0.012 |
