# SERVICE — sites
# Reglas de negocio y orquestación. No hablar HTTP aquí.
"""
Lógica de emplazamientos.

El site es el nivel donde se ancla el aislamiento por organización: tiene
`organization_id` propio, y de él cuelgan los sensores. Toda consulta de
esta capa recibe el alcance que calcula `get_org_scope` (issue #27):
`None` para un admin, que ve todas, o la organización de un cliente.

Implementación: issue #29 (`list`, `get` y `list_sensors`); filtros y
`organization_name` de la B0 (#138). Alta, edición y borrado: B2 (#139).
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
from app.shared.dependencies import DbSession
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
        Sites que puede ver quien pregunta, paginados y ordenados por nombre.

        `organization_id` sale siempre de `get_org_scope`: `None` (admin)
        significa todas las organizaciones. `q` busca en nombre y dirección
        y `organization_filter` es el `?organization_id=` de la B0.
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
        Un site por id.

        Un site de otra organización responde lo mismo que uno que no
        existe: decir «existe pero no es tuyo» ya confirma que ese id es
        real. El código `SITE_NOT_FOUND` es el que ya usa el mock del
        frontend.
        """
        return self._respuesta(self._visible(site_id, organization_id))

    def list_sensors(
        self, site_id: UUID, organization_id: UUID | None, offset: int, limit: int
    ) -> Page[SensorResponse]:
        """
        Sensores instalados en un site.

        Existe como ruta propia en vez de un campo dentro de
        `SiteResponse` porque un site puede tener muchos sensores y el
        mapa solo necesita los marcadores. Devolverlos siempre anidados
        obligaría a cargarlos aunque nadie los mire.

        Primero se comprueba que el site sea visible para quien pregunta
        (`organization_id` de `get_org_scope`); si no, 404 `SITE_NOT_FOUND`,
        como en `get`. Los sensores salen con el mismo formato que en
        `GET /api/sensors`: se reutiliza su conversión y su cálculo de
        estado, con la última lectura de toda la página en una consulta.
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
    # ALTA, EDICIÓN Y BORRADO — solo admin (B2). Lo exige el router.
    # ---------------------------------------------------------
    def create(self, payload: SiteCreate) -> SiteResponse:
        """
        Alta de edificio en un cliente.

        El nombre no se repite dentro del mismo cliente (restricción
        `uq_sites_organization_name`): se mira antes para dar un 409 claro,
        y la restricción lo garantiza aunque dos altas lleguen a la vez.
        """
        if OrganizationRepository(self.db).get_by_id(payload.organization_id) is None:
            raise NotFoundError(
                "La organización indicada no existe.", code="ORGANIZATION_NOT_FOUND"
            )
        self._nombre_libre(payload.organization_id, payload.name)

        try:
            with transaction(self.db):
                site = self.sites.create(
                    organization_id=payload.organization_id, **site_campos(payload)
                )
        except IntegrityError as exc:
            self._nombre_libre(payload.organization_id, payload.name, causa=exc)
            raise
        return self._respuesta(site)

    def update(self, site_id: UUID, payload: SiteUpdate) -> SiteResponse:
        """
        Modificación parcial (`exclude_unset`).

        **Quitar plantas no puede dejar sensores fuera del edificio.** Si un
        sensor está en la planta 5 y el edificio pasa a tener 3 plantas, se
        responde 422 `FLOOR_OUT_OF_SITE`: hay que mover antes el sensor.

        El site se lee bloqueado (B3): mientras se comprueban las plantas,
        ningún sensor puede darse de alta ni moverse en este edificio, porque
        esas operaciones también bloquean el site.
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
        Borra un edificio **solo si está vacío**. Se perdería algo si no:

        - Con sensores, sus lecturas y alertas: 409 `SITE_HAS_SENSORS`.
        - Con documentos, los documentos y sus ficheros: 409
          `SITE_HAS_DOCUMENTS` (revisión de la PR #194). La tabla los
          borraría en cascada sin avisar.

        Borrar un cliente entero con todo lo suyo es la B16.

        Bloquea el site (B3): un alta de sensor que llegue a la vez espera,
        y cuando entra ve que el edificio ya no existe (404).
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
    # AUXILIARES
    # ---------------------------------------------------------
    def _visible(self, site_id: UUID, organization_id: UUID | None) -> Site:
        """
        El site, si existe y es visible para quien pregunta.

        Un site de otra organización responde lo mismo que uno que no
        existe: decir «existe pero no es tuyo» ya confirma que ese id es
        real. El código `SITE_NOT_FOUND` es el que ya usa el mock del
        frontend.
        """
        site = self.sites.get_by_id(site_id, organization_id)
        if site is None:
            raise NotFoundError("El site indicado no existe.", code="SITE_NOT_FOUND")
        return site

    def _bloqueado(self, site_id: UUID) -> Site:
        """El site bloqueado hasta el final de la transacción, o 404."""
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
    Columnas de un site a partir de un `SiteBase` (alta de site y
    `first_site` del alta de organización). Las coordenadas pasan a
    `Decimal` (`Numeric(9, 6)`) y el tipo de edificio, a su valor.
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
    La tabla guarda latitud y longitud como `Numeric(9, 6)`, que llegan
    como `Decimal`; el contrato y el mapa las esperan como número JSON.
    Se convierten aquí, respetando el `None` de un site sin coordenadas.

    `organization_name` (B0) llega ya cargado en los listados: el
    repository usa `selectinload(Site.organization)`. `sensor_count` y
    `status` (B2) salen de `SiteRepository.counts`.
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
    """Proveedor del service para `Depends`."""
    return SiteService(db)
