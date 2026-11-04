# TaskMon API

FastAPI backend for TaskMon: mobile-number OTP login and user profiles, on MySQL.

## Layout

```
app/
├── main.py              # App factory: middleware, error handlers, routers
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
| GET | `/health` | | Liveness |
| GET | `/health/ready` | | Readiness (503 if the DB is unreachable) |

Mobile numbers are normalised to E.164: `9876543210`, `919876543210` and `+91 98765-43210` all become `+919876543210`.

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
```

Inside Docker, `DB_HOST=localhost` points at the container itself. Use your MySQL host
(e.g. `host.docker.internal` on Docker Desktop).

## Before going live

- Replace `StaticOtpProvider` (`services/otp_service.py`) with an SMS provider and add OTP expiry and attempt limits.
- Add rate limiting on `/auth/*` (at the gateway or with Redis).
- Set `ENVIRONMENT=production`, `DOCS_ENABLED=false`, `LOG_JSON=true` and a strong `JWT_SECRET_KEY`.
