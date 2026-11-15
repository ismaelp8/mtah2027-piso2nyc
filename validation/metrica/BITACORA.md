# Metrica sample-data: la convención de la organizadora · bitácora

> Sale de la revisión externa del 15/11 y de la conversación posterior con Ismael. Solo datos abiertos de
> otros partidos: lo puede ejecutar Claude. Solo agregados. **La regla de esta bitácora se escribe antes de
> puntuar ningún método.**

## 1. Por qué

- SkillCorner ya dijo que B5 aguanta con tracking automático, pero con la convención de SkillCorner.
- Metrica, la organizadora del reto, publica 3 partidos con tracking y eventos sincronizados, y el PDF de
  sus definiciones de eventos. Es la convención «toque con impacto significativo» de
  `docs/investigacion_metodos.md` §8 y del experimento 1.
- El juego 3 está en el formato EPTS del ATD. Sirve además para probar `possession/io.py` con un fichero
  real de Metrica, sin tocar el partido del reto.
- Son 3 partidos. **No sustituye** al harness de la DFL ni a SkillCorner: dice si la ventaja de B5 aguanta
  con otra convención, no elige una versión.

## 2. Los datos

- https://github.com/metrica-sports/sample-data. Piden citar la fuente en cualquier uso público. No hay
  fichero de licencia.
- Juegos 1 y 2: CSV, coordenadas 0–1, campo 105 × 68, 25 fps. El balón va al final del CSV de cada equipo.
- Juego 3: tracking EPTS (`frame:jugadores:balón`) y eventos en JSON.
- Se guardan fuera del repo, en `$MTAH_OPEN_DATA_DIR/metrica`.
- **Cómo llegaron** [medido en la revisión, §8]: los bajó el revisor externo el 15/11, sin script. Los 9
  ficheros de `data/` (175 MB) son, byte a byte, los del commit
  `e706dd506b360d69d9d123d5b8026e7294b13996` del repositorio (15/04/2021): se comparó el hash de git de
  cada fichero con el del repositorio. Para repetirlo, se baja ese commit y se deja su carpeta `data/`
  en `$MTAH_OPEN_DATA_DIR/metrica/data/`.

## 3. Las etiquetas (fijadas antes de medir)

Es la derivación ya escrita en `docs/investigacion_metodos.md` §5.3, precisada aquí:

- **Se para el juego** en el frame de inicio de: `BALL OUT`; `FAULT RECEIVED`; un `SHOT` cuyo subtipo
  contiene `GOAL`; un `BALL LOST` con subtipo `END HALF` u `OFFSIDE`.
- **Se reanuda** en el frame de inicio del siguiente `SET PIECE`. Entre la parada y ese saque, `D`. Antes
  del primer `SET PIECE` de cada parte y después del `END HALF`, `D`.
- **El equipo** en el juego es el del último evento de control en esa parte: `SET PIECE`, `PASS`,
  `RECOVERY`, `SHOT` o `CARRY`. El `CARRY` solo aparece en el juego 3 (los CSV de los juegos 1 y 2 no lo
  traen): es el equipo que conduce el balón, así que es control. Un `CHALLENGE` no cambia el equipo: es
  un duelo, y la definición de Metrica no da la posesión por un toque sin impacto.
- Un frame de juego anterior a cualquier evento de control queda en `X`.
- Las dos partes van separadas por un hueco de `X`, como en el harness.

**Qué convención es:** la de los eventos de Metrica (posesión desde el primer evento con impacto, no el
flag de un proveedor ni el control de 12 frames). Se describe (posesiones por minuto vivo y huella) y no
se corrige.

**Congelada el 15/11, antes de ejecutar `medir.py`.** No se ha editado después de ver la huella de
retrasos ni de compararla con la tabla oficial. Esa comparación no ha cambiado una sola línea de esta
sección.

## 4. El tracking

- Metros con el origen en una esquina: `x_m = x · 105`, `y_m = y · 68`. El (0, 0) de Metrica es la
  esquina superior izquierda. El pipeline solo usa distancias, así que el sentido de `y` no cambia
  ninguna etiqueta y no se invierte.
- Un slot por jugador, con su equipo, barajado a trozos como en el harness.
- **Condiciones:** «tal cual» (vota) y «suavizado 25» (sin voto: la media móvil del harness, sin rellenar
  huecos). El balón no se tapa en los `D`: no se sabe si Metrica lo congela.
- Juegos 1 y 2: el balón es el último par de columnas del CSV del equipo local.
- Juego 3: las posiciones las lee `possession/io.py` (el fichero es `frame:jugadores:balón`, a 25 fps).
  El equipo de cada slot es el que da kloppy en ese mismo orden: 11 locales y luego 11 visitantes, y se
  comprueba que las `x` coinciden en el primer frame. El balón de kloppy no se usa, porque su canal no
  cae en 0–1.

## 5. Versiones

Las mismas que en SkillCorner, con los coeficientes de la entrega (nunca han visto estos partidos):

| versión | qué |
|---|---|
| control | baseline oficial, voto de ±50 |
| N1 | `candidates.evidence`, `dead_state` y Viterbi con coste 25 |
| `main` | B5, `dead_state` y Viterbi con coste 25 |

`D` oráculo decide. `D` propio es descriptivo.

## 6. Regla de lectura (fijada antes de medir)

Con 3 partidos no se puede pedir 6 de 7. Se lee así, solo con «tal cual» y el `D` oráculo:

- **«B5 aguanta con la convención de Metrica»:** `main` gana al control por 0,03 o más con los 3 juntos,
  en 3 de 3, y con el intervalo por encima de cero.
- **«La ventaja sobre N1 aguanta»:** lo mismo, `main` frente a N1, pero basta con 2 de 3: con 3 partidos
  un solo partido en contra no tumba una ventaja que ya ganó en 19 de 20 en SkillCorner.
- **Si `main` no gana al control:** se avisa a Ismael. No cambia la entrega por sí solo: son 3 partidos y
  otra convención.
- **Descriptivo:** el `D` propio, el suavizado, las posesiones por minuto vivo, la huella de retrasos y si
  `possession/io.py` lee el juego 3 (recuento de líneas, sin imprimir valores).
- Después de ver los números no se cambia esta regla.

## 7. Resultado

15/11, con los 3 partidos; detalle y salida en `validation/resultados/2026-11-15_metrica.md`.

- **«B5 aguanta con la convención de Metrica»: sí** [medido]. `main` frente al control, con el `D` oráculo y
  el balón tal cual: +0,118, intervalo +0,095 a +0,141, en 3 de 3.
- **«La ventaja sobre N1 aguanta»: sí** [medido]. `main` frente a N1: +0,058, intervalo +0,037 a +0,080, en
  2 de 3. En la condición que no vota (balón suavizado) es 3 de 3.
- **Descriptivo:** con el `D` propio, `main` saca 0,537 y el control 0,412. El lector del ATD lee el juego
  3 sin saltarse ninguna línea; `from_files` no lo monta porque los metadatos traen 35 jugadores y el
  tracking 22 slots.

## 8. Nota de la revisión (Ismael, 15/11)

Revisado antes de subirlo. Las comprobaciones están en `python validation/metrica/sensibilidad_paradas.py`,
escrito **después** de ver la medida: no cambia la regla de §3 ni decide nada. Su salida está al final de
`validation/resultados/2026-11-15_metrica.md`.

- **Se reproduce** [medido]. `medir.py --bootstrap 1000` sobre `main` en `3b227c4` da la misma salida, línea
  a línea. La caché es lo que da el lector de ahora, en los 3 juegos.
- **[sin verificar] Que §3 y §6 se escribieran antes de medir.** Nada de esta carpeta se subió antes de la
  medida, así que el orden no se puede comprobar con `git log`: descansa en la palabra del revisor externo.
  El «2 de 3» frente a N1 es justo lo que salió. No cambia nada: este resultado confirma, no decide.
- **La parada va adelantada** [medido]. La regla para el juego en el frame de inicio del evento. Un
  `BALL OUT` dura 36 frames de mediana (de 20 a 69): empieza en el golpeo, no cuando el balón sale. Las
  faltas y los fueras de juego duran 0.
- **Hay paradas que la regla no ve** [medido]. 36 de los 247 saques (el 15 %) llegan con la etiqueta todavía
  en juego. Antes de ellos hay un balón perdido, una tarjeta, una mano o un duelo con falta, sin
  `FAULT RECEIVED` ni `BALL OUT`. El tiempo entre el último evento y esos saques suma como mucho el 7,4 % de
  los frames en juego. Es una cota: no se sabe cuándo se paró el balón.
- **La conclusión aguanta con la parada en el frame final del evento** [medido]:

  | | regla de §3 (parada al inicio) | parada en el frame final |
  |---|---|---|
  | `main` frente al control, `D` oráculo | +0,118 [+0,095 a +0,141], 3 de 3 | +0,112 [+0,088 a +0,135], 3 de 3 |
  | `main` frente a N1, `D` oráculo | +0,058 [+0,037 a +0,080], 2 de 3 | +0,067 [+0,044 a +0,089], 3 de 3 |
  | posesiones · por minuto vivo | 879 · 4,70 | 942 · 4,99 |
  | huella de retrasos a 25 frames | 0,724 | 0,690 |
  | frames `D` | 34,8 % | 34,2 % |

- **Qué se puede decir y qué no:**
  - **sí:** B5 gana al baseline y a N1 en estos 3 partidos, con las dos formas de poner la parada;
  - **no:** que estas etiquetas sean «la convención de la organizadora». Son una derivación nuestra de sus
    eventos. Sus posesiones por minuto y su huella se mueven con la regla de paradas (de 4,70 a 4,99 y de
    0,724 a 0,690), y hay paradas sin marcar. No se usan como referencia de convención, ni para decir si
    quedan más cerca o más lejos de la tabla oficial que SkillCorner (0,678).
