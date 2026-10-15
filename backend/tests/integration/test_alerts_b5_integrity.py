"""B5: integridad referencial y concurrencia real en PostgreSQL."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import time

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError
from app.modules.alerts.model import Alert
from app.modules.alerts.repository import AlertRepository
from app.modules.alerts.service import AlertService
from app.modules.organizations.model import Organization
from app.modules.sensors.model import Sensor
from app.modules.sites.model import Site
from app.modules.users.model import User


@pytest.fixture()
def data(engine):
    with Session(engine, expire_on_commit=False) as db:
        org = Organization(name="B5")
        db.add(org)
        db.flush()
        site = Site(organization_id=org.id, name="Torre")
        db.add(site)
        db.flush()
        sensor = Sensor(site_id=site.id, name="Sensor", external_id="B5", low_threshold=1, high_threshold=9)
        actors = [User(email=f"b5-{i}@example.com", name=f"Operador {i}", role="admin", password_hash="unused") for i in range(2)]
        db.add_all([sensor, *actors])
        db.flush()
        alert = Alert(sensor_id=sensor.id, alert_type="LOW_PRESSURE", severity="WARNING", status="ACTIVE", message="Presión baja")
        db.add(alert)
        db.commit()
        return alert.id, [u.id for u in actors]


def test_borrar_actor_conserva_alerta_y_fechas(engine, data):
    alert_id, actors = data
    with Session(engine) as db:
        service = AlertService(db)
        service.acknowledge(alert_id, None, actors[0])
        before = service.resolve(alert_id, None, actors[0])
        db.delete(db.get(User, actors[0]))
        db.commit()
    with Session(engine) as db:
        row = db.get(Alert, alert_id)
        assert row.acknowledged_by is None
        assert row.resolved_by is None
        response = AlertService(db).list(None, 0, 20).items[0]
        assert response.state == "RESOLVED"
        assert response.acknowledged_by_name is None
        assert response.resolved_by_name is None
        assert response.acknowledged_at.replace(tzinfo=None) == before.acknowledged_at.replace(tzinfo=None)
        assert response.resolved_at.replace(tzinfo=None) == before.resolved_at.replace(tzinfo=None)


def _wait_for_lock(engine):
    deadline = time.monotonic() + 10
    # PostgreSQL conserva una instantánea de estadísticas por transacción.
    # Cada sondeo necesita una nueva para observar el bloqueo que acaba de llegar.
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
        while time.monotonic() < deadline:
            if connection.scalar(text("SELECT count(*) FROM pg_stat_activity WHERE datname = current_database() AND wait_event_type = 'Lock'")):
                return
            time.sleep(0.02)
    pytest.fail("La segunda acción no esperó el bloqueo de la alerta")


@pytest.mark.parametrize("action", ["acknowledge", "resolve"])
def test_primera_accion_conserva_actor_y_fecha(engine, data, action):
    if engine.dialect.name != "postgresql":
        pytest.skip("La concurrencia requiere bloqueo de filas PostgreSQL")
    alert_id, actors = data
    when = datetime(2026, 10, 12, tzinfo=timezone.utc)

    def second_request():
        with Session(engine) as db:
            # Objeto cargado antes de esperar: el bloqueo debe refrescarlo.
            loaded = db.get(Alert, alert_id)
            assert loaded.status == "ACTIVE"
            try:
                return getattr(AlertService(db), action)(alert_id, None, actors[1])
            except ConflictError as exc:
                return exc

    # Mantener la primera operación abierta hasta que la segunda esté
    # bloqueada; rollback y join también se ejecutan si falla la espera.
    with ThreadPoolExecutor(max_workers=1) as executor:
        with Session(engine) as first:
            repository = AlertRepository(first)
            repository.get_by_id(alert_id, None, for_update=True)
            getattr(repository, action)(alert_id, when, actors[0])
            first.flush()
            future = executor.submit(second_request)
            try:
                _wait_for_lock(engine)
                first.commit()
            finally:
                first.rollback()
        result = future.result(timeout=10)
    if action == "resolve":
        assert isinstance(result, ConflictError)
        assert result.code == "ALERT_ALREADY_RESOLVED"
    else:
        assert result.acknowledged_by_name == "Operador 0"
    with Session(engine) as db:
        row = db.get(Alert, alert_id)
        assert (row.resolved_by if action == "resolve" else row.acknowledged_by) == actors[0]
        stamp = row.resolved_at if action == "resolve" else row.acknowledged_at
        assert stamp == when
