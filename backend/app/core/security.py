# SECURITY — password hashing and session cookie signing.
"""
The two cryptographic operations of issue #26.

--------------------------------------------------------------------
WHAT IT DOES AND DOES NOT DO
--------------------------------------------------------------------
No business decision is made here: it does not check whether a user
exists or has permission. That belongs to the service. This module only
knows how to turn a password into a hash, compare a password with a hash,
and put an id into a signed string and get it back out.

It is kept apart for two concrete reasons:

1. It is the only part of the backend to review if the algorithm changes
   tomorrow. Spread across the services, that change would mean searching
   the whole project.
2. It is tested on its own, without a database and without starting the
   application.

--------------------------------------------------------------------
WHY ARGON2 AND NOT A NORMAL HASH
--------------------------------------------------------------------
`sha256("my-password")` is very fast, and that is exactly the problem: a
graphics card tries billions per second. Argon2 is designed to be **slow
on purpose** and to use memory, so brute force is expensive even if the
hashes are stolen.

It also salts each password automatically. The *salt* is a random value
mixed in before computing the hash and stored inside it: two people with
the same password get different hashes, and a precomputed table is
useless.

--------------------------------------------------------------------
WHY A SIGNED COOKIE AND NOT A JWT IN localStorage
--------------------------------------------------------------------
ADR 0001 decides it. In short: whatever lives in `localStorage` can be
read by any JavaScript on the page, so an injected script steals the
session. JavaScript cannot read an `httpOnly` cookie — it just travels
with each request.

**Signed is not the same as encrypted.** Whoever has the cookie can read
the id inside it; what they cannot do is change it, because the signature
would no longer match. That is why only the user id goes inside: no data
that matters if it is read.
"""

from __future__ import annotations

from uuid import UUID

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.core.app_config import app_settings

# Cookie name. A constant so the router and the tests do not each type it
# by hand.
SESSION_COOKIE = "aquaguard_session"

# How long a session lasts before asking to log in again. Eight hours is a
# working day: whoever logs in in the morning does not have to repeat it
# after lunch, and the session does not stay alive forever on a shared
# computer.
SESSION_MAX_AGE_SECONDS = 8 * 60 * 60

# The "purpose" of the signature. Two strings signed with the same key but
# a different `salt` are not interchangeable, so a session token could not
# be slipped in tomorrow where a password-reset one is expected.
_SESSION_SALT = "aquaguard.session.v1"

_hasher = PasswordHasher()


def _serializer() -> URLSafeTimedSerializer:
    """
    Cookie signer.

    It is built on each call instead of kept in a module variable, on
    purpose: that way it reads `SECRET_KEY` when it is used. Cached, a
    test that changes the key would keep signing with the old one and pass
    for the wrong reasons.
    """
    return URLSafeTimedSerializer(app_settings.SECRET_KEY, salt=_SESSION_SALT)


def session_cookie_kwargs() -> dict[str, object]:
    """
    Attributes used to set and to delete the session cookie.

    They live here, and are not typed by hand in each endpoint, because
    **deleting a cookie requires repeating the same attributes it was set
    with**. If logout used a different `path` than login, the browser
    would treat it as another cookie and not delete it: the user would
    think they had logged out and would still be in.

    - `httponly`: JavaScript cannot read it (ADR 0001).
    - `secure`: only sent over HTTPS. Locally it is False because it is
      served over http; in production it is enabled from `.env`.
    - `samesite="lax"`: not sent on requests coming from another site,
      except when navigating. It stops most CSRF attacks without breaking
      arriving at the application from an external link.
    """
    return {
        "httponly": True,
        "secure": app_settings.COOKIE_SECURE,
        "samesite": "lax",
        "path": "/",
    }


def hash_password(password: str) -> str:
    """
    Turns a password into the hash stored in the database.

    The resulting string already holds the algorithm, its parameters and
    the salt, so nothing else needs to be stored in another column.
    """
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """
    Checks whether a password matches a hash.

    Returns `False` instead of raising, also when the hash is corrupt or
    has a format Argon2 does not recognize. The caller only needs to know
    whether it gets in, and an `InvalidHashError` escaping from here would
    end in a 500 instead of the right 401.
    """
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, InvalidHashError):
        return False


def needs_rehash(password_hash: str) -> bool:
    """
    Tells whether the hash should be recomputed with today's parameters.

    Argon2 recommends raising the cost as hardware improves. When that
    happens, old hashes stay valid but become weak, and this is the moment
    to renew them: at login we have the plain password, the only time it
    can be redone.
    """
    try:
        return _hasher.check_needs_rehash(password_hash)
    except InvalidHashError:
        return False


def create_session_token(user_id: UUID) -> str:
    """
    Creates the signed content of the session cookie.

    It only holds the user id. Neither the role nor the organization: if
    they were inside, changing someone's role would have no effect until
    they logged in again. With only the id, each request reads the user
    from the database and sees their real state.
    """
    return _serializer().dumps(str(user_id))


def read_session_token(token: str) -> UUID | None:
    """
    Gets the user id out of the cookie, or `None` if it is not valid.

    Returns `None` in the three cases where it cannot be trusted: a
    signature that does not match (tampered with or from another key), an
    expired session, or content that is not a UUID. The caller treats them
    the same — no session — and they should not be told apart outside:
    telling someone "your signature is invalid" versus "it has expired"
    gives them information about what is failing in their attempt.
    """
    try:
        raw = _serializer().loads(token, max_age=SESSION_MAX_AGE_SECONDS)
    except (BadSignature, SignatureExpired):
        return None

    try:
        return UUID(raw)
    except (ValueError, TypeError, AttributeError):
        return None
