# NOTICES — alerts
# Avisos por email al cliente cuando nadie se encarga de una alerta (#275).
"""
Nuestro servicio es avisar a tiempo. Si una alerta sigue «Sin atender»
(nadie ha pulsado «Me encargo»), se avisa al cliente por email y, si nadie
responde, AquaGuard llama. Lo llama cada minuto `alerts/vigilante.py`.

Calendario (minutos desde que saltó la alerta), el mismo que dibuja el
frontend en `utils/notificationSteps.js`:

    CRITICAL  email 1 a los 5 · email 2 a los 20 · a los 45, AquaGuard llama
    WARNING   email 1 a los 60

- **A quién**: el 1.º al email de contacto de la organización; el 2.º a ese
  contacto y a todos sus usuarios activos. Sin contacto, el 1.º va a los
  usuarios. Sin nadie a quien enviar, no se apunta nada (se ve en el log).
- **Uno por vuelta y por alerta**: si el backend estuvo parado y ya tocaban
  los dos, se envía el 1.º y el 2.º en la vuelta siguiente, no los dos de
  golpe.
- **Se apunta antes de enviar**: la fila de `alert_notifications` se guarda
  primero (con `UNIQUE (alert_id, attempt)`) y después se envía. Si el
  proceso muere entre medias, ese aviso se pierde, pero nunca se repite.
  Avisar dos veces asusta y quita credibilidad; uno perdido lo cubre el
  siguiente y, al final, la llamada.
- «Me encargo» o cerrar la alerta para los avisos: solo se miran las
  alertas ACTIVE sin `acknowledged_at`.
- **Mientras se confirma el cierre automático (#277), no se avisa**: si las
  lecturas ya son normales, sería absurdo escribir «nadie atiende tu
  alerta». Si vuelven a ir mal, se sigue donde se estaba.
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
    emails: tuple[int, ...]   # minutos de cada email
    llamada: int | None       # minuto en que AquaGuard debe llamar


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
    """sqlite (tests) devuelve las fechas sin zona; se guardan en UTC."""
    return fecha if fecha.tzinfo else fecha.replace(tzinfo=timezone.utc)


def siguiente_aviso(alerta: Alert) -> datetime | None:
    """
    Cuándo toca el próximo email de esta alerta, o None si ya no toca
    ninguno (enviados todos, alguien se encarga o está cerrada).
    Es `next_notification_at` de la API.
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
    # Sin repetir el contacto si también es usuario
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
    Envía los emails que tocan ahora. Devuelve cuántos ha enviado.

    `ahora` se puede pasar desde fuera para probarlo sin depender del reloj.
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
        # El primer email que falta; si aún no es su hora, nada esta vuelta
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

        # Primero se apunta; si otra vuelta ya lo apuntó, no se envía
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
