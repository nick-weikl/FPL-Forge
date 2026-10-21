from app.database import get_db
from app.services.team_import_service import preview_team_import
from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/fpl", tags=["Public FPL import"])


@router.get("/teams/{entry_id}/preview")
def preview(entry_id: int = Path(ge=1, le=2147483647), db: Session = Depends(get_db)):
    return preview_team_import(db, entry_id)
