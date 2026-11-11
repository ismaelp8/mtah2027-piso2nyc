---
name: actualizar
description: Pone al día la copia local con GitHub. Trae lo último de main a la rama actual o, si la PR de esa rama ya se mergeó, vuelve a main, lo actualiza y borra la rama local. Úsala cuando alguien diga "actualiza", "trae lo último", "ya me han aprobado/mergeado la PR" o "mi rama está desactualizada".
---

# Actualizar la copia local

Quien te habla puede no saber git: explica cada paso en una frase sencilla. Nada de `reset --hard`,
`rebase` sobre ramas ya subidas, `push --force` ni descartar cambios sin un sí explícito.

1. **Estado:**
   ```
   git fetch origin --prune
   git branch --show-current
   git status --short
   ```
2. **Si está en `main`:** `git pull --ff-only origin main`. Si falla, el `main` local tiene commits que
   no están en GitHub. Para y explícalo: lo normal es moverlos a una rama con
   `git switch -c <tipo/descripcion>` y abrir PR.
3. **Si está en una rama, mira si su PR ya se mergeó:**
   `gh pr view --json number,state,mergedAt,url`.
   - **Mergeada** (`state` = `MERGED`):
     1. si hay cambios sin commitear, pregunta antes qué hacer con ellos;
     2. `git switch main` y `git pull --ff-only origin main`;
     3. borra la rama local con `git branch -d <rama>`. Si `-d` se niega (pasa con los merges con squash),
        comprueba con `gh pr view` que está mergeada y usa `git branch -D <rama>` **solo con su sí**;
     4. dile que puede empezar otra tarea con `/empezar`.
   - **Abierta o sin PR:** trae `main` a la rama.
     1. Si hay cambios sin commitear, propón primero un commit con su autoría (como en `/subir` §4) o
        dejarlo para después.
     2. Ejecuta `git merge origin/main`.
     3. Si hay conflictos, enséñale qué ficheros chocan (`git status --short`) y resuélvelos con él,
        fichero a fichero. En un fichero oficial gana `origin/main`. Antes de abrir un notebook en
        conflicto, comprueba sus outputs con `.claude/skills/subir/outputs_notebooks.py`.
     4. Si la rama ya estaba subida, el merge se sube con `git push`, después de preguntar.
4. **Cierre:** dile en una línea dónde está y si hay algo pendiente.
