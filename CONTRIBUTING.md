# Normas del repo

Estas normas las sigue todo el equipo, y Claude también. Si delegas el git en Claude, las skills de
`.claude/skills/` las aplican por ti: mira la última sección.

> **Nadie las hace cumplir por nosotros.** Con GitHub Free y el repo privado no hay protección de ramas
> ni CODEOWNERS (la API responde 403). Se cumplen porque las cumplimos.

## Lo esencial

1. **Solo Ismael (`ismaelp8`) sube directo a `main`.** Los demás, una rama por tarea y siempre por PR.
2. **Cada PR lleva la plantilla y la revisa otra persona del equipo,** la que esté disponible. Nadie
   aprueba su propia PR, y basta con una aprobación para mergear.
3. **El commit es de quien sube los cambios,** con su propia identidad de git. Nunca aparece como hecho
   por Claude ni por otra persona.
4. **Ningún dato del partido entra en git:** ni vídeos, ni tracking, ni cachés, ni CSV de entregas, ni
   outputs de notebooks, ni PDFs.
5. **Los ficheros oficiales no se tocan.** Las correcciones de Metrica entran por `upstream`.
6. **Los datos del partido no pasan por Claude** (ver la regla nº 1 en `CLAUDE.md`).

---

## 1. Antes de empezar: tu máquina (una sola vez)

Comandos en PowerShell (Windows) y en bash (macOS/Linux). Donde solo hay un bloque, vale para los dos.

**Tu identidad de git.** Es la que firma tus commits. Usa tu nombre y el email de tu cuenta de GitHub, o
el `...@users.noreply.github.com` que aparece en GitHub → Settings → Emails.
```bash
git config user.name "Nombre Apellido"
git config user.email "tu-email-de-github@ejemplo.com"
git config user.name; git config user.email      # comprobar
```
Si compartes ordenador o Claude hizo algo con la identidad de otra persona, corrígelo **antes** de
hacer commit.

**GitHub CLI** (`gh`): Claude lo usa para abrir y revisar PR.
```bash
gh auth login        # GitHub.com → HTTPS → login con el navegador
gh auth status
```

**Remotos.** `origin` es nuestro repo y `upstream` el de Metrica.
```bash
git remote -v
git remote add upstream https://github.com/metrica-sports/more-than-a-hack-2027.git   # si no aparece
```

**Tu `CLAUDE.local.md` (opcional).** Es un fichero personal que Claude lee junto a `CLAUDE.md` y que no
se sube. No podemos tocar el `.gitignore` oficial, así que cada uno lo excluye en su copia:
```bash
echo CLAUDE.local.md >> .git/info/exclude
```
```powershell
Add-Content .git/info/exclude CLAUDE.local.md    # no uses >> en PowerShell 5: escribe en UTF-16 y git no lo entiende
```
Contenido de ejemplo:
```markdown
# Personal
- Soy <nombre> (GitHub `<usuario>`). Mi papel: <área>.
- Sistema: Windows con PowerShell | macOS con zsh | Linux.
- Git: lo hago yo | lo delego en Claude (explícamelo paso a paso).
- Mi entorno de Python: <ruta del venv>.
```

---

## 2. Ramas

- **Una rama por tarea,** creada desde un `main` actualizado (`/empezar`). Ramas cortas: mejor mergear
  cada día que acumular. Ismael puede saltarse la rama y trabajar directo en `main` (§5).
- **Nombre:** `tipo/descripcion-corta`, en minúsculas, con guiones, sin tildes ni espacios.

| tipo | para qué | ejemplo |
|---|---|---|
| `feat` | código nuevo del pipeline | `feat/detector-balon-muerto` |
| `exp` | experimento que puede no llegar a `main` | `exp/hmm-tres-estados` |
| `fix` | arreglo de algo que ya está en `main` | `fix/alineacion-smart-tagging` |
| `docs` | documentación, decisiones, documento técnico | `docs/documento-tecnico` |
| `infra` | herramientas, dependencias, configuración, pipeline de un comando | `infra/requirements-fijados` |
| `sync` | traer cambios de `upstream` | `sync/upstream-20261113` |

---

## 3. Commits

- **Mensaje:** una frase en español que diga **qué cambia y por qué**.
  - Mayúscula inicial y sin punto final.
  - Primera línea de unos 72 caracteres como mucho.
  - Si el porqué necesita más, una línea en blanco y un párrafo de cuerpo.
- **Un cambio lógico por commit.** Lo que no tiene que ver va en otro commit, o en otra rama.
- **Ficheros siempre por nombre:** `git add <fichero> <fichero>`. Nunca `git add -A`, `git add .` ni
  `git commit -a`: así no se cuela nada de lo de la sección 7.
- Ejemplos:
  ```
  El detector de D usa los SET PIECES como fin del tramo muerto
  La interpolación del balón no rellena huecos de más de 10 frames, que inventaban posesiones
  Plantilla de PR y normas del repo
  ```

## 4. Autoría

- **El autor de un commit es siempre la persona que sube los cambios,** con su propia identidad de git
  (sección 1).
- **Nunca** aparece Claude como autor ni como coautor: nada de `Co-Authored-By`. En las PR, nada de
  "Generated with Claude Code". `.claude/settings.json` ya lo desactiva en Claude Code. Si aun así
  aparece, se quita antes de subir.
- **Nunca** se hace un commit con la identidad de otra persona. Ismael no firma lo de Manuel, y al
  revés.
- El merge con squash de GitHub atribuye el commit final al autor de la PR, así que la regla se cumple
  también en `main`.

---

## 5. Pull requests

- **Todo entra en `main` por PR, salvo lo que sube Ismael** (último punto de esta sección), con la
  plantilla de `.github/pull_request_template.md` rellena. Si todavía es trabajo en curso, se abre como
  borrador (`--draft`).
- **Revisión:** la revisa, la aprueba y la mergea cualquier persona del equipo que no sea quien la abre
  (decisión de Ismael, 15/11). `/subir` pide la revisión a Ismael (`ismaelp8`) y a David (`ortegafer`) para
  que alguien se entere, pero no hace falta que sean ellos.
- **Una aprobación basta.** Nadie aprueba su propia PR.
- **Merge:** lo hace quien aprueba (o el autor, si el reviewer se lo pide).
  - Con **squash**, para que cada PR sea un commit en `main`. Después se borra la rama.
  - **Excepción: las PR `sync/*` se mergean con merge commit,** nunca con squash. Si se aplastan, git
    pierde la pista de qué commits de Metrica ya tenemos y la siguiente sincronización da conflictos.
- **Comprobación mínima antes de pedir revisión:**
  - las métricas de la validación externa, si el cambio toca el modelo;
  - `/evaluar`, si genera una entrega;
  - todo ello en agregados, sin valores por frame.
- **Si `gh` no deja pedir revisión a dos personas a la vez,** se crea la PR y se añade a cada reviewer
  por separado con `gh pr edit <n> --add-reviewer <usuario>`.
- **Ismael (`ismaelp8`) puede hacer commit y push directo a `main`,** sin rama ni PR: es quien más
  cambios hace y quien mejor conoce git. Lo demás no cambia:
  - sus commits pasan las mismas comprobaciones que una PR: nada de lo de §7, notebooks sin outputs,
    ficheros oficiales sin tocar y su propia autoría;
  - antes del push, `git fetch origin`. Si GitHub tiene commits nuevos,
    `git pull --rebase --autostash origin main`, que solo recoloca sus commits aún no subidos, y después
    `git push origin main`;
  - nunca `--force`;
  - si quiere que David le revise algo, usa rama y PR como el resto.

  Para los demás, `main` se moverá más a menudo: `/actualizar` trae esos cambios a su rama.

---

## 6. Traer cambios de Metrica (`upstream`)

La organización corrige el scorer o la documentación de vez en cuando. Esos cambios entran así, con
`/sincronizar-upstream`:
```bash
git fetch upstream
git log --oneline main..upstream/main          # ¿hay algo nuevo?
git switch main; git pull --ff-only origin main
git switch -c sync/upstream-AAAAMMDD
git merge upstream/main                        # el commit de merge lo firma quien sincroniza
git push -u origin sync/upstream-AAAAMMDD      # y PR de tipo sync, que se mergea con merge commit
```
- Si hay conflicto en un fichero oficial, gana la versión de `upstream`: nosotros no los tocamos.
- Si necesitamos un arreglo en un fichero oficial, se abre un issue en
  https://github.com/metrica-sports/more-than-a-hack-2027. No se parchea aquí.

---

## 7. Qué no entra nunca en git

El repo será **público** el 17/11 y el historial de git es permanente. Lo que entra en un commit se
queda ahí aunque se borre después.

| qué | dónde vive | por qué |
|---|---|---|
| vídeos (`*.mp4`) | `$MTAH_DATA_DIR/tactical/` y `/broadcast/` | redistribución prohibida; GitHub limita a 100 MB por fichero |
| ATD, homografía, Smart Tagging (`BAR-ATH_tactical*`, `BAR-ATH_broadcast*`) | `$MTAH_DATA_DIR/...` | redistribución prohibida |
| cachés y features por frame (`*.npz`, `*.npy`, `*.parquet`, `*.pkl`, `*.feather`, `*.h5`) | `$MTAH_DATA_DIR/cache/` | son datos derivados que permiten reconstruir los originales |
| nuestras entregas (`evaluation/results/*.csv`) e informes (`evaluation/reports/`) | donde están (los ignora `.gitignore`) | son las etiquetas del partido completo |
| outputs de notebooks | en ningún sitio | llevan datos dentro |
| PDFs | fuera del repo | `.gitignore` los ignora; el documento técnico se escribe en `.md` y se exporta |
| `CLAUDE.local.md`, `.claude/settings.local.json` | tu copia local | son personales |
| entornos virtuales, `__pycache__` | fuera del repo o ignorados | no son código |

- **Los datos se descomprimen fuera del repo** (`MTAH_DATA_DIR`), nunca en `data/`.
- **Antes de cada commit,** mira `git status`: no puede aparecer ningún `BAR-ATH_*` salvo
  `evaluation/gt/BAR-ATH_possession_gt_public*`.
- **El `.gitignore` de la raíz es oficial y no se toca.** Lo que haya que excluir además, se excluye en
  `.git/info/exclude` de tu copia o no se añade. La única excepción es `validation/.gitignore`, que
  ignora los ficheros de datos dentro de esa carpeta como red de seguridad.

## 8. Notebooks

- **Siempre se suben sin outputs.** Los outputs guardan tablas, coordenadas y gráficos del partido.
- **Para limpiarlos:**
  - en Jupyter: *Kernel → Restart Kernel and Clear Outputs of All Cells* y guardar;
  - o por línea de comandos (comprueba primero y limpia después; solo imprime recuentos):
    ```bash
    python .claude/skills/subir/outputs_notebooks.py notebooks/
    python .claude/skills/subir/outputs_notebooks.py --limpiar notebooks/mi_notebook.ipynb
    ```
- **No se le pasa a Claude un notebook con outputs.** Claude lo comprueba con el script antes de abrirlo.
- **La exploración va en `notebooks/`,** con nombres `tema_autor.ipynb` (por ejemplo,
  `balon_muerto_manuel.ipynb`). La lógica que sirve se pasa a un módulo del paquete. Un notebook no forma
  parte del pipeline.

## 9. Ficheros oficiales

No se modifican:
- `games.py`, `evaluation/` y `starter/`;
- los `.md` oficiales (README, CHALLENGE, DATA, EVALUATION, SUBMISSION, RULES, FAQ, OVERVIEW);
- `.gitignore`, `LICENSE`, `CITATION.cff`, `requirements-starter.txt` y `data/README.md`.

La única excepción prevista es fijar las versiones de `requirements.txt` antes de congelar, y la decide
el responsable de infraestructura.

---

## 10. Con Claude: las skills

Si no quieres pelearte con git, díselo a Claude con estas órdenes (o con tus palabras: las reconoce).
Antes de subir nada te enseña un resumen y te pide confirmación.

| escribe | y Claude… |
|---|---|
| `/empezar detector de balón muerto` | actualiza `main` y te crea la rama `feat/detector-balon-muerto` |
| `/subir` | limpia notebooks, revisa los ficheros, hace el commit a tu nombre, lo sube y abre la PR con reviewers (Ismael puede subir directo a `main`) |
| `/actualizar` | trae lo último de `main` a tu rama; si tu PR ya se mergeó, te devuelve a `main` limpio |
| `/revisar-pr 12` | (quien revise) revisa la PR 12, te propone aprobar o pedir cambios, y mergea si se lo dices |
| `/sincronizar-upstream` | (Ismael) trae las correcciones de Metrica en una rama `sync/` con su PR |
| `/evaluar` | valida y puntúa una entrega, solo con agregados |
| `/decision HMM frente a histéresis` | apunta la decisión en `docs/decisiones.md` |
