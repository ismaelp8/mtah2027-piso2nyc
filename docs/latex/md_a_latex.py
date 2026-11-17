"""Pasa docs/documento_tecnico.md a LaTeX y, si se pide, compila el PDF.

El .md es la fuente: se edita allí y este script regenera docs/latex/documento_tecnico.tex con la
plantilla docs/latex/plantilla.tex. Así el .md, el .tex y el PDF dicen siempre lo mismo.

Uso (desde la raíz del repo; vale python3 3.10 o más, sin dependencias):

    python3 docs/latex/md_a_latex.py              # regenera el .tex
    python3 docs/latex/md_a_latex.py --pdf        # y compila docs/latex/build/<equipo>.pdf
    python3 docs/latex/md_a_latex.py --comprobar  # falla si el .tex no está al día con el .md

Entiende el Markdown que usa el documento: títulos #, ## y ###, párrafos, **negrita**, *cursiva*,
`código`, listas con - y 1. (anidadas), citas con >, tablas con |, bloques ``` y enlaces sueltos.
Las etiquetas [medido], [inferencia], [sin verificar]... salen en color, y las [PENDIENTE: ...], en
rojo, para que ninguna llegue a la entrega sin querer.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent.parent
MD = RAIZ / "docs" / "documento_tecnico.md"
PLANTILLA = AQUI / "plantilla.tex"
TEX = AQUI / "documento_tecnico.tex"
BUILD = AQUI / "build"

CONCURSO = "More than a Hack 2027 · Frame-level Ball Possession"
FECHA = "17 de noviembre de 2026"

CABECERA = (
    "% GENERADO por docs/latex/md_a_latex.py a partir de docs/documento_tecnico.md.\n"
    "% No lo edites a mano: cambia el .md (o docs/latex/plantilla.tex) y regenera.\n"
)

# Etiquetas de evidencia que el documento pone entre corchetes.
ETIQUETAS = ("medido", "inferencia", "sin verificar", "descriptivo", "lectura con poca evidencia")


# ------------------------------------------------------------------------------------------------
# Texto en línea
# ------------------------------------------------------------------------------------------------

_ESPECIALES = {
    "\\": r"\textbackslash{}",
    "{": r"\{",
    "}": r"\}",
    "#": r"\#",
    "$": r"\$",
    "%": r"\%",
    "&": r"\&",
    "_": r"\_",
    "^": r"\textasciicircum{}",
    "~": r"\textasciitilde{}",
}


def escapar(texto: str) -> str:
    return "".join(_ESPECIALES.get(c, c) for c in texto)


def codigo(texto: str) -> str:
    """Código en línea: escapa y deja partir la línea en / _ . = - y en los hashes largos."""
    trozos = re.split(r"([0-9a-fA-F]{16,})", texto)
    salida = []
    for i, trozo in enumerate(trozos):
        if i % 2:
            salida.append(r"\seqsplit{" + trozo + "}")
            continue
        for c in trozo:
            salida.append(_ESPECIALES.get(c, c))
            if c in "/_.=-":
                salida.append(r"\allowbreak{}")
    return r"\code{" + "".join(salida) + "}"


class EnLinea:
    """Convierte una línea de Markdown a LaTeX. Conoce las secciones que existen para enlazar los §."""

    def __init__(self, secciones: set[str]):
        self.secciones = secciones

    def __call__(self, texto: str) -> str:
        guardados: list[str] = []

        def guardar(latex: str) -> str:
            guardados.append(latex)
            return f"\x00{len(guardados) - 1}\x01"

        # 1. Lo que no se escapa: código, enlaces y DOI.
        texto = re.sub(r"`([^`]+)`", lambda m: guardar(codigo(m.group(1))), texto)
        texto = re.sub(
            r"\[([^\]]+)\]\((https?://[^)\s]+)\)",
            lambda m: guardar(r"\href{" + m.group(2) + "}{" + escapar(m.group(1)) + "}"),
            texto,
        )
        texto = re.sub(
            r"https?://[^\s<>()]+[^\s<>().,;:]",
            lambda m: guardar(r"\url{" + m.group(0) + "}"),
            texto,
        )
        texto = re.sub(
            r"doi:(10\.[^\s,;]+[^\s.,;])",
            lambda m: guardar(
                r"\href{https://doi.org/" + m.group(1) + r"}{\nolinkurl{doi:" + m.group(1) + "}}"
            ),
            texto,
        )

        # 2. El resto se escapa.
        texto = escapar(texto)

        # 3. Formato.
        texto = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", texto)
        texto = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"\\emph{\1}", texto)

        # 4. Etiquetas entre corchetes.
        def etiqueta(m: re.Match) -> str:
            dentro = m.group(1)
            if dentro.startswith("PENDIENTE"):
                return r"\pendiente{" + dentro + "}"
            if dentro.lower().startswith(ETIQUETAS):
                return r"\etiqueta{" + dentro + "}"
            return m.group(0)

        texto = re.sub(r"\[([^\[\]]+)\]", etiqueta, texto)

        # 5. Tipografía: espacio fino e irrompible antes de %; los § de nuestras secciones, enlazados.
        texto = texto.replace(r" \%", r"~\%")

        def seccion(m: re.Match) -> str:
            numero = m.group(1)
            # «`CONTRIBUTING.md` §7» habla de otro documento: no se enlaza.
            if numero not in self.secciones or m.group(0).startswith("\x01"):
                return m.group(0)
            return r"\hyperref[sec:" + numero + r"]{\S" + numero + "}"

        texto = re.sub(r"(?:\x01 )?§(\d+(?:\.\d+)?)", seccion, texto)

        # 6. Se recupera lo guardado.
        return re.sub(r"\x00(\d+)\x01", lambda m: guardados[int(m.group(1))], texto)


# ------------------------------------------------------------------------------------------------
# Bloques
# ------------------------------------------------------------------------------------------------

RE_TITULO = re.compile(r"(#{1,6})\s+(.*)")
RE_VINETA = re.compile(r"[-*]\s+(.*)")
RE_NUMERO = re.compile(r"(\d{1,2})\.\s+(.*)")


def sangria(linea: str) -> int:
    return len(linea) - len(linea.lstrip(" "))


def empieza_bloque(linea: str, dentro_de_parrafo: bool) -> bool:
    if linea.startswith(("```", "|", ">")) or RE_TITULO.match(linea) or RE_VINETA.match(linea):
        return True
    m = RE_NUMERO.match(linea)
    # Como en CommonMark: una lista numerada solo corta un párrafo si empieza en 1.
    return bool(m) and (not dentro_de_parrafo or m.group(1) == "1")


def leer_bloques(lineas: list[str]) -> list[tuple]:
    bloques: list[tuple] = []
    i, n = 0, len(lineas)
    while i < n:
        linea = lineas[i]
        if not linea.strip():
            i += 1
            continue
        if linea.startswith("```"):
            j = i + 1
            while j < n and not lineas[j].startswith("```"):
                j += 1
            bloques.append(("codigo", lineas[i + 1 : j]))
            i = j + 1
            continue
        m = RE_TITULO.match(linea)
        if m:
            bloques.append(("titulo", len(m.group(1)), m.group(2).strip()))
            i += 1
            continue
        if linea.startswith("|"):
            j = i
            while j < n and lineas[j].startswith("|"):
                j += 1
            bloques.append(("tabla", lineas[i:j]))
            i = j
            continue
        if linea.startswith(">"):
            j = i
            while j < n and lineas[j].startswith(">"):
                j += 1
            dentro = [re.sub(r"^> ?", "", l) for l in lineas[i:j]]
            bloques.append(("cita", leer_bloques(dentro)))
            i = j
            continue
        if RE_VINETA.match(linea) or RE_NUMERO.match(linea):
            bloque, i = leer_lista(lineas, i)
            bloques.append(bloque)
            continue
        j = i + 1
        while j < n and lineas[j].strip() and not empieza_bloque(lineas[j], True):
            j += 1
        bloques.append(("parrafo", " ".join(l.strip() for l in lineas[i:j])))
        i = j
    return bloques


def leer_lista(lineas: list[str], i: int) -> tuple[tuple, int]:
    numerada = bool(RE_NUMERO.match(lineas[i]))
    patron = RE_NUMERO if numerada else RE_VINETA
    n = len(lineas)
    elementos = []
    while i < n:
        m = patron.match(lineas[i])
        if not m:
            break
        marca = len(lineas[i]) - len(m.group(m.lastindex))  # ancho de «- » o «1. »
        contenido = [m.group(m.lastindex)]
        i += 1
        siguiente_es_elemento = False
        while i < n:
            linea = lineas[i]
            if not linea.strip():
                k = i
                while k < n and not lineas[k].strip():
                    k += 1
                if k < n and sangria(lineas[k]) >= marca:
                    contenido.extend([""] * (k - i))
                    i = k
                    continue
                siguiente_es_elemento = k < n and bool(patron.match(lineas[k]))
                i = k
                break
            if sangria(linea) > 0:
                contenido.append(linea[marca:] if sangria(linea) >= marca else linea.lstrip())
                i += 1
                continue
            if patron.match(linea) or empieza_bloque(linea, True):
                break
            contenido.append(linea)  # continuación perezosa del párrafo
            i += 1
        elementos.append(leer_bloques(contenido))
        if i < n and not patron.match(lineas[i]):
            break
        if siguiente_es_elemento:
            continue
    return ("lista", numerada, elementos), i


# ------------------------------------------------------------------------------------------------
# Salida
# ------------------------------------------------------------------------------------------------


def celdas(fila: str) -> list[str]:
    fila = fila.strip()
    if fila.startswith("|"):
        fila = fila[1:]
    if fila.endswith("|") and not fila.endswith("\\|"):
        fila = fila[:-1]
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", fila)]


def largo_visible(celda: str) -> int:
    return len(re.sub(r"[`*]", "", celda))


class Escritor:
    def __init__(self, secciones: set[str]):
        self.en_linea = EnLinea(secciones)
        self.numero = [-1, 0]  # sección y subsección, para comprobar la numeración del .md

    def bloques(self, bloques: list[tuple]) -> str:
        return "\n".join(self.bloque(b) for b in bloques)

    def bloque(self, b: tuple) -> str:
        tipo = b[0]
        if tipo == "parrafo":
            return self.en_linea(b[1]) + "\n"
        if tipo == "titulo":
            return self.titulo(b[1], b[2])
        if tipo == "lista":
            entorno = "enumerate" if b[1] else "itemize"
            items = []
            for elemento in b[2]:
                cuerpo = self.bloques(elemento).strip()
                items.append(r"  \item " + cuerpo.replace("\n\n\n", "\n\n"))
            return "\\begin{" + entorno + "}\n" + "\n".join(items) + "\n\\end{" + entorno + "}\n"
        if tipo == "cita":
            return "\\begin{nota}\n" + self.bloques(b[1]).strip() + "\n\\end{nota}\n"
        if tipo == "codigo":
            return (
                "\\begin{bloquecodigo}\n\\begin{Verbatim}[breaklines,fontsize=\\small]\n"
                + "\n".join(b[1])
                + "\n\\end{Verbatim}\n\\end{bloquecodigo}\n"
            )
        if tipo == "tabla":
            return self.tabla(b[1])
        raise ValueError(f"bloque desconocido: {tipo}")

    def titulo(self, nivel: int, texto: str) -> str:
        if nivel not in (2, 3):
            raise SystemExit(f"Solo se admiten títulos ## y ### dentro del documento: «{texto}»")
        m = re.match(r"(\d+(?:\.\d+)?)\.?\s+(.*)", texto)
        if not m:
            raise SystemExit(f"Al título le falta el número de sección: «{texto}»")
        numero, nombre = m.groups()
        if nivel == 2:
            self.numero = [self.numero[0] + 1, 0]
            esperado = str(self.numero[0])
            orden = "section"
        else:
            self.numero[1] += 1
            esperado = f"{self.numero[0]}.{self.numero[1]}"
            orden = "subsection"
        if numero != esperado:
            raise SystemExit(
                f"La numeración del .md salta: «{texto}» debería ser {esperado}. "
                "LaTeX numera solo; corrige el .md."
            )
        latex = self.en_linea(nombre)
        if "\\" in latex:
            latex = r"\texorpdfstring{" + latex + "}{" + nombre.replace("`", "") + "}"
        return f"\\{orden}{{{latex}}}\\label{{sec:{numero}}}\n"

    def tabla(self, lineas: list[str]) -> str:
        filas = [celdas(l) for l in lineas]
        cabecera, cuerpo = filas[0], [f for f in filas[2:]]
        ncol = len(cabecera)
        for f in cuerpo:
            if len(f) != ncol:
                raise SystemExit(f"Una fila de tabla tiene {len(f)} columnas y la cabecera {ncol}: {f}")

        # Columnas cortas a su ancho natural; las largas reparten el ancho de la página.
        maximos = [max(largo_visible(f[c]) for f in filas[:1] + cuerpo) for c in range(ncol)]
        medias = [sum(largo_visible(f[c]) for f in cuerpo) / max(len(cuerpo), 1) for c in range(ncol)]
        largas = [c for c in range(ncol) if maximos[c] > 24]
        if largas:
            pesos = {c: max(medias[c], 10) ** 0.7 for c in largas}
            total = sum(pesos.values())
            spec = []
            for c in range(ncol):
                if c in pesos:
                    hsize = len(largas) * pesos[c] / total
                    spec.append(
                        r">{\raggedright\arraybackslash\hsize=" + f"{hsize:.3f}" + r"\hsize}X"
                    )
                else:
                    spec.append("l")
            inicio = r"\begin{xltabular}{\linewidth}{@{}" + "".join(spec) + "@{}}"
            fin = r"\end{xltabular}"
        else:
            inicio = r"\begin{longtable}{@{}" + "l" * ncol + "@{}}"
            fin = r"\end{longtable}"

        def fila(cs: list[str], negrita: bool = False) -> str:
            hechas = [self.en_linea(c) for c in cs]
            if negrita:
                hechas = [r"\textbf{" + h + "}" for h in hechas]
            return " & ".join(hechas) + r" \\"

        cab = fila(cabecera, negrita=True)
        partes = [
            r"{\small",
            inicio,
            r"\toprule",
            cab,
            r"\midrule",
            r"\endfirsthead",
            r"\toprule",
            cab,
            r"\midrule",
            r"\endhead",
            r"\bottomrule",
            r"\endlastfoot",
        ]
        partes += [fila(f) for f in cuerpo]
        partes += [fin, "}"]
        return "\n".join(partes) + "\n"


# ------------------------------------------------------------------------------------------------
# Documento
# ------------------------------------------------------------------------------------------------


def convertir(md: str) -> tuple[str, dict]:
    lineas = md.split("\n")
    bloques = leer_bloques(lineas)

    # Qué secciones existen, para enlazar los §.
    secciones = set()
    for b in bloques:
        if b[0] == "titulo" and b[1] in (2, 3):
            m = re.match(r"(\d+(?:\.\d+)?)", b[2])
            if m:
                secciones.add(m.group(1))
    escritor = Escritor(secciones)
    en_linea = escritor.en_linea

    if not bloques or bloques[0][0] != "titulo" or bloques[0][1] != 1:
        raise SystemExit("El .md tiene que empezar por un título # .")
    titulo = bloques[0][2]
    primera = next(
        (k for k, b in enumerate(bloques) if b[0] == "titulo" and b[1] == 2), len(bloques)
    )
    portada_bloques, cuerpo_bloques = bloques[1:primera], bloques[primera:]

    equipo = "Equipo"
    portada = []
    for b in portada_bloques:
        if b[0] == "parrafo" and b[1].startswith("**Equipo:**"):
            equipo = b[1][len("**Equipo:**") :].strip()
            continue
        if b[0] == "parrafo" and b[1].startswith("**Summary (English).**"):
            texto = en_linea(b[1][len("**Summary (English).**") :].strip())
            portada.append(
                "\\begin{resumen}{Summary (English)}\n\\begin{otherlanguage}{english}\n"
                + texto
                + "\n\\end{otherlanguage}\n\\end{resumen}\n"
            )
            continue
        portada.append(escritor.bloque(b))

    if ":" in titulo:
        principal, subtitulo = (t.strip() for t in titulo.split(":", 1))
        subtitulo = subtitulo[:1].upper() + subtitulo[1:]
    else:
        principal, subtitulo = titulo, ""

    # La primera sección del .md fija desde qué número cuenta LaTeX (0 o 1, por ejemplo).
    primera_seccion = next(
        (int(re.match(r"\d+", b[2]).group(0)) for b in cuerpo_bloques
         if b[0] == "titulo" and b[1] == 2 and re.match(r"\d+", b[2])),
        1,
    )
    escritor.numero = [primera_seccion - 1, 0]
    cuerpo = f"\\setcounter{{section}}{{{primera_seccion - 1}}}\n" + escritor.bloques(cuerpo_bloques)

    plantilla = PLANTILLA.read_text(encoding="utf-8")
    sustituciones = {
        "%%CONCURSO%%": escapar(CONCURSO),
        "%%TITULO%%": en_linea(principal),
        "%%SUBTITULO%%": en_linea(subtitulo),
        "%%TITULO_CORTO%%": en_linea(principal),
        "%%TITULO_PDF%%": escapar(titulo),
        "%%EQUIPO%%": escapar(equipo),
        "%%FECHA%%": escapar(FECHA),
        "%%PORTADA%%": "\n".join(portada).strip(),
        "%%CUERPO%%": cuerpo.strip(),
    }
    tex = plantilla
    for marca, valor in sustituciones.items():
        tex = tex.replace(marca, valor)
    sobran = re.findall(r"%%[A-Z_]+%%", tex)
    if sobran:
        raise SystemExit(f"La plantilla tiene marcas sin sustituir: {sorted(set(sobran))}")

    info = {
        "equipo": equipo,
        "pendientes": len(re.findall(r"\[PENDIENTE", md)),
        "secciones": len(secciones),
    }
    return CABECERA + tex, info


def compilar(equipo: str) -> Path:
    pdflatex = shutil.which("pdflatex")
    if not pdflatex:
        raise SystemExit(
            "No encuentro pdflatex. Instala TeX Live o MiKTeX, o sube docs/latex/documento_tecnico.tex "
            "a Overleaf (compilador pdfLaTeX)."
        )
    BUILD.mkdir(exist_ok=True)
    orden = [
        pdflatex,
        "-interaction=nonstopmode",
        "-halt-on-error",
        "-file-line-error",
        f"-output-directory={BUILD.name}",
        TEX.name,
    ]
    log = BUILD / "documento_tecnico.log"
    for pasada in range(1, 5):
        r = subprocess.run(orden, cwd=AQUI, capture_output=True, text=True, errors="replace")
        if r.returncode != 0:
            errores = [l for l in r.stdout.splitlines() if ":" in l and ("Error" in l or l.startswith("!"))]
            print("\n".join(errores[-15:]) or r.stdout[-3000:], file=sys.stderr)
            raise SystemExit(f"pdflatex ha fallado en la pasada {pasada}; el detalle está en {log}")
        texto_log = log.read_text(encoding="latin-1")
        if pasada >= 2 and "Rerun" not in texto_log and "rerun" not in texto_log:
            break
    pdf = BUILD / "documento_tecnico.pdf"
    destino = BUILD / f"{equipo}.pdf"
    shutil.copyfile(pdf, destino)
    avisos = len(re.findall(r"^Overfull \\hbox", texto_log, flags=re.M))
    if avisos:
        print(f"Aviso: {avisos} líneas se salen del margen (Overfull \\hbox en {log}).")
    return destino


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--pdf", action="store_true", help="compila también el PDF con pdflatex")
    p.add_argument("--comprobar", action="store_true", help="falla si el .tex no está al día")
    args = p.parse_args()

    tex, info = convertir(MD.read_text(encoding="utf-8"))

    if args.comprobar:
        actual = TEX.read_text(encoding="utf-8") if TEX.exists() else ""
        if actual != tex:
            raise SystemExit(
                f"{TEX.relative_to(RAIZ)} no está al día con el .md: "
                "ejecuta python3 docs/latex/md_a_latex.py"
            )
        print(f"{TEX.relative_to(RAIZ)} está al día.")
        return

    TEX.write_text(tex, encoding="utf-8", newline="\n")
    print(f"Escrito {TEX.relative_to(RAIZ)} ({info['secciones']} secciones).")
    if info["pendientes"]:
        print(
            f"Ojo: el documento tiene {info['pendientes']} marcas [PENDIENTE]; "
            "en el PDF salen en rojo."
        )
    if args.pdf:
        destino = compilar(info["equipo"])
        print(f"PDF: {destino.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
