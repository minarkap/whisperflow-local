"""
Post-procesador de texto transcrito.
Detecta listas expresadas con ordinales o numerales en español
y las convierte a formato con guiones.
"""

import re

# Ordinales y numerales que indican un elemento de lista
_LIST_MARKERS = (
    r"primero|segundo|tercero|cuarto|quinto|"
    r"sexto|séptimo|octavo|noveno|décimo|"
    r"primer|tercer|"                          # formas apocopadas
    r"uno|dos|tres|cuatro|cinco|"
    r"seis|siete|ocho|nueve|diez"
)

# Patrón completo: marcador al inicio de segmento, opcionalmente seguido de coma o punto
_MARKER_RE = re.compile(
    rf"(?<![a-záéíóúñ])({_LIST_MARKERS})[\s,.:;-]*",
    re.IGNORECASE,
)


def format_text(text: str) -> str:
    """Detecta listas y las formatea con guiones. Si no hay lista, devuelve el texto intacto."""
    markers = list(_MARKER_RE.finditer(text))
    if len(markers) < 2:
        return text  # sin lista detectada

    # Texto antes del primer marcador (introducción)
    preamble = text[: markers[0].start()].strip()

    # Dividir en segmentos: (marcador, contenido)
    items = []
    for i, match in enumerate(markers):
        start = match.end()
        end = markers[i + 1].start() if i + 1 < len(markers) else len(text)
        content = text[start:end].strip().rstrip(".,;")
        if content:
            # Capitalizar primera letra del item
            content = content[0].upper() + content[1:]
            items.append(f"- {content}")

    if not items:
        return text

    parts = []
    if preamble:
        parts.append(preamble)
    parts.extend(items)
    return "\n".join(parts)
