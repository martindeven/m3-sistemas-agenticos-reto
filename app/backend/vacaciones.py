"""Reglas de cálculo de HU-10: días hábiles, aniversario de antigüedad y saldo anual."""
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from models import Vacacion

FESTIVOS: dict[int, list[date]] = {
    2026: [
        date(2026, 1, 1),
        date(2026, 2, 2),
        date(2026, 3, 16),
        date(2026, 5, 1),
        date(2026, 9, 16),
        date(2026, 11, 16),
        date(2026, 12, 25),
    ],
    2027: [
        date(2027, 1, 1),
        date(2027, 2, 1),
        date(2027, 3, 15),
        date(2027, 5, 1),
        date(2027, 9, 16),
        date(2027, 11, 15),
        date(2027, 12, 25),
    ],
}


def calcular_dias_habiles(fecha_inicio: date, fecha_fin: date) -> int:
    """Cuenta los días hábiles del periodo, incluyendo inicio y fin."""
    festivos_anio = set(FESTIVOS.get(fecha_inicio.year, []))
    dias = 0
    fecha = fecha_inicio
    while fecha <= fecha_fin:
        if fecha.weekday() < 5 and fecha not in festivos_anio:
            dias += 1
        fecha += timedelta(days=1)
    return dias


def fecha_aniversario(fecha_ingreso: date) -> date:
    """Primer aniversario de ingreso; 29 de febrero cae en 1 de marzo si el año no es bisiesto."""
    anio_objetivo = fecha_ingreso.year + 1
    try:
        return fecha_ingreso.replace(year=anio_objetivo)
    except ValueError:
        return date(anio_objetivo, 3, 1)


def dias_usados_en_anio(db: Session, empleado_id: int, anio: int) -> int:
    solicitudes = db.scalars(
        select(Vacacion)
        .where(Vacacion.empleado_id == empleado_id)
        .where(Vacacion.fecha_inicio >= date(anio, 1, 1))
        .where(Vacacion.fecha_inicio <= date(anio, 12, 31))
    ).all()
    return sum(s.dias_habiles for s in solicitudes)
