"""Contratos de escritura de la API pública."""

from __future__ import annotations

from app.modules.sites.schemas import SiteBase


class PublicSiteWrite(SiteBase):
    """
    Edificio que crea (POST) o reemplaza (PUT) la API pública.

    Son los campos del alta del admin sin `organization_id`: la organización
    sale siempre de la API key, así que no se puede crear ni mover un
    edificio a otro cliente. En un PUT, un campo opcional que no se envía
    vuelve a su valor por defecto, porque el PUT reemplaza el edificio
    entero; para cambiar un solo campo está el PATCH de la app.
    """
