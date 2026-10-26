"""
Cambios de estado de organizaciones a la vez (B1, issue #139, PR #191).

Cada cambio de estado bloquea la fila de la organización mientras valida y
guarda (`OrganizationRepository.get_for_update`). Estos tests abren una
transacción que ya tiene la fila bloqueada y a medio cambiar, lanzan la
segunda operación en otro hilo y comprueban que espera y valida contra el
estado nuevo, no contra el que había al empezar.

Solo corren en PostgreSQL: SQLite no bloquea filas.
"""

from __future__ import annotations

import threading
import time
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core import models  # noqa: F401 - registra los modelos ORM
from app.core.app_config import app_settings
from app.core.exceptions import ConflictError
from app.modules.organizations.model import Organization
from app.modules.organizations.repository import OrganizationRepository
from app.modules.organizations.service import OrganizationService

ESPERA_MAXIMA = 10  # segundos


@pytest.fixture()
def postgres(engine):
    if engine.dialect.name != "postgresql":
        pytest.skip("El bloqueo de filas solo se puede comprobar en PostgreSQL")
    return engine


def _organizacion_en_prueba(engine) -> tuple[Organization, datetime]:
    fin = datetime.now(timezone.utc) + timedelta(days=3)
    with Session(engine, expire_on_commit=False) as db:
        organizacion = Organization(
            name="Colegio Luna", status="TRIAL", trial_ends_at=fin
        )
        db.add(organizacion)
        db.commit()
    return organizacion, fin


def _en_otro_hilo(engine, accion) -> tuple[threading.Thread, dict]:
    """Ejecuta `accion(service)` con su propia sesión, como otra petición."""
    resultado: dict = {}

    def ejecutar():
        with Session(engine) as db:
            try:
                resultado["respuesta"] = accion(OrganizationService(db))
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
    pytest.fail("La segunda operación no llegó a esperar el bloqueo de la fila")


def _estado_final(engine, organization_id) -> Organization:
    with Session(engine) as db:
        return db.scalars(
            select(Organization).where(Organization.id == organization_id)
        ).one()


def test_ampliar_mientras_se_suspende_da_409_y_queda_suspendida(postgres):
    organizacion, _ = _organizacion_en_prueba(postgres)

    with Session(postgres) as primera:
        # Una suspensión a medias: fila bloqueada y estado cambiado, sin commit.
        en_curso = OrganizationRepository(primera).get_for_update(organizacion.id)
        en_curso.status = "SUSPENDED"
        primera.flush()

        hilo, resultado = _en_otro_hilo(
            postgres, lambda s: s.extend_trial(organizacion.id)
        )
        _esperar_a_que_se_bloquee(postgres)
        primera.commit()

    hilo.join(ESPERA_MAXIMA)
    error = resultado.get("error")
    assert isinstance(error, ConflictError), resultado
    assert error.code == "ORGANIZATION_NOT_IN_TRIAL"
    assert _estado_final(postgres, organizacion.id).status == "SUSPENDED"


def test_dos_ampliaciones_a_la_vez_suman_los_dias_dos_veces(postgres):
    organizacion, fin = _organizacion_en_prueba(postgres)
    dias = timedelta(days=app_settings.TRIAL_DAYS)

    with Session(postgres) as primera:
        # Una ampliación a medias: fila bloqueada y fin movido, sin commit.
        en_curso = OrganizationRepository(primera).get_for_update(organizacion.id)
        en_curso.trial_ends_at = en_curso.trial_ends_at.astimezone(timezone.utc) + dias
        primera.flush()

        hilo, resultado = _en_otro_hilo(
            postgres, lambda s: s.extend_trial(organizacion.id)
        )
        _esperar_a_que_se_bloquee(postgres)
        primera.commit()

    hilo.join(ESPERA_MAXIMA)
    assert "error" not in resultado, resultado
    assert _estado_final(postgres, organizacion.id).trial_ends_at == fin + 2 * dias
