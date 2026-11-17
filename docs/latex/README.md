# El documento técnico en LaTeX

El texto vive en [`docs/documento_tecnico.md`](../documento_tecnico.md). Esta carpeta lo convierte en un
PDF maquetado para el formulario de la entrega (`<equipo>.pdf`, como pide `SUBMISSION.md`).

| fichero | qué es |
|---|---|
| `md_a_latex.py` | convierte el `.md` en `documento_tecnico.tex` y, con `--pdf`, compila el PDF |
| `plantilla.tex` | el aspecto: letra, colores, márgenes, portada, cajas y tablas |
| `documento_tecnico.tex` | **generado**: no se edita a mano. Es un único fichero, válido para Overleaf |
| `build/` | lo que deja pdflatex, con el PDF final. No va a git |

## Cómo se genera el PDF

Desde la raíz del repo, con Python 3.10 o más (sin dependencias) y `pdflatex` (TeX Live o MiKTeX):

```bash
python3 docs/latex/md_a_latex.py --pdf
```

Deja el PDF en `docs/latex/build/<equipo>.pdf`, con el nombre que diga la línea `**Equipo:**` del `.md`.

Sin LaTeX instalado: `python3 docs/latex/md_a_latex.py` solo regenera el `.tex`. Ese fichero se sube a
Overleaf (proyecto vacío, compilador pdfLaTeX) y compila tal cual. El documento solo lleva agregados, así
que subirlo no choca con la regla del concurso sobre los datos del partido.

## Al cambiar el documento

1. Edita el `.md` (el texto) o `plantilla.tex` (el aspecto). No toques `documento_tecnico.tex`.
2. Regenera con el comando de arriba y sube el `.md` y el `.tex` juntos.
3. `python3 docs/latex/md_a_latex.py --comprobar` falla si el `.tex` no está al día con el `.md`.

Las marcas `[PENDIENTE: ...]` del `.md` salen en rojo en el PDF, y el script avisa de cuántas quedan.
