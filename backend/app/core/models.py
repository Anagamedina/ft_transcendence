# MODELS — imports the models so SQLAlchemy knows them.
"""
ORM model registry.

This module defines nothing. It only imports, and that is its whole job.

--------------------------------------------------------------------
WHAT PROBLEM IT SOLVES
--------------------------------------------------------------------
Models refer to each other **by name, in a string**:

    class Sensor(Base):
        alerts: Mapped[list["Alert"]] = relationship(...)

SQLAlchemy does not resolve that `"Alert"` when it reads the file: it
leaves it pending and looks it up later, on the first query, in a
registry that only holds **the classes that have been imported**. If
nobody imported `Alert`, it does not find it and blows up:

    InvalidRequestError: When initializing mapper Mapper[Sensor(sensors)],
    expression 'Alert' failed to locate a name ('Alert')

And it is not only the missing table that fails: SQLAlchemy configures
all the mappers at once, so one model that is not imported breaks **any**
query of the application, not only those on its table.

--------------------------------------------------------------------
WHY IT DID NOT HAPPEN IN THE TESTS
--------------------------------------------------------------------
Because each test file builds the registry by hand:

    from app.modules.alerts.model import Alert  # noqa: F401

With that line the test passes, and the application, which does not have
it, fails. The worst possible combination: green locally and 500 when the
stack starts.

--------------------------------------------------------------------
WHY HERE AND NOT IN EACH PLACE
--------------------------------------------------------------------
`migrations/env.py` already had this same list, because Alembic needs it
to compare the schema. Repeating it in a second place guarantees that
someone adds a model, updates one copy and forgets the other.

With a single module, whoever adds a new model adds it **here**, and the
application and the migrations get it at the same time.

--------------------------------------------------------------------
HOW TO USE IT
--------------------------------------------------------------------
It is imported for its side effect, not for what it exports:

    from app.core import models  # noqa: F401

It is in `main.py`, before the application is built, and in
`migrations/env.py`.
"""

from __future__ import annotations

# Order does not matter: SQLAlchemy resolves the references once they are
# all registered, not as they are read.
#
# `auth` is missing because its `model.py` defines no table:
# authentication uses `User`, which lives in `users`. If it ever adds one
# (persistent sessions, for example), import it here.
from app.modules.alerts.model import Alert, AlertNotification
from app.modules.documents.model import Document
from app.modules.invitations.model import Invitation
from app.modules.organizations.model import Organization
from app.modules.readings.model import Reading
from app.modules.sensors.model import Sensor
from app.modules.sites.model import Site
from app.modules.users.model import User

# The list is exported so it is explicit what gets registered, and so a
# test can check that none is missing.
__all__ = [
    "Alert",
    "AlertNotification",
    "Document",
    "Invitation",
    "Organization",
    "Reading",
    "Sensor",
    "Site",
    "User",
]
