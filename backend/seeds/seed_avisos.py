"""
Demo data for the client notices (#275): one alert in each phase.

    make seed-avisos      (needs `make all` first: uses its clients and buildings)

Each case gets its own sensor ("Demo avisos · …"), because a sensor can have
only one open alert. The sensors send no readings, so the offline check
leaves them alone.

| Case | Alert | What the admin page shows |
|---|---|---|
| critica-nueva      | critical, 2 min ago, no notice      | «Aún no · en 3 min» |
| critica-1-aviso    | critical, 12 min, 1st email         | «1 aviso · el 2.º en 8 min» |
| critica-2-avisos   | critical, 32 min, 2 emails          | «2 avisos», call at 45 |
| critica-llamar     | critical, 55 min, 2 emails          | «2 avisos · llamar» (pink row) |
| leve-nueva         | leve, 25 min, no notice             | «Aún no · en 35 min» |
| leve-avisada       | leve, 75 min, 1 email               | «1 aviso», nothing more |
| critica-en-curso   | critical, 30 min, 1 email, taken    | En curso: «… se encarga» |
| leve-en-curso      | leve, 40 min, taken before any email| En curso, no notices |
| critica-arreglada  | critical, 2 h, 2 emails, closed     | Arregladas |

Rules:
- Idempotent: fixed ids. Running it again deletes these alerts (and their
  notices) and creates them again with times relative to now, so the
  phases are fresh. Nothing else in the database is touched.
- The backend keeps working on them: a minute later it may send the next
  email (Mailpit, http://localhost:8025), as it would for a real alert.
- Refuses to run with ENV=production.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID, uuid5

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core import models  # noqa: F401 - registers the ORM models
from app.core.app_config import app_settings
from app.core.database import SessionLocal, transaction
from app.modules.alerts.model import Alert, AlertNotification
from app.modules.organizations.model import Organization
from app.modules.sensors.model import Sensor
from app.modules.sites.model import Site
from app.modules.users.model import User

NAMESPACE = UUID("2f6c9a1e-7b3d-4e58-9c0a-275a1e2b3c4d")

# (key, site, floor, alert type, severity, minutes ago, emails sent at
#  these minutes, taken at minute, closed at minute)
CASES = [
    ("critica-nueva", "Hotel Gòtic Centro", 2, "LOW_PRESSURE", "CRITICAL", 2, [], None, None),
    ("critica-1-aviso", "Finca Mallorca 401", 3, "HIGH_PRESSURE", "CRITICAL", 12, [5], None, None),
    ("critica-2-avisos", "Residencia Sant Gervasi", 1, "LOW_PRESSURE", "CRITICAL", 32, [5, 20], None, None),
    ("critica-llamar", "Polideportivo Poblenou", 0, "SENSOR_OFFLINE", "CRITICAL", 55, [5, 20], None, None),
    ("leve-nueva", "Hotel Gòtic Centro", 4, "HIGH_PRESSURE", "WARNING", 25, [], None, None),
    ("leve-avisada", "Estación de bombeo Zona Franca", 0, "LOW_PRESSURE", "WARNING", 75, [60], None, None),
    ("critica-en-curso", "Residencia Gràcia", 2, "LOW_PRESSURE", "CRITICAL", 30, [5], 12, None),
    ("leve-en-curso", "Finca Mallorca 401", -1, "HIGH_PRESSURE", "WARNING", 40, [], 3, None),
    ("critica-arreglada", "Polideportivo Poblenou", 1, "HIGH_PRESSURE", "CRITICAL", 120, [5, 20], None, 40),
]

LOW, HIGH = Decimal("1.500"), Decimal("6.000")
MESSAGE = {
    "LOW_PRESSURE": f"Presión por debajo del umbral: 0.9 bar (mínimo {LOW.normalize()})",
    "HIGH_PRESSURE": f"Presión por encima del umbral: 6.6 bar (máximo {HIGH.normalize()})",
    "SENSOR_OFFLINE": "Sin lecturas desde hace más de 5 minutos",
}


def _id(kind: str, key: str) -> UUID:
    return uuid5(NAMESPACE, f"{kind}:{key}")


def _recipients(db: Session, organization: Organization, attempt: int) -> str:
    users = db.scalars(
        select(User.email)
        .where(User.organization_id == organization.id, User.role == "client")
        .order_by(User.email)
    ).all()
    contact = [organization.contact_email] if organization.contact_email else []
    if attempt == 1 and contact:
        return contact[0]
    return ", ".join(dict.fromkeys([*contact, *users]))


def seed() -> None:
    if app_settings.is_production:
        sys.exit("seed_avisos: refusing to run with ENV=production.")

    now = datetime.now(timezone.utc)
    db = SessionLocal()
    try:
        with transaction(db):
            db.execute(delete(Alert).where(Alert.id.in_([_id("alert", c[0]) for c in CASES])))

            for number, case in enumerate(CASES, start=1):
                key, site_name, floor, alert_type, severity, ago, emails, taken, closed = case
                site = db.scalar(select(Site).where(Site.name == site_name))
                if site is None:
                    sys.exit(f"seed_avisos: no existe el edificio «{site_name}». Ejecuta antes `make all`.")
                organization = db.get(Organization, site.organization_id)

                sensor = db.get(Sensor, _id("sensor", key))
                if sensor is None:
                    sensor = Sensor(id=_id("sensor", key))
                    db.add(sensor)
                sensor.site_id = site.id
                sensor.external_id = f"AVISO-{number:02d}"
                sensor.name = f"Demo avisos · {key.replace('-', ' ')}"
                sensor.sensor_type = "PRESSURE"
                sensor.unit = "bar"
                sensor.floor = floor
                sensor.low_threshold = LOW
                sensor.high_threshold = HIGH
                sensor.is_active = True
                db.flush()

                created = now - timedelta(minutes=ago)
                user = db.scalar(
                    select(User).where(User.organization_id == organization.id, User.role == "client")
                )
                admin = db.scalar(select(User).where(User.role == "admin"))
                alert = Alert(
                    id=_id("alert", key),
                    sensor_id=sensor.id,
                    alert_type=alert_type,
                    severity=severity,
                    message=MESSAGE[alert_type],
                    status="RESOLVED" if closed is not None else "ACTIVE",
                    created_at=created,
                    acknowledged_at=created + timedelta(minutes=taken) if taken is not None else None,
                    acknowledged_by=user.id if taken is not None and user else None,
                    resolved_at=created + timedelta(minutes=closed) if closed is not None else None,
                    resolved_by=admin.id if closed is not None and admin else None,
                )
                db.add(alert)
                db.flush()

                for attempt, minute in enumerate(emails, start=1):
                    db.add(AlertNotification(
                        alert_id=alert.id,
                        attempt=attempt,
                        channel="EMAIL",
                        recipient=_recipients(db, organization, attempt),
                        sent_at=created + timedelta(minutes=minute),
                    ))
    finally:
        db.close()

    print(f"seed_avisos: {len(CASES)} alertas de demo de avisos, con horas de ahora.")


if __name__ == "__main__":
    seed()
