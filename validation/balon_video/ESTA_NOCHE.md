# Esta noche (16/11): el ensayo de la entrega y el balón del vídeo

Es la guía para ejecutar todo en orden en un Windows con los datos del partido. Cada paso dice qué ejecutar en
PowerShell (tal cual), qué mirar y qué pegarle a Claude.
- Claude no ve nada del partido: solo lo que le pegues (regla nº 1 de `CLAUDE.md`).
- Las reglas de cada puerta están en [`BITACORA.md`](BITACORA.md). Esta guía no cambia ninguna.

**Quién la sigue (16/11, 18:40).**
- **Antonio, esta tarde,** hace los pasos 0 a 9 en su máquina y, mañana, el 10.
  - Las rutas de abajo son las de Ismael. Cambia `C:\Users\34656` por tu carpeta de usuario y `C:\dev\mtah2027-piso2nyc`
    por tu copia del repo.
  - En Linux o macOS, mira la nota del paso 11.
- **Ismael, esta noche,** hace el paso 1 (el ensayo de la entrega) y el paso 11 como segunda máquina. Si Antonio no
  llegara, Ismael sigue la guía entera y Antonio hace el 11.

**Estado de la rama (16/11, 18:40).** Ya está todo subido a `exp/balon-video`: el código, las pruebas, esta guía y los
dos JSON de la condición 5. El paso 3 lo comprueba.

**Sobre los JSON de la condición 5:**
- El `script_sha256` del JSON de la emulación (`358043bf30d2…`) es el del `emular_dfl.py` commiteado.
- Su campo `codigo` dice «0ba8b24 (con cambios sin commit en el código que se usa)». Se debe a un fichero nuevo que
  estaba sin commitear cuando se generó (`possession/balon_video.py`), y que ni la emulación ni el harness importan, así
  que no cambia ninguna cifra [comprobado por la revisión: entre `48f29cf` y `0ba8b24` no cambió nada de lo que usa].
- No se regenera, para que nadie lea una versión a medias.

## Antes de empezar

- **Abre PowerShell** y déjala abierta. No hace falta activar nada: cada comando lleva la ruta completa del Python
  que usa. Un *entorno* es una carpeta con su propio Python y sus paquetes, y hay dos:
  - el limpio de la entrega, `C:\Users\34656\.venvs\mtah2027-entrega`, con solo numpy y pandas;
  - el del detector, `C:\Users\34656\.venvs\mtah2027-balon`, que se crea en el paso 4. Así lo del detector no toca
    lo de la entrega.
- **Ejecuta los comandos tal cual,** uno por línea.
  - No añadas `|`, `>` ni `Tee-Object`: en Windows, la salida de Python por una tubería pierde las tildes o da error.
  - Para pegar, espera a que el comando acabe, selecciona el texto en la ventana y cópialo con Ctrl+C. Ojo: Ctrl+C
    sin nada seleccionado corta el programa que esté corriendo.
- **Si algo no sale como dice «Qué mirar», para ahí** y pégalo. No sigas con el paso siguiente.
- **Si un script falla,** pega su línea de error.
  - Los scripts de `validation\partido\` imprimen solo el tipo de error y las líneas del código, sin datos.
  - Si falla `possession.pipeline` (pasos 1, 10 y 11 a; en el 10, a través de `probar_entrega.py`), sale un
    traceback de Python. Pega la última línea solo si es un `ErrorCache` (el de la caché del balón del vídeo) o el
    error del ATD («el ATD no es como el del 15/11…»). Si es otra, pega solo los nombres de fichero y los números de
    línea, sin el mensaje.
- **Todo va en CPU,** aunque tengas GPU: así sale igual en todas las máquinas.
- **Antes de pegar nada,** repasa «Qué no pegar nunca», al final.

## Paso 0. Ponerse al día (1 minuto)

```powershell
cd C:\dev\mtah2027-piso2nyc
git fetch origin
git status
Test-Path $env:MTAH_DATA_DIR
```

**Qué mirar:**
- `git status` no lista ningún fichero modificado. Los que no están en git («untracked») no molestan.
- `Test-Path` dice `True`: `MTAH_DATA_DIR` apunta a una carpeta que existe.

**Qué pegar:** nada, si sale así. Si no, la salida de `git status` (solo lleva nombres de ficheros).

## Paso 1. El ensayo de la entrega en `main` (unos minutos)

Regenera la entrega vigente con el entorno limpio. Tiene que salir igual, byte a byte, que `equipo_v8`.

```powershell
git checkout main
git pull
C:\Users\34656\.venvs\mtah2027-entrega\Scripts\python.exe -m possession.pipeline --name ensayo_16nov
C:\Users\34656\.venvs\mtah2027-entrega\Scripts\python.exe evaluation\validate_submission.py evaluation\results\ensayo_16nov.csv
```

**Qué mirar:**
- La línea de versiones: `python 3.13.9, numpy 2.5.4`.
- `código: commit …, sin cambios locales en el código de la entrega`. A las 20:45, `main` estaba en `c52a746`.
  - El commit que imprime es nuevo: la PR 20 (`10aadef`) añade a `possession/temporal.py` una opción apagada
    («cortas a `D`»). `pipeline.PIECES` y `DELIVERY_LAYERS` no cambian, así que el sha256 tiene que ser el de siempre.
  - Si dice `CON CAMBIOS SIN COMMITEAR`, para.
- **Si eres la segunda máquina de la detección** (paso 11), no hace falta la puerta 1b en tu máquina: decide la de
  Antonio. Haz los pasos 3 a 7 y después el 9, solo si su 1b dijo `SIGUE`.
- `frames con piezas en conflicto: 0`.
- **`sha256: d78c514dcf5e8ad9bcff5f76da0aadf409c01ce89ad65ad0435421daf31ce2b2`.** El sha256 es la huella del
  fichero: si cambia un solo byte, sale otra. Esta es la de `equipo_v8`.
- El validador empieza por `OK` y acaba con `Valid.`.

**Si el sha256 no es ese, para aquí y avisa.** Que la entrega se reproduzca va antes que todo lo demás.

**Qué pegar:** la salida entera de los dos comandos de Python.

## Paso 2. La puerta 1a: cuánto mide el balón en el vídeo (un par de minutos)

Sigues en `main`, con el entorno limpio. El script lee el ATD y la homografía e imprime solo percentiles.

```powershell
C:\Users\34656\.venvs\mtah2027-entrega\Scripts\python.exe validation\partido\tamano_balon_video.py
```

**Qué mirar:** el `"diametro_balon_px"` de arriba del todo (no los de dentro de `"por_zona"`), y en él, `"p50"`.
- **Si `p50` es menor que 3,** la línea del balón del vídeo se para (bitácora, puerta 0). Pega la salida y no
  hagas los pasos 3 a 10. La parte a) del paso 11, reproducir `equipo_v8`, sigue en pie.
- Si es 3 o más, sigue.

**Qué pegar:** el JSON entero (el bloque entre `{` y `}`).

## Paso 3. Cambiar a la rama del balón del vídeo (1 minuto)

```powershell
git checkout exp/balon-video
git pull
git branch --show-current
Test-Path validation\partido\balon_video_detectar.py
Test-Path possession\balon_video.py
Test-Path validation\scripts\prueba_balon_video_detectar.py
Test-Path validation\scripts\prueba_balon_video_capa.py
Test-Path validation\balon_video\salidas\2026-11-16_emulacion_dfl.json
Test-Path validation\balon_video\salidas\2026-11-16_calibracion_temblor_dfl.json
Test-Path validation\balon_video\ESTA_NOCHE.md
Test-Path validation\balon_video\emular_dfl.py
Test-Path validation\balon_video\calibrar_temblor_dfl.py
Test-Path validation\balon_video\salidas\2026-11-16_emulacion_dfl.md
Test-Path validation\balon_video\salidas\2026-11-16_calibracion_temblor_dfl.md
```

**Qué mirar:** la rama es `exp/balon-video` y los once `Test-Path` dicen `True`.

**Si alguno dice `False`,** falta subir algo a la rama:
1. Avisa a Claude.
2. Mientras, puedes hacer los pasos 4 y 5, que no lo necesitan.
3. Cuando esté subido, haz `git pull` y repite los `Test-Path`.

**Qué pegar:** los once `True` o `False`, en orden.

## Paso 4. El entorno del detector (una sola vez; de 5 a 15 minutos)

Crea un entorno nuevo con Python 3.13 e instala las versiones fijadas. Baja varios cientos de MB, sobre todo torch.

```powershell
py -3.13 -m venv C:\Users\34656\.venvs\mtah2027-balon
C:\Users\34656\.venvs\mtah2027-balon\Scripts\python.exe -m pip install torch==2.15.0 torchvision==0.29.2 ultralytics==8.4.215 opencv-python==5.0.0.93 numpy==2.5.4 pandas==3.1.1
C:\Users\34656\.venvs\mtah2027-balon\Scripts\python.exe -m pip show opencv-python-headless
```

**Qué mirar:**
- El `pip install` acaba con `Successfully installed …`.
- `pip show` dice `WARNING: Package(s) not found: opencv-python-headless`. Tiene que haber un solo opencv,
  `opencv-python`, porque dos se pisan.
- **Si `pip show` sí lo encuentra,** quita los dos y vuelve a poner el bueno:

  ```powershell
  C:\Users\34656\.venvs\mtah2027-balon\Scripts\python.exe -m pip uninstall -y opencv-python-headless opencv-python
  C:\Users\34656\.venvs\mtah2027-balon\Scripts\python.exe -m pip install opencv-python==5.0.0.93
  ```

**Qué pegar:** nada si sale así; si falla, el error de pip. Las versiones se comprueban en el paso 5.

## Paso 5. El modelo (1 o 2 minutos)

Esto hace el paso:
1. Baja el modelo abierto de Hugging Face a `C:\Users\34656\mtah2027-modelos\`, fuera del repo.
2. Comprueba que es exactamente el fijado.
3. Lo carga sin red y detecta en una imagen en negro.

El detector corre en tu máquina: no manda nada del partido a ningún sitio.

```powershell
C:\Users\34656\.venvs\mtah2027-balon\Scripts\python.exe validation\balon_video\detector.py --descargar
C:\Users\34656\.venvs\mtah2027-balon\Scripts\python.exe validation\balon_video\detector.py --comprobar
```

**Qué mirar:**
- Con `--descargar`: `modelo en C:\Users\34656\mtah2027-modelos\yolo-football-ball-detection.pt  sha256 fb37942448e7…  revisión 63666b30e2a4`.
- Con `--comprobar`:
  - `escaneo del pickle: 29 clases o funciones, todas permitidas`;
  - `cargado en CPU con 4 hilos; detecciones en una imagen en negro: …`. Lo esperable es 0;
  - una línea con las versiones: python `3.13.9`, numpy `2.5.4`, torch `2.15.0` (puede llevar `+cpu` detrás), opencv
    `5.0.0` y ultralytics `8.4.215`.
- Si sale `ERROR: …`, para y pégalo.

**Qué pegar:** la salida de los dos.

## Paso 6. Las pruebas sin datos (unos minutos)

Prueban el código con datos inventados. Ninguna lee el partido.

```powershell
C:\Users\34656\.venvs\mtah2027-balon\Scripts\python.exe validation\scripts\prueba_detector_balon.py
C:\Users\34656\.venvs\mtah2027-balon\Scripts\python.exe validation\scripts\prueba_balon_video_sondeo.py
C:\Users\34656\.venvs\mtah2027-balon\Scripts\python.exe validation\scripts\prueba_balon_video_detectar.py
C:\Users\34656\.venvs\mtah2027-balon\Scripts\python.exe validation\scripts\prueba_balon_video_capa.py
C:\Users\34656\.venvs\mtah2027-balon\Scripts\python.exe validation\scripts\prueba_pipeline.py
```

**Qué mirar:** cada una acaba en `TODO BIEN`.
- Las líneas `[SALTA]` son normales. Por ejemplo, la prueba del detector se salta la detección en imágenes del
  dataset abierto, que no tienes.
- Si alguna acaba en `FALLAN …`, para.

**Qué pegar:** solo la última línea de cada una, en orden. Cópiala a mano.

## Paso 7. El ensayo corto del sondeo (unos 5 minutos)

Comprueba que todo arranca con el partido y cronometra:
- lee el ATD entero;
- abre el vídeo y lo decodifica hasta la mitad de la 1ª parte.

No mide nada del balón.

```powershell
C:\Users\34656\.venvs\mtah2027-balon\Scripts\python.exe validation\partido\balon_video_sondeo.py --ensayo --tramos 1 --largo 50
```

**Qué mirar:**
- `"resultado": "ensayo correcto"`.
- `"hilos_torch": 4` y `"backend_video": "FFMPEG"` (el lector de vídeo).
- `"ms_por_frame_decodificado"` y `"ms_por_frame_detectado_en_imagen_negra"`: con ellas se calcula cuánto tarda el
  paso 8.
- `"horas_estimadas_partido_entero_techo"` es lo más que tardaría el paso 9.
  - Es un techo: solo se detecta donde el ATD ve el balón.
  - **Si pasa de 8, no hagas los pasos 8 y 9:** pega el JSON y espera. La puerta 0 para la línea si el tiempo para
    los 199.319 frames no cabe en 8 horas en esta máquina (bitácora, puerta 0; también la 2.4).

**Qué pegar:** el JSON entero.

## Paso 8. La puerta 1b (lo que tarda sale de las cifras del paso 7)

Es la medida de verdad, con la variante fijada: busca el balón en un recorte de 320 píxeles alrededor de donde lo ve
el ATD, ampliado al doble, con confianza 0,10.
- Detecta en 40 tramos de 15 segundos: 15.000 frames, 10 minutos de vídeo.
- Además, decodifica el vídeo entero para contar sus frames.

**Antes:** los dos `Test-Path` de los JSON del paso 3 tienen que decir `True`. Si no, no lo lances, porque saldría
«sin veredicto».

```powershell
C:\Users\34656\.venvs\mtah2027-balon\Scripts\python.exe validation\partido\balon_video_sondeo.py
```

**Cuánto tarda, en minutos,** con las dos cifras del paso 7:
- (199.319 × `ms_por_frame_decodificado` + 15.000 × `ms_por_frame_detectado_en_imagen_negra`) / 60.000;
- más unos 3 minutos para leer el ATD y la homografía.

Por ejemplo, si salieran 3 ms y 60 ms, serían unos 28 minutos. Son cifras inventadas, solo para ver la cuenta: en tu
máquina no se ha medido nunca lo que tarda en decodificar este vídeo.

Va enseñando el % hecho de la muestra. **Al llegar al 100 % sigue un rato más,** porque decodifica el resto del
vídeo para contar sus frames. No lo cortes.

**Qué mirar:** al final del JSON, dentro de `"veredictos"`, la línea `"global"`.

| `"global"` | qué haces |
|---|---|
| `"SIGUE"` | pega el JSON; lanza el paso 9 sin esperar respuesta solo si el techo del paso 7 fue de 8 horas o menos (si no, espera respuesta) |
| `"NO SIGUE"` | la línea del balón del vídeo se para aquí: pega el JSON y no lances el paso 9 |
| `"sin veredicto: …"` | pega el JSON y no lances el paso 9 |

Más arriba, como comprobación:
- `"frames_decodificados": 199319`;
- `"hilos_torch": 4`;
- dentro de `"parametros"`, `"variante_fijada": true` y `"emulacion": "2026-11-16_emulacion_dfl.json"`. Si sale
  `null`, no ha leído la emulación.

**Qué pegar:** el JSON entero, desde `{` hasta `}`. Las líneas de progreso no hacen falta.

## Paso 9. Solo si la 1b dice `SIGUE`: la detección del partido entero (de noche)

- **Qué hace:** detecta el balón en todo el partido.
- **Dónde lo guarda:** en una caché, es decir, un fichero de tu carpeta de datos:
  `MTAH_DATA_DIR\tactical\BAR-ATH_tactical_balon_video.npz`.
- **Cuánto tarda:** horas. El paso 7 da el techo.

**Antes de lanzarlo:**
- deja el portátil enchufado;
- que no se suspenda: en Configuración > Sistema > Energía, pon que no se suspenda nunca mientras está enchufado, y
  no cierres la tapa. Por la mañana lo vuelves a dejar como estaba;
- si puedes, pausa las actualizaciones de Windows hasta mañana (Configuración > Windows Update), para que no
  reinicie de noche.

```powershell
C:\Users\34656\.venvs\mtah2027-balon\Scripts\python.exe validation\partido\balon_video_detectar.py
```

- **No hagas clic dentro de la ventana mientras corre.** En la consola clásica de Windows, un clic la pone en modo
  «Seleccionar» y el programa se queda parado hasta que pulsas Esc.
- **Si se corta** (un reinicio, un corte de luz, la ventana cerrada, o un `ERROR` al guardar), vuelve a lanzar el
  mismo comando, en una PowerShell nueva. Guarda lo hecho cada 5.000 frames y sigue desde ahí. Si lo lanzaste con
  `--forzar`, relánzalo también con `--forzar`: sigue desde lo guardado igual.

  ```powershell
  cd C:\dev\mtah2027-piso2nyc
  C:\Users\34656\.venvs\mtah2027-balon\Scripts\python.exe validation\partido\balon_video_detectar.py
  ```

  - **No hagas `git pull` antes de relanzarlo.** Si el pull cambia el código que detecta, el script se para con
    «hay un parcial de otra configuración (difiere: …)» y no toca lo hecho. Pega esa línea y espera: con `--forzar`
    se tiraría lo hecho. El `git pull` va después, cuando la detección haya acabado.
- **Si por la mañana la ventana está cerrada y ya había acabado,** el mismo comando dice «ya existe la caché». Entonces
  saca el resumen sin volver a detectar. Lleva también los tiempos acumulados de todas las ejecuciones:

  ```powershell
  cd C:\dev\mtah2027-piso2nyc
  C:\Users\34656\.venvs\mtah2027-balon\Scripts\python.exe validation\partido\balon_video_detectar.py --resumen
  ```

- **La caché es dato del partido:** no la abras, no la copies al repo y no la pegues.

**Qué pegar, por la mañana:** el JSON que imprime al acabar. Lleva:
- la huella de la caché, que se compara con la de Antonio en el paso 11;
- `"informativo"`, con el commit con que se detectó, que es el que usará Antonio;
- `"tiempos_acumulados"`, sumados entre reanudaciones: es la medida de tiempo de la puerta 2.4;
- `"para_comparar_maquinas"`: huellas sin datos para saber, si las cachés no coinciden, si cambia la lista de
  frames, el código o solo el detector.

## Paso 10. Mañana: la entrega de prueba (puerta 2.2)

Solo con la detección del paso 9 acabada **y después de que Claude haya leído la 2.1** con el JSON del paso 9, en
datos abiertos, y diga que pasa. Si no pasa, la línea se para y no se genera la entrega de prueba (la bitácora fija
el orden: la 2.1 y después la 2.2). Abre una ventana nueva de PowerShell:

```powershell
cd C:\dev\mtah2027-piso2nyc
git checkout exp/balon-video
git pull
git branch --show-current
Test-Path evaluation\results\equipo_v8.csv
C:\Users\34656\.venvs\mtah2027-entrega\Scripts\python.exe validation\partido\probar_entrega.py prueba_balon_video --capa balon_video.ajuste_b5_video --contra equipo_v8
C:\Users\34656\.venvs\mtah2027-entrega\Scripts\python.exe evaluation\validate_submission.py evaluation\results\prueba_balon_video.csv
C:\Users\34656\.venvs\mtah2027-entrega\Scripts\python.exe evaluation\run_evaluation.py --no-detail
```

- Basta el entorno limpio: la capa solo lee la caché de la detección, no el vídeo.
- `probar_entrega.py` hace tres cosas seguidas:
  1. genera la entrega de prueba;
  2. cuenta el balón fuera;
  3. la compara con `equipo_v8`.
- **Si el `Test-Path` de `equipo_v8.csv` da `False`,** no lances `probar_entrega.py` con `--contra equipo_v8`: genera
  la entrega y cuenta el balón fuera, y solo al final dice «No encuentro una de las entregas…», sin parar. Lánzalo
  desde el principio con `--contra ensayo_16nov`, que vale solo si el paso 1 dio el sha256 de `equipo_v8`.

**Qué mirar:** los criterios de daño de la puerta 2.2, escritos antes de generarla. Pasa si se cumplen todos:
- `frames con piezas en conflicto: 0` y, en los dos tramos, ninguna racha de menos de 25 frames: ni posesiones, ni de
  juego, ni paradas.
- El `D` casi no se mueve:
  - entre los frames evaluados que pasan de `D` a juego y los que pasan de juego a `D`, como mucho 1.000;
  - las paradas, entre 110 y 122 (las 116 de `equipo_v8`, ±6).
- Las posesiones, entre 219 y 328.
- Los frames que pasan de un equipo al otro, como mucho 15.886, el 10 % de los evaluados.
- El validador da `OK` y `Valid.`.
- La tabla de la ventana pública se mira, pero **no decide nada**.

Esto solo dice que la capa no rompe nada. Si mejora o no, lo decide la puerta 2.1, en datos abiertos.

**Qué pegar:** la salida entera de los tres comandos de Python.

## Paso 11. La segunda máquina (la que no hizo los pasos 8 y 9)

Esta tarde los pasos 8 y 9 los hace Antonio, así que esta parte la hace Ismael esta noche. En lo de abajo, «Ismael» es
quien hizo el paso 9 y «Antonio» la segunda máquina: si es al revés, cambia los nombres.

Son dos cosas, con sus rutas: `<repo>`, `<entorno limpio>` y `<entorno del detector>` son las de esa máquina.
- En Windows, el Python es `<carpeta>\Scripts\python.exe`.
- En Linux o macOS, es `<carpeta>/bin/python`, y las rutas van con `/`. El entorno se crea con
  `python3.13 -m venv <carpeta>`, en vez de `py -3.13 -m venv <carpeta>`.

Lo de «Qué no pegar nunca» vale igual para él.

**a) Reproducir `equipo_v8`.** En `main`, con un entorno limpio de Python 3.13 y `requirements-entrega.txt`. Las
líneas de `venv` y `pip install` solo hacen falta si aún no tiene ese entorno.

```powershell
cd <repo>
git checkout main
git pull
py -3.13 -m venv <entorno limpio>
<entorno limpio>\Scripts\python.exe -m pip install -r requirements-entrega.txt
<entorno limpio>\Scripts\python.exe -m possession.pipeline --name ensayo_antonio
<entorno limpio>\Scripts\python.exe evaluation\validate_submission.py evaluation\results\ensayo_antonio.csv
```

Tiene que dar `sha256: d78c514dcf5e8ad9bcff5f76da0aadf409c01ce89ad65ad0435421daf31ce2b2`, con
`python 3.13.x, numpy 2.5.4`. Pega a Claude la salida de los dos últimos comandos.

**b) Solo si la 1b pasó: la detección del partido entero en su máquina.** Es la puerta 2.3, que la bitácora escribe
así: «el comando único regenera la entrega byte a byte dos veces en una máquina y una en otra (con la detección
dentro)». Necesita el vídeo táctico en su carpeta de datos (`tactical\BAR-ATH_tactical.mp4`, 4,9 GB).
1. `git fetch origin` y `git checkout <commit>`, con el `"commit"` de `"informativo"` del JSON del paso 9 de Ismael (no
   `git pull` de la rama: si entra algo entre las dos ejecuciones, la comparación no vale). Las dos cachés tienen que
   decir `"cambios_sin_commitear": false`.
2. Los pasos 4, 5 y 6 de esta guía, con su `<entorno del detector>`.
   - En Linux, antes del `pip install` del paso 4, instala torch desde el índice de CPU, para no bajar varios GB de
     CUDA:

     ```bash
     <entorno del detector>/bin/python -m pip install torch==2.15.0 torchvision==0.29.2 --index-url https://download.pytorch.org/whl/cpu
     ```

3. El paso 7, para saber cuánto tardará (con la misma parada si pasa de 8 horas).
4. El paso 9, de noche si hace falta. Pega el JSON del final.
5. Solo si la 2.1 pasó (como en el paso 10): con su caché y el entorno limpio, la entrega de prueba del paso 10
   (solo el primer comando de Python, el de `probar_entrega.py`, con `--contra ensayo_antonio`), y pega su `sha256`.

Y en la máquina de Ismael, la segunda ejecución: repetir el paso 9 con `--forzar` (rehace la caché) y regenerar la
entrega de prueba del paso 10. Tienen que salir la misma huella de la caché y el mismo sha256 de la entrega.

Las entregas de prueba solo se comparan si `possession.pipeline` imprime en las dos máquinas el mismo
`código: commit …` y `sin cambios locales en el código de la entrega`. Si la rama se ha movido después del paso 10 de
Ismael, Antonio hace `git checkout` de ese mismo commit para su entrega de prueba.

**Cómo se lee** (Claude): si las huellas de la caché coinciden, la entrega tiene que salir igual. Si no coinciden,
deciden los sha256 de las entregas de prueba; y `"para_comparar_maquinas"` dice si cambia la lista de frames
(`lista_sha256`), el código (`codigo_sha256`) o solo lo que da el detector (`huella_solo_pixeles`).

## Qué no pegar nunca

- **El contenido de ningún CSV:** ni las entregas ni nada de `evaluation\results`.
- **Nada de `evaluation\reports`.**
- **Nada de la carpeta de datos (`MTAH_DATA_DIR`):**
  - ni el vídeo, ni el ATD, ni la homografía, ni el Smart Tagging;
  - ni la caché de detecciones (`BAR-ATH_tactical_balon_video…`);
  - tampoco imágenes ni capturas del vídeo.
- **Ningún fichero adjunto con `@` ni arrastrado al chat:** adjuntar un fichero ya cuenta como subirlo.
- **Solo lo que imprimen los comandos de esta guía.** Si alguna salida enseñara valores del partido (no debería), no
  la pegues: di qué script era y en qué paso.
