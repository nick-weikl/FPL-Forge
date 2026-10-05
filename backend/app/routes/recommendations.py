from fastapi import APIRouter, Depends, HTTPException
from app.services.recommendation_service import get_transfer_candidates, get_best_squad_transfer
from app.schemas.recommendation import TransferRecommendationRequest, SquadOptimizationRequest

router = APIRouter(
    prefix="/api/recommendations",
    tags=["Recommendations"]
)

@router.post("/transfers/{player_id}")
def get_transfer_candidates_route(
    player_id: int,
    request: TransferRecommendationRequest
):
    result = get_transfer_candidates(
        current_player_id=player_id,
        current_gameweek=request.current_gameweek,
        owned_player_ids=request.owned_player_ids,
        bank_tenths=request.bank_tenths,
        limit=request.limit
    )

    if isinstance(result, dict) and "error" in result:
        raise HTTPException(
            status_code=400,
            detail=result["error"]
        )

    return result


@router.post("/squad-transfer")
def get_best_squad_transfer_route(
    request: SquadOptimizationRequest
):
    result = get_best_squad_transfer(
        current_gameweek=request.current_gameweek,
        owned_player_ids=request.owned_player_ids,
        bank_tenths=request.bank_tenths
    )

    if isinstance(result, dict) and "error" in result:
        raise HTTPException(
            status_code=400,
            detail=result
        )

    return result