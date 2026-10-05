from fastapi import APIRouter

from app.schemas.squad import SquadValidationRequest
from app.services.squad_service import validate_squad


router = APIRouter(
    prefix="/api/squads",
    tags=["Squads"]
)


@router.post("/validate")
def validate_squad_route(
    request: SquadValidationRequest
):
    return validate_squad(
        request.owned_player_ids
    )