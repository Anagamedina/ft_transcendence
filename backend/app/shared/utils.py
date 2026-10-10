# UTILS — helpers compartidos (paginación, fechas, conversiones UUID, etc.).
"""Helpers sin estado que usan varios módulos."""

from __future__ import annotations

from sqlalchemy import ColumnElement, or_


def matches_text(q: str, *columns) -> ColumnElement[bool]:
    """
    Condición de la búsqueda `?q=` (B0): alguna de las columnas contiene
    el texto, sin distinguir mayúsculas.

    Se escapan `%` y `_`: son comodines de LIKE, y sin escaparlos buscar
    «100%» encontraría cualquier cosa que empiece por 100.
    """
    escaped = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    pattern = f"%{escaped}%"
    return or_(*(column.ilike(pattern, escape="\\") for column in columns))
