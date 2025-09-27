# Roach Parlor Betting Tracker

An internal toolset for tracking sports wagers for a small Discord community. The project is structured as a FastAPI web app with a Jinja-based dashboard, a Discord bot that ingests slips through AI-powered OCR/extraction, and a Postgres persistence layer. Use this document to quickly orient new collaborators (human or AI agents) who need to modify or extend the system.

## High-Level Architecture

- **FastAPI application** (`web/app`)
  - Exposes REST endpoints for wagers, users, and reference catalog data.
  - Serves several server-rendered HTML pages (TailwindCSS via CDN) for dashboards, stats, and admin views.
  - Uses SQLAlchemy ORM models (`models.py`) backed by an Alembic-managed Postgres schema.
- **Discord bot** (`bot/`)
  - Listens to a target channel, sends image slips to OpenAI Responses API for structured extraction, and POSTs the resulting wager payloads into the web service.
- **Database**
  - Postgres 14 (Docker service `db`) hosts all persistent data.
  - Alembic migrations live in `migrations/` and apply automatically via `web/app/database.py:init_db()` on startup.
- **Container orchestration**
  - `docker-compose.yml` builds and runs the three services (`web`, `bot`, `db`).
  - Environment variables provide secrets and external API configuration.

## Code Layout

```
project-root/
├── README.md                      # (this file)
├── docker-compose.yml             # Docker services (web, bot, db)
├── migrations/                    # Alembic revisions
├── web/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py                # FastAPI entrypoint + page routes
│       ├── database.py            # SQLAlchemy engine/session helpers
│       ├── models.py              # ORM models (League, Team, User, Wager, ...)
│       ├── schemas.py             # Pydantic schemas for API responses
│       ├── crud.py                # Database access layer used by routes & pages
│       ├── routers/
│       │   ├── users.py           # /users REST endpoints
│       │   ├── wagers.py          # /wagers REST endpoints
│       │   └── catalog.py         # /catalog reference data endpoints
│       └── templates/             # Jinja templates for dashboards
│           ├── base.html          # Top-level layout and navigation
│           ├── index.html         # Main dashboard of active wagers
│           ├── archived.html      # Archived wager list
│           ├── stats.html         # Player statistics + charts
│           ├── catalog.html       # League/team/player catalog browser
│           ├── admin_login.html   # Admin key prompt (optional)
│           └── admin_wagers.html  # Full-system admin control panel
└── bot/
    ├── Dockerfile
    ├── requirements.txt
    └── main.py                    # Discord bot ingestion pipeline
```

## FastAPI Application: Design Notes

- **Layered structure**
  - Routers (`routers/*.py`) define HTTP endpoints and Pydantic request/response models.
  - Business/data operations live in `crud.py`; routers and page handlers call these helpers instead of embedding SQL.
  - ORM models (`models.py`) capture the relational structure. Relationships are configured with backrefs and cascade rules so deletions cascade through wagers → legs → matchups.
  - `main.py` wires everything together, registers API routers, and provides view-rendering endpoints that pull data using the same CRUD helpers.

- **Templating pattern**
  - `FastAPI` + `Jinja2Templates` render TailwindCSS-enhanced HTML pages.
  - Layout is centralized in `base.html`; each page extends it and receives a `request` plus context data.
  - UI actions (status toggles, archiving, deletes) use HTML forms with POST redirects to keep state on the server.

- **Admin access**
  - Authentication now flows through the `auth_users` table with salted PBKDF2 password hashes. On startup the app seeds an admin record using `ADMIN_USERNAME`/`ADMIN_PASSWORD` (falling back to `ADMIN_ACCESS_KEY` for legacy setups).
  - Successful sign-in issues a signed `session_token` cookie (via `SESSION_SECRET`); the `_require_admin` helper guards all protected routes and form handlers.
  - Admin dashboard consolidates every wager (active, archived, or removed) with inline controls to edit core fields, change status, toggle archive state, update leg statuses, or permanently delete entries.

- **Reference data / catalog**
  - Leagues, teams, and players have dedicated CRUD endpoints (`/catalog/...`).
  - `crud.build_team_alias_lookup` prepares fuzzy alias matching used to highlight teams in wager legs. Pages hydrate this data and annotate legs before rendering.

- **Stats and derived metrics**
  - `main.py:_wager_profit_delta` and related helpers compute per-user profit, win/loss counts, and daily aggregates for the `/stats` page.
  - Chart payloads are serialized as JSON and rendered client-side (see `stats.html`).

## Discord Bot Pipeline

- Subscribes to a configured Discord channel using `discord.py`.
- When a message with an image arrives, it:
  1. Ensures the Discord user exists in the web service (`/users/`).
  2. Sends the image to the OpenAI Responses API using the system prompt in `bot/main.py`. The model extracts the wager description, stake, line, optional legs, and matchup metadata.
  3. Normalizes and cleans the payload, then POSTs it to the FastAPI `/wagers/` endpoint to create a record.
  4. Maintains a short-lived cache of league/team aliases fetched from the web app's catalog endpoints to improve team matching in future requests.
- The bot expects `OPENAI_API_KEY`, `DISCORD_TOKEN`, `API_URL`, and optional routing variables (e.g., `TARGET_CHANNEL`).

## Database Model Overview

Key tables and relationships (managed through SQLAlchemy and Alembic):

- `users`: Discord-linked participants; one-to-many with `wagers`.
- `auth_users`: Application login accounts with hashed credentials and admin flag.
- `wagers`: Core bet entity with amount, line, status (`open|won|lost|removed`), archive flag, timestamps, and optional screenshot URL.
- `wager_legs`: Optional breakdown for parlay/prop legs; each stores a description and status.
- `wager_matchups`: Optional link to a league and home/away teams, plus scheduled datetime.
- `leagues` / `teams` / `players`: Reference catalog used both for matching and for manual admin edits.

`crud.update_wager_details` centralizes validation for admin edits, ensuring decimals are normalized and status values map to the enum.

## HTTP Endpoints (selected)

- `GET /` – dashboard of active wagers by user.
- `GET /archived` – archived wagers grouped by user.
- `GET /stats` – aggregate win/loss and profit charts.
- `GET /admin` – admin login portal (redirects to dashboard when already authenticated).
- `GET /admin/wagers` – admin control panel for all wagers (requires authenticated admin session).
- API routers
  - `POST /users/` – ensure/create a Discord user record.
  - `GET /wagers/{user_id}` – list wagers for a user.
  - `POST /wagers/` – create a wager (used by bot & manual tools).
  - `PATCH /wagers/{id}/status` – toggle status (open/won/lost/removed).
  - `PATCH /wagers/{id}/archive` – toggle archive flag.
  - `DELETE /wagers/{id}` – delete a wager (admin flows wrap this).
  - `PATCH /wagers/legs/{leg_id}/status` – update individual leg status.
  - `GET/POST /catalog/...` – manage leagues, teams, players.

## Environment Variables

| Variable | Used By | Purpose |
|----------|---------|---------|
| `DATABASE_URL` | web | SQLAlchemy connection string (e.g., `postgresql+psycopg2://user:pass@db:5432/betdb`). |
| `SESSION_SECRET` | web | Secret used to sign session cookies; set to a long random string in production. |
| `ADMIN_USERNAME` | web | Username for the seeded admin account (`admin` by default). |
| `ADMIN_PASSWORD` | web | Password for the seeded admin account. If omitted, the value of `ADMIN_ACCESS_KEY` is reused. |
| `ADMIN_ACCESS_KEY` | web | Legacy fallback for environments that still rely on a shared key; safe to drop once the new vars are set. |
| `POSTGRES_PASSWORD` etc. | db | Postgres credentials (see `docker-compose.yml`). |
| `DISCORD_TOKEN` | bot | Discord bot authentication token. |
| `OPENAI_API_KEY` | bot | Key for OpenAI Responses API. |
| `API_URL` | bot | Base URL of the FastAPI service (`http://web:8000` in Docker, `http://localhost:8000` locally). |
| `TARGET_CHANNEL`, `WEB_UI_URL`, `TARGET_CHANNEL`, `WEB_UI_URL` | bot | Optional routing/customization for Discord output. |

## Running the Stack

1. Ensure Docker and Docker Compose are installed.
2. Export required environment variables (`DATABASE_URL`, `POSTGRES_PASSWORD`, Discord/OpenAI keys) plus authentication settings (`SESSION_SECRET`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`).
3. Launch the stack:
   ```bash
   docker compose up --build
   ```
4. Web UI becomes available at `http://localhost:8000`; Discord bot logs to stdout once connected.
5. To run the FastAPI app locally without Docker, install dependencies from `web/requirements.txt`, set env vars, and launch `uvicorn app.main:app --reload` from within `web/`.

## Development Patterns & Tips

- Prefer editing through CRUD helpers instead of inline SQL in routes/templates. This keeps logic centralized and consistent between API and admin flows.
- When adding new page routes, reuse `_require_admin`, `_normalize_wager_status`, and other helpers in `main.py` to stay aligned with existing behavior.
- `crud.build_team_alias_lookup` and `crud.match_leg_description_to_teams` implement the fuzzy team matching used across dashboards—tap into them if new features require team detection.
- Admin templates pass `redirect_to` to form handlers so users stay on the same page post-action. Preserve that pattern when adding new actions.
- Alembic migrations should mirror any changes to `models.py`. Run `alembic revision --autogenerate` (configured elsewhere) and check results before applying.
- For testing basic syntax, `python3 -m compileall web/app` is a quick CI-lite smoke check.
- Whenever you adjust behavior, routes, or project layout, update this README (and other docs) so the next agent has accurate context.

## Onboarding Checklist for New AI Agents

1. **Read this README** to understand architecture and flows.
2. **Inspect `web/app/main.py`** for page routes and admin logic—most orchestrations happen there.
3. **Browse `crud.py` and `models.py`** to learn available data operations and schema.
4. **Check templates** for any UI changes required; their structure heavily influences how forms interact with endpoints.
5. **Review `bot/main.py`** if changes need to propagate through the ingestion pipeline.
6. Confirm required environment variables are set before running or testing.

With this context, new contributors (human or AI) should be able to dive into feature work or bugfixes with minimal ramp-up time.
