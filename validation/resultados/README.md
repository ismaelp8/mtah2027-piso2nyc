# Resultados

Cada resultado de la validación va en un fichero, para que lo vea todo el equipo y para el documento
técnico.

## Cómo se apunta un resultado

- **Nombre:** `AAAA-MM-DD_tema.md`, por ejemplo `2026-11-12_experimento0.md`.
- **Cabecera:** fecha y quién; datos usados, con su versión; comando exacto; para qué; lectura en tres
  líneas. Si responde a alguna duda de `PASOS.md`, su número (D1…D21).
- **Debajo, la salida tal cual,** en un bloque de código.
- **Para el experimento 0** hay una plantilla: copia `_plantilla_experimento0.md`.
- **Si de un resultado sale una decisión,** se apunta también en `docs/decisiones.md` (`/decision`).
- **Se añade una línea al índice** de abajo.

## Qué se puede apuntar

- **Solo agregados:** recuentos, porcentajes, cuantiles, métricas, tiempos.
- **Del partido del reto:** nunca valores por frame ni números de frame concretos. Los agregados (por
  ejemplo, el perfil del ATD) sí.
- **De datos abiertos:** agregados por partido. Nunca copias de los datos: las licencias no lo permiten.
- **Nada ajustado contra la ventana pública.**
- **Una diferencia por debajo del ruido es un empate.** La regla está en la sección 5.8 de
  `docs/investigacion_metodos.md`.

## Índice

| fecha | quién | qué | fichero | en una línea |
|---|---|---|---|---|
| 2026-11-11 | Claude (sesión de Ismael) | coste de cada tipo de error en `spellF1`, con GT sintética | [sensibilidad_metrica](2026-11-11_sensibilidad_metrica.md) | inventar cambios de posesión y no ver las posesiones cortas son los errores más caros |
| 2026-11-11 | Claude (sesión de Ismael) | perfil de la GT pública | [perfil_ventana_publica](2026-11-11_perfil_ventana_publica.md) | hay posesiones de 19 y 33 frames; la ventana tiene menos posesiones cortas y menos `D` que el partido completo |
| 2026-11-11 | Claude (sesión de Ismael) | baselines oficiales en la ventana pública | [baselines_ventana_publica](2026-11-11_baselines_ventana_publica.md) | el baseline cambia de equipo en momentos equivocados y confunde "sin balón" con balón muerto |
| 2026-11-11 | Claude (sesión de Ismael) | datos abiertos del Barça como local | [inventario_datos_barca_local](2026-11-11_inventario_datos_barca_local.md) | no hay tracking con flags del Barça; sí eventos de 264 partidos en el Camp Nou y un Clásico con tracking de broadcast |
| 2026-11-11 | Claude (sesión de Ismael) | experimento 0: flags de la Bundesliga frente a `CHALLENGE.md` | [experimento0](2026-11-11_experimento0.md) | `D` sí sirve tal cual; el cambio de posesión no: la DFL da la posesión al rival en su primer toque aunque no controle; el balón está congelado durante los `D` |
| 2026-11-12 | Claude (sesión de Ismael) | experimento 1: cuándo cambia la posesión y con qué control corregir la DFL | [criterio_posesion](2026-11-12_criterio_posesion.md) | hay tres lecturas (toque, toque con impacto, control); con los eventos humanos de la DFL se puede elegir el control sin circularidad; falta mirar el vídeo de la ventana pública |
| 2026-11-12 | Manuel (ejecución local), con Claude | ¿sirve el balón del ATD para el detector de `D`? | [balon_muerto_atd](2026-11-12_balon_muerto_atd.md) | con la regla probada, no: solo el 4,2 % de los frames con balón lo tiene fuera del campo, quieto 3 s o más se ve 17 veces y en ningún saque inicial se encuentra el golpeo; x = 0,5 separa a los equipos; el detector se queda en el tramo antes del saque (2.934 frames) |
| 2026-11-13 | Claude (sesión de Ana) | revisión del detector de `D` v1 y qué vale el `D` en la métrica | [revision_balon_muerto](2026-11-13_revision_balon_muerto.md) | el `D` suma por la precisión de sus fronteras (≤ 1 s), no por la cobertura: todas las paradas 2 s tarde valen lo mismo que ninguna; los jugadores solos dan el estado (AUC 0,93–0,97) pero no el momento; dos descartes prematuros; propuesta v2 por capas y criterio de aceptación medible en la DFL |
| 2026-11-14 | Claude (sesión de Ismael); Ismael ejecutó la ventana en local | experimento 2: la convención de la GT pública medida con el tracking, en vez de a ojo | [experimento2_convencion_tracking](2026-11-14_experimento2_convencion_tracking.md) | en la DFL el instrumento distingue "cambia en el toque" de "exige control"; en la ventana queda sin decidir porque el balón del ATD se comporta como uno suavizado ~1 s y el detector de toques casi no ve toques (2,2/min frente a 20–38); la degradación DFL→ATD tiene que suavizar el balón |
| 2026-11-14 | Claude (sesión de Ismael) | harness de la DFL: primera medida del esqueleto del pipeline | [harness_dfl](2026-11-14_harness_dfl.md) | con el `D` oráculo, quién gana depende de la convención: con las etiquetas de control el Viterbi con coste 25 gana al voto del baseline por más de 0,10 en los 7 partidos; con el flag, empata o pierde por poco; con la regla de §5.8 no gana ninguna versión |
| 2026-11-14 | Ismael (ejecución local), con Claude | perfil del balón del ATD en todo el partido, leído con la regla fijada antes | [perfil_atd](2026-11-14_perfil_atd.md) | ningún `DISPUTAS` queda: el ATD casi no tiene huecos cortos y pierde el balón en bloques de 5 s o más, como la DFL con solo los `D` tapados; la mayor parte de su 41 % sin balón sería balón muerto (inferencia), así que la condición `huecos` del harness es demasiado dura; el suavizado de 25 frames cuadra (descriptivo) |
