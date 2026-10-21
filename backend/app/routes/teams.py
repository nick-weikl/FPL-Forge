from app.database import get_db
from app.models.team import Team
from app.services.fixture_difficulty_service import get_fixture_difficulty, get_team_strength
from app.services.fpl_price_service import FPL_SEASON
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/teams", tags=["Teams"])


@router.get("")
def get_teams(db: Session = Depends(get_db)):
    teams = db.query(Team).filter(Team.fpl_season == FPL_SEASON).all()

    return teams


@router.get("/{team_id}")
def get_team(team_id: int, db: Session = Depends(get_db)):
    team = db.query(Team).filter(Team.id == team_id, Team.fpl_season == FPL_SEASON).first()

    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    return team


@router.get("/{team_id}/strength")
def get_team_strength_route(
    team_id: int, current_gameweek: int = Query(..., ge=1, le=38), db: Session = Depends(get_db)
):

    strength_data = get_team_strength(team_id, current_gameweek)

    if "error" in strength_data:
        raise HTTPException(status_code=404, detail=strength_data["error"])

    return strength_data


@router.get("/{team_id}/fixture-difficulty")
def get_fixture_difficulty_route(
    team_id: int, player_position: str, current_gameweek: int = Query(..., ge=1, le=38)
):
    difficulty_data = get_fixture_difficulty(team_id, player_position, current_gameweek)

    if "error" in difficulty_data:
        raise HTTPException(status_code=400, detail=difficulty_data["error"])

    return difficulty_data
