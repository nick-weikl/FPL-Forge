from app.database import SessionLocal
from app.models.player import Player
from app.services.player_scoring_service import (
    get_ranked_players_by_position
)

def get_transfer_candidates(
    current_player_id,
    current_gameweek,
    owned_player_ids,
    bank_tenths=0,
    limit=5
):
    db = SessionLocal()

    try:
        player = (
            db.query(Player)
            .filter(Player.id == current_player_id)
            .first()
        )

        if not player:
            return {
                "error": "Player not found"
            }

        if current_player_id not in owned_player_ids:
            return {
                "error": "Current player is not in the owned squad"
            }

        current_player_price = player.price_tenths

        if current_player_price is None:
            return {
                "error": "Current player does not have price data"
            }

        ranked_players = get_ranked_players_by_position(
            player.position,
            current_gameweek
        )

        if (
            isinstance(ranked_players, dict)
            and "error" in ranked_players
        ):
            return ranked_players

        current_player_score = None

        for ranked_player in ranked_players:
            if ranked_player["player_id"] == current_player_id:
                current_player_score = ranked_player["overall_score"]
                break

        if current_player_score is None:
            return {
                "error": "Current player does not have a valid score"
            }

        available_budget = (
            current_player_price + bank_tenths
        )

        owned_players = (
            db.query(Player)
            .filter(Player.id.in_(owned_player_ids))
            .all()
        )

        team_counts = {}

        for owned_player in owned_players:
            team_id = owned_player.team_id

            team_counts[team_id] = (
                team_counts.get(team_id, 0) + 1
            )

        # Remove the outgoing player from the effective squad
        current_team_id = player.team_id

        if current_team_id in team_counts:
            team_counts[current_team_id] -= 1

        candidates = []

        for candidate in ranked_players:
            # Don't recommend the same player
            if candidate["player_id"] == current_player_id:
                continue

            # Don't recommend a player already owned
            if candidate["player_id"] in owned_player_ids:
                continue

            candidate_price = candidate.get("price_tenths")
            candidate_team_id = candidate.get("team_id")

            # Skip candidates with missing required data
            if (
                candidate_price is None
                or candidate_team_id is None
            ):
                continue

            # Skip unaffordable candidates
            if candidate_price > available_budget:
                continue

            # Skip players that would create 4 players
            # from the same Premier League club
            if team_counts.get(candidate_team_id, 0) >= 3:
                continue

            candidate_data = candidate.copy()

            candidate_data["score_gain"] = round(
                candidate_data["overall_score"]
                - current_player_score,
                2
            )

            candidate_data["recommendation_strength"] = (
                get_recommendation_strength(
                    candidate_data["score_gain"]
                )
            )

            candidates.append(candidate_data)

        upgrades = [
            candidate
            for candidate in candidates
            if candidate["score_gain"] > 0
        ]

        return {
            "current_player_id": current_player_id,
            "current_player_score": current_player_score,
            "current_player_price_tenths": current_player_price,
            "bank_tenths": bank_tenths,
            "available_budget_tenths": available_budget,
            "position": player.position,
            "upgrade_found": len(upgrades) > 0,
            "candidates": upgrades[:limit]
        }

    finally:
        db.close()


def get_recommendation_strength(score_gain):
    if score_gain <= 0:
        return "none"
    elif score_gain >= 2.0:
        return "strong"
    elif score_gain >= 1.0:
        return "moderate"
    else:
        return "slight"