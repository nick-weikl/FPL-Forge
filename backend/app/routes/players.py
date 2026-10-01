from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.player import Player


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
def get_player_summary(
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

    from app.services.player_analytics_service import get_player_summary
    return get_player_summary(player_id)