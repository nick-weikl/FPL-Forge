from datetime import datetime, timedelta, timezone

from app.models import Fixture, Player, PlayerMatchStat
from app.models.fpl_data import FPLImport
from app.services.football_api import SEASON
from app.services.fpl_price_service import FPL_SEASON
from sqlalchemy import func, select

PRICE_MAX_AGE = timedelta(days=7)


def has_current_price(player, now):
    observed = player.price_updated_at
    if observed is None or player.price_tenths is None or player.price_tenths <= 0:
        return False
    if observed.tzinfo is None:
        observed = observed.replace(tzinfo=timezone.utc)
    return timedelta(0) <= now - observed <= PRICE_MAX_AGE


def get_data_quality(db):
    now = datetime.now(timezone.utc)
    imports = list(db.scalars(select(FPLImport).where(FPLImport.season == SEASON)))
    stale = db.scalar(
        select(func.count())
        .select_from(Fixture)
        .where(
            Fixture.season == SEASON,
            Fixture.fixture_date < now.replace(tzinfo=None) - timedelta(hours=3),
            Fixture.status.in_(["NS", "LIVE"]),
        )
    )
    missing_api = db.scalar(
        select(func.count())
        .select_from(Player)
        .where(Player.fpl_season == FPL_SEASON, Player.external_api_id.is_(None))
    )
    api_gw = db.scalar(
        select(func.max(Fixture.gameweek)).join(PlayerMatchStat).where(Fixture.season == SEASON)
    )
    fpl_gw = max((r.gameweek for r in imports), default=None)
    missing_club = db.scalar(
        select(func.count())
        .select_from(PlayerMatchStat)
        .join(Fixture)
        .where(Fixture.season == SEASON, PlayerMatchStat.team_id.is_(None))
    )
    players = list(db.scalars(select(Player).where(Player.fpl_season == FPL_SEASON)))
    unusable_prices = sum(not has_current_price(player, now) for player in players)
    warnings = []
    if unusable_prices:
        warnings.append(
            f"{unusable_prices} players have missing, invalid or outdated prices (older than seven days or dated in the future); they are excluded from incoming transfers. Refresh prices before acting."
        )
    if stale:
        warnings.append(
            f"{stale} past fixtures still lack a final status; refresh official fixtures."
        )
    if missing_api:
        warnings.append(
            f"{missing_api} players lack API-Sports links. Official FPL points are independent of these links."
        )
    if fpl_gw and (api_gw or 0) < fpl_gw:
        warnings.append(
            f"Advanced API-Sports stats stop at GW{api_gw or 0}; official FPL points reach GW{fpl_gw}."
        )
    if missing_club:
        warnings.append(
            f"{missing_club} API-Sports rows have unknown historical clubs; current clubs were not substituted."
        )
    return {
        "season": FPL_SEASON,
        "unusable_price_players": unusable_prices,
        "official_fpl_through_gameweek": fpl_gw,
        "api_sports_through_gameweek": api_gw,
        "past_unfinished_fixtures": stale,
        "unlinked_api_players": missing_api,
        "unknown_api_historical_clubs": missing_club,
        "warnings": warnings,
    }
