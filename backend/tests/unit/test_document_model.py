"""
Documents table (D4, issue #132).

Runs on SQLite with foreign keys switched on, so ON DELETE CASCADE and
SET NULL behave as in PostgreSQL. The PostgreSQL side (migration
81bfe9714e30) is covered by `make migration-check`.
"""

import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core import models  # noqa: F401 - registers the ORM models
from app.core.database import Base
from app.modules.documents.model import Document
from app.modules.organizations.model import Organization
from app.modules.sites.model import Site
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
def site(db: Session) -> Site:
    org = Organization(name="Org A")
    db.add(org)
    db.flush()
    site = Site(organization_id=org.id, name="Edificio A")
    db.add(site)
    db.flush()
    return site


def _document(site: Site, storage_key="sites/a/plano.pdf", **extra):
    data = {
        "organization_id": site.organization_id,
        "site_id": site.id,
        "kind": "PLAN",
        "filename": "plano.pdf",
        "content_type": "application/pdf",
        "size": 1024,
        "storage_key": storage_key,
        **extra,
    }
    return Document(**data)


def test_a_document_is_stored_with_its_metadata(db: Session, site: Site):
    document = _document(site)
    db.add(document)
    db.flush()
    db.refresh(document)

    assert document.id is not None
    assert document.created_at is not None
    assert document.uploaded_by is None


@pytest.mark.parametrize("kind", ["PLAN", "REPORT", "INVOICE", "PHOTO", "OTHER"])
def test_every_kind_of_the_contract_is_accepted(db: Session, site: Site, kind: str):
    db.add(_document(site, kind=kind))
    db.flush()


def test_a_kind_outside_the_list_is_rejected(db: Session, site: Site):
    db.add(_document(site, kind="CONTRACT"))
    with pytest.raises(IntegrityError):
        db.flush()


def test_size_cannot_be_negative(db: Session, site: Site):
    db.add(_document(site, size=-1))
    with pytest.raises(IntegrityError):
        db.flush()


def test_size_fits_files_bigger_than_2_gb(db: Session, site: Site):
    document = _document(site, size=3 * 1024**3)
    db.add(document)
    db.flush()
    db.refresh(document)

    assert document.size == 3 * 1024**3


def test_storage_key_is_unique(db: Session, site: Site):
    db.add(_document(site, storage_key="same"))
    db.add(_document(site, storage_key="same"))
    with pytest.raises(IntegrityError):
        db.flush()


def test_deleting_the_site_deletes_its_documents(db: Session, site: Site):
    db.add_all([_document(site, storage_key="k1"), _document(site, storage_key="k2")])
    db.flush()

    db.delete(site)
    db.flush()

    assert db.scalars(select(Document)).all() == []


def test_an_organization_with_sites_cannot_be_deleted(db: Session, site: Site):
    """
    documents -> organizations is CASCADE, but sites -> organizations is
    RESTRICT: an organization with buildings is not deleted, documents
    included. Its documents go away when its sites do.
    """
    db.add(_document(site))
    db.flush()

    db.delete(db.get(Organization, site.organization_id))
    with pytest.raises(IntegrityError):
        db.flush()


def test_deleting_the_uploader_keeps_the_document(db: Session, site: Site):
    user = User(
        organization_id=site.organization_id,
        email="lucia@example.com",
        name="Lucía",
        password_hash="hashed",
        role="client",
    )
    db.add(user)
    db.flush()
    document = _document(site, uploaded_by=user.id)
    db.add(document)
    db.flush()

    db.delete(user)
    db.flush()
    db.refresh(document)

    assert document.uploaded_by is None
