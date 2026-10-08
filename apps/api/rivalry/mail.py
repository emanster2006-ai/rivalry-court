import smtplib
from email.message import EmailMessage

from rivalry.config import settings


def send_score_notice(addresses: list[str], duel_id: str) -> None:
    for address in addresses:
        msg = EmailMessage()
        msg["Subject"] = "Rivalry Court score needs your review"
        msg["From"] = settings.mail_from
        msg["To"] = address
        msg.set_content(
            f"Your duel has a score entry. Confirm or dispute within 72 hours: "
            f"{settings.web_url}/?duel={duel_id}\n"
        )
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as client:
            if settings.smtp_user:
                client.login(settings.smtp_user, settings.smtp_password)
            client.send_message(msg)
