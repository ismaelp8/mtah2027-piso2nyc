---
name: subir
description: Termina una tarea y la manda a revisión. Limpia los outputs de los notebooks, revisa que no se cuele nada prohibido, hace el commit con la autoría de quien sube, hace push y abre la PR con la plantilla y los reviewers correctos; si es Ismael, puede subirlo directo a main sin PR. Úsala cuando alguien diga "sube esto", "ya he terminado", "haz la PR" o "/subir".
argument-hint: "[resumen opcional del cambio]"
---

# Subir una tarea y abrir la PR

Quien te habla puede no saber git: explica cada paso en una frase sencilla. Pedir `/subir` es pedir que
se suba, pero **antes del push enséñale el resumen del paso 7 y espera su sí**.

Resumen que da la persona: $ARGUMENTS

## 1. Rama e identidad

- Ejecuta `git branch --show-current` y `gh api user --jq .login`.
  - **Si es Ismael (`ismaelp8`) y está en `main`,** puede subir directo a `main` (`CONTRIBUTING.md` §5):
    sigue ahí salvo que pida rama y PR. Los pasos marcados «directo a `main`» son para este caso.
  - **Si es otra persona y está en `main`, no hagas commit ahí.** Propón una rama
    (`CONTRIBUTING.md` §2) y créala con `git switch -c <rama>`: los cambios se vienen con ella.
- Ejecuta `git config user.name` y `git config user.email`. Tienen que ser los de la persona que te
  habla. Si no lo son, para y ayúdale a configurarlos. Nunca uses la identidad de otra persona.

## 2. Notebooks, antes de mirar ningún diff

```
python .claude/skills/subir/outputs_notebooks.py
```
El script solo imprime recuentos.
- Si algún notebook sale `SUCIO`, díselo y pide permiso para limpiarlo, avisando de que perderá los
  outputs (los recupera volviendo a ejecutar). Con su sí:
  ```
  python .claude/skills/subir/outputs_notebooks.py --limpiar <notebook>
  ```
- No leas ni hagas diff de un notebook hasta que salga `OK`.

## 3. Qué se va a subir

- Ejecuta `git status --short` (solo nombres). Antes de seguir, para y pregunta si aparece:
  - un `BAR-ATH_*` que no sea `evaluation/gt/BAR-ATH_possession_gt_public*`;
  - `*.mp4`, `*.npz`, `*.npy`, `*.parquet`, `*.pkl`, `*.feather`, `*.h5` o `*.pdf`;
  - un `*.csv` fuera de `evaluation/gt/`;
  - algo dentro de `data/`;
  - `CLAUDE.local.md` o `.claude/settings.local.json`;
  - un fichero oficial modificado: `games.py`, `evaluation/`, `starter/`, los `.md` oficiales,
    `.gitignore`, `LICENSE`, `CITATION.cff`, `requirements-starter.txt`, `data/README.md`.

  Nada de eso entra en git (`CONTRIBUTING.md` §7 y §9).
- Mira el cambio con `git diff --stat` y luego con `git diff -- <ficheros>`, solo de los ficheros que
  han pasado el filtro anterior. Los notebooks ya están limpios.
- Si el cambio toca código del pipeline, lanza el agente `revisor`. Resuelve los 🔴 o díselos a la
  persona antes de seguir.
- Si es un cambio de método y `docs/decisiones.md` no aparece entre los ficheros, propón `/decision`.

## 4. Commit

- Ficheros **por nombre**: `git add <fichero> <fichero> …`. Nunca `-A`, `.` ni `commit -a`.
- Mensaje: una frase en español que diga qué cambia y por qué, con mayúscula inicial, sin punto final y
  de unos 72 caracteres (`CONTRIBUTING.md` §3).
- Sin `Co-Authored-By` ni ninguna otra atribución.
- Si el mensaje tiene más de una línea, escríbelo en un fichero temporal fuera del repo y usa
  `git commit -F <fichero>`.
- Comprueba la autoría con `git log -1 --format="%an <%ae>%n%b"`: tiene que ser la persona, y el cuerpo
  no puede llevar `Co-Authored-By`.

## 5. Ponerse al día con `main`

- Ejecuta `git fetch origin` y `git rev-list --count HEAD..origin/main`.
- Si es mayor que 0, mergea `origin/main` en la rama (`git merge origin/main`) y resuelve los conflictos
  con la persona. Nunca uses `rebase` sobre algo ya subido ni `--force`.
- **Directo a `main`:** si es mayor que 0, `git pull --rebase --autostash origin main`. Solo recoloca los
  commits de Ismael que aún no están en GitHub. Si hay conflictos, resuélvelos con él.

## 6. Datos de la PR

**Directo a `main`:** sin PR, sáltate este paso.

- **Título:** la frase del commit, o un resumen si hay varios commits.
- **Cuerpo:** la plantilla de `.github/pull_request_template.md` rellena.
  - **Qué cambia y por qué:** dos o tres frases.
  - **Tipo:** marcado.
  - **Cómo se ha comprobado:** solo agregados.
  - **Checklist:** marca solo lo que sea verdad.
  - Sin "Generated with Claude Code" ni atribuciones.
- **A quién se le pide la revisión por defecto,** según quién abre. Puede revisarla cualquier otra persona
  del equipo. Mira quién es con `gh api user --jq .login`:

  | login | `--reviewer` |
  |---|---|
  | `ismaelp8` | `ortegafer` |
  | `ortegafer` | `ismaelp8` |
  | otro | `ismaelp8` y `ortegafer` |

- **¿Borrador?** Si la persona dice que aún no está terminado, añade `--draft`.

## 7. Confirmación (obligatoria)

Enséñale en pocas líneas y espera su sí:
- la rama (o `main`, si sube directo);
- los commits (`git log --oneline origin/main..HEAD`);
- los ficheros;
- el título y los reviewers, si hay PR.

## 8. Push y PR

**Directo a `main`:** `git push origin main`, sin PR. Nunca `--force`.

Con rama:
```
git push -u origin <rama>
gh pr create --base main --head <rama> --title "<título>" --body-file <fichero-temporal> --reviewer <login>
```
- **El cuerpo** escríbelo en un fichero temporal fuera del repo; así se evitan problemas de comillas en
  PowerShell.
- **Si `--reviewer` falla con dos personas,** crea la PR sin él y añádelos uno a uno con
  `gh pr edit <n> --add-reviewer <login>`. Dile cuál ha funcionado.

## 9. Cierre

Dale el enlace de la PR y explícale lo que sigue:
- la revisa otra persona del equipo, la que esté disponible;
- con una aprobación, quien aprueba la mergea;
- después, `/actualizar` le devuelve a `main` limpio.

**Directo a `main`:** dale el hash del commit subido. Los demás lo reciben con `/actualizar`.

No mergees tú.
