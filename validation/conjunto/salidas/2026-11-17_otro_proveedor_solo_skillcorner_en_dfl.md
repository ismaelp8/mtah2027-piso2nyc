# Modelo conjunto frente a `main` · tanda «solo_sc» · DFL · 7 partidos

Código: 4845078 · bootstrap pareado de 1000 · `main` = B5, `dead_state` y `decode_cortas_a_d` · salidas del modelo: las de torch.

## Candidato K2

α elegida para cada partido con los otros: 4 en 7. Con los 7: 4.

| `D` | condición | etiquetas | main | candidato | diferencia [5–95 %] | gana en | posesiones: candidato / main / reales |
|---|---|---|---|---|---|---|---|
| etiquetas | como el ATD | control | 0.728 | 0.632 | -0.096 [-0.110 a -0.082] | 0 de 7 | 1769 / 1661 / 1736 |
| etiquetas | como el ATD | flag | 0.498 | 0.438 | -0.060 [-0.072 a -0.048] | 0 de 7 | 1769 / 1661 / 3061 |
| etiquetas | como el ATD, sin bloques | control | 0.748 | 0.673 | -0.075 [-0.088 a -0.061] | 0 de 7 | 1824 / 1675 / 1736 |
| etiquetas | como el ATD, sin bloques | flag | 0.512 | 0.471 | -0.041 [-0.053 a -0.030] | 0 de 7 | 1824 / 1675 / 3061 |
| propio | como el ATD | control | 0.623 | 0.561 | -0.062 [-0.075 a -0.048] | 0 de 7 | 1573 / 1538 / 1736 |
| propio | como el ATD | flag | 0.414 | 0.378 | -0.036 [-0.047 a -0.025] | 0 de 7 | 1573 / 1538 / 3061 |
| propio | como el ATD, sin bloques | control | 0.651 | 0.606 | -0.045 [-0.059 a -0.032] | 0 de 7 | 1608 / 1537 / 1736 |
| propio | como el ATD, sin bloques | flag | 0.431 | 0.407 | -0.024 [-0.034 a -0.014] | 1 de 7 | 1608 / 1537 / 3061 |
| propio, balón a la vista en los D | como el ATD | control | 0.587 | 0.546 | -0.041 [-0.055 a -0.029] | 0 de 7 | 1606 / 1613 / 1736 |
| propio, balón a la vista en los D | como el ATD | flag | 0.395 | 0.366 | -0.029 [-0.039 a -0.019] | 0 de 7 | 1606 / 1613 / 3061 |
| propio, balón a la vista en los D | como el ATD, sin bloques | control | 0.613 | 0.586 | -0.026 [-0.038 a -0.015] | 1 de 7 | 1665 / 1621 / 1736 |
| propio, balón a la vista en los D | como el ATD, sin bloques | flag | 0.409 | 0.396 | -0.013 [-0.022 a -0.004] | 1 de 7 | 1665 / 1621 / 3061 |

Regla: punto 1 (control, +0.005 y 6 de 7 en las 4 celdas): **no pasa** · punto 3 (flag, no pierde más de 0.005): **no pasa** · balón a la vista en los `D` (no pierde más de 0.005 con ninguna convención): **no pasa**.

Sin el partido del piloto (J03WMX), descriptivo: etiquetas · como el ATD · control: -0.097 (0 de 6); etiquetas · como el ATD · flag: -0.064 (0 de 6); etiquetas · como el ATD, sin bloques · control: -0.077 (0 de 6); etiquetas · como el ATD, sin bloques · flag: -0.048 (0 de 6); propio · como el ATD · control: -0.061 (0 de 6); propio · como el ATD · flag: -0.038 (0 de 6); propio · como el ATD, sin bloques · control: -0.047 (0 de 6); propio · como el ATD, sin bloques · flag: -0.030 (0 de 6); propio, balón a la vista en los D · como el ATD · control: -0.043 (0 de 6); propio, balón a la vista en los D · como el ATD · flag: -0.030 (0 de 6); propio, balón a la vista en los D · como el ATD, sin bloques · control: -0.029 (1 de 6); propio, balón a la vista en los D · como el ATD, sin bloques · flag: -0.017 (0 de 6).

Los valores de α, uno a uno (descriptivo; diferencia con `main` y en cuántos gana):

| α | control, como el ATD, `D` etiquetas | flag, como el ATD, `D` etiquetas | control, como el ATD, sin bloques, `D` etiquetas | flag, como el ATD, sin bloques, `D` etiquetas | control, como el ATD, `D` propio | flag, como el ATD, `D` propio | control, como el ATD, sin bloques, `D` propio | flag, como el ATD, sin bloques, `D` propio |
|---|---|---|---|---|---|---|---|---|
| 4 | -0.096 (0) | -0.060 (0) | -0.075 (0) | -0.041 (0) | -0.062 (0) | -0.036 (0) | -0.045 (0) | -0.024 (1) |

## Veredicto con la regla (puntos 1 y 3; el 2, SkillCorner, solo se abre si pasan)

- K2: punto 1 no pasa, punto 3 no pasa, balón a la vista no pasa → **no sigue** (ganancia media con control en las 4 celdas: -0.069)
