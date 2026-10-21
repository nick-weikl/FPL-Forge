# Deployment readiness and operator runbook

This change prepares an anonymous MVP for deployment. It does **not** provision hosting, publish a site, migrate a production database, or claim production verification. The container configuration has been parsed locally; Docker image builds and live infrastructure checks remain unverified because the local Docker engine was not running.

## Included application protections

- Database sync routes are disabled by default. They return 404 unless `ENABLE_ADMIN_SYNC=true`; enabling also requires an `ADMIN_SYNC_TOKEN` of at least 32 characters. Enabled routes require that token in `X-Admin-Token`. Never ship it in frontend variables. Prefer offline operator commands and keep sync disabled on the public service.
- Public diagnostic provider calls were removed. Startup never writes schemas or ingests data. Production disables interactive API documentation.
- Production requires explicit `ALLOWED_HOSTS`. Optional CORS origins must be exact HTTPS origins. The supplied frontend proxies `/api` on the same origin, avoiding cross-origin setup.
- Requests have a 64 KB body cap, including streamed bodies. A bounded, per-process API rate limiter returns 429 with a retry hint. The Nginx template adds a per-client rate limit before the API. Apply your hosting provider's global limits too, especially if running multiple instances.
- Errors return safe messages and a generated request reference; internal exception details stay in server logs. Request bodies and credentials are not intentionally logged. Access logs are disabled in the supplied container command and Nginx template; configure any hosting/proxy logs and retention consciously.
- Security headers include a same-origin script policy, frame protection and no-referrer policy. API responses are not cached. Content-hashed assets can be cached; the HTML shell and theme initializer revalidate. SPA deep links fall back to the frontend shell.
- The API container runs as a non-root user with a read-only filesystem. The database is not bundled or published by Compose. Readiness checks database access and required core tables, not the freshness or completeness of season data.
- Browser requests time out and have recoverable errors. React has a rendering error boundary. Local persistence failures and malformed JSON show a visible warning; backup restoration validates the current season and player IDs before asking for confirmation.

## Before the first public launch

1. Choose a hosting region, domain, HTTPS termination and a managed PostgreSQL service. Configure TLS certificates, automated renewal, process restarts and uptime alerts. Terminate HTTPS in a trusted reverse proxy; enable HSTS there only after HTTPS is working.
2. Create separate database roles. The web application should have read-only access to the public data tables and required sequences/schema usage. Migrations and ingestion use a separate operator credential. Set database connection and statement timeouts; use encrypted database connections (`sslmode=verify-full` with your provider's CA where supported).
3. Back up the database, verify a restore in a separate database, run the migration preview and then migration with the operator role, and import validated current-season data. Keep protected source archives outside the public web root. Check schema migration status, season, player IDs and official points coverage.
4. Store `DATABASE_URL` and any operator API keys in the host's secret store. Use `APP_ENV=production`, explicit allowed hosts (including internal health-check hosts), no public admin sync, and the correct season. Never put secrets in `VITE_` variables, images, backups committed to Git, or CI output.
5. Build and scan the container images in the target Linux environment. The templates use maintained image tags; pin tested image digests for a reproducible release. Review the generated lockfile, dependency audits and CI results. No image scan or remote CI run has been performed in this task.
6. Smoke-test the real HTTPS domain: deep links, imports, CORS/host rejection, disabled admin routes, browser backups, both themes, error responses, and `/healthz`. Check that backend ports and database ports cannot be reached publicly. Verify the actual proxy's IP forwarding, rate limiting, CSP and cache headers.
7. Run a load test against a disposable staging deployment. Set concurrency, rate limits, memory/CPU limits and database pool capacity for measured traffic. The included rate limiter is process-local and keyed by the socket peer; do not trust arbitrary forwarded headers. Behind a trusted proxy, configure Uvicorn's forwarded-IP trust only for that proxy. In the Compose template Nginx handles per-client limiting, while the backend limit acts as a per-peer aggregate backstop.
8. Add the real operator's support/contact information and an accurate privacy notice for the chosen hosting and log retention. Confirm data-provider permissions for public use. The app's Help text describes application behavior, not an unknown hosting provider's policy. There are no advertising/analytics trackers or account cookies in this MVP.
9. Set up ongoing error and health monitoring, a manual data-update procedure, dependency review and a rollback plan. Automated ingestion remains intentionally deferred. Do not invite users to make decisions on outdated season data; the UI shows the available coverage and refuses incomplete analysis.

## Container template

The local template binds the frontend to loopback port 8080 and keeps the backend private. Put an HTTPS reverse proxy in front of it; it is not an Internet-facing TLS setup by itself.

```sh
# Set DATABASE_URL in your shell/secret manager to the populated, read-only app role.
# Include your domain plus the internal hosts needed by readiness checks.
export ALLOWED_HOSTS=your-domain.example,localhost,127.0.0.1,backend
export FPL_SEASON_START=2026
docker compose config --quiet
docker compose build
docker compose up -d
```

Health: backend `/health/live` checks the process; `/health/ready` checks database access and core schema. Frontend `/healthz` proxies readiness for an external monitor. A public API error includes an `X-Request-ID` that an operator can match to exception logs. Do not send secret values or complete user requests to a public bug tracker.

If hosting frontend and API separately, set the public build-time `VITE_API_BASE_URL`, exact HTTPS `CORS_ORIGINS`, allowed hosts, and a matching CSP `connect-src`; the supplied same-origin CSP intentionally does not allow arbitrary remote APIs. Serve the built `dist` folder, not Vite's development or preview server.

## Rollback

Keep the previously tested images and a recoverable database backup. Roll back application images first when possible; do not automatically roll back schema changes against a live database. Migrations are never triggered by application startup. Test recovery separately before launch.

## Authentication decision

User authentication can stay out of MVP 1 while personal state remains local and no server-side private user records exist. LocalStorage is not encrypted cloud storage and is accessible to scripts on the same origin; protecting scripts and avoiding secrets in browser storage still matters. Add authentication and server-side authorization before introducing synced accounts, private user records or paid features. Operator access to ingestion is separate from user accounts and is protected now.

References: [FastAPI deployment concepts](https://fastapi.tiangolo.com/deployment/concepts/) and [HTTPS deployment](https://fastapi.tiangolo.com/deployment/https/). Accessibility checks target [WCAG contrast guidance](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html); automated testing alone does not certify conformance.
