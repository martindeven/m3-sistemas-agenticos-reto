"""Configuración de la base de datos SQLite con SQLAlchemy 2."""
from pathlib import Path
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DATOS_DIR = Path(__file__).parent / "datos"
DATOS_DIR.mkdir(exist_ok=True)

DATABASE_URL = f"sqlite:///{DATOS_DIR / 'empleados.db'}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def obtener_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
