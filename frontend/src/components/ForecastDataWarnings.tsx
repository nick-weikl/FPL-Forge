interface Props {
  quality: { unusable_price_players?: number; past_unfinished_fixtures?: number };
}

export default function ForecastDataWarnings({ quality }: Props) {
  const prices = quality.unusable_price_players ?? 0;
  const fixtures = quality.past_unfinished_fixtures ?? 0;
  if (!prices && !fixtures) return null;
  return (
    <div className="budget-assumption" role="status">
      <strong>Check data freshness before acting.</strong>
      {prices > 0 && (
        <p>{prices} players have unusable prices and are excluded from incoming transfers.</p>
      )}
      {fixtures > 0 && (
        <p>
          {fixtures} past fixtures still lack final results. The stored schedule and forecast may be
          out of date.
        </p>
      )}
    </div>
  );
}
