import logging
from datetime import timedelta

from sqlalchemy import or_, select

from app.config import settings
from app.db import SessionLocal
from app.models import Ticket, utcnow
from app.sms import build_reminder_message, send_sms

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def run_reminders() -> None:
    now = utcnow()
    reminder_cutoff = now - timedelta(days=settings.REMINDER_AFTER_DAYS)
    interval_cutoff = now - timedelta(days=settings.REMINDER_INTERVAL_DAYS)
    today = now.date()

    with SessionLocal() as db:
        eligible = db.scalars(
            select(Ticket).where(
                Ticket.status == "ready",
                Ticket.picked_up_at.is_(None),
                Ticket.ready_at <= reminder_cutoff,
                or_(
                    Ticket.last_reminder_at.is_(None),
                    Ticket.last_reminder_at <= interval_cutoff,
                ),
            )
        ).all()

        sent = 0
        for ticket in eligible:
            ready_date = ticket.ready_at.strftime("%b %d, %Y") if ticket.ready_at else ""
            body = build_reminder_message(
                ticket.customer_name,
                ticket.item_description,
                ready_date,
            )
            send_sms(ticket.customer_phone, body)
            ticket.last_reminder_at = now
            sent += 1

        db.commit()
        logger.info("Sent %d reminder(s)", sent)

        overdue = db.scalars(
            select(Ticket).where(
                Ticket.status.in_(("received", "in_progress")),
                Ticket.due_date < today,
            )
        ).all()

        for ticket in overdue:
            logger.info(
                "OVERDUE: #%s %s %s due %s",
                ticket.id,
                ticket.customer_name,
                ticket.item_description,
                ticket.due_date,
            )


if __name__ == "__main__":
    run_reminders()
