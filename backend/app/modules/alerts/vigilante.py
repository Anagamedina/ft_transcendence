# VIGILANTE — alerts
# Background task that, every minute, looks for silent sensors, closes the
# alerts the readings already confirm (#277) and notifies the client of the
# ones nobody handles (#275).
"""
Periodic check of silent sensors (issue #28).

`detectar_sensores_mudos` decides; this module only calls it every
`COMPROBAR_CADA`. Ana chose this on 2026-10-04 over computing it when the
alerts are queried: so the alert shows up on time even if nobody is
looking at the app, and it carries the real time it was detected.

It starts and stops with the application (`lifespan` in `main.py`).

Two things to keep in mind:

- **A failure in one round does not stop the watch.** It is logged and
  it carries on: if the database goes down for a moment, it resumes as
  soon as it is back.
- **Today the backend runs in a single process** (`tools/entrypoint.sh`,
  no `--workers`, and a single replica in `compose.yaml`). If there were
  several one day, each would start its own watch: they would not open
  duplicate alerts in the normal case, because it checks whether one is
  already open, but two rounds at the same time could. It would need a
  review.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from app.core.database import SessionLocal
from app.modules.alerts.autoclose import cerrar_por_lecturas
from app.modules.alerts.notices import enviar_avisos
from app.modules.alerts.offline import detectar_sensores_mudos

logger = logging.getLogger(__name__)

COMPROBAR_CADA = timedelta(minutes=1)


def una_vuelta() -> int:
    """
    One full check, with its own session: it does not run inside any
    request, so there is no `get_db` to provide one.

    Returns how many alerts it opened, or 0 if it failed.
    """
    db = SessionLocal()
    try:
        abiertas = detectar_sensores_mudos(db)
        if abiertas:
            logger.info("SENSOR_OFFLINE: %d alerta(s) nueva(s)", abiertas)
        return abiertas
    except Exception:
        logger.exception("Fallo al buscar sensores mudos; se reintenta en la siguiente vuelta")
        return 0
    finally:
        db.close()


def una_vuelta_de_cierres() -> int:
    """
    Closes the alerts whose sensor has been normal for 15 minutes (#277),
    with its own session and its own try, like the other rounds.
    """
    db = SessionLocal()
    try:
        cerradas = cerrar_por_lecturas(db)
        if cerradas:
            logger.info("Cierre automático: %d alerta(s) cerradas por las lecturas", cerradas)
        return cerradas
    except Exception:
        logger.exception("Fallo al cerrar alertas por las lecturas; se reintenta en la siguiente vuelta")
        return 0
    finally:
        db.close()


def una_vuelta_de_avisos() -> int:
    """
    The client emails for unhandled alerts (#275), with its own session and
    its own try: if sending fails, silent sensors are still searched for,
    and the other way round.
    """
    db = SessionLocal()
    try:
        enviados = enviar_avisos(db)
        if enviados:
            logger.info("Avisos al cliente: %d email(s) de alertas sin atender", enviados)
        return enviados
    except Exception:
        logger.exception("Fallo al enviar avisos al cliente; se reintenta en la siguiente vuelta")
        return 0
    finally:
        db.close()


async def vigilar() -> None:
    """
    Endless loop: one round, wait, another round. The query is synchronous
    (plain SQLAlchemy), so it runs in a separate thread so it does not
    block requests meanwhile.
    """
    while True:
        await asyncio.to_thread(una_vuelta)
        # Close first: so no notice is sent for what is already fixed
        await asyncio.to_thread(una_vuelta_de_cierres)
        await asyncio.to_thread(una_vuelta_de_avisos)
        await asyncio.sleep(COMPROBAR_CADA.total_seconds())
