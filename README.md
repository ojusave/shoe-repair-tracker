# Shoe Repair Ticket Tracker

Track shoe repair tickets and text customers when repairs are ready.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/ojusave/shoe-repair-tracker)

## What gets deployed

The `render.yaml` Blueprint creates three resources:

- **repair-tracker** — Python web service (FastAPI + Jinja2)
- **repair-reminders** — daily cron job for pickup reminder texts
- **repair-db** — managed PostgreSQL shared by both services

## Environment variables

`DATABASE_URL` is wired automatically from the managed Postgres instance.

Twilio and store name are **optional at deploy time**. Leave them blank: the app still runs, SMS is logged as `[SMS skipped]`, and messages use the default store name `the shop`. Add these in the Dashboard later when you are ready:

| Variable | Purpose |
|---|---|
| `STORE_NAME` | Shop name in SMS (default: `the shop`) |
| `TWILIO_ACCOUNT_SID` | Twilio account SID |
| `TWILIO_AUTH_TOKEN` | Twilio auth token |
| `TWILIO_FROM_NUMBER` | Twilio sender number (E.164) |

Reminder tuning (cron, defaults in `render.yaml`):

| Variable | Default |
|---|---|
| `REMINDER_AFTER_DAYS` | `3` |
| `REMINDER_INTERVAL_DAYS` | `3` |

## Canadian SMS note

Twilio sending to **Canadian mobile numbers** requires a Canadian long code or a toll-free number that has completed registration/verification. Start that process early: verification can take several days and will block go-live if it is not done.

## Local development

```bash
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000. Local runs use SQLite (`local.db`) by default. Without Twilio credentials, SMS calls are logged as `[SMS skipped]` and never sent.

Run the reminder job manually:

```bash
python -m app.reminders
```

## Cost

At low volume (~100 tickets/month): a Starter web service, a cron job, and a managed Postgres database (`basic-256mb`). The database is not free on Render; the web and cron services are inexpensive at this scale.

## License

MIT
