import logging
import os
import smtplib
from email.message import EmailMessage
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


def _frontend_base() -> str:
    return os.getenv("FRONTEND_URL", "http://localhost:8080").split(",")[0].strip().rstrip("/")


def send_verification_email(email: str, token: str) -> None:
    link = f"{_frontend_base()}/verify-email?token={token}"
    subject = "Verify your StudyBuddy email"
    body = (
        "Welcome to StudyBuddy!\n\n"
        f"Verify your email by opening this link:\n{link}\n\n"
        "This link expires in 24 hours."
    )
    _send(email, subject, body, link)


def send_password_reset_email(email: str, token: str) -> None:
    link = f"{_frontend_base()}/reset-password?token={token}"
    subject = "Reset your StudyBuddy password"
    body = (
        "We received a request to reset your StudyBuddy password.\n\n"
        f"Reset it here:\n{link}\n\n"
        "If you did not request this, you can ignore this email."
    )
    _send(email, subject, body, link)


def _send(to_email: str, subject: str, body: str, link: str) -> None:
    smtp_host = os.getenv("SMTP_HOST", "").strip()
    smtp_user = os.getenv("SMTP_USER", "").strip()
    smtp_pass = os.getenv("SMTP_PASSWORD", "").strip()
    smtp_from = os.getenv("SMTP_FROM", smtp_user or "noreply@studybuddy.local").strip()

    if not smtp_host:
        logger.info("[DEV EMAIL] To: %s | Subject: %s | Link: %s", to_email, subject, link)
        log_path = Path(__file__).resolve().parent.parent / "dev_emails.log"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"=== {subject} ===\n")
            f.write(f"To: {to_email}\n")
            f.write(f"Time: {datetime.now().isoformat()}\n")
            f.write(f"Link: {link}\n")
            f.write(f"{body}\n")
            f.write("=" * 40 + "\n\n")
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = smtp_from
    msg["To"] = to_email
    msg.set_content(body)

    port = int(os.getenv("SMTP_PORT", "587"))
    with smtplib.SMTP(smtp_host, port, timeout=20) as server:
        server.starttls()
        if smtp_user and smtp_pass:
            server.login(smtp_user, smtp_pass)
        server.send_message(msg)
