# EMAILS — texts of the My account emails (B19).
"""
Subject and body of the two confirmation emails of the GDPR module:

- on data download (`GET /api/me/export`),
- on a deletion request (`POST /api/me/deletion-request`), only the
  first time.

Plain text, no HTML templates (outside the scope of B19). The emails are
written in Spanish, the language of the users. Each function gets plain
data and not the ORM `User`: the email is sent in the background, when
the request's database session is already closed.
"""

from __future__ import annotations

from datetime import datetime

EXPORT_SUBJECT = "Has descargado tus datos de AquaGuard"
DELETION_SUBJECT = "Hemos recibido tu petición de baja"

_FIRMA = "El equipo de AquaGuard"


def _fecha(momento: datetime) -> str:
    """Readable date and time. The API stores UTC and says so."""
    return momento.strftime("%d/%m/%Y a las %H:%M (UTC)")


def export_body(name: str, exported_at: datetime) -> str:
    return (
        f"Hola, {name}:\n"
        "\n"
        f"El {_fecha(exported_at)} se descargó una copia de los datos de tu "
        "cuenta de AquaGuard: tu cuenta, tu organización y sus edificios.\n"
        "\n"
        "Si has sido tú, no tienes que hacer nada.\n"
        "Si no has sido tú, cambia tu contraseña en Mi cuenta y avisa al "
        "administrador.\n"
        "\n"
        f"{_FIRMA}\n"
    )


def deletion_body(name: str, requested_at: datetime) -> str:
    return (
        f"Hola, {name}:\n"
        "\n"
        f"Hemos registrado tu petición de baja el {_fecha(requested_at)}.\n"
        "\n"
        "Todavía no se ha borrado nada. Un administrador revisará la petición "
        "y cerrará tu cuenta. Hasta entonces puedes seguir entrando y "
        "descargar tus datos desde Mi cuenta.\n"
        "\n"
        "Si no has pedido la baja, avisa al administrador.\n"
        "\n"
        f"{_FIRMA}\n"
    )
