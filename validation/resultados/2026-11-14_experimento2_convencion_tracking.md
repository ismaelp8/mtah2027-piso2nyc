# Qué convención sigue la GT pública, medida con el tracking · 2026-11-14 · Claude (sesión de Ismael)

> Experimento 2. Responde a Ismael (14/11). Antonio está con otra cosa y a ojo se escapan cosas: hay que
> usar todos los datos (el tracking de jugadores y balón) y comparar con la ventana pública. Solo
> agregados. Cada afirmación lleva **[medido]**, **[inferencia]** o **[sin verificar]**. El registro paso
> a paso, los criterios fijados antes de medir y la regla de lectura están en
> `validation/experimento2/BITACORA.md`.

**En pocas líneas:**

1. **El recuento a ojo del vídeo se sustituye por un instrumento sobre el tracking.**
   - Usa las medidas de toque y control de los experimentos 0 y 1, con sus umbrales, adaptadas para
     aguantar los huecos del balón.
   - Responde a máquina dos de las tres preguntas del protocolo de Antonio (sección 17 de la bitácora del
     experimento 1): cuándo cambia la etiqueta respecto al primer toque del equipo nuevo, y si los toques
     del rival sin control la cambian.
   - La intención del toque no se ve en el tracking.
2. **Se calibró en los 7 partidos de la DFL** con el mismo código, degradando el tracking para parecerse
   al ATD: 41 % sin balón, con una fracción de las disputas tapadas, y ruido. [medido]
   - **Distingue** "cambia en el toque" de "exige control" (0,89 frente a 0,31 con pérdidas al azar)
     mientras el tracking no pierda casi todas las disputas y el ruido no pase de unos 10 cm.
   - **No distingue si pierde todas las disputas.** Además, la ventana tiene unos 4 minutos de juego: en
     el mejor caso da 5–8 casos, y la respuesta es orientativa.
3. **En la ventana pública queda sin decidir, por la regla fijada antes de ejecutarlo.** [medido] El
   detector de toques casi no ve toques en el ATD: 2,2 por minuto vivo, frente a 20–38 en la DFL.
   - Así no pasa el control de cordura: 0 toques sueltos del rival, y ninguno de los 12 cambios con toque
     visible.
   - No es por falta de balón: en la ventana se ve el 93,5 % del tiempo de juego, y alrededor de los 12
     cambios.
   - Se mantiene la decisión del 12/11: exigir control.
4. **Lo más útil del experimento es por qué falla:** el balón del ATD se comporta como uno suavizado en
   torno a 1 s.
   - [medido] En la DFL, una media móvil de 25 frames reproduce las tres medidas de tracking del ATD:
     temblor de 0,9 cm frente a 1,2, 3,5 toques por minuto frente a 2,2 y 10,4 controles frente a 13,4.
   - [inferencia] Nada que dependa de cambios bruscos de la velocidad del balón, calibrado en la DFL,
     funcionará tal cual en el ATD. La degradación DFL→ATD tiene que suavizar el balón, no solo quitarlo
     y meter ruido.
5. **De paso, la regla del temporizador de Antonio** (sección 8 de la bitácora) apenas cambia las
   etiquetas de la DFL: con 10 frames de margen siguen 6,0 cambios por minuto vivo, frente a 2,78 con la
   corrección por control. [medido]

- **Código:**
  - `validation/experimento2/`: `instrumento.py`, `calibrar_dfl.py` y `pruebas_sinteticas.py`;
  - `validation/partido/recuento_ventana.py`, que solo ejecuta una persona;
  - `validation/experimento1/temporizador.py`.
- **Datos:** los 7 partidos de la Bundesliga (Bassek et al., 2025), sobre la caché del experimento 0. Del
  partido, solo la ventana pública del ATD y la GT pública, y solo en local.
- **Comandos:**
  - `python validation/experimento2/pruebas_sinteticas.py` (todas pasan);
  - `python validation/experimento2/calibrar_dfl.py --tabla` (unos 70 s);
  - `python validation/experimento1/temporizador.py`.

## 1. Calibración en la DFL (variante base)

[medido] Las proporciones son de los 7 partidos juntos y, entre corchetes, el mínimo y el máximo por
partido. `r1` es la proporción de toques sueltos del rival que cambian la etiqueta con el flag (lectura 1)
y `r3`, con la corregida "C0-12 o dos toques" (lectura 3).

| disputas tapadas | ruido | disputas entre los frames con balón | temblor (cm) | sueltos/min vivo | `r1` | `r3` | ¿distingue? |
|---|---|---|---|---|---|---|---|
| limpia | – | 21,0 % | 2,2 | 1,89 | 0,88 [0,72–0,94] | 0,19 [0,14–0,29] | sí |
| 0 % | 0 cm | 21,3 % | 2,2 | 1,37 | 0,89 [0,77–0,94] | 0,31 [0,21–0,43] | sí |
| 0 % | 10 cm | 20,6 % | 29,6 | 1,65 | 0,67 [0,58–0,74] | 0,22 [0,17–0,29] | sí |
| 0 % | 25 cm | 21,0 % | 72,5 | 2,03 | 0,53 [0,46–0,62] | 0,18 [0,15–0,22] | no |
| 50 % | 0 cm | 13,9 % | 2,2 | 0,93 | 0,90 [0,80–0,97] | 0,32 [0,23–0,42] | sí |
| 75 % | 0 cm | 7,7 % | 2,2 | 0,61 | 0,90 [0,79–1,00] | 0,38 [0,29–0,48] | sí |
| 100 % | 0 cm | 0,0 % | 2,2 | 0,22 | 0,95 [0,83–1,00] | 0,70 [0,46–0,83] | no |

La tabla completa (25 y 75 % con ruido, la variante ampliada, la fecha del cambio) está en la sección 6 de
la bitácora.

## 2. Ventana pública

Ismael la ejecutó una vez, en local (`python validation/partido/recuento_ventana.py`). La lectura completa,
con la regla de la sección 7 de la bitácora paso a paso, está en la sección 9 de la bitácora.

| medida de tracking (variante base) | ATD, ventana | DFL limpia | DFL, condición elegida (50 % de disputas tapadas, sin ruido) |
|---|---|---|---|
| balón visible en juego | 93,5 % | 100 % | 59,0 % |
| disputas entre los frames con balón | 14,6 % | 21,0 % | 13,9 % |
| temblor del balón | 1,2 cm | 2,2 cm | 2,2 cm |
| toques con equipo por minuto vivo | **2,2** | 37,9 | 20,1 |
| controles Ret-12 por minuto vivo | 13,4 | 13,4 | 9,4 |

- **Condición:** "50 % de disputas tapadas, sin ruido".
- **Control de cordura:** no pasa (toques 0,11 veces los de la condición): **sin decidir**.
- **Exploración posterior, solo con tracking** (no estaba fijada antes) [medido]: en la DFL, la media móvil
  de 25 frames sobre el balón da 0,9 cm de temblor, 3,5 toques por minuto y 10,4 controles por minuto.

Salida tal cual (solo agregados):

```json
{
 "experimento": "2 · recuento con el tracking en la ventana pública",
 "frames_de_la_ventana": 7500,
 "calidad_del_atd": {"frames_que_faltan": 0, "lineas_con_otro_numero_de_slots": 0, "slots": 46},
 "variantes": {
  "base": {
   "tasas": {
    "balon_visible_en_juego_pct": 93.5, "disputa_entre_frames_con_balon_pct": 14.6,
    "temblor_balon_mediana_cm": 1.2, "toques_con_equipo_por_minuto_vivo": 2.2,
    "controles_ret12_por_minuto_vivo": 13.4, "cortas_intercaladas_por_minuto_vivo": 0.75,
    "huecos_rival_que_cambian": null, "huecos_placebo_que_cambian": 0.0,
    "sueltos_rival_que_cambian": null, "sueltos_placebo_que_cambian": 0.5,
    "sueltos_rival_por_minuto_vivo": 0.0, "cambios_con_toque_visible": 0.0,
    "en_el_toque_de_los_que_tienen_toque": null, "poco_despues_o_mas_tarde_de_los_que_tienen_toque": null
   },
   "recuentos": {
    "frames_vivos": 6031, "frames_vivos_con_balon": 5640, "frames_vivos_con_balon_en_disputa": 823,
    "toques_con_equipo": 9, "controles_ret12": 54, "temblor_balon_mediana_m": 0.012280565500010148,
    "cambios_directos": 12, "cambios_con_balon_visible_la_mitad_de_±1s": 12,
    "fecha_respecto_al_toque": {"antes del toque": 0, "en el toque": 0, "poco después": 0, "más tarde": 0,
                                "sin toque visible": 12},
    "fecha_respecto_al_control": {"antes del control": 2, "en el inicio del control": 1,
                                  "6-15 frames después del inicio": 1, "más de 15 después del inicio": 1,
                                  "sin control": 7},
    "cortas_intercaladas": {"control": 0, "solo toque": 0, "sin balón": 0, "nada": 3},
    "toques_rival_sin_control": {"toques": 0, "toques_que_cambian": 0, "huecos": 0, "huecos_que_cambian": 0},
    "placebo_toques_propios": {"toques": 3, "toques_que_cambian": 0, "huecos": 2, "huecos_que_cambian": 0},
    "toques_sueltos_rival": {"episodios": 0, "cambian": 0},
    "placebo_toques_sueltos_propios": {"episodios": 2, "cambian": 1}
   }
  },
  "ampliada": {
   "tasas": {
    "balon_visible_en_juego_pct": 93.5, "disputa_entre_frames_con_balon_pct": 14.6,
    "temblor_balon_mediana_cm": 1.2, "toques_con_equipo_por_minuto_vivo": 4.5,
    "controles_ret12_por_minuto_vivo": 15.9, "cortas_intercaladas_por_minuto_vivo": 0.75,
    "huecos_rival_que_cambian": null, "huecos_placebo_que_cambian": 0.0,
    "sueltos_rival_que_cambian": 0.33, "sueltos_placebo_que_cambian": 0.33,
    "sueltos_rival_por_minuto_vivo": 0.75, "cambios_con_toque_visible": 0.08,
    "en_el_toque_de_los_que_tienen_toque": 1.0, "poco_despues_o_mas_tarde_de_los_que_tienen_toque": 0.0
   },
   "recuentos": {
    "frames_vivos": 6031, "frames_vivos_con_balon": 5640, "frames_vivos_con_balon_en_disputa": 823,
    "toques_con_equipo": 18, "controles_ret12": 64, "temblor_balon_mediana_m": 0.012280565500010148,
    "cambios_directos": 12, "cambios_con_balon_visible_la_mitad_de_±1s": 12,
    "fecha_respecto_al_toque": {"antes del toque": 0, "en el toque": 1, "poco después": 0, "más tarde": 0,
                                "sin toque visible": 11},
    "fecha_respecto_al_control": {"antes del control": 3, "en el inicio del control": 1,
                                  "6-15 frames después del inicio": 0, "más de 15 después del inicio": 1,
                                  "sin control": 7},
    "cortas_intercaladas": {"control": 0, "solo toque": 0, "sin balón": 0, "nada": 3},
    "toques_rival_sin_control": {"toques": 0, "toques_que_cambian": 0, "huecos": 0, "huecos_que_cambian": 0},
    "placebo_toques_propios": {"toques": 4, "toques_que_cambian": 0, "huecos": 4, "huecos_que_cambian": 0},
    "toques_sueltos_rival": {"episodios": 3, "cambian": 1},
    "placebo_toques_sueltos_propios": {"episodios": 3, "cambian": 1}
   }
  }
 }
}
```

## 3. Sin verificar

- Que el ATD esté suavizado de verdad, y no interpolado entre detecciones. Tampoco se sabe si es igual
  en el resto del partido, donde falta mucho más balón (41 % de los frames evaluados según `DATA.md`,
  frente al 6,5 % de la ventana).
- Que el ruido gaussiano independiente frame a frame se parezca al error real del ATD. Por lo visto en la
  ventana, el error del ATD se parece más a un suavizado que a un ruido.
