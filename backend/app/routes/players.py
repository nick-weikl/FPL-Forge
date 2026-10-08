from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import Optional

from app.database import get_db
from app.models.player import Player
from app.services.player_analytics_service import get_player_recent_form
from app.services.player_analytics_service import get_player_summary
from app.services.fixture_analytics_service import get_upcoming_fixtures
from app.services.fixture_analytics_service import get_player_fixture_outlook
from app.services.player_scoring_service import get_all_player_metrics, get_forward_scores, get_midfielder_scores, get_defender_scores, get_goalkeeper_scores, get_ranked_players_by_position
from app.services.fpl_price_service import FPL_SEASON


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
    query = (
        db.query(Player)
        .options(joinedload(Player.team))
        .filter(Player.fpl_season == FPL_SEASON)
    )

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

    players = query.all()

    return [
        {
            "id": player.id,
            "external_api_id": player.external_api_id,
            "name": player.name,
            "position": player.position,
            "team_id": player.team_id,
            "team_name": player.team.name if player.team else None,
            "price_tenths": player.price_tenths,
        }
        for player in players
    ]


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
    current_gameweek: int,
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

    return get_player_summary(
        player_id=player_id,
        current_gameweek=current_gameweek,
        db=db
    )


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

    summary = get_player_summary(
        player_id=player_id,
        current_gameweek=current_gameweek,
        db=db
    )

    recent_form = get_player_recent_form(
        player_id=player_id,
        current_gameweek=current_gameweek,
        num_matches=recent_matches,
        db=db
    )

    upcoming_fixtures = get_upcoming_fixtures(
        player_id=player_id,
        current_gameweek=current_gameweek,
        limit=fixture_limit,
        db=db
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


@router.get("/scores/midfielders")
def get_midfielder_scores_route(
    current_gameweek: int
):
    return get_midfielder_scores(current_gameweek)


@router.get("/scores/defenders")
def get_defender_scores_route(
    current_gameweek: int
):
    return get_defender_scores(current_gameweek)


@router.get("/scores/goalkeepers")
def get_goalkeeper_scores_route(
    current_gameweek: int
):
    return get_goalkeeper_scores(current_gameweek)


@router.get("/scores/ranked")
def get_ranked_players_route(
    position: str,
    current_gameweek: int
):
    result = get_ranked_players_by_position(
        position,
        current_gameweek
    )

    if isinstance(result, dict) and "error" in result:
        raise HTTPException(
            status_code=400,
            detail=result["error"]
        )

    return result