# Local acceptance testing — October 27, 2026

This pass exercised the production Nginx/frontend/FastAPI containers at `http://127.0.0.1:18080` against a separate restored PostgreSQL test database. The public app role was read-only. The source application database was not changed. Tests used a generated inexpensive 15-player squad, not the owner's private team. No new Premier League or API-Sports data was requested.

## Browsers and scope

- Installed Brave/Chromium 155, driven in a separate headless Playwright CLI session, covered the main journey, errors, persistence, mobile layouts and keyboard controls.
- Actual installed Safari **27.0.1 (22625.1.29.11.28)** was operated through its native macOS UI. It was not substituted with Playwright WebKit.
- **Firefox is unverified.** It was not installed, and approval to download the browser test packages was declined. No download was retried. Firefox remains an owner review item.
- This is functional and responsive QA. It is not a complete accessibility audit, screen-reader certification, real-device touch test, load test or forecast-accuracy backtest.

## Verified journeys

| Check                                                               | Result                                                                                                                                                                                                                                                        |
| ------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Restore a generated backup with a preview and explicit confirmation | Passed in Chromium and actual Safari; 15 players, bank and settings loaded                                                                                                                                                                                    |
| Native Safari file picker and restored valid formation              | Passed; 3–4–3, distinct captain/vice and separate reserve goalkeeper                                                                                                                                                                                          |
| Starter/substitute swap                                             | Passed in Chromium and Safari; invalid positions stayed unavailable                                                                                                                                                                                           |
| Keyboard controls                                                   | Chromium Tab/Enter reached and activated a valid goalkeeper swap and outfield bench ordering; visible focus checked. Safari Up/Return changed the open native captain selector from Jonah Kusi-Asare to George Shepherd while keeping a distinct vice-captain |
| Saved state after reload                                            | Squad, valid lineup, bank, captain/vice and entered selling values persisted                                                                                                                                                                                  |
| Real recommendation request and rendering                           | Passed; the generated snapshot/settings returned +55.00 net points, with the double-transfer 4-point hit charged once                                                                                                                                         |
| Overview and Transfer Lab                                           | Matching gain for the same saved squad/settings; both show the unfinished-fixture warning                                                                                                                                                                     |
| Manual editing and browser backup recovery                          | Remove/search/re-add restored a valid 15-player squad without changing bank; malformed JSON was rejected without changing selections; restore cancellation preserved the edited squad; download succeeded                                                     |
| Invalid bank and missing official GW8 coverage                      | Readable errors, with no misleading success result                                                                                                                                                                                                            |
| Request failure and retry                                           | An aborted browser request showed an error; repeating after restoring the request recovered                                                                                                                                                                   |
| Themes                                                              | Light/dark choices persisted across navigation; Safari native light-theme control also worked                                                                                                                                                                 |
| Unknown route                                                       | Page-not-found recovery rendered through the production SPA proxy                                                                                                                                                                                             |

The sample numbers are test observations from stored GW7 data, not advice for the owner's actual team. Ten past fixtures remain unfinished in this stored snapshot. Prices were still within their seven-day eligibility limit during this pass; they expire without a separately authorized refresh. A successful UI check does not make that old snapshot current.

## Responsive checks and evidence

All six pages were checked at **320, 390, 768, 1024 and 1440 CSS pixels** in **light and dark themes**: 60 combinations, with no document-level horizontal overflow. Transfer Lab included populated recommendations. A second pass checked populated Overview at all five widths in both themes. The wide fixture/projection tables retain their own intentional horizontal scroll areas.

A fast initial automated navigation sweep reached the real proxy's rate limit. The app displayed its readable 429/retry state. The completed layout pass was paced to respect that limit rather than weakening the production configuration.

Ignored local artifacts under `output/playwright/` include:

- `production-backup.json`: generated sample squad suitable for the separate restored PostgreSQL test database.
- `production-transfer-desktop.png`, `production-transfer-lab-dark-320.png`, `production-squad-dark-320.png`, `production-overview-light-1440.png` and `production-overview-dark-320.png`: visually inspected screenshots.
- `responsive-result.txt`, `populated-overview-result.txt`, `transfer-result.txt`, `keyboard-core-result.txt` and `recovery-and-edit-result.txt`: browser-check evidence.
- The acceptance-only `serve_fixture.py`, `acceptance-backup.json` and supporting CLI snippets: an isolated in-memory SQLite app made from the existing local archive. Its clock is fixed to that archive's observation time solely inside that test process, so the fixture does not expire. It does not connect to the source PostgreSQL database or add production test endpoints. This helper is an ignored local artifact and is not part of the production image or deployment.

Generated backups and screenshots are review aids, not repository source. Keep them ignored. Do not upload actual personal browser backups or database archives with a commit.

## Owner's manual review before committing

1. Open the isolated local production app. Download a backup of any existing browser selection before replacing it. In Help, choose the generated sample `output/playwright/production-backup.json`, inspect the preview, cancel once, then repeat and confirm.
2. On My Squad, confirm 15 players, a valid XI, a distinct captain and vice, a reserve goalkeeper, and £1.0m bank. Select a starter and swap a compatible substitute. Order the outfield bench. Reload and confirm the state remains.
3. Using only Tab/Shift+Tab, Enter/Space and the native select-arrow keys, reach the lineup controls, change captain and navigate the wide tables. Confirm visible focus and no keyboard trap. Safari may require its normal full-keyboard-navigation preference or Option+Tab to visit every control; this task did not change OS or browser accessibility preferences.
4. In Transfer Lab, use last completed gameweek 7, enter real selling values, and run analysis. Compare the result with Overview and the weekly totals. Try gameweek 8 to see the missing-coverage error, then restore 7. Do not change stored timestamps to bypass expired-price protection.
5. Remove a player under Edit squad, search and re-add them, and verify formation/captains repair appropriately without changing the saved bank. Download a backup and restore it after a deliberate local edit; cancel must preserve the edit and confirmation must replace it.
6. Check all six pages at a narrow phone width in both themes. Scroll the wide tables inside their panels. Repeat the squad-to-analysis journey in **Firefox**, which remains the browser gate from this pass, and on a real phone/touch device.
7. Review the documented pending permission, freshness, hosting and accessibility boundaries. Keep commits and pushes on hold until the owner approves the final change list.

Live public FPL team-ID retrieval was intentionally not repeated while provider permission is pending. Existing automated import tests cover mocked valid, invalid, missing-player and provider-failure responses; these are distinct from a fresh live-provider check.
