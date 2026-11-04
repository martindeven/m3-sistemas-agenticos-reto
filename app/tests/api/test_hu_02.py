"""Pruebas de API para HU-02: consultar el directorio de empleados."""
import sqlite3
import uuid
from datetime import date
from pathlib import Path

import httpx

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


def test_cp01_directorio_completo_con_datos_principales(url_api: str) -> None:
    """CP-01: Ver el directorio completo con los datos principales."""
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

    respuesta = httpx.get(f"{url_api}/api/empleados")
    assert respuesta.status_code == 200
    empleados = {e["correo"]: e for e in respuesta.json()}

    encontrado_1 = empleados[empleado_1["correo"]]
    assert encontrado_1["numero_empleado"] == empleado_1["numero_empleado"]
    assert encontrado_1["nombre"] == f"Ana Pérez {token}"
    assert encontrado_1["puesto"] == "Analista"
    assert encontrado_1["departamento"] == "Tecnología"
    assert encontrado_1["estado"] == "activo"

    encontrado_2 = empleados[empleado_2["correo"]]
    assert encontrado_2["numero_empleado"] == empleado_2["numero_empleado"]
    assert encontrado_2["nombre"] == f"Luis Gómez {token}"
    assert encontrado_2["puesto"] == "Vendedor"
    assert encontrado_2["departamento"] == "Ventas"
    assert encontrado_2["estado"] == "activo"


def test_cp03_buscar_empleado_por_nombre(url_api: str) -> None:
    """CP-03: Buscar un empleado por nombre."""
    token = uuid.uuid4().hex[:8]
    nombre = f"Ana Pérez {token}"
    empleado = _crear_empleado(url_api, nombre=nombre, correo=_correo_unico(f"ana.{token}"))

    respuesta = httpx.get(f"{url_api}/api/empleados", params={"busqueda": nombre})
    assert respuesta.status_code == 200
    correos = [e["correo"] for e in respuesta.json()]
    assert empleado["correo"] in correos


def test_cp05_buscar_empleado_por_correo(url_api: str) -> None:
    """CP-05: Buscar un empleado por correo."""
    correo = _correo_unico(f"carlos.ruiz.{uuid.uuid4().hex[:8]}")
    empleado = _crear_empleado(url_api, nombre="Carlos Ruiz", correo=correo)

    respuesta = httpx.get(f"{url_api}/api/empleados", params={"busqueda": correo})
    assert respuesta.status_code == 200
    correos = [e["correo"] for e in respuesta.json()]
    assert empleado["correo"] in correos


def test_cp07_busqueda_no_distingue_mayusculas(url_api: str) -> None:
    """CP-07: La búsqueda no distingue mayúsculas de minúsculas."""
    token = uuid.uuid4().hex[:8]
    nombre = f"Ana Pérez {token}"
    empleado = _crear_empleado(url_api, nombre=nombre, correo=_correo_unico(f"ana.{token}"))

    respuesta = httpx.get(f"{url_api}/api/empleados", params={"busqueda": nombre.upper()})
    assert respuesta.status_code == 200
    correos = [e["correo"] for e in respuesta.json()]
    assert empleado["correo"] in correos


def test_cp09_filtrar_empleados_por_departamento(url_api: str) -> None:
    """CP-09: Filtrar empleados por departamento."""
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

    respuesta = httpx.get(f"{url_api}/api/empleados", params={"departamento": "Ventas"})
    assert respuesta.status_code == 200
    correos = [e["correo"] for e in respuesta.json()]
    assert incluido["correo"] in correos
    assert excluido["correo"] not in correos


def test_cp11_busqueda_sin_coincidencias(url_api: str) -> None:
    """CP-11: Buscar un término que no coincide con ningún empleado."""
    termino = f"Zutano Inexistente {uuid.uuid4().hex}"

    respuesta = httpx.get(f"{url_api}/api/empleados", params={"busqueda": termino})
    assert respuesta.status_code == 200
    assert respuesta.json() == []


def test_cp13_empleado_baja_sigue_en_directorio(url_api: str) -> None:
    """CP-13: Un empleado dado de baja sigue apareciendo en el directorio."""
    empleado = _crear_empleado(url_api, correo=_correo_unico(f"baja.{uuid.uuid4().hex[:8]}"))
    _marcar_baja(empleado["id"], "2024-01-10")

    respuesta = httpx.get(f"{url_api}/api/empleados")
    assert respuesta.status_code == 200
    encontrado = next(e for e in respuesta.json() if e["correo"] == empleado["correo"])
    assert encontrado["estado"] == "baja"
    assert encontrado["fecha_baja"] == "2024-01-10"
