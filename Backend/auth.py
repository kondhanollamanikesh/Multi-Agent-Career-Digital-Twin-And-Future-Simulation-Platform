# ============================================================
# Career Digital Twin - Authentication
# ============================================================
#
# Full login/auth system:
#   - bcrypt password hashing (never stores plain text)
#   - JWT bearer tokens (HS256)
#   - get_current_user FastAPI dependency
#
# The signing secret is read from .env (JWT_SECRET_KEY).
# If it is missing, one is generated and persisted so
# existing sessions survive server restarts.
# ============================================================

import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
from dotenv import load_dotenv

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


load_dotenv()


# ============================================================
# 1. CONFIGURATION
# ============================================================

ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_DAYS = 7

ENV_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    ".env"
)


# ============================================================
# 2. SIGNING SECRET
# ============================================================
#
# Read from .env. If absent, generate a strong secret and
# persist it so tokens do not break on every restart.
# ============================================================

def _resolve_secret() -> str:

    secret = os.getenv("JWT_SECRET_KEY")

    if secret and secret.strip():

        return secret.strip()

    print(
        "[Auth] JWT_SECRET_KEY missing from .env - "
        "generating and saving one."
    )

    secret = secrets.token_urlsafe(64)

    try:

        lines = []

        if os.path.exists(ENV_PATH):

            with open(
                ENV_PATH, "r", encoding="utf-8"
            ) as file:

                lines = file.read().splitlines()

        # Do not duplicate the key if it already exists.

        lines = [
            line for line in lines
            if not line.startswith("JWT_SECRET_KEY=")
        ]

        lines.append(
            f"JWT_SECRET_KEY={secret}"
        )

        with open(
            ENV_PATH, "w", encoding="utf-8"
        ) as file:

            file.write(
                "\n".join(lines) + "\n"
            )

        print(
            "[Auth] JWT_SECRET_KEY saved to .env."
        )

    except Exception as exc:

        # Still works in-memory for this run.

        print(
            "[Auth] Could not persist JWT_SECRET_KEY:",
            exc
        )

    return secret


JWT_SECRET_KEY = _resolve_secret()


# ============================================================
# 3. PASSWORD HASHING
# ============================================================

def hash_password(plain: str) -> str:

    return bcrypt.hashpw(
        plain.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")


def verify_password(
    plain: str,
    hashed: str
) -> bool:

    if not plain or not hashed:
        return False

    try:

        return bcrypt.checkpw(
            plain.encode("utf-8"),
            hashed.encode("utf-8")
        )

    except Exception:

        return False


# ============================================================
# 4. TOKENS
# ============================================================

def create_access_token(
    user_id: str,
    email: str
) -> str:

    payload = {

        "sub": str(user_id),

        "email": email,

        "iat": datetime.now(timezone.utc),

        "exp": datetime.now(timezone.utc)
        + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=ALGORITHM
    )


def decode_access_token(
    token: str
) -> Optional[dict]:

    try:

        return jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[ALGORITHM]
        )

    except jwt.ExpiredSignatureError:

        return None

    except jwt.InvalidTokenError:

        return None


# ============================================================
# 5. CURRENT USER DEPENDENCY
# ============================================================
#
# Protects an endpoint. Returns the token payload so the
# route can read user_id. Raises 401 when the token is
# missing, malformed or expired.
# ============================================================

_bearer = HTTPBearer(
    auto_error=False
)


def get_current_user(
    credentials: Optional[
        HTTPAuthorizationCredentials
    ] = Depends(_bearer)
) -> dict:

    if credentials is None:

        raise HTTPException(

            status_code=401,

            detail=(
                "Not authenticated. Log in to get a token."
            ),

            headers={"WWW-Authenticate": "Bearer"}
        )

    payload = decode_access_token(
        credentials.credentials
    )

    if payload is None:

        raise HTTPException(

            status_code=401,

            detail=(
                "Invalid or expired token. Log in again."
            ),

            headers={"WWW-Authenticate": "Bearer"}
        )

    return payload
