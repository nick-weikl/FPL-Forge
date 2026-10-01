from fastapi import APIRouter, Query

from app.services.team_service import sync_premier_league_teams
from app.services.player_service import sync_premier_league_players
from app.services.fixture_service import sync_premier_league_fixtures
from app.services.player_match_stat_service import sync_completed_fixture_stats


router = APIRouter(
    prefix="/sync",
    tags=["Sync"]
)


@router.post("/teams")
def sync_teams():
    return sync_premier_league_teams()


@router.post("/players")
def sync_players():
    return sync_premier_league_players()


@router.post("/fixtures")
def sync_fixtures():
    return sync_premier_league_fixtures()


@router.post("/player-match-stats/batch")
def sync_player_match_stats_batch(
    limit: int = Query(default=2, ge=1, le=10)
):
    return sync_completed_fixture_stats(limit)