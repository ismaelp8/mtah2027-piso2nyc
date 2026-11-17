# Modelo conjunto · tanda «r2_solo_dfl» · pliegue todos · semilla 20261125

Entrena con 7 partidos de la DFL y 0 de SkillCorner; deja fuera: 1874553, 1899585, 1927964, 1959846, 1996435, 2006229, 2007448, 2010085, 2013725, 2016236.
Configuración: {"abandono": 0.1, "calentamiento": 100, "canales": 40, "decaimiento": 0.0001, "dilaciones": [1, 2, 4, 8, 16, 32], "grupos": 512, "hueco": [25, 100], "lote": 32, "margen": 64, "oculto": 32, "p_10hz": 0.0, "p_a_la_vista": 0.5, "p_duplicado": 0.25, "p_falta": 0.06, "p_hueco": 0.3, "p_rato": 0.1, "p_ruido": 0.0, "pasos": 3000, "peso_cambios": 1.0, "peso_flag": 0.3, "rato": [25, 125], "retraso_max": 5, "sigma_duplicado": 0.4, "sigma_ruido": 0.2, "tasa": 0.002, "visibilidad_min": 1.0}

Pesos: 36260
paso     1 · z 0.6916 · cambios 1.4469 · flag 0.6899 · 3 s
paso   250 · z 0.3283 · cambios 0.2569 · flag 0.3741 · 250 s
paso   500 · z 0.1692 · cambios 0.1302 · flag 0.2259 · 526 s
paso   750 · z 0.1509 · cambios 0.1183 · flag 0.2055 · 749 s
paso  1000 · z 0.1370 · cambios 0.1092 · flag 0.1936 · 954 s
paso  1250 · z 0.1256 · cambios 0.1023 · flag 0.1847 · 1163 s
paso  1500 · z 0.1182 · cambios 0.0977 · flag 0.1820 · 1403 s
paso  1750 · z 0.1077 · cambios 0.0932 · flag 0.1746 · 1661 s
paso  2000 · z 0.1012 · cambios 0.0883 · flag 0.1677 · 1922 s
paso  2250 · z 0.0965 · cambios 0.0860 · flag 0.1665 · 2139 s
paso  2500 · z 0.0924 · cambios 0.0839 · flag 0.1641 · 2541 s
paso  2750 · z 0.0913 · cambios 0.0822 · flag 0.1652 · 2919 s
paso  3000 · z 0.0909 · cambios 0.0842 · flag 0.1644 · 3152 s

## Fuera de muestra: los partidos que el pliegue no vio (descriptivo, umbral 0,5)

| partido | balón | acierto de z en los vivos | pérdida de z | cambios | vistos | avisos por minuto vivo | avisos buenos |
|---|---|---|---|---|---|---|---|
| sc 1874553 | detectado | 85.4 % | 0.6759 | 222 | 13 % | 2.1 | 26 % |
| sc 1874553 | detectado, suavizado | 85.2 % | 0.6611 | 222 | 13 % | 1.8 | 29 % |
| sc 1899585 | detectado | 81.0 % | 0.7823 | 198 | 18 % | 2.5 | 29 % |
| sc 1899585 | detectado, suavizado | 80.9 % | 0.7607 | 198 | 16 % | 2.0 | 32 % |
| sc 1927964 | detectado | 88.0 % | 0.5997 | 200 | 15 % | 1.7 | 28 % |
| sc 1927964 | detectado, suavizado | 87.9 % | 0.5764 | 200 | 15 % | 1.5 | 33 % |
| sc 1959846 | detectado | 84.2 % | 0.7710 | 211 | 14 % | 2.6 | 24 % |
| sc 1959846 | detectado, suavizado | 84.3 % | 0.7437 | 211 | 14 % | 2.4 | 25 % |
| sc 1996435 | detectado | 83.8 % | 0.8017 | 262 | 14 % | 2.4 | 29 % |
| sc 1996435 | detectado, suavizado | 83.7 % | 0.7653 | 262 | 13 % | 2.1 | 30 % |
| sc 2006229 | detectado | 86.1 % | 0.7760 | 230 | 14 % | 2.1 | 29 % |
| sc 2006229 | detectado, suavizado | 85.9 % | 0.7520 | 230 | 12 % | 1.8 | 28 % |
| sc 2007448 | detectado | 85.4 % | 0.7854 | 194 | 13 % | 2.2 | 25 % |
| sc 2007448 | detectado, suavizado | 85.3 % | 0.7735 | 194 | 14 % | 2.0 | 28 % |
| sc 2010085 | detectado | 84.2 % | 0.7327 | 192 | 8 % | 1.9 | 17 % |
| sc 2010085 | detectado, suavizado | 84.4 % | 0.7173 | 192 | 9 % | 1.8 | 19 % |
| sc 2013725 | detectado | 79.7 % | 0.9037 | 263 | 17 % | 3.1 | 29 % |
| sc 2013725 | detectado, suavizado | 79.6 % | 0.8820 | 263 | 17 % | 2.7 | 33 % |
| sc 2016236 | detectado | 81.3 % | 0.8531 | 238 | 16 % | 2.6 | 28 % |
| sc 2016236 | detectado, suavizado | 81.3 % | 0.8321 | 238 | 15 % | 2.4 | 28 % |

Hecho en 3197 s.
