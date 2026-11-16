"""Prueba de `temporal.cortas_a_d` y `temporal.decode_cortas_a_d` (idea 1.3). No lee ningún dato.

    python validation/scripts/prueba_cortas_a_d.py

Qué comprueba:

1. **La misma lógica que S9.** Con `D` permitido en todas partes, `cortas_a_d` por tramos da exactamente lo
   mismo que la variante «a D» de `validation/investigacion_1116/paquete_control.py`: las candidatas de
   `cambio_antes_de_parada.candidatas` puestas a `D`. Es lo que hace reproducible la columna «cortas a `D`».
2. **Que la referencia no ha cambiado.** El AST de `candidatas` en el fichero de la investigación tiene que
   seguir siendo el de la copia que usa esta prueba. Si alguien la cambia, esto falla y hay que repetir la
   medida, no tocar la copia a la ligera.
3. **`allowed` manda.** Una candidata con `D` prohibido en alguno de sus frames se queda como está, y ese es
   el único caso en que `cortas_a_d` se separa de la referencia.
4. **Los bordes, a mano:** la primera racha del tramo y la última nunca son candidatas; el corte es estricto
   (`corte` frames no entra, `corte - 1` sí); no vale si la racha anterior es `D` ni si la siguiente no es `D`.
5. **Una sola pasada.** Convertir una candidata puede crear otra; como la referencia, no se encadena.
6. **Solo añade `D`:** ningún frame cambia de equipo, ningún `D` deja de serlo y las posesiones no suben.
7. **`decode_cortas_a_d`:** da lo mismo con los tramos en lista, tupla o generador; escribe `X` fuera de los
   tramos; es determinista; no toca los arrays que recibe; con `corte` 1 es exactamente `decode`; y los
   `params` llegan al Viterbi.
8. **El corte de por defecto es el de la regla (125 frames) y se aplica.** Con evidencia forzada, una racha
   de 100 frames entra con 125 y no con 75. Con evidencia al azar las rachas no llegan a 125, así que sin
   esto el valor del corte no se ejercitaría (lo encontró un sabotaje).
9. **Las erratas dan error:** un corte de 0 o negativo.

Imprime solo recuentos. Sale con código 1 si algo falla.
"""

import ast
import copy
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from possession import temporal  # noqa: E402
from possession.tracking import A, D, H, N_STATES, X  # noqa: E402

SEMILLA = 20261116
CORTE = temporal.CORTE_CORTAS
REFERENCIA = os.path.join(ROOT, "validation", "investigacion_1116", "cambio_antes_de_parada.py")
FALLOS = []


def comprobar(condicion, que):
    if not condicion:
        FALLOS.append(que)


# -- la referencia de S9, copiada palabra por palabra de cambio_antes_de_parada.py ---------------------
# No se importa de allí porque ese fichero carga la DFL y SkillCorner al importarse, y esta prueba no lee
# datos. La comprobación 2 verifica que la copia sigue siendo igual a la original.
def referencia_candidatas(pred, blocks, corte):
    out = []
    for a, b in blocks:
        r = temporal.runs(pred[a:b])
        for k in range(1, len(r) - 1):
            etiqueta, i, j = r[k]
            if etiqueta in (H, A) and r[k + 1][0] == D and r[k - 1][0] in (H, A) and r[k - 1][0] != etiqueta \
                    and j - i < corte:
                out.append((a + i, a + j, r[k - 1][0]))
    return out


def referencia_aplicada(codes, blocks, corte):
    """La variante «a D» de S9: las candidatas puestas a `D`, sin mirar `allowed`."""
    out = np.array(codes, copy=True)
    for i, j, _ in referencia_candidatas(codes, blocks, corte):
        out[i:j] = D
    return out


def mio_por_tramos(codes, allowed, blocks, corte):
    """`cortas_a_d` tramo a tramo, como lo llama `decode_cortas_a_d`."""
    out = np.array(codes, copy=True)
    for a, b in blocks:
        out[a:b] = temporal.cortas_a_d(out[a:b], allowed[a:b], corte)
    return out


def logica(ruta_o_fuente, nombre, es_fuente=False):
    """AST de una función, sin su nombre ni su docstring: compara lógica, no formato ni comentarios."""
    if es_fuente:
        fuente = ruta_o_fuente
    else:
        with open(ruta_o_fuente, encoding="utf-8") as handle:
            fuente = handle.read()
    for nodo in ast.parse(fuente).body:
        if isinstance(nodo, ast.FunctionDef) and nodo.name == nombre:
            nodo = copy.deepcopy(nodo)
            nodo.name = "f"
            nodo.decorator_list = []
            cuerpo = nodo.body
            if cuerpo and isinstance(cuerpo[0], ast.Expr) and isinstance(cuerpo[0].value, ast.Constant) \
                    and isinstance(cuerpo[0].value.value, str):
                nodo.body = cuerpo[1:]
            return ast.dump(nodo)
    return None


# -- datos inventados ----------------------------------------------------------------------------------
def etiquetas(rng, n, largo_max=200):
    """Etiquetas con rachas de largo variable y sin dos rachas iguales seguidas."""
    out = np.empty(n, dtype=np.int8)
    t, anterior = 0, -1
    while t < n:
        opciones = [s for s in (H, A, D) if s != anterior]
        s = int(opciones[rng.integers(len(opciones))])
        largo = int(rng.integers(1, largo_max))
        out[t:t + largo] = s
        anterior, t = s, t + largo
    return out


def tramos(n):
    """Dos tramos, como las dos partes, con frames fuera por delante, en medio y por detrás."""
    return ((n // 10, n // 2 - n // 10), (n // 2 + n // 10, n - n // 10))


def evidencia(rng, n):
    """(score, allowed) inventados, finitos en todo y con algún estado permitido en cada frame."""
    score = rng.normal(0.0, 10.0, size=(n, N_STATES))
    allowed = rng.random((n, N_STATES)) > 0.15
    allowed[~allowed.any(axis=1), :] = True
    return score, allowed


def a_mano(partes):
    """Etiquetas a partir de [(etiqueta, largo)]."""
    return np.concatenate([np.full(largo, etiqueta, dtype=np.int8) for etiqueta, largo in partes])


def vivas(codes):
    """Cuántas rachas de `H` o `A` hay."""
    return sum(1 for etiqueta, _, _ in temporal.runs(codes) if etiqueta in (H, A))


def forzado(partes, margen=400):
    """(score, allowed, blocks, esperado): evidencia que obliga al Viterbi a dar exactamente `partes`.

    Con ±1000 de puntuación por frame, desviarse cuesta 2.000 y ahorra como mucho un coste de cambio de
    25, así que el camino de más puntuación es el pedido. Hace falta para ejercitar el valor del corte: con
    evidencia al azar las rachas salen de 1 a 20 frames y nunca llegan a los 125.
    """
    dentro = a_mano(partes)
    n = len(dentro) + 2 * margen
    score = np.full((n, N_STATES), -1000.0)
    blocks = ((margen, margen + len(dentro)),)
    for t, etiqueta in enumerate(dentro):
        score[margen + t, etiqueta] = 1000.0
    return score, np.ones((n, N_STATES), bool), blocks, dentro


# -- 1 y 3. frente a la referencia ---------------------------------------------------------------------
def prueba_frente_a_la_referencia(rng, casos=400):
    distintos_con_prohibido = 0
    for _ in range(casos):
        n = int(rng.integers(600, 1800))
        codes, blocks = etiquetas(rng, n), tramos(n)
        todo = np.ones((n, N_STATES), bool)
        comprobar(np.array_equal(mio_por_tramos(codes, todo, blocks, CORTE),
                                 referencia_aplicada(codes, blocks, CORTE)),
                  "no da lo mismo que la referencia de S9 con D permitido")
        # Con `D` prohibido en algún sitio solo se puede separar dejando candidatas sin convertir.
        allowed = todo.copy()
        allowed[rng.random(n) < 0.02, D] = False
        allowed[~allowed.any(axis=1), :] = True
        mio = mio_por_tramos(codes, allowed, blocks, CORTE)
        ref = referencia_aplicada(codes, blocks, CORTE)
        # `codes` es inventado y `allowed` también, así que las etiquetas de partida pueden estar prohibidas:
        # lo que se exige es que no se escriba un `D` prohibido nuevo.
        comprobar(np.all(allowed[mio != codes, D]), "ha puesto un D donde está prohibido")
        distinto = mio != ref
        if distinto.any():
            distintos_con_prohibido += 1
            comprobar(np.array_equal(mio[distinto], codes[distinto]),
                      "donde se separa de la referencia no deja las etiquetas de main")
            comprobar(np.all(ref[distinto] == D), "se separa de la referencia en algo que no es D")
    comprobar(distintos_con_prohibido > 0,
              "con D prohibido nunca se ha separado de la referencia: no se prueba nada")
    return casos


def prueba_referencia_sin_cambios(_rng):
    original = logica(REFERENCIA, "candidatas")
    comprobar(original is not None, "no se encuentra `candidatas` en {}".format(REFERENCIA))
    with open(os.path.abspath(__file__), encoding="utf-8") as handle:
        copia = logica(handle.read(), "referencia_candidatas", es_fuente=True)
    comprobar(original == copia,
              "`candidatas` de la investigación ya no es igual a la copia de esta prueba: si la lógica de S9 "
              "ha cambiado, hay que repetir la medida")
    return 1


# -- 4, 5 y 6. casos a mano y propiedades --------------------------------------------------------------
def prueba_bordes(_rng):
    casos = []

    def todo(n):
        return np.ones((n, N_STATES), bool)

    # Entra: H larga, A corta, D. La A pasa a D.
    codes = a_mano([(H, 300), (A, 10), (D, 300)])
    salida = temporal.cortas_a_d(codes, todo(len(codes)), CORTE)
    casos.append((np.array_equal(salida, a_mano([(H, 300), (D, 310)])), "el caso que entra no ha entrado"))

    # El corte es estricto: `corte` frames no entra, `corte - 1` sí.
    justo = a_mano([(H, 300), (A, CORTE), (D, 300)])
    casos.append((np.array_equal(temporal.cortas_a_d(justo, todo(len(justo)), CORTE), justo),
                  "una racha de `corte` frames ha entrado"))
    uno_menos = a_mano([(H, 300), (A, CORTE - 1), (D, 300)])
    casos.append((np.all(temporal.cortas_a_d(uno_menos, todo(len(uno_menos)), CORTE)[300:] == D),
                  "una racha de `corte - 1` frames no ha entrado"))

    # La primera racha del tramo no es candidata (le falta la de antes), aunque sea corta y la siga un D.
    primera = a_mano([(A, 10), (D, 300)])
    casos.append((np.array_equal(temporal.cortas_a_d(primera, todo(len(primera)), CORTE), primera),
                  "la primera racha del tramo ha entrado"))

    # La última tampoco (le falta el D de después).
    ultima = a_mano([(D, 300), (H, 300), (A, 10)])
    casos.append((np.array_equal(temporal.cortas_a_d(ultima, todo(len(ultima)), CORTE), ultima),
                  "la última racha del tramo ha entrado"))

    # No vale si la de antes es `D` (no es un cambio directo desde el otro equipo).
    desde_d = a_mano([(H, 100), (D, 300), (A, 10), (D, 300)])
    casos.append((np.array_equal(temporal.cortas_a_d(desde_d, todo(len(desde_d)), CORTE), desde_d),
                  "una racha que viene de D ha entrado"))

    # No vale si la siguiente no es `D`.
    sin_d = a_mano([(H, 300), (A, 10), (H, 300), (D, 50)])
    casos.append((np.array_equal(temporal.cortas_a_d(sin_d, todo(len(sin_d)), CORTE), sin_d),
                  "una racha que no acaba en D ha entrado"))

    # `allowed` manda: con `D` prohibido en un solo frame de la candidata, no entra.
    codes = a_mano([(H, 300), (A, 10), (D, 300)])
    allowed = todo(len(codes))
    allowed[305, D] = False
    casos.append((np.array_equal(temporal.cortas_a_d(codes, allowed, CORTE), codes),
                  "ha entrado con D prohibido en un frame"))

    # Una sola pasada: A larga, H corta, A corta, D. Entra la última A; la H queda pegada al D sin encadenarse.
    cascada = a_mano([(A, 300), (H, 10), (A, 10), (D, 300)])
    salida = temporal.cortas_a_d(cascada, todo(len(cascada)), CORTE)
    casos.append((np.array_equal(salida, a_mano([(A, 300), (H, 10), (D, 310)])),
                  "la pasada se ha encadenado: no es una sola"))

    # No modifica lo que recibe.
    codes = a_mano([(H, 300), (A, 10), (D, 300)])
    antes = codes.copy()
    temporal.cortas_a_d(codes, todo(len(codes)), CORTE)
    casos.append((np.array_equal(codes, antes), "ha modificado el array que recibe"))

    for ok, que in casos:
        comprobar(ok, que)
    return len(casos)


def prueba_solo_anade_d(rng, casos=300):
    for _ in range(casos):
        n = int(rng.integers(600, 1500))
        codes, blocks = etiquetas(rng, n), tramos(n)
        salida = mio_por_tramos(codes, np.ones((n, N_STATES), bool), blocks, CORTE)
        cambia = salida != codes
        comprobar(np.all(salida[cambia] == D), "algo ha cambiado a algo que no es D")
        comprobar(np.all(np.isin(codes[cambia], (H, A))), "ha cambiado un frame que no era de un equipo")
        comprobar(np.all(salida[codes == D] == D), "ha tocado un D")
        for a, b in blocks:
            comprobar(vivas(salida[a:b]) <= vivas(codes[a:b]), "han subido las posesiones de un tramo")
    return casos


# -- 7 y 8. el decodificador ---------------------------------------------------------------------------
def prueba_decodificador(rng, casos=40):
    for _ in range(casos):
        n = int(rng.integers(600, 1200))
        score, allowed = evidencia(rng, n)
        blocks = tramos(n)
        de_lista = temporal.decode_cortas_a_d(score, allowed, list(blocks))
        comprobar(np.array_equal(temporal.decode_cortas_a_d(score, allowed, tuple(blocks)), de_lista),
                  "los tramos en tupla dan algo distinto")
        comprobar(np.array_equal(temporal.decode_cortas_a_d(score, allowed, (b for b in blocks)), de_lista),
                  "los tramos en un generador dan algo distinto")
        comprobar(np.array_equal(temporal.decode_cortas_a_d(score, allowed, blocks), de_lista),
                  "no es determinista")
        fuera = np.ones(n, bool)
        for a, b in blocks:
            fuera[a:b] = False
        comprobar(np.all(de_lista[fuera] == X), "no escribe X fuera de los tramos")
        # Dentro de los tramos, aquí sí se puede exigir todo: `decode` respeta `allowed` y `cortas_a_d`
        # solo escribe un `D` permitido, así que ninguna etiqueta puede estar prohibida.
        dentro = np.flatnonzero(~fuera)
        comprobar(np.all(allowed[dentro, de_lista[dentro]]),
                  "el decodificador deja una etiqueta prohibida en un tramo")
        # Con corte 1 ninguna racha mide menos: es exactamente `decode`.
        comprobar(np.array_equal(temporal.decode_cortas_a_d(score, allowed, blocks, corte=1),
                                 temporal.decode(score, allowed, blocks)),
                  "con corte 1 no es igual que decode")
        # Es el Viterbi de `decode` y después la regla, tramo a tramo.
        base = temporal.decode(score, allowed, blocks)
        comprobar(np.array_equal(de_lista, mio_por_tramos(base, allowed, blocks, CORTE)),
                  "no es decode y después cortas_a_d")
        # Los costes llegan al Viterbi: con otros `params` es el Viterbi de esos params y después la regla.
        otros = {"switch": 0.0, "to_dead": 0.0, "from_dead": 0.0}
        con_params = temporal.decode_cortas_a_d(score, allowed, blocks, params=otros)
        base_params = temporal.decode(score, allowed, blocks, params=otros)
        comprobar(np.array_equal(con_params, mio_por_tramos(base_params, allowed, blocks, CORTE)),
                  "no pasa los params al Viterbi")
        # No toca lo que recibe.
        s0, a0 = score.copy(), allowed.copy()
        temporal.decode_cortas_a_d(score, allowed, blocks)
        comprobar(np.array_equal(score, s0) and np.array_equal(allowed, a0),
                  "el decodificador ha modificado la evidencia")
    return casos


def prueba_corte_por_defecto(_rng):
    """El corte de por defecto es el de la regla (125 frames) y se aplica de verdad.

    Con evidencia al azar todas las rachas son mucho más cortas que 125, así que el valor del corte no se
    ejercita; aquí se fuerza una racha de 100 frames, que entra con 125 y no con 75.
    """
    casos = []
    score, allowed, blocks, dentro = forzado([(H, 300), (A, 100), (D, 300)])
    a, b = blocks[0]
    casos.append((np.array_equal(temporal.decode(score, allowed, blocks)[a:b], dentro),
                  "la evidencia forzada no da la secuencia pedida: la prueba no mide lo que cree"))
    esperado = a_mano([(H, 300), (D, 400)])
    casos.append((np.array_equal(temporal.decode_cortas_a_d(score, allowed, blocks)[a:b], esperado),
                  "con el corte de por defecto no entra una racha de 100 frames"))
    casos.append((np.array_equal(temporal.decode_cortas_a_d(score, allowed, blocks, corte=CORTE)[a:b],
                                 esperado),
                  "el corte de por defecto no es CORTE_CORTAS"))
    casos.append((np.array_equal(temporal.decode_cortas_a_d(score, allowed, blocks, corte=75)[a:b], dentro),
                  "con un corte de 75 ha entrado una racha de 100 frames"))
    # Con una candidata que seguro dispara, los tramos en un generador tienen que dar lo mismo.
    de_lista = temporal.decode_cortas_a_d(score, allowed, list(blocks))
    casos.append((np.array_equal(temporal.decode_cortas_a_d(score, allowed, (t for t in blocks)), de_lista),
                  "con los tramos en un generador no aplica la regla"))
    casos.append((not np.array_equal(de_lista, temporal.decode(score, allowed, blocks)),
                  "la regla no cambia nada en el caso forzado: no se prueba nada"))
    for ok, que in casos:
        comprobar(ok, que)
    return len(casos)


def prueba_erratas(rng):
    n = 600
    score, allowed = evidencia(rng, n)
    blocks = tramos(n)
    casos = [("corte 0", 0), ("corte negativo", -5)]
    for que, corte in casos:
        try:
            temporal.decode_cortas_a_d(score, allowed, blocks, corte=corte)
            FALLOS.append("errata sin error: " + que)
        except ValueError:
            pass
    return len(casos)


def main():
    rng = np.random.default_rng(SEMILLA)
    pruebas = [
        ("la misma lógica que la referencia de S9 (y allowed manda)", prueba_frente_a_la_referencia),
        ("la referencia de la investigación no ha cambiado", prueba_referencia_sin_cambios),
        ("bordes y casos a mano", prueba_bordes),
        ("solo añade D, no sube posesiones", prueba_solo_anade_d),
        ("decode_cortas_a_d: tramos, X, determinismo, corte 1", prueba_decodificador),
        ("el corte de por defecto, con evidencia forzada", prueba_corte_por_defecto),
        ("erratas", prueba_erratas),
    ]
    for nombre, prueba in pruebas:
        antes = len(FALLOS)
        casos = prueba(rng)
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
