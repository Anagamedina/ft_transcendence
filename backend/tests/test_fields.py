"""
Reglas comunes de los campos (`app/shared/fields.py`).

Las rutas que las usan (alta y edición de clientes, registro, invitación,
"Hazte cliente", Mi cuenta) tienen sus propios tests; aquí se prueba cada
regla una vez, con los casos límite.
"""

import pytest

from app.core.exceptions import DomainValidationError
from app.shared.fields import (
    clean_text,
    normalize_email,
    normalize_phone,
    organization_name,
    person_name,
)


def _codigo(funcion, valor):
    with pytest.raises(DomainValidationError) as exc:
        funcion(valor)
    return exc.value.code


@pytest.mark.parametrize(
    "valor",
    ["612345678", "612 345 678", "612.34.56.78", "612-345-678", "+34 612 345 678",
     "+34612345678", "0034 612 345 678", "(+34) 612 34 56 78"],
)
def test_telefono_espanol_en_cualquier_formato(valor):
    assert normalize_phone(valor) == "+34 612 345 678"


def test_telefono_fijo():
    assert normalize_phone("93 123 45 67") == "+34 931 234 567"


@pytest.mark.parametrize(
    "valor",
    ["", "   ", None, "12345678", "512345678", "6123456789", "+33 612 345 678",
     "612 345 67a", "+34"],
)
def test_telefono_no_valido(valor):
    assert _codigo(normalize_phone, valor) == "INVALID_PHONE"


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [("Hotel Mar", "Hotel Mar"), ("  Hotel   Mar  ", "Hotel Mar"),
     ("Hotel Gòtic", "Hotel Gòtic"), ("Comunidad Mallorca 401", "Comunidad Mallorca 401"),
     ("Aigües Zona Franca", "Aigües Zona Franca"), ("Ca n'Oller", "Ca n'Oller"),
     ("Hotel Mar, S.L.", "Hotel Mar, S.L."), ("Mar & Sol (Gràcia)", "Mar & Sol (Gràcia)"),
     ("  Hotel   Mar,  S.L. ", "Hotel Mar, S.L.")],
)
def test_nombre_de_organizacion(valor, esperado):
    assert organization_name(valor) == esperado


@pytest.mark.parametrize(
    "valor", ["", "   ", "Mar!", "A/B", "Hotel@Mar", "Hotel #1", "<script>", "...", "&"]
)
def test_nombre_de_organizacion_con_signos_no_permitidos_o_vacio(valor):
    assert _codigo(organization_name, valor) == "INVALID_NAME"


def test_el_acento_compuesto_es_el_mismo_nombre():
    # «ò» escrito como «o» + acento combinado
    assert organization_name("Hotel Gòtic") == "Hotel Gòtic"


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [("Ana Medina", "Ana Medina"), (" Laura   P. ", "Laura P."),
     ("María O'Neill-Pérez", "María O'Neill-Pérez"), ("Jordi Pujol i Soley", "Jordi Pujol i Soley")],
)
def test_nombre_de_persona(valor, esperado):
    assert person_name(valor) == esperado


@pytest.mark.parametrize("valor", ["", "   ", "Ana 2", "ana@mar.dev", "<script>", "..."])
def test_nombre_de_persona_no_valido(valor):
    assert _codigo(person_name, valor) == "INVALID_NAME"


def test_textos_y_emails():
    assert clean_text("  Carrer   de la Lluna 1 ") == "Carrer de la Lluna 1"
    assert clean_text("   ") is None
    assert clean_text(None) is None
    assert normalize_email(" Ana@Mar.DEV ") == "ana@mar.dev"
