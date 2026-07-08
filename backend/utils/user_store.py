import secrets
import uuid
from datetime import datetime, timezone

from utils.db import get_connection
from utils.jwt_utils import auth_token_expiry, hash_token, refresh_token_expiry
from utils.password_utils import hash_password, verify_password


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_user_by_id(user_id: str) -> dict | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            row = cur.fetchone()
            return row if row else None


def get_user_by_email(email: str) -> dict | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM users WHERE email = %s",
                (email.strip().lower(),),
            )
            row = cur.fetchone()
            return row if row else None


def get_user_by_oauth(provider: str, oauth_id: str) -> dict | None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM users WHERE oauth_provider = %s AND oauth_id = %s",
                (provider, oauth_id),
            )
            row = cur.fetchone()
            return row if row else None


def create_password_user(email: str, password: str, email_verified: bool = False) -> dict:
    user_id = str(uuid.uuid4())
    normalized = email.strip().lower()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (id, email, password_hash, email_verified, created_at)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    user_id,
                    normalized,
                    hash_password(password),
                    1 if email_verified else 0,
                    _now_iso(),
                ),
            )
    return get_user_by_id(user_id)  # type: ignore[return-value]


def create_or_update_oauth_user(email: str, provider: str, oauth_id: str) -> dict:
    existing = get_user_by_oauth(provider, oauth_id)
    if existing:
        return existing

    normalized = email.strip().lower()
    by_email = get_user_by_email(normalized)
    if by_email:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE users
                    SET oauth_provider = %s, oauth_id = %s, email_verified = 1
                    WHERE id = %s
                    """,
                    (provider, oauth_id, by_email["id"]),
                )
        return get_user_by_id(by_email["id"])  # type: ignore[return-value]

    user_id = str(uuid.uuid4())
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (id, email, password_hash, email_verified, oauth_provider, oauth_id, created_at)
                VALUES (%s, %s, NULL, 1, %s, %s, %s)
                """,
                (user_id, normalized, provider, oauth_id, _now_iso()),
            )
    return get_user_by_id(user_id)  # type: ignore[return-value]


def verify_user_password(email: str, password: str) -> dict | None:
    user = get_user_by_email(email)
    if not user or not verify_password(password, user.get("password_hash")):
        return None
    return user


def mark_email_verified(user_id: str) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET email_verified = 1 WHERE id = %s",
                (user_id,),
            )


def update_password(user_id: str, password: str) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET password_hash = %s WHERE id = %s",
                (hash_password(password), user_id),
            )


def create_email_token(user_id: str, token_type: str, hours: int = 24) -> str:
    raw = secrets.token_urlsafe(32)
    token_hash = hash_token(raw)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO auth_tokens (token_hash, user_id, token_type, expires_at, used)
                VALUES (%s, %s, %s, %s, 0)
                """,
                (token_hash, user_id, token_type, auth_token_expiry(hours).isoformat()),
            )
    return raw


def consume_email_token(raw_token: str, token_type: str) -> dict | None:
    token_hash = hash_token(raw_token)
    now = _now_iso()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT * FROM auth_tokens
                WHERE token_hash = %s AND token_type = %s AND used = 0 AND expires_at > %s
                """,
                (token_hash, token_type, now),
            )
            row = cur.fetchone()
            if not row:
                return None
            cur.execute(
                "UPDATE auth_tokens SET used = 1 WHERE token_hash = %s",
                (token_hash,),
            )
            cur.execute(
                "SELECT * FROM users WHERE id = %s",
                (row["user_id"],),
            )
            user = cur.fetchone()
            return user if user else None


def store_refresh_token(user_id: str, raw_token: str) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO refresh_tokens (token_hash, user_id, expires_at, revoked)
                VALUES (%s, %s, %s, 0)
                """,
                (hash_token(raw_token), user_id, refresh_token_expiry().isoformat()),
            )


def consume_refresh_token(raw_token: str) -> dict | None:
    token_hash = hash_token(raw_token)
    now = _now_iso()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT * FROM refresh_tokens
                WHERE token_hash = %s AND revoked = 0 AND expires_at > %s
                """,
                (token_hash, now),
            )
            row = cur.fetchone()
            if not row:
                return None
            cur.execute(
                "UPDATE refresh_tokens SET revoked = 1 WHERE token_hash = %s",
                (token_hash,),
            )
            cur.execute(
                "SELECT * FROM users WHERE id = %s",
                (row["user_id"],),
            )
            user = cur.fetchone()
            return user if user else None


def public_user(user: dict) -> dict:
    return {
        "id": user["id"],
        "email": user["email"],
        "email_verified": bool(user["email_verified"]),
        "oauth_provider": user.get("oauth_provider"),
        "created_at": user["created_at"],
    }


# ── Chat History ──────────────────────────────────────────────────────────────

def save_message(
    user_id: str,
    session_id: str,
    session_title: str,
    role: str,
    content: str,
    sources: list | None = None,
) -> None:
    import json
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO chat_history (user_id, session_id, session_title, role, content, sources, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    user_id,
                    session_id,
                    session_title,
                    role,
                    content,
                    json.dumps(sources) if sources else None,
                    _now_iso(),
                ),
            )


def get_user_sessions(user_id: str) -> list:
    """Return distinct chat sessions for a user, newest first."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT session_id, session_title, MAX(created_at) AS last_active
                FROM chat_history
                WHERE user_id = %s
                GROUP BY session_id, session_title
                ORDER BY last_active DESC
                """,
                (user_id,),
            )
            return cur.fetchall()


def get_session_messages(user_id: str, session_id: str) -> list:
    """Return all messages in a session for a user, oldest first."""
    import json
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT role, content, sources, created_at
                FROM chat_history
                WHERE user_id = %s AND session_id = %s
                ORDER BY id ASC
                """,
                (user_id, session_id),
            )
            rows = cur.fetchall()
            for row in rows:
                if row.get("sources") and isinstance(row["sources"], str):
                    try:
                        row["sources"] = json.loads(row["sources"])
                    except Exception:
                        row["sources"] = []
            return rows


def delete_session(user_id: str, session_id: str) -> None:
    """Delete all messages in a session for a user."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM chat_history WHERE user_id = %s AND session_id = %s",
                (user_id, session_id),
            )
