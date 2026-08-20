"""SMTP email delivery for account recovery."""

from __future__ import annotations

import asyncio
import smtplib
from email.message import EmailMessage

from app.core.config import settings


async def send_password_reset_email(recipient: str, reset_url: str) -> None:
    if not settings.smtp_configured:
        raise RuntimeError("SMTP is not configured")

    message = EmailMessage()
    message["Subject"] = "DocAssist 비밀번호 재설정"
    message["From"] = settings.SMTP_FROM_EMAIL
    message["To"] = recipient
    message.set_content(
        "DocAssist 비밀번호를 재설정하려면 아래 주소를 열어 주세요.\n\n"
        f"{reset_url}\n\n"
        f"이 링크는 {settings.PASSWORD_RESET_EXPIRE_MINUTES}분 동안 유효합니다. "
        "요청하지 않았다면 이 메일을 무시해 주세요."
    )

    def deliver() -> None:
        smtp_class = smtplib.SMTP_SSL if settings.SMTP_USE_SSL else smtplib.SMTP
        with smtp_class(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as server:
            if settings.SMTP_STARTTLS and not settings.SMTP_USE_SSL:
                server.starttls()
            if settings.SMTP_USERNAME:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.send_message(message)

    await asyncio.to_thread(deliver)
