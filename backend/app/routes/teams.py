from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.team import Team
from app.services.fixture_difficulty_service import get_team_strength


router = APIRouter(
    prefix="/api/teams",
    tags=["Teams"]
)


@router.get("")
def get_teams(db: Session = Depends(get_db)):
    teams = db.query(Team).all()

    return teams


@router.get("/{team_id}")
def get_team(
    team_id: int,
    db: Session = Depends(get_db)
):
    team = (
        db.query(Team)
        .filter(Team.id == team_id)
        .first()
    )

    if not team:
        raise HTTPException(
            status_code=404,
            detail="Team not found"
        )

    return team


@router.get("/{team_id}/strength")
def get_team_strength_route(
    team_id: int,
    current_gameweek: int,
    db: Session = Depends(get_db)
):

    strength_data = get_team_strength(team_id, current_gameweek)

    if "error" in strength_data:
        raise HTTPException(
            status_code=404,
            detail=strength_data["error"]
        )

    return strength_data