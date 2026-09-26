"""
Que la aplicación pueda consultar la base de datos de verdad.

Los modelos se referencian entre sí por nombre en una cadena de texto
(`Mapped[list["Alert"]]`), y SQLAlchemy resuelve esos nombres contra un
registro que solo contiene las clases que alguien haya importado. Si la
aplicación no las importa todas, la primera consulta revienta con un 500
—cualquier consulta, no solo la de la tabla que falte—.

OJO CON CÓMO SE PRUEBA ESTO. Un test normal aquí no vale: pytest ejecuta
todos los archivos en el mismo proceso, y los demás tests importan los
modelos que necesitan. Para cuando llegara este, el registro ya estaría
lleno y pasaría aunque la aplicación estuviera rota — que es exactamente
lo que ocurrió: 31 tests en verde y un 500 al levantar el stack.

Por eso se lanza un proceso nuevo que importa **solo lo que importa la
aplicación** y nada más.
"""

import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent


def _en_proceso_limpio(codigo: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-c", codigo],
        cwd=BACKEND,
        capture_output=True,
        text=True,
    )


def test_la_app_registra_sus_modelos_al_arrancar():
    """
    Importar la aplicación tiene que bastar para poder consultar.

    Si este test falla, la aplicación arranca y responde al health check,
    pero devuelve 500 en cuanto alguien toca la base de datos.
    """
    resultado = _en_proceso_limpio(
        "import app.main\n"
        "import sqlalchemy.orm as orm\n"
        "orm.configure_mappers()\n"
        "print('OK')\n"
    )

    assert resultado.returncode == 0, (
        "Importar la aplicación no deja los mapas de SQLAlchemy utilizables.\n"
        "Probablemente falte un modelo en app/core/models.py.\n\n"
        f"{resultado.stderr[-1500:]}"
    )


def test_sin_el_registro_falla(  ):
    """
    La otra mitad: comprueba que el test de arriba mide algo.

    Importar un modelo suelto, sin el registro, tiene que fallar. Si esto
    pasara, significaría que SQLAlchemy resuelve los nombres por su cuenta
    y el test de arriba estaría comprobando el aire.
    """
    resultado = _en_proceso_limpio(
        "from app.modules.sensors.model import Sensor\n"
        "import sqlalchemy.orm as orm\n"
        "orm.configure_mappers()\n"
    )

    assert resultado.returncode != 0
    assert "failed to locate a name" in resultado.stderr


def test_estan_los_seis_modelos_con_tabla():
    """
    Que no se quede ninguno fuera al añadir uno nuevo.

    `auth` no entra: su `model.py` no define tabla, la autenticación usa
    `User`. Si algún día la define, este test lo cantará.
    """
    from app.core import models

    esperados = {"Alert", "Organization", "Reading", "Sensor", "Site", "User"}

    assert set(models.__all__) == esperados
    for nombre in esperados:
        assert hasattr(models, nombre), f"falta {nombre} en app/core/models.py"
