# SERVICE — sites
# Business rules and orchestration. No HTTP here.
"""
Site logic.

The site is the level where the isolation by organization is anchored: it
has its own `organization_id`, and the sensors hang from it. Every query
of this layer gets the scope `get_org_scope` computes (issue #27): `None`
for an admin, who sees all, or a client's organization.

Implementation: issue #29 (`list`, `get` and `list_sensors`); filters and
`organization_name` from B0 (#138). Create, edit and delete: B2 (#139).
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import transaction
from app.core.exceptions import ConflictError, DomainValidationError, NotFoundError
from app.modules.organizations.repository import OrganizationRepository
from app.modules.sensors.repository import SensorRepository
from app.modules.sensors.schemas import SensorResponse
from app.modules.sensors.service import sensor_a_respuesta
from app.modules.sites.model import Site
from app.modules.sites.repository import SiteCounts, SiteRepository
from app.modules.sites.schemas import SiteCreate, SiteResponse, SiteUpdate
from app.modules.subscriptions.plans import max_sites_for
from app.shared.dependencies import DbSession
from app.shared.enums import OrganizationStatus
from app.shared.schemas import Page


class SiteService:
    def __init__(self, db: Session, sites: SiteRepository | None = None) -> None:
        self.db = db
        self.sites = sites or SiteRepository(db)

    def list(
        self,
        organization_id: UUID | None,
        offset: int,
        limit: int,
        q: str | None = None,
        organization_filter: UUID | None = None,
    ) -> Page[SiteResponse]:
        """
        Sites the caller can see, paginated and ordered by name.

        `organization_id` always comes from `get_org_scope`: `None` (admin)
        means every organization. `q` searches name and address and
        `organization_filter` is the B0 `?organization_id=`.
        """
        filas, total = self.sites.list_by_organization(
            organization_id=organization_id,
            offset=offset,
            limit=limit,
            q=q,
            organization_filter=organization_filter,
        )
        contadores = self.sites.counts([f.id for f in filas])
        return Page[SiteResponse](
            items=[_to_response(f, contadores[f.id]) for f in filas],
            total=total,
            page=offset // limit + 1,
            page_size=limit,
        )

    def get(self, site_id: UUID, organization_id: UUID | None) -> SiteResponse:
        """
        One site by id.

        A site from another organization answers the same as one that does
        not exist: saying "it exists but it is not yours" already confirms
        that id is real. The `SITE_NOT_FOUND` code is the one the frontend
        mock already uses.
        """
        return self._respuesta(self._visible(site_id, organization_id))

    def list_sensors(
        self, site_id: UUID, organization_id: UUID | None, offset: int, limit: int
    ) -> Page[SensorResponse]:
        """
        Sensors installed in a site.

        It is its own route instead of a field inside `SiteResponse`
        because a site can have many sensors and the map only needs the
        markers. Always returning them nested would force loading them
        even if nobody looks.

        It first checks that the site is visible to the caller
        (`organization_id` from `get_org_scope`); otherwise, 404
        `SITE_NOT_FOUND`, as in `get`. The sensors come out in the same
        format as `GET /api/sensors`: its conversion and status computation
        are reused, with the last reading of the whole page in one query.
        """
        self._visible(site_id, organization_id)

        sensores = SensorRepository(self.db)
        filas, total = sensores.list_by_site(site_id, offset=offset, limit=limit)
        vivos = sensores.live([f.id for f in filas])
        ahora = datetime.now(timezone.utc)
        return Page[SensorResponse](
            items=[sensor_a_respuesta(f, vivos.get(f.id), ahora) for f in filas],
            total=total,
            page=offset // limit + 1,
            page_size=limit,
        )

    # ---------------------------------------------------------
    # CREATE, EDIT AND DELETE — admin only (B2). The router requires it.
    # ---------------------------------------------------------
    def create(self, payload: SiteCreate) -> SiteResponse:
        """
        Creates a building in a client.

        The name does not repeat within the same client
        (`uq_sites_organization_name` constraint): it is checked first to
        give a clear 409, and the constraint guarantees it even if two
        creations arrive at once.

        **The building limit is never exceeded** (B14): 1 on trial, the
        contracted ones for a client. 409 `SITE_LIMIT_REACHED`, with
        `max_sites` in `details`. The organization is read locked so two
        creations at once do not count the same buildings and both pass.
        """
        organizaciones = OrganizationRepository(self.db)
        if organizaciones.get_by_id(payload.organization_id) is None:
            raise NotFoundError(
                "La organización indicada no existe.", code="ORGANIZATION_NOT_FOUND"
            )
        self._nombre_libre(payload.organization_id, payload.name)

        try:
            with transaction(self.db):
                organizacion = organizaciones.get_for_update(payload.organization_id)
                self._cabe_otro_edificio(organizacion)
                site = self.sites.create(
                    organization_id=payload.organization_id, **site_campos(payload)
                )
        except IntegrityError as exc:
            self._nombre_libre(payload.organization_id, payload.name, causa=exc)
            raise
        return self._respuesta(site)

    def _cabe_otro_edificio(self, organizacion) -> None:
        """409 `SITE_LIMIT_REACHED` if it already has all the buildings it can."""
        limite = max_sites_for(organizacion)
        if limite is None or self.sites.count_by_organization(organizacion.id) < limite:
            return
        cuantos = "1 edificio" if limite == 1 else f"{limite} edificios"
        if organizacion.status == OrganizationStatus.TRIAL.value:
            motivo = (
                f"{organizacion.name} está en prueba y ya tiene {cuantos}, que es "
                "el máximo. Podrá añadir más cuando se haga cliente."
            )
        else:
            motivo = (
                f"{organizacion.name} ya tiene {cuantos}, los que tiene "
                "contratados. Para añadir más tiene que ampliar el contrato."
            )
        raise ConflictError(
            motivo, details={"field": "organization_id", "max_sites": limite},
            code="SITE_LIMIT_REACHED",
        )

    def update(self, site_id: UUID, payload: SiteUpdate) -> SiteResponse:
        """
        Partial update (`exclude_unset`).

        **Removing floors cannot leave sensors outside the building.** If a
        sensor is on floor 5 and the building goes down to 3 floors, it
        answers 422 `FLOOR_OUT_OF_SITE`: the sensor has to be moved first.

        The site is read locked (B3): while the floors are checked, no
        sensor can be created or moved in this building, because those
        operations lock the site too.
        """
        cambios = payload.model_dump(exclude_unset=True)
        for campo, codigo in (("name", "INVALID_NAME"), ("floors", "INVALID_FLOORS"),
                              ("basements", "INVALID_FLOORS"),
                              ("building_type", "INVALID_BUILDING_TYPE")):
            if campo in cambios and cambios[campo] is None:
                raise DomainValidationError(
                    f"`{campo}` no puede quedar vacío.", code=codigo
                )
        if "building_type" in cambios:
            cambios["building_type"] = cambios["building_type"].value
        for coordenada in ("latitude", "longitude"):
            if coordenada in cambios:
                cambios[coordenada] = _decimal(cambios[coordenada])

        try:
            with transaction(self.db):
                site = self._bloqueado(site_id)
                if "name" in cambios:
                    self._nombre_libre(
                        site.organization_id, cambios["name"], exclude_id=site.id
                    )

                plantas = cambios.get("floors", site.floors)
                sotanos = cambios.get("basements", site.basements)
                ocupadas = self.sites.sensor_floor_range(site.id)
                if ocupadas is not None:
                    mas_baja, mas_alta = ocupadas
                    if mas_baja < -sotanos or mas_alta > plantas - 1:
                        raise DomainValidationError(
                            f"Hay sensores entre la planta {mas_baja} y la {mas_alta}: "
                            f"con {plantas} plantas y {sotanos} sótanos quedarían fuera "
                            "del edificio. Muévelos antes.",
                            code="FLOOR_OUT_OF_SITE",
                        )
                site = self.sites.update(site, **cambios)
        except IntegrityError as exc:
            if "name" in cambios:
                organizacion = self._visible(site_id, None).organization_id
                self._nombre_libre(
                    organizacion, cambios["name"], exclude_id=site_id, causa=exc
                )
            raise
        return self._respuesta(site)

    def delete(self, site_id: UUID) -> None:
        """
        Deletes a building **only if it is empty**. Otherwise something
        would be lost:

        - With sensors, their readings and alerts: 409 `SITE_HAS_SENSORS`.
        - With documents, the documents and their files: 409
          `SITE_HAS_DOCUMENTS` (review of PR #194). The table would delete
          them in cascade without warning.

        Deleting a whole client with everything it owns is B16.

        It locks the site (B3): a sensor creation arriving at the same time
        waits, and when it gets in it sees the building no longer exists
        (404).
        """
        with transaction(self.db):
            site = self._bloqueado(site_id)
            if self.sites.has_sensors(site.id):
                raise ConflictError(
                    "El edificio tiene sensores. Quítalos o muévelos antes de borrarlo.",
                    code="SITE_HAS_SENSORS",
                )
            if self.sites.has_documents(site.id):
                raise ConflictError(
                    "El edificio tiene documentos. Bórralos antes de borrar el edificio.",
                    code="SITE_HAS_DOCUMENTS",
                )
            self.sites.delete(site)

    # ---------------------------------------------------------
    # HELPERS
    # ---------------------------------------------------------
    def _visible(self, site_id: UUID, organization_id: UUID | None) -> Site:
        """
        The site, if it exists and is visible to the caller.

        A site from another organization answers the same as one that does
        not exist: saying "it exists but it is not yours" already confirms
        that id is real. The `SITE_NOT_FOUND` code is the one the frontend
        mock already uses.
        """
        site = self.sites.get_by_id(site_id, organization_id)
        if site is None:
            raise NotFoundError("El site indicado no existe.", code="SITE_NOT_FOUND")
        return site

    def _bloqueado(self, site_id: UUID) -> Site:
        """The site, locked until the end of the transaction, or 404."""
        site = self.sites.get_for_update(site_id)
        if site is None:
            raise NotFoundError("El site indicado no existe.", code="SITE_NOT_FOUND")
        return site

    def _nombre_libre(
        self,
        organization_id: UUID,
        nombre: str,
        exclude_id: UUID | None = None,
        causa: Exception | None = None,
    ) -> None:
        if self.sites.name_taken(organization_id, nombre, exclude_id=exclude_id):
            raise ConflictError(
                "Ese cliente ya tiene un edificio con ese nombre.",
                code="SITE_NAME_TAKEN",
            ) from causa

    def _respuesta(self, site: Site) -> SiteResponse:
        return _to_response(site, self.sites.counts([site.id])[site.id])


def site_campos(datos) -> dict:
    """
    Columns of a site from a `SiteBase` (site creation and `first_site` of
    the organization creation). The coordinates become `Decimal`
    (`Numeric(9, 6)`) and the building type, its value.
    """
    return {
        "name": datos.name,
        "address": datos.address,
        "latitude": _decimal(datos.latitude),
        "longitude": _decimal(datos.longitude),
        "floors": datos.floors,
        "basements": datos.basements,
        "building_type": datos.building_type.value,
    }


def _decimal(valor: float | None) -> Decimal | None:
    return None if valor is None else Decimal(str(valor))


def _to_response(site: Site, contadores: SiteCounts) -> SiteResponse:
    """
    The table stores latitude and longitude as `Numeric(9, 6)`, which
    arrive as `Decimal`; the contract and the map expect them as JSON
    numbers. They are converted here, keeping the `None` of a site without
    coordinates.

    `organization_name` (B0) comes already loaded in lists: the repository
    uses `selectinload(Site.organization)`. `sensor_count` and `status`
    (B2) come from `SiteRepository.counts`.
    """
    return SiteResponse(
        id=site.id,
        organization_id=site.organization_id,
        organization_name=site.organization.name,
        name=site.name,
        address=site.address,
        latitude=None if site.latitude is None else float(site.latitude),
        longitude=None if site.longitude is None else float(site.longitude),
        floors=site.floors,
        basements=site.basements,
        building_type=site.building_type,
        sensor_count=contadores.sensors,
        status=contadores.status,
        created_at=site.created_at,
    )


def get_site_service(db: DbSession) -> SiteService:
    """Service provider for `Depends`."""
    return SiteService(db)
