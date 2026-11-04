"""Pruebas end-to-end para HU-03: editar y dar de baja a un empleado."""
import uuid
from datetime import date

import httpx
from playwright.sync_api import Page, expect


def _correo_unico(prefijo: str) -> str:
    return f"{prefijo}.{uuid.uuid4().hex[:8]}@empresa.com"


def _crear_empleado(url_api: str, **datos) -> dict:
    cuerpo = {
        "nombre": "Empleado de prueba",
        "correo": _correo_unico("empleado"),
        "puesto": "Puesto de prueba",
        "departamento": "Tecnología",
        "fecha_ingreso": date.today().isoformat(),
    }
    cuerpo.update(datos)
    respuesta = httpx.post(f"{url_api}/api/empleados", json=cuerpo)
    assert respuesta.status_code == 201
    return respuesta.json()


def _dar_de_baja(url_api: str, empleado_id: int, fecha_baja: str) -> dict:
    respuesta = httpx.patch(f"{url_api}/api/empleados/{empleado_id}/baja", json={"fecha_baja": fecha_baja})
    assert respuesta.status_code == 200
    return respuesta.json()


def test_cp02_editar_puesto_y_departamento_empleado_activo(page: Page, url_api: str, url_web: str) -> None:
    """CP-02: Editar correctamente el puesto y el departamento de un empleado activo."""
    empleado = _crear_empleado(url_api, puesto="Analista", departamento="Ventas")

    page.goto(url_web)
    fila = page.get_by_test_id(f"fila-empleado-{empleado['id']}")
    fila.get_by_test_id(f"editar-empleado-{empleado['id']}").click()
    fila.get_by_test_id("empleado-puesto").fill("Analista Senior")
    fila.get_by_test_id("empleado-departamento").select_option("Tecnología")
    fila.get_by_test_id("empleado-guardar").click()

    expect(page.get_by_test_id("mensaje-exito")).to_be_visible()
    expect(fila).to_contain_text("Analista Senior")
    expect(fila).to_contain_text("Tecnología")


def test_cp04_dar_de_baja_empleado_activo(page: Page, url_api: str, url_web: str) -> None:
    """CP-04: Dar de baja correctamente a un empleado activo."""
    empleado = _crear_empleado(url_api, fecha_ingreso="2022-01-10")

    page.goto(url_web)
    fila = page.get_by_test_id(f"fila-empleado-{empleado['id']}")
    fila.get_by_test_id(f"baja-empleado-{empleado['id']}").click()
    fila.get_by_test_id("empleado-fecha-baja").fill("2024-05-15")
    fila.get_by_test_id("confirmar-baja").click()

    expect(page.get_by_test_id("mensaje-exito")).to_be_visible()
    expect(page.get_by_test_id(f"estado-empleado-{empleado['id']}")).to_have_text("Baja")
    expect(page.get_by_test_id(f"fila-empleado-{empleado['id']}")).to_be_visible()


def test_cp06_no_editar_empleado_dado_de_baja(page: Page, url_api: str, url_web: str) -> None:
    """CP-06: No se puede editar a un empleado que ya está dado de baja."""
    empleado = _crear_empleado(url_api, fecha_ingreso="2020-01-01")
    _dar_de_baja(url_api, empleado["id"], "2024-01-10")

    page.goto(url_web)
    fila = page.get_by_test_id(f"fila-empleado-{empleado['id']}")
    fila.get_by_test_id(f"editar-empleado-{empleado['id']}").click()
    fila.get_by_test_id("empleado-puesto").fill("Gerente")
    fila.get_by_test_id("empleado-guardar").click()

    expect(page.get_by_test_id("mensaje-error")).to_contain_text("No se puede editar a un empleado dado de baja")


def test_cp08_editar_con_puesto_invalido(page: Page, url_api: str, url_web: str) -> None:
    """CP-08: Editar con un puesto inválido muestra mensaje de error."""
    empleado = _crear_empleado(url_api)

    page.goto(url_web)
    fila = page.get_by_test_id(f"fila-empleado-{empleado['id']}")
    fila.get_by_test_id(f"editar-empleado-{empleado['id']}").click()
    fila.get_by_test_id("empleado-puesto").fill("A")
    fila.get_by_test_id("empleado-guardar").click()

    expect(page.get_by_test_id("mensaje-error")).to_contain_text("puesto")


def test_cp10_editar_con_departamento_no_permitido(page: Page, url_api: str, url_web: str) -> None:
    """CP-10: Editar con un departamento que no está en la lista permitida muestra mensaje de error."""
    empleado = _crear_empleado(url_api)

    page.goto(url_web)
    fila = page.get_by_test_id(f"fila-empleado-{empleado['id']}")
    fila.get_by_test_id(f"editar-empleado-{empleado['id']}").click()
    fila.get_by_test_id("empleado-departamento").select_option("Marketing")
    fila.get_by_test_id("empleado-guardar").click()

    expect(page.get_by_test_id("mensaje-error")).to_contain_text("departamento")


def test_cp12_dar_de_baja_con_fecha_anterior_a_ingreso(page: Page, url_api: str, url_web: str) -> None:
    """CP-12: Dar de baja con una fecha de baja anterior a la fecha de ingreso muestra mensaje de error."""
    empleado = _crear_empleado(url_api, fecha_ingreso="2023-03-01")

    page.goto(url_web)
    fila = page.get_by_test_id(f"fila-empleado-{empleado['id']}")
    fila.get_by_test_id(f"baja-empleado-{empleado['id']}").click()
    fila.get_by_test_id("empleado-fecha-baja").fill("2023-02-15")
    fila.get_by_test_id("confirmar-baja").click()

    expect(page.get_by_test_id("mensaje-error")).to_contain_text("fecha_baja")


def test_cp14_dar_de_baja_sin_fecha_baja(page: Page, url_api: str, url_web: str) -> None:
    """CP-14: Dar de baja sin indicar la fecha de baja muestra mensaje de error."""
    empleado = _crear_empleado(url_api)

    page.goto(url_web)
    fila = page.get_by_test_id(f"fila-empleado-{empleado['id']}")
    fila.get_by_test_id(f"baja-empleado-{empleado['id']}").click()
    fila.get_by_test_id("empleado-fecha-baja").fill("")
    fila.get_by_test_id("confirmar-baja").click()

    expect(page.get_by_test_id("mensaje-error")).to_contain_text("fecha_baja")
