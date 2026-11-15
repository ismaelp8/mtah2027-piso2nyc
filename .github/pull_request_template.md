## Qué cambia y por qué

<!-- Dos o tres frases. Si es una decisión de método, enlaza su entrada de docs/decisiones.md. -->

## Tipo

<!-- Marca uno con una x: [x] -->
- [ ] `feat`: código nuevo del pipeline
- [ ] `exp`: experimento
- [ ] `fix`: arreglo
- [ ] `docs`: documentación
- [ ] `infra`: herramientas, dependencias, configuración
- [ ] `sync`: cambios de `upstream` (se mergea con merge commit, no con squash)

## Cómo se ha comprobado

<!--
SOLO agregados: spellF1 / macroF1 de la validación externa (fuente, nº de partidos y de posesiones),
recuentos, tiempos. Nunca filas, frames, coordenadas ni etiquetas por frame del partido.
La ventana pública de 5 minutos solo sirve para comprobar que el pipeline funciona, no para elegir
entre versiones. Diferencias de spellF1 de menos de ~0,04 son ruido.
-->

## Checklist

- [ ] La rama se llama `tipo/descripcion` y la PR va contra `main`
- [ ] En el diff no hay datos del partido, vídeos, cachés, CSV de entregas, PDFs ni `CLAUDE.local.md`
- [ ] Los notebooks van sin outputs (`python .claude/skills/subir/outputs_notebooks.py`)
- [ ] No hay rutas fijas: todo pasa por `games.py` y `MTAH_DATA_DIR`
- [ ] Es determinista: semillas fijas y nada que dependa del orden de ficheros
- [ ] No hay constantes ligadas a frames concretos de este partido ni ajustes contra la ventana pública
- [ ] Los scripts imprimen solo agregados
- [ ] Los ficheros oficiales están sin tocar (`games.py`, `evaluation/`, `starter/`, `.md` oficiales, `.gitignore`)
- [ ] La decisión está apuntada en `docs/decisiones.md`, si es un cambio de método
- [ ] Los commits son míos, con mi identidad de git y sin `Co-Authored-By`

<!--
Revisión: puede revisarla y mergearla cualquiera del equipo, también quien la abre. Si toca código que usa
la entrega, avísalo al mergearla para que alguien la regenere y la valide.
-->
