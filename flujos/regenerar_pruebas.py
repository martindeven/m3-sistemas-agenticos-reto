"""Regenera las pruebas de una historia con el automatizador y las ejecuta contra la app desplegada.

Sirve para rehacer las pruebas de HU-01 a HU-03 cuando se corrigen las instrucciones del
automatizador, sin volver a correr toda la fábrica. No toca app/ a mano: quien escribe es el
agente, a través de Claude Code con sus hooks y su auditoría.

Requiere la app arriba en los puertos 8000 y 8080 (docker compose up -d en app/).

Uso:  python -m flujos.regenerar_pruebas HU-02
"""
import re
import sys

from agentes import automatizador
from agentes.base import SALIDA
from flujos import verificacion


MAX_CORRECCIONES = 1


def fallos_de_la_historia(log: str, hu: str) -> str:
    """Del log de ejecutar_pruebas, solo los bloques de fallas de los archivos de esta historia.

    Las fallas de regresión (otras historias) no se le pasan al agente: no son su tarea aquí.
    """
    bloques = re.split(r"\n(?=- tests\.)", log)
    return "\n".join(b for b in bloques if b.startswith("- tests.") and f"test_{verificacion._hu_min(hu)}" in b)


def main(hu: str) -> int:
    """Llama al automatizador, corre la suite completa e imprime el resultado; devuelve 0 si todo pasó.

    Si fallan pruebas de esta historia, le devuelve esas fallas al automatizador para que las corrija
    (como mucho MAX_CORRECCIONES veces) y vuelve a correr la suite.
    """
    _, costo = automatizador.automatizar(hu)
    print(f"Automatizador terminó · {costo:.2f} USD")
    ok, log = verificacion.ejecutar_pruebas(hu)
    for correccion in range(1, MAX_CORRECCIONES + 1):
        fallos = fallos_de_la_historia(log, hu)
        if ok or not fallos:
            break
        print(f"\nCorrección {correccion}: le paso al automatizador las fallas de {hu}\n{fallos}")
        _, c = automatizador.automatizar(hu, fallos)
        costo += c
        print(f"Automatizador terminó · {c:.2f} USD (total {costo:.2f} USD)")
        ok, log = verificacion.ejecutar_pruebas(hu)
    print(f"\nPruebas: {'OK' if ok else 'FALLA'}\n{log}")
    return 0 if ok else 1


if __name__ == "__main__":
    if len(sys.argv) != 2 or not re.fullmatch(r"HU-\d\d", sys.argv[1]):
        sys.exit("Uso: python -m flujos.regenerar_pruebas HU-02")
    if not (SALIDA / sys.argv[1] / "casos_prueba.json").exists():
        sys.exit(f"No existe salida/{sys.argv[1]}/casos_prueba.json: primero corre la fábrica para esa historia.")
    sys.exit(main(sys.argv[1]))
