# Lo siguiente de K2: promediar modelos (K6), un proveedor más (K7) y entrenar por secuencia (K8)

- **Quién y cuándo:** Claude, en una sesión de Ismael, el 17/11/2026. Lo coordinó y revisó otra sesión de Claude (la que
  hizo el estudio de K2 y K3). Rama `exp/k2-siguiente`, que sale de `exp/k2-refinar` en `4a67424`.
- **Encargo:** «seguir mejorando la red K2 (evidencia de equipo) por orden de prioridad».
- **Regla nº 1 respetada.** No se ha abierto nada del partido. Todo se midió en datos abiertos de otros partidos:
  - los 7 de la Bundesliga (DFL; Bassek et al., 2025, CC BY 4.0);
  - los 10 de entrenamiento de SkillCorner (A-League 2024/25, MIT). **El examen de SkillCorner no se ha leído**;
  - los 3 de Metrica sample-data.
- **Reglas escritas antes de medir:** `docs/decisiones.md`, 17/11, entradas K6a, K7 y K8, cada una en su commit antes de
  entrenar o medir.
- **Etiquetas:** [medido] en esta sesión, con la salida en `validation/conjunto/salidas/`; [inferencia] es una lectura
  mía.
- **Nada de esto cambia la entrega.** Mientras se hacía, Ismael decidió entregar con K3 (`main`, `23dcbc1`). Esta rama
  no toca `pipeline.PIECES`.

Para leerlo sin el resto del repo:
- **`main`, en las tablas de aquí,** es la evidencia de equipo B5: una regresión logística sobre unos 30 resúmenes por
  frame. Es la referencia de todo el estudio de K2, aunque la entrega ya lleve K3.
- **K2** es la red que mira a cada jugador (`validation/resultados/2026-11-17_modelo_conjunto.md`). Gana a B5 dentro de
  los proveedores que ha visto, y fuera de ellos va de un empate a una pérdida pequeña.
- **K3** es la media de K2 y B5 (`2026-11-17_refinamientos_k2.md`). Es la que va en la entrega.
- **Las cifras son diferencias de spellF1.** Por debajo de unos ±0,01 es ruido.

## En pocas líneas

1. **K6a, promediar los 8 modelos de K2 que ya existen, no mueve nada en Metrica** [medido]: +0,001 de media frente a
   K2, dentro del ruido (±0,01). La idea de promediar no se cierra, porque 3 partidos ven poco; queda en espera.
2. **K7, entrenar con Metrica como un proveedor más, no ayuda a trasladarse a SkillCorner** [medido].
   - Con una sola salida (K7c) queda como los modelos de solo la DFL (+0,001 de media).
   - Con una salida por proveedor (K7s) pierde (−0,012), porque la salida de Metrica aprende su convención, que cambia
     de equipo de más.
   - La salida por proveedor con la DFL y SkillCorner, que es el montaje de la entrega, queda sin probar.
3. **Sin ver el balón, K2 sabe bastante más que B5** [medido]:
   - en la DFL «como el ATD», K2 acierta el equipo en el 89 % de los frames de juego sin balón y B5 en el 84 %;
   - en SkillCorner, 73 % frente a 66 %;
   - con balón, los dos están a 2 puntos o menos.

   En el partido falta el balón en el 41 % de lo evaluado.
4. **K8, entrenar con la energía del decodificador:** ver la sección de K8.
5. **Queda listo para la GPU** el comando que entrena y mide una ronda de 8 pliegues (`LISTO_PARA_GPU.md`).

## K6a: la media de los 8 juegos de pesos de K2, sin entrenar

- **Qué es.** `conjunto_pesos.npz` trae 8 juegos de pesos de K2: los 7 pliegues y el de «todos». Ninguno vio Metrica.
  K6a es la media de sus 8 salidas. Es un filtro para decidir si merece la pena entrenar varias semillas de K2 y
  promediarlas.
- **Regla:** «apunta bien» si frente a K2 la media de las 4 celdas de Metrica llega a +0,003 y ninguna baja de −0,002.
  Si no, K6 no se cierra, porque 3 partidos ven poco, y queda detrás de K7 y K8.
- **Resultado** [medido]: −0,000, +0,003, +0,002 y −0,001 frente a K2. Partido a partido, de −0,013 a +0,012. **No
  apunta bien.**
- **Un hallazgo de paso** [medido]: en Metrica, sin balón, K2 acierta el equipo solo en el 44,7 % de los frames, menos
  que una moneda. En la DFL acierta el 89 %, así que el problema es de las etiquetas de Metrica (sacadas de eventos), no
  de K2. Por eso esos frames no cuentan al entrenar K7 [inferencia, con la medida de la DFL como razón].

## K7: Metrica como un proveedor más en el entrenamiento

- **Qué se probó.** K2 entrenado con la DFL y Metrica, sin SkillCorner, y puntuado en SkillCorner (10 partidos) frente a
  los tres modelos de solo la DFL que ya había.
  - SkillCorner es el sentido difícil: de un tracking limpio a uno automático, como del entrenamiento al partido.
  - Metrica fue un cuarto del lote.
  - Dos variantes: K7c, con una sola salida, y K7s, con una salida por proveedor, usando en un proveedor nuevo la media
    de las dos.
- **Regla:** una variante «se traslada mejor» si queda en lo mejor de los tres modelos o por encima en las 4 celdas, y su
  media llega a +0,004 frente a `main`.
- **Resultado** [medido], frente a `main`:

| versión | etiquetas, detectado | etiquetas, suavizado | propio, detectado | propio, suavizado | media |
|---|---|---|---|---|---|
| lo mejor de los tres de solo la DFL | −0,005 | +0,001 | −0,000 | +0,003 | – |
| K7c, una sola salida | −0,007 | +0,003 | +0,000 | +0,008 | +0,001 |
| K7s, la media de las dos salidas (vota) | −0,026 | −0,020 | −0,004 | +0,000 | −0,012 |
| K7s, solo la salida de la DFL (sin voto) | −0,004 | −0,001 | +0,006 | +0,007 | +0,002 |
| K7s, solo la salida de Metrica (sin voto) | −0,057 | −0,047 | −0,017 | −0,013 | −0,034 |

- **Con la regla, no pasa ninguna.** La lectura, escrita antes: «Metrica no ayuda a trasladarse a un tracking
  automático», no «las salidas por proveedor no sirven».
- **Lo que se ve** [inferencia]:
  - Las dos salidas sí separan las convenciones. La de Metrica, entrenada con etiquetas de eventos, predice 3.194
    posesiones en SkillCorner, frente a 2.422 la de la DFL (hay 3.228).
  - Si algún día se prueba una salida por proveedor para la entrega, la salida que se use en el partido hay que decidirla
    antes, y la media de las dos no es una elección neutra.
  - **Para la ronda con GPU:** separar las salidas sí separa las convenciones. La salida de la DFL, sola, queda como los
    modelos de solo la DFL (+0,002), y la de Metrica, sola, pierde 0,034. En el partido habría que usar la salida de
    control, no la media. Eso es lo que falta probar en el montaje de la entrega, con la DFL y SkillCorner.

## K8: entrenar con la energía del decodificador (piloto)

[pendiente: se rellena con el resultado del piloto]

## Las comprobaciones del instrumento y lo que pasó por el camino

- **Cada medida repite antes lo publicado** de `main` y de K2 (o de las réplicas) y se para si no sale. Ha salido en
  todas [medido].
- **Comprobaciones del código nuevo** [medido]:
  - la exportación de Metrica es la del lector, frame a frame;
  - el entrenamiento de K7 con Metrica a 0 da los pesos de K2 bit a bit;
  - los pesos pasados a numpy dan la salida de torch, con diferencias de 4e-6 o menos;
  - la pérdida por secuencia de K8 da lo mismo que enumerar todos los caminos.
- **K8 con su término a cero da los pesos de K2 salvo redondeo** (3e-6 tras 20 pasos), no bit a bit.
  - Cada script se repite bit a bit consigo mismo [medido]. El último bit entre dos scripts depende de cómo queda la
    memoria de cada proceso [inferencia].
  - Para lo que sirve la comprobación (ver que los datos, el azar y la red son los mismos) vale; una diferencia de verdad
    daría cuatro órdenes de magnitud más.
- **Un entrenamiento se cortó por falta de memoria** (otros procesos de la máquina). Desde entonces, los entrenamientos
  de K7 y K8 guardan un punto de control cada 500 pasos y reanudan solos desde él, con los mismos pesos bit a bit
  [medido].

## Lo que no se ha podido medir

- **Una ronda de 8 pliegues de cualquier candidato.** En este portátil son unas 7 horas, y la máquina de la GPU no estaba
  disponible.
- **La salida por proveedor con la DFL y SkillCorner** (el montaje de la entrega): pide esa ronda.
- **Cuánto baila K2 de un entrenamiento a otro dentro del proveedor,** salvo la pareja del piloto de K8.
- **Nada frente a K3,** que es lo que va en la entrega: si algo pasara, habría que mirarlo con otra regla.

## Listo para la GPU

`validation/conjunto/LISTO_PARA_GPU.md`: qué hace falta antes (rama, entorno y caché), un comando para entrenar los 8
pliegues (`ronda_pliegues.py`) y otro para medirlos frente a K2 y a `main` (`medir_pliegues.py`), y qué pegar después.
`medir_pliegues.py --comprobar` da lo publicado [medido]. Solo se ejecuta para un candidato cuyo piloto haya pasado.

## Ficheros

| fichero | qué es |
|---|---|
| `validation/conjunto/k6.py` | K6a en Metrica |
| `validation/conjunto/signo_sin_balon.py` | el acierto del signo de z con balón y sin él, para K2 y B5 |
| `validation/conjunto/exportar_metrica.py`, `entrenar_k7.py`, `juntar_k7.py`, `comprobar_k7.py`, `k7.py` | K7: exportar Metrica, entrenar, pasar a numpy, comprobar y medir |
| `validation/conjunto/crf.py`, `entrenar_k8.py`, `comprobar_k8.py`, `piloto_k8.py` | K8: la pérdida por secuencia, entrenar, comprobar y el piloto |
| `validation/conjunto/puntos.py`, `comprobar_puntos.py` | puntos de control de los entrenamientos y su comprobación |
| `validation/conjunto/ronda_pliegues.py`, `medir_pliegues.py`, `LISTO_PARA_GPU.md` | la ronda de 8 pliegues para la GPU |
| `validation/conjunto/salidas/2026-11-17_k6a_*`, `…_signo_sin_balon.md`, `…_entrenamiento_k7*`, `…_k7*_en_skillcorner.md`, `…_medir_pliegues_comprobar.md`, `…_entrenamiento_k2cpu_s26.md`, `…_entrenamiento_k8_s26.md`, `…_piloto_k8.md` | las salidas agregadas |
