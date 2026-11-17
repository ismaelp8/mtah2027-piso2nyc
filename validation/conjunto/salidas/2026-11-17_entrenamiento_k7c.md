# K7c · tanda «k7c» · semilla 20261124

Entrena con 7 partidos de la DFL y 3 de Metrica, sin SkillCorner. Variante c: una sola z.
Limpieza de Metrica: dejan de contar 41550 de 280343 frames vivos (14.8 %), los que no tienen balón crudo.
Configuración: {"abandono": 0.1, "calentamiento": 100, "canales": 40, "decaimiento": 0.0001, "dilaciones": [1, 2, 4, 8, 16, 32], "grupos": 512, "hueco": [25, 100], "lote": 32, "margen": 64, "oculto": 32, "p_10hz": 0.0, "p_a_la_vista": 0.5, "p_duplicado": 0.25, "p_falta": 0.06, "p_hueco": 0.3, "p_rato": 0.1, "p_ruido": 0.0, "pasos": 3000, "peso_cambios": 1.0, "peso_flag": 0.3, "rato": [25, 125], "retraso_max": 5, "sigma_duplicado": 0.4, "sigma_ruido": 0.2, "tasa": 0.002, "visibilidad_min": 1.0}
Parte de Metrica en el lote: 0.25 · dispositivo cpu · torch 2.15.0+cpu · hilos 12 · columnas de slots 33

Pesos: 36260
paso     1 · z 0.6974 · cambios 1.1890 · flag 0.6920 · 2 s
paso   250 · z 0.2928 · cambios 0.2328 · flag 0.3479 · 162 s
paso   500 · z 0.1645 · cambios 0.1369 · flag 0.2241 · 334 s
paso   750 · z 0.1499 · cambios 0.1283 · flag 0.2085 · 505 s
paso  1000 · z 0.1405 · cambios 0.1209 · flag 0.1975 · 676 s
paso  1250 · z 0.1333 · cambios 0.1169 · flag 0.1907 · 843 s
paso  1500 · z 0.1264 · cambios 0.1124 · flag 0.1840 · 1005 s
paso  1750 · z 0.1182 · cambios 0.1081 · flag 0.1782 · 1170 s
paso  2000 · z 0.1142 · cambios 0.1063 · flag 0.1745 · 1334 s
paso  2250 · z 0.1089 · cambios 0.1029 · flag 0.1693 · 1533 s
paso  2500 · z 0.1033 · cambios 0.1008 · flag 0.1664 · 1752 s
# K7c · tanda «k7c» · semilla 20261124

Entrena con 7 partidos de la DFL y 3 de Metrica, sin SkillCorner. Variante c: una sola z.
Limpieza de Metrica: dejan de contar 41550 de 280343 frames vivos (14.8 %), los que no tienen balón crudo.
Configuración: {"abandono": 0.1, "calentamiento": 100, "canales": 40, "decaimiento": 0.0001, "dilaciones": [1, 2, 4, 8, 16, 32], "grupos": 512, "hueco": [25, 100], "lote": 32, "margen": 64, "oculto": 32, "p_10hz": 0.0, "p_a_la_vista": 0.5, "p_duplicado": 0.25, "p_falta": 0.06, "p_hueco": 0.3, "p_rato": 0.1, "p_ruido": 0.0, "pasos": 3000, "peso_cambios": 1.0, "peso_flag": 0.3, "rato": [25, 125], "retraso_max": 5, "sigma_duplicado": 0.4, "sigma_ruido": 0.2, "tasa": 0.002, "visibilidad_min": 1.0}
Parte de Metrica en el lote: 0.25 · dispositivo cpu · torch 2.15.0+cpu · hilos 12 · columnas de slots 33

Pesos: 36260
paso     1 · z 0.6974 · cambios 1.1890 · flag 0.6920 · 4 s
paso   250 · z 0.2928 · cambios 0.2328 · flag 0.3479 · 239 s
paso   500 · z 0.1649 · cambios 0.1369 · flag 0.2245 · 488 s
paso   750 · z 0.1502 · cambios 0.1284 · flag 0.2088 · 718 s
paso  1000 · z 0.1410 · cambios 0.1212 · flag 0.1979 · 959 s
paso  1250 · z 0.1340 · cambios 0.1175 · flag 0.1908 · 1177 s
paso  1500 · z 0.1272 · cambios 0.1132 · flag 0.1844 · 1399 s
paso  1750 · z 0.1192 · cambios 0.1090 · flag 0.1793 · 1620 s
paso  2000 · z 0.1158 · cambios 0.1071 · flag 0.1761 · 1853 s
paso  2250 · z 0.1112 · cambios 0.1037 · flag 0.1707 · 2072 s
paso  2500 · z 0.1054 · cambios 0.1012 · flag 0.1683 · 2286 s
paso  2750 · z 0.1017 · cambios 0.0987 · flag 0.1644 · 2506 s
paso  3000 · z 0.1037 · cambios 0.1001 · flag 0.1672 · 2739 s

Pesos en k7c_todos.pt.

## Fuera de muestra: SkillCorner, mitad de entrenamiento, que este modelo no vio (descriptivo, umbral 0,5)

| partido | balón | acierto de z en los vivos | pérdida de z | cambios | vistos | avisos por minuto vivo | avisos buenos |
|---|---|---|---|---|---|---|---|
| sc 1874553 | detectado | 85.2 % | 0.5521 | 222 | 16 % | 2.0 | 32 % |
| sc 1874553 | detectado, suavizado | 85.6 % | 0.5312 | 222 | 11 % | 1.7 | 27 % |
| sc 1899585 | detectado | 81.5 % | 0.6264 | 198 | 14 % | 2.4 | 24 % |
| sc 1899585 | detectado, suavizado | 81.4 % | 0.6142 | 198 | 12 % | 1.8 | 26 % |
| sc 1927964 | detectado | 88.2 % | 0.4739 | 200 | 16 % | 1.7 | 31 % |
| sc 1927964 | detectado, suavizado | 88.0 % | 0.4650 | 200 | 14 % | 1.4 | 31 % |
| sc 1959846 | detectado | 83.7 % | 0.6157 | 211 | 15 % | 2.6 | 25 % |
| sc 1959846 | detectado, suavizado | 84.1 % | 0.5946 | 211 | 13 % | 2.0 | 28 % |
| sc 1996435 | detectado | 83.9 % | 0.6379 | 262 | 13 % | 2.4 | 26 % |
| sc 1996435 | detectado, suavizado | 83.9 % | 0.6187 | 262 | 10 % | 1.7 | 30 % |
| sc 2006229 | detectado | 85.6 % | 0.6136 | 230 | 13 % | 2.0 | 28 % |
| sc 2006229 | detectado, suavizado | 85.9 % | 0.5994 | 230 | 14 % | 1.7 | 34 % |
| sc 2007448 | detectado | 85.0 % | 0.6419 | 194 | 12 % | 2.0 | 24 % |
| sc 2007448 | detectado, suavizado | 85.2 % | 0.6193 | 194 | 14 % | 1.7 | 33 % |
| sc 2010085 | detectado | 84.3 % | 0.5908 | 192 | 10 % | 2.0 | 19 % |
| sc 2010085 | detectado, suavizado | 84.6 % | 0.5860 | 192 | 8 % | 1.5 | 19 % |
| sc 2013725 | detectado | 79.7 % | 0.7425 | 263 | 15 % | 3.3 | 23 % |
| sc 2013725 | detectado, suavizado | 79.8 % | 0.7205 | 263 | 14 % | 2.5 | 28 % |
| sc 2016236 | detectado | 81.7 % | 0.6637 | 238 | 16 % | 2.5 | 29 % |
| sc 2016236 | detectado, suavizado | 81.7 % | 0.6441 | 238 | 13 % | 2.1 | 29 % |

Hecho en 2759 s.
