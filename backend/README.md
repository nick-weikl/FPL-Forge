# FPL Forge backend

Run commands from `backend/` with the project's Python environment. Set `DATABASE_URL` in `backend/.env` (or the process environment). `FPL_SEASON_START` defaults to `2026`. Credentials and downloaded data are ignored by Git. Use `requirements-dev.txt` for tests and operator smoke checks; runtime images install `requirements.txt`. Use a read-only role for the running web application and a separate operator role for explicitly authorized updates.

See [database recovery](../DATABASE_RECOVERY.md), [manual refresh](../MANUAL_REFRESH.md) and [deployment](../DEPLOYMENT.md) for the reviewed operator workflows. No new provider retrieval is authorized while the permission decision remains pending.

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

`recent FPL points / recorded player fixtures in the last up to five gameweeks × current club fixtures in the next five gameweeks`

Model `recent_fpl_points_baseline_v2` uses each player’s recorded fixture opportunities, so a club transfer does not divide old-club points by the new club’s fixture count. Recorded DNPs count as zero, including zero-minute rows with an unknown historical club. Missing records are unknown and excluded; short histories can produce less reliable estimates.

Estimates are not calibrated predictions. The model uses the selected starting XI and doubles the selected captain. Incoming players inherit the outgoing slot and captaincy. It does not optimize future lineups or model bench points, automatic substitutions, vice-captain fallback, chips or the future value of banked transfers. It uses the current roster/prices and therefore is not a historical backtest. Injured/suspended/unavailable players are excluded from buying; known unavailable owned players can still be sold. Unknown history blocks analysis rather than silently declaring no upgrade. Missing official lookback gameweeks also block analysis. Responses include coverage, horizon, assumptions and model units.

Incoming prices must be positive, observed within seven days, and not dated in the future. Unusable prices and past unfinished fixtures produce visible freshness warnings on Overview and Transfer Lab. If unusable prices leave no eligible incoming players, analysis returns an actionable error instead of recommending a hold. Partial candidate coverage still permits analysis with a warning.

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

### Read-only PostgreSQL recommendation check

With development dependencies and the configured local database, run `python -m app.scripts.check_recommendations` from `backend`. It generates a legal inexpensive sample squad, enforces PostgreSQL read-only connections, and checks the real strategy endpoint for free-transfer settings 0, 1 and 2, budgets, club/position rules, captain/bench weighting, one-time hits, missing coverage and simulated stale prices. The stale scenario changes only the checker’s in-memory clock. It never retrieves provider data or changes stored prices. This is an arithmetic/integrity check, not a predictive backtest.

## Health and deployment readiness

`/health/live` is independent of PostgreSQL. `/health/ready` checks the columns of every required application table; in production it also requires the exact migration versions/checksums in the shared registry. It returns a safe HTTP 503 if a table, column or migration is missing or different. Startup never repairs those conditions. Readiness does not establish roster completeness or freshness; inspect `/api/data-quality` and use the read-only integrity checker separately.
