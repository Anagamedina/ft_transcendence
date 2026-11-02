# UTILS — shared helpers (pagination, dates, UUID conversions, etc.).
"""Stateless helpers used by several modules."""

from __future__ import annotations

from sqlalchemy import ColumnElement, or_


def matches_text(q: str, *columns) -> ColumnElement[bool]:
    """
    Condition of the `?q=` search (B0): one of the columns contains the
    text, ignoring case.

    `%` and `_` are escaped: they are LIKE wildcards, and without escaping
    them searching "100%" would find anything starting with 100.
    """
    escaped = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    pattern = f"%{escaped}%"
    return or_(*(column.ilike(pattern, escape="\\") for column in columns))
