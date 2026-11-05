"""Sesión 1 · Agente 1, analista: historia de usuario -> criterios de aceptación en Gherkin.

Uso:  python -m agentes.analista historias/HU-01-registrar-empleado.md
"""
import re
import sys
import unicodedata
from pathlib import Path

from agentes.base import RAIZ, SALIDA, ejecutar_agente, herramientas_archivos, hu_de, rel

SISTEMA = """Eres analista de producto en un equipo de software. Conviertes historias de usuario
en criterios de aceptación escritos en Gherkin, en español.

Cómo trabajas:
1. Lee la historia, el archivo contexto/reglas_negocio.md y los archivos contexto/convenciones_*.md
   que cite la historia.
2. Escribe {destino}. La primera línea es `# language: es` y usas las palabras clave
   Característica, Escenario, Dado, Cuando, Entonces, Y.
3. Incluye el camino feliz y un escenario de error por cada regla de negocio que aplique a ESTA historia.
4. Cada escenario se puede verificar desde la pantalla o la API: datos concretos, nada de «funciona bien».
5. No inventes reglas. Si falta información, agrégala al final como comentarios bajo `# Preguntas abiertas`.
6. Si la historia cita un archivo de convenciones con la tabla «Errores: mensajes exactos»:
   - Escribe un escenario por cada fila de esa tabla, con su código HTTP y el `detail` copiado
     letra por letra (acentos y puntuación incluidos). Donde la tabla dice N, escribe un número concreto.
     Un solo mensaje de error por escenario.
   - No uses «Antecedentes:» ni «Esquema del escenario:»; solo «Escenario:» con datos concretos.
   - Incluye estos límites, con estas palabras en el título del escenario:
     · «límite exacto»: se usan justo los días que quedan; se acepta y quedan 0.
     · «excede por uno»: se pide un día más de los que quedan; se rechaza con el mensaje de tope.
     · «primer día de antigüedad»: la fecha de inicio es justo el aniversario de ingreso; se acepta.
     · Un periodo que incluye un festivo (el festivo no se descuenta).
     · Un periodo solo de fin de semana (se rechaza porque no incluye días hábiles).
7. Responde al final con una sola línea: cuántos escenarios escribiste."""


def escenarios(gherkin: str) -> list[str]:
    """Nombres de los escenarios del Gherkin, en orden."""
    return re.findall(r"^\s*Escenario:\s*(.+?)\s*$", gherkin, flags=re.MULTILINE)


def preguntas_abiertas(gherkin: str) -> list[str]:
    """Líneas bajo «# Preguntas abiertas» al final del Gherkin; vacío si no hay."""
    if "# Preguntas abiertas" not in gherkin:
        return []
    bloque = gherkin.split("# Preguntas abiertas", 1)[1]
    return [l.lstrip("# -").strip() for l in bloque.splitlines() if l.strip().lstrip("#").strip()]


def convenciones_citadas(historia: Path) -> list[Path]:
    """Archivos contexto/convenciones_*.md que la historia menciona y que existen, sin repetir.

    HU-01 a HU-03 no citan ninguno, así que para ellas devuelve una lista vacía.
    """
    citas = re.findall(r"contexto/convenciones_[\w-]+\.md", historia.read_text(encoding="utf-8"))
    rutas = [RAIZ / c for c in dict.fromkeys(citas)]   # dict.fromkeys quita repetidos y conserva el orden
    return [r for r in rutas if r.exists()]


def mensajes_exactos(historia: Path) -> list[str]:
    """Valores `detail` de la tabla «Errores: mensajes exactos» de las convenciones que cita la historia.

    Lee las filas de la tabla hasta el siguiente encabezado. Solo cuenta las filas cuya segunda
    celda es un código HTTP (así se salta la cabecera) y toma el texto entre backticks de la
    última celda. Si la historia no cita convenciones, devuelve [].
    """
    mensajes: list[str] = []
    for archivo in convenciones_citadas(historia):
        dentro = False
        for linea in archivo.read_text(encoding="utf-8").splitlines():
            if re.match(r"^#+\s*Errores: mensajes exactos", linea):
                dentro = True
                continue
            if dentro and linea.startswith("#"):
                break                                     # terminó la sección
            if dentro and linea.strip().startswith("|"):
                celdas = [c.strip() for c in linea.strip().strip("|").split("|")]
                valor = re.fullmatch(r"`(.+)`", celdas[-1])
                if len(celdas) >= 3 and celdas[1].isdigit() and valor and valor[1] not in mensajes:
                    mensajes.append(valor[1])
    return mensajes


def patron_mensaje(mensaje: str) -> re.Pattern:
    """Regex que busca el mensaje letra por letra; la «N» suelta de la tabla vale por cualquier número.

    `(?<!\\w)N(?!\\w)` solo toca la N aislada: la de «No se pueden…» queda igual.
    """
    return re.compile(re.sub(r"(?<!\w)N(?!\w)", r"\\d+", re.escape(mensaje)))


def _sin_acentos(texto: str) -> str:
    """Minúsculas y sin acentos, para comparar títulos de escenario sin depender de cómo se escriban."""
    return "".join(c for c in unicodedata.normalize("NFD", texto.lower()) if unicodedata.category(c) != "Mn")


def validar_gherkin(texto: str, mensajes: list[str] | None = None) -> list[str]:
    """Evaluador determinista: devuelve los problemas encontrados; vacío = válido.

    Siempre revisa la forma (idioma, Característica, Dado/Cuando/Entonces). Si recibe `mensajes`
    (los `detail` exactos de las convenciones), revisa además que cada uno aparezca letra por letra
    en su propio escenario, que haya camino feliz y que estén los escenarios límite de tope y antigüedad.
    """
    problemas = []
    if not texto.lstrip().startswith("# language: es"):
        problemas.append("La primera línea debe ser '# language: es'.")
    if "Característica:" not in texto:
        problemas.append("Falta 'Característica:'.")
    bloques = re.split(r"^\s*Escenario:", texto, flags=re.MULTILINE)[1:]
    if len(bloques) < 2:
        problemas.append("Se esperan al menos 2 escenarios (camino feliz y un error).")
    for i, bloque in enumerate(bloques, 1):
        for clave in ("Dado", "Cuando", "Entonces"):
            if not re.search(rf"^\s*{clave}\b", bloque, flags=re.MULTILINE):
                problemas.append(f"El escenario {i} no tiene '{clave}'.")
    if mensajes:
        problemas += _validar_mensajes(bloques, mensajes)
    return problemas


def _validar_mensajes(bloques: list[str], mensajes: list[str]) -> list[str]:
    """Reglas extra de validar_gherkin cuando la historia tiene una tabla de mensajes exactos."""
    problemas = []
    patrones = {m: patron_mensaje(m) for m in mensajes}
    titulos = [b.strip().splitlines()[0].strip() if b.strip() else "" for b in bloques]
    # Qué mensajes contiene cada escenario
    contiene = [[m for m, p in patrones.items() if p.search(b)] for b in bloques]

    for m in mensajes:
        if not any(m in c for c in contiene):
            problemas.append(f"Falta el mensaje exacto: «{m}»")
    for titulo, c in zip(titulos, contiene):
        if len(c) > 1:
            problemas.append(f"El escenario «{titulo}» mezcla varios mensajes; usa uno por mensaje.")
    if not any(not c and not re.search(r"\b4\d\d\b", b) for b, c in zip(bloques, contiene)):
        problemas.append("Falta un escenario de camino feliz (solicitud aceptada).")

    def hay(clave: str, condicion) -> bool:
        """¿Algún escenario con `clave` en el título cumple la condición?"""
        return any(clave in _sin_acentos(t) and condicion(b, c) for t, b, c in zip(titulos, bloques, contiene))

    tope = next((m for m in mensajes if "excede" in m), None)
    if tope:
        if not hay("limite exacto", lambda b, c: tope not in c and re.search(r"\b0\b", b)):
            problemas.append("Falta el escenario de límite exacto: usar justo los días que quedan (quedan 0).")
        if not hay("excede por uno", lambda b, c: tope in c):
            problemas.append("Falta el escenario «excede por uno» con el mensaje de tope.")
    antiguedad = next((m for m in mensajes if "antigüedad" in m), None)
    if antiguedad and not hay("primer dia de antiguedad", lambda b, c: antiguedad not in c):
        problemas.append("Falta el escenario del primer día con antigüedad (aceptado).")
    return problemas


def generar_criterios(historia: Path, max_intentos: int = 2) -> Path:
    """Ejecuta al analista y valida su Gherkin; si hay problemas, se los devuelve para que corrija.

    Los mensajes exactos salen de las convenciones que cita la historia (vacío en HU-01 a HU-03).
    """
    carpeta = SALIDA / hu_de(historia)
    destino = carpeta / "criterios.feature"
    herramientas = herramientas_archivos(lectura=[RAIZ / "historias", RAIZ / "contexto"], escritura=carpeta)
    mensajes = mensajes_exactos(historia)
    tarea = f"Historia de usuario: {rel(historia)}"
    for intento in range(1, max_intentos + 1):
        print(f"Analista · intento {intento}")
        ejecutar_agente(SISTEMA.format(destino=rel(destino)), herramientas, tarea, nombre="analista")
        problemas = validar_gherkin(destino.read_text(encoding="utf-8"), mensajes) if destino.exists() \
            else [f"No se escribió {rel(destino)}."]
        if not problemas:
            return destino
        # Reflexión guiada por un evaluador determinista: el agente recibe los problemas y corrige
        tarea += "\n\nTu versión anterior tiene estos problemas; corrígelos:\n- " + "\n- ".join(problemas)
    raise ValueError("Criterios inválidos tras varios intentos:\n- " + "\n- ".join(problemas))


if __name__ == "__main__":
    ruta = generar_criterios(Path(sys.argv[1]).resolve())
    texto = ruta.read_text(encoding="utf-8")
    print(f"\nListo: {rel(ruta)} · {len(escenarios(texto))} escenarios")
    for p in preguntas_abiertas(texto):
        print("  Pregunta abierta:", p)
