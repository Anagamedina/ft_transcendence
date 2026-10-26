# VIGILANTE — alerts
# Tarea en segundo plano que, cada minuto, busca sensores mudos, cierra las
# alertas que las lecturas ya confirman (#277) y avisa al cliente de las que
# nadie atiende (#275).
"""
Comprobación periódica de sensores mudos (issue #28).

`detectar_sensores_mudos` decide; este módulo solo la llama cada
`COMPROBAR_CADA`. Opción elegida por Ana el 04-10-2026 frente a calcularlo
al consultar las alertas: así la alerta aparece a tiempo aunque nadie esté
mirando la app, y lleva la fecha real de cuando se detectó.

Arranca y se para con la aplicación (`lifespan` en `main.py`).

Dos cosas a tener en cuenta:

- **Un fallo en una vuelta no para la vigilancia.** Se registra en el log
  y se sigue: si la base se cae un momento, en cuanto vuelva se retoma.
- **Hoy el backend corre en un solo proceso** (`tools/entrypoint.sh`, sin
  `--workers`, y una sola réplica en `compose.yaml`). Si algún día hay
  varios, cada uno lanzaría su propia vigilancia: no abrirían alertas
  duplicadas en el caso normal, porque se comprueba si ya hay una
  abierta, pero dos vueltas a la vez podrían. Habría que revisarlo.
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
    Una comprobación completa, con su propia sesión: no corre dentro de
    ninguna petición, así que no hay `get_db` que se la dé.

    Devuelve cuántas alertas ha abierto, o 0 si ha fallado.
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
    Cierra las alertas cuyo sensor lleva 15 minutos normal (#277), con su
    propia sesión y su propio try, como las otras vueltas.
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
    Los emails al cliente de las alertas sin atender (#275), con su propia
    sesión y su propio try: si falla el envío, los sensores mudos se siguen
    buscando, y al revés.
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
    Bucle infinito: una vuelta, espera, otra vuelta. La consulta es
    síncrona (SQLAlchemy normal), así que se ejecuta en un hilo aparte para
    no bloquear las peticiones mientras tanto.
    """
    while True:
        await asyncio.to_thread(una_vuelta)
        # Primero se cierran: así no se avisa de lo que ya está arreglado
        await asyncio.to_thread(una_vuelta_de_cierres)
        await asyncio.to_thread(una_vuelta_de_avisos)
        await asyncio.sleep(COMPROBAR_CADA.total_seconds())
