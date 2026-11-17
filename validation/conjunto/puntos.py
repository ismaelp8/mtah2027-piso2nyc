"""Puntos de control de un entrenamiento del modelo conjunto (K7 y K8), para reanudarlo si se corta.

No se ejecuta solo. Lo usan `entrenar_k7.py` y `entrenar_k8.py`. `entrenar.py` (K2) no cambia.

Un punto guarda todo lo que hace falta para que reanudar dé los mismos pesos, bit a bit, que no haberse parado: los
pesos, el optimizador, el plan de la tasa, el paso, el estado del generador de numpy (los trozos), el del generador de
torch de los aumentos y el global de torch (el abandono y, en la GPU, el de CUDA). Además guarda con qué se lanzó
(etiqueta, pliegue, semilla y configuración): un punto de otro entrenamiento no se carga. La comprobación está en
`comprobar_puntos.py`.

Los puntos van fuera del repo, en `conjunto_cache/puntos/`, y se borran al guardar los pesos finales.
"""

import torch

import cj_comun as cj


def ruta(etiqueta, pliegue):
    return cj.carpeta() / "puntos" / "{}_{}.pt".format(etiqueta, pliegue)


def guardar(destino, firma, paso, modelo, opt, plan, rng, gen):
    destino.parent.mkdir(parents=True, exist_ok=True)
    estado = {"firma": firma, "paso": paso, "modelo": modelo.state_dict(), "opt": opt.state_dict(),
              "plan": plan.state_dict(), "numpy": rng.bit_generator.state, "gen": gen.get_state(),
              "torch": torch.get_rng_state(),
              "cuda": torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None}
    temporal = destino.with_suffix(".tmp")
    torch.save(estado, temporal)
    temporal.replace(destino)  # o el punto entero, o el anterior: nunca medio escrito


def cargar(origen, firma, modelo, opt, plan, rng, gen):
    """Restaura el entrenamiento y devuelve el último paso hecho. Se niega si el punto es de otro entrenamiento."""
    estado = torch.load(origen, map_location="cpu", weights_only=False)
    if estado["firma"] != firma:
        raise ValueError("el punto de control {} es de otro entrenamiento: {} frente a {}".format(
            origen.name, estado["firma"], firma))
    modelo.load_state_dict(estado["modelo"])
    opt.load_state_dict(estado["opt"])
    plan.load_state_dict(estado["plan"])
    rng.bit_generator.state = estado["numpy"]
    gen.set_state(estado["gen"])
    torch.set_rng_state(estado["torch"])
    if estado["cuda"] is not None and torch.cuda.is_available():
        torch.cuda.set_rng_state_all(estado["cuda"])
    return int(estado["paso"])


def borrar(destino):
    if destino.is_file():
        destino.unlink()
