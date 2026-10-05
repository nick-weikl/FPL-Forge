from pydantic import BaseModel


class TransferRecommendationRequest(BaseModel):
    current_gameweek: int
    bank_tenths: int = 0
    owned_player_ids: list[int]
    limit: int = 5


class SquadOptimizationRequest(BaseModel):
    current_gameweek: int
    bank_tenths: int = 0
    owned_player_ids: list[int]
    limit_per_player: int = 1