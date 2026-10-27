# Manual data refresh

This is an operator procedure, not a background task. Opening the app never downloads data, creates tables, migrates or imports. The public web service must keep its read-only database role and `ENABLE_ADMIN_SYNC=false`.

No new Premier League or API-Sports retrieval was performed for the release-readiness work. Provider permission remains pending. Use the already-local archive for isolated tests; perform new retrieval or a production refresh only when the owner has resolved the provider conditions and authorized that operator activity.

## Before updating a real database

1. Choose the season and the last **finalized** gameweek. `FPL_SEASON_START=2026` means `2026/27`; do not change the season label on old observations. Record the operator, target database, archive path and gameweek in a private operations log.
2. Open a separate operator shell with the database credential supplied through a secret manager. `DATABASE_URL` is used by the Python commands. Configure a matching libpq service (`PGSERVICE=fpl_forge_operator`) and protected password file for `pg_dump`/`psql`, following [DATABASE_RECOVERY.md](DATABASE_RECOVERY.md). Never paste database URLs, passwords or API keys into Git, screenshots or issue reports.
3. Confirm the target using `psql -X -c 'SELECT current_database(), current_user;'`. Confirm it matches the Python connection configuration. Do not leave operator credentials in the public web container. Ensure each new Python/libpq connection starts as the operator group: configure the login's database-specific startup role or the operator URL's `options=-c%20role%3Dfpl_forge_operator` parameter as described in the recovery guide. A `SET ROLE` in a previous `psql` window is not inherited by Python. Verify both `session_user` and `current_user` before applying changes so future tables receive the intended ownership and web SELECT defaults.
4. Back up the populated database before applying migrations or data changes. Verify recovery in a separate test database using the recovery guide. Keep the source archive and the last good backup until the updated data has been checked.

Example backup from `backend`, with libpq service credentials already configured:

```sh
umask 077
mkdir -p backups
backup_file="backups/pre-refresh-$(date -u +%Y%m%dT%H%M%SZ).dump"
pg_dump --format=custom --no-owner --no-acl --file="$backup_file"
pg_restore --list "$backup_file"
shasum -a 256 "$backup_file"
```

A readable archive listing is not a successful recovery test. Follow the separate restore drill before depending on the backup.

## Validate an archive

Use a new directory per observation. Never overwrite old source files, change the manifest timestamp, or relabel old prices as fresh. The importer verifies stored source URLs and SHA-256 hashes.

After provider permission and owner authorization, the explicit retrieval command is:

```sh
# From backend; this makes external provider requests, but no database writes.
.venv/bin/python -m app.scripts.download_fpl_dump data/fpl/2026-27-YYYYMMDD --through-gameweek 7
```

Replace the directory and gameweek with the actual approved refresh. While permission is pending, skip retrieval and point the preview at an already-existing archive for isolated validation.

```sh
# From backend, with DATABASE_URL configured for the intended target.
.venv/bin/python -m app.scripts.migrate --check
.venv/bin/python -m app.scripts.import_fpl_dump /path/to/archive --through-gameweek 7
```

Review the preview's season, observation time, roster/new-player counts, completed fixtures, official-stat rows and unassigned historical clubs. A zero-minute DNP may have an unknown club; participating players require historical evidence. Imports must cover every finalized fixture in the requested gameweeks. Stop on checksum, identity, coverage, season or points/minutes validation errors.

The `migrate --check` command must report no pending migration and unchanged applied checksums. Apply a new migration only as a separately reviewed schema change after backup and an isolated recovery test. Never edit an applied migration file.

## Apply and verify

Only after reviewing the preview and backup, run the same archive and gameweek with `--apply`:

```sh
.venv/bin/python -m app.scripts.import_fpl_dump /path/to/archive --through-gameweek 7 --apply
.venv/bin/python -m app.scripts.migrate --check
.venv/bin/python -m app.scripts.check_database_integrity --require-ready
.venv/bin/python -m app.scripts.check_recommendations
```

The archive import runs in one transaction with an advisory lock. If validation or import fails, the transaction rolls back; inspect the failure rather than switching to the legacy rebuild. Successful re-import of the same archive must not duplicate observations or snapshots. Preserve internal player IDs because saved browser squads use them.

The integrity and recommendation checkers use read-only database connections. The recommendation checker requires the development dependencies and usable stored prices. It tests a generated legal squad; it does not submit FPL transfers or establish predictive quality. An old archive may import successfully yet still have expired prices; do not alter timestamps to force recommendation checks to pass.

Review `/api/data-quality` and `/api/dashboard` through the running application. Confirm season, latest completed gameweek, unfinished past fixtures, price eligibility, forecast horizon and warning text. Readiness checks schema/migration availability; it intentionally does not imply current data. Test your saved squad in both Overview and Transfer Lab, including selling values and bank, then mark the refresh complete in the private operations log.

## Advanced statistics and failure recovery

Official FPL point observations are independent of API-Sports links. Missing advanced ratings, shots or other provider fields must remain unknown. The current API-Sports batch import is an optional separate operator activity under the provider's authorization and quota; it is not triggered by an official archive import. Keep public sync routes disabled. Do not use `rebuild_fpl_data` or `add_fpl_fields` as a routine refresh procedure.

If a successful but incorrect update is discovered, retain the failed archive and error references privately. Put the application into maintenance if its advice is unsafe, restore the last good backup into a **new** database, validate it and deliberately switch the application connection. Do not overwrite the working database with an untested restore or pretend an old backup has current prices. Application-image rollback and database recovery are separate operations; see [DEPLOYMENT.md](DEPLOYMENT.md) and [DATABASE_RECOVERY.md](DATABASE_RECOVERY.md).
