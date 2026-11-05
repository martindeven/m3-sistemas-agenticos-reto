"""Pruebas end-to-end para HU-10: solicitar vacaciones."""
import uuid

import httpx
from playwright.sync_api import Page, expect


def _crear_empleado(
    url_api: str,
    *,
    nombre: str = "Empleado Prueba",
    departamento: str = "Ventas",
    fecha_ingreso: str = "2024-01-15",
) -> dict:
    correo = f"{nombre.lower().replace(' ', '.')}.{uuid.uuid4().hex[:8]}@empresa.com"
    cuerpo = {
        "nombre": nombre,
        "correo": correo,
        "puesto": "Analista",
        "departamento": departamento,
        "fecha_ingreso": fecha_ingreso,
    }
    respuesta = httpx.post(f"{url_api}/api/empleados", json=cuerpo)
    assert respuesta.status_code == 201
    return respuesta.json()


def _registrar_vacaciones_previas(url_api: str, empleado_id: int, fecha_inicio: str, fecha_fin: str) -> None:
    respuesta = httpx.post(
        f"{url_api}/api/empleados/{empleado_id}/vacaciones",
        json={"fecha_inicio": fecha_inicio, "fecha_fin": fecha_fin},
    )
    assert respuesta.status_code == 201


def _abrir_panel(page: Page, url_web: str, empleado_id: int):
    page.goto(url_web)
    fila = page.get_by_test_id(f"fila-empleado-{empleado_id}")
    fila.get_by_test_id(f"vacaciones-abrir-{empleado_id}").click()
    return page.get_by_test_id(f"panel-vacaciones-{empleado_id}")


def test_cp02_registrar_solicitud_valida(page: Page, url_api: str, url_web: str) -> None:
    """CP-02: Registrar una solicitud de vacaciones válida."""
    empleado = _crear_empleado(url_api, nombre="Ana CP02", fecha_ingreso="2024-01-15")

    panel = _abrir_panel(page, url_web, empleado["id"])
    expect(panel.get_by_test_id("vacaciones-disponibles")).to_have_text("12")

    panel.get_by_test_id("vacaciones-fecha-inicio").fill("2026-07-06")
    panel.get_by_test_id("vacaciones-fecha-fin").fill("2026-07-10")
    panel.get_by_test_id("vacaciones-enviar").click()

    mensaje = panel.get_by_test_id("vacaciones-mensaje").get_by_test_id("mensaje-exito")
    expect(mensaje).to_have_text("Solicitud registrada: 5 días hábiles. Te quedan 7 días hábiles en 2026.")


def test_cp06_fecha_fin_anterior_a_fecha_inicio(page: Page, url_api: str, url_web: str) -> None:
    """CP-06: Rechazar la solicitud cuando la fecha de fin es anterior a la de inicio."""
    empleado = _crear_empleado(url_api, nombre="Diana CP06", fecha_ingreso="2024-01-15")

    panel = _abrir_panel(page, url_web, empleado["id"])
    panel.get_by_test_id("vacaciones-fecha-inicio").fill("2026-07-10")
    panel.get_by_test_id("vacaciones-fecha-fin").fill("2026-07-05")
    panel.get_by_test_id("vacaciones-enviar").click()

    mensaje = panel.get_by_test_id("vacaciones-mensaje").get_by_test_id("mensaje-error")
    expect(mensaje).to_have_text("La fecha de fin no puede ser anterior a la fecha de inicio")


def test_cp08_periodo_cruza_de_anio(page: Page, url_api: str, url_web: str) -> None:
    """CP-08: Rechazar la solicitud cuando el periodo cruza de un año a otro."""
    empleado = _crear_empleado(url_api, nombre="Eduardo CP08", fecha_ingreso="2024-01-15")

    panel = _abrir_panel(page, url_web, empleado["id"])
    panel.get_by_test_id("vacaciones-fecha-inicio").fill("2026-12-28")
    panel.get_by_test_id("vacaciones-fecha-fin").fill("2027-01-08")
    panel.get_by_test_id("vacaciones-enviar").click()

    mensaje = panel.get_by_test_id("vacaciones-mensaje").get_by_test_id("mensaje-error")
    expect(mensaje).to_have_text("Las vacaciones deben estar dentro de un mismo año calendario")


def test_cp10_anio_sin_festivos(page: Page, url_api: str, url_web: str) -> None:
    """CP-10: Rechazar la solicitud cuando el año no está en la tabla de festivos."""
    empleado = _crear_empleado(url_api, nombre="Fernanda CP10", fecha_ingreso="2024-01-01")

    panel = _abrir_panel(page, url_web, empleado["id"])
    panel.get_by_test_id("vacaciones-fecha-inicio").fill("2028-07-10")
    panel.get_by_test_id("vacaciones-fecha-fin").fill("2028-07-14")
    panel.get_by_test_id("vacaciones-enviar").click()

    mensaje = panel.get_by_test_id("vacaciones-mensaje").get_by_test_id("mensaje-error")
    expect(mensaje).to_have_text("Solo se pueden solicitar vacaciones en 2026 y 2027")


def test_cp12_antiguedad_insuficiente(page: Page, url_api: str, url_web: str) -> None:
    """CP-12: Rechazar la solicitud por antigüedad insuficiente."""
    empleado = _crear_empleado(url_api, nombre="Gabriel CP12", fecha_ingreso="2025-12-21")

    panel = _abrir_panel(page, url_web, empleado["id"])
    panel.get_by_test_id("vacaciones-fecha-inicio").fill("2026-12-18")
    panel.get_by_test_id("vacaciones-fecha-fin").fill("2026-12-18")
    panel.get_by_test_id("vacaciones-enviar").click()

    mensaje = panel.get_by_test_id("vacaciones-mensaje").get_by_test_id("mensaje-error")
    expect(mensaje).to_have_text("Se requiere al menos un año de antigüedad a la fecha de inicio")


def test_cp14_periodo_sin_dias_habiles(page: Page, url_api: str, url_web: str) -> None:
    """CP-14: Rechazar un periodo solo de fin de semana porque no incluye días hábiles."""
    empleado = _crear_empleado(url_api, nombre="Hugo CP14", fecha_ingreso="2024-01-15")

    panel = _abrir_panel(page, url_web, empleado["id"])
    panel.get_by_test_id("vacaciones-fecha-inicio").fill("2026-07-11")
    panel.get_by_test_id("vacaciones-fecha-fin").fill("2026-07-12")
    panel.get_by_test_id("vacaciones-enviar").click()

    mensaje = panel.get_by_test_id("vacaciones-mensaje").get_by_test_id("mensaje-error")
    expect(mensaje).to_have_text("El periodo no incluye días hábiles")


def test_cp16_rebasa_dias_disponibles(page: Page, url_api: str, url_web: str) -> None:
    """CP-16: Rechazar la solicitud cuando rebasa los días disponibles del año."""
    empleado = _crear_empleado(url_api, nombre="Irene CP16", fecha_ingreso="2024-01-15")
    _registrar_vacaciones_previas(url_api, empleado["id"], "2026-09-14", "2026-09-18")

    panel = _abrir_panel(page, url_web, empleado["id"])
    expect(panel.get_by_test_id("vacaciones-disponibles")).to_have_text("8")

    panel.get_by_test_id("vacaciones-fecha-inicio").fill("2026-10-05")
    panel.get_by_test_id("vacaciones-fecha-fin").fill("2026-10-15")
    panel.get_by_test_id("vacaciones-enviar").click()

    mensaje = panel.get_by_test_id("vacaciones-mensaje").get_by_test_id("mensaje-error")
    expect(mensaje).to_have_text("La solicitud excede los días disponibles: quedan 8 días hábiles")


def test_cp18_limite_exacto_quedan_cero(page: Page, url_api: str, url_web: str) -> None:
    """CP-18: Límite exacto: se usan justo los días que quedan y quedan 0."""
    empleado = _crear_empleado(url_api, nombre="Javier CP18", fecha_ingreso="2024-01-15")
    _registrar_vacaciones_previas(url_api, empleado["id"], "2026-07-06", "2026-07-10")

    panel = _abrir_panel(page, url_web, empleado["id"])
    expect(panel.get_by_test_id("vacaciones-disponibles")).to_have_text("7")

    panel.get_by_test_id("vacaciones-fecha-inicio").fill("2026-07-13")
    panel.get_by_test_id("vacaciones-fecha-fin").fill("2026-07-21")
    panel.get_by_test_id("vacaciones-enviar").click()

    mensaje = panel.get_by_test_id("vacaciones-mensaje").get_by_test_id("mensaje-exito")
    expect(mensaje).to_have_text("Solicitud registrada: 7 días hábiles. Te quedan 0 días hábiles en 2026.")


def test_cp20_excede_por_uno(page: Page, url_api: str, url_web: str) -> None:
    """CP-20: Excede por uno: se pide un día más de los que quedan y se rechaza."""
    empleado = _crear_empleado(url_api, nombre="Karla CP20", fecha_ingreso="2024-01-15")
    _registrar_vacaciones_previas(url_api, empleado["id"], "2026-07-06", "2026-07-10")

    panel = _abrir_panel(page, url_web, empleado["id"])
    expect(panel.get_by_test_id("vacaciones-disponibles")).to_have_text("7")

    panel.get_by_test_id("vacaciones-fecha-inicio").fill("2026-08-03")
    panel.get_by_test_id("vacaciones-fecha-fin").fill("2026-08-12")
    panel.get_by_test_id("vacaciones-enviar").click()

    mensaje = panel.get_by_test_id("vacaciones-mensaje").get_by_test_id("mensaje-error")
    expect(mensaje).to_have_text("La solicitud excede los días disponibles: quedan 7 días hábiles")


def test_cp22_primer_dia_de_antiguedad(page: Page, url_api: str, url_web: str) -> None:
    """CP-22: Primer día de antigüedad: la fecha de inicio es justo el aniversario de ingreso."""
    empleado = _crear_empleado(url_api, nombre="Luis CP22", fecha_ingreso="2025-12-21")

    panel = _abrir_panel(page, url_web, empleado["id"])
    panel.get_by_test_id("vacaciones-fecha-inicio").fill("2026-12-21")
    panel.get_by_test_id("vacaciones-fecha-fin").fill("2026-12-21")
    panel.get_by_test_id("vacaciones-enviar").click()

    mensaje = panel.get_by_test_id("vacaciones-mensaje").get_by_test_id("mensaje-exito")
    expect(mensaje).to_have_text("Solicitud registrada: 1 días hábiles. Te quedan 11 días hábiles en 2026.")


def test_cp24_periodo_con_festivo_no_lo_descuenta(page: Page, url_api: str, url_web: str) -> None:
    """CP-24: Un periodo que incluye un festivo no descuenta ese día."""
    empleado = _crear_empleado(url_api, nombre="Marina CP24", fecha_ingreso="2024-01-15")

    panel = _abrir_panel(page, url_web, empleado["id"])
    panel.get_by_test_id("vacaciones-fecha-inicio").fill("2026-12-21")
    panel.get_by_test_id("vacaciones-fecha-fin").fill("2026-12-31")
    panel.get_by_test_id("vacaciones-enviar").click()

    mensaje = panel.get_by_test_id("vacaciones-mensaje").get_by_test_id("mensaje-exito")
    expect(mensaje).to_have_text("Solicitud registrada: 8 días hábiles. Te quedan 4 días hábiles en 2026.")
