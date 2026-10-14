# ROUTER — search
# Capa HTTP fina: valida schemas → llama service → responde.
"""
Búsqueda global del panel (B17, issue #150).

    GET /api/search?q=diag&limit=5

Admin y cliente, cada uno dentro de su alcance (`OrgScope`, #27).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.exceptions import DomainValidationError
from app.modules.search.schemas import SearchResponse
from app.modules.search.service import SearchService, get_search_service
from app.shared.dependencies import OrgScope
from app.shared.schemas import error_response

router = APIRouter(prefix="/search", tags=["Search"])

SearchSvc = Annotated[SearchService, Depends(get_search_service)]

# Con una sola letra casi todo coincide, y la respuesta no ayuda a nadie.
Q_MIN = 2


@router.get(
    "",
    response_model=SearchResponse,
    summary="Buscar en el panel",
    description=(
        "Busca clientes, edificios y sensores a la vez, sin distinguir "
        "mayúsculas. Devuelve los primeros `limit` de cada tipo y el total.\n\n"
        "Un cliente solo encuentra edificios y sensores de su organización, "
        "y ninguna organización."
    ),
    responses={
        **error_response(status.HTTP_401_UNAUTHORIZED, "No hay sesión (`UNAUTHORIZED`)."),
        **error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            f"`q` con menos de {Q_MIN} caracteres sin contar espacios (`QUERY_TOO_SHORT`).",
        ),
    },
)
def search(
    service: SearchSvc,
    scope: OrgScope,
    q: Annotated[str, Query(max_length=100, description="Texto a buscar.")],
    limit: Annotated[
        int, Query(ge=1, le=20, description="Resultados por tipo (máximo 20).")
    ] = 5,
) -> SearchResponse:
    q = q.strip()
    if len(q) < Q_MIN:
        raise DomainValidationError(
            f"Escribe al menos {Q_MIN} caracteres para buscar.",
            details={"field": "q", "message": f"Mínimo {Q_MIN} caracteres."},
            code="QUERY_TOO_SHORT",
        )
    return service.search(q, scope, limit)
