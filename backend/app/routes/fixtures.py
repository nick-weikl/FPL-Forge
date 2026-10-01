from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.fixture import Fixture
from app.services.player_match_stat_service import sync_player_match_stats


router = APIRouter(
    prefix="/api/fixtures",
    tags=["Fixtures"]
)


@router.get("")
def get_fixtures(
    db: Session = Depends(get_db),
    home_team_id: Optional[int] = None,
    away_team_id: Optional[int] = None,
    team_id: Optional[int] = None,
    gameweek: Optional[int] = None
):
    query = db.query(Fixture)

    if home_team_id is not None:
        query = query.filter(Fixture.home_team_id == home_team_id)

    if away_team_id is not None:
        query = query.filter(Fixture.away_team_id == away_team_id)

    if gameweek is not None:
        query = query.filter(Fixture.gameweek == gameweek)

    if team_id is not None:
        query = query.filter(
            (Fixture.home_team_id == team_id) | (Fixture.away_team_id == team_id)
        )

    return query.all()


@router.get("/gameweek/{gameweek}")
def get_fixtures_by_gameweek(
    gameweek: int,
    db: Session = Depends(get_db)
):
    fixtures = (
        db.query(Fixture)
        .filter(Fixture.gameweek == gameweek)
        .all()
    )

    return fixtures


@router.get("/by-team/{team_id}")
def get_fixtures_by_team(
    team_id: int,
    db: Session = Depends(get_db)
):
    fixtures = (
        db.query(Fixture)
        .filter(
            (Fixture.home_team_id == team_id) | (Fixture.away_team_id == team_id)
        )
        .all()
    )

    return fixtures


@router.get("/by-team/{team_id}/gameweek/{gameweek}")
def get_fixtures_by_team_and_gameweek(
    team_id: int,
    gameweek: int,
    db: Session = Depends(get_db)
):
    fixtures = (
        db.query(Fixture)
        .filter(
            ((Fixture.home_team_id == team_id) | (Fixture.away_team_id == team_id)) &
            (Fixture.gameweek == gameweek)
        )
        .all()
    )

    return fixtures


@router.get("/{fixture_id}/player-stats-test")
def test_player_stats(fixture_id: int):
    return sync_player_match_stats(fixture_id)
