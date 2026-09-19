import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import Base
from app.modules.alerts.model import Alert  # noqa: F401 - registers the ORM model
from app.modules.organizations.model import Organization
from app.modules.organizations.repository import OrganizationRepository
from app.modules.readings.model import Reading  # noqa: F401 - registers the ORM model
from app.modules.sensors.model import Sensor  # noqa: F401 - registers the ORM model
from app.modules.sites.model import Site  # noqa: F401 - registers the ORM model
from app.modules.users.model import User
from app.modules.users.repository import UserRepository


@pytest.fixture()
def db():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture()
def organization(db: Session) -> Organization:
    org = Organization(name="Org A")
    db.add(org)
    db.flush()
    return org


def test_create_user_and_get_by_email(db: Session, organization: Organization):
    repository = UserRepository(db)

    user = repository.create(
        organization_id=organization.id,
        email="  Someone@Example.COM ",
        password_hash="hashed",
        role="CLIENT",
    )
    db.commit()

    assert user.email == "someone@example.com"
    found = repository.get_by_email("someone@example.com")
    assert found is not None
    assert found.id == user.id

    # Búsqueda debe normalizar también mayúsculas/espacios de la query.
    found_variant = repository.get_by_email(" Someone@Example.com")
    assert found_variant is not None
    assert found_variant.id == user.id


def test_get_by_email_not_found_returns_none(db: Session):
    repository = UserRepository(db)
    assert repository.get_by_email("missing@example.com") is None


def test_get_by_id_is_scoped_to_organization(db: Session, organization: Organization):
    other_org = Organization(name="Org B")
    db.add(other_org)
    db.flush()

    repository = UserRepository(db)
    user = repository.create(
        organization_id=organization.id,
        email="scoped@example.com",
        password_hash="hashed",
        role="CLIENT",
    )
    db.commit()

    assert repository.get_by_id(user.id, organization.id) is user
    assert repository.get_by_id(user.id, other_org.id) is None


def test_duplicate_email_raises_integrity_error_and_rolls_back(
    db: Session, organization: Organization
):
    repository = UserRepository(db)
    repository.create(
        organization_id=organization.id,
        email="dup@example.com",
        password_hash="hashed",
        role="CLIENT",
    )
    db.commit()

    with pytest.raises(SQLAlchemyError):
        repository.create(
            organization_id=organization.id,
            email="dup@example.com",
            password_hash="hashed",
            role="CLIENT",
        )

    # La transacción quedó revertida: no hay una fila fantasma pendiente.
    db.rollback()
    found = repository.get_by_email("dup@example.com")
    assert found is not None


def test_organization_repository_get_by_id(db: Session, organization: Organization):
    repository = OrganizationRepository(db)

    assert repository.get_by_id(organization.id) is organization
    assert repository.get_by_id(organization.id).id == organization.id


def test_organization_repository_get_by_id_missing_returns_none(db: Session):
    import uuid

    repository = OrganizationRepository(db)
    assert repository.get_by_id(uuid.uuid4()) is None
