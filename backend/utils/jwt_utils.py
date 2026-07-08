import os
import secrets
import hashlib
from datetime import datetime, timedelta, timezone

import jwt

JWT_SECRET = os.getenv("JWT_SECRET") or os.getenv("SUPABASE_JWT_SECRET") or "dev-change-me-in-production"
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_MINUTES = int(os.getenv("ACCESS_TOKEN_MINUTES", "15"))
REFRESH_TOKEN_DAYS = int(os.getenv("REFRESH_TOKEN_DAYS", "7"))


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(user_id: str, email: str, email_verified: bool) -> str:
    now = _utcnow()
    payload = {
        "sub": user_id,
        "email": email,
        "email_verified": email_verified,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_refresh_token_value() -> str:
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def decode_access_token(token: str) -> dict:
    payload = jwt.decode(
        token,
        JWT_SECRET,
        algorithms=[JWT_ALGORITHM],
        options={"require": ["exp", "sub", "type"]},
    )
    if payload.get("type") != "access":
        raise jwt.InvalidTokenError("Invalid token type.")
    return payload


def refresh_token_expiry() -> datetime:
    return _utcnow() + timedelta(days=REFRESH_TOKEN_DAYS)


def auth_token_expiry(hours: int) -> datetime:
    return _utcnow() + timedelta(hours=hours)
