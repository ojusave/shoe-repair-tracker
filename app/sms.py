import logging
import re

from twilio.rest import Client

from app.config import settings

logger = logging.getLogger(__name__)


def normalize_phone(raw: str) -> str:
    """Normalize a phone number to E.164 format."""
    stripped = raw.strip()
    if stripped.startswith("+"):
        return stripped

    digits = re.sub(r"\D", "", raw)
    if len(digits) == 10:
        return f"+1{digits}"
    if len(digits) == 11 and digits.startswith("1"):
        return f"+{digits}"
    return f"+{digits}"


def _twilio_configured() -> bool:
    return bool(
        settings.TWILIO_ACCOUNT_SID
        and settings.TWILIO_AUTH_TOKEN
        and settings.TWILIO_FROM_NUMBER
    )


def send_sms(to: str, body: str) -> bool:
    """Send an SMS via Twilio. Logs and returns False if creds are missing."""
    if not _twilio_configured():
        logger.info("[SMS skipped] to=%s body=%s", to, body)
        return False

    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    client.messages.create(
        body=body,
        from_=settings.TWILIO_FROM_NUMBER,
        to=to,
    )
    logger.info("[SMS sent] to=%s", to)
    return True


def build_ready_message(name: str, item: str) -> str:
    return (
        f"Hi {name}, your {item} is ready for pickup at {settings.STORE_NAME}."
    )


def build_reminder_message(name: str, item: str, ready_date: str) -> str:
    return (
        f"Hi {name}, friendly reminder your {item} has been ready for pickup "
        f"since {ready_date} at {settings.STORE_NAME}."
    )
