from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.team import Team


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