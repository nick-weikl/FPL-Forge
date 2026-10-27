# FPL Forge — MVP 1

A browser-based FPL squad planner with public team import, a starting XI and ordered bench, captain choices, fixture exploration and transparent transfer forecasts. No user accounts: personal squad selections and settings stay in localStorage. Analysis sends selected player IDs and transfer settings to the API; the application does not save these selections in its database.

## Run locally

Use Node.js 24, Python 3.12 and PostgreSQL. From `backend`, create a virtual environment, install `requirements-dev.txt` for local development/testing (`requirements.txt` for runtime only), and copy `.env.example` to `.env` with your database connection. Use a read-only web role for the application; operator migrations/imports run in a separate shell. From `frontend`, run `npm ci`. The frontend development server proxies `/api` to `127.0.0.1:8000`; no frontend environment file is required for this setup.

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

A database with the correct season's roster, fixtures and official FPL history is required for analysis. If starting from a backup, use the isolated restore procedure in [DATABASE_RECOVERY.md](DATABASE_RECOVERY.md). Migrations and ingestion run explicitly; opening the application never migrates or populates the database. Data-provider permission is still pending: do not treat these setup commands as authorization to retrieve new provider data or publish it. Existing local archives and database backups are intentionally excluded from Git and Docker builds.

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
npm run format:check
npm audit
```

```sh
cd backend
.venv/bin/python -B -m unittest discover -s tests -v
.venv/bin/ruff check ..
.venv/bin/ruff format --check ..
```

Tests use isolated SQLite databases. The archive integration test additionally runs when a local archive is available. GitHub Actions runs the frontend checks and backend tests on Linux; no deployment or production database access is configured in CI.

See [QA.md](QA.md) for the current verification record and known limitations. Detailed procedures:

- [DEPLOYMENT.md](DEPLOYMENT.md): same-origin hosting, secrets, health monitoring, container operation and rollback.
- [DATABASE_RECOVERY.md](DATABASE_RECOVERY.md): tested isolated backup recovery and database-role setup.
- [ACCEPTANCE_TESTING.md](ACCEPTANCE_TESTING.md): browser/device evidence and the manual review checklist.
- [MANUAL_REFRESH.md](MANUAL_REFRESH.md): explicit preview/apply/verification workflow and freshness checks.
- [RECOMMENDATION_QA.md](RECOMMENDATION_QA.md): October 27 forecast arithmetic and stale-data checks.

A healthy service is not proof of current season data. `/health/live` checks the process; production `/health/ready` validates the required tables/columns and applied migration checksums. Use `/api/data-quality` and the UI warnings to check freshness separately. Public hosting, provider permission, real HTTPS/domain validation and operational monitoring on a chosen host remain release decisions.

## Code style

From `frontend`, run `npm run format` to format maintained frontend code, documentation, and configuration. Run `npm run format:check` to check without editing.

Install `backend/requirements-dev.txt`, then run `ruff check .` and `ruff format .` from the repository root. CI checks both formatters. Applied migration `backend/app/migrations/v001.py` is deliberately excluded: its exact file checksum is recorded in the database and must remain unchanged. Generated files, dependencies, and lockfiles are not reformatted.
