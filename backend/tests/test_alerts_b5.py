"""B5: filtros combinables, estados derivados y trazabilidad por HTTP."""
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import event
from sqlalchemy.orm import Session

from app.modules.alerts.model import Alert
from app.modules.alerts.service import AlertService
from app.modules.users.model import User
from test_alerts_endpoints import client, datos, engine, _entrar  # noqa: F401


@pytest.fixture()
def escenario(engine, datos):
    start = datetime(2026, 10, 12, tzinfo=timezone.utc)
    with Session(engine) as db:
        for i, saved in enumerate(datos["a"]["alertas"]):
            alert = db.get(Alert, saved.id)
            alert.created_at = start + timedelta(days=i * 7)
            if i == 1:
                alert.acknowledged_at = alert.created_at + timedelta(minutes=1)
                alert.acknowledged_by = datos["a"]["user"].id
                alert.severity = "CRITICAL"
            if i == 2:
                alert.status = "RESOLVED"
                alert.resolved_at = alert.created_at + timedelta(seconds=90)
                alert.resolved_by = datos["a"]["user"].id
        db.commit()
    return start


@pytest.mark.parametrize("params,indices", [
    ({"state": "ACTIVE"}, [0]),
    ({"state": "ACKNOWLEDGED"}, [1]),
    ({"state": "RESOLVED"}, [2]),
    ({"status": "ACTIVE"}, [0, 1]),
    ({"severity": "CRITICAL"}, [1]),
    ({"status": "RESOLVED", "state": "ACKNOWLEDGED"}, []),
    ({"created_from": "2026-10-12", "created_to": "2026-10-19"}, [0]),
    ({"created_from": "2026-10-19T02:00:00+02:00"}, [1, 2]),
    ({"created_to": "2026-10-19T00:00:00Z"}, [0]),
    ({"created_from": "2026-10-19", "created_to": "2026-10-26", "state": "ACKNOWLEDGED", "severity": "CRITICAL", "q": "  BAJA  "}, [1]),
])
def test_filtros(client, datos, escenario, params, indices):
    _entrar(client, datos["a"]["user"])
    response = client.get("/api/alerts", params=params)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["total"] == len(indices)
    assert {item["id"] for item in body["items"]} == {str(datos["a"]["alertas"][i].id) for i in indices}


@pytest.mark.parametrize("params", [
    {"severity": "HIGH"}, {"state": "UNKNOWN"}, {"status": "ACKNOWLEDGED"},
    {"created_from": "ayer"}, {"created_to": "mañana"},
    {"created_from": "2026-10-19", "created_to": "2026-10-12"},
    {"created_from": "2026-10-19", "created_to": "2026-10-19"},
])
def test_filtros_invalidos(client, datos, params):
    _entrar(client, datos["a"]["user"])
    response = client.get("/api/alerts", params=params)
    assert response.status_code == 422
    if "created_from" in params and "created_to" in params:
        assert response.json()["error"]["code"] == "INVALID_DATE_RANGE"


def test_filtros_por_cliente_edificio_y_paginacion(client, datos, escenario, engine):
    with Session(engine) as db:
        admin = User(email="admin-b5@example.com", name="Admin B5", role="admin", password_hash="unused")
        db.add(admin)
        db.commit()
        _entrar(client, admin)
    sensor = datos["a"]["sensor"]
    params = {"organization_id": str(datos["a"]["user"].organization_id), "site_id": str(sensor.site_id), "sensor_id": str(sensor.id), "status": "ACTIVE", "page_size": 1}
    first = client.get("/api/alerts", params=params).json()
    second = client.get("/api/alerts", params={**params, "page": 2}).json()
    assert first["total"] == second["total"] == 2
    assert first["items"][0]["id"] != second["items"][0]["id"]
    _entrar(client, datos["b"]["user"])
    assert client.get("/api/alerts", params=params).json()["total"] == 0


def test_actor_primero_y_resolucion_directa(client, datos, engine):
    user = datos["a"]["user"]
    alert_id = datos["a"]["alertas"][0].id
    _entrar(client, user)
    first = client.patch(f"/api/alerts/{alert_id}/acknowledge").json()
    assert first["state"] == "ACKNOWLEDGED"
    assert first["acknowledged_by_name"] == user.name
    assert first["resolution_minutes"] is None
    with Session(engine) as db:
        # Cierra AquaGuard (admin); el cliente solo dice «Me encargo».
        other = User(email="other-b5@example.com", name="Otro operador", role="admin", organization_id=None, password_hash="unused")
        db.add(other)
        db.commit()
        _entrar(client, other)
        other_id = other.id
    repeated = client.patch(f"/api/alerts/{alert_id}/acknowledge").json()
    assert repeated == first
    resolved = client.patch(f"/api/alerts/{alert_id}/resolve").json()
    assert resolved["resolved_by_name"] == "Otro operador"
    assert resolved["acknowledged_by_name"] == user.name
    assert resolved["state"] == "RESOLVED"
    assert resolved["resolution_minutes"] >= 0
    assert client.patch(f"/api/alerts/{alert_id}/resolve").status_code == 409
    with Session(engine) as db:
        alert = db.get(Alert, alert_id)
        assert alert.acknowledged_by == user.id
        assert alert.resolved_by == other_id
    direct_id = datos["a"]["alertas"][1].id
    direct = client.patch(f"/api/alerts/{direct_id}/resolve").json()
    assert direct["acknowledged_at"] is None
    assert direct["acknowledged_by_name"] is None
    after = client.patch(f"/api/alerts/{direct_id}/acknowledge").json()
    assert after["state"] == "RESOLVED"
    assert after["resolved_at"] == direct["resolved_at"]
    assert after["acknowledged_by_name"] == "Otro operador"


def test_nombres_duracion_e_historicos(client, datos, escenario, engine):
    _entrar(client, datos["a"]["user"])
    items = client.get("/api/alerts").json()["items"]
    resolved = next(i for i in items if i["state"] == "RESOLVED")
    assert resolved["resolution_minutes"] == 1.5
    assert resolved["resolved_by_name"] == datos["a"]["user"].name
    for key in ("organization_name", "site_name", "sensor_name", "floor"):
        assert key in resolved
    alert_id = datos["a"]["alertas"][1].id
    with Session(engine) as db:
        db.get(Alert, alert_id).acknowledged_by = None
        db.commit()
    body = client.patch(f"/api/alerts/{alert_id}/acknowledge").json()
    assert body["acknowledged_by_name"] is None


def test_carga_de_actores_no_crece_por_alerta(engine, datos, escenario):
    def count():
        statements = []
        def record(*args):
            statements.append(args[2])
        event.listen(engine, "before_cursor_execute", record)
        try:
            with Session(engine) as db:
                AlertService(db).list(None, 0, 100)
        finally:
            event.remove(engine, "before_cursor_execute", record)
        return len(statements)
    before = count()
    with Session(engine) as db:
        for i in range(10):
            actor = User(email=f"actor-{i}@example.com", name=f"Actor {i}", role="admin", password_hash="unused")
            db.add(actor)
            db.flush()
            db.add(Alert(sensor_id=datos["a"]["sensor"].id, alert_type="LOW_PRESSURE", severity="WARNING", status="RESOLVED", message="Histórica", acknowledged_at=escenario, acknowledged_by=actor.id, resolved_by=actor.id, resolved_at=escenario))
        db.commit()
    assert count() == before


def test_openapi_b5(client):
    spec = client.get("/api/openapi.json").json()
    params = {p["name"] for p in spec["paths"]["/api/alerts"]["get"]["parameters"]}
    assert {"severity", "state", "created_from", "created_to", "q", "organization_id", "site_id"} <= params
    fields = spec["components"]["schemas"]["AlertResponse"]["properties"]
    assert {"acknowledged_by_name", "resolved_by_name", "resolution_minutes"} <= fields.keys()


def test_orden_estable_si_coinciden_fechas(client, datos, escenario, engine):
    _entrar(client, datos["a"]["user"])
    with Session(engine) as db:
        for alert in datos["a"]["alertas"]:
            db.get(Alert, alert.id).created_at = escenario
        db.commit()
    expected = sorted((str(a.id) for a in datos["a"]["alertas"]), reverse=True)
    actual = []
    for page in range(1, 4):
        body = client.get("/api/alerts", params={"page_size": 1, "page": page}).json()
        assert body["total"] == 3
        actual.append(body["items"][0]["id"])
    assert actual == expected


def test_resuelta_sin_fecha_no_inventa_duracion(client, datos, engine):
    _entrar(client, datos["a"]["user"])
    with Session(engine) as db:
        alert = db.get(Alert, datos["a"]["alertas"][0].id)
        alert.status = "RESOLVED"
        alert.acknowledged_at = datetime(2026, 10, 12, tzinfo=timezone.utc)
        db.commit()
    item = client.get("/api/alerts", params={"state": "RESOLVED"}).json()["items"][0]
    assert item["state"] == "RESOLVED"
    assert item["resolved_at"] is None
    assert item["resolution_minutes"] is None
    assert item["resolved_by_name"] is None
