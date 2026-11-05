"""Pruebas end-to-end para HU-02: consultar el directorio de empleados."""
import uuid

import httpx
from playwright.sync_api import Page, expect


def _crear_empleado(
    url_api: str,
    *,
    nombre: str,
    puesto: str,
    departamento: str,
    fecha_ingreso: str = "2024-01-15",
) -> dict:
    correo = f"{uuid.uuid4().hex[:10]}@empresa.com"
    cuerpo = {
        "nombre": nombre,
        "correo": correo,
        "puesto": puesto,
        "departamento": departamento,
        "fecha_ingreso": fecha_ingreso,
    }
    respuesta = httpx.post(f"{url_api}/api/empleados", json=cuerpo)
    assert respuesta.status_code == 201
    return respuesta.json()


def test_cp02_ver_directorio_completo(page: Page, url_api: str, url_web: str) -> None:
    """CP-02: Ver el directorio completo con los datos principales."""
    ana = _crear_empleado(url_api, nombre="Ana Pérez", puesto="Analista", departamento="Tecnología")
    luis = _crear_empleado(url_api, nombre="Luis Gómez", puesto="Vendedor", departamento="Ventas")

    page.goto(url_web)

    tabla = page.get_by_test_id("tabla-empleados")
    expect(tabla).to_be_visible()

    fila_ana = tabla.get_by_test_id(f"fila-empleado-{ana['id']}")
    expect(fila_ana.get_by_test_id(f"numero-empleado-{ana['id']}")).to_have_text(ana["numero_empleado"])
    expect(fila_ana).to_contain_text("Ana Pérez")
    expect(fila_ana).to_contain_text("Analista")
    expect(fila_ana).to_contain_text("Tecnología")
    expect(fila_ana.get_by_test_id(f"estado-empleado-{ana['id']}")).to_have_text("Activo")

    fila_luis = tabla.get_by_test_id(f"fila-empleado-{luis['id']}")
    expect(fila_luis.get_by_test_id(f"numero-empleado-{luis['id']}")).to_have_text(luis["numero_empleado"])
    expect(fila_luis).to_contain_text("Luis Gómez")
    expect(fila_luis).to_contain_text("Vendedor")
    expect(fila_luis).to_contain_text("Ventas")
    expect(fila_luis.get_by_test_id(f"estado-empleado-{luis['id']}")).to_have_text("Activo")


def test_cp04_buscar_empleado_por_nombre(page: Page, url_api: str, url_web: str) -> None:
    """CP-04: Buscar un empleado por nombre."""
    ana = _crear_empleado(url_api, nombre="Ana Pérez", puesto="Analista", departamento="Tecnología")

    page.goto(url_web)
    page.get_by_test_id("buscar-empleados").fill("Ana Pérez")

    tabla = page.get_by_test_id("tabla-empleados")
    fila_ana = tabla.get_by_test_id(f"fila-empleado-{ana['id']}")
    expect(fila_ana).to_contain_text("Ana Pérez")


def test_cp06_buscar_empleado_por_correo(page: Page, url_api: str, url_web: str) -> None:
    """CP-06: Buscar un empleado por correo."""
    correo = f"carlos.ruiz.{uuid.uuid4().hex[:8]}@empresa.com"
    cuerpo = {
        "nombre": "Carlos Ruiz",
        "correo": correo,
        "puesto": "Contador",
        "departamento": "Finanzas",
        "fecha_ingreso": "2024-01-15",
    }
    creado = httpx.post(f"{url_api}/api/empleados", json=cuerpo)
    assert creado.status_code == 201
    carlos = creado.json()

    page.goto(url_web)
    page.get_by_test_id("buscar-empleados").fill(correo)

    tabla = page.get_by_test_id("tabla-empleados")
    fila_carlos = tabla.get_by_test_id(f"fila-empleado-{carlos['id']}")
    expect(fila_carlos).to_contain_text("Carlos Ruiz")


def test_cp08_busqueda_no_distingue_mayusculas(page: Page, url_api: str, url_web: str) -> None:
    """CP-08: La búsqueda no distingue mayúsculas de minúsculas."""
    ana = _crear_empleado(url_api, nombre="Ana Pérez", puesto="Analista", departamento="Tecnología")

    page.goto(url_web)
    page.get_by_test_id("buscar-empleados").fill("ANA PÉREZ")

    tabla = page.get_by_test_id("tabla-empleados")
    fila_ana = tabla.get_by_test_id(f"fila-empleado-{ana['id']}")
    expect(fila_ana).to_contain_text("Ana Pérez")


def test_cp10_filtrar_empleados_por_departamento(page: Page, url_api: str, url_web: str) -> None:
    """CP-10: Filtrar empleados por departamento."""
    ana = _crear_empleado(url_api, nombre="Ana Pérez", puesto="Analista", departamento="Tecnología")
    luis = _crear_empleado(url_api, nombre="Luis Gómez", puesto="Vendedor", departamento="Ventas")

    page.goto(url_web)
    page.get_by_test_id("filtro-departamento").select_option("Ventas")

    tabla = page.get_by_test_id("tabla-empleados")
    fila_luis = tabla.get_by_test_id(f"fila-empleado-{luis['id']}")
    expect(fila_luis).to_contain_text("Luis Gómez")
    expect(tabla.get_by_test_id(f"fila-empleado-{ana['id']}")).not_to_be_visible()


def test_cp12_buscar_termino_sin_coincidencias(page: Page, url_web: str) -> None:
    """CP-12: Buscar un término que no coincide con ningún empleado."""
    termino = f"Zutano Inexistente {uuid.uuid4().hex}"

    page.goto(url_web)
    page.get_by_test_id("buscar-empleados").fill(termino)

    sin_resultados = page.get_by_test_id("sin-resultados")
    expect(sin_resultados).to_be_visible()
    expect(sin_resultados).to_have_text("No se encontraron empleados")


def test_cp14_empleado_de_baja_sigue_en_directorio(page: Page, url_api: str, url_web: str) -> None:
    """CP-14: Un empleado dado de baja sigue apareciendo en el directorio."""
    empleado = _crear_empleado(
        url_api, nombre="Diana Flores", puesto="Analista", departamento="Operaciones", fecha_ingreso="2024-01-01"
    )
    baja = httpx.patch(f"{url_api}/api/empleados/{empleado['id']}/baja", json={"fecha_baja": "2024-01-10"})
    assert baja.status_code == 200

    page.goto(url_web)

    tabla = page.get_by_test_id("tabla-empleados")
    fila = tabla.get_by_test_id(f"fila-empleado-{empleado['id']}")
    expect(fila).to_be_visible()
    expect(fila.get_by_test_id(f"estado-empleado-{empleado['id']}")).to_have_text("Baja")
