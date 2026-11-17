# Modelo conjunto frente a `main` · tanda «piloto1» · SkillCorner, mitad de entrenamiento · 2 partidos

Código: b4ec45f · bootstrap pareado de 200 · `main` = B5, `dead_state` y `decode_cortas_a_d`.

## Candidato K1 (descriptivo: todos los valores de γ, sin elegir)

| γ | `D` | condición | main | candidato | diferencia [5–95 %] | gana en | posesiones: candidato / main / reales |
|---|---|---|---|---|---|---|---|
| 2 | etiquetas | detectado | 0.498 | 0.494 | -0.004 [-0.008 a +0.001] | 1 de 2 | 444 / 430 / 611 |
| 2 | etiquetas | detectado, suavizado | 0.490 | 0.486 | -0.004 [-0.009 a +0.002] | 0 de 2 | 443 / 428 / 611 |
| 2 | propio | detectado | 0.397 | 0.398 | +0.001 [-0.006 a +0.009] | 1 de 2 | 419 / 409 / 611 |
| 2 | propio | detectado, suavizado | 0.390 | 0.391 | +0.001 [-0.006 a +0.008] | 1 de 2 | 417 / 407 / 611 |
| 4 | etiquetas | detectado | 0.498 | 0.493 | -0.005 [-0.011 a +0.002] | 1 de 2 | 447 / 430 / 611 |
| 4 | etiquetas | detectado, suavizado | 0.490 | 0.486 | -0.004 [-0.010 a +0.003] | 0 de 2 | 447 / 428 / 611 |
| 4 | propio | detectado | 0.397 | 0.398 | +0.001 [-0.009 a +0.010] | 1 de 2 | 421 / 409 / 611 |
| 4 | propio | detectado, suavizado | 0.390 | 0.399 | +0.009 [-0.000 a +0.019] | 2 de 2 | 419 / 407 / 611 |
| 8 | etiquetas | detectado | 0.498 | 0.492 | -0.006 [-0.016 a +0.004] | 0 de 2 | 464 / 430 / 611 |
| 8 | etiquetas | detectado, suavizado | 0.490 | 0.492 | +0.002 [-0.010 a +0.014] | 1 de 2 | 463 / 428 / 611 |
| 8 | propio | detectado | 0.397 | 0.402 | +0.005 [-0.008 a +0.017] | 1 de 2 | 427 / 409 / 611 |
| 8 | propio | detectado, suavizado | 0.390 | 0.408 | +0.018 [+0.005 a +0.031] | 2 de 2 | 430 / 407 / 611 |

## Candidato K2 (descriptivo: todos los valores de α, sin elegir)

| α | `D` | condición | main | candidato | diferencia [5–95 %] | gana en | posesiones: candidato / main / reales |
|---|---|---|---|---|---|---|---|
| 0.0625 | etiquetas | detectado | 0.498 | 0.512 | +0.014 [-0.008 a +0.038] | 1 de 2 | 456 / 430 / 611 |
| 0.0625 | etiquetas | detectado, suavizado | 0.490 | 0.510 | +0.020 [-0.002 a +0.044] | 1 de 2 | 453 / 428 / 611 |
| 0.0625 | propio | detectado | 0.397 | 0.401 | +0.004 [-0.015 a +0.024] | 1 de 2 | 438 / 409 / 611 |
| 0.0625 | propio | detectado, suavizado | 0.390 | 0.395 | +0.006 [-0.012 a +0.028] | 2 de 2 | 438 / 407 / 611 |
| 0.125 | etiquetas | detectado | 0.498 | 0.530 | +0.032 [+0.014 a +0.053] | 2 de 2 | 431 / 430 / 611 |
| 0.125 | etiquetas | detectado, suavizado | 0.490 | 0.520 | +0.030 [+0.012 a +0.053] | 2 de 2 | 442 / 428 / 611 |
| 0.125 | propio | detectado | 0.397 | 0.416 | +0.019 [+0.003 a +0.035] | 2 de 2 | 420 / 409 / 611 |
| 0.125 | propio | detectado, suavizado | 0.390 | 0.407 | +0.018 [+0.002 a +0.036] | 2 de 2 | 423 / 407 / 611 |
| 0.25 | etiquetas | detectado | 0.498 | 0.532 | +0.034 [+0.015 a +0.054] | 2 de 2 | 416 / 430 / 611 |
| 0.25 | etiquetas | detectado, suavizado | 0.490 | 0.531 | +0.041 [+0.022 a +0.059] | 2 de 2 | 420 / 428 / 611 |
| 0.25 | propio | detectado | 0.397 | 0.413 | +0.016 [-0.000 a +0.033] | 2 de 2 | 398 / 409 / 611 |
| 0.25 | propio | detectado, suavizado | 0.390 | 0.414 | +0.024 [+0.008 a +0.042] | 2 de 2 | 398 / 407 / 611 |
| 0.5 | etiquetas | detectado | 0.498 | 0.554 | +0.056 [+0.040 a +0.072] | 2 de 2 | 404 / 430 / 611 |
| 0.5 | etiquetas | detectado, suavizado | 0.490 | 0.544 | +0.054 [+0.036 a +0.072] | 2 de 2 | 408 / 428 / 611 |
| 0.5 | propio | detectado | 0.397 | 0.427 | +0.030 [+0.017 a +0.046] | 2 de 2 | 393 / 409 / 611 |
| 0.5 | propio | detectado, suavizado | 0.390 | 0.416 | +0.026 [+0.011 a +0.043] | 2 de 2 | 394 / 407 / 611 |
| 1 | etiquetas | detectado | 0.498 | 0.552 | +0.054 [+0.040 a +0.071] | 2 de 2 | 406 / 430 / 611 |
| 1 | etiquetas | detectado, suavizado | 0.490 | 0.544 | +0.054 [+0.038 a +0.074] | 2 de 2 | 408 / 428 / 611 |
| 1 | propio | detectado | 0.397 | 0.424 | +0.027 [+0.012 a +0.043] | 2 de 2 | 396 / 409 / 611 |
| 1 | propio | detectado, suavizado | 0.390 | 0.418 | +0.029 [+0.014 a +0.046] | 2 de 2 | 393 / 407 / 611 |
| 2 | etiquetas | detectado | 0.498 | 0.550 | +0.052 [+0.037 a +0.070] | 2 de 2 | 418 / 430 / 611 |
| 2 | etiquetas | detectado, suavizado | 0.490 | 0.539 | +0.049 [+0.032 a +0.070] | 2 de 2 | 413 / 428 / 611 |
| 2 | propio | detectado | 0.397 | 0.424 | +0.027 [+0.013 a +0.043] | 2 de 2 | 404 / 409 / 611 |
| 2 | propio | detectado, suavizado | 0.390 | 0.421 | +0.031 [+0.014 a +0.049] | 2 de 2 | 397 / 407 / 611 |
| 4 | etiquetas | detectado | 0.498 | 0.548 | +0.050 [+0.033 a +0.068] | 2 de 2 | 437 / 430 / 611 |
| 4 | etiquetas | detectado, suavizado | 0.490 | 0.540 | +0.050 [+0.030 a +0.072] | 2 de 2 | 435 / 428 / 611 |
| 4 | propio | detectado | 0.397 | 0.429 | +0.032 [+0.017 a +0.050] | 2 de 2 | 416 / 409 / 611 |
| 4 | propio | detectado, suavizado | 0.390 | 0.423 | +0.033 [+0.016 a +0.051] | 2 de 2 | 418 / 407 / 611 |
| 8 | etiquetas | detectado | 0.498 | 0.533 | +0.035 [+0.015 a +0.053] | 2 de 2 | 472 / 430 / 611 |
| 8 | etiquetas | detectado, suavizado | 0.490 | 0.521 | +0.031 [+0.011 a +0.052] | 2 de 2 | 469 / 428 / 611 |
| 8 | propio | detectado | 0.397 | 0.414 | +0.017 [+0.002 a +0.034] | 2 de 2 | 446 / 409 / 611 |
| 8 | propio | detectado, suavizado | 0.390 | 0.408 | +0.019 [+0.000 a +0.037] | 2 de 2 | 440 / 407 / 611 |
