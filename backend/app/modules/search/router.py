# ROUTER — search
# Thin HTTP layer: validates schemas → calls the service → answers.
"""
Global search of the panel (B17, issue #150).

    GET /api/search?q=diag&limit=5

Admin and client, each within their scope (`OrgScope`, #27).
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

# With a single letter almost everything matches, and the answer helps nobody.
Q_MIN = 2


@router.get(
    "",
    response_model=SearchResponse,
    summary="Search the panel",
    description=(
        "Searches clients, buildings and sensors at once, ignoring case. "
        "Returns the first `limit` of each type and the total.\n\n"
        "A client only finds buildings and sensors of its organization, and "
        "no organization."
    ),
    responses={
        **error_response(status.HTTP_401_UNAUTHORIZED, "No session (`UNAUTHORIZED`)."),
        **error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            f"`q` with fewer than {Q_MIN} characters not counting spaces (`QUERY_TOO_SHORT`).",
        ),
    },
)
def search(
    service: SearchSvc,
    scope: OrgScope,
    q: Annotated[str, Query(max_length=100, description="Text to search.")],
    limit: Annotated[
        int, Query(ge=1, le=20, description="Results per type (20 at most).")
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
