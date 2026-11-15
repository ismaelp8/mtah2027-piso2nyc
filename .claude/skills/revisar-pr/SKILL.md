---
name: revisar-pr
description: Para quien revise la PR de otra persona (cualquiera del equipo). Revisa una PR del repo con el agente revisor, propone aprobar, pedir cambios o comentar, y la mergea si se pide (squash, o merge commit si es sync/*). Úsala con "/revisar-pr 12", "revisa la PR de Manuel" o "¿qué PR tengo pendientes?".
argument-hint: "[número de PR]"
---

# Revisar una PR

PR: $ARGUMENTS

## 1. Elegir la PR

- **Sin número:** `gh pr list --search "review-requested:@me"` y, si no sale ninguna, `gh pr list`.
  Pregunta cuál revisar.
- **Con número:** ejecuta
  `gh pr view <n> --json number,title,author,headRefName,baseRefName,isDraft,reviewDecision,reviews,files,url`.
- **Si el autor es quien te habla** (`gh api user --jq .login`), no puede aprobarla. Díselo; solo puede
  comentar.

## 2. Preparar la copia local

- Si quien revisa tiene cambios sin commitear (`git status --short`), pregunta antes de cambiar de rama.
- Ejecuta `gh pr checkout <n>` y luego `git fetch origin main`.

## 3. Seguridad primero: solo nombres, antes de ver ningún contenido

- **Saca la lista de ficheros** de la PR, solo los nombres: el campo `files` de `gh pr view` o
  `git diff --name-status origin/main...HEAD`.
- **Notebooks:** si hay alguno, ejecuta `python .claude/skills/subir/outputs_notebooks.py <notebooks>`.
  Si alguno tiene outputs, **no lo abras**: es un 🔴 y basta para pedir cambios.
- **Comprueba** que no entra nada de `CONTRIBUTING.md` §7 (datos, cachés, CSV de entregas, PDFs,
  `CLAUDE.local.md`) y que no se toca ningún fichero oficial (§9).
- **Si algo falla aquí,** esos ficheros no se abren ni entran en ningún diff. Pasa directamente al §5
  con «pedir cambios».

## 4. Revisión

- Lanza el agente `revisor` sobre `origin/main...HEAD` con el número de PR como contexto. Él repite el
  filtro de nombres antes de mirar contenido.
- Lee tú también el diff de lo importante y resume para quien revisa:
  - qué hace la PR (dos líneas);
  - los 🔴 (bloquean), los 🟡 (conviene cambiar) y los 💭 (opcionales), con fichero:línea;
  - los commits y su autoría: `git log --format="%h %an <%ae> %s" origin/main..HEAD`. Si algún cuerpo
    lleva `Co-Authored-By`, es un 🔴.

## 5. Veredicto (solo con su decisión)

Pregunta: ¿aprobar, pedir cambios o comentar? Escribe el texto con sus palabras, o un borrador que él
apruebe, sin atribuciones a Claude.
```
gh pr review <n> --approve --body-file <fichero>
gh pr review <n> --request-changes --body-file <fichero>
gh pr review <n> --comment --body-file <fichero>
```
El fichero temporal va fuera del repo.

## 6. Merge (solo si lo pide y hay al menos una aprobación de otra persona)

1. Comprueba con `gh pr view <n> --json reviewDecision,reviews,mergeable` que hay una aprobación y que
   no hay conflictos.
2. Mergea según la rama:
   - **Rama normal:** `gh pr merge <n> --squash --delete-branch`
   - **Rama `sync/*`:** `gh pr merge <n> --merge --delete-branch`. Con squash, git perdería la historia
     de `upstream`.

   `--delete-branch` borra la rama en GitHub y en local, y deja a quien revisa en `main`.
3. Actualiza con `git pull --ff-only origin main` y, si estaba trabajando en otra rama, vuelve a ella
   con `git switch <su rama>`.

## 7. Cierre

Una línea con lo hecho: aprobada, cambios pedidos o mergeada, con el enlace.
