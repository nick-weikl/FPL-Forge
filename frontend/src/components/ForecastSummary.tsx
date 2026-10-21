import type { StrategyResponse } from "../types/recommendation";
export default function ForecastSummary({ result }: { result: StrategyResponse }) {
  const weeks = result.baseline.gameweeks;
  const period = weeks.length
    ? `GW${weeks[0].gameweek}–${weeks[weeks.length - 1].gameweek}`
    : "No upcoming gameweeks";
  const chosen =
    result.recommended_strategy === "single_transfer"
      ? result.single_transfer
      : result.recommended_strategy === "double_transfer"
        ? result.double_transfer
        : null;
  const sellingAssumptions = result.selling_price_assumptions?.length ?? 0;
  return (
    <section className="panel forecast-summary" aria-labelledby="forecast-summary-title">
      <div className="panel-heading">
        <div>
          <h2 id="forecast-summary-title">
            {chosen ? "Your highest estimated gain" : "Keeping your XI comes out ahead"}
          </h2>
          <p>
            {period} · {result.horizon_gameweeks} gameweeks total
          </p>
        </div>
        <strong className="forecast-summary-gain">
          {result.best_net_score_gain > 0 ? "+" : ""}
          {result.best_net_score_gain.toFixed(2)} <span>estimated net points</span>
        </strong>
      </div>
      <p>
        Compared with keeping your starting XI and captain.{" "}
        {chosen
          ? `This includes ${chosen.transfer_cost ? `a ${chosen.transfer_cost}-point transfer hit` : "no transfer hit"}.`
          : "No transfer option improves the estimate after hits."}{" "}
        This is a forecast, not a guaranteed result.
      </p>
      {sellingAssumptions > 0 && (
        <p className="budget-assumption">
          <strong>Check your selling values:</strong> {sellingAssumptions} owned{" "}
          {sellingAssumptions === 1 ? "player uses" : "players use"} current market prices. Your
          actual selling values may be lower, so the suggested move may be unaffordable.
        </p>
      )}
      <details>
        <summary>Method, coverage & limitations</summary>
        <p>
          Official FPL results through GW{result.data_quality.official_fpl_through_gameweek ?? "—"}.
          Recent points per club fixture are projected across upcoming fixture counts. The estimate
          does not adjust for opposition or model future rotation.
        </p>
        <ul>
          {result.warnings.map((warning) => (
            <li key={warning}>{warning}</li>
          ))}
        </ul>
        <p>No transfers are submitted to FPL. Review your real team before acting.</p>
      </details>
    </section>
  );
}
