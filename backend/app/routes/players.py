from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.player import Player
from app.services.player_analytics_service import get_player_recent_form
from app.services.player_analytics_service import get_player_summary
from app.services.fixture_analytics_service import get_upcoming_fixtures
from app.services.fixture_analytics_service import get_player_fixture_outlook
from app.services.player_scoring_service import get_all_player_metrics, get_forward_scores


router = APIRouter(
    prefix="/api/players",
    tags=["Players"]
)


@router.get("")
def get_players(
    team_id: Optional[int] = None,
    position: Optional[str] = None,
    db: Session = Depends(get_db),
    name: Optional[str] = None,
):
    query = db.query(Player)

    if team_id is not None:
        query = query.filter(
            Player.team_id == team_id
        )

    if position is not None:
        query = query.filter(
            Player.position == position
        )

    if name is not None:
        query = query.filter(
            Player.name.ilike(f"%{name}%")
        )

    return query.all()


@router.get("/{player_id}")
def get_player(
    player_id: int,
    db: Session = Depends(get_db)
):
    player = (
        db.query(Player)
        .filter(Player.id == player_id)
        .first()
    )

    if not player:
        raise HTTPException(
            status_code=404,
            detail="Player not found"
        )

    return player


@router.get("/{player_id}/summary")
def get_player_summary_route(
    player_id: int,
    db: Session = Depends(get_db)
):
    player = (
        db.query(Player)
        .filter(Player.id == player_id)
        .first()
    )

    if not player:
        raise HTTPException(
            status_code=404,
            detail="Player not found"
        )

    return get_player_summary(player_id)


@router.get("/{player_id}/recent-form")
def get_player_recent_form_route(
    player_id: int,
    current_gameweek: int,
    num_matches: int = 5,
    db: Session = Depends(get_db)
):
    player = (
        db.query(Player)
        .filter(Player.id == player_id)
        .first()
    )

    if not player:
        raise HTTPException(
            status_code=404,
            detail="Player not found"
        )

    return get_player_recent_form(player_id, current_gameweek, num_matches)


@router.get("/{player_id}/upcoming-fixtures")
def get_player_upcoming_fixtures(
    player_id: int,
    current_gameweek: int = 4,
    limit: int = 5,
    db: Session = Depends(get_db)
):
    player = (
        db.query(Player)
        .filter(Player.id == player_id)
        .first()
    )

    if not player:
        raise HTTPException(
            status_code=404,
            detail="Player not found"
        )

    return get_upcoming_fixtures(
        player_id,
        current_gameweek,
        limit
    )


@router.get("/{player_id}/analytics")
def get_player_analytics_route(
    player_id: int,
    current_gameweek: int = 4,
    recent_matches: int = 5,
    fixture_limit: int = 5,
    db: Session = Depends(get_db)
):
    player = (
        db.query(Player)
        .filter(Player.id == player_id)
        .first()
    )

    if not player:
        raise HTTPException(
            status_code=404,
            detail="Player not found"
        )

    summary = get_player_summary(player_id)

    recent_form = get_player_recent_form(
        player_id,
        recent_matches
    )

    upcoming_fixtures = get_upcoming_fixtures(
        player_id,
        current_gameweek,
        fixture_limit
    )

    return {
        "player_id": player_id,
        "summary": summary,
        "recent_form": recent_form,
        "upcoming_fixtures": upcoming_fixtures
    }


@router.get("/{player_id}/fixture-outlook")
def get_player_fixture_outlook_route(
    player_id: int,
    current_gameweek: int,
    limit: int = 5
):
    outlook = get_player_fixture_outlook(
        player_id,
        current_gameweek,
        limit
    )

    if "error" in outlook:
        raise HTTPException(
            status_code=404,
            detail=outlook["error"]
        )

    return outlook


@router.get("/{player_id}/metrics")
def get_all_player_metrics_route(
    current_gameweek: int = 5,
    position: str = "Attacker"
):
    return get_all_player_metrics(current_gameweek, position)


@router.get("/scores/forwards")
def get_forward_scores_route(
    current_gameweek: int
):
    return get_forward_scores(current_gameweek)