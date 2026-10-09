"""
Invitations table (D3, issue #130).

Runs on SQLite with foreign keys switched on, so ON DELETE CASCADE and
SET NULL behave as in PostgreSQL. The PostgreSQL side (migration
edcf330361ab) is covered by `make migration-check`.
"""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core import models  # noqa: F401 - registers the ORM models
from app.core.database import Base
from app.modules.invitations.model import Invitation
from app.modules.organizations.model import Organization
from app.modules.users.model import User


@pytest.fixture()
def db():
    engine = create_engine("sqlite+pysqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def _foreign_keys_on(dbapi_connection, _record):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture()
def org(db: Session) -> Organization:
    org = Organization(name="Org A")
    db.add(org)
    db.flush()
    return org


def _invitation(org_id, email="ana@example.com", code_hash="hash-1", **extra):
    return Invitation(
        organization_id=org_id,
        email=email,
        code_hash=code_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        **extra,
    )


def test_a_new_invitation_is_pending(db: Session, org: Organization):
    invitation = _invitation(org.id)
    db.add(invitation)
    db.flush()
    db.refresh(invitation)

    assert invitation.id is not None
    assert invitation.created_at is not None
    assert invitation.accepted_at is None
    assert invitation.revoked_at is None


def test_code_hash_is_unique(db: Session, org: Organization):
    db.add(_invitation(org.id, email="a@example.com", code_hash="same"))
    db.add(_invitation(org.id, email="b@example.com", code_hash="same"))
    with pytest.raises(IntegrityError):
        db.flush()


def test_only_one_pending_invitation_per_email_and_organization(
    db: Session, org: Organization
):
    db.add(_invitation(org.id, code_hash="hash-1"))
    db.add(_invitation(org.id, code_hash="hash-2"))
    with pytest.raises(IntegrityError):
        db.flush()


def test_the_same_email_can_be_pending_in_another_organization(
    db: Session, org: Organization
):
    other = Organization(name="Org B")
    db.add(other)
    db.flush()

    db.add(_invitation(org.id, code_hash="hash-1"))
    db.add(_invitation(other.id, code_hash="hash-2"))
    db.flush()


@pytest.mark.parametrize("ended", ["accepted_at", "revoked_at"])
def test_after_accepting_or_revoking_a_new_one_can_be_sent(
    db: Session, org: Organization, ended: str
):
    db.add(
        _invitation(org.id, code_hash="hash-1", **{ended: datetime.now(timezone.utc)})
    )
    db.add(_invitation(org.id, code_hash="hash-2"))
    db.flush()


def test_email_must_be_lowercase(db: Session, org: Organization):
    db.add(_invitation(org.id, email="Ana@Example.com"))
    with pytest.raises(IntegrityError):
        db.flush()


def test_cannot_be_accepted_and_revoked(db: Session, org: Organization):
    now = datetime.now(timezone.utc)
    db.add(_invitation(org.id, accepted_at=now, revoked_at=now))
    with pytest.raises(IntegrityError):
        db.flush()


def test_deleting_the_organization_deletes_its_invitations(
    db: Session, org: Organization
):
    db.add(_invitation(org.id))
    db.flush()

    db.delete(org)
    db.flush()

    assert db.scalars(select(Invitation)).all() == []


def test_deleting_the_creator_keeps_the_invitation(db: Session, org: Organization):
    admin = User(
        organization_id=org.id,
        email="admin@example.com",
        name="Admin",
        password_hash="hashed",
        role="admin",
    )
    db.add(admin)
    db.flush()
    invitation = _invitation(org.id, created_by=admin.id)
    db.add(invitation)
    db.flush()

    db.delete(admin)
    db.flush()
    db.refresh(invitation)

    assert invitation.created_by is None
