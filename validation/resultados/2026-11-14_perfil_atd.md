# Perfil del balón del ATD en todo el partido, frente a la DFL degradada · 2026-11-14 · Ismael (ejecución local), con Claude

> Paso 1 de «Ismael» en `docs/PLAN_ENTREGA.md` §3. Solo agregados. Cada afirmación lleva **[medido]**,
> **[inferencia]** o **[sin verificar]**. Los agregados, la regla de lectura y sus cambios antes de medir
> están en `validation/perfil_atd/BITACORA.md` (secciones 4 a 8). Se fijaron y se subieron a `main` antes
> de ejecutar nada en el partido (commit `84b8d7c`), con el sí de Ismael a todo lo que cambió (§8).

**En pocas líneas:**

1. **La regla no deja ningún valor de `DISPUTAS`** [medido]. Lo que puede decidir el harness sigue en
   «todavía no» (R7). Según la regla, el paso 3 cambia la forma de tapar el balón y se vuelve a leer con
   la misma regla.
2. **El ATD casi no tiene huecos cortos** [medido]:
   - 15 huecos de hasta 0,5 s y menos de 5 en cada intervalo hasta 5 s;
   - frente a 76 huecos de 5 a 15 s y 55 de más de 15 s.

   La degradación de hoy del harness hace justo lo contrario: bloques de 1 s de media.
3. **El balón del ATD se parece al de la DFL con el balón tapado solo en los `D`** (la condición
   `limpio`), no al de la condición `huecos` [medido]:
   - visibilidad: 59,3 % frente al 54,5 % y al 32,2 %;
   - huecos de 5 s o más: 111 por 90 minutos frente a 88 y 119;
   - reparto de los huecos de hasta 15 s: casi igual al de `limpio`;
   - pérdidas que abren un hueco largo: 1,3 a 2,0 por 1.000 frames, frente a 1,2 a 1,4 en `limpio`.

   **[inferencia]** La mayor parte del 41 % de balón que falta sería balón muerto, no juego. La condición
   `huecos` del harness, que quita el 41 % del balón **en juego**, sería mucho más dura que el ATD.
4. **Descriptivo, no veredicto de la regla:** los toques y controles por minuto del ATD cuadran con un
   suavizado de 25 frames (3,3 y 12,2 por minuto, frente a 3,8 y 11,0) [medido]. Es lo que el
   experimento 2 solo infería. La proximidad está cerca, con la DFL algo más cerca del balón [medido].
   Las dos se midieron con un `DISPUTAS` que no pasa R1', así que la regla no las da por buenas.

- **Código:**
  - `validation/perfil_atd/perfil.py` (la medida);
  - `validation/partido/perfil_atd.py` (el ATD);
  - `validation/perfil_atd/perfil_dfl.py` (la DFL);
  - `validation/perfil_atd/leer_atd.py` (la regla).

  La lectura se hizo con `validation/perfil_atd/` tal como está en `84b8d7c`. Desde entonces
  `validation/harness/dfl.py` solo ha cambiado en que `cargar` devuelve también `meta`, que la regla no
  usa.
- **Datos:**
  - el ATD táctico del partido y su Smart Tagging (paquete de la organización), solo en local;
  - los 7 partidos de la Bundesliga (Bassek et al., 2025, CC BY 4.0).
- **Comandos:**
  - `python validation/partido/perfil_atd.py`: Ismael, una vez, el 14/11; 7 s;
  - `python validation/perfil_atd/leer_atd.py <salida>`: Claude;
  - `python validation/perfil_atd/perfil_dfl.py --harness --json`: Claude, para la sección 2.

## 1. La regla, paso a paso

**R0, control: cuadra** [medido]: 158.857 frames evaluados, 94.214 con balón, 59 tramos de balón parado
con 7.336 frames.

**R1', R2 y R3' (deciden las severidades baja y media):**

| `DISPUTAS` | R1' baja | R2 baja | R1' media | R2 media | R3' | ¿queda? |
|---|---|---|---|---|---|---|
| 0 | sí (`OBJETIVO` 0,001) | sí | sí (0) | no | sí | no |
| 0,25 | sí (0) | no | no | no | sí | no |
| 0,5 | no | no | no | no | sí | no |
| 0,75 | no | no | no | no | sí | no |
| 1 | no | no | no | no | no | no |

- **La `s` de las severidades baja y media del ATD es del 0,08 %** [medido]. Es la fracción de frames sin
  balón en huecos de hasta 2 s (o 5 s), contando los frames con balón más esos. Se cuenta del primer al
  último frame con balón de cada parte, sin los frames de balón parado.
- **Por qué falla R1':** con cualquier `DISPUTAS` mayor que 0, la parte dirigida ya tapa más que eso,
  aunque `OBJETIVO` valga 0. Su suelo es 2,9 % (0,25) y 6,4 % (0,5) en la baja, y 6,8 % y 14,0 % en la
  media.
- **Por qué falla R2 con `DISPUTAS` 0:**
  - en la media, los pocos huecos cortos del ATD son casi todos de hasta 0,5 s (15 de 16), y los de la
    DFL, de 2 a 5 s;
  - en la alta (que se apunta y no decide), el ATD tiene el 82,6 % de sus huecos de hasta 15 s entre 5 y
    15 s, y la DFL con huecos al azar solo el 12,3 %.
- **Distancia al ATD** (§7.8; menos es más parecido): 13,57 (0), 12,48 (0,25), 13,14 (0,5), 17,52 (0,75)
  y 23,64 (1).
- **R4' (suavizado):** 25 frames, con 3,8 toques y 11,0 controles por minuto, frente a 3,3 y 12,2 del
  ATD. Se calculó con `DISPUTAS` 0,25, que no queda: es **descriptivo**.

  | suavizado (frames) | toques/min | controles/min |
  |---|---|---|
  | 1 | 37,7 | 14,1 |
  | 5 | 33,3 | 13,9 |
  | 11 | 19,4 | 13,4 |
  | **25** | **3,8** | **11,0** |
  | 51 | 0,4 | 6,7 |

- **R5 (proximidad, con el suavizado de 25):** cuadra en las cuatro medidas. La DFL está algo más cerca
  del balón: el más cercano a 1 m o menos en el 30,1 % de los frames, frente al 28,2 % del ATD.
  También **descriptivo**.
- **R7:**
  - el orden entre evidencias de equipo por proximidad: **todavía no**;
  - lo que use la velocidad del balón: **todavía no**;
  - el paso 3 cambia la forma de tapar y se vuelve a leer con esta misma regla.

La lectura completa, con el reparto celda a celda, está en la salida de `leer_atd.py`. Se puede repetir
con el JSON del final.

## 2. Lo que dice el perfil, frente a las condiciones de hoy del harness

Medido con `perfil_dfl.py --harness`: los 7 partidos de la DFL juntos, 668 minutos, frente a los 106 del
ATD. El ATD no tiene etiquetas: todas las medidas son sobre todo el tramo, con el balón en juego o no.

| medida | ATD | DFL `limpio` (solo los `D` tapados) | DFL `huecos` |
|---|---|---|---|
| balón visible (% de los frames) | 59,3 | 54,5 | 32,2 |
| huecos de 5 s o más, por 90 minutos | 111 | 88 | 119 |
| huecos de hasta 2 s | 15 y < 5 | 0 | 3.527 |
| `s` alta (huecos de hasta 15 s, %) | 15,7 | 9,0 [7,2–11,1] | 41,5 |
| reparto de los huecos de hasta 15 s: ≤ 0,5 s / 0,5–2 / 2–5 / 5–15 s (%) | 16,3 / < 5 / < 5 / 82,6 | 0 / 0 / 16,5 / 83,5 | 27,3 / 45,1 / 19,0 / 8,5 |
| pérdidas que abren un hueco de más de 5 s, por 1.000 frames con balón: fuera / en disputa | 1,29 / 1,99 | 1,15 / 1,38 | — |
| salto tras un hueco de más de 5 s: < 3 / 3–15 / ≥ 15 m (% de los huecos) | 16 / 46 / 38 | 13 / 67 / 20 | — |
| balón en disputa (% de los frames con balón, sin parado) | 14,5 | 21,3 | 14,1 |
| toques por minuto (umbral 3 m/s) | 3,3 | 38,6 | 3,6 con el suavizado |

Todo [medido]. Lectura:

- **El ATD pierde el balón en bloques largos, como la DFL cuando el balón está muerto** [medido]. En la
  DFL `limpio` el balón solo falta en los `D` y sus bordes, y sale el mismo reparto de huecos, una
  visibilidad parecida y una tasa de pérdidas parecida.
- **[inferencia]** La mayor parte del 41 % de balón que le falta al ATD sería balón muerto. Apoyos:
  - 131 huecos largos en 106 minutos son más o menos las paradas de un partido;
  - en los 10 s antes de cada `SET PIECE`, el ATD ve el balón en el 27,6 % de los frames, frente al
    59,2 % del resto [medido];
  - el diagnóstico del 12/11 vio el balón fuera del campo en solo el 4,2 % de los frames con balón;
  - en la ventana pública se ve el 93,5 % del juego (experimento 2) [medido].

  En contra o sin cerrar:
  - el ATD ve el balón en el 68 % de los frames de las ventanas `SET PIECES` [medido];
  - tiene menos disputas que la DFL `limpio` (14,5 % frente a 21,3 %) [medido], que es lo que haría
    perder el balón en las disputas, o ver menos jugadores (10,2 por equipo frente a 11);
  - más saltos largos tras los huecos (38 % frente a 20 %) [medido];
  - y la ventana pública no representa al partido (2026-11-11_perfil_ventana_publica).

  **No se puede comprobar sin etiquetas** [sin verificar].
- **Si es así, la condición `huecos` del harness es mucho más dura que el ATD:** quita el 41 % del balón
  en juego. Los números con `huecos` de `2026-11-14_harness_dfl.md` serían pesimistas. Lo más parecido
  al ATD sería `limpio` con el balón suavizado [inferencia].
- **También pone en duda una frase del README del harness y del plan (§4):** «no hay balón» casi
  equivale a «`D`» en la DFL tapada, «cosa que en el ATD no pasa». Según este perfil, en el ATD podría
  pasar bastante [inferencia]. El descarte del 13/11, que dice no usar la falta de balón como `D`, se
  basó en el retraso y el parpadeo que mete hacerlo a pelo. Este perfil no lo cambia, pero afecta a las
  piezas de `D` de Manuel y Ana.

## 3. Qué cambia en el harness

**Nada todavía.** El paso 3 (cambiar la forma de tapar y volver a leer) espera a que Ismael decida. Los
dos candidatos fijados antes de medir (§7.4) son:

- la ley de huecos del ATD;
- los argumentos `dilatar` y `aire` de la parte dirigida.

Ninguno corrige que se tape el juego. Según la sección 2, lo que falta es tapar **menos** balón en juego.
Eso no estaba previsto y se apuntará en la bitácora como cambio posterior a medir.

## 4. Lo que esta medida no dice

- **Dónde caen los huecos del ATD:** si en juego o en balón muerto. Sin etiquetas del partido no se puede
  medir, y la ventana pública no sirve para elegir. Un agregado del partido podría ayudar sin etiquetas:
  cuántos frames sin balón caen dentro de las fases tácticas del Smart Tagging con `Team` H o A, frente a
  las ventanas `SET PIECES`.
- **Si la degradación cambia el orden entre versiones.** Se sabrá al volver a medir el harness con la
  forma nueva.
- **El ruido de la medida del ATD:** es un solo partido de 106 minutos. Las celdas pequeñas están
  suprimidas («< 5») y la regla las trata como cotas.

## Salida del ATD, tal cual

```json
{
 "perfil": "ATD del partido, frames evaluados, las dos partes juntas",
 "segundos": 7,
 "0_control": {"frames_evaluados": 158857, "frames_con_balon": 94214, "balon_visible_pct": 59.307,
  "balon_parado": {"tramos_n": 59, "frames": 7336, "frames_pct": 4.618, "frames_con_balon_fuera_de_ellos": 86878}},
 "1_huecos_y_rachas": {
  "intervalos": ["≤ 0,5 s", "0,5–2 s", "2–5 s", "5–15 s", "> 15 s"],
  "todo": {"huecos_n": [15, "< 5", "< 5", 76, 55], "huecos_frames": [51, "< 5", "< 5", 16066, null],
   "frames_sin_balon_en_huecos_de_mas_de_15_s_o_en_los_bordes": 48504,
   "rachas_n": ["< 5", 14, 20, 43, 72], "rachas_frames": ["< 5", 473, 1995, 9898, 81848]},
  "sin_parado": {"huecos_n": [15, "< 5", "< 5", 76, 55], "huecos_frames": [51, "< 5", "< 5", 16066, null]},
  "s_pct": {"todo": {"baja (huecos de hasta 2 s)": 0.077, "media (huecos de hasta 5 s)": 0.077, "alta (huecos de hasta 15 s)": 14.625},
   "sin_parado": {"baja (huecos de hasta 2 s)": 0.084, "media (huecos de hasta 5 s)": 0.084, "alta (huecos de hasta 15 s)": 15.666}},
  "reparto_de_los_huecos_pct": {"sin_parado": {
   "baja (huecos de hasta 2 s)": {"≤ 0,5 s": 93.75, "0,5–2 s": "< 5"},
   "media (huecos de hasta 5 s)": {"≤ 0,5 s": 93.75, "0,5–2 s": "< 5", "2–5 s": "< 5"},
   "alta (huecos de hasta 15 s)": {"≤ 0,5 s": 16.304, "0,5–2 s": "< 5", "2–5 s": "< 5", "5–15 s": 82.609}}}},
 "2_salto_tras_hueco": {"distancias": ["< 3 m", "3–15 m", "≥ 15 m"],
  "huecos_n": {"huecos de hasta 5 s": ["< 5", 12, "< 5"], "huecos de más de 5 s": [21, 60, 50]}},
 "3a_disputas": {"todo": {"frames_con_balon": 94214, "disputa_pct": 13.866},
  "sin_parado": {"frames_con_balon": 86878, "disputa_pct": 14.523}},
 "3b_perdidas_por_1000_frames_con_balon": {
  "huecos de hasta 5 s": {"fuera de disputa": {"frames_con_balon": 81150, "perdidas_n": 8, "por_1000_frames": 0.099},
   "en disputa": {"frames_con_balon": 13064, "perdidas_n": 8, "por_1000_frames": 0.612}},
  "huecos de más de 5 s": {"fuera de disputa": {"frames_con_balon": 81150, "perdidas_n": 105, "por_1000_frames": 1.294},
   "en disputa": {"frames_con_balon": 13064, "perdidas_n": 26, "por_1000_frames": 1.99}},
  "placebo: dos mitades al azar, huecos de hasta 5 s": {
   "mitad A": {"frames_con_balon": 47062, "perdidas_n": 7, "por_1000_frames": 0.149},
   "mitad B": {"frames_con_balon": 47152, "perdidas_n": 9, "por_1000_frames": 0.191}}},
 "4_suavizado": {
  "todo": {"minutos_con_balon": 62.809, "temblor_cm": 0.915,
   "toques_por_min": {"umbral 3 m/s": 3.025, "umbral 2 m/s": 8.311, "umbral 1 m/s": 13.724},
   "controles_ret12_por_min": 11.893, "autocorrelacion_velocidad": {"5 frames": 0.961, "12 frames": 0.797, "25 frames": 0.406},
   "ternas": {"segunda_diferencia_menor_de_1_mm_pct": 3.943, "segunda_diferencia_menor_de_5_mm_pct": 32.301}},
  "sin_parado": {"minutos_con_balon": 57.919, "temblor_cm": 1.003,
   "toques_por_min": {"umbral 3 m/s": 3.263, "umbral 2 m/s": 8.84, "umbral 1 m/s": 14.434},
   "controles_ret12_por_min": 12.224, "autocorrelacion_velocidad": {"5 frames": 0.962, "12 frames": 0.8, "25 frames": 0.411},
   "ternas": {"segunda_diferencia_menor_de_1_mm_pct": 2.661, "segunda_diferencia_menor_de_5_mm_pct": 28.352}}},
 "5_proximidad": {
  "todo": {"mas_cercano_a_1_m_o_menos_pct": 28.494, "mas_cercano_a_1.5_m_o_menos_pct": 41.828,
   "mas_cercano_a_3_m_o_menos_pct": 65.335, "mas_cercano_a_mas_de_5_m_pct": 18.566,
   "rival_1_m_mas_lejos_pct": 82.819, "cambios_de_equipo_mas_cercano_por_min": 28.658},
  "sin_parado": {"mas_cercano_a_1_m_o_menos_pct": 28.214, "mas_cercano_a_1.5_m_o_menos_pct": 41.792,
   "mas_cercano_a_3_m_o_menos_pct": 65.676, "mas_cercano_a_mas_de_5_m_pct": 18.025,
   "rival_1_m_mas_lejos_pct": 81.872, "cambios_de_equipo_mas_cercano_por_min": 30.819}},
 "6_detecciones": {"pares_de_frames_con_balon": 94065, "saltos_de_mas_de_40_m_s_n": 216, "saltos_de_mas_de_40_m_s_pct": 0.23,
  "rachas_con_balon": 149, "rachas_de_1_o_2_frames_n": "< 5", "rachas_de_1_o_2_frames_pct": "< 5",
  "pares_con_la_misma_posicion_n": 77, "pares_con_la_misma_posicion_pct": 0.082,
  "rachas_con_la_misma_posicion_n": {"< 1 s": 49, "1–5 s": "< 5", "5–30 s": "< 5", "30 s o más": "< 5"}},
 "7_jugadores": {"slots_por_equipo": {"local": 24.0, "visitante": 22.0},
  "localizados_por_frame": {"local": {"media": 10.201, "p10": 9.0, "p50": 11.0, "p90": 11.0},
   "visitante": {"media": 10.286, "p10": 9.0, "p50": 11.0, "p90": 11.0}},
  "tramos_de_un_slot_s": {"p10": 2.6, "p50": 35.52, "p90": 284.632}, "tramos_por_minuto": 11.51,
  "temblor_cm": 0.136, "saltos_de_mas_de_12_m_s_por_minuto": 0.689},
 "8_set_pieces": {"ventanas": 59, "dentro de las ventanas": {"frames": 43899, "con_balon_pct": 68.065},
  "10 s antes": {"frames": 11742, "con_balon_pct": 27.602}, "resto de los evaluados": {"frames": 103216, "con_balon_pct": 59.189}}
}
```

El JSON es el que pegó Ismael, con los mismos valores y otro sangrado.
