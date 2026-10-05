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


class DoubleTransferRecommendationRequest(BaseModel):
    current_gameweek: int
    bank_tenths: int = 0
    owned_player_ids: list[int]
    candidates_per_player: int = 3


class TransferStrategyRequest(BaseModel):
    current_gameweek: int
    bank_tenths: int = 0
    free_transfers: int = 1
    owned_player_ids: list[int]
    candidates_per_player: int = 10