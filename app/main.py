import logging
from datetime import date, datetime
from pathlib import Path

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import Base, engine, get_db
from app.models import Ticket, utcnow
from app.sms import (
    build_ready_message,
    build_reminder_message,
    normalize_phone,
    send_sms,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Shoe Repair Tracker")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

STATUS_LABELS = {
    "received": "Received",
    "in_progress": "In progress",
    "ready": "Ready",
    "picked_up": "Picked up",
}


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


def _parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    today = utcnow().date()
    active = db.scalars(
        select(Ticket)
        .where(Ticket.status != "picked_up")
        .order_by(Ticket.due_date.asc())
    ).all()
    picked_up = db.scalars(
        select(Ticket)
        .where(Ticket.status == "picked_up")
        .order_by(Ticket.picked_up_at.desc())
    ).all()
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "active_tickets": active,
            "picked_up_tickets": picked_up,
            "today": today,
            "status_labels": STATUS_LABELS,
            "store_name": settings.STORE_NAME,
        },
    )


@app.get("/history", response_class=HTMLResponse)
def history(request: Request, db: Session = Depends(get_db)):
    tickets = db.scalars(
        select(Ticket)
        .where(Ticket.status == "picked_up")
        .order_by(Ticket.picked_up_at.desc())
    ).all()
    return templates.TemplateResponse(
        request,
        "history.html",
        {
            "tickets": tickets,
            "status_labels": STATUS_LABELS,
            "store_name": settings.STORE_NAME,
        },
    )


@app.get("/tickets/new", response_class=HTMLResponse)
def new_ticket_form(request: Request):
    return templates.TemplateResponse(
        request,
        "ticket_form.html",
        {
            "ticket": None,
            "status_labels": STATUS_LABELS,
            "store_name": settings.STORE_NAME,
        },
    )


@app.post("/tickets")
def create_ticket(
    customer_name: str = Form(...),
    customer_phone: str = Form(...),
    item_description: str = Form(...),
    work_description: str = Form(...),
    due_date: str = Form(...),
    db: Session = Depends(get_db),
):
    ticket = Ticket(
        customer_name=customer_name.strip(),
        customer_phone=normalize_phone(customer_phone),
        item_description=item_description.strip(),
        work_description=work_description.strip(),
        due_date=_parse_date(due_date),
        status="received",
    )
    db.add(ticket)
    db.commit()
    return RedirectResponse(url=f"/tickets/{ticket.id}", status_code=303)


@app.get("/tickets/{ticket_id}", response_class=HTMLResponse)
def ticket_detail(ticket_id: int, request: Request, db: Session = Depends(get_db)):
    ticket = db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return templates.TemplateResponse(
        request,
        "ticket_detail.html",
        {
            "ticket": ticket,
            "status_labels": STATUS_LABELS,
            "store_name": settings.STORE_NAME,
            "today": utcnow().date(),
        },
    )


@app.post("/tickets/{ticket_id}")
def update_ticket(
    ticket_id: int,
    customer_name: str = Form(...),
    customer_phone: str = Form(...),
    item_description: str = Form(...),
    work_description: str = Form(...),
    due_date: str = Form(...),
    status: str = Form(...),
    db: Session = Depends(get_db),
):
    ticket = db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket.customer_name = customer_name.strip()
    ticket.customer_phone = normalize_phone(customer_phone)
    ticket.item_description = item_description.strip()
    ticket.work_description = work_description.strip()
    ticket.due_date = _parse_date(due_date)

    if status != ticket.status:
        ticket.status = status
        if status == "ready" and ticket.ready_at is None:
            ticket.ready_at = utcnow()
        if status == "picked_up" and ticket.picked_up_at is None:
            ticket.picked_up_at = utcnow()

    ticket.updated_at = utcnow()
    db.commit()
    return RedirectResponse(url=f"/tickets/{ticket_id}", status_code=303)


@app.post("/tickets/{ticket_id}/ready")
def mark_ready(ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket.status = "ready"
    ticket.ready_at = utcnow()
    ticket.updated_at = utcnow()
    db.commit()

    body = build_ready_message(ticket.customer_name, ticket.item_description)
    send_sms(ticket.customer_phone, body)

    return RedirectResponse(url=f"/tickets/{ticket_id}", status_code=303)


@app.post("/tickets/{ticket_id}/pickup")
def mark_pickup(ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket.status = "picked_up"
    ticket.picked_up_at = utcnow()
    ticket.updated_at = utcnow()
    db.commit()
    return RedirectResponse(url="/", status_code=303)


@app.post("/tickets/{ticket_id}/remind")
def send_reminder(ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ready_date = ticket.ready_at.strftime("%b %d, %Y") if ticket.ready_at else ""
    body = build_reminder_message(
        ticket.customer_name,
        ticket.item_description,
        ready_date,
    )
    send_sms(ticket.customer_phone, body)
    ticket.last_reminder_at = utcnow()
    ticket.updated_at = utcnow()
    db.commit()
    return RedirectResponse(url=f"/tickets/{ticket_id}", status_code=303)
