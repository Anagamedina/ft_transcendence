# NOTICES — alerts
# Email notices to the client when nobody handles an alert (#275).
"""
Our service is to warn in time. If an alert is still "Sin atender"
(unhandled: nobody pressed "Me encargo", "I'll handle it"), the client is
emailed and, if nobody answers, AquaGuard calls. `alerts/vigilante.py`
calls this every minute.

Schedule (minutes since the alert fired), the same one the frontend draws
in `utils/notificationSteps.js`:

    CRITICAL  email 1 at 5 · email 2 at 20 · at 45, AquaGuard calls
    WARNING   email 1 at 60

- **Who to**: the 1st to the organization contact email; the 2nd to that
  contact and all its active users. Without a contact, the 1st goes to
  the users. With nobody to send to, nothing is recorded (it shows in the
  log).
- **One per round and per alert**: if the backend was stopped and both
  were already due, the 1st is sent and the 2nd on the next round, not
  both at once.
- **Recorded before sending**: the `alert_notifications` row is saved
  first (with `UNIQUE (alert_id, attempt)`) and then sent. If the process
  dies in between, that notice is lost, but it is never repeated. Warning
  twice scares people and costs credibility; a lost one is covered by the
  next one and, in the end, by the call.
- "Me encargo" or closing the alert stops the notices: only ACTIVE alerts
  without `acknowledged_at` are looked at.
- **While the automatic closing (#277) is being confirmed, no notice is
  sent**: if the readings are already normal, writing "nobody is handling
  your alert" would be absurd. If they go bad again, it carries on where
  it was.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.app_config import app_settings
from app.modules.alerts.autoclose import normal_desde
from app.modules.alerts.model import Alert, AlertNotification
from app.modules.sensors.model import Sensor
from app.modules.sites.model import Site
from app.modules.users.model import User
from app.shared.email import send_email

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Calendario:
    emails: tuple[int, ...]   # minute of each email
    llamada: int | None       # minute when AquaGuard must call


CALENDARIO = {
    "CRITICAL": Calendario(emails=(5, 20), llamada=45),
    "WARNING": Calendario(emails=(60,), llamada=None),
}

TIPO = {
    "LOW_PRESSURE": "Presión baja",
    "HIGH_PRESSURE": "Presión alta",
    "SENSOR_OFFLINE": "Sensor sin conexión",
}
URGENCIA = {"CRITICAL": "crítica", "WARNING": "leve"}


def _utc(fecha: datetime) -> datetime:
    """sqlite (tests) returns dates without a zone; they are stored in UTC."""
    return fecha if fecha.tzinfo else fecha.replace(tzinfo=timezone.utc)


def siguiente_aviso(alerta: Alert) -> datetime | None:
    """
    When the next email of this alert is due, or None if none is due any
    more (all sent, someone is handling it or it is closed).
    It is the API `next_notification_at`.
    """
    if alerta.status != "ACTIVE" or alerta.acknowledged_at is not None:
        return None
    calendario = CALENDARIO.get(alerta.severity)
    if calendario is None:
        return None
    enviados = {n.attempt for n in alerta.notifications}
    for intento, minutos in enumerate(calendario.emails, start=1):
        if intento not in enviados:
            return _utc(alerta.created_at) + timedelta(minutes=minutos)
    return None


def _destinatarios(db: Session, alerta: Alert, intento: int) -> list[str]:
    organizacion = alerta.sensor.site.organization
    contacto = [organizacion.contact_email] if organizacion.contact_email else []
    if intento == 1 and contacto:
        return contacto
    usuarios = db.scalars(
        select(User.email).where(
            User.organization_id == organizacion.id,
            User.role == "client",
            User.is_active.is_(True),
        ).order_by(User.email)
    ).all()
    # Without repeating the contact if it is also a user
    return list(dict.fromkeys([*contacto, *usuarios]))


def _texto(alerta: Alert, intento: int) -> tuple[str, str]:
    sensor = alerta.sensor
    site = sensor.site
    tipo = TIPO.get(alerta.alert_type, alerta.alert_type)
    urgencia = URGENCIA.get(alerta.severity, alerta.severity.lower())
    asunto = f"[AquaGuard] Alerta {urgencia} sin atender: {tipo} en {site.name}"
    if intento > 1:
        asunto = f"{asunto} ({intento}.º aviso)"
    cuerpo = (
        f"Hola,\n\n"
        f"Hay una alerta {urgencia} que nadie ha atendido todavía:\n\n"
        f"  {tipo} · {alerta.message}\n"
        f"  {site.name} · planta {sensor.floor} · {sensor.name}\n"
        f"  Desde: {_utc(alerta.created_at):%d-%m-%Y %H:%M} UTC\n\n"
        f"Entra en AquaGuard y pulsa «Me encargo» para que sepamos que alguien "
        f"se ocupa: {app_settings.PUBLIC_BASE_URL}/app/alerts\n\n"
        f"Si nadie responde, el equipo de AquaGuard te llamará.\n"
    )
    return asunto, cuerpo


def enviar_avisos(db: Session, ahora: datetime | None = None) -> int:
    """
    Sends the emails that are due now. Returns how many it sent.

    `ahora` ("now") can be passed in to test it without depending on the
    clock.
    """
    ahora = ahora or datetime.now(timezone.utc)
    pendientes = db.scalars(
        select(Alert)
        .where(Alert.status == "ACTIVE", Alert.acknowledged_at.is_(None))
        .options(
            selectinload(Alert.notifications),
            selectinload(Alert.sensor).selectinload(Sensor.site).selectinload(Site.organization),
        )
    ).all()

    enviados = 0
    for alerta in pendientes:
        calendario = CALENDARIO.get(alerta.severity)
        if calendario is None:
            continue
        hechos = {n.attempt for n in alerta.notifications}
        # The first missing email; if it is not due yet, nothing this round
        intento = next(
            (i for i in range(1, len(calendario.emails) + 1) if i not in hechos), None
        )
        if intento is None:
            continue
        if _utc(alerta.created_at) + timedelta(minutes=calendario.emails[intento - 1]) > ahora:
            continue
        if normal_desde(db, alerta, ahora) is not None:
            continue

        destinatarios = _destinatarios(db, alerta, intento)
        if not destinatarios:
            logger.warning("Alerta %s: el cliente no tiene a quién avisar", alerta.id)
            continue

        # Record it first; if another round already recorded it, do not send
        try:
            db.add(AlertNotification(
                alert_id=alerta.id,
                attempt=intento,
                channel="EMAIL",
                recipient=", ".join(destinatarios),
                sent_at=ahora,
            ))
            db.commit()
        except IntegrityError:
            db.rollback()
            continue

        asunto, cuerpo = _texto(alerta, intento)
        for destinatario in destinatarios:
            send_email(destinatario, asunto, cuerpo)
        enviados += 1

    return enviados
