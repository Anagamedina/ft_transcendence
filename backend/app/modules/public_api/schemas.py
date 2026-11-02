"""Write contracts of the public API."""

from __future__ import annotations

from app.modules.sites.schemas import SiteBase


class PublicSiteWrite(SiteBase):
    """
    Building the public API creates (POST) or replaces (PUT).

    They are the fields of the admin creation without `organization_id`:
    the organization always comes from the API key, so a building cannot
    be created in or moved to another client. In a PUT, an optional field
    that is not sent goes back to its default, because the PUT replaces
    the whole building; to change a single field there is the app PATCH.
    """
