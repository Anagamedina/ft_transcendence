# EMAILS — textos de los emails de Mi cuenta (B19).
"""
Asunto y cuerpo de los dos emails de confirmación del módulo GDPR:

- al descargar los datos (`GET /api/me/export`),
- al pedir la baja (`POST /api/me/deletion-request`), solo la primera vez.

Texto plano, sin plantillas HTML (fuera del alcance de B19). Cada función
recibe datos simples y no el `User` del ORM: el email se envía en segundo
plano, cuando la sesión de base de datos de la petición ya está cerrada.
"""

from __future__ import annotations

from datetime import datetime

EXPORT_SUBJECT = "Has descargado tus datos de AquaGuard"
DELETION_SUBJECT = "Hemos recibido tu petición de baja"

_FIRMA = "El equipo de AquaGuard"


def _fecha(momento: datetime) -> str:
    """Fecha y hora legibles. La API guarda en UTC y así se indica."""
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
