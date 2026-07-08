import logging
import re
from functools import wraps
import jwt
from flask import jsonify, request
from utils.jwt_utils import decode_access_token

logger = logging.getLogger(__name__)

UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)

def is_auth_configured() -> bool:
    # Always True since we run our own SQLite auth database locally
    return True

def verify_access_token(token: str) -> dict:
    """Verify our own HS256 JWT access token."""
    return decode_access_token(token)

def get_bearer_token() -> str | None:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header[7:].strip()
    return token or None

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_bearer_token()
        if not token:
            return jsonify({"error": "Missing or invalid Authorization header."}), 401

        try:
            payload = verify_access_token(token)
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Session expired. Please sign in again."}), 401
        except jwt.InvalidTokenError as e:
            logger.error("Auth failed: %s", e)
            return jsonify({"error": "Invalid authentication token."}), 401
        except Exception as e:
            logger.error("Unexpected auth error: %s", e)
            return jsonify({"error": "Authentication error."}), 500

        user_id = payload.get("sub")
        # Ensure it's a valid user ID format
        if not user_id or not UUID_RE.match(user_id):
            return jsonify({"error": "Invalid user identity in token."}), 401

        request.user_id = user_id
        request.user_email = payload.get("email")
        return f(*args, **kwargs)

    return decorated
