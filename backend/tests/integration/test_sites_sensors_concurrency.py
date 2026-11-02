"""
Plantas de un edificio y sus sensores a la vez (B3, issue #139).

Editar un edificio, borrarlo, dar de alta un sensor y moverlo de planta
bloquean la fila del site (`SiteRepository.get_for_update`). Estos tests
abren una transacción que ya tiene el site bloqueado y a medio cambiar,
lanzan la otra operación en otro hilo y comprueban que espera y valida
contra lo que dejó la primera.

Solo corren en PostgreSQL: SQLite no bloquea filas.
"""

from __future__ import annotations

import threading
import time
from decimal import Decimal

import pytest
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core import models  # noqa: F401 - registra los modelos ORM
from app.core.exceptions import DomainValidationError, NotFoundError
from app.modules.organizations.model import Organization
from app.modules.sensors.model import Sensor
from app.modules.sensors.schemas import SensorCreate, SensorUpdate
from app.modules.sensors.service import SensorService
from app.modules.sites.model import Site
from app.modules.sites.repository import SiteRepository

ESPERA_MAXIMA = 10  # segundos


@pytest.fixture()
def postgres(engine):
    if engine.dialect.name != "postgresql":
        pytest.skip("El bloqueo de filas solo se puede comprobar en PostgreSQL")
    return engine


@pytest.fixture()
def torre(postgres):
    """Torre: 6 plantas (de la 0 a la 5), con un sensor en la planta 3."""
    with Session(postgres, expire_on_commit=False) as db:
        organizacion = Organization(name="Hotel Sol")
        db.add(organizacion)
        db.flush()
        site = Site(organization_id=organizacion.id, name="Torre", floors=6)
        db.add(site)
        db.flush()
        sensor = Sensor(
            site_id=site.id,
            external_id="S-1",
            name="Sensor 1",
            floor=3,
            low_threshold=Decimal("1"),
            high_threshold=Decimal("9"),
        )
        db.add(sensor)
        db.commit()
    return {"site": site, "sensor": sensor}


def _en_otro_hilo(engine, accion) -> tuple[threading.Thread, dict]:
    """Ejecuta `accion(service)` con su propia sesión, como otra petición."""
    resultado: dict = {}

    def ejecutar():
        with Session(engine) as db:
            try:
                resultado["respuesta"] = accion(SensorService(db))
            except Exception as exc:  # se comprueba en el test
                resultado["error"] = exc

    hilo = threading.Thread(target=ejecutar)
    hilo.start()
    return hilo, resultado


def _esperar_a_que_se_bloquee(engine) -> None:
    """Espera a que la otra petición esté parada esperando el bloqueo."""
    limite = time.monotonic() + ESPERA_MAXIMA
    with engine.connect() as conexion:
        while time.monotonic() < limite:
            esperando = conexion.scalar(
                text(
                    "SELECT count(*) FROM pg_stat_activity "
                    "WHERE datname = current_database() AND wait_event_type = 'Lock'"
                )
            )
            if esperando:
                return
            time.sleep(0.02)
    pytest.fail("La segunda operación no llegó a esperar el bloqueo del site")


def test_mover_un_sensor_mientras_se_quitan_plantas_da_422(postgres, torre):
    with Session(postgres) as primera:
        # Una edición del edificio a medias: le quita la planta 5, sin commit.
        site = SiteRepository(primera).get_for_update(torre["site"].id)
        site.floors = 5
        primera.flush()

        hilo, resultado = _en_otro_hilo(
            postgres,
            lambda s: s.update(torre["sensor"].id, SensorUpdate(floor=5)),
        )
        _esperar_a_que_se_bloquee(postgres)
        primera.commit()

    hilo.join(ESPERA_MAXIMA)
    error = resultado.get("error")
    assert isinstance(error, DomainValidationError), resultado
    assert error.code == "FLOOR_OUT_OF_SITE"
    with Session(postgres) as db:
        assert db.get(Sensor, torre["sensor"].id).floor == 3


def test_dar_de_alta_un_sensor_mientras_se_borra_el_edificio_da_404(postgres, torre):
    with Session(postgres) as primera:
        # Un borrado a medias del edificio, sin commit. Para poder borrarlo
        # se quita antes su sensor.
        site = SiteRepository(primera).get_for_update(torre["site"].id)
        primera.delete(primera.get(Sensor, torre["sensor"].id))
        primera.delete(site)
        primera.flush()

        alta = SensorCreate(
            site_id=torre["site"].id,
            external_id="S-2",
            name="Sensor 2",
            min_pressure=1.5,
            max_pressure=6,
        )
        hilo, resultado = _en_otro_hilo(postgres, lambda s: s.create(alta))
        _esperar_a_que_se_bloquee(postgres)
        primera.commit()

    hilo.join(ESPERA_MAXIMA)
    error = resultado.get("error")
    assert isinstance(error, NotFoundError), resultado
    assert error.code == "SITE_NOT_FOUND"
    with Session(postgres) as db:
        assert db.scalars(select(Sensor).where(Sensor.external_id == "S-2")).first() is None
