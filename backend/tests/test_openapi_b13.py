"""Comprobaciones del contrato OpenAPI publicado por B13."""

from fastapi.testclient import TestClient

from app.main import app
from app.openapi import CONTRACT_MODELS
from app.shared.schemas import error_response


def _schemas() -> dict:
    return TestClient(app).get("/api/openapi.json").json()["components"]["schemas"]


def test_los_modelos_de_rutas_no_se_inyectan_manualmente():
    nombres = {getattr(model, "__name__", "") for model in CONTRACT_MODELS}

    assert not nombres.intersection(
        {
            "RegisterRequest",
            "LoginRequest",
            "SessionResponse",
            "MessageResponse",
            "OrganizationResponse",
            "SiteResponse",
            "SensorResponse",
            "ReadingResponse",
            "AlertResponse",
            "DocumentResponse",
        }
    )


def test_los_requests_y_responses_tienen_ejemplo_completo():
    schemas = _schemas()

    for nombre in (
        "RegisterRequest",
        "LoginRequest",
        "SessionResponse",
        "OrganizationCreate",
        "OrganizationResponse",
        "SiteCreate",
        "SiteResponse",
        "SensorCreate",
        "SensorResponse",
        "ReadingCreate",
        "ReadingResponse",
        "AlertResponse",
        "DocumentResponse",
        "InvitationCreate",
        "InvitationPublicResponse",
        "InvitationAccept",
    ):
        assert schemas[nombre].get("examples"), nombre


def test_los_errores_documentados_conservan_el_envelope_de_la_api():
    response = error_response(
        404,
        "El sensor no existe (`SENSOR_NOT_FOUND`).",
    )[404]

    assert response["content"]["application/json"]["example"] == {
        "error": {
            "code": "SENSOR_NOT_FOUND",
            "message": "La operación no se puede completar.",
            "details": None,
        }
    }

