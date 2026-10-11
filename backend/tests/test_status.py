"""
Página de estado (issue #154): `GET /api/status`.

Es pública y la ve cualquiera, así que se comprueba qué cuenta de cada
componente en cada situación y que no se le escapa nada sensible.
"""

import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core import models  # noqa: F401 - registra los modelos ORM
from app.core.app_config import app_settings
from app.core.database import Base, get_db
from app.main import app
from app.modules.readings.model import Reading

_SECRETO = "postgresql://aquaguard:contrasena-secreta@database:5432/aquaguard"


@pytest.fixture()
def engine():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture()
def client(engine, tmp_path, monkeypatch):
    def _get_db():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db] = _get_db
    monkeypatch.setattr(app_settings, "BACKUPS_DIR", str(tmp_path))
    monkeypatch.setattr(app_settings, "BACKUP_INTERVAL_HOURS", 24)
    yield TestClient(app)
    app.dependency_overrides.clear()


def _lectura(engine, hace: timedelta):
    with Session(engine) as db:
        db.add(
            Reading(
                sensor_id=uuid4(),
                value=Decimal("3.5"),
                unit="bar",
                recorded_at=datetime.now(timezone.utc) - hace,
                created_at=datetime.now(timezone.utc) - hace,
            )
        )
        db.commit()


def _backup(tmp_path, nombre: str, hace: timedelta, contenido: bytes = b"x" * 100):
    fichero = tmp_path / nombre
    fichero.write_bytes(contenido)
    momento = (datetime.now(timezone.utc) - hace).timestamp()
    os.utime(fichero, (momento, momento))


def _componentes(client) -> dict:
    cuerpo = client.get("/api/status").json()
    return {c["name"]: c for c in cuerpo["components"]}


def test_todo_en_marcha_es_operational(client, engine, tmp_path):
    _lectura(engine, hace=timedelta(seconds=10))
    _backup(tmp_path, "aquaguard-20261010-120000.sql.gz", hace=timedelta(hours=1))

    respuesta = client.get("/api/status")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["status"] == "OPERATIONAL"
    assert [c["name"] for c in cuerpo["components"]] == [
        "backend",
        "database",
        "simulator",
        "backup",
    ]
    assert all(c["status"] == "OPERATIONAL" for c in cuerpo["components"])
    datetime.fromisoformat(cuerpo["checked_at"].replace("Z", "+00:00"))


def test_no_pide_sesion(client):
    assert client.get("/api/status").status_code == 200


def test_sin_lecturas_el_simulador_esta_caido(client):
    simulador = _componentes(client)["simulator"]

    assert simulador["status"] == "DOWN"
    assert simulador["last_event_at"] is None


def test_lectura_antigua_deja_el_simulador_caido_pero_dice_cuando(client, engine):
    _lectura(engine, hace=timedelta(minutes=30))

    simulador = _componentes(client)["simulator"]

    assert simulador["status"] == "DOWN"
    assert simulador["last_event_at"] is not None


def test_sin_backups_el_backup_esta_caido(client):
    backup = _componentes(client)["backup"]

    assert backup["status"] == "DOWN"
    assert backup["last_event_at"] is None
    assert backup["size_bytes"] is None


def test_devuelve_fecha_y_tamano_del_backup_mas_reciente(client, tmp_path):
    _backup(tmp_path, "aquaguard-20261008-120000.sql.gz", timedelta(hours=50), b"x" * 10)
    _backup(tmp_path, "aquaguard-20261010-120000.sql.gz", timedelta(hours=2), b"x" * 300)

    backup = _componentes(client)["backup"]

    assert backup["status"] == "OPERATIONAL"
    assert backup["size_bytes"] == 300


def test_backup_atrasado_es_degraded(client, tmp_path):
    _backup(tmp_path, "aquaguard-20261001-120000.sql.gz", hace=timedelta(hours=49))

    assert _componentes(client)["backup"]["status"] == "DEGRADED"


def test_un_backup_a_medias_no_cuenta(client, tmp_path):
    _backup(tmp_path, "aquaguard-20261010-120000.sql.gz.tmp", hace=timedelta(minutes=1))

    assert _componentes(client)["backup"]["status"] == "DOWN"


def test_un_componente_caido_deja_el_global_en_degraded(client, engine):
    _lectura(engine, hace=timedelta(seconds=10))

    assert client.get("/api/status").json()["status"] == "DEGRADED"


class _SesionCaida:
    def execute(self, *args, **kwargs):
        raise OperationalError("SELECT 1", {}, Exception(f"could not connect to {_SECRETO}"))


def test_con_la_base_caida_responde_200_y_lo_cuenta(client):
    def _get_db():
        yield _SesionCaida()

    app.dependency_overrides[get_db] = _get_db

    respuesta = client.get("/api/status")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    componentes = {c["name"]: c["status"] for c in cuerpo["components"]}
    assert cuerpo["status"] == "DOWN"
    assert componentes["backend"] == "OPERATIONAL"
    assert componentes["database"] == "DOWN"
    assert componentes["simulator"] == "DOWN"
    assert "contrasena-secreta" not in respuesta.text
    assert "postgresql://" not in respuesta.text
