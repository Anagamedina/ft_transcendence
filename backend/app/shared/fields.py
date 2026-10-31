"""
Shared rules for the fields of people and organizations.

Like `shared/passwords.py`: one rule per piece of data, used by every
route where that data is written (create, edit, sign-up, invitation,
"Hazte cliente"). Before, each route had its own, and the same phone
number or tax id was accepted in one place and rejected in another.

Each function returns the already normalized value, which is what gets
stored, or stops with a 422 and its own code (`INVALID_NAME`,
`INVALID_PHONE`, `INVALID_TAX_ID`, `INVALID_POSTAL_CODE`, `INVALID_IBAN`)
so the form knows which field to mark. That is why they live in the
service and not in the schema: the schema would only give the generic
`VALIDATION_ERROR`.

The same rules, with the same messages, are in
`frontend/src/utils/validation.js`. If you change one, change both.
"""

from __future__ import annotations

import re
import unicodedata

from app.core.exceptions import DomainValidationError

_ESPACIOS = re.compile(r"\s+")
# Separators people type in tax ids, IBANs and phone numbers.
_SEPARADORES = re.compile(r"[\s.\-]")
_SEPARADORES_TELEFONO = re.compile(r"[\s.\-()]")

# Spanish phone: 9 digits starting with 6 or 7 (mobile) or 8 or 9
# (landline), with an optional +34 or 0034 prefix.
_TELEFONO = re.compile(r"^[6789][0-9]{8}$")
# NIF, NIE, CIF or another country's tax id, without separators.
_TAX_ID = re.compile(r"^[A-Z0-9]{8,15}$")
# Spanish IBAN: ES and 22 digits. The check digits are not verified.
_IBAN = re.compile(r"^ES[0-9]{22}$")
# Spanish postal code: five digits.
_POSTAL_CODE = re.compile(r"^[0-9]{5}$")
# Besides letters and spaces, a person's name can have apostrophes
# (O'Neill), hyphens (Pérez-Gil) and periods (Laura P.).
_SIGNOS_NOMBRE = frozenset("'’-.")
# And an organization's name, besides numbers, the signs used in company
# names: "Hotel Mar, S.L.", "Ca n'Oller", "Mar & Sol (Gràcia)".
_SIGNOS_ORGANIZACION = frozenset(".,'’-&()")


MENSAJE_NOMBRE_ORGANIZACION = (
    "El nombre solo puede tener letras, números, espacios y los signos . , ' - & ( )."
)


def clean_text(valor: str | None) -> str | None:
    """
    '  Hotel   Mar ' → 'Hotel Mar'. An empty text becomes `None`.

    NFC joins a letter and its accent into one character: "ò" typed as
    "o" + "̀" and a single-character "ò" are the same name.
    """
    if valor is None:
        return None
    texto = _ESPACIOS.sub(" ", unicodedata.normalize("NFC", valor)).strip()
    return texto or None


def normalize_email(valor: str) -> str:
    """' Ana@X.com ' → 'ana@x.com': the same email, however it is typed."""
    return valor.strip().lower()


def person_name(valor: str | None) -> str:
    """Name of a person: letters, spaces, `'`, `-` and `.`."""
    nombre = clean_text(valor)
    if nombre is None:
        _invalido("name", "El nombre no puede estar vacío.", "INVALID_NAME")
    if not any(c.isalpha() for c in nombre) or not all(
        c.isalpha() or c == " " or c in _SIGNOS_NOMBRE for c in nombre
    ):
        _invalido(
            "name",
            "El nombre solo puede tener letras, espacios, apóstrofos, guiones y puntos.",
            "INVALID_NAME",
        )
    return nombre


def organization_name(valor: str | None, campo: str = "name") -> str:
    """
    Name of an organization: letters (with accents, "ñ" and "ç"), numbers,
    spaces and the signs `. , ' ’ - & ( )`, with at least one letter or
    number. `@`, `#`, `/`, `<`, `!`… are left out: they are not part of a
    company name.
    """
    nombre = clean_text(valor)
    if nombre is None:
        _invalido(campo, "El nombre no puede estar vacío.", "INVALID_NAME")
    if not any(c.isalnum() for c in nombre) or not all(
        c.isalnum() or c == " " or c in _SIGNOS_ORGANIZACION for c in nombre
    ):
        _invalido(campo, MENSAJE_NOMBRE_ORGANIZACION, "INVALID_NAME")
    return nombre


def normalize_phone(valor: str | None) -> str:
    """'612.34.56.78', '+34 612345678' o '0034 612 345 678' → '+34 612 345 678'."""
    numero = _SEPARADORES_TELEFONO.sub("", valor or "")
    if numero.startswith("+34"):
        numero = numero[3:]
    elif numero.startswith("0034"):
        numero = numero[4:]
    if not numero:
        _invalido("phone", "El teléfono es obligatorio.", "INVALID_PHONE")
    if not _TELEFONO.match(numero):
        _invalido(
            "phone",
            "Escribe un teléfono español de 9 cifras, por ejemplo 612 345 678.",
            "INVALID_PHONE",
        )
    return f"+34 {numero[:3]} {numero[3:6]} {numero[6:]}"


def normalize_tax_id(valor: str) -> str:
    """'b-1234 5678' → 'B12345678', o 422 `INVALID_TAX_ID`."""
    tax_id = _SEPARADORES.sub("", valor).upper()
    if not _TAX_ID.match(tax_id):
        raise DomainValidationError(
            "El NIF o CIF no es válido.",
            details={"field": "tax_id", "message": "Entre 8 y 15 letras o números."},
            code="INVALID_TAX_ID",
        )
    return tax_id


def check_postal_code(valor: str) -> str:
    """'08002' → '08002', o 422 `INVALID_POSTAL_CODE`."""
    postal_code = valor.strip()
    if not _POSTAL_CODE.match(postal_code):
        raise DomainValidationError(
            "El código postal no es válido.",
            details={"field": "postal_code", "message": "Cinco cifras."},
            code="INVALID_POSTAL_CODE",
        )
    return postal_code


def mask_iban(valor: str) -> str:
    """
    Masked Spanish IBAN, or 422 `INVALID_IBAN`.

        'ES91 2100 0418 4502 0005 1332' → 'ES** **** **** **** **** 1332'

    Only the shape is checked (`ES` and 22 digits), not the check digits:
    there is no real charge, and a stricter rule would only block a
    subscription over one mistyped digit.
    """
    iban = _SEPARADORES.sub("", valor).upper()
    if not _IBAN.match(iban):
        raise DomainValidationError(
            "El IBAN no es válido.",
            details={"field": "iban", "message": "ES y 22 cifras."},
            code="INVALID_IBAN",
        )
    oculto = iban[:2] + "*" * (len(iban) - 6) + iban[-4:]
    return " ".join(oculto[i : i + 4] for i in range(0, len(oculto), 4))


def _invalido(campo: str, mensaje: str, codigo: str) -> None:
    raise DomainValidationError(
        mensaje, details={"field": campo, "message": mensaje}, code=codigo
    )
