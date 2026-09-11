# SEED DEMO — datos iniciales deterministas (org, site, sensor, user demo).
# Ejecutar tras migraciones para demos reproducibles.
"""
Seed de desarrollo — issue #15.

Objetivo: dejar una base recién migrada con datos suficientes para el
vertical slice (org, usuarios, sites, sensores) sin insertar nada a mano.

Diseño: cada entidad se busca por su clave natural antes
de crearla (nombre de organización, email de usuario, nombre de site
dentro de la organización, external_id de sensor dentro del site).
Ejecutarlo dos veces deja el mismo resultado, no datos duplicados.

Todo ocurre en una única transacción (ver `transaction()` en
`app.core.database`): si algo falla a mitad, se hace rollback completo y
no queda un estado parcial.

Uso, desde `backend/` y con las migraciones ya aplicadas:

    python -m seeds.seed_demo
"""

from __future__ import annotations

import hashlib
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.database import SessionLocal, transaction

# Importados para registrar sus modelos en el mapper de SQLAlchemy:
# Sensor referencia "Reading" y "Alert" como relaciones, y esas clases
# tienen que estar cargadas antes de que se resuelva esa relación.
from app.modules.alerts import model as _alerts_model  # noqa: F401
from app.modules.readings import model as _readings_model  # noqa: F401

from app.modules.organizations.model import Organization
from app.modules.sensors.model import Sensor
from app.modules.sites.model import Site
from app.modules.users.model import User

ORGANIZATION_NAME = "Demo"


def _placeholder_password_hash(password: str) -> str:
    """
    Hash de marcador de posición — SOLO para datos de desarrollo.

    Todavía no existe un hasher real: `app/core/security.py`
    Usamos sha256 de la librería estándar porque es determinista y no añade una dependencia nueva antes
    de que se decida cuál usar en producción (Argon2/bcrypt).

    Cuando #26 aporte el hasher definitivo.
    ejecutar el seed - estos usuarios habrá que recrearlos, ya que este hash no es compatible con un verificador real.
    """
    return "seed-sha256$" + hashlib.sha256(password.encode("utf-8")).hexdigest()


def _get_or_create_organization(db: Session, name: str) -> Organization:
    organization = db.query(Organization).filter_by(name=name).one_or_none()
    if organization is not None:
        return organization
    organization = Organization(name=name)
    db.add(organization)
    db.flush()
    return organization


def _get_or_create_user(
    db: Session,
    *,
    organization_id: UUID,
    email: str,
    password: str,
    role: str,
) -> User:
    user = db.query(User).filter_by(email=email).one_or_none()
    if user is not None:
        return user
    user = User(
        organization_id=organization_id,
        email=email,
        password_hash=_placeholder_password_hash(password),
        role=role,
    )
    db.add(user)
    db.flush()
    return user


def _get_or_create_site(
    db: Session,
    *,
    organization_id: UUID,
    name: str,
    address: str | None = None,
    latitude: Decimal | None = None,
    longitude: Decimal | None = None,
) -> Site:
    site = (
        db.query(Site)
        .filter_by(organization_id=organization_id, name=name)
        .one_or_none()
    )
    if site is not None:
        return site
    site = Site(
        organization_id=organization_id,
        name=name,
        address=address,
        latitude=latitude,
        longitude=longitude,
    )
    db.add(site)
    db.flush()
    return site


def _get_or_create_sensor(
    db: Session,
    *,
    site_id: UUID,
    external_id: str,
    name: str,
    unit: str,
    low_threshold: Decimal | None = None,
    high_threshold: Decimal | None = None,
) -> Sensor:
    sensor = (
        db.query(Sensor)
        .filter_by(site_id=site_id, external_id=external_id)
        .one_or_none()
    )
    if sensor is not None:
        return sensor
    sensor = Sensor(
        site_id=site_id,
        external_id=external_id,
        name=name,
        unit=unit,
        low_threshold=low_threshold,
        high_threshold=high_threshold,
    )
    db.add(sensor)
    db.flush()
    return sensor


def seed() -> None:
    db = SessionLocal()
    try:
        with transaction(db):
            organization = _get_or_create_organization(db, ORGANIZATION_NAME)

            _get_or_create_user(
                db,
                organization_id=organization.id,
                email="admin@aquaguard.dev",
                password="dev-admin-only",
                role="ADMIN",
            )
            _get_or_create_user(
                db,
                organization_id=organization.id,
                email="client@aquaguard.dev",
                password="dev-client-only",
                role="CLIENT",
            )

            site_hotel = _get_or_create_site(
                db,
                organization_id=organization.id,
                name="Hotel Mediterráneo",
                address="Passeig Marítim 12, Barcelona",
                latitude=Decimal("41.385000"),
                longitude=Decimal("2.190000"),
            )
            site_office = _get_or_create_site(
                db,
                organization_id=organization.id,
                name="Edificio Central",
                address="Calle Mayor 4, Madrid",
                latitude=Decimal("40.416900"),
                longitude=Decimal("-3.703800"),
            )

            _get_or_create_sensor(
                db,
                site_id=site_hotel.id,
                external_id="SENS-001",
                name="Presión entrada",
                unit="bar",
                low_threshold=Decimal("1.500"),
                high_threshold=Decimal("6.000"),
            )
            _get_or_create_sensor(
                db,
                site_id=site_hotel.id,
                external_id="SENS-002",
                name="Presión salida",
                unit="bar",
                low_threshold=Decimal("1.000"),
                high_threshold=Decimal("5.500"),
            )
            _get_or_create_sensor(
                db,
                site_id=site_office.id,
                external_id="SENS-003",
                name="Presión general",
                unit="bar",
                low_threshold=Decimal("1.500"),
                high_threshold=Decimal("6.000"),
            )

        print(f"Seed OK — organization={organization.name!r} id={organization.id}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
