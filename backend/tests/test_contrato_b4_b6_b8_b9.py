"""
Contrato de la B4, la B6, la B8 y la B9 (#141, #144), publicado antes que
las rutas para que el frontend monte sus pantallas con mocks.

Comprueba que el OpenAPI lo publica y las reglas que el frontend tiene que
poder dar por hechas: el código de una invitación solo sale al crearla, el
email no se edita y `GET /api/me` mantiene `user` donde estaba.
"""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.modules.invitations.schemas import (
    InvitationAccept,
    InvitationResponse,
    InvitationSentResponse,
)
from app.modules.users.schemas import MeResponse, MeUpdate, PasswordChange, UserUpdate
from app.shared.enums import InvitationStatus

CONTRATO = [
    # B4
    "InvitationCreate",
    "InvitationResponse",
    "Page_InvitationResponse_",
    "InvitationSentResponse",
    "InvitationPublicResponse",
    "InvitationAccept",
    "InvitationStatus",
    # B6
    "UserUpdate",
    "UserAdminResponse",
    "Page_UserAdminResponse_",
    # B8
    "MeResponse",
    "OrganizationSummary",
    "MeUpdate",
    "PasswordChange",
    # B9
    "OverviewResponse",
    "WeeklyAlertsResponse",
    "WeeklyAlertsRow",
    "TopSensorsResponse",
    "TopSensorItem",
]


@pytest.fixture(scope="module")
def schemas():
    return TestClient(app).get("/api/openapi.json").json()["components"]["schemas"]


@pytest.mark.parametrize("nombre", CONTRATO)
def test_el_openapi_publica_el_contrato(schemas, nombre):
    assert nombre in schemas


def test_los_estados_de_invitacion(schemas):
    assert schemas["InvitationStatus"]["enum"] == ["PENDING", "ACCEPTED", "REVOKED", "EXPIRED"]


def test_el_codigo_solo_sale_al_crear_o_reenviar(schemas):
    """En la base solo queda su hash: después no se puede volver a enseñar."""
    assert "code" not in schemas["InvitationResponse"]["properties"]
    assert "url" not in schemas["InvitationResponse"]["properties"]
    assert {"code", "url"} <= set(schemas["InvitationSentResponse"]["required"])


def test_una_invitacion_enviada_es_una_invitacion_mas_el_codigo():
    campos = set(InvitationSentResponse.model_fields) - set(InvitationResponse.model_fields)
    assert campos == {"code", "url"}


def test_al_aceptar_no_se_elige_el_email():
    with pytest.raises(ValidationError):
        InvitationAccept(
            name="Laura", password="x" * 12, accept_terms=True, email="otra@x.dev"
        )


def test_el_email_no_se_edita():
    with pytest.raises(ValidationError):
        UserUpdate(email="otra@x.dev")
    with pytest.raises(ValidationError):
        MeUpdate(name="Ana", email="otra@x.dev")


def test_cambiar_contrasena_pide_la_actual():
    with pytest.raises(ValidationError):
        PasswordChange(new_password="agua-que-no-se-escapa")


def test_mi_cuenta_mantiene_user_donde_estaba(schemas):
    """El frontend ya lee `GET /api/me` como `{user: ...}` (stores/auth.js)."""
    assert "user" in schemas["MeResponse"]["required"]
    ahora = datetime.now(timezone.utc)
    respuesta = MeResponse.model_validate(
        {
            "user": {
                "id": uuid4(),
                "email": "ana@hotelmar.dev",
                "name": "Ana",
                "role": "client",
                "organization_id": uuid4(),
                "created_at": ahora,
            },
            "organization": {
                "id": uuid4(),
                "name": "Hotel Mar",
                "status": "TRIAL",
                "trial_ends_at": ahora,
            },
        }
    )
    assert respuesta.organization.status == "TRIAL"


def test_el_admin_ve_si_el_usuario_esta_activo_y_cuando_entro(schemas):
    propiedades = schemas["UserAdminResponse"]["properties"]
    assert {"is_active", "last_login_at", "organization_name"} <= set(propiedades)


def test_el_estado_de_invitacion_vale_para_la_respuesta():
    InvitationResponse(
        id=uuid4(),
        organization_id=uuid4(),
        organization_name="Hotel Mar",
        email="nuevo@hotelmar.dev",
        status=InvitationStatus.EXPIRED,
        expires_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
    )
