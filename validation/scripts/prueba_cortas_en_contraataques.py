"""Prueba de `validation/partido/cortas_en_contraataques.py` con datos inventados. No lee ningún dato.

    python validation/scripts/prueba_cortas_en_contraataques.py

El script de verdad lee dos entregas del partido y el Smart Tagging, así que lo ejecuta una persona. Aquí se
prueba su núcleo, que es puro: `quitadas`, `posesiones`, `medir` y el texto de `lineas`.

Qué comprueba:

1. `quitadas` encuentra una posesión que pasa a `D` entera y no las que solo cambian en parte.
2. Solo mira dentro de los tramos evaluados: lo de fuera no cuenta.
3. `medir` cuenta bien las que solapan la ventana del contraataque y las que empiezan dentro de ella.
4. `medir` detecta un cambio que no va a `D` (no sería «cortas a `D`» sola).
5. El aviso salta con más de 2 en la ventana y no salta con 2, y el código de salida lo acompaña.
6. `ventana_contraataques` pide la ventana a `transiciones.push`: sale exactamente la de la capa de la entrega.

Imprime solo recuentos. Sale con código 1 si algo falla.
"""

import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "evaluation"))
sys.path.insert(0, os.path.join(ROOT, "validation", "partido"))
import cortas_en_contraataques as cec  # noqa: E402
from possession import transiciones  # noqa: E402
from possession.tracking import A, D, H, X  # noqa: E402

FALLOS = []


def comprobar(condicion, que):
    if not condicion:
        FALLOS.append(que)


def a_mano(partes):
    return np.concatenate([np.full(largo, etiqueta, dtype=np.int8) for etiqueta, largo in partes])


def prueba_quitadas():
    blocks = ((100, 900),)
    # Una posesión de A de 10 frames que pasa a D entera, y una de H que solo cambia a medias.
    antes = a_mano([(X, 100), (H, 300), (A, 10), (D, 200), (H, 100), (D, 90), (X, 100)])
    despues = antes.copy()
    despues[400:410] = D  # la de A, entera
    despues[710:730] = D  # solo una parte de la de H
    lista = cec.quitadas(antes, despues, blocks)
    comprobar(lista == [(400, 410)], "no encuentra solo la posesión que pasa a D entera")
    comprobar(cec.posesiones(antes, blocks) == 3, "cuenta mal las posesiones de antes")
    comprobar(cec.posesiones(despues, blocks) == 2, "cuenta mal las posesiones de después")
    return 3


def prueba_solo_en_los_tramos():
    blocks = ((100, 500),)
    # La misma posesión corta, pero fuera del tramo evaluado: no cuenta.
    antes = a_mano([(H, 100), (A, 10), (D, 390), (H, 10), (D, 90)])
    despues = antes.copy()
    despues[500:510] = D  # fuera del tramo
    comprobar(cec.quitadas(antes, despues, blocks) == [], "cuenta una posesión de fuera de los tramos")
    return 1


def prueba_medir():
    blocks = ((0, 1000),)
    antes = a_mano([(H, 300), (A, 10), (D, 100), (H, 200), (A, 10), (D, 380)])
    despues = antes.copy()
    despues[300:310] = D  # dentro de la ventana
    despues[610:620] = D  # fuera de la ventana
    ventana = np.zeros(1000, bool)
    ventana[250:400] = True
    res = cec.medir(antes, despues, blocks, ventana)
    comprobar(res["quitadas"] == 2, "medir: cuenta mal las quitadas")
    comprobar(res["en_ventana"] == 1, "medir: cuenta mal las que solapan la ventana")
    comprobar(res["empiezan_en_ventana"] == 1, "medir: cuenta mal las que empiezan en la ventana")
    comprobar(res["cambios_que_no_son_a_d"] == 0, "medir: ve un cambio que no es a D donde no lo hay")

    # Solapa la ventana pero no empieza dentro.
    ventana2 = np.zeros(1000, bool)
    ventana2[305:400] = True
    res2 = cec.medir(antes, despues, blocks, ventana2)
    comprobar(res2["en_ventana"] == 1 and res2["empiezan_en_ventana"] == 0,
              "medir: no distingue solapar de empezar dentro")

    # Un cambio que no va a D.
    otro = despues.copy()
    otro[700:710] = A
    res3 = cec.medir(antes, otro, blocks, ventana)
    comprobar(res3["cambios_que_no_son_a_d"] == 10, "medir: no detecta un cambio que no es a D")
    return 6


def prueba_aviso():
    blocks = ((0, 1000),)
    antes = a_mano([(H, 100), (A, 10), (H, 100), (A, 10), (H, 100), (A, 10), (H, 100), (A, 10), (D, 560)])
    ventana = np.ones(1000, bool)
    casos = []
    for cuantas, debe_avisar in ((2, False), (3, True)):
        despues = antes.copy()
        for k in range(cuantas):
            inicio = 100 + k * 110
            despues[inicio:inicio + 10] = D
        res = cec.medir(antes, despues, blocks, ventana)
        texto = "\n".join(cec.lineas(res, ["v8", "prueba"], 24))
        avisa = "PARA Y AVISA" in texto
        casos.append((res["en_ventana"] == cuantas, "el aviso: cuenta mal con {}".format(cuantas)))
        casos.append((avisa == debe_avisar, "el aviso {} con {} en la ventana".format(
            "no salta" if debe_avisar else "salta", cuantas)))
        casos.append((("cumplido" in texto) == (not debe_avisar),
                      "el texto de cumplido no cuadra con {}".format(cuantas)))
    comprobar(cec.TOPE_AVISO == 2, "el tope del aviso ya no es 2, el del criterio 5")
    for ok, que in casos:
        comprobar(ok, que)
    return len(casos) + 1


def prueba_ventana_es_la_de_la_capa():
    """La ventana sale de `transiciones.push`, así que es la de la capa de la entrega, no una copia."""
    n, fps = 2000, 25
    blocks = ((0, 2000),)
    fases = [(H, 100, 1000), (A, 1500, 1520)]
    score, _ = transiciones.push(n, blocks, fases, fps, neutral=False)
    esperada = (score[:, H] > 0) | (score[:, A] > 0)
    # La primera fase se corta a los 5 s (125 frames); la segunda acaba antes del tope.
    comprobar(int(esperada[100:1000].sum()) == transiciones.CAP_S * fps,
              "la ventana de una fase larga no se corta a CAP_S segundos")
    comprobar(int(esperada[1500:1520].sum()) == 20, "la ventana de una fase corta no es la fase entera")
    comprobar(int(esperada.sum()) == transiciones.CAP_S * fps + 20, "la ventana tiene frames de más")
    return 3


def main():
    pruebas = [
        ("quitadas y posesiones", prueba_quitadas),
        ("solo dentro de los tramos evaluados", prueba_solo_en_los_tramos),
        ("medir: ventana, inicio y cambios que no son a D", prueba_medir),
        ("el aviso de más de 2", prueba_aviso),
        ("la ventana es la de transiciones.push", prueba_ventana_es_la_de_la_capa),
    ]
    for nombre, prueba in pruebas:
        antes = len(FALLOS)
        casos = prueba()
        print("{}: {} casos, {}".format(nombre, casos, "OK" if len(FALLOS) == antes else
                                        "{} FALLOS".format(len(FALLOS) - antes)))
    if FALLOS:
        print("\nFALLA:")
        for que in sorted(set(FALLOS)):
            print("  - {} ({} veces)".format(que, FALLOS.count(que)))
        sys.exit(1)
    print("\nTodo OK.")


if __name__ == "__main__":
    main()
