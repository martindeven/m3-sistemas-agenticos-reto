"""Pruebas end-to-end para HU-02: consultar el directorio de empleados."""
import sqlite3
import uuid
from datetime import date
from pathlib import Path

import httpx
from playwright.sync_api import Page, expect

RUTA_BD = Path(__file__).resolve().parents[2] / "backend" / "datos" / "empleados.db"


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


def _marcar_baja(empleado_id: int, fecha_baja: str) -> None:
    """Marca un empleado como dado de baja directo en la BD.

    La API no expone todavía un endpoint para dar de baja a un empleado,
    así que la precondición se arma escribiendo directo en la base de datos.
    """
    conexion = sqlite3.connect(RUTA_BD)
    try:
        conexion.execute(
            "UPDATE empleados SET estado = 'baja', fecha_baja = ? WHERE id = ?",
            (fecha_baja, empleado_id),
        )
        conexion.commit()
    finally:
        conexion.close()


def test_cp02_directorio_completo_con_datos_principales(page: Page, url_api: str, url_web: str) -> None:
    """CP-02: Ver el directorio completo con los datos principales."""
    token = uuid.uuid4().hex[:8]
    empleado_1 = _crear_empleado(
        url_api,
        nombre=f"Ana Pérez {token}",
        correo=_correo_unico(f"ana.{token}"),
        puesto="Analista",
        departamento="Tecnología",
    )
    empleado_2 = _crear_empleado(
        url_api,
        nombre=f"Luis Gómez {token}",
        correo=_correo_unico(f"luis.{token}"),
        puesto="Vendedor",
        departamento="Ventas",
    )

    page.goto(url_web)

    expect(page.get_by_test_id("tabla-empleados")).to_be_visible()

    fila_1 = page.get_by_test_id(f"fila-empleado-{empleado_1['id']}")
    expect(fila_1.get_by_test_id(f"numero-empleado-{empleado_1['id']}")).to_have_text(
        empleado_1["numero_empleado"]
    )
    expect(fila_1).to_contain_text(f"Ana Pérez {token}")
    expect(fila_1).to_contain_text("Analista")
    expect(fila_1).to_contain_text("Tecnología")
    expect(fila_1.get_by_test_id(f"estado-empleado-{empleado_1['id']}")).to_have_text("Activo")

    fila_2 = page.get_by_test_id(f"fila-empleado-{empleado_2['id']}")
    expect(fila_2.get_by_test_id(f"numero-empleado-{empleado_2['id']}")).to_have_text(
        empleado_2["numero_empleado"]
    )
    expect(fila_2).to_contain_text(f"Luis Gómez {token}")
    expect(fila_2).to_contain_text("Vendedor")
    expect(fila_2).to_contain_text("Ventas")
    expect(fila_2.get_by_test_id(f"estado-empleado-{empleado_2['id']}")).to_have_text("Activo")


def test_cp04_buscar_empleado_por_nombre(page: Page, url_api: str, url_web: str) -> None:
    """CP-04: Buscar un empleado por nombre."""
    token = uuid.uuid4().hex[:8]
    nombre = f"Ana Pérez {token}"
    empleado = _crear_empleado(url_api, nombre=nombre, correo=_correo_unico(f"ana.{token}"))

    page.goto(url_web)
    page.get_by_test_id("buscar-empleados").fill(nombre)

    fila = page.get_by_test_id(f"fila-empleado-{empleado['id']}")
    expect(fila).to_contain_text(nombre)


def test_cp06_buscar_empleado_por_correo(page: Page, url_api: str, url_web: str) -> None:
    """CP-06: Buscar un empleado por correo."""
    correo = _correo_unico(f"carlos.ruiz.{uuid.uuid4().hex[:8]}")
    empleado = _crear_empleado(url_api, nombre="Carlos Ruiz", correo=correo)

    page.goto(url_web)
    page.get_by_test_id("buscar-empleados").fill(correo)

    fila = page.get_by_test_id(f"fila-empleado-{empleado['id']}")
    expect(fila).to_be_visible()


def test_cp08_busqueda_no_distingue_mayusculas(page: Page, url_api: str, url_web: str) -> None:
    """CP-08: La búsqueda no distingue mayúsculas de minúsculas."""
    token = uuid.uuid4().hex[:8]
    nombre = f"Ana Pérez {token}"
    empleado = _crear_empleado(url_api, nombre=nombre, correo=_correo_unico(f"ana.{token}"))

    page.goto(url_web)
    page.get_by_test_id("buscar-empleados").fill(nombre.upper())

    fila = page.get_by_test_id(f"fila-empleado-{empleado['id']}")
    expect(fila).to_contain_text(nombre)


def test_cp10_filtrar_empleados_por_departamento(page: Page, url_api: str, url_web: str) -> None:
    """CP-10: Filtrar empleados por departamento."""
    token = uuid.uuid4().hex[:8]
    incluido = _crear_empleado(
        url_api,
        nombre=f"Luis Gómez {token}",
        correo=_correo_unico(f"luis.{token}"),
        puesto="Vendedor",
        departamento="Ventas",
    )
    excluido = _crear_empleado(
        url_api,
        nombre=f"Ana Pérez {token}",
        correo=_correo_unico(f"ana.{token}"),
        puesto="Analista",
        departamento="Tecnología",
    )

    page.goto(url_web)
    page.get_by_test_id("filtro-departamento").select_option("Ventas")

    expect(page.get_by_test_id(f"fila-empleado-{incluido['id']}")).to_contain_text("Ventas")
    expect(page.get_by_test_id(f"fila-empleado-{excluido['id']}")).to_have_count(0)


def test_cp12_busqueda_sin_coincidencias(page: Page, url_web: str) -> None:
    """CP-12: Buscar un término que no coincide con ningún empleado."""
    termino = f"Zutano Inexistente {uuid.uuid4().hex}"

    page.goto(url_web)
    page.get_by_test_id("buscar-empleados").fill(termino)

    expect(page.get_by_test_id("sin-resultados")).to_have_text("No se encontraron empleados")


def test_cp14_empleado_baja_sigue_en_directorio(page: Page, url_api: str, url_web: str) -> None:
    """CP-14: Un empleado dado de baja sigue apareciendo en el directorio."""
    empleado = _crear_empleado(url_api, correo=_correo_unico(f"baja.{uuid.uuid4().hex[:8]}"))
    _marcar_baja(empleado["id"], "2024-01-10")

    page.goto(url_web)

    fila = page.get_by_test_id(f"fila-empleado-{empleado['id']}")
    expect(fila).to_be_visible()
    expect(page.get_by_test_id(f"estado-empleado-{empleado['id']}")).to_have_text("Baja")
