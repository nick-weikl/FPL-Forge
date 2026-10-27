# Release-readiness QA — October 27, 2026

Base revision: `7d40828`. This report covers local, uncommitted changes. No commit, push, registry publication, public deployment, source-database migration/update or new football-provider retrieval was performed. The Premier League permission response remains pending.

## Verification record

| Area                         | Evidence                                                                                                                                                                                                                                                                                                                                                          |
| ---------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Backend checks               | 60 tests pass in the existing local Python environment, including the local archive integration. Production Python 3.12 image independently runs the same 60 tests with 59 passing and the unavailable archive integration skipped.                                                                                                                               |
| Frontend checks              | 21 tests pass locally and independently in the pinned Node 24 Linux image; ESLint, TypeScript/Vite production build and formatting checks pass. Production image builds use Node 24.                                                                                                                                                                              |
| Dependencies                 | A fresh install found a transitive development-only Zod advisory; only its lock resolution changed from 4.6.5 to 4.6.7. Fresh audit reports zero known npm advisories at this date. This does not cover operating-system image vulnerabilities.                                                                                                                   |
| Production images            | Python 3.12 API and Node 24 build/Nginx runtime images build successfully from pinned base digests. Both application containers start healthy and run non-root with read-only filesystems, dropped capabilities and resource/process limits.                                                                                                                      |
| HTTP boundaries              | Repeatable smoke check passes frontend shell/deep links, API proxy, liveness/readiness, allowed-host rejection, disabled production docs, every admin sync route, request-size limits, request references and security/cache headers.                                                                                                                             |
| Outage and recovery          | With only the isolated test database stopped, frontend readiness changed from HTTP 200 to 503, backend liveness stayed 200, and both configured Docker health commands failed. Restarting that database restored readiness and both containers became healthy; the full smoke check passed again.                                                                 |
| Readiness accuracy           | Required tables and mapped columns are checked. Production also checks exact migration versions/checksums. Regression tests cover a missing table/ledger and changed checksum; migration preview rejects unknown applied versions rather than claiming no work is pending. Liveness stays independent of database readiness.                                      |
| Database recovery            | Existing PostgreSQL 17 custom backup restored into a separate Docker database. Migration and the already-local official archive were applied only there. Read-only checks find no orphaned foreign keys or duplicate unique keys, no pending/unknown/changed migrations, and required schema present.                                                             |
| Stable IDs and source safety | All 667 existing restored player/FPL ID mappings survived migration/import. Independent before/after row counts and content fingerprints match for all eight source tables. Source roles and database contents were not changed.                                                                                                                                  |
| Database permissions         | A real web login can read the migration ledger and app data; INSERT, UPDATE, CREATE TABLE and sequence access are denied even after disabling the session's default read-only setting. Operator ownership/default privileges and migration/import operation are checked separately.                                                                               |
| Browser journey              | Actual Safari 27.0.1 and Brave/Chromium passed the tested squad-to-recommendation, backup, keyboard, persistence and error/retry journeys. All six pages at five widths in two themes, plus ten populated Overview layouts, passed without document-level horizontal overflow (70 cases). Detailed evidence is in [ACCEPTANCE_TESTING.md](ACCEPTANCE_TESTING.md). |

The backup is older than the current source database. It contains 667 players and 2,000 advanced-stat rows; applying the local official archive reconstructs 668 players, 4,551 official rows, seven imports and 668 price snapshots. This does not reconstruct later API-Sports observations or make archived prices fresh. The restored review app displays those coverage/freshness limitations.

## Repeating the checks

From `backend` with development dependencies installed:

```sh
.venv/bin/python -B -m unittest discover -s tests -v
.venv/bin/ruff check ..
.venv/bin/ruff format --check ..
# With the intended database configured, using enforced read-only checker connections:
.venv/bin/python -m app.scripts.check_database_integrity --require-ready
.venv/bin/python -m app.scripts.check_recommendations
```

From `frontend`:

```sh
npm ci
npm test
npm run lint
npm run build
npm run format:check
npm audit
```

For container smoke checks, use `scripts/smoke_deployment.py` and the same private Compose variable file/project described in [DEPLOYMENT.md](DEPLOYMENT.md). Use [DATABASE_RECOVERY.md](DATABASE_RECOVERY.md) to repeat a restore into a new explicitly disposable database, never over the source database. Use [MANUAL_REFRESH.md](MANUAL_REFRESH.md) for any separately authorized refresh.

## Owner review before commit or push

1. Review the running isolated container app at `http://127.0.0.1:18080`; follow [ACCEPTANCE_TESTING.md](ACCEPTANCE_TESTING.md) for a safe generated browser backup and the full browser checklist. This is a restored test database, not the working source database.
2. Check squad restore preview/cancellation/confirmation, XI/captains, bank/selling values, reload persistence and agreement between Overview/Transfer Lab. Keep archived-data warnings visible and understandable.
3. Use a narrow phone-sized window and keyboard-only navigation. Check fixture-table scrolling, focus, dialogs and help. Repeat in Firefox once that browser is available; it was not tested here.
4. Read the recovery procedure, verify the isolated target naming/no-overwrite guards, and review the prepared role grants, secret-store instructions and monitoring/rollback configuration before using them on a chosen host.
5. Review all local changes and explicitly approve any later commit/push. No hosting or provider permission should be inferred from successful local tests.

## Inaccessible and external release checks

- Firefox is not installed. Permission to download a browser was declined, so Firefox and downloaded Playwright WebKit were not run. Actual Safari was exercised directly; WebKit results are not substituted for Safari results.
- Public HTTPS/domain/certificate renewal, edge/global per-client limits, real hosted secrets/role provisioning, notification delivery, managed backups and production rollback remain dependent on a selected host. Monitoring templates are prepared, not activated.
- Local production-image runtime tests used Linux ARM64. Pinned base digests are multiarchitecture indexes with AMD64 entries, but an AMD64 app build/runtime was not performed locally.
- CI now includes both container builds, but the new workflow has not run remotely because these changes have not been committed or pushed.
- OS/image CVE scanning, measured staging concurrency/load capacity, screen-reader testing and complete accessibility conformance are not established by this work.
- New provider retrieval, data freshness updates, and a public/friends release remain pending the permission/provider decision and explicit owner authorization.

Historical October 21 checks remain in Git history. This report does not reuse earlier accessibility or browser claims as new observations. See [RECOMMENDATION_QA.md](RECOMMENDATION_QA.md) for the separate previously completed recommendation-arithmetic audit.
