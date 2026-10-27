# Recommendation integrity check — October 27, 2026

Scope: recommendation arithmetic, historical fixture denominators, PostgreSQL integration and stale-data behavior. Work is based on merge commit `2d4b40f`. No database updates, migrations, new football-provider requests, commits, pushes or deployments were performed.

## Changes

- Forecast model `recent_fpl_points_baseline_v2` divides recent points by each player's recorded official fixture opportunities. This avoids mixing historical points with the current club's different fixture count after a transfer. Recorded zero-minute/DNP rows remain in the denominator even when their historical club is unknown. Missing records are unknown rather than imputed zeros. Upcoming fixtures still follow the current club. Short histories remain an explicit limitation; this change does not establish predictive accuracy.
- Price eligibility and data-quality reporting use the same rule: a positive price with an observation timestamp between now and seven days ago, inclusive. Missing, invalid, expired and future-dated observations are excluded from incoming transfers and reported.
- If unusable prices leave no eligible incoming players, the strategy endpoint returns HTTP 400 with an actionable error. It does not silently conclude that keeping the squad is best. Partial price coverage allows analysis with a warning.
- Overview and Transfer Lab show price and unfinished-fixture warnings without requiring the method details to be opened. Help and backend documentation describe the revised denominator and limitations.
- A repeatable read-only PostgreSQL checker generates a legal sample squad and exercises the real strategy endpoint. The archive integration test uses its recorded observation time so it remains deterministic after archive prices expire.

## Verification

- 55 backend tests passed, including six new regression tests and the full local archive integration test. New cases cover unequal old/new club schedules, recorded DNPs, missing history, blank/double gameweeks, the exact seven-day boundary, missing/zero/future prices, partial price coverage, all-stale failure and unfinished-fixture warnings.
- 21 frontend tests passed. ESLint, Prettier, Ruff lint/format checks and the TypeScript/Vite production build passed. The warning component was also rendered and checked for healthy, partial-price, unfinished-fixture and combined warning states.
- The backend suite ran using the existing local Python 3.10.9 environment; CI's Python 3.12 environment was not independently recreated. Frontend checks used local Node 26.10.0. Browser interaction and layout checks for these changes remain for local review.

## Stored PostgreSQL results

Every checker connection had PostgreSQL `default_transaction_read_only=on`; a transaction also confirmed read-only mode. The checker used stored data and in-process HTTP requests, with no provider requests.

- Official and advanced coverage: GW7, with 668 players forecastable.
- No historical club-transfer example was present in the stored GW3–7 lookback. The transfer correction was therefore verified with synthetic historical fixtures, not claimed as observed in this database.
- Fourteen players have fewer recorded fixtures than their current club's lookback fixture count. Their denominator changes in v2; this includes short histories and is not evidence that all fourteen transferred clubs.
- Current prices were still usable at check time. Ten past fixtures remained unfinished in the database, so the stored forecast must not be treated as an up-to-date real-world recommendation.
- With the generated legal squad, £1.0m bank and supplied market-price selling values, the best double-transfer estimates were +51.00, +55.00 and +59.00 net points with 0, 1 and 2 free transfers. These are sample integrity results, not recommendations for the owner's actual squad.
- For each plan, the checker independently verified position matching, ownership exclusion, distinct incoming players, three-per-club limits, affordability, remaining bank, fixed-XI/bench/captain multipliers, transfer hits charged once and agreement between plan gains and weekly breakdowns.
- Requesting GW8 failed with HTTP 400 for missing official lookback coverage. Advancing only the checker's in-memory clock by eight days produced HTTP 400 for expired prices, with no hold strategy returned. Stored timestamps were never altered.

Run again from `backend`, with development dependencies installed and the existing database configured:

```sh
python -m app.scripts.check_recommendations
```

The successful-transfer scenarios require usable stored prices and future gameweeks. If the existing snapshot has expired, refresh it only after that operator activity is separately authorized; do not change timestamps to make this check pass.

## Owner review before commit or push

1. Run the app locally and analyze a complete saved squad in Transfer Lab with the last completed gameweek set to 7 for this stored snapshot. Check the visible unfinished-fixture warning and the method explanation.
2. Confirm Overview and Transfer Lab agree for the same squad, XI, captain, bank, selling values and free transfers. Compare net gains to the displayed weekly breakdown.
3. Set the last completed gameweek to 8 and confirm the missing-coverage message is readable. Return it to 7 afterward. Once stored prices expire, analysis should report unavailable rather than recommend keeping the squad.
4. Review the intended model change: recorded DNPs count as zero, missing records are excluded, and short histories can be optimistic. No forecasting calibration or backtest has been added.
5. Approve the reviewed changes before any commit or push. Provider permission, data refresh, container/runtime verification and public deployment remain separate work.
