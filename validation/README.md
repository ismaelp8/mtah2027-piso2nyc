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
| `scripts/prueba_pipeline.py` | prueba el esqueleto del pipeline (`possession/`) con un partido inventado: interfaz de las piezas, tramos evaluados, tramo antes del saque, decodificador contra la búsqueda exhaustiva, determinismo, CSV y lector del ATD | ninguno del partido |
| `scripts/comprobar_balon_muerto.py` | comprueba `possession/dead_ball.py`: interfaz, que no abre ficheros, dónde marca `D`, que no contradice la GT pública, determinismo, que los frames de saque del FAQ y de `games.py` cuadran y que con otro partido da error | GT pública |
| `partido/diagnostico_balon_muerto.py` | ¿sirve el balón del ATD para el detector de `D`? Balón fuera del campo, en los reinicios y en los saques iniciales | **datos del partido: solo una persona** |
| `partido/diagnostico_coordenadas.py` | ¿separa x = 0,5 a los dos equipos? Temblor del balón y tramos con el balón quieto | **datos del partido: solo una persona** |
| `partido/comun.py` | constantes y utilidades de los dos diagnósticos (no se ejecuta solo) | — |
| `partido/agregados_smart_tagging.py` | ventanas `SET PIECES` por tipo (duración, `Team N/A`), cobertura de los frames evaluados por las fases, huecos entre fases, goles → saque posterior | **datos del partido: solo una persona** |
| `partido/agregados_balon_reinicios.py` | ¿las "reanudaciones" del detector de golpeo caen donde acaba la ventana `SET PIECES` y donde suben los jugadores? Balón que desaparece saliendo del campo; columna de velocidad del ATD frente al desplazamiento suavizado | **datos del partido: solo una persona** |
| `partido/agregados_jugadores.py` | velocidad media de los jugadores (en todo el partido, antes y después de cada reinicio, al principio y al final de cada parte) frente a la DFL; jugadores fuera de los límites | **datos del partido: solo una persona** |
| `partido/recuento_ventana.py` | experimento 2: qué convención sigue la GT pública (cuándo cambia la posesión), medida con el tracking en vez de a ojo; se lee con la regla de `experimento2/BITACORA.md` §7 | **datos del partido: solo una persona** (ATD de la ventana y GT pública) |
| `experimento2/calibrar_dfl.py` | calibra ese instrumento en la DFL degradada para parecerse al ATD (`--tabla` da las tablas de la bitácora) | DFL |
| `experimento2/pruebas_sinteticas.py` | prueba el instrumento y el lector de `recuento_ventana.py` con datos inventados | GT pública y datos sintéticos |
| `scripts/revision_balon_muerto/` | pruebas de la revisión del detector de `D` (13/11): coste de cada error de `D`, `io.py` con un ATD sintético, jugadores solos en la DFL; su `README.md` dice cómo repetirlas | GT pública, GT sintética, DFL |

Se ejecutan desde la raíz del repo, con el entorno de siempre:

```bash
python validation/scripts/perfil_etiquetas.py evaluation/gt/BAR-ATH_possession_gt_public.csv
python validation/scripts/sensibilidad_metrica.py
python validation/scripts/descargar_datos_abiertos.py dfl --solo-ligeros
python validation/scripts/comprobar_balon_muerto.py
python validation/scripts/revision_balon_muerto/coste_errores_D.py
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
