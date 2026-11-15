# Validación externa

Aquí está todo lo que sirve para decidir entre métodos **sin mirar etiquetas del partido**: los pasos
que faltan, los scripts y los resultados. El porqué está en
[`docs/investigacion_metodos.md`](../docs/investigacion_metodos.md).

| qué | dónde |
|---|---|
| pasos para completar el experimento 0 y siguientes, con las dudas abiertas (D1…D21) | [`PASOS.md`](PASOS.md) |
| resultados, uno por fichero, con su índice | [`resultados/`](resultados/README.md) |
| scripts | [`scripts/`](scripts/) |
| scripts que leen datos del partido (solo los ejecuta una persona) | [`partido/`](partido/) |

## Scripts

| script | qué hace | datos que lee |
|---|---|---|
| `scripts/perfil_etiquetas.py` | perfil de un CSV `frame,label`: posesiones, paradas y huella de retrasos frente a la tabla oficial | GT pública o etiquetas de datos abiertos |
| `scripts/sensibilidad_metrica.py` | cuánto cuesta cada tipo de error en `spellF1`, con una GT sintética | ninguno del partido |
| `scripts/silbato.py` | biblioteca: detector de silbatos en el audio de un vídeo, alineado a sus frames (B6) | ninguno: lo decide quien la llama |
| `scripts/prueba_silbato.py` | prueba el detector de silbatos con audio sintético | ninguno del partido |
| `partido/silbato_audio.py` | **lee el partido** (vídeo, Smart Tagging y ATD): ¿se oye el silbato?, ¿cuadra con los goles, las faltas y los saques?, ¿frenan los jugadores después? Solo agregados. Lo ejecuta una persona | vídeo táctico, Smart Tagging y ATD |
| `scripts/descargar_datos_abiertos.py` | descarga la Bundesliga, los eventos del Barça como local y el Clásico de 2019, con versiones fijadas, fuera del repo | datos abiertos de otros partidos |
| `harness/puntuar.py` | **harness de la DFL:** ejecuta el pipeline (`possession/`) en los 7 partidos abiertos y lo puntúa con el scorer oficial, con dos convenciones de etiquetas, tres condiciones del balón y el baseline de control; aplica la regla de §5.8. Su `README.md` dice cómo se usa | DFL |
| `harness/dfl.py` | biblioteca del harness: un partido de la DFL en el formato de `possession/tracking.py`, con sus etiquetas y el balón degradado | DFL |
| `harness/versiones/` | ficheros JSON con las versiones que compara cada uno (`puntuar.py --versiones`); `ejemplo.json` es el de muestra | — |
| `scripts/prueba_harness.py` | prueba la lectura de los ficheros de versiones del harness: el ejemplo, las opciones de una función, las funciones de otro módulo y el partido que se deja fuera, y que cada errata da error antes de medir | ninguno |
| `apuesta_b/entrenar.py` | apuesta B: entrena la evidencia de equipo aprendida (`possession/aprendida.py`) en los 7 partidos de la DFL, un pliegue por partido, y escribe sus coeficientes en el módulo | DFL |
| `apuesta_b/escala.py` | apuesta B, descriptivo: cuánto pesa la evidencia de equipo por frame (N1 frente a la aprendida) en juego con balón, sin balón y en los `D` | DFL |
| `apuesta_b/jugadores.py` | apuesta B con los jugadores degradados como el ATD (suavizado y tres variantes de ausencias), calibrado con el perfil del ATD; medida de sensibilidad que no cambia el harness (`--versiones` elige qué se puntúa) | DFL y los agregados ya publicados del perfil del ATD |
| `apuesta_b/d_propio.py` | apuesta B: con la pieza de `D` de `main` dentro y sin oráculo, cuántas paradas reales ve cada versión de un fichero de versiones (`--versiones`), con el balón tapado en los `D` y a la vista; criterios 2 y 3 de B5, descriptivo para lo demás | DFL |
| `apuesta_b/comprobar_camino_nuevo.py` | comprobación del instrumento: N1 por el camino nuevo del harness («aprendida.…» con «dejar_fuera») da lo mismo que `{}` | DFL |
| `scripts/prueba_aprendida.py` | prueba la evidencia aprendida con el partido inventado: interfaz, determinismo, simetría, orden de los slots y los 16 juegos de coeficientes | ninguno |
| `scripts/prueba_pipeline.py` | prueba el esqueleto del pipeline (`possession/`) con un partido inventado: interfaz de las piezas, cambiar una pieza por otra función, tramos evaluados, tramo antes del saque, decodificador contra la búsqueda exhaustiva, determinismo, CSV y lector del ATD | ninguno del partido |
| `scripts/comprobar_balon_muerto.py` | comprueba `possession/dead_ball.py`: interfaz, que no abre ficheros, dónde marca `D`, que no contradice la GT pública, determinismo, que los frames de saque del FAQ y de `games.py` cuadran, que con otro partido da error; con un Smart Tagging inventado (en una carpeta temporal que se borra), las capas de gol a saque y del hueco antes de cada reinicio; y, con un partido inventado en memoria, que la regla de `partido/agregados_dead_ball.py` da lo esperado (importa sus cuentas con la apertura de ficheros prohibida; nunca ejecuta su `main`, que es lo que lee el partido) | GT pública |
| `partido/agregados_dead_ball.py` | **lee el partido** (ATD y Smart Tagging): ¿anclan los goles y lo anclado se comporta como balón muerto?, ¿hay un hueco sin balón antes de cada reinicio? Imprime la regla de `docs/decisiones.md` aplicada. Solo agregados. Lo ejecuta una persona | **datos del partido: solo una persona** |
| `partido/diagnostico_balon_muerto.py` | ¿sirve el balón del ATD para el detector de `D`? Balón fuera del campo, en los reinicios y en los saques iniciales | **datos del partido: solo una persona** |
| `partido/diagnostico_coordenadas.py` | ¿separa x = 0,5 a los dos equipos? Temblor del balón y tramos con el balón quieto | **datos del partido: solo una persona** |
| `skillcorner/descargar.py` | baja los 20 partidos abiertos de SkillCorner (A-League 2024/25, licencia MIT; unos 1,8 GB) a la carpeta de datos abiertos, con el sha256 de cada tracking comprobado | descarga datos abiertos de otros partidos |
| `skillcorner/lector.py` | biblioteca: un partido de SkillCorner en el formato de `possession/tracking.py` (de 10 a 25 fps), con sus etiquetas | SkillCorner, datos abiertos de otros partidos |
| `skillcorner/prueba_lector.py` | prueba el lector de SkillCorner con un partido inventado | ninguno |
| `skillcorner/medir.py` | ¿aguanta B5 con un tracking automático? Puntúa el control, N1 y `main` en los partidos de SkillCorner, con la regla de `skillcorner/BITACORA.md` | SkillCorner, datos abiertos de otros partidos |
| `metrica/lector.py` | biblioteca: los 3 partidos abiertos de Metrica en el formato de `possession/tracking.py`, con las etiquetas derivadas de sus eventos (`metrica/BITACORA.md` §3) | Metrica sample-data, datos abiertos de otros partidos |
| `metrica/prueba_lector.py` | prueba el lector de Metrica con etiquetas y un partido inventados | ninguno |
| `metrica/medir.py` | ¿aguanta B5 con etiquetas derivadas de los eventos de Metrica? Puntúa el control, N1 y `main` en sus 3 partidos, con la regla de `metrica/BITACORA.md` | Metrica sample-data, datos abiertos de otros partidos |
| `metrica/sensibilidad_paradas.py` | comprobaciones de la revisión: cuánto dura cada evento que para el juego, cuántos saques llegan sin parada antes y la misma medida con la parada en el frame final del evento. Descriptivo, escrito después de medir | Metrica sample-data, datos abiertos de otros partidos |
| `scripts/diagnostico_errores.py` | ¿por qué fallamos? Causa de cada posesión que no encontramos, retraso de los cambios y qué borde del `D` cuesta más. Descriptivo. Solo usa la mitad de SkillCorner; la otra queda como examen | la DFL y SkillCorner, datos abiertos de otros partidos |
| `partido/ver_ventana.py` | **lee una entrega nuestra:** dibuja la GT pública y la entrega en una imagen, con el tiempo del vídeo, para ver los 5 minutos junto al vídeo. No imprime etiquetas y escribe fuera del repo | **una entrega nuestra** y la GT pública: solo lo ejecuta una persona |
| `partido/comparar_entregas.py` | **lee dos entregas nuestras:** cuántos frames evaluados cambian de etiqueta entre una y otra, a qué distancia de los bordes de los tramos evaluados y de qué etiqueta a cuál. Para cuando una pieza cambia y la entrega se regenera. No imprime etiquetas ni frames | **dos entregas nuestras:** solo lo ejecuta una persona |
| `scripts/prueba_comparar_entregas.py` | prueba `partido/comparar_entregas.py` con dos entregas inventadas | ninguno |
| `partido/clips_ventana.py` | **lee una entrega nuestra:** escribe, fuera del repo, una página para el navegador con el vídeo táctico y un tramo por cada sitio en que la entrega y la GT pública difieren, con las dos etiquetas en directo debajo del vídeo. Solo imprime cuántos tramos hay y la ruta. Cómo se usa y qué mirar: [`partido/GUIA_VISIONADO.md`](partido/GUIA_VISIONADO.md) | **una entrega nuestra**, la GT pública y el vídeo táctico: solo lo ejecuta una persona |
| `scripts/prueba_clips_ventana.py` | prueba `partido/clips_ventana.py` con una GT y una entrega inventadas: tramos, margen, fundido, recortes, etiquetas «borde», «equipo» y «D», datos de la página, salida solo de recuentos y que no escribe en el repo | GT pública (contra sí misma) |
| `partido/comun.py` | constantes y utilidades de los dos diagnósticos (no se ejecuta solo) | — |
| `partido/agregados_smart_tagging.py` | ventanas `SET PIECES` por tipo (duración, `Team N/A`), cobertura de los frames evaluados por las fases, huecos entre fases, goles → saque posterior | **datos del partido: solo una persona** |
| `partido/agregados_balon_reinicios.py` | ¿las "reanudaciones" del detector de golpeo caen donde acaba la ventana `SET PIECES` y donde suben los jugadores? Balón que desaparece saliendo del campo; columna de velocidad del ATD frente al desplazamiento suavizado | **datos del partido: solo una persona** |
| `partido/agregados_jugadores.py` | velocidad media de los jugadores (en todo el partido, antes y después de cada reinicio, al principio y al final de cada parte) frente a la DFL; jugadores fuera de los límites | **datos del partido: solo una persona** |
| `partido/recuento_ventana.py` | experimento 2: qué convención sigue la GT pública (cuándo cambia la posesión), medida con el tracking en vez de a ojo; se lee con la regla de `experimento2/BITACORA.md` §7 | **datos del partido: solo una persona** (ATD de la ventana y GT pública) |
| `experimento2/calibrar_dfl.py` | calibra ese instrumento en la DFL degradada para parecerse al ATD (`--tabla` da las tablas de la bitácora) | DFL |
| `experimento2/pruebas_sinteticas.py` | prueba el instrumento y el lector de `recuento_ventana.py` con datos inventados | GT pública y datos sintéticos |
| `scripts/revision_balon_muerto/` | pruebas de la revisión del detector de `D` (13/11): coste de cada error de `D`, `io.py` con un ATD sintético, jugadores solos en la DFL; su `README.md` dice cómo repetirlas | GT pública, GT sintética, DFL |
| `perfil_atd/perfil.py` | biblioteca: el perfil del balón y de los jugadores de un `Tracking` (huecos, dónde se pierde, suavizado, proximidad, detecciones falsas, jugadores, `SET PIECES`), el mismo para el ATD y para la DFL. Agregados y regla de lectura en `perfil_atd/BITACORA.md` | ninguno: lo decide quien la llama |
| `perfil_atd/perfil_dfl.py` | el perfil en los 7 partidos de la DFL con la degradación del harness parametrizada: la medida en seco (`--seco`), las condiciones de hoy (`--harness`) o una condición (`--condicion`) | DFL |
| `perfil_atd/leer_atd.py` | la regla de lectura de la bitácora como código: lee la salida del perfil del ATD, mide la DFL y dice qué degradación sale y qué puede decidir el harness; con `--ensayo`, un partido de la DFL hace de ATD | salida pegada del ATD (agregados) y DFL |
| `partido/perfil_atd.py` | **lee el partido** (ATD y Smart Tagging): el perfil del balón del ATD en todos los frames evaluados, con las dos partes juntas y las celdas de menos de 5 casos suprimidas. Lo ejecuta una persona | **datos del partido: solo una persona** |
| `partido/slots_duplicados.py` | **lee el partido** (ATD): % de frames con dos slots del mismo equipo a 0,3, 0,5 y 1 m o menos (también cerca del balón) y con más de 11 slots en un equipo; si el ATD duplica jugadores, B5 los cuenta doble en sus núcleos. Lo ejecuta una persona | **datos del partido: solo una persona** |
| `apuesta_b/eventos_toque.py` | apuesta B, ronda de B5: comprueba el detector de toques de B8 frente al anexo A.4 de la revisión externa (eventos por minuto de juego, ±20 %) | DFL |
| `scripts/prueba_perfil_atd.py` | prueba el perfil con trackings inventados de resultado conocido, la supresión de celdas, que no abre ficheros y que el script del partido no imprime valores al fallar | ninguno del partido |
| `partido/limpieza_balon.py` | **lee el partido** (ATD): qué hace la limpieza del balón (`ball.clean_v1`) paso a paso en los frames evaluados, con las dos partes juntas y las celdas de menos de 5 casos suprimidas; regla de lectura en `docs/decisiones.md` (14/11). Lo ejecuta una persona | **datos del partido: solo una persona** |
| `scripts/prueba_limpieza.py` | prueba la limpieza del balón (`ball.clean_v1`, también la corrección del paso 2), las evidencias N1, N2 y Ret y el recuento de `partido/limpieza_balon.py` con trackings inventados de resultado conocido | ninguno del partido |
| `retraso_balon/retraso.py` | biblioteca: el desfase entre el balón y el jugador que lo lleva en un `Tracking` (rachas de conducción, correlación de velocidades por desfase, bootstrap y lectura), el mismo para el ATD y para la DFL. Regla en `retraso_balon/BITACORA.md` | ninguno: lo decide quien la llama |
| `retraso_balon/calibrar_dfl.py` | versión 1: calibra esa medida en los 7 partidos de la DFL, que tiene que dar 0 con el balón «como el ATD», +12 con una media hacia atrás y ±6 desplazándolo (bitácora §3). **No pasó** (§7) | DFL |
| `retraso_balon/calibrar_dfl_v2.py` | versión 2: compara la curva entera con una familia de curvas de la DFL con retrasos conocidos, dejando un partido fuera, con retrasos de −9 a +12 (bitácora §8.3); da también la familia y el residuo de referencia al script del partido. Con `--anchos 13 37 49`, la sensibilidad al ancho del suavizado centrado (§11) | DFL |
| `partido/retraso_balon.py` | **lee el partido** (ATD) y la DFL: ¿llega el balón con retraso respecto a los jugadores? El desfase de la versión 2 en los frames evaluados, con su intervalo y la lectura de la bitácora §8.5; solo si la calibración v2 pasa. Lo ejecuta una persona | **datos del partido: solo una persona** |
| `scripts/prueba_retraso_balon.py` | prueba la medida del retraso (las dos versiones) con trackings inventados de desfase conocido, sus filtros, la familia, la lectura y que el script del partido solo imprime agregados | ninguno del partido |
| `partido/fases_smart_tagging.py` | **lee el partido** (ATD y Smart Tagging) **y una entrega nuestra** (`--entrega`): ¿sirven las fases del Smart Tagging como pista de equipo? El acuerdo con el control claro frente a las fases desplazadas (la regla del plan), los solapes, las transiciones frente a nuestros cambios y el alcance del empujón; regla en `fases_smart_tagging/BITACORA.md`. Lo ejecuta una persona | **datos del partido y una entrega: solo una persona** |
| `partido/fases_smart_tagging_revision.py` | **lee el partido** (ATD y Smart Tagging) **y una entrega nuestra**: el recuento de revisión de la bitácora §7, con los solapes por código y por pareja (¿vale la tabla?) y cuánto tardamos en los contraataques y con qué etiqueta vamos dentro de ellos, frente al placebo. Lo ejecuta una persona | **datos del partido y una entrega: solo una persona** |
| `scripts/prueba_fases_smart_tagging.py` | prueba los dos recuentos con un partido inventado de resultado conocido: la tabla de códigos, los solapes, el acuerdo y su placebo, la regla, las transiciones, el alcance, la revisión, la lectura de la entrega y que solo imprimen agregados | ninguno del partido |
| `posesiones_cortas/diagnostico.py` | posesiones cortas, descriptivo: convención frente a modelo y margen de B5 dentro de cada posesión real | DFL y SkillCorner (`lector.ENTRENAMIENTO`) |
| `posesiones_cortas/informacion.py` | posesiones cortas, descriptivo: acierto del más cercano por frame, con jugadores tal cual y suavizados | DFL y SkillCorner (`lector.ENTRENAMIENTO`) |
| `posesiones_cortas/informacion_direccion.py` | posesiones cortas, descriptivo: acierto de la dirección en que se mueve el balón | DFL y SkillCorner (`lector.ENTRENAMIENTO`) |
| `posesiones_cortas/puerta_skillcorner.py` | posesiones cortas, puerta: entrenar los rasgos de B5 con todos los frames de SkillCorner | DFL y SkillCorner (`lector.ENTRENAMIENTO`) |
| `posesiones_cortas/techo_propuestas.py` | posesiones cortas, descriptivo: techo de proponer y clasificar trozos del rival | DFL y SkillCorner (`lector.ENTRENAMIENTO`) |
| `posesiones_cortas/puerta_direccion.py` | posesiones cortas, puerta de la dirección del balón (en los mismos partidos) | DFL |
| `posesiones_cortas/entrenar_b9.py` | entrena B9 (`possession/aprendida.py`) y escribe sus coeficientes; B1 a B8 se copian tal cual | DFL |
| `posesiones_cortas/medir_b9.py` | B9: placebo, retraso del balón y SkillCorner; el modo `examen` se niega a ejecutarse (B9 descartado) | DFL y SkillCorner (`lector.ENTRENAMIENTO`) |
| `posesiones_cortas/largas.py` | fase 2, descriptivo: por qué no encontramos las posesiones de 2 s o más | DFL y SkillCorner (`lector.ENTRENAMIENTO`) |
| `posesiones_cortas/fase2.py` | fase 2, descriptivo: las que sobran, cuánto vale cada tipo de fallo y `main` con el balón tarde | DFL y SkillCorner (`lector.ENTRENAMIENTO`) |
| `posesiones_cortas/inventadas.py` | fase 2, descriptivo: dónde están las posesiones inventadas y qué son con la otra convención | DFL |
| `posesiones_cortas/ritmo_d_propio.py` | fase 4: posesiones por minuto de juego predicho con nuestro `D`, para comparar con el partido igual con igual | DFL y SkillCorner (`lector.ENTRENAMIENTO`) |
| `posesiones_cortas/pista_sintetica.py` | fase 4, descriptivo: cuánto valdría una pista de equipo de fuera (como las fases del Smart Tagging), con una pista sintética | DFL |
| `posesiones_cortas/pista_transiciones.py` | fase 4, descriptivo: cuánto valdría una pista que marque dónde cambia la posesión (como las transiciones del Smart Tagging), con una pista sintética | DFL |
| `posesiones_cortas/retraso_cambios.py` | descriptivo: retraso con signo de nuestros cambios de equipo hasta ±4 s | DFL y SkillCorner (`lector.ENTRENAMIENTO`) |
| `posesiones_cortas/huecos.py` | biblioteca: dónde caen nuestros cambios de equipo respecto a los huecos del balón en el juego (H3 y H5 del visionado) | ninguno: lo decide quien la llama |
| `posesiones_cortas/huecos_dfl.py` | la referencia de la DFL de `partido/huecos_y_cambios.py`: `main` con nuestro `D`, huecos al azar | DFL |
| `partido/huecos_y_cambios.py` | **lee el partido** (ATD) y una entrega nuestra: dónde caen nuestros cambios respecto a los huecos del balón, frente a la DFL, con la regla de `posesiones_cortas/BITACORA.md` §14. Lo ejecuta una persona | **datos del partido: solo una persona** |
| `scripts/prueba_huecos.py` | prueba `posesiones_cortas/huecos.py` y la regla de `partido/huecos_y_cambios.py` con datos inventados | ninguno del partido |
| `posesiones_cortas/sandwiches.py` | ¿cuenta la GT los toques sin control? Posesiones cortas entre dos del otro equipo, por convención; con `--gt-publica`, también en la GT pública | DFL, SkillCorner (`lector.ENTRENAMIENTO`) y la GT pública |
| `posesiones_cortas/puerta_no_lineal.py` | fase 3, puerta: una red de una capa con los rasgos de B9 y de los jugadores, fuera de muestra | DFL y SkillCorner (`lector.ENTRENAMIENTO`) |

Se ejecutan desde la raíz del repo, con el entorno de siempre:

```bash
python validation/scripts/perfil_etiquetas.py evaluation/gt/BAR-ATH_possession_gt_public.csv
python validation/scripts/sensibilidad_metrica.py
python validation/scripts/descargar_datos_abiertos.py dfl --solo-ligeros
python validation/scripts/comprobar_balon_muerto.py
python validation/scripts/revision_balon_muerto/coste_errores_D.py
python validation/scripts/prueba_perfil_atd.py
python validation/perfil_atd/perfil_dfl.py --seco
python validation/scripts/prueba_harness.py
```

## Reglas

- **Los scripts de `validation/scripts/` solo leen datos abiertos de otros partidos, la GT pública o
  nada.** Claude puede ejecutarlos. Los que lean datos del partido van en `validation/partido/`: los
  ejecuta solo una persona y pega solo agregados (regla nº 1 de `CLAUDE.md`).
- **`validation/.gitignore` ignora los ficheros de datos** (`*.csv`, `*.json`, `*.xml`...) como red de
  seguridad. El `.gitignore` oficial de la raíz no se toca.
- **Los datos se descargan fuera del repo** (por defecto, `~/mtah2027-datos-abiertos`) y nunca se suben.
  Al repo van los scripts y los resultados agregados.
- **`CLAUDE.md` y `docs/GUIA_EQUIPO.md` están alineados con este plan desde el 11/11** en la validación
  externa y en la política de `X`. Si vuelven a discrepar, manda
  [`docs/investigacion_metodos.md`](../docs/investigacion_metodos.md) hasta que se corrijan.
