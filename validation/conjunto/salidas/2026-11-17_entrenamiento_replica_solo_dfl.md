# Modelo conjunto · tanda «r_solo_dfl» · pliegue todos · semilla 20261124

Entrena con 7 partidos de la DFL y 0 de SkillCorner; deja fuera: 1874553, 1899585, 1927964, 1959846, 1996435, 2006229, 2007448, 2010085, 2013725, 2016236.
Configuración: {"abandono": 0.1, "calentamiento": 100, "canales": 40, "decaimiento": 0.0001, "dilaciones": [1, 2, 4, 8, 16, 32], "grupos": 512, "hueco": [25, 100], "lote": 32, "margen": 64, "oculto": 32, "p_10hz": 0.0, "p_a_la_vista": 0.5, "p_duplicado": 0.25, "p_falta": 0.06, "p_hueco": 0.3, "p_rato": 0.1, "p_ruido": 0.0, "pasos": 3000, "peso_cambios": 1.0, "peso_flag": 0.3, "rato": [25, 125], "retraso_max": 5, "sigma_duplicado": 0.4, "sigma_ruido": 0.2, "tasa": 0.002, "visibilidad_min": 1.0}

Pesos: 36260
paso     1 · z 0.6955 · cambios 1.1897 · flag 0.6926 · 3 s
paso   250 · z 0.2951 · cambios 0.2187 · flag 0.3483 · 274 s
paso   500 · z 0.1660 · cambios 0.1270 · flag 0.2225 · 535 s
paso   750 · z 0.1462 · cambios 0.1139 · flag 0.2007 · 782 s
paso  1000 · z 0.1380 · cambios 0.1081 · flag 0.1925 · 1105 s
paso  1250 · z 0.1263 · cambios 0.1011 · flag 0.1841 · 1583 s
paso  1500 · z 0.1160 · cambios 0.0949 · flag 0.1757 · 1908 s
paso  1750 · z 0.1055 · cambios 0.0906 · flag 0.1721 · 2146 s
paso  2000 · z 0.1003 · cambios 0.0886 · flag 0.1700 · 2376 s
paso  2250 · z 0.0927 · cambios 0.0838 · flag 0.1659 · 2604 s
paso  2500 · z 0.0907 · cambios 0.0835 · flag 0.1652 · 2837 s
paso  2750 · z 0.0867 · cambios 0.0820 · flag 0.1631 · 3066 s
paso  3000 · z 0.0857 · cambios 0.0811 · flag 0.1625 · 3303 s

## Fuera de muestra: los partidos que el pliegue no vio (descriptivo, umbral 0,5)

| partido | balón | acierto de z en los vivos | pérdida de z | cambios | vistos | avisos por minuto vivo | avisos buenos |
|---|---|---|---|---|---|---|---|
| sc 1874553 | detectado | 84.9 % | 0.6894 | 222 | 15 % | 2.4 | 26 % |
| sc 1874553 | detectado, suavizado | 85.0 % | 0.6739 | 222 | 11 % | 2.0 | 23 % |
| sc 1899585 | detectado | 81.2 % | 0.7783 | 198 | 19 % | 2.7 | 28 % |
| sc 1899585 | detectado, suavizado | 81.0 % | 0.7638 | 198 | 16 % | 2.4 | 26 % |
| sc 1927964 | detectado | 88.1 % | 0.5740 | 200 | 18 % | 1.7 | 33 % |
| sc 1927964 | detectado, suavizado | 88.1 % | 0.5562 | 200 | 15 % | 1.5 | 33 % |
| sc 1959846 | detectado | 83.8 % | 0.7929 | 211 | 13 % | 2.3 | 24 % |
| sc 1959846 | detectado, suavizado | 83.6 % | 0.7704 | 211 | 12 % | 2.2 | 23 % |
| sc 1996435 | detectado | 84.3 % | 0.7637 | 262 | 15 % | 2.4 | 29 % |
| sc 1996435 | detectado, suavizado | 84.4 % | 0.7305 | 262 | 13 % | 2.0 | 31 % |
| sc 2006229 | detectado | 85.4 % | 0.7806 | 230 | 13 % | 1.9 | 29 % |
| sc 2006229 | detectado, suavizado | 85.3 % | 0.7564 | 230 | 12 % | 1.7 | 30 % |
| sc 2007448 | detectado | 85.7 % | 0.7709 | 194 | 15 % | 2.1 | 28 % |
| sc 2007448 | detectado, suavizado | 85.7 % | 0.7549 | 194 | 14 % | 1.9 | 31 % |
| sc 2010085 | detectado | 84.4 % | 0.7190 | 192 | 11 % | 2.1 | 18 % |
| sc 2010085 | detectado, suavizado | 84.5 % | 0.7098 | 192 | 11 % | 1.9 | 21 % |
| sc 2013725 | detectado | 80.5 % | 0.9020 | 263 | 15 % | 3.0 | 26 % |
| sc 2013725 | detectado, suavizado | 80.7 % | 0.8744 | 263 | 14 % | 2.5 | 28 % |
| sc 2016236 | detectado | 81.3 % | 0.8468 | 238 | 16 % | 2.9 | 25 % |
| sc 2016236 | detectado, suavizado | 81.1 % | 0.8307 | 238 | 14 % | 2.6 | 23 % |

Hecho en 3348 s.
