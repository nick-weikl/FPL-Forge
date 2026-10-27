# Database recovery and role verification

## Verified locally on October 27, 2026

The existing custom-format PostgreSQL 17 backup `backend/backups/20261021T191312Z/before-fixes.dump` was restored into a **new database on a separate PostgreSQL 17 Docker server**. The existing application database and its roles were not changed. Read-only source checks before and after the drill produced identical row counts and canonical row SHA-256 fingerprints for all eight source tables.

The backup's SHA-256 recorded for this drill is `e3bb10ffa0e619488565b486ed26248d0ba00644bdd699a866c54fceb36ac68c`. This was calculated from the available file during the drill; there was no independently stored original checksum or signature to establish older provenance.

| Checkpoint                                      | Verified state                                                                                                                                                                                                                                                    |
| ----------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Backup restored before migration                | 20 teams, 667 players, 380 fixtures, 2,000 advanced match-stat rows; four legacy tables                                                                                                                                                                           |
| Migration preview                               | `001_fpl_history` pending                                                                                                                                                                                                                                         |
| Migration applied in test database              | Eight tables; migration checksum matched the unchanged migration source; a second check showed no pending versions                                                                                                                                                |
| Relational checks                               | Zero foreign-key orphans and zero duplicate keys across the restored database's unique constraints/indexes                                                                                                                                                        |
| Existing local archive applied in test database | 668 players, 4,551 official FPL rows, seven imports through GW7, 668 price snapshots; all 667 existing internal player/FPL-ID mappings preserved                                                                                                                  |
| Operator role                                   | Migration check/apply and re-import succeeded under the operator role; a DDL/insert probe was rolled back; newly created tables inherited web SELECT only                                                                                                         |
| Actual web login                                | SELECT, including the migration ledger, succeeded; INSERT, UPDATE, public-schema CREATE TABLE and sequence reads were denied even after switching off the login's read-only transaction default                                                                   |
| Restore safeguards                              | Wrong hash, protected database name and an existing target were rejected; TLS/connection query options survived use of a private libpq service file                                                                                                               |
| Role safeguards                                 | Re-running grants succeeded; prior direct CREATE/TEMP/schema rights and global/schema default writes were removed; built-in privileged roles, inherited write memberships and unexpected public SECURITY DEFINER functions were rejected with nonzero exit status |
| Schema drift                                    | A missing required table made `--require-ready` fail in a second disposable database; that verification database was removed afterward                                                                                                                            |

Only the test database was migrated and populated. The already-local validated FPL archive supplied the additional official history; no provider download occurred. Advanced stats in this old backup remain at 2,000 rows through GW5, while the original application database has newer advanced observations. Historical prices and fixture dates remain unchanged, so data freshness still needs its own check.

**Recovery limitation:** the only available backup predates the October 21 fixes and later imports. Restoring it alone does not recreate the latest October 27 dataset. Before a release, take a new protected backup of the intended release database and repeat the drill against that artifact. A managed-host backup/PITR restoration has not been tested.

## Repeat the isolated restore drill

Use the project's Python environment with backend dependencies, matching PostgreSQL client utilities, and an isolated PostgreSQL admin connection loaded from a secret store into `RECOVERY_ADMIN_DATABASE_URL`. Do not point that variable at the running application database. The helper does not read the application's `.env`.

From the repository root:

```sh
python ops/database/restore_backup.py /protected/path/to/backup.dump \
  --database-name fpl_forge_restore_20261027_review \
  --expected-sha256 EXPECTED_BACKUP_SHA256
```

The helper verifies the hash before creation, accepts only disposable database names beginning `fpl_forge_restore_`, refuses existing targets, and restores in one transaction using `--no-owner --no-privileges`. It never uses `--clean`, overwrites an existing database, or automatically deletes a failed or successful target. A failed restore may leave the newly created empty target for inspection; choose a new name for another attempt.

Direct libpq URL query options such as `sslmode=verify-full`, `sslrootcert` and application/timeout settings are retained. Credentials are written only to a short-lived mode-0600 service file and do not appear in subprocess arguments. Environment TLS settings remain in effect. Nested `PGSERVICE` configurations and line breaks in connection parameters are rejected rather than silently simplified. Use an expanded admin URL from the secret store. Local Docker used `sslmode=disable`; use the managed provider's verified TLS requirements remotely.

Next load the **restored target's** operator URL into `DATABASE_URL`, change to `backend`, and inspect before applying:

```sh
python -m app.scripts.check_database_integrity
python -m app.scripts.migrate --check
python -m app.scripts.migrate
python -m app.scripts.migrate --check
python -m app.scripts.check_database_integrity --require-ready
```

Alternatively, `restore_backup.py --migrate` runs the explicit migration preview/apply/check against only its newly created target. The helper retains that target for inspection.

`check_database_integrity` uses PostgreSQL read-only, repeatable-read connections. It reports required ORM tables/columns, foreign-key orphans, duplicate unique keys, migration versions/checksums, counts and data fingerprints. `integrity_ok` describes relational/ledger integrity and can be true for a legacy backup with pending migrations. `ready_for_application` also requires the current table/column schema and no pending migrations; `--require-ready` returns a failing exit code otherwise. It does **not** establish season freshness, import coverage, correct data-provider use, or predictive accuracy. The checker normalizes timestamp rendering to UTC and sorts canonical JSON text with the C collation. Fingerprints describe row data, not dump bytes, complete schema metadata, or a claim of byte-identical backups across PostgreSQL versions. The recorded source-before/after comparison used identical server/session settings.

If additional archived data must be recovered, follow [MANUAL_REFRESH.md](MANUAL_REFRESH.md), preserving internal player IDs and checking provenance, season and coverage before applying to the recovery target. Compare mappings and totals before considering a cutover. Never refresh the running database merely to make a recovery test pass.

## Separate web and operator access

[ops/database/roles.sql](ops/database/roles.sql) is a reviewed template for an explicitly named database. Run it as that database's owner/admin, with connection credentials supplied by a private libpq service or secret-store environment. It is transactional, checks the connected target, creates dedicated unprivileged NOLOGIN groups, and refuses privileged/reused role memberships and unexpected public SECURITY DEFINER functions.

```sh
psql -X --set=ON_ERROR_STOP=1 \
  --set=target_database=YOUR_DATABASE \
  --set=operator_role=fpl_forge_operator \
  --set=web_role=fpl_forge_web \
  --file=ops/database/roles.sql
```

The operator group owns the database, public schema, tables and sequences. The web group receives CONNECT, schema USAGE and table SELECT, including `schema_migrations`; it receives no sequence rights, DML, schema CREATE or database TEMP rights. PUBLIC database/schema/table/sequence access is revoked for this target. Existing direct web CREATE/TEMP/schema rights and global/schema default table/sequence privileges are reset before minimal grants are applied. Defaults grant future operator-owned tables to the web group for SELECT only. Operator sessions must run as `fpl_forge_operator` before creating objects or running migrations/imports, so ownership and defaults apply. A `SET ROLE` issued in one `psql` session does not carry into a later Python process. Configure the operator login's database-specific startup role through the secret/account mechanism (`ALTER ROLE operator_login IN DATABASE target SET role TO fpl_forge_operator`, run by the authorized administrator), or add the libpq startup option `options=-c%20role%3Dfpl_forge_operator` to the operator connection URL (combine with any existing query options). Configure the matching private libpq service to use the same role. Verify `SELECT session_user, current_user;` through both operator tools; the session user should be the login and the current user the operator group before applying anything.

Provision actual LOGIN credentials separately through the host's account/secret mechanism. Give the web login only membership in `fpl_forge_web`, no administrator attributes or other memberships, and set its `default_transaction_read_only=on`. Give the operator login only the required operator group; use it in an isolated operator job. NOLOGIN-group settings do not automatically become login session defaults. Never put an operator URL in the public app container, frontend build variables, Git, or a recovery report. The drill tested actual PostgreSQL grants, not only a read-only URL flag.

## Manual acceptance before a real cutover

1. Start with a newly created recovery target and the expected artifact hash. Confirm a changed hash and an already-existing target are refused.
2. Compare restored counts, stable internal/FPL IDs, schema errors and migration ledger against the backup's recorded version and intended release. Inspect missing coverage separately.
3. Verify a second migration check is empty and `--require-ready` succeeds. Confirm the app's `/health/ready` and frontend `/healthz` succeed with the web login.
4. With that actual web login, check SELECT succeeds and a rolled-back write/DDL probe fails for permission reasons even if the session's read-only default is disabled. Confirm it has no inherited administrator/write memberships. Do not run write probes against the source database.
5. Confirm the operator can preview/apply migrations and import only in the recovery target. Check web SELECT defaults on any newly created table, then roll back/remove the probe.
6. Keep the previous app images, protected backup and original database until the restored deployment has been reviewed. Repoint configuration only during an explicitly approved cutover; this task did not perform one.

## Drill resources and cleanup

The review environment uses database `fpl_forge_restore_20261027` on the standalone PostgreSQL container `fpl-forge-release-db-20261027`, with a loopback-only database port. A generated web login has access only to its public data. Connection files live in private temporary storage outside Git. The container and target were left available for container/browser testing and owner review, not promoted to production.

After review, stop the review app first. Remove only the named standalone test container/network when no reviewer needs it; this discards its isolated test data. Keep the original backup protected. Rotate/delete temporary review credentials and private connection files. No automatic cleanup command targets the application's original database.
