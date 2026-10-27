# Deployment readiness and operator runbook

The supported prepared topology is one Linux host running the same-origin Nginx frontend and FastAPI backend, behind a host-level HTTPS proxy, with a separate PostgreSQL service. No paid host, domain, production secret store, public endpoint or notification service has been provisioned. Docker runtime checks are recorded below; successful local checks do not establish hosted TLS, production capacity or provider permission.

## Runtime boundaries

- The frontend listens on unprivileged container port 8080 and binds only host loopback. The backend has no published host port. PostgreSQL is deliberately not part of the production Compose file.
- Both application containers run as non-root users with read-only root filesystems, dropped Linux capabilities, bounded process counts, CPU/memory limits and temporary writable directories. The limits are starting budgets (backend 1 CPU/512 MB, frontend 0.5 CPU/128 MB), not a measured load-test capacity claim.
- Admin sync is forced off by Compose. Backend sync routes return 404 before provider work. Production API docs are disabled. Migrations and ingestion are separate operator commands and never run at startup.
- Readiness validates the database schema and production migration ledger. A database connection refusal normally returns 503; a blackholed database can exceed the frontend’s five-second health-proxy timeout and return 504 before the backend’s ten-second connection timeout. Both must alert as failed readiness. It does not establish current prices, completed results or season coverage; inspect `/api/data-quality` and follow [MANUAL_REFRESH.md](MANUAL_REFRESH.md).
- Nginx caps bodies at 64 KB, adds security headers, avoids caching API responses, caches hashed assets for one year, and supports SPA deep links. Its API rate limit uses the socket peer. When an HTTPS proxy is in front, configure per-client limits at that trusted edge; all requests otherwise share the proxy's Nginx budget. The backend limiter is an aggregate per-peer backstop, not a distributed global limit.
- Access logs are disabled in the provided app/Nginx commands. Application exceptions include request references. Configure host/proxy/managed-database log retention and redact secrets; never submit database URLs or complete user payloads to public issue trackers.

## Private configuration and database roles

Copy `deploy/production.env.example` to a protected location outside the checkout, set permissions to 0600, and replace its placeholder values. Use the selected host's secret manager to supply the read-only web `DATABASE_URL`; do not bake it into images. The sample values are unusable placeholders, not credentials. Real `*.env` files and `deploy/private/` are Git-ignored. Never run an expanded `docker compose config` in shared logs: use `config --quiet`.

Set these deployment variables:

| Variable                          | Requirement                                                                                                           |
| --------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| `DATABASE_URL`                    | Populated database using the read-only web login; use `sslmode=verify-full` and the provider CA for a hosted database |
| `ALLOWED_HOSTS`                   | Exact public domain plus `localhost,127.0.0.1,backend` for internal health probes; Compose requires it explicitly     |
| `FPL_SEASON_START`                | Season starting year, currently 2026                                                                                  |
| `FRONTEND_PORT`                   | Host loopback port, default 8080                                                                                      |
| `BACKEND_IMAGE`, `FRONTEND_IMAGE` | Locally built names during review; tested registry digests for a hosted release                                       |

`APP_ENV=production`, empty CORS origins and `ENABLE_ADMIN_SYNC=false` are fixed by this same-origin Compose topology. The browser uses `/api`; no frontend secret or public build-time API override is needed. If a future deployment separates origins, review CORS and CSP together before using it.

The sample URL explicitly uses the image's OS CA bundle at `/etc/ssl/certs/ca-certificates.crt` for providers whose certificate chain is publicly trusted. For a provider-specific CA, obtain and verify its certificate through that provider, store a readable certificate file at a protected host path, set `DATABASE_CA_FILE` in the private variable file, and change the URL's `sslrootcert` to `/run/secrets/postgres-ca.crt`. Add `-f compose.yml -f deploy/compose.database-tls.example.yml` to **every** Compose command for that deployment, including startup and rollback. For the Python smoke checker, pass `--compose-file deploy/compose.database-tls.example.yml` so its internal Compose probes use that overlay too. The overlay mounts only the CA file read-only; never disable certificate verification to make a hosted connection pass. Local recovery used isolated non-TLS PostgreSQL; hosted TLS and the provider CA have not been exercised.

Use separate owner/operator and web roles. Only the operator owns/migrates/imports; the web login receives database CONNECT, schema USAGE and SELECT on the necessary tables, including `schema_migrations`. Do not grant table writes, schema creation, role creation or database creation to the web login. Apply default SELECT privileges for future operator-owned tables and verify inherited/public privileges too. Use the role verification and restore procedures in [DATABASE_RECOVERY.md](DATABASE_RECOVERY.md). Keep a documented credential-rotation procedure in the selected secret manager; restart the backend after rotation and repeat readiness/smoke checks.

## Build and local or staging verification

From the repository root, use the same private variable file and stable Compose project name for every command:

```sh
docker compose --env-file /secure/fpl-forge/production.env -p fpl-forge config --quiet
docker compose --env-file /secure/fpl-forge/production.env -p fpl-forge build
docker compose --env-file /secure/fpl-forge/production.env -p fpl-forge up -d --force-recreate --wait --wait-timeout 90
python3 scripts/smoke_deployment.py --env-file /secure/fpl-forge/production.env --project fpl-forge
```

Recreate the entire application stack on release or rollback, including an unchanged frontend image: Nginx resolves the backend service address when it starts, so restarting only the backend could retain a stale upstream address. This simple single-host procedure permits a brief maintenance interruption; it is not a zero-downtime rollout.

The smoke checker reads public responses and executes HTTP probes inside the backend. It changes neither database contents nor server configuration. It verifies the frontend shell, deep links, both health paths, disabled production docs/admin routes, host rejection, API proxy/no-store/reference headers, hashed-asset caching/security headers and oversized-request rejection. Use `--base-url http://127.0.0.1:18080` if a review stack uses that port.

Base images are pinned to the digests tested on October 27, 2026. Dependency lockfiles remain authoritative. Review and update base digests and dependency advisories before release and periodically afterward, rebuild, retest and retain the previously tested release. CI now builds both container images as well as running source checks; no remote CI execution has occurred for these uncommitted changes. Container-runtime checks use a separately restored test database and do not require publishing or starting production infrastructure.

## Host setup before publication

1. Select the region, domain and Linux host/managed PostgreSQL. Keep database access private to the app/operator network and use managed backups. Confirm provider permissions before publishing football data.
2. Install a trusted HTTPS proxy on the same host. `deploy/Caddyfile.example` provides a same-origin reverse proxy to loopback port 8080 with certificate automation and HSTS. Supply the real domain, preserve certificate storage across restarts, verify renewal and firewall public access to HTTPS. HSTS is appropriate only after the real HTTPS domain works. The example has not obtained a certificate or run on a public domain.
3. Populate and verify the database using an operator credential, then start the public web process with the read-only credential. Test restoring a current backup separately first. Validate source freshness before users act on analysis.
4. Publish tested images to the chosen registry only after explicit approval. Record immutable image digests, Git revision, migration versions, season/import timestamps and backup reference in a private release record. Set `BACKEND_IMAGE` and `FRONTEND_IMAGE` to those digests. Run `pull`, then `up -d --no-build --force-recreate --wait`; do not build from a moving branch on the host.
5. Repeat the smoke checker against the actual HTTPS domain. Confirm public backend/database ports are closed, exact host/CORS behavior, CSP/cache/security headers and edge rate limits. Exercise the owner's acceptance checklist, then a small concurrency test before raising the initial limits.
6. Add a real support contact and a hosting-specific privacy/log-retention notice. Configure database storage/connection alerts, certificate-expiry alerts and application error notifications. Verify each notification reaches the actual operator before inviting testers.

## Monitoring prepared for hosting

`/health/live` is the private process check; `/health/ready` is the private schema/database check; frontend `/healthz` exposes the readiness result to an external monitor. Compose checks both containers and restarts exited processes. Docker does not automatically restart a merely unhealthy process: the external monitor/operator must investigate persistent unhealthy status.

`deploy/blackbox.yml`, `deploy/prometheus.example.yml` and `deploy/fpl-alerts.yml` provide an optional HTTPS readiness probe and alerts for two minutes of failure or a missing probe. Substitute the actual domain/exporter address, install them into the selected monitoring stack, configure Alertmanager or the host's notification integration, and deliberately exercise the alert/recovery path. They are preparation files; no recurring monitor or notifications have been activated here. A hosted uptime service can monitor the same endpoint instead. Monitor data freshness separately from uptime with `/api/data-quality` and the manual refresh checklist.

## Rollback and recovery

1. Keep the previous release's private variable file and immutable frontend/backend image digests. Preserve a tested backup and the source archive references used for ingestion.
2. For an application regression without schema incompatibility, set the previous image digests in the private deployment file, then run:

```sh
docker compose --env-file /secure/fpl-forge/production.env -p fpl-forge pull
docker compose --env-file /secure/fpl-forge/production.env -p fpl-forge up -d --no-build --force-recreate --wait --wait-timeout 90
python3 scripts/smoke_deployment.py --env-file /secure/fpl-forge/production.env --project fpl-forge
```

3. Do not automatically reverse migrations or restore a backup over the active database. If schema/data recovery is required, restore to a new database, verify migrations and data/IDs, test with a separate read-only web login, then switch the private database URL during a controlled maintenance window. The detailed drill is in [DATABASE_RECOVERY.md](DATABASE_RECOVERY.md).
4. If readiness fails after deployment, inspect safe health responses and matching request-reference logs, check the database/migration status, and roll back to the prior compatible app release. Never enable admin sync as a readiness workaround. Notify the operator and retain the failed release evidence without exposing secrets.

## Local evidence and limits

The local release-readiness report records the exact image/runtime and browser/database checks. Production builds use Python 3.12 and Node 24. A fresh build discovered GHSA-mrhx-c7xc-m3w5 in transitive development-only Zod 4.6.5 (ESLint tooling); its lock resolution was updated to compatible 4.6.7 and the fresh dependency audit returned zero known vulnerabilities. Zod is not shipped in the Nginx-only final image. This is a dated advisory check, not a guarantee of vulnerability-free images; image CVE scanning remains a release operation.

Verified locally on Docker Desktop 4.97.0 / Docker Engine 29.9.2, Linux arm64. The pinned base digests are multi-architecture OCI indexes with AMD64 entries, so CI can resolve them; actual AMD64 application builds/runtime remain for CI or the chosen host. All 21 frontend tests also passed inside the pinned Node 24 Linux container:

| Check                                                                       | Result                                                                                                                                |
| --------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| Backend Python 3.12 image build and frontend Node 24 production build       | Passed                                                                                                                                |
| App startup against separately restored PostgreSQL with read-only web login | Both containers healthy                                                                                                               |
| Backend process/database/schema readiness; frontend readiness proxy         | Passed                                                                                                                                |
| Isolated database stop/start drill                                          | Readiness 200 → 503 → 200; liveness stayed alive; both configured health commands failed during outage, then final containers healthy |
| Disabled API docs and every guarded sync endpoint                           | 404                                                                                                                                   |
| Untrusted Host                                                              | 400                                                                                                                                   |
| SPA deep link, HTML/theme revalidation, API no-store/request reference      | Passed                                                                                                                                |
| Hashed asset caching plus security headers                                  | Passed                                                                                                                                |
| Request body above 64 KB                                                    | 413                                                                                                                                   |
| Non-root users, read-only root filesystems, dropped capabilities and limits | Inspected and confirmed                                                                                                               |
| Monitoring/Compose/CI YAML syntax                                           | Parsed; hosted monitoring not activated                                                                                               |

The review app is left at `http://127.0.0.1:18080`, Compose project `fpl-forge-release`, with private variable file `/private/tmp/fpl-forge-release-compose.env` and isolated-network override `/private/tmp/fpl-forge-release-compose.override.yml`. This is a local restored test database, not the source database. From the repository root, repeat the smoke check with those paths and `--base-url http://127.0.0.1:18080`. To stop only the review app after acceptance:

```sh
docker compose --env-file /private/tmp/fpl-forge-release-compose.env -f compose.yml -f /private/tmp/fpl-forge-release-compose.override.yml -p fpl-forge-release down
```

The separate `fpl-forge-release-db-20261027` database container remains available for recovery inspection. Stop it with `docker stop fpl-forge-release-db-20261027` after the review. Do not delete its volume or private credential files until the owner is finished. These local `/private/tmp` paths are session-specific and are not production secret-storage instructions.

No public hosting, domain, registry publication, production backup policy, monitoring destination or public TLS/certificate cycle has been exercised. No claim of public-launch readiness overrides those external checks or pending data-use permission.
