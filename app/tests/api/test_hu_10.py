"""Pruebas de API para HU-10: solicitar vacaciones."""
import uuid

import httpx

ID_EMPLEADO_INEXISTENTE = 2_000_000_000


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


def _solicitar_vacaciones(url_api: str, empleado_id: int, fecha_inicio: str, fecha_fin: str) -> httpx.Response:
    return httpx.post(
        f"{url_api}/api/empleados/{empleado_id}/vacaciones",
        json={"fecha_inicio": fecha_inicio, "fecha_fin": fecha_fin},
    )


def test_cp01_registrar_solicitud_valida(url_api: str) -> None:
    """CP-01: Registrar una solicitud de vacaciones válida."""
    empleado = _crear_empleado(url_api, nombre="Ana CP01", fecha_ingreso="2024-01-15")

    respuesta = _solicitar_vacaciones(url_api, empleado["id"], "2026-07-06", "2026-07-10")

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["dias_habiles"] == 5
    assert cuerpo["dias_restantes"] == 7
    assert cuerpo["dias_disponibles"] == 7


def test_cp03_empleado_no_existe(url_api: str) -> None:
    """CP-03: Rechazar la solicitud cuando el empleado no existe."""
    respuesta = _solicitar_vacaciones(url_api, ID_EMPLEADO_INEXISTENTE, "2026-07-06", "2026-07-10")

    assert respuesta.status_code == 404
    assert respuesta.json()["detail"] == "Empleado no encontrado"


def test_cp04_empleado_dado_de_baja(url_api: str) -> None:
    """CP-04: Rechazar la solicitud cuando el empleado está dado de baja."""
    empleado = _crear_empleado(url_api, nombre="Carlos CP04", fecha_ingreso="2023-01-10")
    baja = httpx.patch(
        f"{url_api}/api/empleados/{empleado['id']}/baja",
        json={"fecha_baja": "2024-05-15"},
    )
    assert baja.status_code == 200

    respuesta = _solicitar_vacaciones(url_api, empleado["id"], "2026-07-06", "2026-07-10")

    assert respuesta.status_code == 409
    assert respuesta.json()["detail"] == "No se pueden solicitar vacaciones para un empleado dado de baja"


def test_cp05_fecha_fin_anterior_a_fecha_inicio(url_api: str) -> None:
    """CP-05: Rechazar la solicitud cuando la fecha de fin es anterior a la de inicio."""
    empleado = _crear_empleado(url_api, nombre="Diana CP05", fecha_ingreso="2024-01-15")

    respuesta = _solicitar_vacaciones(url_api, empleado["id"], "2026-07-10", "2026-07-05")

    assert respuesta.status_code == 400
    assert respuesta.json()["detail"] == "La fecha de fin no puede ser anterior a la fecha de inicio"


def test_cp07_periodo_cruza_de_anio(url_api: str) -> None:
    """CP-07: Rechazar la solicitud cuando el periodo cruza de un año a otro."""
    empleado = _crear_empleado(url_api, nombre="Eduardo CP07", fecha_ingreso="2024-01-15")

    respuesta = _solicitar_vacaciones(url_api, empleado["id"], "2026-12-28", "2027-01-08")

    assert respuesta.status_code == 400
    assert respuesta.json()["detail"] == "Las vacaciones deben estar dentro de un mismo año calendario"


def test_cp09_anio_sin_festivos(url_api: str) -> None:
    """CP-09: Rechazar la solicitud cuando el año no está en la tabla de festivos."""
    empleado = _crear_empleado(url_api, nombre="Fernanda CP09", fecha_ingreso="2024-01-01")

    respuesta = _solicitar_vacaciones(url_api, empleado["id"], "2028-07-10", "2028-07-14")

    assert respuesta.status_code == 400
    assert respuesta.json()["detail"] == "Solo se pueden solicitar vacaciones en 2026 y 2027"


def test_cp11_antiguedad_insuficiente(url_api: str) -> None:
    """CP-11: Rechazar la solicitud por antigüedad insuficiente."""
    empleado = _crear_empleado(url_api, nombre="Gabriel CP11", fecha_ingreso="2025-12-21")

    respuesta = _solicitar_vacaciones(url_api, empleado["id"], "2026-12-18", "2026-12-18")

    assert respuesta.status_code == 400
    assert respuesta.json()["detail"] == "Se requiere al menos un año de antigüedad a la fecha de inicio"


def test_cp13_periodo_sin_dias_habiles(url_api: str) -> None:
    """CP-13: Rechazar un periodo solo de fin de semana porque no incluye días hábiles."""
    empleado = _crear_empleado(url_api, nombre="Hugo CP13", fecha_ingreso="2024-01-15")

    respuesta = _solicitar_vacaciones(url_api, empleado["id"], "2026-07-11", "2026-07-12")

    assert respuesta.status_code == 400
    assert respuesta.json()["detail"] == "El periodo no incluye días hábiles"


def test_cp15_rebasa_dias_disponibles(url_api: str) -> None:
    """CP-15: Rechazar la solicitud cuando rebasa los días disponibles del año."""
    empleado = _crear_empleado(url_api, nombre="Irene CP15", fecha_ingreso="2024-01-15")
    previa = _solicitar_vacaciones(url_api, empleado["id"], "2026-09-14", "2026-09-18")
    assert previa.status_code == 201
    assert previa.json()["dias_habiles"] == 4

    respuesta = _solicitar_vacaciones(url_api, empleado["id"], "2026-10-05", "2026-10-15")

    assert respuesta.status_code == 400
    assert respuesta.json()["detail"] == "La solicitud excede los días disponibles: quedan 8 días hábiles"


def test_cp17_limite_exacto_quedan_cero(url_api: str) -> None:
    """CP-17: Límite exacto: se usan justo los días que quedan y quedan 0."""
    empleado = _crear_empleado(url_api, nombre="Javier CP17", fecha_ingreso="2024-01-15")
    previa = _solicitar_vacaciones(url_api, empleado["id"], "2026-07-06", "2026-07-10")
    assert previa.status_code == 201
    assert previa.json()["dias_habiles"] == 5

    respuesta = _solicitar_vacaciones(url_api, empleado["id"], "2026-07-13", "2026-07-21")

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["dias_habiles"] == 7
    assert cuerpo["dias_restantes"] == 0
    assert cuerpo["dias_disponibles"] == 0


def test_cp19_excede_por_uno(url_api: str) -> None:
    """CP-19: Excede por uno: se pide un día más de los que quedan y se rechaza."""
    empleado = _crear_empleado(url_api, nombre="Karla CP19", fecha_ingreso="2024-01-15")
    previa = _solicitar_vacaciones(url_api, empleado["id"], "2026-07-06", "2026-07-10")
    assert previa.status_code == 201
    assert previa.json()["dias_habiles"] == 5

    respuesta = _solicitar_vacaciones(url_api, empleado["id"], "2026-08-03", "2026-08-12")

    assert respuesta.status_code == 400
    assert respuesta.json()["detail"] == "La solicitud excede los días disponibles: quedan 7 días hábiles"


def test_cp21_primer_dia_de_antiguedad(url_api: str) -> None:
    """CP-21: Primer día de antigüedad: la fecha de inicio es justo el aniversario de ingreso."""
    empleado = _crear_empleado(url_api, nombre="Luis CP21", fecha_ingreso="2025-12-21")

    respuesta = _solicitar_vacaciones(url_api, empleado["id"], "2026-12-21", "2026-12-21")

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["dias_habiles"] == 1
    assert cuerpo["dias_restantes"] == 11


def test_cp23_periodo_con_festivo_no_lo_descuenta(url_api: str) -> None:
    """CP-23: Un periodo que incluye un festivo no descuenta ese día."""
    empleado = _crear_empleado(url_api, nombre="Marina CP23", fecha_ingreso="2024-01-15")

    respuesta = _solicitar_vacaciones(url_api, empleado["id"], "2026-12-21", "2026-12-31")

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["dias_habiles"] == 8
    assert cuerpo["dias_restantes"] == 4
