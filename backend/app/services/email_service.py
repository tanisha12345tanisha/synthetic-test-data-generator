import asyncio
from email.message import EmailMessage
import smtplib

from app.core.config import get_settings


async def send_password_reset_email(email: str, token: str) -> None:
    settings = get_settings()
    if not settings.smtp_host or not settings.smtp_from_email:
        return
    reset_url = f"{settings.frontend_url.rstrip('/')}/reset-password?token={token}"
    message = EmailMessage()
    message["Subject"] = "Reset your Synthetic Test Data Generator password"
    message["From"] = settings.smtp_from_email
    message["To"] = email
    message.set_content(
        "Use the following single-use link to reset your password. "
        f"The link expires soon.\n\n{reset_url}"
    )

    def send() -> None:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as client:
            if settings.smtp_starttls:
                client.starttls()
            if settings.smtp_username and settings.smtp_password:
                client.login(settings.smtp_username, settings.smtp_password)
            client.send_message(message)

    await asyncio.to_thread(send)
