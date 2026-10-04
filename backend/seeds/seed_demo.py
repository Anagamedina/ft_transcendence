from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, transaction
from app.core.security import hash_password, verify_password

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


def _get_or_create_organization(db: Session, name: str) -> Organization:
    # Case-insensitive, same as the uq_organizations_name_lower index.
    organization = (
        db.query(Organization)
        .filter(func.lower(Organization.name) == name.lower())
        .one_or_none()
    )
    if organization is not None:
        return organization
    organization = Organization(name=name)
    db.add(organization)
    db.flush()
    return organization


def _get_or_create_user(
    db: Session,
    *,
    organization_id: UUID | None,
    email: str,
    name: str,
    password: str,
    role: str,
) -> User:
    user = db.query(User).filter_by(email=email).one_or_none()
    if user is not None:
        if user.name == "Migrated User":
            user.name = name
        if not verify_password(password, user.password_hash):
            user.password_hash = hash_password(password)
        user.organization_id = organization_id
        return user
    user = User(
        organization_id=organization_id,
        email=email,
        name=name,
        password_hash=hash_password(password),
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
    sensor_id: UUID,
    site_id: UUID,
    external_id: str,
    name: str,
    unit: str,
    low_threshold: Decimal,
    high_threshold: Decimal,
    location: str | None = None,
) -> Sensor:
    sensor = (
        db.query(Sensor)
        .filter_by(site_id=site_id, external_id=external_id)
        .one_or_none()
    )
    if sensor is not None:
        if sensor.location is None:
            sensor.location = location
        return sensor
    sensor = Sensor(
        id=sensor_id,
        site_id=site_id,
        external_id=external_id,
        name=name,
        location=location,
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
                organization_id=None,
                email="admin@aquaguard.dev",
                name="Demo Admin",
                password="dev-admin-only",
                role="admin",
            )
            _get_or_create_user(
                db,
                organization_id=organization.id,
                email="client@aquaguard.dev",
                name="Demo Client",
                password="dev-client-only",
                role="client",
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
                sensor_id=UUID("00000000-0000-4000-8000-000000000001"),
                site_id=site_hotel.id,
                external_id="SENS-001",
                name="Presión entrada",
                location="Sala técnica",
                unit="bar",
                low_threshold=Decimal("1.500"),
                high_threshold=Decimal("6.000"),
            )
            _get_or_create_sensor(
                db,
                sensor_id=UUID("00000000-0000-4000-8000-000000000002"),
                site_id=site_hotel.id,
                external_id="SENS-002",
                name="Presión salida",
                location="Cubierta",
                unit="bar",
                low_threshold=Decimal("1.000"),
                high_threshold=Decimal("5.500"),
            )
            _get_or_create_sensor(
                db,
                sensor_id=UUID("00000000-0000-4000-8000-000000000003"),
                site_id=site_office.id,
                external_id="SENS-003",
                name="Presión general",
                location="Sótano - Cuarto de bombas",
                unit="bar",
                low_threshold=Decimal("1.500"),
                high_threshold=Decimal("6.000"),
            )

        print(f"Seed OK — organization={organization.name!r} id={organization.id}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
