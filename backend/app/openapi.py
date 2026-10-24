# OPENAPI — publica los contratos que todavía no usa ninguna ruta.
"""
Contratos sin ruta (issue #23, ampliado en la B0 #138).

--------------------------------------------------------------------
EL PROBLEMA
--------------------------------------------------------------------
FastAPI genera el documento OpenAPI **a partir de las rutas**: recorre los
endpoints registrados y publica los schemas que aparecen en sus
`response_model` y sus cuerpos. Un schema que no use ninguna ruta no sale
en el documento.

Eso chocaba con cómo trabaja el equipo: el contrato se fija antes que el
endpoint, para que el frontend construya sus mocks sin esperar. Pasó con
la issue #23, cuando Auth, Sensors, Sites y Alerts aún no tenían rutas
(llegaron en las #25 a #29), y vuelve a pasar con el rediseño: por
ejemplo `OrganizationResponse` antes de la B1, o `SensorHealth` antes de
la B3.

Sin esto habría que elegir entre dos cosas malas:

  a) Publicar rutas que no funcionan, solo para que salgan sus schemas.
  b) Dejar al frontend sin contrato e inventarse el `MockAdapter` — que
     es exactamente el fallo que el documento avisa en el apartado 10:
     si el mock devuelve `data` y la API devuelve `items`, todo funciona
     tres semanas y se rompe el día de integrar.

--------------------------------------------------------------------
LA SOLUCIÓN
--------------------------------------------------------------------
Se inyectan los schemas (y los enums de la B0) directamente en
`components.schemas` del documento OpenAPI, sin declarar ninguna ruta.
Resultado:

  - Swagger muestra **solo** las rutas que de verdad existen.
  - La sección **Schemas** de esa misma página lista el contrato
    completo, del que el frontend puede copiar los ejemplos.

Cuando una ruta nueva usa uno de estos schemas, no cambia de forma: solo
pasa a tener una ruta que lo use, y FastAPI lo publica por su cuenta (ver
el `setdefault` de `register_contract_schemas`).
"""

from __future__ import annotations

from typing import Any, Callable

from fastapi import FastAPI
from pydantic import TypeAdapter
from pydantic.json_schema import models_json_schema

from app.modules.analytics.schemas import (
    OverviewResponse,
    TopSensorsResponse,
    WeeklyAlertsResponse,
)
from app.modules.invitations.schemas import (
    InvitationAccept,
    InvitationCreate,
    InvitationPublicResponse,
    InvitationResponse,
    InvitationSentResponse,
)
from app.modules.users.schemas import (
    MeResponse,
    MeUpdate,
    PasswordChange,
    UserAdminResponse,
    UserCreate,
    UserUpdate,
)
from app.shared.enums import (
    InvitationStatus,
)
from app.shared.schemas import Page

# Solo se inyectan contratos que todavía no usa ninguna ruta. Los modelos de
# endpoints reales los genera FastAPI desde sus decoradores; mantenerlos
# también aquí ocultaba si el contrato documentado coincidía con la ruta.
#
# Los `Page[...]` se listan explícitamente porque `Page` es genérico:
# `Page[SensorResponse]` y `Page[AlertResponse]` son dos schemas distintos
# en OpenAPI, y solo existen si se nombran.
CONTRACT_MODELS: list[type] = [
    # Usuarios — alta prevista para B6, todavía sin ruta en esta rama.
    UserCreate,
    # Invitaciones — contrato de la B4 (#141)
    InvitationCreate,
    InvitationResponse,
    Page[InvitationResponse],
    InvitationSentResponse,
    InvitationPublicResponse,
    InvitationAccept,
    # Usuarios — contrato de la B6 (#141), aún sin rutas en esta rama.
    UserUpdate,
    UserAdminResponse,
    Page[UserAdminResponse],
    # Mi cuenta — contrato de la B8 (#144)
    MeResponse,
    MeUpdate,
    PasswordChange,
    # Panel y KPIs — contrato de la B9 (#144)
    OverviewResponse,
    WeeklyAlertsResponse,
    TopSensorsResponse,
]


# Vocabulario común de la B0 (issue #138). Los enums usados por una ruta
# aparecen automáticamente junto al modelo que los referencia.
# `InvitationStatus` ya lo usan las rutas de la B4 (#141); sigue aquí
# porque el `setdefault` de abajo lo deja igual si ya está.
CONTRACT_ENUMS: list[type] = [
    InvitationStatus,
]


# Ejemplos completos, no solo de campos aislados. Se mantienen aquí para
# que el documento publicado sea la fuente que consume el frontend y para
# que los UUID y fechas de demostración sean iguales en requests y responses.
# Los ejemplos parciales de `Field(examples=...)` siguen siendo útiles en
# los campos, pero no permiten copiar una respuesta completa desde Swagger.
_SCHEMA_EXAMPLES: dict[str, dict[str, Any]] = {
    "HealthResponse": {
        "status": "ok",
        "service": "aquaguard-api",
        "version": "0.1.0",
    },
    "DatabaseHealthResponse": {
        "status": "ok",
        "database": "connected",
        "checked_at": "2026-10-14T09:00:00Z",
    },
    "StatusResponse": {
        "status": "OPERATIONAL",
        "checked_at": "2026-10-14T09:00:00Z",
        "components": [
            {"name": "backend", "status": "OPERATIONAL", "last_event_at": None, "size_bytes": None},
            {"name": "database", "status": "OPERATIONAL", "last_event_at": None, "size_bytes": None},
        ],
    },
    "RegisterRequest": {
        "name": "Ana Medina",
        "email": "ana@hotelmar.com",
        "password": "agua-que-no-se-escapa",
        "organization_name": "Hotel Mar",
        "accept_terms": True,
    },
    "LoginRequest": {
        "email": "ana@aquaguard.dev",
        "password": "una-contrasena-larga",
    },
    "UserCreate": {
        "email": "nuevo.gestor@hotelmar.com",
        "name": "Laura Puig",
        "password": "agua-que-no-se-escapa",
    },
    "SessionResponse": {
        "user": {
            "id": "22222222-2222-4222-8222-222222222222",
            "email": "ana@hotelmar.com",
            "name": "Ana Medina",
            "role": "client",
            "organization_id": "11111111-1111-4111-8111-111111111111",
            "created_at": "2026-10-14T09:00:00Z",
        }
    },
    "UserResponse": {
        "id": "22222222-2222-4222-8222-222222222222",
        "email": "ana@hotelmar.com",
        "name": "Ana Medina",
        "role": "client",
        "organization_id": "11111111-1111-4111-8111-111111111111",
        "created_at": "2026-10-01T10:00:00Z",
    },
    "MessageResponse": {"message": "Sesión cerrada."},
    "OrganizationCreate": {
        "name": "Hotel Diagonal Mar",
        "city": "Barcelona",
        "contact_email": "contacto@diagonalmar.com",
        "phone": "+34 600 000 000",
        "first_site": {
            "name": "Torre Diagonal",
            "address": "Avinguda Diagonal, 100, Barcelona",
            "latitude": 41.4036,
            "longitude": 2.2135,
            "floors": 6,
            "basements": 2,
            "building_type": "HOTEL",
        },
    },
    "OrganizationResponse": {
        "id": "11111111-1111-4111-8111-111111111111",
        "name": "Hotel Diagonal Mar",
        "status": "ACTIVE",
        "trial_ends_at": None,
        "city": "Barcelona",
        "contact_email": "contacto@diagonalmar.com",
        "phone": "+34 600 000 000",
        "legal_name": "Hoteles Diagonal S.L.",
        "tax_id": "B12345678",
        "billing_email": "facturacion@diagonalmar.com",
        "billing_address": "Avinguda Diagonal 100",
        "postal_code": "08019",
        "plan": "PRO",
        "billing_period": "MONTHLY",
        "contracted_sites": 2,
        "contracted_sensors": 12,
        "monthly_price_eur": 199,
        "subscribed_at": "2026-10-08T09:30:00Z",
        "iban_masked": "ES** **** **** **** **** 1332",
        "sepa_accepted_at": "2026-10-08T09:30:00Z",
        "site_count": 1,
        "sensor_count": 8,
        "user_count": 4,
        "open_alerts": 3,
        "critical_alerts": 1,
        "created_at": "2026-10-01T10:00:00Z",
    },
    "OrganizationUpdate": {
        "name": "Hotel Diagonal Mar",
        "city": "Barcelona",
        "billing_email": "facturacion@diagonalmar.com",
    },
    "OrganizationDelete": {"confirm_name": "Hotel Diagonal Mar"},
    "OrganizationDeleted": {
        "id": "11111111-1111-4111-8111-111111111111",
        "name": "Hotel Diagonal Mar",
        "deleted": {
            "readings": 5094,
            "alerts": 12,
            "sensors": 8,
            "documents": 2,
            "sites": 1,
            "invitations": 1,
            "users": 4,
            "organizations": 1,
        },
        "detached_admins": 0,
        "deleted_files": 2,
    },
    "SiteCreate": {
        "organization_id": "11111111-1111-4111-8111-111111111111",
        "name": "Torre Diagonal",
        "address": "Avinguda Diagonal, 100, Barcelona",
        "latitude": 41.4036,
        "longitude": 2.2135,
        "floors": 6,
        "basements": 2,
        "building_type": "HOTEL",
    },
    "SiteBase": {
        "name": "Torre Diagonal",
        "address": "Avinguda Diagonal, 100, Barcelona",
        "latitude": 41.4036,
        "longitude": 2.2135,
        "floors": 6,
        "basements": 2,
        "building_type": "HOTEL",
    },
    "SiteResponse": {
        "id": "33333333-3333-4333-8333-333333333333",
        "organization_id": "11111111-1111-4111-8111-111111111111",
        "organization_name": "Hotel Diagonal Mar",
        "name": "Torre Diagonal",
        "address": "Avinguda Diagonal, 100, Barcelona",
        "latitude": 41.4036,
        "longitude": 2.2135,
        "floors": 6,
        "basements": 2,
        "building_type": "HOTEL",
        "sensor_count": 8,
        "status": "OK",
        "created_at": "2026-10-01T10:05:00Z",
    },
    "SiteUpdate": {"name": "Torre Diagonal", "floors": 6},
    "SensorCreate": {
        "site_id": "33333333-3333-4333-8333-333333333333",
        "name": "Presión entrada",
        "location": "Cuarto técnico",
        "sensor_type": "PRESSURE",
        "min_pressure": 1.5,
        "max_pressure": 6.0,
        "external_id": "SENS-001",
        "unit": "bar",
        "floor": 0,
    },
    "SensorResponse": {
        "id": "44444444-4444-4444-8444-444444444444",
        "site_id": "33333333-3333-4333-8333-333333333333",
        "site_name": "Torre Diagonal",
        "organization_id": "11111111-1111-4111-8111-111111111111",
        "organization_name": "Hotel Diagonal Mar",
        "floor": 0,
        "external_id": "SENS-001",
        "name": "Presión entrada",
        "location": "Cuarto técnico",
        "sensor_type": "PRESSURE",
        "unit": "bar",
        "min_pressure": 1.5,
        "max_pressure": 6.0,
        "status": "ONLINE",
        "health": "OK",
        "last_seen_at": "2026-10-14T09:59:00Z",
        "last_value": 3.4,
        "created_at": "2026-10-01T10:10:00Z",
    },
    "SensorUpdate": {"name": "Presión entrada", "max_pressure": 6.0, "floor": 0},
    "ReadingCreate": {
        "id": "55555555-5555-4555-8555-555555555555",
        "sensor_id": "44444444-4444-4444-8444-444444444444",
        "pressure": 3.42,
        "measured_at": "2026-10-14T09:58:00Z",
    },
    "ReadingResponse": {
        "id": "55555555-5555-4555-8555-555555555555",
        "sensor_id": "44444444-4444-4444-8444-444444444444",
        "pressure": 3.42,
        "measured_at": "2026-10-14T09:58:00Z",
        "created_at": "2026-10-14T09:58:01Z",
    },
    "ReadingSeriesResponse": {
        "sensor_id": "44444444-4444-4444-8444-444444444444",
        "unit": "bar",
        "min_pressure": 1.5,
        "max_pressure": 6.0,
        "bucket": "2h",
        "from": "2026-10-07T00:00:00Z",
        "to": "2026-10-14T00:00:00Z",
        "points": [
            {
                "t": "2026-10-13T08:00:00Z",
                "avg": 3.4,
                "min": 3.1,
                "max": 3.8,
            }
        ],
    },
    "SeriesPoint": {
        "t": "2026-10-13T08:00:00Z",
        "avg": 3.4,
        "min": 3.1,
        "max": 3.8,
    },
    "AlertResponse": {
        "id": "66666666-6666-4666-8666-666666666666",
        "sensor_id": "44444444-4444-4444-8444-444444444444",
        "sensor_name": "Presión entrada",
        "site_id": "33333333-3333-4333-8333-333333333333",
        "site_name": "Torre Diagonal",
        "organization_id": "11111111-1111-4111-8111-111111111111",
        "organization_name": "Hotel Diagonal Mar",
        "floor": 0,
        "type": "LOW_PRESSURE",
        "severity": "WARNING",
        "message": "Presión por debajo del umbral: 0.8 bar (mínimo 1.5)",
        "status": "ACTIVE",
        "state": "ACTIVE",
        "created_at": "2026-10-14T09:30:00Z",
        "acknowledged_at": None,
        "resolved_at": None,
        "acknowledged_by_name": None,
        "resolved_by_name": None,
        "resolution_minutes": None,
    },
    "DocumentResponse": {
        "id": "77777777-7777-4777-8777-777777777777",
        "organization_id": "11111111-1111-4111-8111-111111111111",
        "site_id": "33333333-3333-4333-8333-333333333333",
        "site_name": "Torre Diagonal",
        "kind": "PLAN",
        "filename": "plano-planta-baja.pdf",
        "content_type": "application/pdf",
        "size": 184320,
        "uploaded_by": "22222222-2222-4222-8222-222222222222",
        "can_delete": True,
        "created_at": "2026-10-14T09:00:00Z",
    },
    "DailyRow": {
        "date": "2026-10-14",
        "organization": "Hotel Diagonal Mar",
        "site": "Torre Diagonal",
        "sensor_id": "44444444-4444-4444-8444-444444444444",
        "sensor_external_id": "SENS-001",
        "sensor_name": "Presión entrada",
        "unit": "bar",
        "readings_count": 96,
        "pressure_min": 2.8,
        "pressure_avg": 3.4,
        "pressure_max": 4.1,
        "alerts_total": 1,
        "alerts_critical": 0,
        "alerts_resolved": 1,
    },
    "UserUpdate": {"name": "Laura Puig", "role": "client"},
    "UserAdminResponse": {
        "id": "22222222-2222-4222-8222-222222222222",
        "email": "laura@hotelmar.com",
        "name": "Laura Puig",
        "role": "client",
        "organization_id": "11111111-1111-4111-8111-111111111111",
        "created_at": "2026-10-14T09:00:00Z",
        "organization_name": "Hotel Mar",
        "is_active": True,
        "last_login_at": "2026-10-14T09:30:00Z",
    },
    "MeResponse": {
        "user": {
            "id": "22222222-2222-4222-8222-222222222222",
            "email": "ana@hotelmar.com",
            "name": "Ana Medina",
            "role": "client",
            "organization_id": "11111111-1111-4111-8111-111111111111",
            "created_at": "2026-10-01T10:00:00Z",
        },
        "organization": {
            "id": "11111111-1111-4111-8111-111111111111",
            "name": "Hotel Mar",
            "status": "TRIAL",
            "trial_ends_at": "2026-10-21T10:00:00Z",
        },
        "last_login_at": "2026-10-14T09:30:00Z",
        "terms_version": "2026-10",
        "terms_accepted_at": "2026-10-01T10:00:00Z",
        "deletion_requested_at": None,
    },
    "OrganizationSummary": {
        "id": "11111111-1111-4111-8111-111111111111",
        "name": "Hotel Mar",
        "status": "TRIAL",
        "trial_ends_at": "2026-10-21T10:00:00Z",
    },
    "MeUpdate": {"name": "Ana Medina"},
    # B15 — exportar mis datos y pedir la baja (#149)
    "MyDataExport": {
        "exported_at": "2026-10-15T10:00:00Z",
        "current_terms_version": "2026-10",
        "account": {
            "id": "22222222-2222-4222-8222-222222222222",
            "email": "ana@hotelmar.com",
            "name": "Ana Medina",
            "role": "client",
            "is_active": True,
            "created_at": "2026-10-01T10:00:00Z",
            "last_login_at": "2026-10-14T09:30:00Z",
            "terms_version": "2026-10",
            "terms_accepted_at": "2026-10-01T10:00:00Z",
            "deletion_requested_at": None,
        },
        "organization": {
            "id": "11111111-1111-4111-8111-111111111111",
            "name": "Hotel Mar",
            "status": "TRIAL",
            "trial_ends_at": "2026-10-21T10:00:00Z",
            "city": "Barcelona",
            "contact_email": "ana@hotelmar.com",
            "phone": None,
            "legal_name": None,
            "tax_id": None,
            "billing_email": None,
            "billing_address": None,
            "postal_code": None,
            "plan": None,
            "billing_period": None,
            "contracted_sites": None,
            "contracted_sensors": None,
            "monthly_price_eur": None,
            "subscribed_at": None,
            "iban_masked": None,
            "sepa_accepted_at": None,
            "created_at": "2026-10-01T10:00:00Z",
        },
        "sites": [
            {
                "id": "33333333-3333-4333-8333-333333333333",
                "name": "Torre Diagonal",
                "address": "Avinguda Diagonal 100",
                "latitude": 41.4036,
                "longitude": 2.2144,
                "district": "SANT_MARTI",
                "floors": 12,
                "basements": 2,
                "building_type": "HOTEL",
                "created_at": "2026-10-01T10:00:00Z",
            }
        ],
    },
    "DeletionRequestResponse": {
        "deletion_requested_at": "2026-10-15T10:00:00Z",
        "message": "Hemos registrado tu petición de baja. Un administrador la tramitará.",
    },
    "PasswordChange": {
        "current_password": "contrasena-anterior",
        "new_password": "agua-que-no-se-escapa",
    },
    "OverviewResponse": {
        "organizations_total": 5,
        "organizations_needing_attention": 2,
        "sites_total": 6,
        "sensors_total": 8,
        "sensors_online": 6,
        "open_alerts": 3,
        "critical_open_alerts": 1,
        "median_resolution_minutes": 42.5,
    },
    "WeeklyAlertsRow": {
        "sensor_id": "44444444-4444-4444-8444-444444444444",
        "sensor_name": "Presión entrada",
        "floor": 0,
        "counts": [0, 2, 0, 1, 0, 0, 3],
    },
    "WeeklyAlertsResponse": {
        "site_id": "33333333-3333-4333-8333-333333333333",
        "site_name": "Torre Diagonal",
        "week_start": "2026-10-05",
        "days": [
            "2026-10-05",
            "2026-10-06",
            "2026-10-07",
            "2026-10-08",
            "2026-10-09",
            "2026-10-10",
            "2026-10-11",
        ],
        "rows": [
            {
                "sensor_id": "44444444-4444-4444-8444-444444444444",
                "sensor_name": "Presión entrada",
                "floor": 0,
                "counts": [0, 2, 0, 1, 0, 0, 3],
            }
        ],
    },
    "TopSensorsResponse": {
        "days": 30,
        "items": [
            {
                "sensor_id": "44444444-4444-4444-8444-444444444444",
                "sensor_name": "Presión entrada",
                "site_id": "33333333-3333-4333-8333-333333333333",
                "site_name": "Torre Diagonal",
                "organization_name": "Hotel Diagonal Mar",
                "alert_count": 12,
                "critical_count": 4,
                "last_alert_at": "2026-10-14T09:30:00Z",
            }
        ],
    },
    "TopSensorItem": {
        "sensor_id": "44444444-4444-4444-8444-444444444444",
        "sensor_name": "Presión entrada",
        "site_id": "33333333-3333-4333-8333-333333333333",
        "site_name": "Torre Diagonal",
        "organization_name": "Hotel Diagonal Mar",
        "alert_count": 12,
        "critical_count": 4,
        "last_alert_at": "2026-10-14T09:30:00Z",
    },
    "InvitationCreate": {
        "email": "nuevo.gestor@hotelmar.com",
        "organization_id": "11111111-1111-4111-8111-111111111111",
    },
    "InvitationPublicResponse": {
        "organization_name": "Hotel Mar",
        "email": "nuevo.gestor@hotelmar.com",
        "expires_at": "2026-10-21T10:00:00Z",
    },
    "InvitationResponse": {
        "id": "88888888-8888-4888-8888-888888888888",
        "organization_id": "11111111-1111-4111-8111-111111111111",
        "organization_name": "Hotel Mar",
        "email": "nuevo.gestor@hotelmar.com",
        "status": "PENDING",
        "expires_at": "2026-10-21T10:00:00Z",
        "accepted_at": None,
        "revoked_at": None,
        "created_by_name": "Ana Medina",
        "created_at": "2026-10-14T09:00:00Z",
    },
    "InvitationSentResponse": {
        "id": "88888888-8888-4888-8888-888888888888",
        "organization_id": "11111111-1111-4111-8111-111111111111",
        "organization_name": "Hotel Mar",
        "email": "nuevo.gestor@hotelmar.com",
        "status": "PENDING",
        "expires_at": "2026-10-21T10:00:00Z",
        "accepted_at": None,
        "revoked_at": None,
        "created_by_name": "Ana Medina",
        "created_at": "2026-10-14T09:00:00Z",
        "code": "k3Vq9mZt2xR8",
        "url": "https://localhost/registro?invitacion=k3Vq9mZt2xR8",
    },
    "InvitationAccept": {
        "name": "Laura Puig",
        "password": "agua-que-no-se-escapa",
        "accept_terms": True,
    },
    # B14 — «Hazte cliente» (#150)
    "PlanResponse": {
        "id": "PRO",
        "name": "Profesional",
        "description": "De 2 a 5 edificios y hasta 50 sensores.",
        "monthly_price_eur": 79,
        "sensor_price_eur": 10,
        "yearly_months": 10,
        "max_sites": 5,
        "max_sensors": 50,
        "features": ["Todo lo del plan Básico", "Histórico de 1 año y exportación CSV"],
    },
    "SubscriptionRequest": {
        "sites": 2,
        "sensors": 12,
        "billing_period": "MONTHLY",
        "legal_name": "Hoteles Diagonal S.L.",
        "tax_id": "B12345678",
        "billing_address": "Avinguda Diagonal 100",
        "postal_code": "08019",
        "city": "Barcelona",
        "billing_email": "facturacion@diagonalmar.com",
        "contact_email": "contacto@diagonalmar.com",
        "phone": "+34 600 000 000",
        "iban": "ES91 2100 0418 4502 0005 1332",
        "accept_terms": True,
        "accept_sepa": True,
    },
    "SubscriptionResponse": {
        "organization_id": "11111111-1111-4111-8111-111111111111",
        "organization_name": "Hotel Diagonal Mar",
        "status": "ACTIVE",
        "plan": "PRO",
        "plan_name": "Profesional",
        "billing_period": "MONTHLY",
        "contracted_sites": 2,
        "contracted_sensors": 12,
        "monthly_price_eur": 199,
        "billed_price_eur": 199,
        "subscribed_at": "2026-10-08T09:30:00Z",
        "legal_name": "Hoteles Diagonal S.L.",
        "tax_id": "B12345678",
        "billing_address": "Avinguda Diagonal 100",
        "postal_code": "08019",
        "city": "Barcelona",
        "billing_email": "facturacion@diagonalmar.com",
        "contact_email": "contacto@diagonalmar.com",
        "phone": "+34 600 000 000",
        "iban_masked": "ES** **** **** **** **** 1332",
        "sepa_accepted_at": "2026-10-08T09:30:00Z",
    },
    # B17 — búsqueda global (#150)
    "SearchResponse": {
        "q": "diag",
        "organizations": {
            "items": [
                {
                    "id": "11111111-1111-4111-8111-111111111111",
                    "name": "Hotel Diagonal Mar",
                    "status": "ACTIVE",
                    "city": "Barcelona",
                }
            ],
            "total": 1,
        },
        "sites": {
            "items": [
                {
                    "id": "33333333-3333-4333-8333-333333333333",
                    "name": "Torre Diagonal",
                    "address": "Avinguda Diagonal 100, Barcelona",
                    "organization_id": "11111111-1111-4111-8111-111111111111",
                    "organization_name": "Hotel Diagonal Mar",
                }
            ],
            "total": 1,
        },
        "sensors": {
            "items": [
                {
                    "id": "44444444-4444-4444-8444-444444444444",
                    "name": "Pressure Sensor Diagonal 02",
                    "external_id": "SENS-102",
                    "location": "Sala técnica",
                    "site_id": "33333333-3333-4333-8333-333333333333",
                    "site_name": "Torre Diagonal",
                    "organization_id": "11111111-1111-4111-8111-111111111111",
                    "organization_name": "Hotel Diagonal Mar",
                }
            ],
            "total": 1,
        },
    },
}

_PAGE_EXAMPLES: dict[str, dict[str, Any]] = {
    "Page_OrganizationResponse_": {"items": [_SCHEMA_EXAMPLES["OrganizationResponse"]], "total": 1, "page": 1, "page_size": 20, "pages": 1},
    "Page_SiteResponse_": {"items": [_SCHEMA_EXAMPLES["SiteResponse"]], "total": 1, "page": 1, "page_size": 20, "pages": 1},
    "Page_SensorResponse_": {"items": [_SCHEMA_EXAMPLES["SensorResponse"]], "total": 1, "page": 1, "page_size": 20, "pages": 1},
    "Page_ReadingResponse_": {"items": [_SCHEMA_EXAMPLES["ReadingResponse"]], "total": 1, "page": 1, "page_size": 20, "pages": 1},
    "Page_AlertResponse_": {"items": [_SCHEMA_EXAMPLES["AlertResponse"]], "total": 1, "page": 1, "page_size": 20, "pages": 1},
    "Page_DocumentResponse_": {"items": [_SCHEMA_EXAMPLES["DocumentResponse"]], "total": 1, "page": 1, "page_size": 20, "pages": 1},
    "Page_InvitationResponse_": {"items": [], "total": 0, "page": 1, "page_size": 20, "pages": 0},
    "Page_UserAdminResponse_": {"items": [_SCHEMA_EXAMPLES["UserAdminResponse"]], "total": 1, "page": 1, "page_size": 20, "pages": 1},
}


def _add_schema_examples(schemas: dict[str, Any]) -> None:
    """Añade ejemplos completos a los schemas generados por FastAPI."""
    for name, example in {**_SCHEMA_EXAMPLES, **_PAGE_EXAMPLES}.items():
        if name in schemas:
            schemas[name]["examples"] = [example]


def _normalize_validation_responses(schema: dict[str, Any]) -> None:
    """Documenta el 422 automático con el envelope real de la API."""
    validation_example = {
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Los datos enviados no son válidos.",
            "details": [
                {
                    "field": "page",
                    "message": "Input should be greater than or equal to 1",
                    "type": "greater_than_equal",
                }
            ],
        }
    }
    for path_item in schema.get("paths", {}).values():
        for operation in path_item.values():
            if not isinstance(operation, dict):
                continue
            response = operation.get("responses", {}).get("422")
            if response is None:
                continue
            existing_content = response.get("content", {}).get("application/json", {})
            existing_schema = existing_content.get("schema", {}).get("$ref", "")
            # Los 422 declarados con `error_response` ya llevan el código
            # de negocio (por ejemplo EMPTY_FILE o FLOOR_OUT_OF_SITE).
            # Solo sustituimos el 422 genérico que FastAPI añade por
            # validación de Pydantic.
            if existing_content.get("example") or not existing_schema.endswith(
                "/HTTPValidationError"
            ):
                continue
            response["description"] = "Los datos enviados no son válidos (`VALIDATION_ERROR`)."
            response["content"] = {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                    "example": validation_example,
                }
            }


def _contract_schemas() -> dict[str, Any]:
    """
    Genera las definiciones JSON Schema de los modelos de arriba.

    `models_json_schema` resuelve de una vez todo el grupo, de modo que
    las referencias entre ellos (`SessionResponse` → `UserResponse`)
    apunten al mismo sitio en lugar de duplicar la definición.

    `ref_template` es lo que hace que las referencias internas apunten a
    `#/components/schemas/...`, que es donde OpenAPI las espera. Por
    defecto Pydantic las pondría en `#/$defs/...` y Swagger las mostraría
    rotas.
    """
    _, top_level = models_json_schema(
        [(model, "validation") for model in CONTRACT_MODELS],
        ref_template="#/components/schemas/{model}",
    )
    schemas = top_level.get("$defs", {})
    for enum in CONTRACT_ENUMS:
        schemas.setdefault(enum.__name__, TypeAdapter(enum).json_schema())
    return schemas


def register_contract_schemas(app: FastAPI) -> None:
    """
    Sustituye `app.openapi` por una versión que añade los contratos.

    Se envuelve la función original en lugar de reescribir la generación
    entera: así todo lo que FastAPI deduce de las rutas sigue igual, y
    esto solo añade.
    """
    original: Callable[[], dict[str, Any]] = app.openapi

    def openapi_with_contracts() -> dict[str, Any]:
        schema = original()
        schemas = schema.setdefault("components", {}).setdefault("schemas", {})
        for name, definition in _contract_schemas().items():
            # `setdefault` y no asignación directa: si un modelo ya salió
            # por una ruta real, manda esa versión. Aquí solo se rellenan
            # los que faltan.
            schemas.setdefault(name, definition)
        _add_schema_examples(schemas)
        _normalize_validation_responses(schema)

        # FastAPI genera el multipart de documentos a partir de la firma de
        # la ruta. El schema tiene un nombre interno, por lo que el ejemplo
        # se fija en el operation para que Swagger lo muestre siempre.
        upload = schema.get("paths", {}).get("/api/documents", {}).get("post")
        if upload:
            multipart = upload.get("requestBody", {}).get("content", {}).get(
                "multipart/form-data"
            )
            if multipart is not None:
                multipart["example"] = {
                    "file": "<bytes de plano-planta-baja.pdf>",
                    "site_id": "33333333-3333-4333-8333-333333333333",
                    "kind": "PLAN",
                }

        # La exportación ofrece dos representaciones. El CSV no puede usar
        # un schema JSON, así que se documenta con una fila real de ejemplo.
        export = schema.get("paths", {}).get("/api/analytics/export", {}).get("get")
        if export:
            content = export.get("responses", {}).get("200", {}).get("content", {})
            json_content = content.get("application/json")
            if json_content is not None:
                json_content["example"] = [
                    {
                        "date": "2026-10-14",
                        "organization": "Hotel Diagonal Mar",
                        "site": "Torre Diagonal",
                        "sensor_id": "44444444-4444-4444-8444-444444444444",
                        "sensor_external_id": "SENS-001",
                        "sensor_name": "Presión entrada",
                        "unit": "bar",
                        "readings_count": 96,
                        "pressure_min": 2.8,
                        "pressure_avg": 3.4,
                        "pressure_max": 4.1,
                        "alerts_total": 1,
                        "alerts_critical": 0,
                        "alerts_resolved": 1,
                    }
                ]
            csv_content = content.get("text/csv")
            if csv_content is not None:
                csv_content["example"] = (
                    "date,organization,site,sensor_id,sensor_external_id,sensor_name,"
                    "unit,readings_count,pressure_min,pressure_avg,pressure_max,"
                    "alerts_total,alerts_critical,alerts_resolved\n"
                    "2026-10-14,Hotel Diagonal Mar,Torre Diagonal,"
                    "44444444-4444-4444-8444-444444444444,SENS-001,"
                    "Presión entrada,bar,96,2.8,3.4,4.1,1,0,1\n"
                )
        # FastAPI cachea el documento en este atributo; se actualiza para
        # que la siguiente petición a /api/openapi.json no lo regenere.
        app.openapi_schema = schema
        return schema

    app.openapi = openapi_with_contracts  # type: ignore[method-assign]
