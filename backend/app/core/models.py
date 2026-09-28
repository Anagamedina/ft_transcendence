# MODELS — importa los siete modelos para que SQLAlchemy los conozca.
"""
Registro de modelos ORM.

Este módulo no define nada. Solo importa, y ese es todo su trabajo.

--------------------------------------------------------------------
QUÉ PROBLEMA RESUELVE
--------------------------------------------------------------------
Los modelos se referencian entre sí **por nombre, en una cadena de
texto**:

    class Sensor(Base):
        alerts: Mapped[list["Alert"]] = relationship(...)

SQLAlchemy no resuelve ese `"Alert"` al leer el archivo: lo deja pendiente
y lo busca más tarde, la primera vez que alguien consulta, en un registro
donde solo están **las clases que se hayan importado**. Si nadie importó
`Alert`, no lo encuentra y revienta:

    InvalidRequestError: When initializing mapper Mapper[Sensor(sensors)],
    expression 'Alert' failed to locate a name ('Alert')

Y no falla solo la tabla que falte: SQLAlchemy configura todos los mapas de
golpe, así que un modelo sin importar tumba **cualquier** consulta de la
aplicación, no solo las de su tabla.

--------------------------------------------------------------------
POR QUÉ NO PASABA EN LOS TESTS
--------------------------------------------------------------------
Porque cada archivo de tests se monta el registro a mano:

    from app.modules.alerts.model import Alert  # noqa: F401

Con esa línea el test pasa, y la aplicación —que no la tiene— falla. Es la
peor combinación posible: verde en local y 500 al levantar el stack.

--------------------------------------------------------------------
POR QUÉ AQUÍ Y NO EN CADA SITIO
--------------------------------------------------------------------
`migrations/env.py` ya tenía esta misma lista, porque Alembic la necesita
para comparar el esquema. Repetirla en un segundo sitio garantiza que
alguien añada un modelo, actualice una copia y se olvide de la otra.

Con un único módulo, quien añada un modelo nuevo lo añade **aquí**, y lo
reciben a la vez la aplicación y las migraciones.

--------------------------------------------------------------------
CÓMO SE USA
--------------------------------------------------------------------
Se importa por su efecto, no por lo que exporta:

    from app.core import models  # noqa: F401

Está en `main.py`, antes de construir la aplicación, y en
`migrations/env.py`.
"""

from __future__ import annotations

# El orden no importa: SQLAlchemy resuelve las referencias cuando ya están
# todas registradas, no según se van leyendo.
#
# `auth` no aparece porque su `model.py` no define ninguna tabla: la
# autenticación usa `User`, que vive en `users`. Si algún día añade una
# (sesiones persistentes, por ejemplo), se importa aquí.
from app.modules.alerts.model import Alert
from app.modules.organizations.model import Organization
from app.modules.readings.model import Reading
from app.modules.sensors.model import Sensor
from app.modules.sites.model import Site
from app.modules.users.model import User

# Se exporta la lista para que sea explícito qué se está registrando, y para
# que un test pueda comprobar que no falta ninguno.
__all__ = [
    "Alert",
    "Organization",
    "Reading",
    "Sensor",
    "Site",
    "User",
]
