# K7s · tanda «k7s» · semilla 20261124

Entrena con 7 partidos de la DFL y 3 de Metrica, sin SkillCorner. Variante s: una z por proveedor; fuera, la media de las dos.
Limpieza de Metrica: dejan de contar 41550 de 280343 frames vivos (14.8 %), los que no tienen balón crudo.
Configuración: {"abandono": 0.1, "calentamiento": 100, "canales": 40, "decaimiento": 0.0001, "dilaciones": [1, 2, 4, 8, 16, 32], "grupos": 512, "hueco": [25, 100], "lote": 32, "margen": 64, "oculto": 32, "p_10hz": 0.0, "p_a_la_vista": 0.5, "p_duplicado": 0.25, "p_falta": 0.06, "p_hueco": 0.3, "p_rato": 0.1, "p_ruido": 0.0, "pasos": 3000, "peso_cambios": 1.0, "peso_flag": 0.3, "rato": [25, 125], "retraso_max": 5, "sigma_duplicado": 0.4, "sigma_ruido": 0.2, "tasa": 0.002, "visibilidad_min": 1.0}
Parte de Metrica en el lote: 0.25 · dispositivo cpu · torch 2.15.0+cpu · hilos 12 · columnas de slots 33

Pesos: 36301
paso     1 · z 0.6994 · cambios 1.2327 · flag 0.6919 · 5 s
paso   250 · z 0.2837 · cambios 0.2327 · flag 0.3410 · 305 s
paso   500 · z 0.1584 · cambios 0.1365 · flag 0.2222 · 550 s
paso   750 · z 0.1426 · cambios 0.1275 · flag 0.2045 · 771 s
paso  1000 · z 0.1344 · cambios 0.1204 · flag 0.1948 · 988 s
paso  1250 · z 0.1259 · cambios 0.1150 · flag 0.1860 · 1231 s
paso  1500 · z 0.1195 · cambios 0.1119 · flag 0.1810 · 1489 s
paso  1750 · z 0.1120 · cambios 0.1079 · flag 0.1766 · 1738 s
paso  2000 · z 0.1078 · cambios 0.1058 · flag 0.1730 · 2103 s
paso  2250 · z 0.1039 · cambios 0.1027 · flag 0.1671 · 2343 s
paso  2500 · z 0.0994 · cambios 0.1008 · flag 0.1642 · 2595 s
paso  2750 · z 0.0952 · cambios 0.0983 · flag 0.1608 · 2823 s
paso  3000 · z 0.0969 · cambios 0.0988 · flag 0.1633 · 3046 s

Pesos en k7s_todos.pt.

## Fuera de muestra: SkillCorner, mitad de entrenamiento, que este modelo no vio (descriptivo, umbral 0,5)

| partido | balón | acierto de z en los vivos | pérdida de z | cambios | vistos | avisos por minuto vivo | avisos buenos |
|---|---|---|---|---|---|---|---|
| sc 1874553 | detectado | 84.8 % | 0.5776 | 222 | 15 % | 2.4 | 28 % |
| sc 1874553 | detectado, suavizado | 84.7 % | 0.5584 | 222 | 13 % | 1.9 | 27 % |
| sc 1899585 | detectado | 80.6 % | 0.6790 | 198 | 18 % | 2.6 | 28 % |
| sc 1899585 | detectado, suavizado | 80.9 % | 0.6627 | 198 | 15 % | 2.1 | 28 % |
| sc 1927964 | detectado | 87.5 % | 0.5107 | 200 | 16 % | 2.0 | 28 % |
| sc 1927964 | detectado, suavizado | 87.4 % | 0.4972 | 200 | 14 % | 1.6 | 29 % |
| sc 1959846 | detectado | 83.2 % | 0.6514 | 211 | 15 % | 2.7 | 24 % |
| sc 1959846 | detectado, suavizado | 83.5 % | 0.6356 | 211 | 14 % | 2.3 | 25 % |
| sc 1996435 | detectado | 82.8 % | 0.6758 | 262 | 13 % | 2.3 | 28 % |
| sc 1996435 | detectado, suavizado | 83.0 % | 0.6531 | 262 | 12 % | 2.0 | 29 % |
| sc 2006229 | detectado | 85.5 % | 0.6084 | 230 | 15 % | 2.4 | 27 % |
| sc 2006229 | detectado, suavizado | 85.6 % | 0.5977 | 230 | 14 % | 1.9 | 32 % |
| sc 2007448 | detectado | 85.0 % | 0.6469 | 194 | 13 % | 2.4 | 22 % |
| sc 2007448 | detectado, suavizado | 84.9 % | 0.6347 | 194 | 12 % | 1.8 | 26 % |
| sc 2010085 | detectado | 84.0 % | 0.6118 | 192 | 12 % | 2.4 | 18 % |
| sc 2010085 | detectado, suavizado | 84.0 % | 0.6069 | 192 | 10 % | 1.8 | 20 % |
| sc 2013725 | detectado | 78.3 % | 0.7876 | 263 | 16 % | 3.6 | 23 % |
| sc 2013725 | detectado, suavizado | 78.5 % | 0.7686 | 263 | 14 % | 2.7 | 27 % |
| sc 2016236 | detectado | 80.7 % | 0.7117 | 238 | 17 % | 2.7 | 28 % |
| sc 2016236 | detectado, suavizado | 80.6 % | 0.7007 | 238 | 14 % | 2.2 | 27 % |

Hecho en 3069 s.
