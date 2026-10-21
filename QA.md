# MVP 1 QA — 21 October 2026

All application checks below used an isolated copy. Live browser flows used public example team #1 and PostgreSQL connections explicitly set to read-only. No code-driven migration, ingestion, production data update, account creation or deployment was performed.

## Completed

- **48 backend tests pass**, including forecast arithmetic, formation/captain validation, price assumptions, archive idempotency, imports, disabled/admin-only sync, bounded public queries, host/CORS checks, rate and request-size limits, safe errors, and readiness failures.
- **21 frontend tests pass**, including local squad reconciliation, saved lineups/captains, readable errors, team IDs, and backup validation. TypeScript production build and ESLint pass.
- Fresh Python 3.12 backend environment installed from the pinned requirements and ran the full suite. Fresh Node dependency installation succeeded; the explicit Mac-only direct build dependency was removed.
- Full frontend dependency audit and backend pinned-dependency audit report **zero known vulnerabilities** after updating Vite to 8.3.5 and Certifi to 2026.10.19. This is an advisory-database check at this date, not a guarantee against future vulnerabilities.
- Compose configuration parses successfully. Application tests confirm production fails closed without explicit hosts and disables API docs. Admin ingestion stays disabled unless deliberately enabled with an operator secret.

## Browser journeys completed

| Journey                                                     | Result                                                                                           |
| ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| Empty first-use state and Help/team-ID instructions         | Guide visible, manual/import paths available; no misleading signed-in avatar                     |
| Dismiss guide, choose light mode, reload                    | Preferences retained                                                                             |
| Light/dark/system modes                                     | Explicit choice persists; system changes follow device preference and work after reload          |
| Invalid team ID and unavailable-team response               | Readable inline errors; squad unchanged                                                          |
| Public team #1 preview, cancel, then confirm                | Cancellation preserves squad; confirmation loads 15 players and £0.1m recorded bank              |
| Remove and re-add a player                                  | Works; edit section stays open through completion                                                |
| Keyboard-only starting goalkeeper substitution and reversal | Works with valid formation and visible focus                                                     |
| Invalid bank and free-transfer settings                     | Analysis blocked with useful errors                                                              |
| Live Transfer Lab analysis                                  | 11 starter IDs, captain/vice and saved selling values sent; totals and gameweek breakdown render |
| Overview versus Transfer Lab                                | Same saved selling values and same estimated gain (+50.00 for the tested snapshot/settings)      |
| Navigate away and back                                      | Entered selling value retained                                                                   |
| Download backup, change to 14 players/£1.2m, cancel restore | Edited state retained                                                                            |
| Confirm backup restore                                      | Original 15 players and £0.1m bank recovered                                                     |
| Browser storage writes blocked                              | Visible warning; app remains usable for the current tab                                          |
| Malformed saved squad/lineup JSON                           | Visible recovery message; no app crash                                                           |
| Network failure, then retry                                 | Useful message and successful recovery                                                           |
| Unknown route                                               | Page-not-found message with recovery link                                                        |

## Accessibility and responsive checks

Automated axe checks targeting WCAG A/AA rules reported **zero violations** after fixes across Overview, My Squad, Players, Fixtures, Transfer Lab and Help in both light and dark modes. Populated forecast results and the first-use guide were checked separately and also reported zero violations. Fixed keyboard-inaccessible horizontal fixture tables and low-contrast dark chart labels.

All six pages were checked at 320, 390, 768, 1024 and 1440 CSS pixels in both themes: no unintended page-level horizontal overflow. Wide tables intentionally scroll inside focusable, labeled regions. Desktop and phone light-mode screenshots were inspected. Keyboard substitutions, focus outlines and preference changes were exercised in a real Chromium-based browser. Fonts no longer request a third-party service.

Automated scans are not a complete WCAG audit. Safari, Firefox, VoiceOver/NVDA, browser zoom combinations, touch hardware and real-user testing remain to be verified before making conformance claims.

## Not completed / launch gates

- Docker image builds, Nginx runtime/header checks, image vulnerability scans: **blocked because the local Docker engine was not running**. Only Compose parsing was verified.
- Remote GitHub Actions execution: not run; workflow prepared locally and no commit/push made for this change.
- Public HTTPS domain, certificate renewal, trusted-proxy IP forwarding, global rate limits, monitoring and rollback: require the selected hosting environment.
- Managed PostgreSQL role grants, TLS settings, backups/restoration and production migration/data coverage: require the production database. The current local database was not modified.
- Staging concurrency/load testing and real-user browser/device testing: not performed.
- Operator identity, support contact, hosting privacy/log retention and data-provider permissions: owner must finalize before public launch.

See DEPLOYMENT.md for the setup and verification steps. No automatic data-refresh feature or user authentication was added.
