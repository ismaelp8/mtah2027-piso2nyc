# Modelo conjunto: entrenamiento con un solo proveedor (comprobación del 17/11)

# Modelo conjunto · tanda «solo_sc» · pliegue todos · semilla 20261124
Entrena con 0 partidos de la DFL y 10 de SkillCorner; deja fuera: J03WMX, J03WN1, J03WOH, J03WOY, J03WPY, J03WQQ, J03WR9.
Pesos: 36260
paso  3000 · z 0.2470 · cambios 0.1912 · flag 0.0000 · 159 s
## Fuera de muestra: los partidos que el pliegue no vio (descriptivo, umbral 0,5)
| partido | balón | acierto de z en los vivos | pérdida de z | cambios | vistos | avisos por minuto vivo | avisos buenos |
| dfl J03WMX | como el ATD | 86.4 % | 0.3313 | 158 | 9 % | 0.9 | 29 % |
| dfl J03WMX | como el ATD, sin bloques | 89.4 % | 0.2379 | 158 | 13 % | 1.1 | 33 % |
| dfl J03WN1 | como el ATD | 83.2 % | 0.3825 | 166 | 7 % | 1.0 | 27 % |
| dfl J03WN1 | como el ATD, sin bloques | 84.8 % | 0.3264 | 166 | 8 % | 1.0 | 29 % |
| dfl J03WOH | como el ATD | 85.0 % | 0.3811 | 144 | 6 % | 0.9 | 19 % |
| dfl J03WOH | como el ATD, sin bloques | 87.9 % | 0.2833 | 144 | 10 % | 1.1 | 26 % |
| dfl J03WOY | como el ATD | 85.2 % | 0.3378 | 142 | 9 % | 0.8 | 36 % |
| dfl J03WOY | como el ATD, sin bloques | 86.4 % | 0.3041 | 142 | 11 % | 0.9 | 36 % |
| dfl J03WPY | como el ATD | 87.2 % | 0.2851 | 138 | 11 % | 0.9 | 31 % |
| dfl J03WPY | como el ATD, sin bloques | 88.1 % | 0.2719 | 138 | 14 % | 0.9 | 39 % |
| dfl J03WQQ | como el ATD | 86.9 % | 0.3309 | 146 | 16 % | 1.2 | 37 % |
| dfl J03WQQ | como el ATD, sin bloques | 90.4 % | 0.2316 | 146 | 18 % | 1.2 | 39 % |
| dfl J03WR9 | como el ATD | 88.6 % | 0.2673 | 132 | 12 % | 0.9 | 31 % |
| dfl J03WR9 | como el ATD, sin bloques | 89.8 % | 0.2253 | 132 | 14 % | 0.9 | 35 % |
Hecho en 169 s.

# Modelo conjunto · tanda «solo_dfl» · pliegue todos · semilla 20261124
Entrena con 7 partidos de la DFL y 0 de SkillCorner; deja fuera: 1874553, 1899585, 1927964, 1959846, 1996435, 2006229, 2007448, 2010085, 2013725, 2016236.
Pesos: 36260
paso  3000 · z 0.0897 · cambios 0.0822 · flag 0.1654 · 157 s
## Fuera de muestra: los partidos que el pliegue no vio (descriptivo, umbral 0,5)
| partido | balón | acierto de z en los vivos | pérdida de z | cambios | vistos | avisos por minuto vivo | avisos buenos |
| sc 1874553 | detectado | 84.6 % | 0.7003 | 222 | 14 % | 2.1 | 27 % |
| sc 1874553 | detectado, suavizado | 84.7 % | 0.6777 | 222 | 13 % | 2.0 | 26 % |
| sc 1899585 | detectado | 80.9 % | 0.7683 | 198 | 15 % | 2.6 | 22 % |
| sc 1899585 | detectado, suavizado | 81.1 % | 0.7381 | 198 | 13 % | 2.3 | 23 % |
| sc 1927964 | detectado | 88.3 % | 0.5709 | 200 | 16 % | 1.6 | 32 % |
| sc 1927964 | detectado, suavizado | 88.2 % | 0.5510 | 200 | 14 % | 1.5 | 29 % |
| sc 1959846 | detectado | 83.5 % | 0.7785 | 211 | 15 % | 2.5 | 25 % |
| sc 1959846 | detectado, suavizado | 83.5 % | 0.7509 | 211 | 13 % | 2.3 | 25 % |
| sc 1996435 | detectado | 83.9 % | 0.7844 | 262 | 13 % | 2.3 | 27 % |
| sc 1996435 | detectado, suavizado | 84.1 % | 0.7455 | 262 | 10 % | 2.0 | 25 % |
| sc 2006229 | detectado | 85.4 % | 0.7815 | 230 | 10 % | 1.9 | 24 % |
| sc 2006229 | detectado, suavizado | 85.4 % | 0.7580 | 230 | 10 % | 1.7 | 26 % |
| sc 2007448 | detectado | 85.0 % | 0.7671 | 194 | 15 % | 2.0 | 30 % |
| sc 2007448 | detectado, suavizado | 85.0 % | 0.7473 | 194 | 15 % | 1.8 | 34 % |
| sc 2010085 | detectado | 84.4 % | 0.7446 | 192 | 12 % | 2.0 | 21 % |
| sc 2010085 | detectado, suavizado | 84.6 % | 0.7298 | 192 | 11 % | 1.9 | 21 % |
| sc 2013725 | detectado | 80.4 % | 0.9121 | 263 | 14 % | 2.8 | 27 % |
| sc 2013725 | detectado, suavizado | 80.2 % | 0.8837 | 263 | 14 % | 2.5 | 27 % |
| sc 2016236 | detectado | 81.2 % | 0.8541 | 238 | 16 % | 2.6 | 26 % |
| sc 2016236 | detectado, suavizado | 81.0 % | 0.8355 | 238 | 11 % | 2.5 | 21 % |
Hecho en 166 s.

