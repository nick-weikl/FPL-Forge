# FPL Forge backend

Run commands from `backend/` with the project's Python environment. Set `DATABASE_URL` in `backend/.env` (or the process environment). `FPL_SEASON_START` defaults to `2026`. Credentials and downloaded data are ignored by Git.

## Database updates

The HTTP application never creates tables. Apply ordered, checksummed PostgreSQL migrations explicitly:

```sh
python -m app.scripts.migrate --check
python -m app.scripts.migrate
```

Migration 001 supports the audited four-table database or a fresh database. It preserves existing IDs and records, adds FPL history/provenance, and scopes provider identities by season. Migration history is stored in `schema_migrations`. Back up PostgreSQL before applying schema changes. Do not edit an already-applied migration; add the next numbered migration.

## Official FPL updates

Download an immutable source archive, then preview and apply it. The download defaults to the latest finalized gameweek; pass `--through-gameweek 6` if only history through six is wanted.

```sh
python -m app.scripts.download_fpl_dump data/fpl/2026-27-YYYYMMDD
python -m app.scripts.import_fpl_dump data/fpl/2026-27-YYYYMMDD --through-gameweek 7
python -m app.scripts.import_fpl_dump data/fpl/2026-27-YYYYMMDD --through-gameweek 7 --apply
```

Each archive includes the official bootstrap, all fixtures, gameweek live JSON, any required player histories, source URLs, retrieval time and SHA-256 hashes. Import validates season, finalized events, roster IDs, 380 fixture pairs, per-player minutes and points, historical club evidence and complete fixture coverage before writing. Imports run in a single transaction with a PostgreSQL advisory lock. Reapplying an archive updates existing observations without duplicating players, match stats or price snapshots. The fixture list refreshes all current-season schedules and results; the `through-gameweek` option bounds player history.

Existing API-Sports IDs and advanced stats are retained. Official FPL observations live separately in `fpl_match_stats`; missing shots/ratings are never synthesized. A null historical club means the official fixture side lists did not identify a non-playing player. Participating players require fixture-side or official player-history evidence.

`GET /api/data-quality` reports provider coverage, missing links and past fixtures without final status. `GET /api/players/{id}/fpl-history` returns official per-fixture observations. The API-Sports batch importer remains available for advanced metrics, and records the represented club from the match response. Its mutation endpoint is POST, not GET.

Do not use the legacy destructive rebuild to refresh a season. Use the archive importer to preserve saved squad IDs and history.

## Recommendations

Transfer recommendations use a transparent baseline in **expected FPL points**:

`recent FPL points / club fixtures in the last up to five gameweeks × club fixtures in the next five gameweeks`

DNPs count as zero. Estimates are not calibrated predictions. The model does not optimize the starting XI, bench, captaincy, chips or the future value of banked transfers. It uses the current roster/prices and therefore is not a historical backtest. Injured/suspended/unavailable players are excluded from buying; known unavailable owned players can still be sold. Unknown history blocks analysis rather than silently declaring no upgrade. Missing official lookback gameweeks also block analysis. Responses include coverage, horizon, assumptions and model units.

A transfer hit subtracts four **FPL points** from the baseline gain. Double transfers search every feasible candidate pair; `candidates_per_player` is accepted for client compatibility but no longer truncates the search. Actual `selling_prices_tenths` can be supplied per owned player. Omitted selling values explicitly assume current market prices. The frontend allows those values to be entered before analysis.

The separate positional Forge ratings remain exploratory analytics. They are not used to compare FPL-point transfer penalties.

## Validation

```sh
python -B -m unittest discover -s tests -v
```

Unit tests use isolated SQLite databases and never connect to production. The optional full-archive integration test validates and imports the local `data/fpl/2026-27` archive twice into an isolated database and verifies idempotency and point totals. Frontend validation: `npm run build` and `npm run lint` from `frontend/`.

## Database-backed frontend pages

`GET /api/dashboard?lookback_gameweeks=5` supplies the current season's players, current prices, official FPL point/minute/goal/assist aggregates, recent gameweek minutes, club directory, and complete fixture schedule. Set the lookback to 38 for season-to-date totals. Missing observations remain null rather than appearing as a confirmed zero. Fixtures use UTC timestamps; null gameweeks remain explicitly unassigned.

Overview, Player Explorer, Fixture Planner, and the squad picker share this response. Saved squads are reconciled by player ID with the current database roster, so changed prices and clubs are reflected without trusting old cached objects. Squad selections and transfer settings stay in local browser storage; they are user inputs, not a connected FPL manager account. Overview's recommendation uses the existing strategy endpoint only for a complete squad and valid settings.

The planner's estimated difficulty combines the existing attacking/defensive opponent measures from stored results. It is labelled as an estimate, not official FPL difficulty. A club/gameweek cell renders every matching fixture, preserving blanks and doubles. No schema migration or database write is needed for these pages.

Frontend squad-cache regression tests run with `npm test` from `frontend/` (Node 22.6+ for TypeScript stripping).
