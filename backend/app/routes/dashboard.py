from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.dashboard_service import get_dashboard

router = APIRouter(prefix='/api', tags=['Dashboard'])


@router.get('/dashboard')
def dashboard(lookback_gameweeks: int = Query(default=5, ge=1, le=38), db: Session = Depends(get_db)):
    return get_dashboard(db, lookback_gameweeks)
