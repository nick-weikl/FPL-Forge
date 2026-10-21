# FPL Forge — MVP 1

A browser-based FPL squad planner with public team import, a starting XI and ordered bench, captain choices, fixture exploration and transparent transfer forecasts. No user accounts: personal squad selections and settings stay in localStorage. Analysis sends selected player IDs and transfer settings to the API; the application does not save these selections in its database.

## Run locally

Use Node.js 24, Python 3.12 and PostgreSQL. From `backend`, create a virtual environment, install `requirements.txt`, and copy `.env.example` to `.env` with your database connection. From `frontend`, run `npm ci`. The frontend development server proxies `/api` to `127.0.0.1:8000`; no frontend environment file is required for this setup.

Run these in separate terminals:

```sh
cd backend
.venv/bin/uvicorn app.main:app --reload
```

```sh
cd frontend
npm run dev
```

Open the frontend's printed local URL. The first-use guide explains how to find your FPL team ID and complete your matchday settings. Help contains forecast assumptions, privacy information, and browser-data backup/restore. Theme defaults to your device preference and can be changed in the header.

A database with the correct season's roster, fixtures and official FPL history is required for analysis. Migrations and ingestion run explicitly; opening the application never migrates or populates the database. Existing local archives and database backups are intentionally excluded from Git and Docker builds.

```sh
cd backend
# Use an operator database role. Back up any existing database first.
.venv/bin/python -m app.scripts.migrate --check
.venv/bin/python -m app.scripts.migrate
# Preview a validated archived official JSON import before applying it:
.venv/bin/python -m app.scripts.import_fpl_dump /path/to/archive --through-gameweek 7
# Add --apply only when you intend to write the validated import.
```

`FPL_SEASON_START` defaults to 2026. Use matching current-season data; do not relabel old data as a new season.

## Verification

```sh
cd frontend
npm test
npm run lint
npm run build
npm audit
```

```sh
cd backend
.venv/bin/python -m unittest discover -s tests -v
```

Tests use isolated SQLite databases. The archive integration test additionally runs when a local archive is available. GitHub Actions runs the frontend checks and backend tests on Linux; no deployment or production database access is configured in CI.

See [QA.md](QA.md) for the latest verified journeys and limitations and [DEPLOYMENT.md](DEPLOYMENT.md) before considering public deployment.

## Code style

From `frontend`, run `npm run format` to format maintained frontend code, documentation, and configuration. Run `npm run format:check` to check without editing.

Install `backend/requirements-dev.txt`, then run `ruff check .` and `ruff format .` from the repository root. CI checks both formatters. Applied migration `backend/app/migrations/v001.py` is deliberately excluded: its exact file checksum is recorded in the database and must remain unchanged. Generated files, dependencies, and lockfiles are not reformatted.
