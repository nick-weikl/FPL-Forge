from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Fixture, Player
from app.models.fpl_data import FPLMatchStat
from app.services.football_api import SEASON
from app.services.data_quality_service import get_data_quality

router = APIRouter(prefix='/api', tags=['Data quality'])


@router.get('/data-quality')
def data_quality(db: Session = Depends(get_db)):
    return get_data_quality(db)


@router.get('/players/{player_id}/fpl-history')
def fpl_history(player_id: int, db: Session = Depends(get_db)):
    rows = db.execute(select(FPLMatchStat, Fixture.gameweek).join(Fixture).where(
        Fixture.season == SEASON, FPLMatchStat.player_id == player_id).order_by(Fixture.fixture_date)).all()
    return [{'fixture_id': row.fixture_id, 'gameweek': gw, 'historical_team_id': row.team_id,
             'minutes': row.minutes, 'total_points': row.total_points, 'stats': row.stats}
            for row, gw in rows]
