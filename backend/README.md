# TaskMon API

FastAPI backend for TaskMon: mobile-number OTP login and user profiles, on MySQL.

## Layout

```
app/
├── main.py              # App factory: middleware, error handlers, routers
├── worker.py            # Reminder worker: sends a push for each due reminder (python -m app.worker)
├── api/
│   ├── deps.py          # Shared dependencies (DB session, current user, OTP provider)
│   ├── router.py        # Aggregates v1 routers
│   ├── health.py        # /health (liveness), /health/ready (DB check)
│   └── v1/
│       ├── auth.py      # /api/v1/auth/send-otp, /api/v1/auth/verify-otp
│       └── users.py     # /api/v1/users/me, /api/v1/users/me/username
├── core/
│   ├── config.py        # Settings from env / .env
│   ├── security.py      # JWT create/verify, PII masking
│   ├── exceptions.py    # AppError hierarchy and HTTP error mapping
│   ├── logging.py       # Text or JSON logs with request ids
│   └── middleware.py    # X-Request-ID and access logging
├── ai/
│   ├── groq_client.py       # One AsyncGroq client; timeouts, retries, rate limits → friendly errors
│   ├── prompts.py           # Classifier prompt (+ insights tip prompt)
│   ├── schemas.py           # Pydantic schema every Groq reply is validated against
│   ├── intent_catalogue.py  # Every supported intent, its fields and examples
│   ├── intent_classifier.py # One Groq call per message → validated ClassifierResult
│   └── response_generator.py# Records → card rows / text (₹, "Tomorrow · 8:00 PM")
├── conversation/
│   ├── manager.py           # Entry point: context → classify → route → save → commit
│   ├── context.py           # Turn state, debug trace, CONTEXT sent to Groq
│   ├── pending_actions.py   # Questions waiting for info / a pick / a yes (stored in MySQL)
│   ├── action_handler.py    # Validate → find target → confirm → run service → history; undo
│   ├── query_handler.py     # Lists, totals, comparison, insights (SQL + Decimal)
│   └── conversation_handler.py # Small talk, clarification, fallback
├── database/
│   ├── base.py          # Declarative Base with constraint naming convention
│   └── connection.py    # Engine, session factory, get_db
├── models/              # SQLAlchemy models (register new ones in models/__init__.py)
├── schemas/             # Pydantic request/response models
└── services/            # Business logic (no FastAPI imports)
alembic/                 # Database migrations
tests/                   # Pytest suite (runs on in-memory SQLite)
```

Requests flow `api → services → models`. Routes stay thin. Services hold the logic and raise
`AppError` subclasses, which `core/exceptions.py` turns into `{"detail": ..., "code": ...}` responses.

## Run locally

```bash
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env              # then set DB_PASSWORD and JWT_SECRET_KEY

# create the database once (MySQL):  CREATE DATABASE taskmon CHARACTER SET utf8mb4;
alembic upgrade head
uvicorn app.main:app --reload
```

API docs are at http://localhost:8000/docs (set `DOCS_ENABLED=false` to hide them).

## API

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/v1/auth/send-otp` | | Sends an OTP (static `STATIC_OTP` for now) |
| POST | `/api/v1/auth/verify-otp` | | Returns `access_token`, `expires_in`, `has_username`, `user` |
| GET | `/api/v1/users/me` | Bearer | Current user |
| PUT | `/api/v1/users/me/username` | Bearer | Set the username (409 `username_taken` if taken) |
| POST | `/api/v1/chat` | Bearer | Chat engine: understands the message and acts on reminders, expenses and notes |
| PUT | `/api/v1/users/me/daily-budget` | Bearer | Set the daily budget `{"daily_budget": 500}` (asked at every login) |
| POST | `/api/v1/sms/bank` | Bearer | A bank SMS `{"text"}` → expense; warning push if the day's budget is passed |
| POST | `/api/v1/reminders/{id}/complete` | Bearer | Mark a reminder done (the notification's Done button) (204) |
| POST | `/api/v1/devices` | Bearer | Save this phone's FCM token `{"token", "platform"}` (204) |
| POST | `/api/v1/devices/unregister` | Bearer | Remove it on logout `{"token"}` (204) |
| GET | `/health` | | Liveness |
| GET | `/health/ready` | | Readiness (503 if the DB is unreachable) |

Mobile numbers are normalised to E.164: `9876543210`, `919876543210` and `+91 98765-43210` all become `+919876543210`.

## AI chat (Groq)

Put your key in `.env` as `GROQ_API_KEY` (optionally `GROQ_MODEL`, `GROQ_REASONING_EFFORT`). The key stays on the server.

`POST /api/v1/chat` with `{"message": "...", "conversation_id": 12, "client_message_id": "<uuid>"}`:

1. Loads the conversation, the open pending action (if any), the records last shown, the last change and
   the user's saved details, plus the last 6 messages.
2. Groq classifies the message once (ACTION / QUERY / CLARIFICATION / CONVERSATION / FALLBACK) and extracts
   intents and fields. The reply is validated with Pydantic; unknown intents are dropped.
3. FastAPI validates every value (dates, times, amounts), asks for anything missing, finds the target record
   (only the user's own), asks "which one?" or "are you sure?" when needed, runs the service and writes
   `action_history`. All figures are calculated in SQL / `Decimal`.
4. Both messages are saved and the turn is committed in one transaction (rolled back on any error).

The reply has `text`, `parts` (text + optional card of records), `pending` (`info` / `select` / `confirm`)
and, with `CHAT_DEBUG=true`, `debug`: every step the engine took (also logged at INFO).

A retry with the same `client_message_id` returns the stored reply instead of acting twice. Pending
questions expire after `PENDING_ACTION_MINUTES`.

## Push notifications (reminders)

The database is the schedule. A reminder is a row in `notification_tasks`; creating, moving, cancelling
or deleting it only changes that row. `app/worker.py` runs separately and, every
`WORKER_INTERVAL_SECONDS` (30):

1. Picks open reminders whose `notify_at` has passed, checked in each user's timezone (`notify_at` is
   stored in local time). Rows are locked with `SKIP LOCKED`, so two workers never send the same one.
2. Sends an FCM push to each of the user's phones (`device_tokens`), through the FCM HTTP v1 API.
3. One-off: marks it `is_notified`. Repeating: moves `notify_at` to the next occurrence.
4. Deletes tokens FCM reports as dead. If FCM is down and nothing was delivered, the reminder stays due
   and the next run tries again. A reminder found more than an hour late (worker was down) is marked done
   without a push.

Every step is logged (`reminder=… user=… phones=… sent=… dead=… failed=…`).

The worker needs `FIREBASE_CREDENTIALS_FILE`: the Firebase Admin SDK service-account JSON (Firebase console
→ Project settings → Service accounts → Generate new private key). It is a secret: never commit it or copy
it into the image. The API itself doesn't need it.

```bash
python -m app.worker     # locally, with FIREBASE_CREDENTIALS_FILE set in .env
```

## Bank SMS → expenses, daily budget

The Android app's native receiver (`mobile-app/modules/bank-sms`) sees every incoming SMS, even when the
app is closed, and forwards only Federal Bank debit alerts to `POST /api/v1/sms/bank`. Other messages
never leave the phone. `services/sms_service.py` reads exactly this format:

```
Debited Rs 50.00 from a/c X9844 on 04Nov26 12:57 via UPI to SAFIYA HASSA. Ref 630830086298. Bal Rs 407.64. ... -Federal Bank
```

→ an expense of ₹50.00 on 2026-11-04 12:57, category `Misc`, description
`UPI to SAFIYA HASSA · Federal Bank X9844`, `reference` 630830086298. The same reference is never recorded
twice. If that day's total is now over the user's daily budget (`users.expense_limit`, set at every login),
the API sends a "Daily budget exceeded" push to the user's phones. So the **API container needs the
Firebase key too** (same mount as the worker). Without it the expense is still saved and the failure is
logged.

## Database tables

| Table | Purpose |
|---|---|
| `users` | Mobile number, username, `expense_limit` |
| `user_details` | Free-text paragraphs about a user |
| `conversations` / `messages` | Chat threads; `messages.role` is `user`, `assistant` or `system` |
| `tasks` | To-dos with `due_at`, `is_completed`, `completed_at` |
| `notes` | Title and content |
| `expenses` | `amount`, `category`, `spent_at` (indexed by user and date) |
| `notification_tasks` | Reminders: `notify_at`, `is_notified`, `notified_at`, `is_completed`, `is_cancelled`, `recurrence` |
| `device_tokens` | Each phone's FCM token (unique), for reminder pushes |
| `pending_actions` | Chat actions waiting for info, a choice or a confirmation |
| `action_history` | Audit log of chat changes with before/after snapshots (undo, duplicate detection) |

Every user-owned table has `user_id` with `ON DELETE CASCADE`, so deleting a user removes all their data.

## Migrations

```bash
alembic revision --autogenerate -m "add tasks table"   # after changing models
alembic upgrade head
alembic check                                          # fails if models and migrations differ
```

## Quality checks

```bash
pytest
ruff check . && ruff format --check .
```

## Docker

```bash
docker build -t taskmon-api .
docker run --rm --env-file .env taskmon-api alembic upgrade head
docker run -p 8000:8000 --env-file .env taskmon-api

# reminder worker: same image, different command; the Firebase key is mounted read-only
docker run -d --name taskmon-worker --no-healthcheck --env-file .env \
  -v /path/to/firebase-key.json:/run/secrets/firebase-key.json:ro \
  taskmon-api python -m app.worker
```

Mount the same key into the API container as well (`-v ...:/run/secrets/firebase-key.json:ro`): it sends
the daily budget warning. With `FIREBASE_CREDENTIALS_FILE=/run/secrets/firebase-key.json` in `.env`. `--no-healthcheck` because the
image's health check calls the API's `/health`, which the worker doesn't serve. The container runs as
uid 10001, so the key file on the host must be readable by that uid.

Secrets are never baked into the image: `.dockerignore` excludes `.env`, and values come from
`--env-file` at run time. On the server, keep the production `.env` next to the checkout (it is gitignored)
and write it as plain `KEY=value` lines (no spaces around `=`, no quotes). With `ENVIRONMENT=production`
the app refuses to start if `JWT_SECRET_KEY` is the template placeholder or `DB_PASSWORD` / `GROQ_API_KEY`
are missing.

Inside Docker, `DB_HOST=localhost` points at the container itself. Use your MySQL host
(e.g. `host.docker.internal` on Docker Desktop).

## Before going live

- Replace `StaticOtpProvider` (`services/otp_service.py`) with an SMS provider and add OTP expiry and attempt limits.
- Add rate limiting on `/auth/*` (at the gateway or with Redis).
- Set `ENVIRONMENT=production`, `DOCS_ENABLED=false`, `LOG_JSON=true` and a strong `JWT_SECRET_KEY`.
