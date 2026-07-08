import os
from urllib.parse import urlencode

from authlib.integrations.flask_client import OAuth
from flask import Blueprint, jsonify, redirect, request

from utils.email_utils import send_password_reset_email, send_verification_email
from utils.jwt_utils import create_access_token, create_refresh_token_value
from utils.rate_limit import limiter
from utils.user_store import (
    consume_email_token,
    consume_refresh_token,
    create_email_token,
    create_or_update_oauth_user,
    create_password_user,
    get_user_by_email,
    get_user_by_id,
    mark_email_verified,
    public_user,
    store_refresh_token,
    update_password,
    verify_user_password,
)

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")
oauth = OAuth()

REQUIRE_EMAIL_VERIFICATION = os.getenv("REQUIRE_EMAIL_VERIFICATION", "true").lower() == "true"


def _frontend_base() -> str:
    return os.getenv("FRONTEND_URL", "http://localhost:8080").split(",")[0].strip().rstrip("/")


def _issue_tokens(user: dict) -> dict:
    access = create_access_token(
        user["id"],
        user["email"],
        bool(user["email_verified"]),
    )
    refresh = create_refresh_token_value()
    store_refresh_token(user["id"], refresh)
    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
        "expires_in": int(os.getenv("ACCESS_TOKEN_MINUTES", "15")) * 60,
        "user": public_user(user),
    }


def _json_error(message: str, status: int = 400):
    return jsonify({"error": message}), status


def init_oauth(app) -> None:
    oauth.init_app(app)
    google_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()
    google_secret = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()
    github_id = os.getenv("GITHUB_CLIENT_ID", "").strip()
    github_secret = os.getenv("GITHUB_CLIENT_SECRET", "").strip()

    if google_id and google_secret:
        oauth.register(
            name="google",
            client_id=google_id,
            client_secret=google_secret,
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"},
        )

    if github_id and github_secret:
        oauth.register(
            name="github",
            client_id=github_id,
            client_secret=github_secret,
            access_token_url="https://github.com/login/oauth/access_token",
            authorize_url="https://github.com/login/oauth/authorize",
            api_base_url="https://api.github.com/",
            client_kwargs={"scope": "user:email"},
        )


@auth_bp.route("/register", methods=["POST"])
@limiter.limit("5 per hour")
def register():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or "@" not in email:
        return _json_error("A valid email is required.")
    if len(password) < 8:
        return _json_error("Password must be at least 8 characters.")

    if get_user_by_email(email):
        return _json_error("An account with this email already exists.", 409)

    email_verified = not REQUIRE_EMAIL_VERIFICATION
    user = create_password_user(email, password, email_verified=email_verified)

    if REQUIRE_EMAIL_VERIFICATION:
        token = create_email_token(user["id"], "verify", hours=24)
        send_verification_email(email, token)
        return jsonify({
            "message": "Account created. Check your email to verify your address before signing in.",
            "email_verification_required": True,
        }), 201

    return jsonify(_issue_tokens(user)), 201


@auth_bp.route("/login", methods=["POST"])
@limiter.limit("10 per minute")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = verify_user_password(email, password)
    if not user:
        return _json_error("Invalid email or password.", 401)

    if REQUIRE_EMAIL_VERIFICATION and not user["email_verified"]:
        return _json_error("Please verify your email before signing in.", 403)

    return jsonify(_issue_tokens(user))


@auth_bp.route("/refresh", methods=["POST"])
@limiter.limit("30 per hour")
def refresh():
    data = request.get_json(silent=True) or {}
    refresh_token = (data.get("refresh_token") or "").strip()
    if not refresh_token:
        return _json_error("Refresh token is required.")

    user = consume_refresh_token(refresh_token)
    if not user:
        return _json_error("Invalid or expired refresh token.", 401)

    return jsonify(_issue_tokens(user))


@auth_bp.route("/me", methods=["GET"])
@limiter.limit("60 per minute")
def me():
    from utils.auth_utils import get_bearer_token, verify_access_token
    import jwt

    token = get_bearer_token()
    if not token:
        return _json_error("Missing token.", 401)
    try:
        payload = verify_access_token(token)
    except jwt.InvalidTokenError:
        return _json_error("Invalid token.", 401)

    user = get_user_by_id(payload["sub"])
    if not user:
        return _json_error("User not found.", 404)
    return jsonify({"user": public_user(user)})


@auth_bp.route("/verify-email", methods=["POST"])
@limiter.limit("20 per hour")
def verify_email():
    data = request.get_json(silent=True) or {}
    token = (data.get("token") or "").strip()
    if not token:
        return _json_error("Verification token is required.")

    user = consume_email_token(token, "verify")
    if not user:
        return _json_error("Invalid or expired verification link.", 400)

    mark_email_verified(user["id"])
    user = get_user_by_id(user["id"])
    return jsonify({
        "message": "Email verified successfully.",
        **_issue_tokens(user),
    })


@auth_bp.route("/resend-verification", methods=["POST"])
@limiter.limit("5 per hour")
def resend_verification():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    user = get_user_by_email(email)

    if user and not user["email_verified"]:
        token = create_email_token(user["id"], "verify", hours=24)
        send_verification_email(email, token)

    return jsonify({
        "message": "If an unverified account exists for that email, a verification link was sent.",
    })


@auth_bp.route("/forgot-password", methods=["POST"])
@limiter.limit("5 per hour")
def forgot_password():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    user = get_user_by_email(email)

    if user and user.get("password_hash"):
        token = create_email_token(user["id"], "reset", hours=1)
        send_password_reset_email(email, token)

    return jsonify({
        "message": "If an account exists for that email, a reset link was sent.",
    })


@auth_bp.route("/reset-password", methods=["POST"])
@limiter.limit("10 per hour")
def reset_password():
    data = request.get_json(silent=True) or {}
    token = (data.get("token") or "").strip()
    password = data.get("password") or ""

    if len(password) < 8:
        return _json_error("Password must be at least 8 characters.")

    user = consume_email_token(token, "reset")
    if not user:
        return _json_error("Invalid or expired reset link.", 400)

    update_password(user["id"], password)
    user = get_user_by_id(user["id"])
    return jsonify({
        "message": "Password updated successfully.",
        **_issue_tokens(user),
    })


@auth_bp.route("/oauth/<provider>", methods=["GET"])
@limiter.limit("30 per hour")
def oauth_login(provider: str):
    if provider not in ("google", "github"):
        return _json_error("Unsupported OAuth provider.", 404)

    # Normalize request domain to match the configured redirect URI domain.
    # This prevents session cookie loss caused by mismatching localhost vs 127.0.0.1.
    redirect_uri = os.getenv(f"{provider.upper()}_REDIRECT_URI")
    if redirect_uri:
        from urllib.parse import urlparse
        parsed_redirect = urlparse(redirect_uri)
        parsed_request = urlparse(request.url)
        if parsed_redirect.netloc and parsed_request.netloc != parsed_redirect.netloc:
            target_url = parsed_request._replace(netloc=parsed_redirect.netloc).geturl()
            logger.info("Redirecting to normalized domain to align session cookies: %s", target_url)
            return redirect(target_url)

    # If mock mode is requested or provider not configured → mock OAuth
    mock_mode = os.getenv("OAUTH_MOCK", "false").lower() == "true"
    if mock_mode or provider not in oauth._clients:
        email = f"mock-{provider}-user@example.com"
        user = create_or_update_oauth_user(email, provider, f"mock-{provider}-id")
        tokens = _issue_tokens(user)
        query = urlencode({
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
        })
        return redirect(f"{_frontend_base()}/auth/callback?{query}")

    if not redirect_uri:
        redirect_uri = f"http://127.0.0.1:5000/auth/oauth/{provider}/callback"

    try:
        return oauth.create_client(provider).authorize_redirect(redirect_uri)
    except Exception as exc:
        logger.error("OAuth redirect error for %s: %s", provider, exc)
        query = urlencode({"error": f"OAuth configuration error for {provider}. Check server logs."})
        return redirect(f"{_frontend_base()}/?{query}")


@auth_bp.route("/oauth/<provider>/callback", methods=["GET"])
@limiter.limit("30 per hour")
def oauth_callback(provider: str):
    if provider not in ("google", "github"):
        return _json_error("Unsupported OAuth provider.", 404)

    try:
        client = oauth.create_client(provider)
        token = client.authorize_access_token()

        if provider == "google":
            userinfo = token.get("userinfo") or client.parse_id_token(token)
            email = userinfo.get("email")
            oauth_id = userinfo.get("sub")
        else:
            resp = client.get("user")
            profile = resp.json()
            email = profile.get("email")
            oauth_id = str(profile.get("id"))
            if not email:
                emails_resp = client.get("user/emails")
                emails = emails_resp.json()
                primary = next((e for e in emails if e.get("primary")), emails[0] if emails else None)
                email = primary.get("email") if primary else None

        if not email or not oauth_id:
            query = urlencode({"error": "Could not retrieve your profile from the OAuth provider."})
            return redirect(f"{_frontend_base()}/?{query}")

        user = create_or_update_oauth_user(email, provider, oauth_id)
        tokens = _issue_tokens(user)
        query = urlencode({
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
        })
        return redirect(f"{_frontend_base()}/auth/callback?{query}")

    except Exception as exc:
        logger.error("OAuth callback error for %s: %s", provider, exc)
        query = urlencode({"error": "OAuth sign-in failed. The redirect URI may not be registered in the provider's console."})
        return redirect(f"{_frontend_base()}/?{query}")
