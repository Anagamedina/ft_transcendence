# IMPORTER — sensors
# Lee y valida el CSV de la importación. No toca la base de datos.
"""
Importación de sensores desde un CSV (módulo «Data export and import»).

Un instalador da de alta todos los sensores de un edificio de una vez. Este
archivo solo convierte el CSV en filas validadas; lo que necesita la base
(el edificio, las etiquetas ya usadas y el límite del contrato) lo
comprueba `SensorService.import_csv`.

**Todo o nada.** Si una fila tiene un error no se importa ninguna, y la
respuesta dice cuáles fallan y por qué, con el número de línea del archivo
(la cabecera es la 1). Así el instalador corrige el archivo y lo vuelve a
subir entero, sin tener que averiguar qué entró y qué no.

**El formato que guarda Excel en español.** Separador `;` o `,`, UTF-8 (con
o sin BOM) o Windows-1252, y decimales con coma o con punto (`1,5` o
`1.5`). Las columnas pueden ir en cualquier orden y sin distinguir
mayúsculas.
"""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass
from typing import BinaryIO

from app.core.app_config import app_settings
from app.core.exceptions import DomainValidationError, PayloadTooLargeError
from app.modules.sensors.schemas import PRESSURE_MAX_BAR, PRESSURE_MIN_BAR

# Un edificio grande tiene unos cientos de sensores: más filas que esto es
# un archivo equivocado, y validarlo todo en una petición no tiene sentido.
MAX_IMPORT_ROWS = 500

REQUIRED_COLUMNS = ("external_id", "name", "min_pressure", "max_pressure")
OPTIONAL_COLUMNS = ("location", "floor")

# Los mismos largos que las columnas de `sensors` y que `SensorCreate`.
_MAX_LENGTH = {"external_id": 100, "name": 120, "location": 120}

# Fuera de tabuladores y saltos de línea, un texto no lleva caracteres de
# control: si los hay, es un binario renombrado a .csv.
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


@dataclass(frozen=True)
class SensorRow:
    """Una fila ya validada, con el número de línea del archivo."""

    line: int
    external_id: str
    name: str
    location: str | None
    floor: int
    min_pressure: float
    max_pressure: float


def parse_sensors_csv(source: BinaryIO) -> tuple[list[SensorRow], list[dict]]:
    """
    Las filas válidas y los errores de las demás, uno por fila y campo.

    Los errores de filas no se lanzan aquí: el service les suma los que
    dependen de la base (etiqueta ya usada, planta que no existe) y lanza
    todos juntos con `invalid_rows`, para que se corrijan de una vez.

    Lanza los errores del archivo entero: 413 `FILE_TOO_LARGE` y 422
    `EMPTY_FILE`, `UNSUPPORTED_FILE_TYPE`, `IMPORT_MISSING_COLUMNS`,
    `IMPORT_NO_ROWS` e `IMPORT_TOO_MANY_ROWS`.
    """
    texto = _decode(source.read(app_settings.MAX_UPLOAD_MB * 1024 * 1024 + 1))
    lector = csv.DictReader(io.StringIO(texto, newline=""), delimiter=_delimiter(texto))
    lector.fieldnames = [(nombre or "").strip().lower() for nombre in lector.fieldnames or []]

    faltan = [c for c in REQUIRED_COLUMNS if c not in lector.fieldnames]
    if faltan:
        raise DomainValidationError(
            f"Al archivo le faltan columnas: {', '.join(faltan)}. La primera "
            f"línea tiene que nombrarlas: {', '.join(REQUIRED_COLUMNS + OPTIONAL_COLUMNS)}.",
            details=[{"field": c, "message": "Falta esta columna."} for c in faltan],
            code="IMPORT_MISSING_COLUMNS",
        )

    filas: list[SensorRow] = []
    errores: list[dict] = []
    vistos: dict[str, int] = {}
    leidas = 0
    for valores in lector:
        # line_num cuenta líneas físicas: con un salto dentro de comillas,
        # sigue apuntando a donde acaba la fila, que es donde la busca Excel.
        linea = lector.line_num
        if not any((v or "").strip() for v in valores.values() if isinstance(v, str)):
            continue  # línea en blanco, típica al final del archivo
        leidas += 1
        if leidas > MAX_IMPORT_ROWS:
            raise DomainValidationError(
                f"El archivo tiene más de {MAX_IMPORT_ROWS} sensores. Divídelo en varios.",
                code="IMPORT_TOO_MANY_ROWS",
            )
        fila, errores_fila = _row(linea, valores)
        if fila is not None and fila.external_id in vistos:
            errores_fila.append(
                row_error(
                    linea,
                    "external_id",
                    f"«{fila.external_id}» ya está en la línea {vistos[fila.external_id]}.",
                )
            )
        if errores_fila:
            errores.extend(errores_fila)
        else:
            vistos[fila.external_id] = linea
            filas.append(fila)

    if not filas and not errores:
        raise DomainValidationError(
            "El archivo no tiene ningún sensor: solo la cabecera.",
            code="IMPORT_NO_ROWS",
        )
    return filas, errores


def invalid_rows(errores: list[dict]) -> DomainValidationError:
    """El 422 de filas con errores; también lo usa el service para los de la base."""
    lineas = len({e["row"] for e in errores})
    return DomainValidationError(
        f"{lineas} {'fila tiene' if lineas == 1 else 'filas tienen'} errores. "
        "No se ha importado ningún sensor: corrige el archivo y súbelo otra vez.",
        details=sorted(errores, key=lambda e: e["row"]),
        code="IMPORT_INVALID_ROWS",
    )


def row_error(linea: int, campo: str, mensaje: str) -> dict:
    return {"row": linea, "field": campo, "message": mensaje}


def _decode(datos: bytes) -> str:
    if len(datos) > app_settings.MAX_UPLOAD_MB * 1024 * 1024:
        raise PayloadTooLargeError(
            f"El archivo pasa de {app_settings.MAX_UPLOAD_MB} MB.",
            code="FILE_TOO_LARGE",
        )
    if not datos.strip():
        raise DomainValidationError("El archivo está vacío.", code="EMPTY_FILE")
    for codificacion in ("utf-8-sig", "cp1252"):
        try:
            texto = datos.decode(codificacion)
        except UnicodeDecodeError:
            continue
        if _CONTROL.search(texto) is None:
            return texto
        break
    raise DomainValidationError(
        "El archivo no es un CSV: guárdalo como «CSV (delimitado por comas)».",
        code="UNSUPPORTED_FILE_TYPE",
    )


def _delimiter(texto: str) -> str:
    """`;` si la cabecera lo usa (Excel en español), si no `,`."""
    cabecera = texto.split("\n", 1)[0]
    return ";" if cabecera.count(";") > cabecera.count(",") else ","


def _row(linea: int, valores: dict) -> tuple[SensorRow | None, list[dict]]:
    """Una fila validada campo a campo, o sus errores (todos, no solo el primero)."""
    errores: list[dict] = []

    def texto(campo: str, obligatorio: bool) -> str | None:
        valor = (valores.get(campo) or "").strip()
        if not valor:
            if obligatorio:
                errores.append(row_error(linea, campo, "Falta este dato."))
            return None
        if len(valor) > _MAX_LENGTH[campo]:
            errores.append(
                row_error(linea, campo, f"Máximo {_MAX_LENGTH[campo]} caracteres.")
            )
        return valor

    def presion(campo: str) -> float | None:
        valor = (valores.get(campo) or "").strip().replace(",", ".")
        if not valor:
            errores.append(row_error(linea, campo, "Falta este dato."))
            return None
        try:
            numero = float(valor)
        except ValueError:
            errores.append(row_error(linea, campo, f"«{valor}» no es un número."))
            return None
        if not PRESSURE_MIN_BAR <= numero <= PRESSURE_MAX_BAR:
            errores.append(
                row_error(
                    linea,
                    campo,
                    f"Tiene que estar entre {PRESSURE_MIN_BAR:g} y {PRESSURE_MAX_BAR:g} bar.",
                )
            )
            return None
        return numero

    external_id = texto("external_id", obligatorio=True)
    name = texto("name", obligatorio=True)
    location = texto("location", obligatorio=False)
    minimo = presion("min_pressure")
    maximo = presion("max_pressure")
    if minimo is not None and maximo is not None and minimo >= maximo:
        errores.append(
            row_error(linea, "min_pressure", "Tiene que ser menor que max_pressure.")
        )

    planta = 0
    valor_planta = (valores.get("floor") or "").strip()
    if valor_planta:
        try:
            planta = int(valor_planta)
        except ValueError:
            errores.append(
                row_error(linea, "floor", f"«{valor_planta}» no es un número de planta.")
            )

    if errores:
        return None, errores
    return (
        SensorRow(
            line=linea,
            external_id=external_id,
            name=name,
            location=location,
            floor=planta,
            min_pressure=minimo,
            max_pressure=maximo,
        ),
        [],
    )
