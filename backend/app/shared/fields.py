"""
Reglas comunes de los campos de personas y organizaciones.

Igual que `shared/passwords.py`: una sola regla por dato, la usan todas las
rutas donde ese dato se escribe (alta, edición, registro, invitación,
"Hazte cliente"). Antes cada ruta tenía la suya y un mismo teléfono o NIF
se aceptaba en un sitio y se rechazaba en otro.

Cada función devuelve el valor ya normalizado, que es lo que se guarda, o
corta con 422 y un código propio (`INVALID_NAME`, `INVALID_PHONE`,
`INVALID_TAX_ID`, `INVALID_POSTAL_CODE`, `INVALID_IBAN`) para que el
formulario sepa qué campo marcar. Por eso viven en el service y no en el
schema: el schema solo daría el genérico `VALIDATION_ERROR`.

Las mismas reglas, con los mismos mensajes, están en
`frontend/src/utils/validation.js`. Si cambias una, cambia las dos.
"""

from __future__ import annotations

import re
import unicodedata

from app.core.exceptions import DomainValidationError

_ESPACIOS = re.compile(r"\s+")
# Separadores que la gente escribe en NIF, IBAN y teléfonos.
_SEPARADORES = re.compile(r"[\s.\-]")
_SEPARADORES_TELEFONO = re.compile(r"[\s.\-()]")

# Teléfono español: 9 cifras que empiezan por 6 o 7 (móvil) o por 8 o 9
# (fijo), con el prefijo +34 o 0034 opcional.
_TELEFONO = re.compile(r"^[6789][0-9]{8}$")
# NIF, NIE, CIF o el identificador fiscal de otro país, ya sin separadores.
_TAX_ID = re.compile(r"^[A-Z0-9]{8,15}$")
# IBAN español: ES, dígitos de control (2) y la cuenta (20 cifras).
_IBAN = re.compile(r"^ES[0-9]{22}$")
# Código postal español: cinco cifras.
_POSTAL_CODE = re.compile(r"^[0-9]{5}$")
# Además de letras y espacios, un nombre de persona puede tener
# apóstrofos (O'Neill), guiones (Pérez-Gil) y puntos (Laura P.).
_SIGNOS_NOMBRE = frozenset("'’-.")
# Y el de una organización, además de números, los signos de los nombres
# de empresa: «Hotel Mar, S.L.», «Ca n'Oller», «Mar & Sol (Gràcia)».
_SIGNOS_ORGANIZACION = frozenset(".,'’-&()")


MENSAJE_NOMBRE_ORGANIZACION = (
    "El nombre solo puede tener letras, números, espacios y los signos . , ' - & ( )."
)


def clean_text(valor: str | None) -> str | None:
    """
    '  Hotel   Mar ' → 'Hotel Mar'. Un texto vacío pasa a `None`.

    NFC junta la letra y su acento en un solo carácter: «ò» escrito como
    «o» + «̀» y «ò» de un solo carácter son el mismo nombre.
    """
    if valor is None:
        return None
    texto = _ESPACIOS.sub(" ", unicodedata.normalize("NFC", valor)).strip()
    return texto or None


def normalize_email(valor: str) -> str:
    """' Ana@X.com ' → 'ana@x.com': el mismo email, escrito como sea."""
    return valor.strip().lower()


def person_name(valor: str | None) -> str:
    """Nombre de una persona: letras, espacios, `'`, `-` y `.`."""
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
    Nombre de una organización: letras (con acentos, «ñ» y «ç»), números,
    espacios y los signos `. , ' ’ - & ( )`, con al menos una letra o un
    número. Fuera quedan `@`, `#`, `/`, `<`, `!`… que no forman parte del
    nombre de una empresa.
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
    IBAN comprobado y enmascarado, o 422 `INVALID_IBAN`.

        'ES91 2100 0418 4502 0005 1332' → 'ES** **** **** **** **** 1332'

    La comprobación es la de ISO 13616: se pasan los cuatro primeros
    caracteres al final, cada letra se cambia por un número (A=10 … Z=35)
    y el resultado módulo 97 tiene que dar 1.
    """
    iban = _SEPARADORES.sub("", valor).upper()
    valido = bool(_IBAN.match(iban))
    if valido:
        reordenado = iban[4:] + iban[:4]
        valido = int("".join(str(int(c, 36)) for c in reordenado)) % 97 == 1
    if not valido:
        raise DomainValidationError(
            "El IBAN no es válido.",
            details={"field": "iban", "message": "Revisa los dígitos de la cuenta."},
            code="INVALID_IBAN",
        )
    oculto = iban[:2] + "*" * (len(iban) - 6) + iban[-4:]
    return " ".join(oculto[i : i + 4] for i in range(0, len(oculto), 4))


def _invalido(campo: str, mensaje: str, codigo: str) -> None:
    raise DomainValidationError(
        mensaje, details={"field": campo, "message": mensaje}, code=codigo
    )
