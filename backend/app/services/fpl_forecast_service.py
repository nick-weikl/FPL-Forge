"""Transparent baseline in FPL points, separate from the exploratory Forge rating.

Forecast = recent FPL points / club fixtures in the lookback * upcoming fixtures
within the next five gameweeks. DNPs count as zero. No claim of model calibration.
"""

from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

from app.database import SessionLocal
from app.models import Fixture, Player
from app.models.fpl_data import FPLImport, FPLMatchStat
from app.services.data_quality_service import get_data_quality
from app.services.football_api import SEASON
from app.services.fpl_price_service import FPL_SEASON
from sqlalchemy import select
from sqlalchemy.orm import joinedload


def build_forecasts(db, current_gameweek, horizon=5):
    if not 1 <= current_gameweek <= 38:
        return {"error": "Gameweek must be 1–38"}
    quality = get_data_quality(db)
    lookback_start = max(1, current_gameweek - 4)
    imported = {r.gameweek for r in db.scalars(select(FPLImport).where(FPLImport.season == SEASON))}
    missing = sorted(set(range(lookback_start, current_gameweek + 1)) - imported)
    if missing:
        return {
            "error": "Official FPL coverage is incomplete for the requested lookback",
            "missing_gameweeks": missing,
            "data_quality": quality,
        }
    fixtures = list(db.scalars(select(Fixture).where(Fixture.season == SEASON)))
    past_counts = Counter()
    future_counts = Counter()
    future_by_week = defaultdict(Counter)
    for f in fixtures:
        if f.gameweek is None:
            continue
        if lookback_start <= f.gameweek <= current_gameweek and f.status == "FT":
            past_counts.update([f.home_team_id, f.away_team_id])
        if current_gameweek < f.gameweek <= min(38, current_gameweek + horizon):
            future_counts.update([f.home_team_id, f.away_team_id])
            future_by_week[f.gameweek].update([f.home_team_id, f.away_team_id])
    points, observations = defaultdict(int), Counter()
    for stat in db.scalars(
        select(FPLMatchStat)
        .join(Fixture)
        .where(
            Fixture.season == SEASON,
            Fixture.status == "FT",
            Fixture.gameweek.between(lookback_start, current_gameweek),
        )
    ):
        points[stat.player_id] += stat.total_points
        observations[stat.player_id] += 1
    rankings = defaultdict(list)
    by_id = {}
    now = datetime.now(timezone.utc)
    for player in db.scalars(
        select(Player).options(joinedload(Player.team)).where(Player.fpl_season == FPL_SEASON)
    ):
        observed = player.price_updated_at
        if observed is not None and observed.tzinfo is None:
            observed = observed.replace(tzinfo=timezone.utc)
        # Unknown history is not treated as a confirmed zero-point player.
        if not observations[player.id] or not past_counts[player.team_id]:
            continue
        forecast = points[player.id] / past_counts[player.team_id] * future_counts[player.team_id]
        eligible = (
            player.availability_status == "a"
            and player.chance_of_playing != 0
            and player.price_tenths is not None
            and player.price_tenths > 0
            and observed is not None
            and now - observed <= timedelta(days=7)
        )
        record = {
            "player_id": player.id,
            "name": player.name,
            "position": player.position,
            "team_id": player.team_id,
            "team_name": player.team.name,
            "price_tenths": player.price_tenths,
            "overall_score": round(forecast, 4),
            "expected_points": round(forecast, 4),
            "can_buy": eligible,
            "observed_matches": observations[player.id],
            "gameweek_points": {
                week: round(
                    points[player.id]
                    / past_counts[player.team_id]
                    * future_by_week[week][player.team_id],
                    4,
                )
                for week in range(current_gameweek + 1, min(38, current_gameweek + horizon) + 1)
            },
        }
        record["overall_score"] = record["expected_points"] = round(
            sum(record["gameweek_points"].values()), 4
        )
        # Injured/unavailable owned players can still be sold; do not project them as available.
        if player.availability_status in ("i", "s", "u") or player.chance_of_playing == 0:
            record["overall_score"] = record["expected_points"] = 0.0
            record["gameweek_points"] = {week: 0.0 for week in record["gameweek_points"]}
        by_id[player.id] = record
        rankings[player.position].append(record)
    for ranking in rankings.values():
        ranking.sort(key=lambda p: (-p["overall_score"], p["price_tenths"] or 0, p["player_id"]))
    return {
        "rankings": dict(rankings),
        "by_id": by_id,
        "data_quality": quality,
        "model": "recent_fpl_points_baseline_v1",
        "score_units": "expected_fpl_points",
        "horizon_gameweeks": min(horizon, 38 - current_gameweek),
        "lookback_gameweeks": [lookback_start, current_gameweek],
        "warnings": quality["warnings"]
        + [
            "Forecast uses recent average FPL points over club fixtures, including DNPs; it is an uncalibrated baseline.",
            "Gains assume the transferred players contribute to your lineup throughout the horizon; bench and captain choices are not optimized.",
            "Current roster and prices are used; this is not a historical backtest.",
        ],
    }


def get_ranked_players_by_position(position, current_gameweek):
    with SessionLocal() as db:
        result = build_forecasts(db, current_gameweek)
        if "error" in result:
            return result
        return result["rankings"].get(position, [])
