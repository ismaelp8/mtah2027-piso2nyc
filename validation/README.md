# Validación externa

Aquí está todo lo que sirve para decidir entre métodos **sin mirar etiquetas del partido**: los pasos
que faltan, los scripts y los resultados. El porqué está en
[`docs/investigacion_metodos.md`](../docs/investigacion_metodos.md).

| qué | dónde |
|---|---|
| pasos para completar el experimento 0 y siguientes, con las dudas abiertas (D1…D21) | [`PASOS.md`](PASOS.md) |
| resultados, uno por fichero, con su índice | [`resultados/`](resultados/README.md) |
| scripts | [`scripts/`](scripts/) |

## Scripts

| script | qué hace | datos que lee |
|---|---|---|
| `scripts/perfil_etiquetas.py` | perfil de un CSV `frame,label`: posesiones, paradas y huella de retrasos frente a la tabla oficial | GT pública o etiquetas de datos abiertos |
| `scripts/sensibilidad_metrica.py` | cuánto cuesta cada tipo de error en `spellF1`, con una GT sintética | ninguno del partido |
| `scripts/descargar_datos_abiertos.py` | descarga la Bundesliga, los eventos del Barça como local y el Clásico de 2019, con versiones fijadas, fuera del repo | datos abiertos de otros partidos |

Se ejecutan desde la raíz del repo, con el entorno de siempre:

```bash
python validation/scripts/perfil_etiquetas.py evaluation/gt/BAR-ATH_possession_gt_public.csv
python validation/scripts/sensibilidad_metrica.py
python validation/scripts/descargar_datos_abiertos.py dfl --solo-ligeros
```

## Reglas

- **Los scripts de `validation/scripts/` solo leen datos abiertos de otros partidos, la GT pública o
  nada.** Claude puede ejecutarlos. Los que lean datos del partido van en `validation/partido/`: los
  ejecuta solo una persona y pega solo agregados (regla nº 1 de `CLAUDE.md`).
- **`validation/.gitignore` ignora los ficheros de datos** (`*.csv`, `*.json`, `*.xml`...) como red de
  seguridad. El `.gitignore` oficial de la raíz no se toca.
- **Los datos se descargan fuera del repo** (por defecto, `~/mtah2027-datos-abiertos`) y nunca se suben.
  Al repo van los scripts y los resultados agregados.
- **Por decisión de Ismael (11/11), este plan manda** sobre lo que digan `CLAUDE.md` y
  `docs/GUIA_EQUIPO.md` sobre la validación externa y la política de `X`. Esos documentos se escribieron
  antes.
