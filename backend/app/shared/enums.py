# ENUMS — vocabulario común de la API (issue #138, B0).
# Un único sitio para los valores que comparten varios módulos.
"""
Valores cerrados de la API (issue #138, B0).

Antes de la B0 cada módulo declaraba los suyos. Con el rediseño, las
mismas palabras aparecen en varias pantallas y en varios endpoints: el
estado de una organización sale en la lista de clientes, en su ficha y en
Mi cuenta. Si cada módulo lo escribe por su cuenta, tarde o temprano uno
dice `TRIAL` y otro `TRIALING`. Por eso viven todos aquí.

Convenio: valores en `UPPER_SNAKE_CASE`, iguales al nombre. Los módulos
los importan desde aquí y no los redefinen; se pueden seguir importando
desde `modules/*/schemas.py`, que los reexportan.

La única excepción es `UserRole` (`admin` / `client`, en minúsculas), que
se queda en `users/schemas.py`: así se guarda en la tabla y así lo usan ya
el frontend y la cookie. Cambiarlo no aporta nada y rompe a todos.

Estados **guardados** frente a estados **calculados**:

- Guardados (la tabla tiene un CHECK con los mismos valores):
  `OrganizationStatus`, `BuildingType`, `SensorType`, `AlertType`,
  `AlertSeverity`, `AlertStatus`. Si se cambia uno, hay que cambiar su
  CHECK con una migración (Daruny).
- Calculados al responder, nunca se guardan: `SensorStatus`,
  `SensorHealth`, `AlertState`.
"""

from __future__ import annotations

from enum import Enum


# ---------------------------------------------------------
# ORGANIZACIONES
# ---------------------------------------------------------
class OrganizationStatus(str, Enum):
    """
    Situación comercial del cliente. CHECK `ck_organizations_status`.

    - `TRIAL`     → prueba de 7 días del registro público (B10).
    - `ACTIVE`    → cliente de pago. Las organizaciones antiguas lo son.
    - `SUSPENDED` → sus usuarios no pueden entrar (B1).
    """

    TRIAL = "TRIAL"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"


# ---------------------------------------------------------
# EDIFICIOS
# ---------------------------------------------------------
class BuildingType(str, Enum):
    """Tipo de edificio. CHECK `ck_sites_building_type`. Lo usa la B2."""

    HOTEL = "HOTEL"
    COMMUNITY = "COMMUNITY"
    OFFICE = "OFFICE"
    SPORTS = "SPORTS"
    RESIDENCE = "RESIDENCE"
    INDUSTRIAL = "INDUSTRIAL"
    OTHER = "OTHER"


# ---------------------------------------------------------
# SENSORES
# ---------------------------------------------------------
class SensorType(str, Enum):
    """
    Magnitud que mide el sensor.

    El documento fija la presión como medición principal y el caudal como
    opcional (apartado 1.2). El MVP y el simulador trabajan con PRESSURE;
    FLOW queda declarado para no tener que cambiar el contrato después.
    """

    PRESSURE = "PRESSURE"
    FLOW = "FLOW"


class SensorStatus(str, Enum):
    """
    Estado operativo del sensor: ¿está mandando lecturas?

    - `ONLINE`   → ha enviado lecturas dentro de la ventana esperada.
    - `OFFLINE`  → lleva demasiado tiempo sin enviar (issue #28).

    Lo calcula el backend a partir de `last_seen_at` (`sensors/status.py`);
    no es un campo que el cliente pueda escribir.
    """

    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"


class SensorHealth(str, Enum):
    """
    Salud del sensor tal y como la pintan las pantallas: el color del
    punto en la planta del edificio. Calculada, no se guarda.

    Junta las dos preguntas que le importan a quien mira el panel:
    ¿manda datos? y ¿lo que manda está bien? Por orden de prioridad:

    - `OFFLINE`  → más de 5 minutos sin lecturas (misma regla que
      `SensorStatus`, en `sensors/status.py`).
    - `CRITICAL` → tiene una alerta activa de gravedad CRITICAL.
    - `WARNING`  → tiene una alerta activa de gravedad WARNING.
    - `OK`       → todo lo demás.

    No sustituye a `SensorStatus`: el frontend ya usa `status` y se
    mantiene. El cálculo y el campo `health` en la respuesta son de la B3.
    """

    OK = "OK"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    OFFLINE = "OFFLINE"


# ---------------------------------------------------------
# ALERTAS
# ---------------------------------------------------------
class AlertType(str, Enum):
    """Regla que disparó la alerta. Los tres casos del apartado 1.2."""

    LOW_PRESSURE = "LOW_PRESSURE"
    HIGH_PRESSURE = "HIGH_PRESSURE"
    SENSOR_OFFLINE = "SENSOR_OFFLINE"


class AlertSeverity(str, Enum):
    """
    Gravedad.

    Es distinta del tipo: una presión baja puede ser WARNING si roza el
    umbral y CRITICAL si se desploma (issue #28).
    """

    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class AlertStatus(str, Enum):
    """
    Ciclo de vida **guardado** en la tabla. CHECK `ck_alerts_status`.

    Solo dos valores: reconocer una alerta no cambia su `status`, rellena
    `acknowledged_at`. Lo que ve la pantalla es `AlertState`.
    """

    ACTIVE = "ACTIVE"
    RESOLVED = "RESOLVED"


class AlertState(str, Enum):
    """
    Estado de la alerta tal y como lo ven las pantallas. Calculado.

    - `RESOLVED`     → `status` es RESOLVED.
    - `ACKNOWLEDGED` → sigue activa, pero alguien la ha reconocido.
    - `ACTIVE`       → sigue activa y nadie la ha reconocido.

    Se deriva de `status` + `acknowledged_at` en vez de añadir un tercer
    valor a la tabla: así no se toca el CHECK y no se pierde cuándo se
    reconoció una alerta que luego se resolvió.
    """

    ACTIVE = "ACTIVE"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"

    @classmethod
    def derive(cls, status: str, acknowledged_at: object | None) -> "AlertState":
        """`status` es el de la tabla; `acknowledged_at`, su columna."""
        if status == AlertStatus.RESOLVED.value:
            return cls.RESOLVED
        if acknowledged_at is not None:
            return cls.ACKNOWLEDGED
        return cls.ACTIVE
