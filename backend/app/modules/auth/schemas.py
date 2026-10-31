# SCHEMAS — auth
# Pydantic request/response (OpenAPI contract). Never return a raw ORM model.
"""
Authentication contract (issue #23).

A detail that shapes all these schemas: **the session travels in an
httpOnly cookie, not in the response body** (ADR 0001,
`docs/decisions/0001-auth-cookie.md`).

That is why there is no `TokenResponse` with an `access_token` inside.
Login returns the user and attaches the cookie through the `Set-Cookie`
header. JavaScript cannot read an httpOnly cookie, which closes the XSS
token theft path a JWT stored in `localStorage` would have.

Consequence for the frontend: calls must use `withCredentials: true` in
Axios. Without it the browser does not send the cookie and everything
answers 401.
"""

from __future__ import annotations

from pydantic import EmailStr, Field

from app.modules.users.schemas import UserResponse
from app.shared.passwords import PASSWORD_MAX_LENGTH, PASSWORD_MIN_LENGTH
from app.shared.schemas import ApiModel, ApiRequest, Password, RawPassword


class RegisterRequest(ApiRequest):
    """
    Public sign-up (B10, issue #140): anyone creates their account and,
    with it, their organization on trial.

    It no longer inherits from the old `UserCreate`, which was removed.
    Until B10 the sign-up was the creation of a client by an admin, with
    `organization_id`; now whoever signs up has no organization yet: they
    create it with `organization_name`. Users of an existing organization
    arrive through an invitation (B4).

    The password is only capped here at 128 characters. The real rule (12
    at least, not common, without the email) is applied by the service
    with `check_password`, to answer `WEAK_PASSWORD` and not the generic
    `VALIDATION_ERROR`.
    """

    name: str = Field(
        min_length=1,
        max_length=120,
        description="Name of the person signing up.",
        examples=["Ana Medina"],
    )
    email: EmailStr = Field(
        description="Account email. Unique in the whole system.",
        examples=["ana@hotelmar.com"],
    )
    password: Password = Field(
        max_length=PASSWORD_MAX_LENGTH,
        description=(
            f"At least {PASSWORD_MIN_LENGTH} characters, not a common "
            "password and not containing the email. Otherwise, 422 "
            "`WEAK_PASSWORD`."
        ),
        examples=["agua-que-no-se-escapa"],
    )
    organization_name: str = Field(
        max_length=120,
        description=(
            "Name of the organization created, on trial. Unique ignoring "
            "case."
        ),
        examples=["Hotel Mar"],
    )
    accept_terms: bool = Field(
        description=(
            "Must be `true`: whoever signs up accepts the terms of use. "
            "Otherwise, 422 `TERMS_NOT_ACCEPTED`."
        ),
        examples=[True],
    )


class LoginRequest(ApiRequest):
    email: EmailStr = Field(
        description="Account email.", examples=["ana@aquaguard.dev"]
    )
    password: RawPassword = Field(
        min_length=1,
        description=(
            "Password. The password rule is NOT applied here: on login, "
            "whatever the user types must be accepted and 401 returned if "
            "it does not match. Rejecting it with a 422 for its length "
            "would reveal which passwords do not exist in the system. It "
            "is compared as is, without trimming spaces, and one longer "
            f"than {PASSWORD_MAX_LENGTH} characters is 401 without reaching "
            "Argon2."
        ),
        examples=["una-contrasena-larga"],
    )


class SessionResponse(ApiModel):
    """
    Response of login, sign-up (B10) and `GET /api/me`.

    It returns the user, not a token: the token goes in the cookie.
    """

    user: UserResponse


class MessageResponse(ApiModel):
    """
    Response of operations without content of their own, like logout.

    Preferred over a `204 No Content` because the frontend already has a
    common handler that expects a JSON body across the API, and a 204
    without a body would need a special case.
    """

    message: str = Field(examples=["Sesión cerrada."])
