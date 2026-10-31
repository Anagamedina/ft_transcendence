# ROUTER — auth
# Thin HTTP layer: validates schemas → calls the service → answers.
"""
Authentication endpoints (`/api/auth/...`).

The router is registered since issue #22. The endpoints are from issue
#26, all three implemented:

    POST /api/auth/login      → opens the session (cookie)
    POST /api/auth/logout     → closes it
    POST /api/auth/register   → public sign-up with a 7-day trial
                                 (B10, #140); opens the session like login

A split worth keeping: **the router sets the session cookie, not the
service**. A cookie is an HTTP header, and the service by definition does
not speak HTTP.

    service → checks the credentials and returns the user
    router  → turns that into a `Set-Cookie`

See `docs/decisions/0001-auth-cookie.md`: the session travels in an
httpOnly cookie, not in a JWT inside the JSON.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.core.security import (
    SESSION_COOKIE,
    SESSION_MAX_AGE_SECONDS,
    create_session_token,
    session_cookie_kwargs,
)
from app.modules.auth.schemas import (
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    SessionResponse,
)
from app.modules.auth.service import AuthService, get_auth_service
from app.shared.schemas import error_response

router = APIRouter(prefix="/auth", tags=["Auth"])

AuthSvc = Annotated[AuthService, Depends(get_auth_service)]


@router.post(
    "/logout",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Log out",
    description=(
        "Deletes the session cookie from the browser.\n\n"
        "**It does not require being authenticated, on purpose.** Logging "
        "out must always work: with an expired session, a broken cookie "
        "or none at all. If it required a valid session, whoever most "
        "needs to log out — someone with a session in a bad state — would "
        "be exactly who could not."
    ),
)
def logout(response: Response, service: AuthSvc) -> MessageResponse:
    # On the server side there is nothing to invalidate: the session is a
    # stateless signed cookie. It is called anyway because it is where
    # revocation would go the day it exists (see the service).
    service.logout()

    # The attributes must be the same it was set with, or the browser would
    # treat it as a different cookie and not delete it.
    response.delete_cookie(SESSION_COOKIE, **session_cookie_kwargs())

    return MessageResponse(message="Sesión cerrada.")


@router.post(
    "/login",
    response_model=SessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Log in",
    description=(
        "Checks the credentials and leaves the session open in an "
        "`httpOnly` cookie.\n\n"
        "It returns the user, **not a token**: the token goes in the "
        "cookie, where JavaScript cannot read it (ADR 0001).\n\n"
        "A missing email and a wrong password answer the same, and take "
        "the same time: telling them apart would reveal which accounts are "
        "registered."
    ),
    responses={
        **error_response(
            status.HTTP_401_UNAUTHORIZED,
            "Wrong email or password (`UNAUTHORIZED`).",
        ),
    },
)
def login(
    payload: LoginRequest,
    response: Response,
    service: AuthSvc,
) -> SessionResponse:
    usuario = service.login(payload)

    # The router sets the cookie, not the service: a cookie is an HTTP
    # header, and the service does not speak HTTP.
    response.set_cookie(
        SESSION_COOKIE,
        create_session_token(usuario.id),
        max_age=SESSION_MAX_AGE_SECONDS,
        **session_cookie_kwargs(),
    )

    return SessionResponse(user=usuario)


@router.post(
    "/register",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Sign up",
    description=(
        "Public sign-up: creates the organization `organization_name` **on "
        "trial** (`TRIAL`, expiring after `TRIAL_DAYS` days, 7 by default) "
        "and the client account inside it.\n\n"
        "**It needs no session and leaves the session open**, like login: "
        "whoever signs up goes straight to their panel.\n\n"
        "The password needs at least 12 characters, cannot be a common "
        "password nor contain the email."
    ),
    responses={
        **error_response(
            status.HTTP_409_CONFLICT,
            "That email already exists (`EMAIL_ALREADY_EXISTS`) or there is "
            "already an organization with that name (`ORGANIZATION_NAME_TAKEN`).",
        ),
        **error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Terms not accepted (`TERMS_NOT_ACCEPTED`), weak password "
            "(`WEAK_PASSWORD`), invalid person or organization name "
            "(`INVALID_NAME`, field in `details.field`) or malformed "
            "fields (`VALIDATION_ERROR`).",
        ),
    },
)
def register(
    payload: RegisterRequest,
    response: Response,
    service: AuthSvc,
) -> SessionResponse:
    creado = service.register(payload)

    # Same as login: the router sets the cookie.
    response.set_cookie(
        SESSION_COOKIE,
        create_session_token(creado.id),
        max_age=SESSION_MAX_AGE_SECONDS,
        **session_cookie_kwargs(),
    )

    return SessionResponse(user=creado)
