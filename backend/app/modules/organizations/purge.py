# PURGE — organizations
# Deletes an organization and everything that hangs from it (issue #133, D9).
"""
`purge_organization(db, organization_id)` deletes an organization with all
its data. Used by B16 (DELETE endpoint, Ana); to *disable* a client, use
`status = 'SUSPENDED'` instead.

--------------------------------------------------------------------
WHY EXPLICIT DELETES AND NOT CASCADE
--------------------------------------------------------------------
Most foreign keys are RESTRICT on purpose: a stray `DELETE FROM sites`
must not take months of readings with it. They stay that way, and this
function is the only path that deletes a whole organization. Table by
table:

    readings     RESTRICT  explicit, one set-based DELETE (can be many rows;
                           never loaded into Python, uses ix_readings_sensor_recorded_at)
    alerts       RESTRICT  explicit
    sensors      RESTRICT  explicit
    documents    CASCADE   explicit anyway, so the counts are returned
    sites        RESTRICT  explicit
    invitations  CASCADE   explicit anyway, same reason
    users        RESTRICT  explicit (clients); admins are detached, see below
    organization           explicit

Rows of *other* organizations that point to a deleted user (alerts
acknowledged_by/resolved_by, invitations.created_by, documents.uploaded_by)
are set to NULL by their ON DELETE SET NULL.

--------------------------------------------------------------------
ADMINS
--------------------------------------------------------------------
An admin manages every organization, even if organization_id points to
one. Deleting the organization does not delete the admin account: it is
detached (organization_id = NULL, which ck_users_client_has_organization
allows for admins). Otherwise purging a client could lock the team out.

--------------------------------------------------------------------
TRANSACTION
--------------------------------------------------------------------
It does not commit. Call it inside `transaction(db)`: if any DELETE fails,
everything is rolled back and nothing is half deleted.

The organization, its sites and its sensors are locked first (FOR UPDATE).
A reading that arrives meanwhile for one of those sensors waits for the
purge and then fails cleanly (its sensor no longer exists), instead of
breaking the purge with a foreign key error.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from app.modules.alerts.model import Alert
from app.modules.documents.model import Document
from app.modules.invitations.model import Invitation
from app.modules.organizations.model import Organization
from app.modules.readings.model import Reading
from app.modules.sensors.model import Sensor
from app.modules.sites.model import Site
from app.modules.users.model import User


@dataclass(frozen=True)
class PurgeResult:
    """How many rows were deleted per table, plus the detached admins."""

    deleted: dict[str, int] = field(default_factory=dict)
    detached_admins: int = 0


def purge_organization(db: Session, organization_id: UUID) -> PurgeResult | None:
    """
    Deletes the organization and all its data. Returns the counts, or None
    if the organization does not exist (B16 answers 404).
    """
    organization = db.execute(
        select(Organization.id)
        .where(Organization.id == organization_id)
        .with_for_update()
    ).scalar_one_or_none()
    if organization is None:
        return None

    site_ids = select(Site.id).where(Site.organization_id == organization_id)
    sensor_ids = select(Sensor.id).where(Sensor.site_id.in_(site_ids))

    # Lock sites and sensors so no reading or sensor sneaks in mid-purge.
    db.execute(select(Site.id).where(Site.organization_id == organization_id).with_for_update())
    db.execute(select(Sensor.id).where(Sensor.site_id.in_(site_ids)).with_for_update())

    deleted: dict[str, int] = {}

    def _delete(name: str, statement) -> None:
        deleted[name] = db.execute(statement).rowcount

    _delete("readings", delete(Reading).where(Reading.sensor_id.in_(sensor_ids)))
    _delete("alerts", delete(Alert).where(Alert.sensor_id.in_(sensor_ids)))
    _delete("sensors", delete(Sensor).where(Sensor.site_id.in_(site_ids)))
    _delete(
        "documents",
        delete(Document).where(Document.organization_id == organization_id),
    )
    _delete("sites", delete(Site).where(Site.organization_id == organization_id))
    _delete(
        "invitations",
        delete(Invitation).where(Invitation.organization_id == organization_id),
    )

    detached_admins = db.execute(
        update(User)
        .where(User.organization_id == organization_id, User.role == "admin")
        .values(organization_id=None)
    ).rowcount
    _delete(
        "users",
        delete(User).where(User.organization_id == organization_id),
    )
    _delete(
        "organizations",
        delete(Organization).where(Organization.id == organization_id),
    )

    # The ORM may still hold objects of the deleted rows: forget them.
    db.expire_all()
    return PurgeResult(deleted=deleted, detached_admins=detached_admins)
