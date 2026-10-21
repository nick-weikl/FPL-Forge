from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

PositiveID = Annotated[int, Field(strict=True, gt=0)]
Money = Annotated[int, Field(strict=True, ge=0)]


class TransferRecommendationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    current_gameweek: int = Field(ge=1, le=38, strict=True)
    bank_tenths: int = Field(default=0, ge=0, strict=True)
    owned_player_ids: list[PositiveID] = Field(min_length=15, max_length=15)
    selling_prices_tenths: dict[PositiveID, Money] = Field(default_factory=dict)
    limit: int = Field(default=5, ge=1, le=50, strict=True)

    @field_validator("selling_prices_tenths", mode="before")
    @classmethod
    def normalize_selling_price_ids(cls, value):
        # FastAPI validates decoded JSON, whose object keys are always strings.
        # Convert only canonical integer keys; keep strict validation on values.
        if not isinstance(value, dict):
            return value
        normalized = {}
        for key, price in value.items():
            if isinstance(key, str) and key.isascii() and key.isdecimal() and str(int(key)) == key:
                key = int(key)
            if key in normalized:
                raise ValueError("Duplicate selling-price player ID")
            normalized[key] = price
        return normalized

    @model_validator(mode="after")
    def validate_squad_ids(self):
        if len(set(self.owned_player_ids)) != 15:
            raise ValueError("Squad contains duplicate players")
        if not set(self.selling_prices_tenths).issubset(self.owned_player_ids):
            raise ValueError("Selling prices must refer to owned players")
        return self


class SquadOptimizationRequest(TransferRecommendationRequest):
    limit_per_player: int = Field(default=1, ge=1, le=50, strict=True)


class DoubleTransferRecommendationRequest(TransferRecommendationRequest):
    # Retained for client compatibility. The optimizer searches all feasible pairs.
    candidates_per_player: int = Field(default=10, ge=1, le=100, strict=True)


class TransferStrategyRequest(DoubleTransferRecommendationRequest):
    free_transfers: int = Field(default=1, ge=0, le=5, strict=True)
    starting_player_ids: list[PositiveID] = Field(min_length=11, max_length=11)
    bench_player_ids: list[PositiveID] = Field(min_length=4, max_length=4)
    captain_id: PositiveID
    vice_captain_id: PositiveID

    @model_validator(mode="after")
    def validate_lineup_ids(self):
        ids = self.starting_player_ids + self.bench_player_ids
        if len(set(ids)) != 15 or set(ids) != set(self.owned_player_ids):
            raise ValueError("Starting XI and bench must contain every owned player exactly once")
        if self.captain_id == self.vice_captain_id or not {
            self.captain_id,
            self.vice_captain_id,
        }.issubset(self.starting_player_ids):
            raise ValueError("Choose different captain and vice-captain from the starting XI")
        return self
