# EMAIL — sending plain-text emails (B19).
"""
Sending emails over standard SMTP (`smtplib`, bundled with Python).

--------------------------------------------------------------------
WHY IT NEVER RAISES
--------------------------------------------------------------------
The email is a notice, not part of the operation. If the SMTP server is
down, the data download or the deletion request has already been done
and must not fail because of it. So any error is logged and the function
returns normally.

It is also called from `BackgroundTasks`, after the response is sent: an
error here could no longer reach the user, it would only clutter the log
with a Starlette trace.

--------------------------------------------------------------------
WITHOUT A CONFIGURED SERVER
--------------------------------------------------------------------
With `SMTP_HOST` empty no connection is attempted: it logs which email
would have been sent. That is the case for the tests and local uvicorn.
"""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage
from email.utils import formataddr

from app.core.app_config import app_settings

logger = logging.getLogger(__name__)

# Maximum seconds to connect and talk to the server. It runs in the
# background, but a server that does not answer must not hang the task.
SMTP_TIMEOUT_SECONDS = 10

SENDER_NAME = "AquaGuard"


def send_email(to: str, subject: str, body: str) -> None:
    """Sends a plain-text email. If it fails, it logs it and carries on."""
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
    # Any error (connection, login, TLS, server rejection): the email never
    # breaks the operation, see the header.
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
