"""
Demo data for `make demo` and the evaluation (issue #131, D6).

Five clients in different situations, buildings with floors and real
coordinates, eight sensors (one offline, one out of range), 30 days of alerts
and readings, demo users and one pending invitation.

Rules:
- Idempotent. Every row is found by a fixed key (UUID, name, email or
  code_hash) and updated if it already exists, so running it twice leaves
  the same rows.
- Dates are relative to now and recalculated on every run, so "today" and
  "this week" always have data.
- Sensors are looked up by their fixed UUID: the simulator
  (SIMULATOR_SENSOR_IDS) and `make smoke` use those ids.
- Refuses to run with ENV=production: the demo passwords are public.
"""

from __future__ import annotations

import hashlib
import random
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID, uuid5

from sqlalchemy import delete, func
from sqlalchemy.orm import Session

from app.core import models  # noqa: F401 - registers the ORM models
from app.core.app_config import app_settings
from app.core.database import SessionLocal, transaction
from app.core.security import hash_password, verify_password
from app.modules.alerts.model import Alert
from app.modules.invitations.model import Invitation
from app.modules.organizations.model import Organization
from app.modules.readings.model import Reading
from app.modules.sensors.model import Sensor
from app.modules.sites.model import Site
from app.modules.users.model import User

# Namespace for the deterministic ids of alerts and readings (uuid5).
DEMO_NAMESPACE = UUID("6d1f3c2a-9b8e-4c7d-a1f0-5e2b8c9d0a11")

# The old seed created a single organization with this name. If it is still
# there, it is renamed to the first client instead of becoming a sixth one.
LEGACY_ORGANIZATION_NAME = "Demo"
LEGACY_SITE_NAMES = ("Hotel Mediterráneo", "Edificio Central")

TERMS_VERSION = "2026-09"

# Shown in the README: the invitation can be accepted with this code.
DEMO_INVITATION_CODE = "AQUAGUARD-DEMO-INVITE"


def _sensor_id(n: int) -> UUID:
    return UUID(f"00000000-0000-4000-8000-{n:012d}")


# ---------------------------------------------------------
# DATA
# ---------------------------------------------------------
ORGANIZATIONS = [
    {
        "name": "Residencias Alcalá",
        "status": "ACTIVE",
        "city": "Alcalá de Henares",
        "contact_email": "mantenimiento@residenciasalcala.es",
        "phone": "+34 918 802 140",
        "legal_name": "Residencias Alcalá S.L.",
        "tax_id": "B86412357",
        "billing_email": "facturacion@residenciasalcala.es",
    },
    {
        "name": "Hotel Turia",
        "status": "TRIAL",
        "trial_ends_in_days": 10,
        "city": "Valencia",
        "contact_email": "direccion@hotelturia.es",
        "phone": "+34 963 512 300",
        "legal_name": None,
        "tax_id": None,
        "billing_email": None,
    },
    {
        "name": "Comunidad Mallorca 401",
        "status": "ACTIVE",
        "city": "Barcelona",
        "contact_email": "admin@fincamallorca401.cat",
        "phone": "+34 934 581 220",
        "legal_name": "Comunidad de Propietarios Mallorca 401",
        "tax_id": "H08765432",
        "billing_email": "admin@fincamallorca401.cat",
    },
    {
        "name": "Polideportivo Abando",
        "status": "ACTIVE",
        "city": "Bilbao",
        "contact_email": "instalaciones@abandokirolak.eus",
        "phone": "+34 944 230 870",
        "legal_name": "Abando Kirolak S.A.",
        "tax_id": "A48123456",
        "billing_email": "contabilidad@abandokirolak.eus",
    },
    {
        "name": "Aguas del Sur",
        "status": "SUSPENDED",
        "city": "Sevilla",
        "contact_email": "operaciones@aguasdelsur.es",
        "phone": "+34 954 610 455",
        "legal_name": "Aguas del Sur Gestión Hídrica S.L.",
        "tax_id": "B41987654",
        "billing_email": "pagos@aguasdelsur.es",
    },
]

SITES = [
    {
        "key": "cervantes",
        "organization": "Residencias Alcalá",
        "name": "Residencia Cervantes",
        "address": "Calle de Santiago 12, 28801 Alcalá de Henares",
        "latitude": Decimal("40.482600"),
        "longitude": Decimal("-3.364300"),
        "floors": 4,
        "basements": 1,
        "building_type": "RESIDENCE",
    },
    {
        "key": "san_diego",
        "organization": "Residencias Alcalá",
        "name": "Residencia San Diego",
        "address": "Plaza de San Diego 3, 28801 Alcalá de Henares",
        "latitude": Decimal("40.483900"),
        "longitude": Decimal("-3.361200"),
        "floors": 3,
        "basements": 0,
        "building_type": "RESIDENCE",
    },
    {
        "key": "turia",
        "organization": "Hotel Turia",
        "name": "Hotel Turia Centro",
        "address": "Carrer de la Pau 18, 46002 València",
        "latitude": Decimal("39.473800"),
        "longitude": Decimal("-0.374900"),
        "floors": 8,
        "basements": 2,
        "building_type": "HOTEL",
    },
    {
        "key": "mallorca",
        "organization": "Comunidad Mallorca 401",
        "name": "Finca Mallorca 401",
        "address": "Carrer de Mallorca 401, 08013 Barcelona",
        "latitude": Decimal("41.403600"),
        "longitude": Decimal("2.174400"),
        "floors": 7,
        "basements": 1,
        "building_type": "COMMUNITY",
    },
    {
        "key": "abando",
        "organization": "Polideportivo Abando",
        "name": "Polideportivo Abando",
        "address": "Calle de Hurtado de Amézaga 6, 48008 Bilbao",
        "latitude": Decimal("43.260700"),
        "longitude": Decimal("-2.927800"),
        "floors": 2,
        "basements": 1,
        "building_type": "SPORTS",
    },
    {
        "key": "bombeo",
        "organization": "Aguas del Sur",
        "name": "Estación de bombeo La Cartuja",
        "address": "Calle Américo Vespucio 5, 41092 Sevilla",
        "latitude": Decimal("37.409300"),
        "longitude": Decimal("-6.004500"),
        "floors": 1,
        "basements": 1,
        "building_type": "INDUSTRIAL",
    },
]

# The first three keep the ids that the simulator and the smoke test use.
#
# Two sensors have a story:
# - 6 (Abando) is OUT OF RANGE: its upper threshold is 2.0 bar and the
#   simulator's normal scenario sends 2.5-4.5 bar, so every reading stays
#   above it without changing the simulator.
# - 7 (Aguas del Sur) is OFFLINE: it is not in SIMULATOR_SENSOR_IDS and its
#   last reading is OFFLINE_SINCE old.
SENSORS = [
    {"n": 1, "site": "cervantes", "external_id": "SENS-001", "name": "Presión entrada",
     "location": "Sótano - Sala de bombas", "floor": -1, "low": "1.500", "high": "6.000"},
    {"n": 2, "site": "cervantes", "external_id": "SENS-002", "name": "Presión cubierta",
     "location": "Cubierta - Depósito", "floor": 4, "low": "1.000", "high": "5.500"},
    {"n": 3, "site": "turia", "external_id": "SENS-003", "name": "Presión general",
     "location": "Sótano 2 - Cuarto de bombas", "floor": -2, "low": "1.500", "high": "6.000"},
    {"n": 4, "site": "turia", "external_id": "SENS-004", "name": "Presión planta 6",
     "location": "Planta 6 - Office", "floor": 6, "low": "1.500", "high": "6.000"},
    {"n": 5, "site": "mallorca", "external_id": "SENS-005", "name": "Presión acometida",
     "location": "Portería - Contador general", "floor": 0, "low": "1.500", "high": "6.000"},
    {"n": 6, "site": "abando", "external_id": "SENS-006", "name": "Presión vestuarios",
     "location": "Sótano - Vestuarios", "floor": -1, "low": "0.500", "high": "2.000"},
    {"n": 7, "site": "bombeo", "external_id": "SENS-007", "name": "Presión impulsión",
     "location": "Nave de bombeo", "floor": 0, "low": "1.500", "high": "8.000"},
    {"n": 8, "site": "san_diego", "external_id": "SENS-008", "name": "Presión cocina",
     "location": "Planta 1 - Cocina", "floor": 1, "low": "1.500", "high": "6.000"},
]

OUT_OF_RANGE_SENSOR = 6
OFFLINE_SENSOR = 7
OFFLINE_SINCE = timedelta(hours=3)

# Passwords are for development only (see the README).
USERS = [
    {"email": "admin@aquaguard.dev", "name": "Demo Admin", "role": "admin",
     "organization": None, "password": "dev-admin-only", "last_login_hours": 1},
    {"email": "client@aquaguard.dev", "name": "Lucía Martín", "role": "client",
     "organization": "Residencias Alcalá", "password": "dev-client-only", "last_login_hours": 2},
    {"email": "hotel@aquaguard.dev", "name": "Javier Soler", "role": "client",
     "organization": "Hotel Turia", "password": "dev-client-only", "last_login_hours": 20},
    {"email": "comunidad@aquaguard.dev", "name": "Montse Puig", "role": "client",
     "organization": "Comunidad Mallorca 401", "password": "dev-client-only", "last_login_hours": 72},
    {"email": "abando@aquaguard.dev", "name": "Iker Etxeberria", "role": "client",
     "organization": "Polideportivo Abando", "password": "dev-client-only", "last_login_hours": 5},
    # Suspended client: the account exists but is disabled.
    {"email": "aguasdelsur@aquaguard.dev", "name": "Rocío Navarro", "role": "client",
     "organization": "Aguas del Sur", "password": "dev-client-only", "last_login_hours": 24 * 25,
     "is_active": False},
]

INVITATION = {
    "organization": "Residencias Alcalá",
    "email": "nuevo.gestor@residenciasalcala.es",
    "expires_in_days": 7,
}

# Alerts of the last 30 days: 19 in total, 16 resolved and 3 active.
# ago = how long ago it was created; ack / resolved = minutes after creation;
# by = email of who acknowledged and resolved it.
ALERTS = [
    # Active
    {"key": "a01", "sensor": OUT_OF_RANGE_SENSOR, "type": "HIGH_PRESSURE", "severity": "CRITICAL",
     "ago": timedelta(hours=2), "ack": 15, "resolved": None, "by": "abando@aquaguard.dev"},
    {"key": "a02", "sensor": OFFLINE_SENSOR, "type": "SENSOR_OFFLINE", "severity": "CRITICAL",
     "ago": OFFLINE_SINCE - timedelta(minutes=5), "ack": None, "resolved": None, "by": None},
    {"key": "a03", "sensor": 4, "type": "LOW_PRESSURE", "severity": "WARNING",
     "ago": timedelta(days=1, hours=4), "ack": 40, "resolved": None, "by": "hotel@aquaguard.dev"},
    # Resolved
    {"key": "r01", "sensor": 1, "type": "LOW_PRESSURE", "severity": "WARNING",
     "ago": timedelta(hours=6), "ack": 10, "resolved": 55, "by": "client@aquaguard.dev"},
    {"key": "r02", "sensor": 5, "type": "HIGH_PRESSURE", "severity": "WARNING",
     "ago": timedelta(days=1, hours=9), "ack": 25, "resolved": 120, "by": "comunidad@aquaguard.dev"},
    {"key": "r03", "sensor": 3, "type": "SENSOR_OFFLINE", "severity": "CRITICAL",
     "ago": timedelta(days=2, hours=3), "ack": 5, "resolved": 35, "by": "hotel@aquaguard.dev"},
    {"key": "r04", "sensor": 2, "type": "LOW_PRESSURE", "severity": "CRITICAL",
     "ago": timedelta(days=3, hours=11), "ack": 8, "resolved": 90, "by": "client@aquaguard.dev"},
    {"key": "r05", "sensor": 6, "type": "HIGH_PRESSURE", "severity": "WARNING",
     "ago": timedelta(days=4, hours=2), "ack": 30, "resolved": 240, "by": "abando@aquaguard.dev"},
    {"key": "r06", "sensor": 8, "type": "HIGH_PRESSURE", "severity": "WARNING",
     "ago": timedelta(days=5, hours=7), "ack": 20, "resolved": 75, "by": "client@aquaguard.dev"},
    {"key": "r07", "sensor": 7, "type": "LOW_PRESSURE", "severity": "WARNING",
     "ago": timedelta(days=7, hours=1), "ack": 60, "resolved": 300, "by": "aguasdelsur@aquaguard.dev"},
    {"key": "r08", "sensor": 4, "type": "SENSOR_OFFLINE", "severity": "CRITICAL",
     "ago": timedelta(days=9, hours=5), "ack": 12, "resolved": 50, "by": "admin@aquaguard.dev"},
    {"key": "r09", "sensor": 1, "type": "HIGH_PRESSURE", "severity": "CRITICAL",
     "ago": timedelta(days=11, hours=8), "ack": 6, "resolved": 45, "by": "client@aquaguard.dev"},
    {"key": "r10", "sensor": 5, "type": "LOW_PRESSURE", "severity": "WARNING",
     "ago": timedelta(days=13, hours=4), "ack": 35, "resolved": 180, "by": "comunidad@aquaguard.dev"},
    {"key": "r11", "sensor": 3, "type": "HIGH_PRESSURE", "severity": "WARNING",
     "ago": timedelta(days=16, hours=10), "ack": 18, "resolved": 95, "by": "hotel@aquaguard.dev"},
    {"key": "r12", "sensor": 7, "type": "SENSOR_OFFLINE", "severity": "CRITICAL",
     "ago": timedelta(days=19, hours=2), "ack": 45, "resolved": 600, "by": "admin@aquaguard.dev"},
    {"key": "r13", "sensor": 8, "type": "LOW_PRESSURE", "severity": "WARNING",
     "ago": timedelta(days=22, hours=6), "ack": 22, "resolved": 70, "by": "client@aquaguard.dev"},
    {"key": "r14", "sensor": 2, "type": "HIGH_PRESSURE", "severity": "WARNING",
     "ago": timedelta(days=25, hours=3), "ack": 28, "resolved": 110, "by": "client@aquaguard.dev"},
    {"key": "r15", "sensor": 6, "type": "LOW_PRESSURE", "severity": "CRITICAL",
     "ago": timedelta(days=27, hours=9), "ack": 9, "resolved": 40, "by": "abando@aquaguard.dev"},
    {"key": "r16", "sensor": 5, "type": "SENSOR_OFFLINE", "severity": "CRITICAL",
     "ago": timedelta(days=29, hours=5), "ack": 50, "resolved": 200, "by": "admin@aquaguard.dev"},
]

ALERT_MESSAGES = {
    "LOW_PRESSURE": "Presión por debajo del umbral inferior ({low} bar)",
    "HIGH_PRESSURE": "Presión por encima del umbral superior ({high} bar)",
    "SENSOR_OFFLINE": "El sensor no envía lecturas (más de 5 minutos)",
}

# One reading every READING_STEP over the last READING_DAYS, per sensor.
READING_DAYS = 7
READING_STEP = timedelta(hours=1)


# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------
def abort_in_production() -> None:
    if app_settings.is_production:
        sys.exit(
            "seed_demo: refusing to run with ENV=production. "
            "The demo users have public passwords."
        )


def _find_organization(db: Session, name: str) -> Organization | None:
    # Case-insensitive, same as the uq_organizations_name_lower index.
    return (
        db.query(Organization)
        .filter(func.lower(Organization.name) == name.lower())
        .one_or_none()
    )


def _upsert_organization(db: Session, data: dict, now: datetime) -> Organization:
    organization = _find_organization(db, data["name"])
    if organization is None:
        legacy = _find_organization(db, LEGACY_ORGANIZATION_NAME)
        if legacy is not None and data["name"] == ORGANIZATIONS[0]["name"]:
            organization = legacy
            organization.name = data["name"]
        else:
            organization = Organization(name=data["name"])
            db.add(organization)

    organization.status = data["status"]
    trial_days = data.get("trial_ends_in_days")
    organization.trial_ends_at = now + timedelta(days=trial_days) if trial_days else None
    for field in ("city", "contact_email", "phone", "legal_name", "tax_id", "billing_email"):
        setattr(organization, field, data[field])
    db.flush()
    return organization


def _upsert_user(
    db: Session, data: dict, organization_id: UUID | None, now: datetime
) -> User:
    user = db.query(User).filter_by(email=data["email"]).one_or_none()
    if user is None:
        user = User(
            email=data["email"],
            password_hash=hash_password(data["password"]),
        )
        db.add(user)
    elif not verify_password(data["password"], user.password_hash):
        user.password_hash = hash_password(data["password"])

    user.name = data["name"]
    user.role = data["role"]
    user.organization_id = organization_id
    user.is_active = data.get("is_active", True)
    user.last_login_at = now - timedelta(hours=data["last_login_hours"])
    user.terms_version = TERMS_VERSION
    user.terms_accepted_at = now - timedelta(days=60)
    db.flush()
    return user


def _upsert_site(db: Session, data: dict, organization_id: UUID) -> Site:
    site = (
        db.query(Site)
        .filter_by(organization_id=organization_id, name=data["name"])
        .one_or_none()
    )
    if site is None:
        site = Site(organization_id=organization_id, name=data["name"])
        db.add(site)
    for field in ("address", "latitude", "longitude", "floors", "basements", "building_type"):
        setattr(site, field, data[field])
    db.flush()
    return site


def _upsert_sensor(db: Session, data: dict, site_id: UUID) -> Sensor:
    sensor = db.get(Sensor, _sensor_id(data["n"]))
    if sensor is None:
        sensor = Sensor(id=_sensor_id(data["n"]))
        db.add(sensor)
    sensor.site_id = site_id
    sensor.external_id = data["external_id"]
    sensor.name = data["name"]
    sensor.location = data["location"]
    sensor.floor = data["floor"]
    sensor.sensor_type = "PRESSURE"
    sensor.unit = "bar"
    sensor.low_threshold = Decimal(data["low"])
    sensor.high_threshold = Decimal(data["high"])
    sensor.is_active = True
    return sensor


def _remove_empty_legacy_sites(db: Session, organization_id: UUID) -> None:
    """The old seed's sites, once their sensors have moved to the new ones."""
    for name in LEGACY_SITE_NAMES:
        site = (
            db.query(Site)
            .filter_by(organization_id=organization_id, name=name)
            .one_or_none()
        )
        if site is not None and not site.sensors:
            db.delete(site)
    db.flush()


def _upsert_alert(
    db: Session, data: dict, sensor: Sensor, users: dict[str, User], now: datetime
) -> None:
    alert_id = uuid5(DEMO_NAMESPACE, f"alert:{data['key']}")
    alert = db.get(Alert, alert_id)
    if alert is None:
        alert = Alert(id=alert_id)
        db.add(alert)

    created_at = now - data["ago"]
    actor = users[data["by"]].id if data["by"] else None
    alert.sensor_id = sensor.id
    alert.alert_type = data["type"]
    alert.severity = data["severity"]
    alert.message = ALERT_MESSAGES[data["type"]].format(
        low=sensor.low_threshold, high=sensor.high_threshold
    )
    alert.created_at = created_at
    alert.status = "RESOLVED" if data["resolved"] is not None else "ACTIVE"
    alert.acknowledged_at = (
        created_at + timedelta(minutes=data["ack"]) if data["ack"] is not None else None
    )
    alert.acknowledged_by = actor if data["ack"] is not None else None
    alert.resolved_at = (
        created_at + timedelta(minutes=data["resolved"])
        if data["resolved"] is not None
        else None
    )
    alert.resolved_by = actor if data["resolved"] is not None else None


def _resolve_stray_active_alerts(
    db: Session, sensor_ids: list[UUID], admin_id: UUID, now: datetime
) -> None:
    """
    Alerts never resolve themselves. An ACTIVE alert on a demo sensor that is
    not one of ALERTS (for example SENSOR_OFFLINE opened while the stack was
    stopped) would stay forever, so the demo would not show its 3 active ones.
    """
    demo_ids = [uuid5(DEMO_NAMESPACE, f"alert:{data['key']}") for data in ALERTS]
    stray = (
        db.query(Alert)
        .filter(
            Alert.sensor_id.in_(sensor_ids),
            Alert.status == "ACTIVE",
            Alert.id.not_in(demo_ids),
        )
        .all()
    )
    for alert in stray:
        alert.status = "RESOLVED"
        alert.resolved_at = now
        alert.resolved_by = admin_id


def _reading_value(rng: random.Random, sensor_n: int) -> Decimal:
    if sensor_n == OUT_OF_RANGE_SENSOR:
        value = rng.uniform(2.4, 3.2)  # above its 2.0 bar threshold
    else:
        value = min(max(rng.gauss(3.5, 0.3), 2.2), 4.8)
    return Decimal(f"{value:.3f}")


def _replace_readings(db: Session, now: datetime) -> int:
    """
    Hourly readings of the last week for every sensor. Their ids are
    deterministic, so a new run deletes the previous ones and writes them
    again with fresh dates. Readings from the simulator are not touched.
    """
    steps = int(timedelta(days=READING_DAYS) / READING_STEP)
    rows = []
    for data in SENSORS:
        rng = random.Random(data["n"])
        # Down to step 0 (now): connected sensors stay ONLINE until the
        # simulator sends its first reading.
        for step in range(steps, -1, -1):
            moment = now - step * READING_STEP
            if data["n"] == OFFLINE_SENSOR and now - moment < OFFLINE_SINCE:
                continue  # offline: nothing in the last OFFLINE_SINCE
            rows.append(
                {
                    "id": uuid5(DEMO_NAMESPACE, f"reading:{data['n']}:{step}"),
                    "sensor_id": _sensor_id(data["n"]),
                    "value": _reading_value(rng, data["n"]),
                    "unit": "bar",
                    "recorded_at": moment,
                    # The offline rule counts when the reading arrived.
                    "created_at": moment,
                }
            )

    db.execute(delete(Reading).where(Reading.id.in_([row["id"] for row in rows])))
    db.execute(Reading.__table__.insert(), rows)
    return len(rows)


def _upsert_invitation(
    db: Session, organization_id: UUID, created_by: UUID, now: datetime
) -> None:
    code_hash = hashlib.sha256(DEMO_INVITATION_CODE.encode()).hexdigest()
    invitation = db.query(Invitation).filter_by(code_hash=code_hash).one_or_none()
    if invitation is None:
        invitation = Invitation(code_hash=code_hash)
        db.add(invitation)
    # Pending again on every run, even if it was accepted or revoked.
    invitation.organization_id = organization_id
    invitation.email = INVITATION["email"].lower()
    invitation.created_by = created_by
    invitation.created_at = now - timedelta(days=1)
    invitation.expires_at = now + timedelta(days=INVITATION["expires_in_days"])
    invitation.accepted_at = None
    invitation.revoked_at = None


# ---------------------------------------------------------
# SEED
# ---------------------------------------------------------
def seed() -> None:
    abort_in_production()
    now = datetime.now(timezone.utc)

    db = SessionLocal()
    try:
        with transaction(db):
            organizations = {
                data["name"]: _upsert_organization(db, data, now)
                for data in ORGANIZATIONS
            }

            users = {
                data["email"]: _upsert_user(
                    db,
                    data,
                    organizations[data["organization"]].id
                    if data["organization"]
                    else None,
                    now,
                )
                for data in USERS
            }

            sites = {
                data["key"]: _upsert_site(
                    db, data, organizations[data["organization"]].id
                )
                for data in SITES
            }

            sensors = {
                data["n"]: _upsert_sensor(db, data, sites[data["site"]].id)
                for data in SENSORS
            }
            db.flush()
            _remove_empty_legacy_sites(db, organizations[ORGANIZATIONS[0]["name"]].id)

            for data in ALERTS:
                _upsert_alert(db, data, sensors[data["sensor"]], users, now)
            db.flush()
            _resolve_stray_active_alerts(
                db,
                [sensor.id for sensor in sensors.values()],
                users["admin@aquaguard.dev"].id,
                now,
            )

            readings = _replace_readings(db, now)

            _upsert_invitation(
                db,
                organizations[INVITATION["organization"]].id,
                users["admin@aquaguard.dev"].id,
                now,
            )

        print(
            f"Seed OK — {len(organizations)} organizations, {len(sites)} sites, "
            f"{len(sensors)} sensors, {len(ALERTS)} alerts, {readings} readings, "
            f"{len(users)} users, 1 pending invitation"
        )
    finally:
        db.close()


if __name__ == "__main__":
    seed()
