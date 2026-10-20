# EMAIL — envío de correos en texto plano (B19).
"""
Envío de emails por SMTP estándar (`smtplib`, viene con Python).

--------------------------------------------------------------------
POR QUÉ NUNCA LANZA ERRORES
--------------------------------------------------------------------
El email es un aviso, no parte de la operación. Si el servidor SMTP está
caído, la descarga de datos o la petición de baja ya se han hecho y no
tienen que fallar por eso. Así que cualquier error se anota en el log y
la función vuelve con normalidad.

Además se llama desde `BackgroundTasks`, después de enviar la respuesta:
un error aquí ya no podría llegar al usuario, solo ensuciaría el log con
una traza de Starlette.

--------------------------------------------------------------------
SIN SERVIDOR CONFIGURADO
--------------------------------------------------------------------
Con `SMTP_HOST` vacío no se intenta conectar: se anota qué email se
habría enviado. Es el caso de los tests y de uvicorn en local.
"""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage
from email.utils import formataddr

from app.core.app_config import app_settings

logger = logging.getLogger(__name__)

# Segundos máximos para conectar y hablar con el servidor. Corre en segundo
# plano, pero un servidor que no contesta no debe dejar la tarea colgada.
SMTP_TIMEOUT_SECONDS = 10

SENDER_NAME = "AquaGuard"


def send_email(to: str, subject: str, body: str) -> None:
    """Envía un email en texto plano. Si falla, lo anota en el log y sigue."""
    if not app_settings.SMTP_HOST:
        logger.info("SMTP_HOST vacío: no se envía «%s» a %s", subject, to)
        return

    message = EmailMessage()
    message["From"] = formataddr((SENDER_NAME, app_settings.SMTP_FROM))
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    try:
        with smtplib.SMTP(
            app_settings.SMTP_HOST,
            app_settings.SMTP_PORT,
            timeout=SMTP_TIMEOUT_SECONDS,
        ) as smtp:
            if app_settings.SMTP_STARTTLS:
                smtp.starttls()
            if app_settings.SMTP_USER:
                smtp.login(app_settings.SMTP_USER, app_settings.SMTP_PASSWORD)
            smtp.send_message(message)
    # Cualquier error (conexión, login, TLS, rechazo del servidor): el email
    # nunca rompe la operación, ver la cabecera.
    except Exception:
        logger.warning(
            "No se ha podido enviar «%s» a %s por %s:%s",
            subject,
            to,
            app_settings.SMTP_HOST,
            app_settings.SMTP_PORT,
            exc_info=True,
        )
        return

    logger.info("Email «%s» enviado a %s", subject, to)
