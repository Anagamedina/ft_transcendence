# SCHEMAS — users
# Pydantic request/response (contrato OpenAPI). No devolver model ORM crudo.
"""
Contrato de usuarios (issue #23).

El punto importante de este archivo es la separación entre lo que entra y
lo que sale:

    UserCreate   → password    (entra, nunca sale)
    UserResponse → sin password ni hash

Es tentador declarar un único `User` y reutilizarlo en las dos
direcciones. No se hace porque el día que el modelo gane un campo
`password_hash` o `reset_token`, ese campo aparecería solo en la respuesta
de la API. Con schemas separados eso no puede ocurrir: `UserResponse`
únicamente copia los campos que declara.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import EmailStr, Field

from app.shared.schemas import ApiModel, ApiRequest


class UserRole(str, Enum):
    """
    Rol dentro de la aplicación.

    Hereda de `str` para que serialice como `"admin"` y no como
    `"UserRole.ADMIN"`, y para poder compararlo con una cadena sin
    convertir. En OpenAPI aparece como un enum de strings, que es lo que
    el frontend necesita para pintar el selector.

    - `admin`  → gestiona organizaciones, sites y sensores.
    - `client` → solo ve los datos de su propia organización.
    """

    ADMIN = "admin"
    CLIENT = "client"


class UserBase(ApiRequest):
    email: EmailStr = Field(
        description="Email del usuario. Único en todo el sistema.",
        examples=["admin@hotel.com"],
    )
    name: str = Field(
        min_length=1,
        max_length=120,
        description="Nombre para mostrar.",
        examples=["Ana Medina"],
    )


class UserCreate(UserBase):
    """Alta de usuario. La contraseña entra por aquí y no sale nunca."""

    password: str = Field(
        min_length=8,
        max_length=128,
        description=(
            "Contraseña en claro. Se envía solo por HTTPS y se guarda "
            "hasheada (issue #26). El mínimo de 8 se valida aquí para no "
            "llegar al service con algo que ya se sabe inválido."
        ),
        examples=["una-contrasena-larga"],
    )


class UserUpdate(ApiRequest):
    """
    Modificación parcial. Todos los campos son opcionales.

    `None` y "campo ausente" significan cosas distintas: para saber cuáles
    tocó el cliente hay que usar `model_dump(exclude_unset=True)`, no
    `exclude_none`.
    """

    name: str | None = Field(default=None, min_length=1, max_length=120)
    role: UserRole | None = None


class UserResponse(ApiModel):
    """
    Usuario tal y como lo ve el cliente.

    Campos según el modelo de dominio del documento de arquitectura
    (apartado 5): `id`, `organization_id`, `name`, `email`, `role`,
    `created_at`. `password_hash` existe en la tabla y NO aparece aquí:
    es justamente lo que garantiza la separación entrada/salida.
    """

    id: UUID = Field(description="Identificador del usuario.")
    email: EmailStr
    name: str
    role: UserRole
    organization_id: UUID | None = Field(
        default=None,
        description=(
            "Organización a la que pertenece. Nulo para un admin global, "
            "que no está atado a ninguna."
        ),
    )
    created_at: datetime = Field(description="Alta del usuario, en UTC.")
