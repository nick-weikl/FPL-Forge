from pydantic import BaseModel


class SquadValidationRequest(BaseModel):
    owned_player_ids: list[int]